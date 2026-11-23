import os
import json
import datetime
import pandas as pd
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

from backend.database import Database
from mysql.connector import Error

def fix_ar(text):
    """تهيئة النص العربي للطباعة في تقارير PDF مع الحفاظ على الأرقام والإنجليزية"""
    if text is None:
        return ""
    text_str = str(text).strip()
    if not text_str:
        return ""
    try:
        has_arabic = any(
            '\u0600' <= char <= '\u06FF' or 
            '\u0750' <= char <= '\u077F' or 
            '\u08A0' <= char <= '\u08FF' or 
            '\uFB50' <= char <= '\uFDFF' or 
            '\uFE70' <= char <= '\uFEFF' 
            for char in text_str
        )
        if has_arabic:
            reshaped = arabic_reshaper.reshape(text_str)
            return get_display(reshaped)
        return text_str
    except Exception:
        return text_str

class PurchasesRepository:
    def __init__(self):
        self.db = Database()
        self._init_tables()

    def _init_tables(self):
        """إنشاء جدول سندات المدفوعات المستقل للموردين إن لم يكن موجوداً"""
        conn = self.db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supplier_payments (
                    payment_id INT AUTO_INCREMENT PRIMARY KEY,
                    supplier_id INT NOT NULL,
                    purchase_id INT,
                    amount DECIMAL(10,2) NOT NULL,
                    payment_date DATE NOT NULL,
                    supplier_voucher_no VARCHAR(100),
                    notes TEXT
                );
            """)
            conn.commit()
            cursor.close()
            conn.close()
        except Error as e:
            print(f"[خطأ في إنشاء جدول سندات الموردين]: {e}")

    def get_clinic_info(self):
        """قراءة بيانات وهوية العيادة من الإعدادات"""
        config_file = os.path.join(os.getcwd(), "clinic_config.json")
        default_cfg = {
            "name": "عيادة تيسير لطب الأسنان",
            "phone": "770000000",
            "address": "صنعاء - اليمن"
        }
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        "name": data.get("name", default_cfg["name"]),
                        "phone": data.get("phone", default_cfg["phone"]),
                        "address": data.get("address", default_cfg["address"])
                    }
            except Exception:
                return default_cfg
        return default_cfg

    # =========================================================================
    # 1. إدارة الموردين (Suppliers) - [إضافة، تعديل، حذف، عرض]
    # =========================================================================
    def get_suppliers_list(self):
        """جلب قائمة جميع الموردين مع إجمالي المديونية إن وجدت"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    s.supplier_id, 
                    s.supplier_name, 
                    COALESCE(s.address, 'غير محدد') as address,
                    COALESCE(s.phone, 'بدون') as phone,
                    COALESCE(s.notes, '') as notes,
                    COALESCE(SUM(p.remaining_amount), 0) AS total_debt
                FROM suppliers s
                LEFT JOIN purchases p ON s.supplier_id = p.supplier_id
                GROUP BY s.supplier_id, s.supplier_name, s.address, s.phone, s.notes
                ORDER BY s.supplier_id DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"[خطأ في جلب قائمة الموردين]: {e}")
            return []

    def add_supplier(self, name, address, phone, notes=""):
        """إضافة مورد جديد إلى قاعدة البيانات"""
        conn = self.db.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات."
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO suppliers (supplier_name, address, phone, notes)
                VALUES (%s, %s, %s, %s);
            """
            cursor.execute(query, (name, address, phone, notes))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم إضافة المورد بنجاح."
        except Error as e:
            return False, f"فشل إضافة المورد: {e}"

    def update_supplier(self, supplier_id, name, address, phone, notes=""):
        """تعديل بيانات مورد موجود"""
        conn = self.db.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات."
        try:
            cursor = conn.cursor()
            query = """
                UPDATE suppliers 
                SET supplier_name = %s, address = %s, phone = %s, notes = %s
                WHERE supplier_id = %s;
            """
            cursor.execute(query, (name, address, phone, notes, supplier_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تحديث بيانات المورد بنجاح."
        except Error as e:
            return False, f"فشل تحديث بيانات المورد: {e}"

    def delete_supplier(self, supplier_id):
        """حذف مورد من النظام"""
        conn = self.db.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات."
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM suppliers WHERE supplier_id = %s;", (supplier_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم حذف المورد بنجاح."
        except Error as e:
            return False, f"تعذر حذف المورد، قد يكون مرتبطاً بفواتير مسجلة: {e}"

    # =========================================================================
    # 2. فواتير ومدفوعات المشتريات (Purchases) - [إضافة، تعديل، حذف، سداد]
    # =========================================================================
    def get_purchases_list(self):
        """جلب سجل فواتير المشتريات مع نوع الفاتورة ورقم سند المورد"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    p.purchase_id,
                    COALESCE(p.invoice_number, '-') as invoice_number,
                    p.supplier_id,
                    COALESCE(s.supplier_name, 'مورد محذوف') as supplier_name,
                    p.description,
                    p.purchase_date,
                    p.total_amount,
                    p.paid_amount,
                    p.remaining_amount,
                    COALESCE(p.purchase_type, 'Cash') as purchase_type,
                    p.payment_status,
                    COALESCE(p.supplier_voucher_no, '-') as supplier_voucher_no,
                    p.payment_date
                FROM purchases p
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
                ORDER BY p.purchase_id DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"[خطأ في جلب فواتير المشتريات]: {e}")
            return []

    def get_supplier_payments_list(self, supplier_id):
        """جلب سندات ودفعات المورد المستقلة"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT payment_id, supplier_id, purchase_id, amount, payment_date, 
                       COALESCE(supplier_voucher_no, '-') as supplier_voucher_no, notes
                FROM supplier_payments
                WHERE supplier_id = %s
                ORDER BY payment_date DESC, payment_id DESC;
            """
            cursor.execute(query, (supplier_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"[خطأ في جلب سندات المورد]: {e}")
            return []

    def add_purchase_invoice(self, invoice_number, supplier_id, description, purchase_date, total_amount, paid_amount, purchase_type="Cash", payment_date=None, supplier_voucher_no=None):
        """إضافة فاتورة مشتريات جديدة مع تحديد أسماء الأعمدة صراحة وتجنب الأعمدة المولدة"""
        conn = self.db.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات."
        try:
            total = float(total_amount) if total_amount and str(total_amount).strip() else 0.0
            paid = float(paid_amount) if paid_amount and str(paid_amount).strip() else 0.0
            
            inv_num = str(invoice_number).strip() if invoice_number else None
            p_date = str(purchase_date).strip() if purchase_date else datetime.date.today().strftime("%Y-%m-%d")
            desc = str(description).strip() if description else ""
            p_type = str(purchase_type).strip() if purchase_type else "Cash"
            vouch_no = str(supplier_voucher_no).strip() if supplier_voucher_no else None

            remaining = max(0.0, total - paid)
            if remaining <= 0 and total > 0:
                payment_status = "Paid"
            elif paid > 0:
                payment_status = "Partial"
            else:
                payment_status = "Unpaid"

            pay_date_val = payment_date if payment_date else (p_date if paid > 0 else None)

            cursor = conn.cursor()
            query = """
                INSERT INTO purchases 
                (invoice_number, purchase_type, supplier_id, description, purchase_date, total_amount, paid_amount, payment_date, payment_status, supplier_voucher_no)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (
                inv_num, 
                p_type, 
                supplier_id, 
                desc, 
                p_date, 
                total, 
                paid, 
                pay_date_val, 
                payment_status, 
                vouch_no
            ))

            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تسجيل فاتورة المشتريات بنجاح."
        except Error as e:
            return False, f"فشل تسجيل الفاتورة: {e}"

    def update_purchase_invoice(self, purchase_id, invoice_number, supplier_id, description, purchase_date, total_amount, paid_amount, purchase_type="Cash"):
        """تعديل فاتورة مشتريات موجودة مسبقاً"""
        conn = self.db.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات."
        try:
            total = float(total_amount) if total_amount and str(total_amount).strip() else 0.0
            paid = float(paid_amount) if paid_amount and str(paid_amount).strip() else 0.0

            inv_num = str(invoice_number).strip() if invoice_number else ""
            p_date = str(purchase_date).strip() if purchase_date else datetime.date.today().strftime("%Y-%m-%d")
            desc = str(description).strip() if description else ""
            p_type = str(purchase_type).strip() if purchase_type else "Cash"

            if (total - paid) <= 0 and total > 0:
                payment_status = "Paid"
            elif paid > 0:
                payment_status = "Partial"
            else:
                payment_status = "Unpaid"

            cursor = conn.cursor()
            query = """
                UPDATE purchases 
                SET invoice_number = %s, supplier_id = %s, description = %s, purchase_date = %s, 
                    total_amount = %s, paid_amount = %s, payment_status = %s, purchase_type = %s
                WHERE purchase_id = %s;
            """
            cursor.execute(query, (inv_num, supplier_id, desc, p_date, total, paid, payment_status, p_type, purchase_id))

            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تحديث فاتورة المشتريات بنجاح."
        except Error as e:
            return False, f"فشل تحديث الفاتورة: {e}"

    def update_supplier_payment(self, payment_id, new_amount, payment_date, supplier_voucher_no=None):
        """تعديل قيمة أو تاريخ سند صرف مسجل مسبقاً وتعديل الفاتورة المرتبطة به"""
        conn = self.db.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات."
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM supplier_payments WHERE payment_id = %s;", (payment_id,))
            payment = cursor.fetchone()
            if not payment:
                cursor.close()
                conn.close()
                return False, "السند غير موجود."

            purchase_id = payment['purchase_id']
            old_amount = float(payment['amount'])
            new_amt = float(new_amount)

            if purchase_id:
                cursor.execute("SELECT total_amount, paid_amount FROM purchases WHERE purchase_id = %s;", (purchase_id,))
                inv = cursor.fetchone()
                if inv:
                    total = float(inv['total_amount'])
                    current_paid = float(inv['paid_amount'])
                    
                    adjusted_paid = (current_paid - old_amount) + new_amt

                    if (total - adjusted_paid) <= 0 and total > 0:
                        status = "Paid"
                    elif adjusted_paid > 0:
                        status = "Partial"
                    else:
                        status = "Unpaid"

                    update_inv = """
                        UPDATE purchases 
                        SET paid_amount = %s, payment_status = %s
                        WHERE purchase_id = %s;
                    """
                    cursor.execute(update_inv, (adjusted_paid, status, purchase_id))

            vouch_no = str(supplier_voucher_no).strip() if supplier_voucher_no else payment['supplier_voucher_no']
            update_pay = """
                UPDATE supplier_payments 
                SET amount = %s, payment_date = %s, supplier_voucher_no = %s
                WHERE payment_id = %s;
            """
            cursor.execute(update_pay, (new_amt, payment_date, vouch_no, payment_id))

            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تحديث السند بنجاح."
        except Error as e:
            return False, f"فشل تحديث السند: {e}"

    def delete_supplier_payment(self, payment_id):
        """حذف سند صرف وإعادة المبلغ المالي إلى مديونية الفاتورة"""
        conn = self.db.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات."
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM supplier_payments WHERE payment_id = %s;", (payment_id,))
            payment = cursor.fetchone()
            if not payment:
                cursor.close()
                conn.close()
                return False, "السند غير موجود."

            purchase_id = payment['purchase_id']
            paid_to_remove = float(payment['amount'])

            if purchase_id:
                cursor.execute("SELECT total_amount, paid_amount FROM purchases WHERE purchase_id = %s;", (purchase_id,))
                inv = cursor.fetchone()
                if inv:
                    total = float(inv['total_amount'])
                    current_paid = float(inv['paid_amount'])
                    
                    new_paid = max(0.0, current_paid - paid_to_remove)
                    new_remaining = total - new_paid

                    if new_remaining == 0:
                        status = "Paid"
                    elif new_paid > 0:
                        status = "Partial"
                    else:
                        status = "Unpaid"

                    update_inv = """
                        UPDATE purchases 
                        SET paid_amount = %s, payment_status = %s
                        WHERE purchase_id = %s;
                    """
                    cursor.execute(update_inv, (new_paid, status, purchase_id))

            cursor.execute("DELETE FROM supplier_payments WHERE payment_id = %s;", (payment_id,))

            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم حذف السند واستعادة المبلغ للفاتورة بنجاح."
        except Error as e:
            return False, f"فشل حذف السند: {e}"
    
    def delete_purchase_invoice(self, purchase_id):
        """حذف فاتورة مشتريات من النظام"""
        conn = self.db.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات."
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM supplier_payments WHERE purchase_id = %s;", (purchase_id,))
            cursor.execute("DELETE FROM purchases WHERE purchase_id = %s;", (purchase_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم حذف فاتورة المشتريات بنجاح."
        except Error as e:
            return False, f"فشل حذف الفاتورة: {e}"

    def make_supplier_payment(self, purchase_id, additional_paid, payment_date, supplier_voucher_no=None):
        """تسجيل دفعة مالية إضافية لفاتورة مشتريات وتخزين السند"""
        conn = self.db.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات."
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT supplier_id, total_amount, paid_amount FROM purchases WHERE purchase_id = %s;", (purchase_id,))
            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return False, "الفاتورة المحددة غير موجودة."

            supplier_id = row[0]
            total = float(row[1] or 0)
            current_paid = float(row[2] or 0)
            add_paid = float(additional_paid or 0)

            new_paid = current_paid + add_paid
            new_remaining = max(0.0, total - new_paid)

            if new_remaining == 0:
                payment_status = "Paid"
            elif new_paid > 0:
                payment_status = "Partial"
            else:
                payment_status = "Unpaid"

            vouch_no = str(supplier_voucher_no).strip() if supplier_voucher_no else None

            update_query = """
                UPDATE purchases 
                SET paid_amount = %s, payment_date = %s, payment_status = %s, supplier_voucher_no = %s
                WHERE purchase_id = %s;
            """
            cursor.execute(update_query, (new_paid, payment_date, payment_status, vouch_no, purchase_id))

            if add_paid > 0:
                pay_insert = """
                    INSERT INTO supplier_payments (supplier_id, purchase_id, amount, payment_date, supplier_voucher_no, notes)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """
                cursor.execute(pay_insert, (supplier_id, purchase_id, add_paid, payment_date, vouch_no, f"سداد لفاتورة رقم #{purchase_id}"))

            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تسديد الدفعة المالية وتوثيق السند بنجاح."
        except Error as e:
            return False, f"فشل تسجيل الدفعة: {e}"
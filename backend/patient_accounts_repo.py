from backend.database import Database
from mysql.connector import Error
import datetime

class PatientAccountsRepository:
    def __init__(self):
        self.db = Database()

    def add_invoice_from_treatment(self, patient_id, treatment_id, total_amount, paid_amount, payment_status, payment_method, payment_date=None):
        """إنشاء فاتورة مالية مرتبطة بالجلسة العلاجية أوتوماتيكياً"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            pay_date = payment_date if payment_date else datetime.date.today().strftime("%Y-%m-%d")
            
            query = """
                INSERT INTO patient_accounts 
                (patient_id, treatment_id, total_amount, paid_amount, payment_date, payment_status, payment_method)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (
                patient_id, 
                treatment_id, 
                total_amount, 
                paid_amount, 
                pay_date, 
                payment_status, 
                payment_method
            ))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تسجيل الفاتورة والذمة المالية بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def get_all_invoices(self):
        """جلب كافة فواتير وحسابات المرضى مع تفاصيلها"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT a.invoice_id, a.patient_id, p.full_name, a.treatment_id, a.total_amount, a.paid_amount, 
                       a.remaining_amount, a.payment_date, a.payment_status, a.payment_method
                FROM patient_accounts a
                LEFT JOIN patients p ON a.patient_id = p.patient_id
                ORDER BY a.invoice_id DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"[خطأ في جلب حسابات المرضى]: {e}")
            return []

    def update_account(self, invoice_id, paid_amount, payment_method):
        """تعديل حركة مالية أو فاتورة سابقة بدون الاقتراب من العمود المولّد"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor(dictionary=True)
            
            # جلب إجمالي الفاتورة فقط لتحديد حالة الدفع (خالص أو مسجز جزئياً)
            cursor.execute("SELECT total_amount FROM patient_accounts WHERE invoice_id = %s;", (invoice_id,))
            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return False, "الحركة المالية غير موجودة."

            total_val = float(row['total_amount'] or 0)
            new_paid = float(paid_amount or 0)
            
            # تحديد الحالة بناءً على المدفوع والإجمالي
            if (total_val - new_paid) <= 0 and total_val > 0:
                status = "Paid"
            elif new_paid > 0:
                status = "Partial"
            else:
                status = "Unpaid"

            # استعلام التحديث المباشر للـ paid_amount فقط (قاعدة البيانات ستحسب remaining_amount تلقائياً)
            update_query = """
                UPDATE patient_accounts 
                SET paid_amount = %s, payment_status = %s, payment_method = %s
                WHERE invoice_id = %s;
            """
            cursor.execute(update_query, (new_paid, status, payment_method, invoice_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تحديث الحركة المالية بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def delete_account(self, invoice_id):
        """حذف حركة مالية أو سند قبض"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM patient_accounts WHERE invoice_id = %s;", (invoice_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم حذف الحركة المالية بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"
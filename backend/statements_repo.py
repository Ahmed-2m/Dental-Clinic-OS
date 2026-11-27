import os
import datetime
import pandas as pd
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

from backend.database import Database
from backend.print_branding import load_clinic_profile, draw_pdf_clinic_logo
from mysql.connector import Error


def fix_ar(text):
    """تهيئة النص العربي للطباعة في تقارير PDF بواسطة FPDF مع الحفاظ على الأرقام والإنجليزية"""
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


def _fit_text(pdf: FPDF, raw_text, max_width: float) -> str:
    """تقليص النص بذكاء قبل التشكيل العربي ليتناسب تماماً مع عرض الخلية دون تجاوز الحدود"""
    text_str = str(raw_text or "").strip()
    if not text_str:
        return ""
    safe_w = max(4.0, max_width - 2.5)
    if pdf.get_string_width(fix_ar(text_str)) <= safe_w:
        return fix_ar(text_str)

    trimmed = text_str
    while len(trimmed) > 1:
        trimmed = trimmed[:-1]
        candidate = fix_ar(trimmed + "..")
        if pdf.get_string_width(candidate) <= safe_w:
            return candidate
    return fix_ar(trimmed)


class StatementsRepository:
    def __init__(self):
        self.db = Database.from_config_file()

    def get_clinic_info(self):
        """قراءة بيانات وهوية العيادة من الملف الموحد للطباعة (clinic_profile.json)"""
        return load_clinic_profile()

    def _init_pdf(self, c_info):
        """تهيئة مستند PDF موحد الأبعاد (A4 بعرض عمل 180 مم وهوافش 15 مم)"""
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_left_margin(15)
        pdf.set_right_margin(15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        draw_pdf_clinic_logo(pdf, c_info)

        font_path = r"C:\Windows\Fonts\arial.ttf"
        font_bold_path = r"C:\Windows\Fonts\arialbd.ttf"
        if os.path.exists(font_path):
            pdf.add_font("ArabicFont", "", font_path, uni=True)
            if os.path.exists(font_bold_path):
                pdf.add_font("ArabicFont", "B", font_bold_path, uni=True)
            font_name = "ArabicFont"
        else:
            font_name = "Arial"

        return pdf, font_name, 180.0

    def _draw_pdf_header(self, pdf: FPDF, font_name: str, c_info: dict, title: str, accent_rgb: tuple, usable_w: float):
        """رسم ترويسة العيادة وعنوان التقرير بعرض موحد 180 مم"""
        pdf.set_font(font_name, "B", 17)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(usable_w, 9, txt=fix_ar(c_info.get("name", "عيادة تيسير لطب الأسنان")), ln=True, align="C")

        pdf.set_font(font_name, "", 10)
        pdf.set_text_color(71, 85, 105)
        clinic_contact = f"العنوان: {c_info.get('address', 'صنعاء')}   |   هاتف: {c_info.get('phone', '770000000')}"
        pdf.cell(usable_w, 6, txt=fix_ar(clinic_contact), ln=True, align="C")

        r, g, b = accent_rgb
        pdf.set_draw_color(r, g, b)
        pdf.set_line_width(0.8)
        line_y = pdf.get_y() + 2
        pdf.line(15, line_y, 15 + usable_w, line_y)
        pdf.ln(5)

        pdf.set_font(font_name, "B", 13)
        pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(r, g, b)
        pdf.cell(usable_w, 9, txt=fix_ar(title), ln=True, align="C", fill=True)
        pdf.ln(4)

    def _draw_table_header(self, pdf: FPDF, font_name: str, headers: list, widths: list, fill_rgb=(15, 23, 42), font_size=9):
        """رسم رأس الجدول بمحاذاة مضبوطة على اليسار 15 مم"""
        pdf.set_x(15)
        pdf.set_fill_color(*fill_rgb)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(font_name, "B", font_size)
        for h, w in zip(headers, widths):
            pdf.cell(w, 8, txt=_fit_text(pdf, h, w), border=1, align="C", fill=True)
        pdf.ln()

    def _draw_signatures(self, pdf: FPDF, font_name: str, usable_w: float, right_label: str):
        """رسم قسم التواقيع في أسفل الصفحة ضمن العرض الموحد"""
        pdf.set_font(font_name, "", 10)
        pdf.set_text_color(100, 116, 139)
        sign_y = pdf.get_y()
        if sign_y > 260:
            pdf.add_page()
            sign_y = pdf.get_y()
        half_w = usable_w / 2.0
        pdf.set_xy(15, sign_y)
        pdf.cell(half_w, 6, txt=fix_ar("توقيع المحاسب / الإدارة: ........................"), align="L")
        pdf.set_xy(15 + half_w, sign_y)
        pdf.cell(half_w, 6, txt=fix_ar(f"{right_label}: ........................"), align="R")

    # =========================================================================
    # 1. قوائم البحث والمساعدات (مرضى، معامل، موظفين، موردين)
    # =========================================================================
    def get_patients_list(self):
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    p.patient_id, 
                    p.full_name, 
                    COALESCE(p.phone, 'بدون') as phone,
                    COALESCE(SUM(a.total_amount - a.paid_amount), 0) AS debt
                FROM patients p
                LEFT JOIN patient_accounts a ON p.patient_id = a.patient_id
                GROUP BY p.patient_id, p.full_name, p.phone
                ORDER BY p.patient_id DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"[خطأ في جلب قائمة المرضى للكشوفات]: {e}")
            return []

    def get_labs_list(self):
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    l.lab_id,
                    l.lab_name,
                    COALESCE(l.phone, 'بدون') as phone,
                    (COALESCE(o.total_cost, 0) - COALESCE(p.total_paid, 0)) AS balance
                FROM labs l
                LEFT JOIN (
                    SELECT lab_id, SUM(total_cost) AS total_cost 
                    FROM lab_orders 
                    GROUP BY lab_id
                ) o ON l.lab_id = o.lab_id
                LEFT JOIN (
                    SELECT lab_id, SUM(amount_paid) AS total_paid 
                    FROM lab_payments 
                    GROUP BY lab_id
                ) p ON l.lab_id = p.lab_id
                ORDER BY l.lab_name ASC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"[خطأ في جلب قائمة المعامل للكشوفات]: {e}")
            return []

    def get_staff_list(self):
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT emp_id, full_name, COALESCE(phone, 'بدون') as phone, COALESCE(salary, 0) as salary
                FROM employees
                ORDER BY emp_id DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"[خطأ في جلب قائمة الموظفين للكشوفات]: {e}")
            return []

    # =========================================================================
    # 2. كشف حساب المريض
    # =========================================================================
    def get_patient_statement(self, patient_id, start_date=None, end_date=None):
        conn = self.db.get_connection()
        if not conn:
            return None, [], {}

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT patient_id, full_name, phone, address, gender, date_of_birth, medical_history
                FROM patients
                WHERE patient_id = %s;
            """, (patient_id,))
            patient_row = cursor.fetchone()
            if not patient_row:
                cursor.close()
                conn.close()
                return None, [], {}

            patient_info = {
                "patient_id": patient_row[0],
                "full_name": patient_row[1],
                "phone": patient_row[2] or "غير مسجل",
                "address": patient_row[3] or "غير محدد",
                "gender": patient_row[4] or "غير محدد",
                "dob": str(patient_row[5] or ""),
                "medical_history": patient_row[6] or "سليم"
            }

            cursor.execute("""
                SELECT treatment_id, treatment_type, description, cost, treatment_date
                FROM treatments
                WHERE patient_id = %s
                ORDER BY treatment_id ASC;
            """, (patient_id,))
            treatments = cursor.fetchall()
            treatments_map = {}
            for idx, tr in enumerate(treatments):
                treatments_map[tr[0]] = {
                    "session_num": idx + 1,
                    "type": tr[1] or "جلسة علاجية",
                    "desc": tr[2] or "",
                    "cost": float(tr[3] or 0),
                    "date": str(tr[4] or "")
                }

            query_acc = """
                SELECT a.invoice_id, a.treatment_id, t.treatment_type, t.description,
                       a.total_amount, a.paid_amount, a.remaining_amount,
                       a.payment_date, a.payment_status, a.payment_method
                FROM patient_accounts a
                LEFT JOIN treatments t ON a.treatment_id = t.treatment_id
                WHERE a.patient_id = %s
            """
            params = [patient_id]

            if start_date and end_date:
                query_acc += " AND a.payment_date BETWEEN %s AND %s"
                params.extend([start_date, end_date])

            query_acc += " ORDER BY a.payment_date ASC, a.invoice_id ASC;"
            cursor.execute(query_acc, tuple(params))
            acc_rows = cursor.fetchall()

            cursor.execute("""
                SELECT 
                    COALESCE(SUM(total_amount), 0) AS total_cost,
                    COALESCE(SUM(paid_amount), 0) AS total_paid,
                    COALESCE(SUM(total_amount - paid_amount), 0) AS total_debt
                FROM patient_accounts
                WHERE patient_id = %s;
            """, (patient_id,))
            totals_res = cursor.fetchone()
            total_cost_all = float(totals_res[0] or 0)
            total_paid_all = float(totals_res[1] or 0)
            net_debt_all = float(totals_res[2] or 0)

            statement_items = []
            period_total_cost = 0.0
            period_total_paid = 0.0
            running_remain = 0.0

            for r in acc_rows:
                inv_id, t_id, t_type, t_desc, total_amt, paid_amt, remain_amt, p_date, status, method = r
                cost = float(total_amt or 0)
                paid = float(paid_amt or 0)

                row_net_change = (cost - paid) if t_id else (-paid)
                running_remain += row_net_change
                remain = max(0.0, running_remain) if running_remain > 0 else running_remain

                period_total_cost += cost
                period_total_paid += paid

                if t_id and t_id in treatments_map:
                    s_info = treatments_map[t_id]
                    type_str = f"جلسة علاجية #{s_info['session_num']} ({s_info['type']})"
                    details_str = s_info['desc'] if s_info['desc'] else (t_desc or "معالجة طبية")
                elif t_id:
                    type_str = f"فاتورة علاجية #{t_id} ({t_type or 'علاج'})"
                    details_str = t_desc or "إجراء طبي"
                else:
                    type_str = "سند قبض وسداد دين"
                    details_str = f"سداد دفعة مالية حسابية ({method or 'نقداً'})"

                statement_items.append({
                    "id": inv_id,
                    "date": str(p_date or ""),
                    "type": type_str,
                    "details": details_str,
                    "cost": cost,
                    "paid": paid,
                    "remain": remain,
                    "method": method or "نقداً",
                    "status": status or "Paid"
                })

            summary = {
                "period": f"{start_date} إلى {end_date}" if start_date and end_date else "كامل السجل المالي التراكمي",
                "total_cost": total_cost_all,
                "total_paid": total_paid_all,
                "net_debt": net_debt_all,
                "period_cost": period_total_cost,
                "period_paid": period_total_paid,
                "transactions_count": len(statement_items)
            }

            cursor.close()
            conn.close()
            return patient_info, statement_items, summary

        except Error as e:
            print(f"[خطأ في استخراج كشف حساب المريض]: {e}")
            return None, [], {}

    # =========================================================================
    # 3. كشف حساب المعمل
    # =========================================================================
    def get_lab_statement(self, lab_id, start_date=None, end_date=None):
        conn = self.db.get_connection()
        if not conn:
            return None, [], [], {}

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT lab_id, lab_name, address, phone FROM labs WHERE lab_id = %s;", (lab_id,))
            lab_row = cursor.fetchone()
            if not lab_row:
                cursor.close()
                conn.close()
                return None, [], [], {}

            lab_info = {
                "lab_id": lab_row[0],
                "lab_name": lab_row[1],
                "address": lab_row[2] or "غير محدد",
                "phone": lab_row[3] or "غير مسجل"
            }

            query_orders = """
                SELECT o.order_id, o.receive_date, o.delivery_date, 
                       COALESCE(p.full_name, 'مريض عام') as patient_name,
                       o.work_type, o.total_cost, COALESCE(o.invoice_id, 'بدون'), COALESCE(o.notes, '')
                FROM lab_orders o
                LEFT JOIN patients p ON o.patient_id = p.patient_id
                WHERE o.lab_id = %s
            """
            p_orders = [lab_id]
            if start_date and end_date:
                query_orders += " AND o.receive_date BETWEEN %s AND %s"
                p_orders.extend([start_date, end_date])
            query_orders += " ORDER BY o.receive_date ASC, o.order_id ASC;"
            cursor.execute(query_orders, tuple(p_orders))
            order_rows = cursor.fetchall()

            orders_list = []
            orders_total = 0.0
            for o in order_rows:
                cost = float(o[5] or 0)
                orders_total += cost
                orders_list.append({
                    "order_id": o[0],
                    "receive_date": str(o[1] or ""),
                    "delivery_date": str(o[2] or ""),
                    "patient_name": o[3],
                    "work_type": o[4] or "تركيبة أسنان",
                    "cost": cost,
                    "invoice_id": str(o[6] or ""),
                    "notes": str(o[7] or "")
                })

            query_payments = """
                SELECT payment_id, payment_date, amount_paid, payment_method, 
                       COALESCE(receipt_no, payment_id) as voucher_no, 
                       COALESCE(notes, '')
                FROM lab_payments
                WHERE lab_id = %s
            """
            p_pays = [lab_id]
            if start_date and end_date:
                query_payments += " AND payment_date BETWEEN %s AND %s"
                p_pays.extend([start_date, end_date])
            query_payments += " ORDER BY payment_date ASC, payment_id ASC;"
            cursor.execute(query_payments, tuple(p_pays))
            pay_rows = cursor.fetchall()

            payments_list = []
            payments_total = 0.0
            for p in pay_rows:
                amount = float(p[2] or 0)
                payments_total += amount
                payments_list.append({
                    "payment_id": p[0],
                    "date": str(p[1] or ""),
                    "amount": amount,
                    "method": p[3] or "نقداً",
                    "voucher_no": str(p[4]),
                    "notes": str(p[5] or "")
                })

            cursor.execute("SELECT COALESCE(SUM(total_cost), 0) FROM lab_orders WHERE lab_id = %s;", (lab_id,))
            total_all_orders = float(cursor.fetchone()[0] or 0)

            cursor.execute("SELECT COALESCE(SUM(amount_paid), 0) FROM lab_payments WHERE lab_id = %s;", (lab_id,))
            total_all_payments = float(cursor.fetchone()[0] or 0)

            net_balance = total_all_orders - total_all_payments

            summary = {
                "period": f"{start_date} إلى {end_date}" if start_date and end_date else "كامل السجل التراكمي للمعمل",
                "total_orders_cost": total_all_orders,
                "total_paid_amount": total_all_payments,
                "net_balance": net_balance,
                "period_orders_cost": orders_total,
                "period_payments_paid": payments_total,
                "orders_count": len(orders_list),
                "payments_count": len(payments_list)
            }

            cursor.close()
            conn.close()
            return lab_info, orders_list, payments_list, summary

        except Error as e:
            print(f"[خطأ في استخراج كشف حساب المعمل]: {e}")
            return None, [], [], {}

    # =========================================================================
    # 4. كشف حساب الموظف
    # =========================================================================
    def get_staff_statement(self, emp_id, start_date=None, end_date=None):
        conn = self.db.get_connection()
        if not conn:
            return None, [], {}

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT emp_id, full_name, phone, address, job_title, salary, hire_date, status
                FROM employees
                WHERE emp_id = %s;
            """, (emp_id,))
            emp_row = cursor.fetchone()
            if not emp_row:
                cursor.close()
                conn.close()
                return None, [], {}

            emp_info = {
                "emp_id": emp_row[0],
                "full_name": emp_row[1],
                "phone": emp_row[2] or "غير مسجل",
                "address": emp_row[3] or "غير محدد",
                "job_title": emp_row[4] or "موظف",
                "base_salary": float(emp_row[5] or 0),
                "hire_date": str(emp_row[6] or ""),
                "status": emp_row[7] or "active"
            }

            query_trans = """
                SELECT transaction_id, transaction_type, amount, transaction_date, COALESCE(description, '')
                FROM employee_transactions
                WHERE emp_id = %s
            """
            params = [emp_id]

            if start_date and end_date:
                query_trans += " AND transaction_date BETWEEN %s AND %s"
                params.extend([start_date, end_date])

            query_trans += " ORDER BY transaction_date ASC, transaction_id ASC;"
            cursor.execute(query_trans, tuple(params))
            trans_rows = cursor.fetchall()

            transactions_list = []
            total_trans_amount = 0.0

            for tr in trans_rows:
                t_id, t_type, amount, t_date, desc = tr
                amt_val = float(amount or 0)
                total_trans_amount += amt_val
                transactions_list.append({
                    "transaction_id": t_id,
                    "type": t_type or "حركة مالية",
                    "amount": amt_val,
                    "date": str(t_date or ""),
                    "description": desc
                })

            net_salary = emp_info["base_salary"]
            for tr in transactions_list:
                t_type = tr["type"]
                amt = tr["amount"]
                if t_type in ["سلفة", "خصم", "سحب عهدة", "تسليم راتب"]:
                    net_salary -= amt
                elif t_type in ["مكافأة"]:
                    net_salary += amt

            summary = {
                "period": f"{start_date} إلى {end_date}" if start_date and end_date else "كامل السجل المالي التراكمي",
                "base_salary": emp_info["base_salary"],
                "total_transactions": total_trans_amount,
                "net_salary": net_salary,
                "transactions_count": len(transactions_list)
            }

            cursor.close()
            conn.close()
            return emp_info, transactions_list, summary

        except Error as e:
            print(f"[خطأ في استخراج كشف حساب الموظف]: {e}")
            return None, [], {}

    # =========================================================================
    # 5. كشف حساب المشتريات
    # =========================================================================
    def get_purchase_statement(self, supplier_id):
        conn = self.db.get_connection()
        if not conn:
            return None, [], {}
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT supplier_id, supplier_name, phone, address FROM suppliers WHERE supplier_id = %s;", (supplier_id,))
            supplier_info = cursor.fetchone()
            if not supplier_info:
                cursor.close()
                conn.close()
                return None, [], {}

            cursor.execute("""
                SELECT purchase_id, COALESCE(invoice_number, '-') as invoice_number, 
                       COALESCE(purchase_type, 'Cash') as purchase_type, 
                       description, purchase_date, total_amount, paid_amount, 
                       remaining_amount, payment_status, 
                       COALESCE(supplier_voucher_no, '-') as supplier_voucher_no
                FROM purchases
                WHERE supplier_id = %s
                ORDER BY purchase_date DESC, purchase_id DESC;
            """, (supplier_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            total_purchases = sum(float(r['total_amount'] or 0) for r in rows)
            total_paid = sum(float(r['paid_amount'] or 0) for r in rows)
            total_remain = sum(float(r['remaining_amount'] or 0) for r in rows)

            summary = {
                "total_purchases": total_purchases,
                "total_paid": total_paid,
                "total_remain": total_remain,
                "invoices_count": len(rows)
            }
            return supplier_info, rows, summary
        except Error as e:
            print(f"[خطأ في جلب كشف حساب المشتريات للمورد]: {e}")
            return None, [], {}

    # =========================================================================
    # 6. تصدير كشف حساب المريض PDF (مضبوط العرض 180 مم)
    # =========================================================================
    def export_patient_statement_pdf(self, patient_id, save_path, start_date=None, end_date=None, clinic_info=None):
        try:
            p_info, items, summary = self.get_patient_statement(patient_id, start_date, end_date)
            if not p_info:
                return False, "تعذر العثور على بيانات المريض المحددة."

            c_info = clinic_info or self.get_clinic_info()
            pdf, font_name, usable_w = self._init_pdf(c_info)
            self._draw_pdf_header(pdf, font_name, c_info, "📄 كشف حساب مالي تفصيلي للمريض", (14, 165, 233), usable_w)

            pdf.set_draw_color(203, 213, 225)
            pdf.set_line_width(0.3)
            pdf.set_fill_color(248, 250, 252)
            start_y = pdf.get_y()
            pdf.rect(15, start_y, usable_w, 24, "DF")

            pdf.set_font(font_name, "B", 10.5)
            pdf.set_text_color(15, 23, 42)
            pdf.set_xy(17, start_y + 3)
            pdf.cell(86, 6, txt=_fit_text(pdf, f"رقم الملف: #{p_info['patient_id']}", 86), align="R")
            pdf.cell(90, 6, txt=_fit_text(pdf, f"اسم المريض: {p_info['full_name']}", 90), align="R")

            pdf.set_xy(17, start_y + 9)
            pdf.set_font(font_name, "", 10)
            pdf.cell(86, 6, txt=_fit_text(pdf, f"العنوان: {p_info['address']}", 86), align="R")
            pdf.cell(90, 6, txt=_fit_text(pdf, f"رقم الهاتف: {p_info['phone']}", 90), align="R")

            pdf.set_xy(17, start_y + 15)
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            pdf.cell(86, 6, txt=_fit_text(pdf, f"تاريخ استخراج الكشف: {today_str}", 86), align="R")
            pdf.cell(90, 6, txt=_fit_text(pdf, f"فترة الكشف: {summary['period']}", 90), align="R")
            pdf.set_y(start_y + 28)

            # 3 بطاقات: 58 + 3 + 58 + 3 + 58 = 180 مم
            col_w = 58
            pdf.set_x(15)
            pdf.set_font(font_name, "B", 9.5)
            pdf.set_fill_color(238, 242, 255)
            pdf.set_text_color(79, 70, 229)
            pdf.cell(col_w, 8, txt=_fit_text(pdf, f"إجمالي العلاجات: {summary['total_cost']:,.2f} ر.ي", col_w), border=1, align="C", fill=True)
            pdf.cell(3, 8, "", ln=False)

            pdf.set_fill_color(236, 253, 245)
            pdf.set_text_color(16, 185, 129)
            pdf.cell(col_w, 8, txt=_fit_text(pdf, f"إجمالي المسدد: {summary['total_paid']:,.2f} ر.ي", col_w), border=1, align="C", fill=True)
            pdf.cell(3, 8, "", ln=False)

            if summary['net_debt'] > 0:
                pdf.set_fill_color(255, 241, 242)
                pdf.set_text_color(225, 29, 72)
                debt_label = f"المديونية المتبقية: {summary['net_debt']:,.2f} ر.ي"
            else:
                pdf.set_fill_color(240, 253, 244)
                pdf.set_text_color(22, 101, 52)
                debt_label = "الحساب خالص بالكامل (0.00)"

            pdf.cell(col_w, 8, txt=_fit_text(pdf, debt_label, col_w), border=1, align="C", fill=True)
            pdf.ln(12)

            # مجموع الأعمدة: 25 + 25 + 25 + 69 + 22 + 14 = 180 مم
            headers = ["المتبقي", "المسدد", "التكلفة", "البيان وتفاصيل الإجراء", "التاريخ", "القيد"]
            widths = [25, 25, 25, 69, 22, 14]
            self._draw_table_header(pdf, font_name, headers, widths)

            pdf.set_text_color(30, 41, 59)
            pdf.set_font(font_name, "", 8.5)
            row_alt = False
            for it in items:
                if pdf.get_y() > 265:
                    pdf.add_page()
                    self._draw_table_header(pdf, font_name, headers, widths)
                    pdf.set_text_color(30, 41, 59)
                    pdf.set_font(font_name, "", 8.5)

                pdf.set_x(15)
                pdf.set_fill_color(248, 250, 252) if row_alt else pdf.set_fill_color(255, 255, 255)
                row_alt = not row_alt
                pdf.cell(widths[0], 7, txt=fix_ar(f"{it['remain']:,.2f}"), border=1, align="C", fill=True)
                pdf.cell(widths[1], 7, txt=fix_ar(f"{it['paid']:,.2f}"), border=1, align="C", fill=True)
                pdf.cell(widths[2], 7, txt=fix_ar(f"{it['cost']:,.2f}"), border=1, align="C", fill=True)
                pdf.cell(widths[3], 7, txt=_fit_text(pdf, f"{it['type']} - {it['details']}", widths[3]), border=1, align="R", fill=True)
                pdf.cell(widths[4], 7, txt=fix_ar(it['date']), border=1, align="C", fill=True)
                pdf.cell(widths[5], 7, txt=fix_ar(f"#{it['id']}"), border=1, align="C", fill=True)
                pdf.ln()

            if not items:
                pdf.set_x(15)
                pdf.cell(usable_w, 10, txt=fix_ar("لا توجد حركات مالية مسجلة لهذا المريض ضمن الفترة المحددة."), border=1, align="C")
                pdf.ln()

            pdf.set_x(15)
            pdf.set_font(font_name, "B", 9)
            pdf.set_fill_color(226, 232, 240)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(widths[0], 8, txt=fix_ar(f"{summary['net_debt']:,.2f}"), border=1, align="C", fill=True)
            pdf.cell(widths[1], 8, txt=fix_ar(f"{summary['total_paid']:,.2f}"), border=1, align="C", fill=True)
            pdf.cell(widths[2], 8, txt=fix_ar(f"{summary['total_cost']:,.2f}"), border=1, align="C", fill=True)
            pdf.cell(sum(widths[3:]), 8, txt=fix_ar("المجموع والإجمالي العام (ر.ي):"), border=1, align="R", fill=True)
            pdf.ln(14)

            self._draw_signatures(pdf, font_name, usable_w, "ختم العيادة الرسمي")
            pdf.output(save_path)
            return True, f"تم استخراج كشف حساب المريض بنجاح:\n{save_path}"
        except Exception as ex:
            return False, f"فشل تصدير كشف حساب المريض إلى PDF: {ex}"

    # =========================================================================
    # 7. تصدير كشف حساب المريض Excel
    # =========================================================================
    def export_patient_statement_excel(self, patient_id, save_path, start_date=None, end_date=None, clinic_info=None):
        try:
            p_info, items, summary = self.get_patient_statement(patient_id, start_date, end_date)
            if not p_info:
                return False, "تعذر العثور على بيانات المريض المحددة."

            c_info = clinic_info or self.get_clinic_info()
            rows_data = []
            for it in items:
                rows_data.append({
                    "رقم القيد": it["id"],
                    "التاريخ": it["date"],
                    "نوع الحركة": it["type"],
                    "البيان والتفاصيل": it["details"],
                    "التكلفة / الاستحقاق (ر.ي)": it["cost"],
                    "المبلغ المسدد (ر.ي)": it["paid"],
                    "المتبقي (ر.ي)": it["remain"],
                    "طريقة السداد": it["method"],
                    "الحالة": it["status"]
                })
            df_items = pd.DataFrame(rows_data)

            summary_data = [
                {"البيان": "اسم العيادة", "القيمة": c_info.get("name", "عيادة تيسير لطب الأسنان")},
                {"البيان": "اسم المريض", "القيمة": p_info["full_name"]},
                {"البيان": "رقم الملف", "القيمة": p_info["patient_id"]},
                {"البيان": "رقم الهاتف", "القيمة": p_info["phone"]},
                {"البيان": "العنوان", "القيمة": p_info["address"]},
                {"البيان": "فترة الكشف", "القيمة": summary["period"]},
                {"البيان": "إجمالي تكلفة العلاجات (ر.ي)", "القيمة": summary["total_cost"]},
                {"البيان": "إجمالي المبالغ المسددة (ر.ي)", "القيمة": summary["total_paid"]},
                {"البيان": "صافي المديونية المتبقية (ر.ي)", "القيمة": summary["net_debt"]},
                {"البيان": "تاريخ استخراج الكشف", "القيمة": datetime.date.today().strftime("%Y-%m-%d")}
            ]
            df_summary = pd.DataFrame(summary_data)

            with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
                df_summary.to_excel(writer, sheet_name="ملخص كشف الحساب", index=False)
                df_items.to_excel(writer, sheet_name="حركات وسجل العمليات", index=False)
                for sheet in writer.sheets.values():
                    sheet.sheet_view.rightToLeft = True

            return True, f"تم تصدير كشف حساب المريض إلى Excel بنجاح:\n{save_path}"
        except Exception as ex:
            return False, f"فشل تصدير كشف حساب المريض إلى Excel: {ex}"

    # =========================================================================
    # 8. تصدير كشف حساب المعمل PDF (مضبوط العرض 180 مم)
    # =========================================================================
    def export_lab_statement_pdf(self, lab_id, save_path, start_date=None, end_date=None, clinic_info=None):
        try:
            lab_info, orders, payments, summary = self.get_lab_statement(lab_id, start_date, end_date)
            if not lab_info:
                return False, "تعذر العثور على بيانات المعمل المحدد."

            c_info = clinic_info or self.get_clinic_info()
            pdf, font_name, usable_w = self._init_pdf(c_info)
            self._draw_pdf_header(pdf, font_name, c_info, "🔬 كشف حساب مالي تفصيلي للمعمل المتعاقد", (16, 185, 129), usable_w)

            pdf.set_draw_color(203, 213, 225)
            pdf.set_line_width(0.3)
            pdf.set_fill_color(248, 250, 252)
            start_y = pdf.get_y()
            pdf.rect(15, start_y, usable_w, 24, "DF")

            pdf.set_font(font_name, "B", 10.5)
            pdf.set_text_color(15, 23, 42)
            pdf.set_xy(17, start_y + 3)
            pdf.cell(86, 6, txt=_fit_text(pdf, f"معرّف المعمل: #{lab_info['lab_id']}", 86), align="R")
            pdf.cell(90, 6, txt=_fit_text(pdf, f"اسم المعمل: {lab_info['lab_name']}", 90), align="R")

            pdf.set_xy(17, start_y + 9)
            pdf.set_font(font_name, "", 10)
            pdf.cell(86, 6, txt=_fit_text(pdf, f"العنوان: {lab_info['address']}", 86), align="R")
            pdf.cell(90, 6, txt=_fit_text(pdf, f"هاتف المعمل: {lab_info['phone']}", 90), align="R")

            pdf.set_xy(17, start_y + 15)
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            pdf.cell(86, 6, txt=_fit_text(pdf, f"تاريخ استخراج الكشف: {today_str}", 86), align="R")
            pdf.cell(90, 6, txt=_fit_text(pdf, f"فترة الكشف: {summary['period']}", 90), align="R")
            pdf.set_y(start_y + 28)

            # 3 بطاقات: 58 + 3 + 58 + 3 + 58 = 180 مم
            col_w = 58
            pdf.set_x(15)
            pdf.set_font(font_name, "B", 9.5)
            pdf.set_fill_color(238, 242, 255)
            pdf.set_text_color(79, 70, 229)
            pdf.cell(col_w, 8, txt=_fit_text(pdf, f"إجمالي الأوامر: {summary['total_orders_cost']:,.2f} ر.ي", col_w), border=1, align="C", fill=True)
            pdf.cell(3, 8, "", ln=False)

            pdf.set_fill_color(236, 253, 245)
            pdf.set_text_color(16, 185, 129)
            pdf.cell(col_w, 8, txt=_fit_text(pdf, f"إجمالي المسدد: {summary['total_paid_amount']:,.2f} ر.ي", col_w), border=1, align="C", fill=True)
            pdf.cell(3, 8, "", ln=False)

            if summary['net_balance'] > 0:
                pdf.set_fill_color(255, 241, 242)
                pdf.set_text_color(225, 29, 72)
                lab_bal_lbl = f"المستحق للمعمل: {summary['net_balance']:,.2f} ر.ي"
            else:
                pdf.set_fill_color(240, 253, 244)
                pdf.set_text_color(22, 101, 52)
                lab_bal_lbl = "الحساب خالص بالكامل (0.00)"

            pdf.cell(col_w, 8, txt=_fit_text(pdf, lab_bal_lbl, col_w), border=1, align="C", fill=True)
            pdf.ln(12)

            pdf.set_x(15)
            pdf.set_font(font_name, "B", 11)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(usable_w, 7, txt=fix_ar("📋 أولاً: سجل أوامر العمل والتركيبات الطبية"), ln=True, align="R")
            pdf.ln(1)

            # مجموع الأعمدة: 28 + 20 + 44 + 51 + 23 + 14 = 180 مم
            headers_ord = ["التكلفة (ر.ي)", "الفاتورة", "المريض", "نوع التركيبة / العمل", "تاريخ الاستلام", "الأمر"]
            widths_ord = [28, 20, 44, 51, 23, 14]
            self._draw_table_header(pdf, font_name, headers_ord, widths_ord, font_size=8.5)

            pdf.set_text_color(30, 41, 59)
            pdf.set_font(font_name, "", 8.5)
            row_alt = False
            for o in orders:
                if pdf.get_y() > 265:
                    pdf.add_page()
                    self._draw_table_header(pdf, font_name, headers_ord, widths_ord, font_size=8.5)
                    pdf.set_text_color(30, 41, 59)
                    pdf.set_font(font_name, "", 8.5)

                pdf.set_x(15)
                pdf.set_fill_color(248, 250, 252) if row_alt else pdf.set_fill_color(255, 255, 255)
                row_alt = not row_alt
                pdf.cell(widths_ord[0], 6.5, txt=fix_ar(f"{o['cost']:,.2f}"), border=1, align="C", fill=True)
                pdf.cell(widths_ord[1], 6.5, txt=_fit_text(pdf, o['invoice_id'], widths_ord[1]), border=1, align="C", fill=True)
                pdf.cell(widths_ord[2], 6.5, txt=_fit_text(pdf, o['patient_name'], widths_ord[2]), border=1, align="R", fill=True)
                pdf.cell(widths_ord[3], 6.5, txt=_fit_text(pdf, o['work_type'], widths_ord[3]), border=1, align="R", fill=True)
                pdf.cell(widths_ord[4], 6.5, txt=fix_ar(o['receive_date']), border=1, align="C", fill=True)
                pdf.cell(widths_ord[5], 6.5, txt=fix_ar(f"#{o['order_id']}"), border=1, align="C", fill=True)
                pdf.ln()

            if not orders:
                pdf.set_x(15)
                pdf.cell(usable_w, 8, txt=fix_ar("لا توجد أوامر عمل مسجلة للمعمل في الفترة المحددة."), border=1, align="C")
                pdf.ln()

            pdf.ln(6)
            pdf.set_x(15)
            pdf.set_font(font_name, "B", 11)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(usable_w, 7, txt=fix_ar("💵 ثانياً: سجل الدفعات وسندات الصرف المسددة للمعمل"), ln=True, align="R")
            pdf.ln(1)

            # مجموع الأعمدة: 34 + 74 + 30 + 25 + 17 = 180 مم
            headers_pay = ["المبلغ المسدد (ر.ي)", "ملاحظات وبيان الصرف", "طريقة السداد", "تاريخ السداد", "السند"]
            widths_pay = [34, 74, 30, 25, 17]
            self._draw_table_header(pdf, font_name, headers_pay, widths_pay, fill_rgb=(16, 185, 129), font_size=8.5)

            pdf.set_text_color(30, 41, 59)
            pdf.set_font(font_name, "", 8.5)
            row_alt = False
            for p in payments:
                if pdf.get_y() > 265:
                    pdf.add_page()
                    self._draw_table_header(pdf, font_name, headers_pay, widths_pay, fill_rgb=(16, 185, 129), font_size=8.5)
                    pdf.set_text_color(30, 41, 59)
                    pdf.set_font(font_name, "", 8.5)

                pdf.set_x(15)
                pdf.set_fill_color(248, 250, 252) if row_alt else pdf.set_fill_color(255, 255, 255)
                row_alt = not row_alt
                pdf.cell(widths_pay[0], 6.5, txt=fix_ar(f"{p['amount']:,.2f}"), border=1, align="C", fill=True)
                pdf.cell(widths_pay[1], 6.5, txt=_fit_text(pdf, p['notes'] or "دفعة نقدية", widths_pay[1]), border=1, align="R", fill=True)
                pdf.cell(widths_pay[2], 6.5, txt=_fit_text(pdf, p['method'], widths_pay[2]), border=1, align="C", fill=True)
                pdf.cell(widths_pay[3], 6.5, txt=fix_ar(p['date']), border=1, align="C", fill=True)
                pdf.cell(widths_pay[4], 6.5, txt=fix_ar(f"#{p['voucher_no']}"), border=1, align="C", fill=True)
                pdf.ln()

            if not payments:
                pdf.set_x(15)
                pdf.cell(usable_w, 8, txt=fix_ar("لا توجد دفعات مالية مسددة للمعمل في الفترة المحددة."), border=1, align="C")
                pdf.ln()

            pdf.ln(10)
            self._draw_signatures(pdf, font_name, usable_w, "توقيع ومصادقة مندوب المعمل")
            pdf.output(save_path)
            return True, f"تم استخراج كشف حساب المعمل بنجاح:\n{save_path}"
        except Exception as ex:
            return False, f"فشل تصدير كشف حساب المعمل إلى PDF: {ex}"

    # =========================================================================
    # 9. تصدير كشف حساب المعمل Excel
    # =========================================================================
    def export_lab_statement_excel(self, lab_id, save_path, start_date=None, end_date=None, clinic_info=None):
        try:
            lab_info, orders, payments, summary = self.get_lab_statement(lab_id, start_date, end_date)
            if not lab_info:
                return False, "تعذر العثور على بيانات المعمل المحدد."

            c_info = clinic_info or self.get_clinic_info()
            orders_rows = []
            for o in orders:
                orders_rows.append({
                    "رقم الأمر": o["order_id"],
                    "تاريخ الاستلام": o["receive_date"],
                    "تاريخ التسليم المتوقع": o["delivery_date"],
                    "اسم المريض": o["patient_name"],
                    "نوع التركيبة / العمل": o["work_type"],
                    "رقم الفاتورة": o["invoice_id"],
                    "التكلفة المستحقة (ر.ي)": o["cost"],
                    "ملاحظات": o["notes"]
                })
            df_orders = pd.DataFrame(orders_rows)

            payments_rows = []
            for p in payments:
                payments_rows.append({
                    "رقم السند": p["payment_id"],
                    "تاريخ السند": p["date"],
                    "المبلغ المسدد (ر.ي)": p["amount"],
                    "طريقة السداد": p["method"],
                    "البيان والملاحظات": p["notes"]
                })
            df_payments = pd.DataFrame(payments_rows)

            summary_rows = [
                {"البيان": "اسم العيادة", "القيمة": c_info.get("name", "عيادة تيسير لطب الأسنان")},
                {"البيان": "اسم المعمل", "القيمة": lab_info["lab_name"]},
                {"البيان": "رقم الهاتف", "القيمة": lab_info["phone"]},
                {"البيان": "العنوان", "القيمة": lab_info["address"]},
                {"البيان": "فترة التقرير", "القيمة": summary["period"]},
                {"البيان": "إجمالي تكلفة أوامر العمل (ر.ي)", "القيمة": summary["total_orders_cost"]},
                {"البيان": "إجمالي المدفوعات المسددة (ر.ي)", "القيمة": summary["total_paid_amount"]},
                {"البيان": "صافي الرصيد المستحق للمعمل (ر.ي)", "القيمة": summary["net_balance"]},
                {"البيان": "عدد أوامر العمل", "القيمة": summary["orders_count"]},
                {"البيان": "عدد سندات الصرف", "القيمة": summary["payments_count"]},
                {"البيان": "تاريخ استخراج الكشف", "القيمة": datetime.date.today().strftime("%Y-%m-%d")}
            ]
            df_summary = pd.DataFrame(summary_rows)

            with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
                df_summary.to_excel(writer, sheet_name="الملخص المالي العام", index=False)
                df_orders.to_excel(writer, sheet_name="أوامر العمل والتركيبات", index=False)
                df_payments.to_excel(writer, sheet_name="المدفوعات وسندات الصرف", index=False)
                for sheet in writer.sheets.values():
                    sheet.sheet_view.rightToLeft = True

            return True, f"تم تصدير كشف حساب المعمل إلى Excel بنجاح:\n{save_path}"
        except Exception as ex:
            return False, f"فشل تصدير كشف حساب المعمل إلى Excel: {ex}"

    # =========================================================================
    # 10. تصدير كشف حساب المشتريات PDF (مضبوط العرض 180 مم بالكامل)
    # =========================================================================
    def export_purchase_statement_pdf(self, supplier_id, save_path, clinic_info=None):
        try:
            sup_info, rows, summary = self.get_purchase_statement(supplier_id)
            if not sup_info:
                return False, "تعذر العثور على بيانات المورد المحدد."

            c_info = clinic_info or self.get_clinic_info()
            pdf, font_name, usable_w = self._init_pdf(c_info)
            self._draw_pdf_header(pdf, font_name, c_info, "📦 كشف حساب مالي تفصيلي لفواتير المشتريات", (79, 70, 229), usable_w)

            # مجموع الأعمدة = 21 + 21 + 21 + 18 + 49 + 20 + 14 + 16 = 180 مم بالضبط
            widths_pur = [21, 21, 21, 18, 49, 20, 14, 16]

            pdf.set_draw_color(203, 213, 225)
            pdf.set_line_width(0.3)
            pdf.set_fill_color(248, 250, 252)
            start_y = pdf.get_y()
            pdf.rect(15, start_y, usable_w, 20, "DF")

            pdf.set_font(font_name, "B", 10.5)
            pdf.set_text_color(15, 23, 42)
            pdf.set_xy(17, start_y + 3)
            pdf.cell(86, 6, txt=_fit_text(pdf, f"معرف المورد: #{sup_info['supplier_id']}", 86), align="R")
            pdf.cell(90, 6, txt=_fit_text(pdf, f"اسم المورد: {sup_info['supplier_name']}", 90), align="R")

            pdf.set_xy(17, start_y + 11)
            pdf.set_font(font_name, "", 10)
            pdf.cell(86, 6, txt=_fit_text(pdf, f"رقم الهاتف: {sup_info.get('phone', 'بدون')}", 86), align="R")
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            pdf.cell(90, 6, txt=_fit_text(pdf, f"تاريخ التقرير: {today_str}", 90), align="R")
            pdf.set_y(start_y + 24)

            headers_pur = ["المتبقي", "المسدد", "الإجمالي", "رقم السند", "البيان والتفاصيل", "التاريخ", "النوع", "الفاتورة"]
            self._draw_table_header(pdf, font_name, headers_pur, widths_pur, font_size=8.5)

            pdf.set_text_color(30, 41, 59)
            pdf.set_font(font_name, "", 8)
            row_alt = False
            for r in rows:
                if pdf.get_y() > 265:
                    pdf.add_page()
                    self._draw_table_header(pdf, font_name, headers_pur, widths_pur, font_size=8.5)
                    pdf.set_text_color(30, 41, 59)
                    pdf.set_font(font_name, "", 8)

                pdf.set_x(15)
                pdf.set_fill_color(248, 250, 252) if row_alt else pdf.set_fill_color(255, 255, 255)
                row_alt = not row_alt

                p_type_txt = "آجل" if r['purchase_type'] == 'Credit' else "نقداً"

                pdf.cell(widths_pur[0], 7, txt=fix_ar(f"{float(r['remaining_amount'] or 0):,.2f}"), border=1, align="C", fill=True)
                pdf.cell(widths_pur[1], 7, txt=fix_ar(f"{float(r['paid_amount'] or 0):,.2f}"), border=1, align="C", fill=True)
                pdf.cell(widths_pur[2], 7, txt=fix_ar(f"{float(r['total_amount'] or 0):,.2f}"), border=1, align="C", fill=True)
                pdf.cell(widths_pur[3], 7, txt=_fit_text(pdf, str(r['supplier_voucher_no']), widths_pur[3]), border=1, align="C", fill=True)
                pdf.cell(widths_pur[4], 7, txt=_fit_text(pdf, r['description'] or "مشتريات عامة", widths_pur[4]), border=1, align="R", fill=True)
                pdf.cell(widths_pur[5], 7, txt=fix_ar(str(r['purchase_date'])), border=1, align="C", fill=True)
                pdf.cell(widths_pur[6], 7, txt=fix_ar(p_type_txt), border=1, align="C", fill=True)
                pdf.cell(widths_pur[7], 7, txt=_fit_text(pdf, str(r['invoice_number']), widths_pur[7]), border=1, align="C", fill=True)
                pdf.ln()

            if not rows:
                pdf.set_x(15)
                pdf.cell(usable_w, 8, txt=fix_ar("لا توجد فواتير مشتريات مسجلة لهذا المورد."), border=1, align="C")
                pdf.ln()

            pdf.set_x(15)
            pdf.set_font(font_name, "B", 8.5)
            pdf.set_fill_color(226, 232, 240)
            pdf.set_text_color(15, 23, 42)

            pdf.cell(widths_pur[0], 8, txt=fix_ar(f"{summary['total_remain']:,.2f}"), border=1, align="C", fill=True)
            pdf.cell(widths_pur[1], 8, txt=fix_ar(f"{summary['total_paid']:,.2f}"), border=1, align="C", fill=True)
            pdf.cell(widths_pur[2], 8, txt=fix_ar(f"{summary['total_purchases']:,.2f}"), border=1, align="C", fill=True)
            pdf.cell(sum(widths_pur[3:]), 8, txt=fix_ar("المجاميع العامة (ر.ي):"), border=1, align="R", fill=True)
            pdf.ln(14)

            self._draw_signatures(pdf, font_name, usable_w, "توقيع ومصادقة المورد")
            pdf.output(save_path)
            return True, f"تم استخراج كشف حساب المشتريات PDF بنجاح:\n{save_path}"
        except Exception as ex:
            return False, f"فشل تصدير كشف حساب المشتريات إلى PDF: {ex}"

    # =========================================================================
    # 11. تصدير كشف حساب المشتريات Excel
    # =========================================================================
    def export_purchase_statement_excel(self, supplier_id, save_path, clinic_info=None):
        try:
            sup_info, rows, summary = self.get_purchase_statement(supplier_id)
            if not sup_info:
                return False, "تعذر العثور على بيانات المورد المحدد."

            c_info = clinic_info or self.get_clinic_info()
            pur_rows = []
            for r in rows:
                pur_rows.append({
                    "رقم الفاتورة": r["invoice_number"],
                    "نوع الفاتورة": "آجل" if r["purchase_type"] == 'Credit' else "نقداً",
                    "رقم سند المورد": r["supplier_voucher_no"],
                    "تاريخ الفاتورة": str(r["purchase_date"]),
                    "البيان والتفاصيل": r["description"],
                    "إجمالي الفاتورة (ر.ي)": float(r["total_amount"] or 0),
                    "المبلغ المسدد (ر.ي)": float(r["paid_amount"] or 0),
                    "المتبقي (ر.ي)": float(r["remaining_amount"] or 0),
                    "حالة السداد": r["payment_status"]
                })
            df_pur = pd.DataFrame(pur_rows)

            summary_rows = [
                {"البيان": "اسم العيادة", "القيمة": c_info.get("name", "عيادة تيسير لطب الأسنان")},
                {"البيان": "اسم المورد", "القيمة": sup_info["supplier_name"]},
                {"البيان": "رقم الهاتف", "القيمة": sup_info.get("phone", "بدون")},
                {"البيان": "العنوان", "القيمة": sup_info.get("address", "غير محدد")},
                {"البيان": "إجمالي قيمة المشتريات (ر.ي)", "القيمة": summary["total_purchases"]},
                {"البيان": "إجمالي المبالغ المسددة (ر.ي)", "القيمة": summary["total_paid"]},
                {"البيان": "صافي المتبقي على المورد (ر.ي)", "القيمة": summary["total_remain"]},
                {"البيان": "عدد الفواتير المسجلة", "القيمة": summary["invoices_count"]},
                {"البيان": "تاريخ استخراج التقرير", "القيمة": datetime.date.today().strftime("%Y-%m-%d")}
            ]
            df_summary = pd.DataFrame(summary_rows)

            with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
                df_summary.to_excel(writer, sheet_name="الملخص المالي للمشتريات", index=False)
                df_pur.to_excel(writer, sheet_name="سجل فواتير المشتريات", index=False)
                for sheet in writer.sheets.values():
                    sheet.sheet_view.rightToLeft = True

            return True, f"تم استخراج كشف حساب المشتريات Excel بنجاح:\n{save_path}"
        except Exception as ex:
            return False, f"فشل تصدير كشف حساب المشتريات إلى Excel: {ex}"

    # =========================================================================
    # 12. تصدير كشف حساب الموظف PDF (مضبوط العرض 180 مم)
    # =========================================================================
    def export_staff_statement_pdf(self, emp_id, save_path, start_date=None, end_date=None, clinic_info=None):
        try:
            emp_info, transactions, summary = self.get_staff_statement(emp_id, start_date, end_date)
            if not emp_info:
                return False, "تعذر العثور على بيانات الموظف المحدد."

            c_info = clinic_info or self.get_clinic_info()
            pdf, font_name, usable_w = self._init_pdf(c_info)
            self._draw_pdf_header(pdf, font_name, c_info, "👥 كشف حساب مالي تفصيلي للموظف", (99, 102, 241), usable_w)

            # مجموع الأعمدة: 25 + 25 + 25 + 69 + 22 + 14 = 180 مم
            widths_tr = [25, 25, 25, 69, 22, 14]

            pdf.set_draw_color(203, 213, 225)
            pdf.set_line_width(0.3)
            pdf.set_fill_color(248, 250, 252)
            start_y = pdf.get_y()
            pdf.rect(15, start_y, usable_w, 24, "DF")

            pdf.set_font(font_name, "B", 10.5)
            pdf.set_text_color(15, 23, 42)
            pdf.set_xy(17, start_y + 3)
            pdf.cell(86, 6, txt=_fit_text(pdf, f"رقم الموظف: #{emp_info['emp_id']}", 86), align="R")
            pdf.cell(90, 6, txt=_fit_text(pdf, f"اسم الموظف: {emp_info['full_name']}", 90), align="R")

            pdf.set_xy(17, start_y + 9)
            pdf.set_font(font_name, "", 10)
            pdf.cell(86, 6, txt=_fit_text(pdf, f"الوظيفة: {emp_info['job_title']}", 86), align="R")
            pdf.cell(90, 6, txt=_fit_text(pdf, f"رقم الهاتف: {emp_info['phone']}", 90), align="R")

            pdf.set_xy(17, start_y + 15)
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            pdf.cell(86, 6, txt=_fit_text(pdf, f"تاريخ استخراج الكشف: {today_str}", 86), align="R")
            pdf.cell(90, 6, txt=_fit_text(pdf, f"فترة الكشف: {summary['period']}", 90), align="R")
            pdf.set_y(start_y + 28)

            headers_tr = ["الرصيد", "له (دائن)", "عليه (مدين)", "البيان وتفاصيل الحركة", "التاريخ", "الرقم"]
            self._draw_table_header(pdf, font_name, headers_tr, widths_tr, font_size=8.5)

            base_sal = float(emp_info['base_salary'] or 0)
            running_balance = base_sal

            pdf.set_x(15)
            pdf.set_text_color(30, 41, 59)
            pdf.set_font(font_name, "", 8.5)
            pdf.set_fill_color(255, 255, 255)

            pdf.cell(widths_tr[0], 7, txt=fix_ar(f"{running_balance:,.2f}"), border=1, align="C", fill=True)
            pdf.cell(widths_tr[1], 7, txt=fix_ar(f"{base_sal:,.2f}"), border=1, align="C", fill=True)
            pdf.cell(widths_tr[2], 7, txt=fix_ar("-"), border=1, align="C", fill=True)
            pdf.cell(widths_tr[3], 7, txt=_fit_text(pdf, "الراتب الأساسي الافتتاحي", widths_tr[3]), border=1, align="R", fill=True)
            pdf.cell(widths_tr[4], 7, txt=fix_ar(emp_info['hire_date'] or "-"), border=1, align="C", fill=True)
            pdf.cell(widths_tr[5], 7, txt=fix_ar("-"), border=1, align="C", fill=True)
            pdf.ln()

            row_alt = False
            total_debit = 0.0
            total_credit = base_sal

            for tr in transactions:
                if pdf.get_y() > 265:
                    pdf.add_page()
                    self._draw_table_header(pdf, font_name, headers_tr, widths_tr, font_size=8.5)
                    pdf.set_text_color(30, 41, 59)
                    pdf.set_font(font_name, "", 8.5)

                pdf.set_x(15)
                pdf.set_fill_color(248, 250, 252) if row_alt else pdf.set_fill_color(255, 255, 255)
                row_alt = not row_alt

                t_type = tr['type']
                amount = float(tr['amount'] or 0)
                debit_val = 0.0
                credit_val = 0.0

                if t_type in ["سلفة", "خصم", "سحب عهدة", "تسليم راتب"]:
                    debit_val = amount
                    running_balance -= amount
                    total_debit += amount
                elif t_type in ["مكافأة"]:
                    credit_val = amount
                    running_balance += amount
                    total_credit += amount

                pdf.cell(widths_tr[0], 7, txt=fix_ar(f"{running_balance:,.2f}"), border=1, align="C", fill=True)
                pdf.cell(widths_tr[1], 7, txt=fix_ar(f"{credit_val:,.2f}" if credit_val > 0 else "-"), border=1, align="C", fill=True)
                pdf.cell(widths_tr[2], 7, txt=fix_ar(f"{debit_val:,.2f}" if debit_val > 0 else "-"), border=1, align="C", fill=True)
                pdf.cell(widths_tr[3], 7, txt=_fit_text(pdf, f"{t_type}: {tr['description']}", widths_tr[3]), border=1, align="R", fill=True)
                pdf.cell(widths_tr[4], 7, txt=fix_ar(tr['date']), border=1, align="C", fill=True)
                pdf.cell(widths_tr[5], 7, txt=fix_ar(f"#{tr['transaction_id']}"), border=1, align="C", fill=True)
                pdf.ln()

            if not transactions and base_sal == 0:
                pdf.set_x(15)
                pdf.cell(usable_w, 8, txt=fix_ar("لا توجد حركات مالية مسجلة لهذا الموظف في الفترة المحددة."), border=1, align="C")
                pdf.ln()

            pdf.set_x(15)
            pdf.set_font(font_name, "B", 8.5)
            pdf.set_fill_color(226, 232, 240)
            pdf.set_text_color(15, 23, 42)

            pdf.cell(widths_tr[0], 8, txt=fix_ar(f"{running_balance:,.2f}"), border=1, align="C", fill=True)
            pdf.cell(widths_tr[1], 8, txt=fix_ar(f"{total_credit:,.2f}"), border=1, align="C", fill=True)
            pdf.cell(widths_tr[2], 8, txt=fix_ar(f"{total_debit:,.2f}"), border=1, align="C", fill=True)
            pdf.cell(sum(widths_tr[3:]), 8, txt=fix_ar("المجاميع النهائية وصافي الراتب المتبقي للصرف (ر.ي):"), border=1, align="R", fill=True)
            pdf.ln(14)

            self._draw_signatures(pdf, font_name, usable_w, "توقيع ومصادقة الموظف")
            pdf.output(save_path)
            return True, f"تم استخراج كشف حساب الموظف بنجاح:\n{save_path}"
        except Exception as ex:
            return False, f"فشل تصدير كشف حساب الموظف إلى PDF: {ex}"

    # =========================================================================
    # 13. تصدير كشف حساب الموظف Excel
    # =========================================================================
    def export_staff_statement_excel(self, emp_id, save_path, start_date=None, end_date=None, clinic_info=None):
        try:
            emp_info, transactions, summary = self.get_staff_statement(emp_id, start_date, end_date)
            if not emp_info:
                return False, "تعذر العثور على بيانات الموظف المحدد."

            c_info = clinic_info or self.get_clinic_info()
            trans_rows = []
            for tr in transactions:
                trans_rows.append({
                    "رقم الحركة": tr["transaction_id"],
                    "التاريخ": tr["date"],
                    "نوع الحركة": tr["type"],
                    "المبلغ (ر.ي)": tr["amount"],
                    "البيان والتفاصيل": tr["description"]
                })
            df_trans = pd.DataFrame(trans_rows)

            summary_rows = [
                {"البيان": "اسم العيادة", "القيمة": c_info.get("name", "عيادة تيسير لطب الأسنان")},
                {"البيان": "اسم الموظف", "القيمة": emp_info["full_name"]},
                {"البيان": "المسمى الوظيفي", "القيمة": emp_info["job_title"]},
                {"البيان": "رقم الهاتف", "القيمة": emp_info["phone"]},
                {"البيان": "تاريخ التعيين", "القيمة": emp_info["hire_date"]},
                {"البيان": "فترة التقرير", "القيمة": summary["period"]},
                {"البيان": "الراتب الأساسي (ر.ي)", "القيمة": summary["base_salary"]},
                {"البيان": "إجمالي الحركات المالية (ر.ي)", "القيمة": summary["total_transactions"]},
                {"البيان": "عدد الحركات", "القيمة": summary["transactions_count"]},
                {"البيان": "تاريخ استخراج الكشف", "القيمة": datetime.date.today().strftime("%Y-%m-%d")}
            ]
            df_summary = pd.DataFrame(summary_rows)

            with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
                df_summary.to_excel(writer, sheet_name="الملخص المالي للموظف", index=False)
                df_trans.to_excel(writer, sheet_name="سجل الحركات المالية", index=False)
                for sheet in writer.sheets.values():
                    sheet.sheet_view.rightToLeft = True

            return True, f"تم تصدير كشف حساب الموظف إلى Excel بنجاح:\n{save_path}"
        except Exception as ex:
            return False, f"فشل تصدير كشف حساب الموظف إلى Excel: {ex}"
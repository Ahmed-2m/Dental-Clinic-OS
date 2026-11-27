import os
import datetime
import pandas as pd
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display
from mysql.connector import Error
from backend.database import Database
from backend.print_branding import load_clinic_profile, draw_pdf_clinic_logo


class DailyTreasuryRepository:
    def __init__(self):
        self.db = Database.from_config_file()

    def get_connection(self):
        return self.db.get_connection()

    def get_balance(self):
        """حساب إجمالي السيولة الحالية في الخزينة لجميع الأوقات"""
        _, _, summary = self.get_daily_transactions()
        return summary.get("net_cash", 0.0)

    def get_daily_transactions(self, target_date=None):
        """جلب تفاصيل حركة الخزينة الصادرة والواردة مطابقة تماماً لهيكل الجداول"""
        conn = self.get_connection()
        if not conn:
            return [], [], {}

        try:
            cursor = conn.cursor()

            # إعداد فلاتر التاريخ للجميع
            date_filter_pat = "WHERE pa.total_amount > 0"
            date_filter_lab = "WHERE lp.amount_paid > 0"
            date_filter_sup = "WHERE sp.amount > 0"
            date_filter_emp = "WHERE et.amount > 0"

            params_pat = []
            params_lab = []
            params_sup = []
            params_emp = []

            if target_date:
                date_filter_pat = "WHERE pa.payment_date = %s AND pa.total_amount > 0"
                date_filter_lab = "WHERE lp.payment_date = %s AND lp.amount_paid > 0"
                date_filter_sup = "WHERE sp.payment_date = %s AND sp.amount > 0"
                date_filter_emp = "WHERE et.transaction_date = %s AND et.amount > 0"
                params_pat = [target_date]
                params_lab = [target_date]
                params_sup = [target_date]
                params_emp = [target_date]

            # 1. الوارد (مقبوضات المرضى من patient_accounts باستخدام invoice_id)
            patient_inflow_query = f"""
                SELECT pa.invoice_id, pa.payment_date, pa.total_amount, 
                       COALESCE(pa.payment_method, 'نقداً'), 
                       COALESCE(p.full_name, 'مريض عام') as client_name,
                       CONCAT('فاتورة رقم #', pa.invoice_id) as notes
                FROM patient_accounts pa
                LEFT JOIN patients p ON pa.patient_id = p.patient_id
                {date_filter_pat}
                ORDER BY pa.payment_date DESC, pa.invoice_id DESC
            """
            cursor.execute(patient_inflow_query, tuple(params_pat))
            patient_rows = cursor.fetchall()

            inflows = []
            total_in = 0.0
            for r in patient_rows:
                amt = float(r[2] or 0)
                total_in += amt
                inflows.append({
                    "id": r[0],
                    "date": str(r[1]),
                    "amount": amt,
                    "method": r[3],
                    "source": f"مريض: {r[4]}",
                    "notes": r[5],
                })

            # 2. الصادر (مدفوعات المعامل من lab_payments مع تضمين رقم المستند receipt_no)
            lab_outflow_query = f"""
                SELECT lp.payment_id, lp.payment_date, lp.amount_paid,
                       COALESCE(lp.payment_method, 'نقداً'),
                       COALESCE(l.lab_name, 'معمل خارجي') as client_name,
                       CONCAT('سند رقم: ', COALESCE(lp.receipt_no, '-'), ' - ', COALESCE(lp.notes, 'سداد معمل')) as notes
                FROM lab_payments lp
                LEFT JOIN labs l ON lp.lab_id = l.lab_id
                {date_filter_lab}
                ORDER BY lp.payment_date DESC, lp.payment_id DESC
            """
            cursor.execute(lab_outflow_query, tuple(params_lab))
            lab_rows = cursor.fetchall()

            outflows = []
            total_out = 0.0
            for r in lab_rows:
                amt = float(r[2] or 0)
                total_out += amt
                outflows.append({
                    "id": r[0],
                    "date": str(r[1]),
                    "amount": amt,
                    "method": r[3],
                    "source": f"معمل: {r[4]}",
                    "notes": r[5],
                })

            # 3. الصادر (مدفوعات الموردين من supplier_payments بدون استدعاء payment_method غير الموجود)
            supplier_outflow_query = f"""
                SELECT sp.payment_id, sp.payment_date, sp.amount,
                       COALESCE(s.supplier_name, 'مورد عام'),
                       CONCAT('سند صرف رقم: ', COALESCE(sp.supplier_voucher_no, '-'), ' - ', COALESCE(sp.notes, 'سداد مبالغ للمورد'))
                FROM supplier_payments sp
                LEFT JOIN suppliers s ON sp.supplier_id = s.supplier_id
                {date_filter_sup}
                ORDER BY sp.payment_date DESC, sp.payment_id DESC
            """
            cursor.execute(supplier_outflow_query, tuple(params_sup))
            sup_rows = cursor.fetchall()
            for r in sup_rows:
                amt = float(r[2] or 0)
                total_out += amt
                outflows.append({
                    "id": r[0],
                    "date": str(r[1]),
                    "amount": amt,
                    "method": "نقداً",
                    "source": f"مورد: {r[3]}",
                    "notes": r[4],
                })

            # 4. الصادر (حركات الموظفين من employee_transactions)
            emp_outflow_query = f"""
                SELECT et.transaction_id, et.transaction_date, et.amount,
                       et.transaction_type, COALESCE(e.full_name, 'موظف'), et.description
                FROM employee_transactions et
                LEFT JOIN employees e ON et.emp_id = e.emp_id
                {date_filter_emp}
                ORDER BY et.transaction_date DESC, et.transaction_id DESC
            """
            cursor.execute(emp_outflow_query, tuple(params_emp))
            emp_rows = cursor.fetchall()
            for r in emp_rows:
                amt = float(r[2] or 0)
                total_out += amt
                outflows.append({
                    "id": r[0],
                    "date": str(r[1]),
                    "amount": amt,
                    "method": "نقداً",
                    "source": f"موظف ({r[3]}): {r[4]}",
                    "notes": r[5] or "-",
                })

            opening_balance = 0.00
            net_cash = (opening_balance + total_in) - total_out

            summary = {
                "target_date": target_date or "كامل السجل",
                "opening_balance": opening_balance,
                "total_inflow": total_in,
                "total_outflow": total_out,
                "net_cash": net_cash,
            }

            cursor.close()
            conn.close()
            return inflows, outflows, summary

        except Error as e:
            print(f"[خطأ في جلب حركات الخزينة]: {e}")
            return [], [], {}

    def close_day_treasury(self, target_date, username="Admin", notes=""):
        """تنفيذ عملية الإغلاق اليومي وحفظها في قاعدة البيانات"""
        if not target_date:
            target_date = datetime.date.today().strftime("%Y-%m-%d")

        _, _, summary = self.get_daily_transactions(target_date)
        if not summary:
            return False, "فشل حساب ملخص الخزينة لتنفيذ الإغلاق."

        conn = self.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات."

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT closing_id FROM daily_closings WHERE closing_date = %s;", (target_date,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return False, f"تنبيه: تاريخ اليوم ({target_date}) تم إغلاقه مسبقاً."

            insert_query = """
                INSERT INTO daily_closings (closing_date, opening_balance, total_inflow, total_outflow, net_cash, closed_by, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (
                target_date,
                summary["opening_balance"],
                summary["total_inflow"],
                summary["total_outflow"],
                summary["net_cash"],
                username,
                notes,
            ))
            conn.commit()
            cursor.close()
            conn.close()
            return True, f"تم إغلاق الصندوق ليوم {target_date} بنجاح وحفظ الرصيد الختامي."
        except Error as e:
            return False, f"خطأ في حفظ الإغلاق اليومي: {e}"

    def export_treasury_pdf(self, target_date, save_path, clinic_info=None):
        """تصدير تقرير الحركة اليومية للصندوق إلى ملف PDF"""
        c_info = clinic_info or load_clinic_profile()
        inflows, outflows, summary = self.get_daily_transactions(target_date)
        if not summary:
            summary = {
                "target_date": target_date or "كامل السجل",
                "opening_balance": 0.0,
                "total_inflow": 0.0,
                "total_outflow": 0.0,
                "net_cash": 0.0,
            }

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        draw_pdf_clinic_logo(pdf, c_info)

        font_path = r"C:\Windows\Fonts\arial.ttf"
        font_bold_path = r"C:\Windows\Fonts\arialbd.ttf"
        has_ar = os.path.exists(font_path)
        if has_ar:
            pdf.add_font("ArabicFont", "", font_path, uni=True)
            if os.path.exists(font_bold_path):
                pdf.add_font("ArabicFont", "B", font_bold_path, uni=True)
            font_name = "ArabicFont"
        else:
            font_name = "Arial"

        # رأس التقرير
        pdf.set_font(font_name, "B", 16)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, txt=self._fix_ar(c_info.get("name", "عيادة تيسير لطب الأسنان")), ln=True, align="C")

        pdf.set_font(font_name, "", 10)
        pdf.set_text_color(71, 85, 105)
        contact_line = f"العنوان: {c_info.get('address', '')}   |   هاتف: {c_info.get('phone', '')}"
        pdf.cell(0, 5, txt=self._fix_ar(contact_line), ln=True, align="C")
        pdf.cell(0, 6, txt=self._fix_ar(f"تقرير حركة الخزينة والصندوق اليومي - التاريخ: {target_date}"), ln=True, align="C")
        pdf.ln(4)

        # بطاقات الملخص المالي في الـ PDF
        col_w = 42
        pdf.set_font(font_name, "B", 9)
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(col_w, 7, txt=self._fix_ar(f"الافتتاح: {summary['opening_balance']:,.2f}"), border=1, align="C", fill=True)
        pdf.cell(col_w, 7, txt=self._fix_ar(f"الوارد: {summary['total_inflow']:,.2f}"), border=1, align="C", fill=True)
        pdf.cell(col_w, 7, txt=self._fix_ar(f"الصادر: {summary['total_outflow']:,.2f}"), border=1, align="C", fill=True)
        pdf.cell(col_w, 7, txt=self._fix_ar(f"الصافي: {summary['net_cash']:,.2f}"), border=1, align="C", fill=True)
        pdf.ln(10)

        # جدول الوارد
        pdf.set_font(font_name, "B", 11)
        pdf.set_text_color(16, 185, 129)
        pdf.cell(0, 6, txt=self._fix_ar("📥 مقبوضات الوارد النقدي (المرضى):"), ln=True, align="R")
        pdf.ln(2)

        pdf.set_fill_color(16, 185, 129)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(font_name, "B", 9)
        pdf.cell(60, 6, txt=self._fix_ar("البيان"), border=1, align="C", fill=True)
        pdf.cell(45, 6, txt=self._fix_ar("المصدر"), border=1, align="C", fill=True)
        pdf.cell(35, 6, txt=self._fix_ar("طريقة الدفع"), border=1, align="C", fill=True)
        pdf.cell(40, 6, txt=self._fix_ar("المبلغ (ر.ي)"), border=1, align="C", fill=True)
        pdf.ln()

        pdf.set_font(font_name, "", 9)
        pdf.set_text_color(30, 41, 59)
        if inflows:
            for item in inflows:
                pdf.cell(60, 6, txt=self._fix_ar(str(item["notes"])), border=1, align="R")
                pdf.cell(45, 6, txt=self._fix_ar(str(item["source"])), border=1, align="R")
                pdf.cell(35, 6, txt=self._fix_ar(str(item["method"])), border=1, align="C")
                pdf.cell(40, 6, txt=self._fix_ar(f"{item['amount']:,.2f}"), border=1, align="C")
                pdf.ln()
        else:
            pdf.cell(180, 6, txt=self._fix_ar("لا توجد مقبوضات مسجلة في هذا التاريخ."), border=1, align="C")
            pdf.ln()

        pdf.ln(6)
        # جدول الصادر
        pdf.set_font(font_name, "B", 11)
        pdf.set_text_color(239, 68, 68)
        pdf.cell(0, 6, txt=self._fix_ar("📤 مدفوعات الصادر النقدي (معامل، مشتريات، موظفين):"), ln=True, align="R")
        pdf.ln(2)

        pdf.set_fill_color(239, 68, 68)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(font_name, "B", 9)
        pdf.cell(60, 6, txt=self._fix_ar("البيان / التفاصيل"), border=1, align="C", fill=True)
        pdf.cell(45, 6, txt=self._fix_ar("المستفيد"), border=1, align="C", fill=True)
        pdf.cell(35, 6, txt=self._fix_ar("طريقة الدفع"), border=1, align="C", fill=True)
        pdf.cell(40, 6, txt=self._fix_ar("المبلغ (ر.ي)"), border=1, align="C", fill=True)
        pdf.ln()

        pdf.set_font(font_name, "", 9)
        pdf.set_text_color(30, 41, 59)
        if outflows:
            for item in outflows:
                pdf.cell(60, 6, txt=self._fix_ar(str(item["notes"])), border=1, align="R")
                pdf.cell(45, 6, txt=self._fix_ar(str(item["source"])), border=1, align="R")
                pdf.cell(35, 6, txt=self._fix_ar(str(item["method"])), border=1, align="C")
                pdf.cell(40, 6, txt=self._fix_ar(f"{item['amount']:,.2f}"), border=1, align="C")
                pdf.ln()
        else:
            pdf.cell(180, 6, txt=self._fix_ar("لا توجد مدفوعات أو مصروفات مسجلة في هذا التاريخ."), border=1, align="C")
            pdf.ln()

        pdf.output(save_path)
        return True, "تم تصدير تقرير الخزينة PDF بنجاح."

    def export_treasury_excel(self, target_date, save_path, clinic_info=None):
        """تصدير تقرير الحركة اليومية للصندوق إلى ملف Excel"""
        c_info = clinic_info or load_clinic_profile()
        inflows, outflows, summary = self.get_daily_transactions(target_date)
        if not summary:
            summary = {
                "target_date": target_date or "كامل السجل",
                "opening_balance": 0.0,
                "total_inflow": 0.0,
                "total_outflow": 0.0,
                "net_cash": 0.0,
            }

        summary_with_clinic = {
            "اسم العيادة": c_info.get("name", "عيادة تيسير لطب الأسنان"),
            "هاتف العيادة": c_info.get("phone", ""),
            "عنوان العيادة": c_info.get("address", ""),
            "التاريخ": summary.get("target_date", target_date or ""),
            "الرصيد الافتتاحي": summary.get("opening_balance", 0.0),
            "إجمالي الوارد": summary.get("total_inflow", 0.0),
            "إجمالي الصادر": summary.get("total_outflow", 0.0),
            "صافي النقدية": summary.get("net_cash", 0.0),
        }

        in_df = pd.DataFrame(inflows) if inflows else pd.DataFrame(columns=["date", "source", "amount", "method", "notes"])
        out_df = pd.DataFrame(outflows) if outflows else pd.DataFrame(columns=["date", "source", "amount", "method", "notes"])

        with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
            summary_df = pd.DataFrame([summary_with_clinic])
            summary_df.to_excel(writer, sheet_name="الملخص المالي", index=False)
            if not in_df.empty:
                in_df.to_excel(writer, sheet_name="الوارد النقدي", index=False)
            if not out_df.empty:
                out_df.to_excel(writer, sheet_name="الصادر النقدي", index=False)
            for sheet in writer.sheets.values():
                sheet.sheet_view.rightToLeft = True

        return True, "تم تصدير تقرير الخزينة Excel بنجاح."

    def _fix_ar(self, text):
        """معالجة وتشكيل وعكس النصوص العربية لتظهر بشكل سليم في تقارير FPDF"""
        if not text or not isinstance(text, str):
            return str(text or "")

        try:
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except Exception:
            return text
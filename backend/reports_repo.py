import os
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display
from backend.database import Database
from backend.print_branding import load_clinic_profile, draw_pdf_clinic_logo


def fix_ar(text):
    if not text:
        return ""
    try:
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)


class ReportsRepository:
    def __init__(self):
        self.db = Database.from_config_file()

    def get_financial_report(self, start_date, end_date):
        """
        جلب كشف حساب مالي تفصيلي (إيرادات/مواعيد ورواتب) خلال فترة محددة.
        """
        conn = self.db.get_connection()
        if not conn:
            return [], {}
        try:
            cursor = conn.cursor()
            query_staff = """
                SELECT emp_id, full_name, job_title, salary, hire_date, status 
                FROM employees 
                WHERE hire_date BETWEEN %s AND %s OR hire_date IS NULL
                ORDER BY emp_id DESC;
            """
            cursor.execute(query_staff, (start_date, end_date))
            rows = cursor.fetchall()

            total_salaries = sum(float(r[3] or 0) for r in rows if r[5] == 'active')

            # إجمالي المرضى
            total_patients = 0
            try:
                cursor.execute("SELECT COUNT(*) FROM patients;")
                res = cursor.fetchone()
                if res:
                    total_patients = res[0] or 0
            except Exception:
                pass

            # إجمالي المواعيد (مع حماية في حال عدم وجود جدول المواعيد)
            total_appointments = 0
            try:
                cursor.execute("SELECT COUNT(*) FROM appointments;")
                res = cursor.fetchone()
                if res:
                    total_appointments = res[0] or 0
            except Exception:
                total_appointments = 0

            summary = {
                "period": f"{start_date} إلى {end_date}",
                "active_staff_count": len([r for r in rows if r[5] == 'active']),
                "total_salaries": total_salaries,
                "total_patients": total_patients,
                "total_appointments": total_appointments,
            }
            cursor.close()
            conn.close()
            return rows, summary
        except Exception as e:
            print(f"[خطأ في التقرير]: {e}")
            return [], {}

    def export_to_excel(self, rows, summary, save_path, clinic_info=None):
        """توليد ملف Excel احترافي منسق"""
        try:
            c_info = clinic_info or load_clinic_profile()
            columns = ["الرقم الوظيفي", "الاسم الكامل", "المسمى الوظيفي", "الراتب", "تاريخ التعيين", "الحالة"]
            df_data = pd.DataFrame(rows, columns=columns)

            summary_data = pd.DataFrame([
                {"البيان": "اسم العيادة", "القيمة": c_info.get("name", "عيادة تيسير")},
                {"البيان": "رقم الهاتف", "القيمة": c_info.get("phone", "")},
                {"البيان": "العنوان", "القيمة": c_info.get("address", "")},
                {"البيان": "فترة التقرير", "القيمة": summary.get("period", "")},
                {"البيان": "إجمالي المرضى المسجلين", "القيمة": summary.get("total_patients", 0)},
                {"البيان": "إجمالي المواعيد", "القيمة": summary.get("total_appointments", 0)},
                {"البيان": "إجمالي التزامات الرواتب", "القيمة": summary.get("total_salaries", 0.0)},
            ])

            with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
                summary_data.to_excel(writer, sheet_name="الملخص العام", index=False)
                df_data.to_excel(writer, sheet_name="تفاصيل الكشف", index=False)

            return True, f"تم تصدير ملف Excel بنجاح:\n{save_path}"
        except Exception as e:
            return False, f"فشل تصدير Excel: {e}"

    def export_to_pdf(self, rows, summary, save_path, clinic_info=None):
        """توليد ملف PDF رسمي مع ترويسة العيادة والشعار وجدول البيانات"""
        try:
            c_info = clinic_info or load_clinic_profile()
            pdf = FPDF()
            pdf.add_page()
            draw_pdf_clinic_logo(pdf, c_info)

            font_path = r"C:\Windows\Fonts\arial.ttf"
            if os.path.exists(font_path):
                pdf.add_font("ArabicFont", "", font_path, uni=True)
                pdf.set_font("ArabicFont", size=14)
            else:
                pdf.set_font("Arial", size=12)

            pdf.cell(0, 10, txt=fix_ar(c_info.get("name", "عيادة تيسير لطب الأسنان")), ln=True, align="C")
            pdf.set_font_size(10)
            pdf.cell(0, 7, txt=fix_ar(f"العنوان: {c_info.get('address', '')} | الهاتف: {c_info.get('phone', '')}"), ln=True, align="C")
            pdf.cell(0, 7, txt=fix_ar(f"تقرير وكشف حساب للفترة: {summary.get('period', '')}"), ln=True, align="C")
            pdf.ln(8)

            pdf.set_font_size(11)
            pdf.cell(0, 8, txt=fix_ar(f"• إجمالي المرضى: {summary.get('total_patients', 0)}   |   • إجمالي المواعيد: {summary.get('total_appointments', 0)}"), ln=True, align="R")
            pdf.cell(0, 8, txt=fix_ar(f"• إجمالي الرواتب المعتمدة: {summary.get('total_salaries', 0.0)}"), ln=True, align="R")
            pdf.ln(5)

            headers = ["الحالة", "التعيين", "الراتب", "الوظيفة", "الاسم", "ID"]
            col_widths = [25, 30, 30, 40, 50, 15]

            pdf.set_fill_color(31, 83, 141)
            pdf.set_text_color(255, 255, 255)
            for h, w in zip(headers, col_widths):
                pdf.cell(w, 9, txt=fix_ar(h), border=1, align="C", fill=True)
            pdf.ln()

            pdf.set_text_color(0, 0, 0)
            pdf.set_font_size(9)
            for r in rows:
                vals = [str(r[5] or ""), str(r[6] or ""), str(r[3] or "0"), str(r[4] or ""), str(r[1] or ""), str(r[0] or "")]
                for v, w in zip(vals, col_widths):
                    pdf.cell(w, 8, txt=fix_ar(v), border=1, align="C")
                pdf.ln()

            pdf.output(save_path)
            return True, f"تم استخراج كشف PDF بنجاح:\n{save_path}"
        except Exception as e:
            return False, f"فشل استخراج PDF: {e}"
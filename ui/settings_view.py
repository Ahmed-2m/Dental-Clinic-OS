import datetime
import json
import os
import subprocess
from tkinter import filedialog
from tkcalendar import Calendar
import customtkinter as ctk

from backend.staff_repo import StaffRepository
from backend.backup_repo import BackupRepository
from backend.reports_repo import ReportsRepository
from ui.theme import THEME, get_font, setup_rtl_entry, setup_rtl_textbox, fix_combobox_rtl, get_clinic_logo

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.config_file = os.path.join(os.getcwd(), "clinic_config.json")
        self.clinic_info = self._load_clinic_config()

        # نظام التبويبات الرئيسي داخل لوحة الإعدادات
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=12,
            segmented_button_selected_color=THEME["primary"],
            segmented_button_selected_hover_color=THEME["primary_hover"],
            segmented_button_unselected_color=THEME["bg_card_secondary"],
            segmented_button_unselected_hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            segmented_button_fg_color=THEME["bg_card_secondary"],
        )
        self.tabview.pack(fill="both", expand=True)

        # ترتيب التبويبات بحيث يظهر التبويب الرئيسي على اليمين
        self.tab_general = self.tabview.add("⚙️ إعدادات عامة")
        self.tab_backup = self.tabview.add("💾 النسخ الاحتياطي")
        self.tab_staff = self.tabview.add("👥 الموظفين والصلاحيات")
        self.tab_reports = self.tabview.add("📊 التقارير والكشوفات")

        # تعيين التبويب الأيمن نشطاً افتراضياً
        self.tabview.set("📊 التقارير والكشوفات")

        self._build_reports_tab()
        self._build_staff_management_tab()
        self._build_backup_tab_content()
        self._build_general_tab_content()

    def _load_clinic_config(self):
        default_cfg = {
            "name": "عيادة تيسير لطب الأسنان",
            "phone": "770000000",
            "address": "صنعاء - اليمن",
            "appearance": "Dark"
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return default_cfg
        return default_cfg

    # =========================================================================
    # 1. تبويب إدارة الموظفين والصلاحيات
    # =========================================================================
    def _build_staff_management_tab(self):
        self.staff_repo = StaffRepository()
        self.selected_emp_id = None

        self.tab_staff.grid_columnconfigure(0, weight=3) # القائمة على اليسار
        self.tab_staff.grid_columnconfigure(1, weight=2) # النموذج على اليمين
        self.tab_staff.grid_rowconfigure(0, weight=1)

        # استخدام CTkScrollableFrame بدلاً من CTkFrame لضمان ظهور شريط التمرير والوصول لكل الحقول
        self.form_frame = ctk.CTkScrollableFrame(
            self.tab_staff, 
            corner_radius=12, 
            fg_color=THEME["bg_card_secondary"],
            border_width=1,
            border_color=THEME["border_light"]
        )
        self.form_frame.grid(row=0, column=1, padx=(6, 0), sticky="nsew")

        self.form_title_lbl = ctk.CTkLabel(
            self.form_frame, 
            text="➕ إضافة موظف / كادر طبي جديد", 
            font=get_font(size=14, weight="bold"),
            text_color=THEME["primary"]
        )
        self.form_title_lbl.pack(anchor="e", padx=16, pady=(14, 8))

        def add_entry_field(label_text, placeholder):
            lbl = ctk.CTkLabel(self.form_frame, text=label_text, font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"])
            lbl.pack(anchor="e", padx=16, pady=(2, 0))
            entry = ctk.CTkEntry(
                self.form_frame,
                placeholder_text=placeholder,
                width=300,
                height=34,
                justify="right",
                fg_color=THEME["bg_card"],
                border_color=THEME["border"]
            )
            entry.pack(anchor="e", padx=16, pady=(0, 4))
            return setup_rtl_entry(entry)

        def add_combo_field(label_text, values_list):
            lbl = ctk.CTkLabel(self.form_frame, text=label_text, font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"])
            lbl.pack(anchor="e", padx=16, pady=(2, 0))
            combo = ctk.CTkComboBox(
                self.form_frame,
                values=values_list,
                width=300,
                height=34,
                justify="right",
                fg_color=THEME["bg_card"],
                border_color=THEME["border"]
            )
            combo.set(values_list[0])
            fix_combobox_rtl(combo)
            combo.pack(anchor="e", padx=16, pady=(0, 4))
            return combo

        self.e_name = add_entry_field("الاسم الكامل:", "أدخل الاسم...")
        self.e_phone = add_entry_field("رقم الهاتف المحمول:", "77xxxxxxx")
        self.e_address = add_entry_field("العنوان والمنطقة:", "صنعاء...")
        
        job_titles = ["طبيب أسنان", "أخصائي تركيبات", "مساعد طبيب", "موظف استقبال", "محاسب", "مسؤول نظام"]
        self.combo_job = add_combo_field("المسمى الوظيفي:", job_titles)

        self.e_salary = add_entry_field("الراتب الشهري (ر.ي):", "0.00")
        
        date_label = ctk.CTkLabel(self.form_frame, text="تاريخ التعيين:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"])
        date_label.pack(anchor="e", padx=16, pady=(2, 0))
        
        date_container = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        date_container.pack(anchor="e", padx=16, pady=(0, 4))
        
        self.e_date = ctk.CTkEntry(date_container, placeholder_text="YYYY-MM-DD", width=250, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.e_date.pack(side="right", padx=(5, 0))
        self.e_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        setup_rtl_entry(self.e_date)

        cal_btn = ctk.CTkButton(
            date_container, text="📅", width=42, height=32,
            fg_color=THEME["bg_app"], hover_color=THEME["bg_card_hover"],
            border_width=1, border_color=THEME["border"],
            command=lambda: self.open_calendar_popup(self.e_date)
        )
        cal_btn.pack(side="right")

        self.e_user = add_entry_field("اسم المستخدم للنظام:", "admin_user")
        self.e_pass = add_entry_field("كلمة المرور:", "******")
        
        roles_list = ["admin", "doctor", "receptionist"]
        self.combo_role = add_combo_field("الصلاحية في النظام:", roles_list)

        status_lbl = ctk.CTkLabel(self.form_frame, text="حالة الحساب:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"])
        status_lbl.pack(anchor="e", padx=16, pady=(2, 0))
        self.combo_status = ctk.CTkComboBox(self.form_frame, values=["active", "inactive"], width=300, height=32, justify="right", fg_color=THEME["bg_card"], border_color=THEME["border"])
        self.combo_status.set("active")
        fix_combobox_rtl(self.combo_status)
        self.combo_status.pack(anchor="e", padx=16, pady=(0, 8))

        btn_row = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        btn_row.pack(anchor="e", padx=16, pady=(4, 12))

        self.cancel_btn = ctk.CTkButton(
            btn_row, text="❌ إلغاء", font=get_font(size=11),
            fg_color=THEME["danger_soft"], hover_color=THEME["danger"],
            text_color=THEME["danger"], height=34, width=80, command=self.reset_form
        )

        self.save_btn = ctk.CTkButton(
            btn_row, text="💾 حفظ الموظف", font=get_font(size=12, weight="bold"),
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"], height=34, width=140, command=self.save_or_update
        )
        self.save_btn.pack(side="right", padx=(5, 0))

        # قائمة الموظفين (يسار)
        list_frame = ctk.CTkFrame(
            self.tab_staff, 
            corner_radius=12, 
            fg_color=THEME["bg_card_secondary"],
            border_width=1,
            border_color=THEME["border_light"]
        )
        list_frame.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
        list_frame.grid_rowconfigure(1, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        header_l = ctk.CTkFrame(list_frame, fg_color="transparent")
        header_l.grid(row=0, column=0, sticky="ew", padx=16, pady=12)
        ctk.CTkLabel(header_l, text="📋 طاقم العمل والصلاحيات", font=get_font(size=14, weight="bold"), text_color=THEME["text_primary"]).pack(side="right")
        ctk.CTkButton(
            header_l, text="🔄 تحديث", width=80, height=30, 
            fg_color=THEME["bg_app"], hover_color=THEME["bg_card_hover"],
            border_width=1, border_color=THEME["border"],
            command=self.refresh_list
        ).pack(side="left")

        self.scroll_cards = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.scroll_cards.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self.refresh_list()

    def open_calendar_popup(self, target_entry):
        top = ctk.CTkToplevel(self)
        top.title("اختيار التاريخ")
        top.geometry("320x300")
        top.attributes("-topmost", True)
        top.resizable(False, False)

        cal = Calendar(top, selectmode="day", year=datetime.date.today().year, month=datetime.date.today().month, day=datetime.date.today().day)
        cal.pack(pady=15, padx=15, fill="both", expand=True)

        def set_date():
            selected_date = cal.get_date()
            try:
                parsed_date = datetime.datetime.strptime(selected_date, "%m/%d/%y").strftime("%Y-%m-%d")
            except Exception:
                try:
                    parsed_date = datetime.datetime.strptime(selected_date, "%Y-%m-%d").strftime("%Y-%m-%d")
                except Exception:
                    parsed_date = selected_date

            target_entry.delete(0, "end")
            target_entry.insert(0, parsed_date)
            top.destroy()

        ctk.CTkButton(top, text="تأكيد التاريخ", fg_color=THEME["primary"], height=32, command=set_date).pack(pady=(0, 15), padx=15, fill="x")

    def save_or_update(self):
        name = self.e_name.get().strip()
        if not name:
            return
        data = (
            name, self.e_phone.get().strip(), self.e_address.get().strip(),
            self.combo_job.get().strip(), self.e_salary.get().strip(), self.e_date.get().strip(),
            self.e_user.get().strip(), self.e_pass.get().strip(), self.combo_role.get().strip(),
            self.combo_status.get().strip()
        )
        if self.selected_emp_id is None:
            ok, _ = self.staff_repo.add(*data)
        else:
            ok, _ = self.staff_repo.update(self.selected_emp_id, *data)

        if ok:
            self.reset_form()
            # استخدام after لتأجيل التحديث لحين الانتهاء من دورة الـ GUI الحالية تفادياً لأخطاء الـ update
            self.after(100, self.refresh_list)

    def reset_form(self):
        self.selected_emp_id = None
        for entry in [self.e_name, self.e_phone, self.e_address, self.e_salary, self.e_user, self.e_pass]:
            entry.delete(0, "end")
        self.e_date.delete(0, "end")
        self.e_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.combo_job.set("طبيب أسنان")
        self.combo_role.set("admin")
        self.combo_status.set("active")
        self.form_title_lbl.configure(text="➕ إضافة موظف / كادر طبي جديد", text_color=THEME["primary"])
        self.save_btn.configure(text="💾 حفظ الموظف", fg_color=THEME["primary"])
        self.cancel_btn.pack_forget()

    def load_for_edit(self, s):
        self.selected_emp_id = s[0]
        self.e_name.delete(0, "end"); self.e_name.insert(0, str(s[1] or ""))
        self.e_phone.delete(0, "end"); self.e_phone.insert(0, str(s[2] or ""))
        self.e_address.delete(0, "end"); self.e_address.insert(0, str(s[3] or ""))
        if s[4]: self.combo_job.set(s[4])
        self.e_salary.delete(0, "end"); self.e_salary.insert(0, str(s[5] or ""))
        self.e_date.delete(0, "end"); self.e_date.insert(0, str(s[6] or ""))
        self.e_user.delete(0, "end"); self.e_user.insert(0, str(s[7] or ""))
        self.e_pass.delete(0, "end")
        if s[8]: self.combo_role.set(str(s[8]))
        if s[9] in ["active", "inactive"]: self.combo_status.set(s[9])

        self.form_title_lbl.configure(text=f"✏️ تعديل موظف (#{s[0]} - {s[1]})", text_color=THEME["warning"])
        self.save_btn.configure(text="💾 حفظ التعديلات", fg_color=THEME["warning"])
        self.cancel_btn.pack(side="right", padx=(5, 0))

    def delete_action(self, emp_id):
        if self.staff_repo.delete(emp_id)[0]:
            if self.selected_emp_id == emp_id:
                self.reset_form()
            self.refresh_list()

    def refresh_list(self):
        try:
            for w in self.scroll_cards.winfo_children():
                w.destroy()
        except Exception:
            pass

        rows = self.staff_repo.get_all()
        if rows:
            for s in rows:
                card = ctk.CTkFrame(
                    self.scroll_cards, 
                    corner_radius=10, 
                    fg_color=THEME["bg_card"],
                    border_width=1,
                    border_color=THEME["border"]
                )
                card.pack(fill="x", pady=4, padx=2)

                top_c = ctk.CTkFrame(card, fg_color="transparent")
                top_c.pack(fill="x", padx=12, pady=(8, 2))

                role_tag = f"[{s[8] or 'staff'}]"
                ctk.CTkLabel(
                    top_c, 
                    text=f"👨‍⚕️ {s[1]}   |   {s[4] or 'طاقم العيادة'} {role_tag}", 
                    font=get_font(size=12, weight="bold"),
                    text_color=THEME["text_primary"]
                ).pack(side="right")

                btn_f = ctk.CTkFrame(card, fg_color="transparent")
                btn_f.pack(fill="x", padx=12, pady=(0, 8))

                sub_txt = f"📞 الهاتف: {s[2] or 'بدون'} | الراتب: {float(s[5] or 0):,.2f} ر.ي | الحالة: {s[9]}"
                ctk.CTkLabel(
                    btn_f, 
                    text=sub_txt, 
                    font=get_font(size=11), 
                    text_color=THEME["text_secondary"]
                ).pack(side="right")

                ctk.CTkButton(
                    btn_f, text="🗑️ حذف", width=60, height=24, 
                    fg_color=THEME["danger_soft"], hover_color=THEME["danger"], 
                    font=get_font(size=10),
                    command=lambda id=s[0]: self.delete_action(id)
                ).pack(side="left", padx=2)

                ctk.CTkButton(
                    btn_f, text="✏️ تعديل", width=60, height=24, 
                    fg_color=THEME["primary"], hover_color=THEME["primary_hover"], 
                    font=get_font(size=10),
                    command=lambda row=s: self.load_for_edit(row)
                ).pack(side="left", padx=2)
        else:
            ctk.CTkLabel(self.scroll_cards, text="لا توجد بيانات موظفين مسجلة.", font=get_font(size=12), text_color=THEME["text_muted"]).pack(pady=25)

    # =========================================================================
    # 2. تبويب التقارير والكشوفات الحسابية (PDF & Excel)
    # =========================================================================
    def _build_reports_tab(self):
        self.reports_repo = ReportsRepository()
        self.current_report_rows = []
        self.current_report_summary = {}

        container = ctk.CTkFrame(self.tab_reports, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=12, pady=10)

        filter_frame = ctk.CTkFrame(
            container, 
            corner_radius=12, 
            fg_color=THEME["bg_card_secondary"],
            border_width=1,
            border_color=THEME["border_light"]
        )
        filter_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            filter_frame, 
            text="📊 مركز التقارير والكشوفات المالية والإدارية المعتمدة", 
            font=get_font(size=14, weight="bold"),
            text_color=THEME["primary"]
        ).pack(anchor="e", padx=16, pady=(10, 6))

        controls_row = ctk.CTkFrame(filter_frame, fg_color="transparent")
        controls_row.pack(fill="x", padx=14, pady=(0, 12))

        def set_daily():
            today = datetime.date.today().strftime("%Y-%m-%d")
            self.rep_start.delete(0, "end"); self.rep_start.insert(0, today)
            self.rep_end.delete(0, "end"); self.rep_end.insert(0, today)
            generate_preview()

        def set_monthly():
            today = datetime.date.today()
            first_day = today.replace(day=1).strftime("%Y-%m-%d")
            self.rep_start.delete(0, "end"); self.rep_start.insert(0, first_day)
            self.rep_end.delete(0, "end"); self.rep_end.insert(0, today.strftime("%Y-%m-%d"))
            generate_preview()

        ctk.CTkButton(
            controls_row, text="📅 كشف اليوم", width=95, height=32, 
            fg_color=THEME["teal"], hover_color=THEME["teal_hover"], font=get_font(size=11, weight="bold"), command=set_daily
        ).pack(side="right", padx=(0, 6))

        ctk.CTkButton(
            controls_row, text="📆 كشف الشهر", width=110, height=32, 
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"], font=get_font(size=11, weight="bold"), command=set_monthly
        ).pack(side="right", padx=(0, 14))

        ctk.CTkLabel(controls_row, text="من:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        self.rep_start = ctk.CTkEntry(controls_row, width=105, height=32, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.rep_start.pack(side="right", padx=(0, 2))
        self.rep_start.insert(0, datetime.date.today().replace(day=1).strftime("%Y-%m-%d"))
        setup_rtl_entry(self.rep_start)
        ctk.CTkButton(controls_row, text="📅", width=34, height=32, fg_color=THEME["bg_app"], border_width=1, border_color=THEME["border"], command=lambda: self.open_calendar_popup(self.rep_start)).pack(side="right", padx=(0, 14))

        ctk.CTkLabel(controls_row, text="إلى:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        self.rep_end = ctk.CTkEntry(controls_row, width=105, height=32, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.rep_end.pack(side="right", padx=(0, 2))
        self.rep_end.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        setup_rtl_entry(self.rep_end)
        ctk.CTkButton(controls_row, text="📅", width=34, height=32, fg_color=THEME["bg_app"], border_width=1, border_color=THEME["border"], command=lambda: self.open_calendar_popup(self.rep_end)).pack(side="right", padx=(0, 14))

        def generate_preview():
            s_date = self.rep_start.get().strip()
            e_date = self.rep_end.get().strip()
            rows, summary = self.reports_repo.get_financial_report(s_date, e_date)
            self.current_report_rows = rows
            self.current_report_summary = summary

            self.report_preview_box.configure(state="normal")
            self.report_preview_box.delete("1.0", "end")

            header_txt = (
                f"=================================================================\n"
                f"  كشف حساب وتقرير إداري شامل | الفترة: {summary.get('period', '')}\n"
                f"  إجمالي المرضى: {summary.get('total_patients', 0)}  |  المواعيد: {summary.get('total_appointments', 0)}  |  إجمالي الرواتب: {summary.get('total_salaries', 0.0)}\n"
                f"=================================================================\n\n"
            )
            self.report_preview_box.insert("end", header_txt)

            if rows:
                for r in rows:
                    r_id = r[0] if len(r) > 0 else "N/A"
                    r_name = r[1] if len(r) > 1 else "غير معروف"
                    r_salary = r[3] if len(r) > 3 else "0"
                    r_role = r[4] if len(r) > 4 else "موظف"
                    r_status = r[5] if len(r) > 5 else "نشط"
                    r_date = r[6] if len(r) > 6 else "تاريخ غير محدد"

                    line = f"• #{r_id} | {r_name} | الوظيفة: {r_role} | الراتب: {r_salary} | التعيين: {r_date} | الحالة: {r_status}\n"
                    self.report_preview_box.insert("end", line)
            else:
                self.report_preview_box.insert("end", "لا توجد قيود مسجلة ضمن النطاق الزمني المحدد.\n")

            self.report_preview_box.configure(state="disabled")

        ctk.CTkButton(
            controls_row, text="🔍 عرض ومعاينة الكشف", width=140, height=32, 
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"], font=get_font(size=11, weight="bold"), command=generate_preview
        ).pack(side="left")

        self.report_preview_box = ctk.CTkTextbox(container, font=ctk.CTkFont(size=12), fg_color=THEME["bg_app"], border_width=1, border_color=THEME["border"])
        self.report_preview_box.pack(fill="both", expand=True, pady=6)
        setup_rtl_textbox(self.report_preview_box)

        export_bar = ctk.CTkFrame(
            container, 
            corner_radius=12, 
            fg_color=THEME["bg_card_secondary"],
            border_width=1,
            border_color=THEME["border_light"]
        )
        export_bar.pack(fill="x", pady=(6, 0))

        def do_export_pdf():
            if not self.current_report_rows:
                generate_preview()
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
                initialfile=f"Tayseer_Report_{datetime.date.today()}.pdf"
            )
            if file_path:
                ok, msg = self.reports_repo.export_to_pdf(self.current_report_rows, self.current_report_summary, file_path, self.clinic_info)
                self.rep_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

        def do_export_excel():
            if not self.current_report_rows:
                generate_preview()
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                initialfile=f"Tayseer_Report_{datetime.date.today()}.xlsx"
            )
            if file_path:
                ok, msg = self.reports_repo.export_to_excel(self.current_report_rows, self.current_report_summary, file_path, self.clinic_info)
                self.rep_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

        ctk.CTkButton(
            export_bar, text="📄 تصدير كـ PDF رسمي للطباعة", width=210, height=36, 
            fg_color=THEME["danger"], hover_color=THEME["danger_hover"], font=get_font(size=12, weight="bold"), command=do_export_pdf
        ).pack(side="right", padx=12, pady=10)

        ctk.CTkButton(
            export_bar, text="📊 تصدير كـ Excel للتحليل", width=200, height=36, 
            fg_color=THEME["success"], hover_color=THEME["success_hover"], font=get_font(size=12, weight="bold"), command=do_export_excel
        ).pack(side="right", padx=4, pady=10)

        self.rep_status_lbl = ctk.CTkLabel(export_bar, text="", font=get_font(size=11))
        self.rep_status_lbl.pack(side="left", padx=14)

        generate_preview()

    # =========================================================================
    # 3. تبويب النسخ الاحتياطي
    # =========================================================================
    def _build_backup_tab_content(self):
        backup_repo = BackupRepository()

        container = ctk.CTkFrame(self.tab_backup, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=25)

        ctk.CTkLabel(container, text="💾 حماية قاعدة البيانات والنسخ الاحتياطي", font=get_font(size=16, weight="bold"), text_color=THEME["primary"]).pack(anchor="e", pady=(0, 6))
        ctk.CTkLabel(container, text="أنشئ نسخة احتياطية سريعة تُحفظ تلقائياً في مجلد النظام لحماية بيانات المرضى في نهاية اليوم، أو صدّرها لمكان مخصص.", font=get_font(size=12), text_color=THEME["text_secondary"]).pack(anchor="e", pady=(0, 20))

        def run_auto_backup():
            success, message = backup_repo.create_automatic_backup()
            status_box.configure(text_color=THEME["success"] if success else THEME["danger"], text=message)

        ctk.CTkButton(
            container, text="🛡️ إنشاء نسخة احتياطية تلقائية سريعة (نهاية اليوم)",
            font=get_font(size=13, weight="bold"), fg_color=THEME["success"], hover_color=THEME["success_hover"],
            height=42, width=350, command=run_auto_backup
        ).pack(anchor="e", pady=(0, 12))

        def run_manual_backup():
            folder_selected = filedialog.askdirectory(title="اختر مجلد الحفظ الخارجي")
            if folder_selected:
                config = backup_repo.db.config
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                full_path = os.path.join(folder_selected, f"tayseer_manual_{timestamp}.sql")
                cmd = ["mysqldump", f"-h{config.get('host', 'localhost')}", f"-P{str(config.get('port', 3306))}", f"-u{config.get('user')}", f"-p{config.get('password')}", config.get('database')]
                try:
                    with open(full_path, "w", encoding="utf-8") as f:
                        subprocess.run(cmd, stdout=f, check=True)
                    status_box.configure(text_color=THEME["success"], text=f"تم التصدير بنجاح إلى:\n{full_path}")
                except Exception as ex:
                    status_box.configure(text_color=THEME["danger"], text=f"فشل التصدير: {ex}")

        ctk.CTkButton(
            container, text="📂 تصدير نسخة إلى مجلد مخصص (فلاش / قرص آخر)",
            font=get_font(size=12, weight="bold"), fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
            height=38, width=350, command=run_manual_backup
        ).pack(anchor="e", pady=(0, 15))

        status_box = ctk.CTkLabel(container, text="", font=get_font(size=12), justify="right")
        status_box.pack(anchor="e", pady=10)

    # =========================================================================
    # 4. تبويب الإعدادات العامة (مرتب بدقة بدون فجوات)
    # =========================================================================
    def _build_general_tab_content(self):
        container = ctk.CTkFrame(self.tab_general, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=25)

        ctk.CTkLabel(container, text="⚙️ إعدادات العيادة العامة والتفضيلات", font=get_font(size=16, weight="bold"), text_color=THEME["primary"]).pack(anchor="e", pady=(0, 6))
        ctk.CTkLabel(container, text="البيانات المحفوظة هنا تُطبع تلقائياً في ترويسة كشوفات الـ PDF وتقارير الـ Excel الرسمية.", font=get_font(size=12), text_color=THEME["text_secondary"]).pack(anchor="e", pady=(0, 16))

        # بطاقة هوية وشعار العيادة المعتمد
        brand_card = ctk.CTkFrame(
            container, 
            corner_radius=12, 
            fg_color=THEME["bg_card_secondary"],
            border_width=1, 
            border_color=THEME["border_light"]
        )
        brand_card.pack(fill="x", pady=(0, 14), padx=4)

        self.settings_logo = get_clinic_logo(variant="full", size=(76, 76))
        if self.settings_logo:
            ctk.CTkLabel(brand_card, text="", image=self.settings_logo).pack(side="left", padx=16, pady=12)

        b_text = ctk.CTkFrame(brand_card, fg_color="transparent")
        b_text.pack(side="right", fill="x", expand=True, padx=16, pady=12)

        ctk.CTkLabel(
            b_text,
            text="شعار وهوية النظام المعتمدة: نظام عيادتي (My Clinic)",
            font=get_font(size=14, weight="bold"),
            text_color=THEME["primary"],
            anchor="e"
        ).pack(fill="x", pady=(0, 3))

        ctk.CTkLabel(
            b_text,
            text="يظهر الشعار تلقائياً في واجهة تسجيل الدخول، لوحة التحكم المركزية، الشريط الجانبي، والتقارير المعتمدة.",
            font=get_font(size=12),
            text_color=THEME["text_secondary"],
            anchor="e"
        ).pack(fill="x")

        info_frame = ctk.CTkFrame(
            container, 
            corner_radius=12, 
            fg_color=THEME["bg_card_secondary"],
            border_width=1,
            border_color=THEME["border_light"]
        )
        info_frame.pack(fill="x", pady=(0, 16), padx=4)

        ctk.CTkLabel(
            info_frame, 
            text="🏥 بيانات العيادة الرسمية للفواتير والتقارير", 
            font=get_font(size=13, weight="bold"),
            text_color=THEME["text_primary"]
        ).pack(anchor="e", padx=20, pady=(14, 8))

        def add_setting_row(label_text, default_val):
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(row, text=label_text, font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"], width=110, anchor="e").pack(side="right", padx=(0, 10))
            entry = ctk.CTkEntry(row, width=380, height=34, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
            entry.pack(side="right")
            entry.insert(0, default_val)
            return setup_rtl_entry(entry)

        self.s_clinic_name = add_setting_row("اسم العيادة:", self.clinic_info.get("name", ""))
        self.s_phone = add_setting_row("هاتف العيادة:", self.clinic_info.get("phone", ""))
        self.s_address = add_setting_row("عنوان العيادة:", self.clinic_info.get("address", ""))

        def save_general_settings():
            self.clinic_info = {
                "name": self.s_clinic_name.get().strip(),
                "phone": self.s_phone.get().strip(),
                "address": self.s_address.get().strip(),
                "appearance": "Dark"
            }
            try:
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.clinic_info, f, ensure_ascii=False, indent=4)
                success_lbl.configure(text="✅ تم حفظ وتحديث الإعدادات بنجاح!", text_color=THEME["success"])
            except Exception as ex:
                success_lbl.configure(text=f"خطأ في الحفظ: {ex}", text_color=THEME["danger"])

        ctk.CTkButton(
            container, text="💾 حفظ التغييرات العامة", font=get_font(size=13, weight="bold"),
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"], height=40, width=220, command=save_general_settings
        ).pack(anchor="e", pady=10)

        success_lbl = ctk.CTkLabel(container, text="", font=get_font(size=12))
        success_lbl.pack(anchor="e", pady=5)
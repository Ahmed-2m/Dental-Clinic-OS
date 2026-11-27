import customtkinter as ctk
from backend.staff_repo import StaffRepository
from ui.theme import THEME, get_font, setup_rtl_entry


class StaffView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.staff_repo = StaffRepository()
        self.selected_emp_id = None

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._build_form_section()
        self._build_cards_section()

    def _build_form_section(self):
        self.form_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=THEME["bg_card_secondary"], border_width=1, border_color=THEME["border_light"])
        self.form_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        self.form_title_lbl = ctk.CTkLabel(
            self.form_frame,
            text="👨‍⚕️ تسجيل موظف أو طبيب جديد",
            font=get_font(size=16, weight="bold"),
            text_color=THEME["primary"],
        )
        self.form_title_lbl.pack(anchor="e", padx=20, pady=(15, 10))

        def add_field(label_text, placeholder):
            lbl = ctk.CTkLabel(self.form_frame, text=label_text, font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"])
            lbl.pack(anchor="e", padx=20, pady=(4, 1))
            entry = ctk.CTkEntry(self.form_frame, placeholder_text=placeholder, width=300, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
            entry.pack(anchor="e", padx=20, pady=(0, 6))
            return setup_rtl_entry(entry)

        self.entry_name = add_field("الاسم الكامل:", "أدخل الاسم...")
        self.entry_phone = add_field("رقم الهاتف المحمول:", "77xxxxxxx")
        self.entry_address = add_field("العنوان والمنطقة:", "مثال: صنعاء، حدة")
        self.entry_job = add_field("المسمى الوظيفي:", "طبيب أسنان / استقبال")
        self.entry_salary = add_field("الراتب الشهري (ر.ي):", "0.00")
        self.entry_hire_date = add_field("تاريخ التعيين:", "2026-11-01")
        self.entry_username = add_field("اسم المستخدم للنظام:", "dr_zakaria")
        self.entry_password = add_field("كلمة المرور:", "******")
        self.entry_role = add_field("الدور / الصلاحية:", "admin / doctor")

        status_lbl = ctk.CTkLabel(self.form_frame, text="حالة الموظف:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"])
        status_lbl.pack(anchor="e", padx=20, pady=(4, 1))
        self.combo_status = ctk.CTkComboBox(self.form_frame, values=["active", "inactive"], width=300, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.combo_status.set("active")
        self.combo_status.pack(anchor="e", padx=20, pady=(0, 10))

        btn_row = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        btn_row.pack(anchor="e", padx=20, pady=(5, 15))

        self.cancel_btn = ctk.CTkButton(
            btn_row,
            text="❌ إلغاء التعديل",
            font=get_font(size=11),
            fg_color=THEME["danger_soft"],
            hover_color=THEME["danger"],
            text_color=THEME["danger"],
            height=32,
            command=self.reset_form,
        )

        self.save_btn = ctk.CTkButton(
            btn_row,
            text="💾 حفظ بيانات الموظف",
            font=get_font(size=13, weight="bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_light"],
            height=34,
            command=self.save_or_update_staff,
        )
        self.save_btn.pack(side="right", padx=(5, 0))

    def _build_cards_section(self):
        main_list_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=THEME["bg_card_secondary"], border_width=1, border_color=THEME["border_light"])
        main_list_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        main_list_frame.grid_rowconfigure(1, weight=1)
        main_list_frame.grid_columnconfigure(0, weight=1)

        header_layout = ctk.CTkFrame(main_list_frame, fg_color="transparent")
        header_layout.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        title_lbl = ctk.CTkLabel(
            header_layout,
            text="👥 بطاقات وسجلات الكادر الطبي والموظفين",
            font=get_font(size=15, weight="bold"),
            text_color=THEME["text_primary"],
        )
        title_lbl.pack(side="right")

        refresh_btn = ctk.CTkButton(
            header_layout,
            text="🔄 تحديث",
            font=get_font(size=11),
            width=85,
            height=28,
            fg_color=THEME["bg_app"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            border_width=1,
            border_color=THEME["border"],
            command=self.refresh_list,
        )
        refresh_btn.pack(side="left")

        self.scrollable_cards_container = ctk.CTkScrollableFrame(main_list_frame, fg_color="transparent")
        self.scrollable_cards_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 15))

        self.refresh_list()

    def save_or_update_staff(self):
        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()
        address = self.entry_address.get().strip()
        job = self.entry_job.get().strip()
        salary = self.entry_salary.get().strip()
        hire_date = self.entry_hire_date.get().strip()
        user = self.entry_username.get().strip()
        pwd = self.entry_password.get().strip()
        role = self.entry_role.get().strip()
        status = self.combo_status.get().strip()

        if not name:
            return

        if self.selected_emp_id is None:
            success, msg = self.staff_repo.add(name, phone, address, job, salary, hire_date, user, pwd, role, status)
        else:
            success, msg = self.staff_repo.update(self.selected_emp_id, name, phone, address, job, salary, hire_date, user, pwd, role, status)

        if success:
            self.reset_form()
            self.refresh_list()

    def reset_form(self):
        self.selected_emp_id = None
        for entry in [
            self.entry_name, self.entry_phone, self.entry_address, self.entry_job,
            self.entry_salary, self.entry_hire_date, self.entry_username,
            self.entry_password, self.entry_role,
        ]:
            entry.delete(0, "end")

        self.combo_status.set("active")
        self.form_title_lbl.configure(text="👨‍⚕️ تسجيل موظف أو طبيب جديد", text_color=THEME["primary"])
        self.save_btn.configure(text="💾 حفظ بيانات الموظف", fg_color=THEME["primary"], hover_color=THEME["primary_hover"])
        self.cancel_btn.pack_forget()

    def load_staff_for_edit(self, s):
        self.selected_emp_id = s[0]
        self.entry_name.delete(0, "end"); self.entry_name.insert(0, str(s[1] or ""))
        self.entry_phone.delete(0, "end"); self.entry_phone.insert(0, str(s[2] or ""))
        self.entry_address.delete(0, "end"); self.entry_address.insert(0, str(s[3] or ""))
        self.entry_job.delete(0, "end"); self.entry_job.insert(0, str(s[4] or ""))
        self.entry_salary.delete(0, "end"); self.entry_salary.insert(0, str(s[5] or ""))
        self.entry_hire_date.delete(0, "end"); self.entry_hire_date.insert(0, str(s[6] or ""))
        self.entry_username.delete(0, "end"); self.entry_username.insert(0, str(s[7] or ""))
        self.entry_password.delete(0, "end")
        self.entry_role.delete(0, "end"); self.entry_role.insert(0, str(s[8] or ""))
        self.combo_status.set(s[9] if s[9] in ["active", "inactive"] else "active")

        self.form_title_lbl.configure(text=f"✏️ تعديل بيانات الموظف (#{s[0]} - {s[1]})", text_color=THEME["warning"])
        self.save_btn.configure(text="💾 حفظ التعديلات", fg_color=THEME["warning"], hover_color=THEME["warning_hover"])
        self.cancel_btn.pack(side="right", padx=(5, 0))

    def delete_staff_action(self, emp_id):
        success, msg = self.staff_repo.delete(emp_id)
        if success:
            if self.selected_emp_id == emp_id:
                self.reset_form()
            self.refresh_list()

    def refresh_list(self):
        for widget in self.scrollable_cards_container.winfo_children():
            widget.destroy()

        staff_data = self.staff_repo.get_all()
        if staff_data:
            for s in staff_data:
                card = ctk.CTkFrame(self.scrollable_cards_container, corner_radius=12, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"])
                card.pack(fill="x", pady=6, padx=4)

                top_c = ctk.CTkFrame(card, fg_color="transparent")
                top_c.pack(fill="x", padx=14, pady=(10, 2))

                ctk.CTkLabel(
                    top_c,
                    text=f"👨‍⚕️ {s[1]}   |   المسمى: {s[4] or 'غير محدد'}",
                    font=get_font(size=13, weight="bold"),
                    text_color=THEME["text_primary"],
                ).pack(side="right")

                actions_frame = ctk.CTkFrame(card, fg_color="transparent")
                actions_frame.pack(fill="x", padx=14, pady=(2, 10))

                sub_txt = f"📞 الهاتف: {s[2] or 'بدون'} | 🏠 العنوان: {s[3] or '---'} | 💰 الراتب: {float(s[5] or 0):,.2f} ر.ي | 🛡️ الدور: {s[8]}"
                ctk.CTkLabel(actions_frame, text=sub_txt, font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right")

                ctk.CTkButton(
                    actions_frame,
                    text="🗑️ حذف",
                    font=get_font(size=10),
                    width=65,
                    height=26,
                    fg_color=THEME["danger_soft"],
                    hover_color=THEME["danger"],
                    text_color=THEME["danger"],
                    command=lambda eid=s[0]: self.delete_staff_action(eid),
                ).pack(side="left", padx=2)

                ctk.CTkButton(
                    actions_frame,
                    text="✏️ تعديل",
                    font=get_font(size=10),
                    width=65,
                    height=26,
                    fg_color=THEME["primary"],
                    hover_color=THEME["primary_hover"],
                    text_color=THEME["text_light"],
                    command=lambda staff=s: self.load_staff_for_edit(staff),
                ).pack(side="left", padx=2)
        else:
            ctk.CTkLabel(self.scrollable_cards_container, text="لا يوجد موظفون مسجلون حالياً.", font=get_font(size=12), text_color=THEME["text_muted"]).pack(pady=35)
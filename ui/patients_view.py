import datetime
import customtkinter as ctk

from backend.patients_repo import PatientsRepository
from ui.theme import THEME, get_font, setup_rtl_entry, setup_rtl_textbox

class PatientsView(ctk.CTkFrame):
    def __init__(self, parent, user_role="admin"):
        super().__init__(parent, fg_color="transparent")
        self.patients_repo = PatientsRepository()
        self.user_role = str(user_role).lower()
        self.selected_patient_id = None

        # نظام التبويبات العصري للمرضى (التبويب الأيمن هو الافتراضي)
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=14,
            segmented_button_selected_color=THEME["primary"],
            segmented_button_selected_hover_color=THEME["primary_hover"],
            segmented_button_unselected_color=THEME["bg_card_secondary"],
            segmented_button_unselected_hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_light"]
        )
        self.tabview.pack(fill="both", expand=True)

        self.tab_form_title = "📝 تسجيل / تعديل ملف مريض"
        self.tab_directory_title = "📋 بطاقات وسجلات المرضى"

        self.tab_form = self.tabview.add(self.tab_form_title)
        self.tab_directory = self.tabview.add(self.tab_directory_title)

        # تعيين التبويب النشط على اليمين افتراضياً
        self.tabview.set(self.tab_directory_title)

        self._build_directory_tab()
        self._build_form_tab()

    # =========================================================================
    # 1. تبويب بطاقات وسجلات المرضى (Directory & Cards)
    # =========================================================================
    def _build_directory_tab(self):
        container = self.tab_directory

        # شريط البحث والتحكم العلوي
        controls_card = ctk.CTkFrame(
            container, 
            fg_color=THEME["bg_card_secondary"], 
            corner_radius=12, 
            border_width=1, 
            border_color=THEME["border_light"]
        )
        controls_card.pack(fill="x", padx=12, pady=(10, 8))

        row = ctk.CTkFrame(controls_card, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=12)

        # اليمين: حقل البحث الفوري وشارة النتائج مع دعم RTL
        self.search_entry = ctk.CTkEntry(
            row,
            placeholder_text="🔍 ابحث بالاسم أو برقم الهاتف...",
            width=350,
            height=42,
            justify="right",
            font=get_font(size=14),
            fg_color=THEME["bg_app"],
            border_color=THEME["border"]
        )
        setup_rtl_entry(self.search_entry)
        self.search_entry.pack(side="right", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_list())

        self.patient_count_badge = ctk.CTkLabel(
            row,
            text="",
            font=get_font(size=13, weight="bold"),
            text_color=THEME["teal"]
        )
        self.patient_count_badge.pack(side="right", padx=10)

        # اليسار: أزرار الإجراءات
        add_quick_btn = ctk.CTkButton(
            row,
            text="➕ تسجيل مريض جديد",
            font=get_font(size=14, weight="bold"),
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            height=42,
            command=self._go_to_new_patient_tab
        )
        add_quick_btn.pack(side="left", padx=4)

        refresh_btn = ctk.CTkButton(
            row,
            text="🔄 تحديث",
            font=get_font(size=13, weight="bold"),
            width=95,
            height=42,
            fg_color=THEME["bg_card"],
            hover_color=THEME["bg_card_hover"],
            border_width=1,
            border_color=THEME["border"],
            command=self.refresh_list
        )
        refresh_btn.pack(side="left", padx=4)

        # حاوية البطاقات القابلة للتمرير
        self.scrollable_cards = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.scrollable_cards.pack(fill="both", expand=True, padx=10, pady=6)

        self.refresh_list()

    def _go_to_new_patient_tab(self):
        self.reset_form()
        self.tabview.set(self.tab_form_title)

    def refresh_list(self):
        for widget in self.scrollable_cards.winfo_children():
            widget.destroy()

        patients_data = self.patients_repo.get_all()
        query = self.search_entry.get().strip().lower() if hasattr(self, "search_entry") else ""

        if patients_data:
            if query:
                patients_data = [
                    p for p in patients_data 
                    if query in (p[1] or "").lower() or query in (p[2] or "").lower()
                ]

            total_found = len(patients_data)
            self.patient_count_badge.configure(text=f"إجمالي النتائج: {total_found} مريض")

            for p in patients_data:
                # p: (id, name, phone, address, gender, dob, history)
                card = ctk.CTkFrame(
                    self.scrollable_cards, 
                    corner_radius=12, 
                    fg_color=THEME["bg_card_secondary"],
                    border_width=1,
                    border_color=THEME["border"]
                )
                card.pack(fill="x", pady=6, padx=4)

                header_row = ctk.CTkFrame(card, fg_color="transparent")
                header_row.pack(fill="x", padx=16, pady=(12, 4))

                # يمين: اسم المريض ورقم الملف
                title_lbl = ctk.CTkLabel(
                    header_row,
                    text=f"👤 {p[1]}   |   الملف #{p[0]}",
                    font=get_font(size=16, weight="bold"),
                    text_color=THEME["text_primary"]
                )
                title_lbl.pack(side="right")

                # يسار: زر التعديل (متاح للجميع)
                edit_btn = ctk.CTkButton(
                    header_row,
                    text="✏️ تعديل البيانات",
                    font=get_font(size=13, weight="bold"),
                    width=120,
                    height=32,
                    fg_color=THEME["primary"],
                    hover_color=THEME["primary_hover"],
                    command=lambda patient=p: self.load_patient_for_edit(patient)
                )
                edit_btn.pack(side="left", padx=4)

                # زر الحذف (يظهر حصرياً للـ admin فقط)
                if self.user_role == "admin":
                    delete_btn = ctk.CTkButton(
                        header_row,
                        text="🗑️ حذف",
                        font=get_font(size=12, weight="bold"),
                        width=85,
                        height=32,
                        fg_color=THEME["danger_soft"],
                        hover_color=THEME["danger"],
                        command=lambda pid=p[0]: self.delete_patient_action(pid)
                    )
                    delete_btn.pack(side="left", padx=4)

                # تفاصيل المريض
                details_row = ctk.CTkFrame(card, fg_color="transparent")
                details_row.pack(fill="x", padx=16, pady=(4, 12))

                gender_ar = "ذكر" if p[4] == 'male' else "أنثى"
                details_txt = (
                    f"📞 الهاتف: {p[2] or 'بدون'}   |   📍 العنوان: {p[3] or 'غير محدد'}   |   "
                    f"⚧ الجنس: {gender_ar}   |   📅 الميلاد: {str(p[5] or '---')}\n"
                    f"🩺 التاريخ الطبي والشكوى: {p[6] or 'لا توجد ملاحظات سابقة'}"
                )

                ctk.CTkLabel(
                    details_row,
                    text=details_txt,
                    font=get_font(size=13),
                    text_color=THEME["text_secondary"],
                    justify="right"
                ).pack(anchor="e")
        else:
            self.patient_count_badge.configure(text="")
            ctk.CTkLabel(
                self.scrollable_cards,
                text="لا يوجد أي مرضى مسجلين حتى الآن.\nيمكنك استخدام تبويب التسجيل لإضافة أول مريض.",
                font=get_font(size=14, weight="bold"),
                text_color=THEME["text_muted"]
            ).pack(pady=40)

    # =========================================================================
    # منتقي التاريخ (التقويم المنبثق)
    # =========================================================================
    def _open_date_picker(self):
        """فتح نافذة منبثقة لاختيار تاريخ الميلاد بسهولة"""
        top = ctk.CTkToplevel(self)
        top.title("اختر تاريخ الميلاد")
        top.geometry("360x240")
        top.resizable(False, False)
        top.grab_set()

        ctk.CTkLabel(
            top, text="📅 حدد تاريخ الميلاد (السنة / الشهر / اليوم)", 
            font=get_font(size=14, weight="bold"), text_color=THEME["primary"]
        ).pack(pady=15)

        row = ctk.CTkFrame(top, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=10)

        current_year = datetime.date.today().year
        years = [str(y) for y in range(current_year, current_year - 100, -1)]
        months = [f"{m:02d}" for m in range(1, 13)]
        days = [f"{d:02d}" for d in range(1, 32)]

        # اختيار السنة
        cb_year = ctk.CTkComboBox(row, values=years, width=115, height=36, justify="center", font=get_font(size=13), fg_color=THEME["bg_app"], border_color=THEME["border"])
        cb_year.pack(side="right", padx=5)
        cb_year.set(str(current_year - 30))

        # اختيار الشهر
        cb_month = ctk.CTkComboBox(row, values=months, width=85, height=36, justify="center", font=get_font(size=13), fg_color=THEME["bg_app"], border_color=THEME["border"])
        cb_month.pack(side="right", padx=5)
        cb_month.set("01")

        # اختيار اليوم
        cb_day = ctk.CTkComboBox(row, values=days, width=85, height=36, justify="center", font=get_font(size=13), fg_color=THEME["bg_app"], border_color=THEME["border"])
        cb_day.pack(side="right", padx=5)
        cb_day.set("01")

        def confirm_date():
            selected = f"{cb_year.get()}-{cb_month.get()}-{cb_day.get()}"
            self.entry_dob.delete(0, "end")
            self.entry_dob.insert(0, selected)
            top.destroy()

        ctk.CTkButton(
            top, text="✔ تأكيد واختيار التاريخ", width=190, height=38,
            fg_color=THEME["success"], hover_color=THEME["success_hover"],
            font=get_font(size=13, weight="bold"), command=confirm_date
        ).pack(pady=15)

    # =========================================================================
    # 2. تبويب تسجيل وتعديل ملف مريض (Form مع دعم RTL كامل)
    # =========================================================================
    def _build_form_tab(self):
        container = self.tab_form

        form_center = ctk.CTkFrame(
            container, 
            fg_color=THEME["bg_card_secondary"], 
            corner_radius=14, 
            border_width=1, 
            border_color=THEME["border_light"]
        )
        form_center.pack(fill="both", expand=True, padx=40, pady=15)

        self.form_title_lbl = ctk.CTkLabel(
            form_center, 
            text="📝 تسجيل ملف مريض جديد في النظام", 
            font=get_font(size=18, weight="bold"),
            text_color=THEME["primary"]
        )
        self.form_title_lbl.pack(anchor="e", padx=30, pady=(18, 12))

        def add_field(label_text, placeholder):
            lbl = ctk.CTkLabel(form_center, text=label_text, font=get_font(size=13, weight="bold"), text_color=THEME["text_secondary"])
            lbl.pack(anchor="e", padx=30, pady=(6, 2))
            entry = ctk.CTkEntry(
                form_center, 
                placeholder_text=placeholder, 
                height=40, 
                justify="right",
                font=get_font(size=14),
                fg_color=THEME["bg_app"], 
                border_color=THEME["border"]
            )
            setup_rtl_entry(entry)
            entry.pack(fill="x", padx=30, pady=(0, 8))
            return entry

        self.entry_name = add_field("اسم المريض الرباعي:", "أدخل الاسم الكامل للمريض...")
        self.entry_phone = add_field("رقم الهاتف المحمول:", "77xxxxxxx")
        self.entry_address = add_field("العنوان والمنطقة:", "مثال: صنعاء - حدة")

        meta_row = ctk.CTkFrame(form_center, fg_color="transparent")
        meta_row.pack(fill="x", padx=30, pady=(6, 8))

        ctk.CTkLabel(meta_row, text="الجنس:", font=get_font(size=13, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.combo_gender = ctk.CTkComboBox(meta_row, values=["ذكر", "أنثى"], width=140, height=38, font=get_font(size=13), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.combo_gender.set("ذكر")
        self.combo_gender.pack(side="right", padx=(0, 24))

        # تاريخ الميلاد مع زر التقويم المنبثق
        ctk.CTkLabel(meta_row, text="تاريخ الميلاد:", font=get_font(size=13, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        
        self.entry_dob = ctk.CTkEntry(meta_row, placeholder_text="1995-05-12", width=150, height=38, font=get_font(size=13), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(self.entry_dob)
        self.entry_dob.pack(side="right", padx=(0, 6))

        btn_calendar = ctk.CTkButton(
            meta_row, text="📅", width=42, height=38,
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
            font=get_font(size=15), command=self._open_date_picker
        )
        btn_calendar.pack(side="right")

        lbl_hist = ctk.CTkLabel(form_center, text="التاريخ الطبي والشكوى الرئيسية والحساسية الدوائية:", font=get_font(size=13, weight="bold"), text_color=THEME["text_secondary"])
        lbl_hist.pack(anchor="e", padx=30, pady=(6, 2))

        self.entry_history = ctk.CTkTextbox(form_center, height=85, font=get_font(size=14), fg_color=THEME["bg_app"], border_color=THEME["border"], border_width=1)
        setup_rtl_textbox(self.entry_history)
        self.entry_history.pack(fill="x", padx=30, pady=(0, 18))

        btn_row = ctk.CTkFrame(form_center, fg_color="transparent")
        btn_row.pack(fill="x", padx=30, pady=(0, 20))

        self.save_btn = ctk.CTkButton(
            btn_row, 
            text="💾 حفظ الملف الطبي", 
            font=get_font(size=14, weight="bold"),
            fg_color=THEME["primary"], 
            hover_color=THEME["primary_hover"],
            height=44,
            width=180,
            command=self.save_or_update_patient
        )
        self.save_btn.pack(side="right", padx=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            btn_row, 
            text="❌ إلغاء والعودة", 
            font=get_font(size=13, weight="bold"),
            fg_color=THEME["danger_soft"], 
            hover_color=THEME["danger"],
            height=44,
            command=self.reset_form
        )

    def save_or_update_patient(self):
        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()
        address = self.entry_address.get().strip()
        gender = self.combo_gender.get().strip()
        dob = self.entry_dob.get().strip()
        history = self.entry_history.get("1.0", "end").strip()

        if not name:
            return

        if self.selected_patient_id is None:
            success, msg = self.patients_repo.add(name, phone, address, gender, dob, history)
        else:
            success, msg = self.patients_repo.update(self.selected_patient_id, name, phone, address, gender, dob, history)

        if success:
            self.reset_form()
            self.refresh_list()
            self.tabview.set(self.tab_directory_title)

    def reset_form(self):
        self.selected_patient_id = None
        self.entry_name.delete(0, "end")
        self.entry_phone.delete(0, "end")
        self.entry_address.delete(0, "end")
        self.entry_dob.delete(0, "end")
        self.entry_history.delete("1.0", "end")
        self.combo_gender.set("ذكر")
        self.form_title_lbl.configure(text="📝 تسجيل ملف مريض جديد في النظام", text_color=THEME["primary"])
        self.save_btn.configure(text="💾 حفظ الملف الطبي", fg_color=THEME["primary"])
        self.cancel_btn.pack_forget()

    def load_patient_for_edit(self, p):
        self.selected_patient_id = p[0]
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, p[1] or "")
        self.entry_phone.delete(0, "end")
        self.entry_phone.insert(0, p[2] or "")
        self.entry_address.delete(0, "end")
        self.entry_address.insert(0, p[3] or "")
        self.combo_gender.set("ذكر" if p[4] == 'male' else "أنثى")
        self.entry_dob.delete(0, "end")
        self.entry_dob.insert(0, str(p[5] or ""))
        self.entry_history.delete("1.0", "end")
        self.entry_history.insert("1.0", p[6] or "")

        self.form_title_lbl.configure(text=f"✏️ تعديل بيانات المريض (#{p[0]} - {p[1]})", text_color=THEME["warning"])
        self.save_btn.configure(text="💾 حفظ التعديلات", fg_color=THEME["warning"])
        self.cancel_btn.pack(side="right", padx=(0, 10))

        self.tabview.set(self.tab_form_title)

    def delete_patient_action(self, patient_id):
        if self.user_role != "admin":
            return
        success, msg = self.patients_repo.delete(patient_id)
        if success:
            if self.selected_patient_id == patient_id:
                self.reset_form()
            self.refresh_list()

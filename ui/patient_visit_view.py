import calendar
import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk

from backend.appointments_repo import AppointmentsRepository
from backend.patients_repo import PatientsRepository
from backend.patient_accounts_repo import PatientAccountsRepository
from backend.statements_repo import StatementsRepository
from backend.treatments_repo import TreatmentsRepository
from ui.theme import THEME, get_font, setup_rtl_entry


def _normalize_search_text(text: str) -> str:
    if not text:
        return ""
    arabic_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    return text.translate(arabic_digits).strip().lower()


def _parse_amount(raw_text: str) -> float:
    if not raw_text:
        return 0.0
    arabic_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    cleaned = raw_text.translate(arabic_digits).replace(",", "").replace("٬", "").strip()
    if not cleaned:
        return 0.0
    return float(cleaned)


class CalendarDialog(ctk.CTkToplevel):
    """نافذة منبثقة لاختيار التاريخ بشكل تقويم شهري تفاعلي"""

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("اختر التاريخ")
        self.geometry("320x350")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=THEME["bg_card"])

        self.callback = callback
        self.today = datetime.date.today()
        self.current_year = self.today.year
        self.current_month = self.today.month

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkButton(
            nav_frame,
            text="◀",
            width=40,
            height=32,
            fg_color=THEME["bg_card_secondary"],
            text_color=THEME["text_primary"],
            command=self.prev_month,
        ).pack(side="right")

        self.month_label = ctk.CTkLabel(
            nav_frame,
            text="",
            font=get_font(size=14, weight="bold"),
            text_color=THEME["primary"],
        )
        self.month_label.pack(side="right", expand=True)

        ctk.CTkButton(
            nav_frame,
            text="▶",
            width=40,
            height=32,
            fg_color=THEME["bg_card_secondary"],
            text_color=THEME["text_primary"],
            command=self.next_month,
        ).pack(side="right")

        self.days_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.days_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.render_calendar()

    def render_calendar(self):
        for w in self.days_frame.winfo_children():
            w.destroy()

        months_ar = [
            "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
            "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
        ]
        self.month_label.configure(text=f"{months_ar[self.current_month - 1]} {self.current_year}")

        days_names = ["سبت", "جمعة", "خميس", "أربعاء", "ثلاثاء", "إثنين", "أحد"]
        for col, d_name in enumerate(days_names):
            lbl = ctk.CTkLabel(
                self.days_frame,
                text=d_name,
                font=get_font(size=11, weight="bold"),
                text_color=THEME["text_muted"],
            )
            lbl.grid(row=0, column=6 - col, padx=2, pady=2, sticky="nsew")

        cal = calendar.monthcalendar(self.current_year, self.current_month)
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day != 0:
                    is_today = (
                        day == self.today.day
                        and self.current_month == self.today.month
                        and self.current_year == self.today.year
                    )
                    btn = ctk.CTkButton(
                        self.days_frame,
                        text=str(day),
                        width=35,
                        height=32,
                        fg_color=THEME["primary"] if is_today else THEME["bg_app"],
                        hover_color=THEME["primary_hover"],
                        text_color=THEME["text_light"] if is_today else THEME["text_primary"],
                        font=get_font(size=12, weight="bold"),
                        command=lambda d=day: self.select_date(d),
                    )
                    btn.grid(row=row_idx + 1, column=6 - col_idx, padx=2, pady=2)

    def prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.render_calendar()

    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.render_calendar()

    def select_date(self, day):
        selected_str = f"{self.current_year:04d}-{self.current_month:02d}-{day:02d}"
        self.callback(selected_str)
        self.destroy()


class PatientVisitView(ctk.CTkFrame):
    def __init__(self, parent, user_role="admin"):
        super().__init__(parent, fg_color="transparent")
        self.user_role = str(user_role).lower()

        self.patients_repo = PatientsRepository()
        self.treatments_repo = TreatmentsRepository()
        self.accounts_repo = PatientAccountsRepository()
        self.appointments_repo = AppointmentsRepository()
        self.statements_repo = StatementsRepository()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=0, sticky="nsew")
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        self.selected_patient = None
        self.editing_treatment_id = None
        self.search_placeholder = "ابحث باسم المريض أو رقم الهاتف أو رقم الملف..."
        self.show_search_screen()

    def _clear_content(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def _fetch_all_patients(self):
        if hasattr(self.patients_repo, "get_all_patients"):
            return self.patients_repo.get_all_patients() or []
        if hasattr(self.patients_repo, "get_all"):
            return self.patients_repo.get_all() or []
        return []

    def _get_patient_debt(self, patient_id) -> float:
        conn = self.patients_repo.db.get_connection()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(total_amount - paid_amount), 0) FROM patient_accounts WHERE patient_id = %s;",
                (patient_id,),
            )
            res = cursor.fetchone()
            cursor.close()
            conn.close()
            return float(res[0] or 0.0) if res else 0.0
        except Exception:
            return 0.0

    def _get_treatment_paid_amount(self, treatment_id) -> float:
        conn = self.accounts_repo.db.get_connection()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(paid_amount), 0) FROM patient_accounts WHERE treatment_id = %s;",
                (treatment_id,),
            )
            res = cursor.fetchone()
            cursor.close()
            conn.close()
            return float(res[0] or 0.0) if res else 0.0
        except Exception:
            return 0.0

    # =========================================================================
    # 1. شاشة اختيار المريض (تعرض الكل افتراضياً + بحث بالاسم أو الهاتف)
    # =========================================================================
    def show_search_screen(self):
        self._clear_content()
        container = self.content_area

        center_card = ctk.CTkFrame(
            container,
            fg_color=THEME["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=THEME["border_light"],
        )
        center_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.72, relheight=0.74)

        ctk.CTkLabel(
            center_card,
            text="🔍 اختر المريض أو ابحث بالاسم أو رقم الهاتف لبدء الجلسة",
            font=get_font(size=16, weight="bold"),
            text_color=THEME["primary"],
        ).pack(pady=(22, 10))

        search_row = ctk.CTkFrame(center_card, fg_color="transparent")
        search_row.pack(fill="x", padx=36, pady=(0, 8))

        e_search = ctk.CTkEntry(
            search_row,
            placeholder_text=self.search_placeholder,
            height=42,
            justify="right",
            font=get_font(size=13),
            fg_color=THEME["bg_app"],
            border_color=THEME["border_focus"],
            border_width=1,
        )
        setup_rtl_entry(e_search)
        e_search.pack(side="right", fill="x", expand=True, padx=(0, 8))

        count_lbl = ctk.CTkLabel(
            search_row,
            text="",
            font=get_font(size=12, weight="bold"),
            text_color=THEME["teal"],
        )
        count_lbl.pack(side="left")

        results_scroll = ctk.CTkScrollableFrame(
            center_card,
            fg_color=THEME["bg_card_secondary"],
            corner_radius=10,
        )
        results_scroll.pack(fill="both", expand=True, padx=36, pady=(4, 22))

        all_patients = self._fetch_all_patients()

        def render_patients(event=None):
            raw_q = (e_search.get() or "").strip()
            query = "" if (not raw_q or raw_q == self.search_placeholder or "ابحث باسم" in raw_q) else _normalize_search_text(raw_q)

            for w in results_scroll.winfo_children():
                w.destroy()

            if query:
                matched = [
                    p for p in all_patients
                    if query in _normalize_search_text(str(p[1] or ""))
                    or (len(p) > 2 and query in _normalize_search_text(str(p[2] or "")))
                    or query == str(p[0] or "")
                ]
            else:
                matched = all_patients

            count_lbl.configure(text=f"العدد: {len(matched)}")

            if matched:
                for p in matched:
                    p_id = p[0]
                    p_name = p[1] or "بدون اسم"
                    p_phone = p[2] if len(p) > 2 and p[2] else "بدون هاتف"
                    ctk.CTkButton(
                        results_scroll,
                        text=f"👤  {p_name}    |    📞 {p_phone}    |    الملف #{p_id}",
                        fg_color=THEME["bg_app"],
                        hover_color=THEME["primary"],
                        anchor="e",
                        height=42,
                        corner_radius=8,
                        font=get_font(size=13, weight="bold"),
                        text_color=THEME["text_primary"],
                        command=lambda patient_obj=p: self.open_patient_dashboard(patient_obj),
                    ).pack(fill="x", pady=4, padx=6)
            else:
                empty_msg = (
                    "لا يوجد أي مرضى مسجلين في النظام بعد."
                    if not all_patients
                    else "عذراً، لم يتم العثور على مريض مطابق للاسم أو رقم الهاتف."
                )
                ctk.CTkLabel(
                    results_scroll,
                    text=empty_msg,
                    font=get_font(size=13, weight="bold"),
                    text_color=THEME["text_muted"],
                ).pack(pady=35)

        e_search.bind("<KeyRelease>", render_patients)
        render_patients()

    # =========================================================================
    # 2. ملف المريض (الجلسات العلاجية + الحساب والطباعة)
    # =========================================================================
    def open_patient_dashboard(self, patient):
        self.selected_patient = patient
        self.editing_treatment_id = None
        self._clear_content()
        container = self.content_area

        p_id, p_name = patient[0], patient[1]
        p_phone = patient[2] if len(patient) > 2 else "غير محدد"
        p_address = patient[3] if len(patient) > 3 else "غير محدد"
        med_hist = patient[6] if len(patient) > 6 else (patient[5] if len(patient) > 5 else "لا يوجد")
        total_debt = self._get_patient_debt(p_id)

        top_profile_card = ctk.CTkFrame(
            container,
            fg_color=THEME["bg_card"],
            corner_radius=14,
            border_width=1,
            border_color=THEME["border_light"],
        )
        top_profile_card.pack(fill="x", pady=(2, 8))

        top_inner = ctk.CTkFrame(top_profile_card, fg_color="transparent")
        top_inner.pack(fill="x", padx=16, pady=12)

        p_info_frame = ctk.CTkFrame(top_inner, fg_color="transparent")
        p_info_frame.pack(side="right")

        ctk.CTkLabel(
            p_info_frame,
            text=f"👤 ملف المريض: {p_name} (#{p_id})",
            font=get_font(size=17, weight="bold"),
            text_color=THEME["text_primary"],
        ).pack(anchor="e")

        ctk.CTkLabel(
            p_info_frame,
            text=f"📞 الهاتف: {p_phone}  |  📍 العنوان: {p_address}  |  🩺 التاريخ الطبي: {med_hist}",
            font=get_font(size=13),
            text_color=THEME["text_secondary"],
        ).pack(anchor="e")

        actions_side = ctk.CTkFrame(top_inner, fg_color="transparent")
        actions_side.pack(side="left")

        ctk.CTkButton(
            actions_side,
            text="🔙 تغيير المريض",
            fg_color=THEME["bg_card_secondary"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            border_width=1,
            border_color=THEME["border_light"],
            command=self.show_search_screen,
            width=140,
            height=38,
            font=get_font(size=13, weight="bold"),
        ).pack(side="left", padx=8)

        debt_color = THEME["danger"] if total_debt > 0 else THEME["success"]
        debt_text = f"⚠️ إجمالي الديون المتبقية: {total_debt:,.2f} ر.ي" if total_debt > 0 else "● الحساب خالص (لا يوجد دين)"
        ctk.CTkLabel(
            actions_side,
            text=debt_text,
            font=get_font(size=14, weight="bold"),
            text_color=debt_color,
            fg_color=THEME["bg_app"],
            corner_radius=8,
            padx=14,
            pady=6,
        ).pack(side="left")

        tabview = ctk.CTkTabview(
            container,
            fg_color=THEME["bg_card"],
            corner_radius=14,
            segmented_button_selected_color=THEME["primary"],
            segmented_button_selected_hover_color=THEME["primary_hover"],
            segmented_button_unselected_color=THEME["bg_card_secondary"],
            segmented_button_unselected_hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
        )
        tabview.pack(fill="both", expand=True)

        tab_payment = tabview.add("💰 كشف الحساب وسداد الديون")
        tab_treatment = tabview.add("🦷 تسجيل جلسة علاجية جديدة")
        tabview.set("🦷 تسجيل جلسة علاجية جديدة")

        self._build_treatment_tab(tab_treatment, patient)
        self._build_payment_tab(tab_payment, patient)

    def _build_treatment_tab(self, tab_treatment, patient):
        p_id, p_name = patient[0], patient[1]
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        form_t = ctk.CTkFrame(
            tab_treatment,
            fg_color=THEME["bg_card_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border_light"],
        )
        form_t.pack(fill="x", padx=12, pady=(10, 8))

        form_title_label = ctk.CTkLabel(
            form_t,
            text="➕ تسجيل تفاصيل الجلسة العلاجية وترحيل الفاتورة",
            font=get_font(size=15, weight="bold"),
            text_color=THEME["primary"],
        )
        form_title_label.pack(anchor="e", padx=16, pady=(12, 6))

        row1_t = ctk.CTkFrame(form_t, fg_color="transparent")
        row1_t.pack(fill="x", padx=14, pady=6)

        ctk.CTkLabel(row1_t, text="نوع العلاج:", font=get_font(size=13, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        e_type = ctk.CTkEntry(row1_t, placeholder_text="حشو، خلع، تنظيف، تقويم...", width=180, height=40, font=get_font(size=14), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_type)
        e_type.pack(side="right", padx=(0, 16))

        ctk.CTkLabel(row1_t, text="التكلفة:", font=get_font(size=13, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        e_cost = ctk.CTkEntry(row1_t, placeholder_text="0.00", width=100, height=40, font=get_font(size=14), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_cost)
        e_cost.pack(side="right", padx=(0, 16))

        ctk.CTkLabel(row1_t, text="المدفوع:", font=get_font(size=13, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        e_paid = ctk.CTkEntry(row1_t, placeholder_text="0.00", width=100, height=40, font=get_font(size=14), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_paid)
        e_paid.pack(side="right", padx=(0, 16))

        ctk.CTkLabel(row1_t, text="التاريخ:", font=get_font(size=13, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        e_date = ctk.CTkEntry(row1_t, width=110, height=40, font=get_font(size=13), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_date)
        e_date.pack(side="right", padx=(0, 4))
        e_date.insert(0, today_str)

        row_next_visit = ctk.CTkFrame(form_t, fg_color="transparent")
        row_next_visit.pack(fill="x", padx=14, pady=6)

        ctk.CTkLabel(row_next_visit, text="📅 تاريخ العودة (اختياري):", font=get_font(size=13, weight="bold"), text_color=THEME["warning"]).pack(side="right", padx=(0, 6))

        next_date_row = ctk.CTkFrame(row_next_visit, fg_color="transparent")
        next_date_row.pack(side="right", padx=(0, 16))

        e_next_visit = ctk.CTkEntry(next_date_row, placeholder_text="YYYY-MM-DD", width=130, height=38, font=get_font(size=13), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_next_visit)
        e_next_visit.pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            next_date_row,
            text="📅 التقويم",
            width=85,
            height=38,
            font=get_font(size=11, weight="bold"),
            fg_color=THEME["bg_card_secondary"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            command=lambda: CalendarDialog(self, lambda d_str: (e_next_visit.delete(0, "end"), e_next_visit.insert(0, d_str))),
        ).pack(side="left")

        row2_t = ctk.CTkFrame(form_t, fg_color="transparent")
        row2_t.pack(fill="x", padx=14, pady=(6, 12))

        save_t_btn = ctk.CTkButton(
            row2_t,
            text="💾 حفظ الجلسة وترحيل الفاتورة",
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_light"],
            width=220,
            height=42,
            font=get_font(size=13, weight="bold"),
        )
        save_t_btn.pack(side="left", padx=(0, 10))

        cancel_edit_btn = ctk.CTkButton(
            row2_t,
            text="❌ إلغاء التعديل",
            fg_color=THEME["danger_soft"],
            hover_color=THEME["danger"],
            width=120,
            height=42,
            font=get_font(size=13, weight="bold"),
            text_color=THEME["danger"],
        )

        e_desc = ctk.CTkEntry(row2_t, placeholder_text="وصف الإجراء الطبي، رقم السن، أو تفاصيل المعالجة والوصفة...", height=42, font=get_font(size=14), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_desc)
        e_desc.pack(side="right", fill="x", expand=True)

        def cancel_editing_mode():
            self.editing_treatment_id = None
            form_title_label.configure(text="➕ تسجيل تفاصيل الجلسة العلاجية وترحيل الفاتورة", text_color=THEME["primary"])
            save_t_btn.configure(text="💾 حفظ الجلسة وترحيل الفاتورة", fg_color=THEME["primary"], hover_color=THEME["primary_hover"])
            cancel_edit_btn.pack_forget()
            for entry in (e_type, e_cost, e_paid, e_desc, e_next_visit):
                entry.delete(0, "end")
            e_date.delete(0, "end")
            e_date.insert(0, today_str)

        cancel_edit_btn.configure(command=cancel_editing_mode)

        def save_treatment_action():
            try:
                cost = _parse_amount(e_cost.get())
                paid = _parse_amount(e_paid.get())
            except ValueError:
                messagebox.showwarning("تنبيه", "يرجى إدخال أرقام صحيحة للتكلفة والمبلغ المدفوع.")
                return
            if cost <= 0 or paid < 0:
                messagebox.showwarning("تنبيه", "يجب أن تكون التكلفة أكبر من صفر والمدفوع صفراً أو أكثر.")
                return

            t_type_val = e_type.get().strip()
            desc_val = e_desc.get().strip()
            date_val = e_date.get().strip() or today_str

            if self.editing_treatment_id:
                conn = self.treatments_repo.db.get_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE treatments SET treatment_type = %s, cost = %s, description = %s, treatment_date = %s WHERE treatment_id = %s;",
                            (t_type_val, cost, desc_val, date_val, self.editing_treatment_id),
                        )
                        remain = max(0.0, cost - paid)
                        status = "Paid" if remain <= 0 else ("Partial" if paid > 0 else "Unpaid")
                        cursor.execute(
                            "UPDATE patient_accounts SET total_amount = %s, paid_amount = %s, remaining_amount = %s, payment_status = %s, payment_date = %s WHERE treatment_id = %s;",
                            (cost, paid, remain, status, date_val, self.editing_treatment_id),
                        )
                        conn.commit()
                        cursor.close()
                        conn.close()
                        self.open_patient_dashboard(patient)
                    except Exception as ex:
                        print(f"Error updating treatment: {ex}")
            else:
                t_id, _ = self.treatments_repo.add_treatment(
                    patient_id=p_id,
                    emp_id=1,
                    treatment_type=t_type_val,
                    description=desc_val,
                    cost=cost,
                    treatment_date=date_val,
                    notes="",
                )
                if not t_id:
                    return

                remain = max(0.0, cost - paid)
                self.accounts_repo.add_invoice_from_treatment(
                    patient_id=p_id,
                    treatment_id=t_id,
                    total_amount=cost,
                    paid_amount=paid,
                    payment_status="Paid" if remain <= 0 else ("Partial" if paid > 0 else "Unpaid"),
                    payment_method="نقداً",
                    payment_date=date_val,
                )

                next_date_val = e_next_visit.get().strip()
                if next_date_val:
                    self.appointments_repo.add_appointment(
                        patient_id=p_id,
                        appointment_date=next_date_val,
                        appointment_time="10:00:00",
                        notes=f"موعد عودة للمريض: {p_name} - جلسة: {t_type_val}",
                    )

                self.open_patient_dashboard(patient)

        save_t_btn.configure(command=save_treatment_action)

        scroll_treatments = ctk.CTkScrollableFrame(tab_treatment, fg_color="transparent")
        scroll_treatments.pack(fill="both", expand=True, padx=10, pady=6)

        def load_treatment_into_form(tr):
            t_id, _, t_type, desc, t_cost, t_date, _ = tr
            current_paid = self._get_treatment_paid_amount(t_id)

            self.editing_treatment_id = t_id
            form_title_label.configure(text=f"✏️ تعديل تفاصيل الجلسة العلاجية (#{t_id})", text_color=THEME["warning"])
            save_t_btn.configure(text="💾 حفظ التعديلات", fg_color=THEME["warning"], hover_color=THEME["warning_hover"])
            cancel_edit_btn.pack(side="left", padx=(0, 10))

            e_type.delete(0, "end")
            e_type.insert(0, t_type or "")
            e_cost.delete(0, "end")
            e_cost.insert(0, f"{float(t_cost or 0):g}")
            e_paid.delete(0, "end")
            e_paid.insert(0, f"{current_paid:g}")
            e_date.delete(0, "end")
            e_date.insert(0, str(t_date or today_str))
            e_desc.delete(0, "end")
            e_desc.insert(0, desc or "")
            e_type.focus()

        treatments_list = self.treatments_repo.get_treatments_by_patient(p_id)
        if treatments_list:
            total_sessions = len(treatments_list)
            for idx, t in enumerate(reversed(treatments_list)):
                t_id, _, t_type, desc, t_cost, t_date, _ = t
                session_num = total_sessions - idx

                linked_appt_date = None
                conn_a = self.appointments_repo.db.get_connection()
                if conn_a:
                    try:
                        cur_a = conn_a.cursor()
                        cur_a.execute(
                            "SELECT appointment_date, notes FROM appointments WHERE patient_id = %s AND appointment_date >= %s ORDER BY appointment_date ASC LIMIT 1;",
                            (p_id, t_date),
                        )
                        res_appt = cur_a.fetchone()
                        if res_appt:
                            linked_appt_date = f"📅 موعد القادم المرتبط: {res_appt[0]} ({res_appt[1] or ''})"
                        cur_a.close()
                        conn_a.close()
                    except Exception:
                        pass

                card = ctk.CTkFrame(scroll_treatments, fg_color=THEME["bg_card_secondary"], corner_radius=10, border_width=1, border_color=THEME["border"])
                card.pack(fill="x", pady=4)

                ctk.CTkLabel(
                    card,
                    text=f"🦷 جلسة علاجية #{session_num}  |  النوع: {t_type or 'عام'}  |  التكلفة: {float(t_cost or 0):,.2f} ر.ي  |  التاريخ: {t_date}",
                    font=get_font(size=14, weight="bold"),
                    text_color=THEME["text_primary"],
                ).pack(anchor="e", padx=14, pady=(8, 2))

                ctk.CTkLabel(
                    card,
                    text=f"📝 الملاحظات والإجراء: {desc or 'لا يوجد وصف مدون'}",
                    font=get_font(size=13),
                    text_color=THEME["text_secondary"],
                ).pack(anchor="e", padx=14, pady=(0, 2))

                if linked_appt_date:
                    ctk.CTkLabel(
                        card,
                        text=linked_appt_date,
                        font=get_font(size=12, weight="bold"),
                        text_color=THEME["warning"],
                    ).pack(anchor="e", padx=14, pady=(0, 2))

                actions_row = ctk.CTkFrame(card, fg_color="transparent")
                actions_row.pack(fill="x", padx=14, pady=(4, 8))

                ctk.CTkButton(
                    actions_row,
                    text="✏️ تعديل الجلسة",
                    width=110,
                    height=32,
                    font=get_font(size=12, weight="bold"),
                    fg_color=THEME["primary"],
                    hover_color=THEME["primary_hover"],
                    text_color=THEME["text_light"],
                    command=lambda tr=t: load_treatment_into_form(tr),
                ).pack(side="left", padx=2)

                if self.user_role == "admin":
                    ctk.CTkButton(
                        actions_row,
                        text="🗑️ حذف الجلسة",
                        width=100,
                        height=32,
                        font=get_font(size=12, weight="bold"),
                        fg_color=THEME["danger_soft"],
                        hover_color=THEME["danger"],
                        text_color=THEME["danger"],
                        command=lambda tid=t_id: self.delete_treatment_action(tid, patient),
                    ).pack(side="left", padx=2)
        else:
            ctk.CTkLabel(
                scroll_treatments,
                text="لا توجد جلسات طبية مسجلة لهذا المريض حتى الآن.",
                font=get_font(size=14, weight="bold"),
                text_color=THEME["text_muted"],
            ).pack(pady=25)

    def _build_payment_tab(self, tab_payment, patient):
        p_id = patient[0]
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        form_p = ctk.CTkFrame(
            tab_payment,
            fg_color=THEME["bg_card_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border_light"],
        )
        form_p.pack(fill="x", padx=12, pady=(10, 8))

        ctk.CTkLabel(
            form_p,
            text="💵 سداد دفعة نقدية لتخفيض الذمة والمديونية",
            font=get_font(size=15, weight="bold"),
            text_color=THEME["success"],
        ).pack(anchor="e", padx=16, pady=(12, 6))

        row1_p = ctk.CTkFrame(form_p, fg_color="transparent")
        row1_p.pack(fill="x", padx=14, pady=6)

        ctk.CTkLabel(row1_p, text="المبلغ المراد سداده (ر.ي):", font=get_font(size=13, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        e_pay_val = ctk.CTkEntry(row1_p, placeholder_text="0.00", width=180, height=40, font=get_font(size=14), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_pay_val)
        e_pay_val.pack(side="right", padx=(0, 16))

        ctk.CTkLabel(row1_p, text="طريقة السداد:", font=get_font(size=13, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        cb_pay_method = ctk.CTkComboBox(row1_p, values=["نقداً", "تحويل بنكي", "شبكة"], width=140, height=40, font=get_font(size=13), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        cb_pay_method.pack(side="right", padx=(0, 4))
        cb_pay_method.set("نقداً")

        row2_p = ctk.CTkFrame(form_p, fg_color="transparent")
        row2_p.pack(fill="x", padx=14, pady=(6, 12))

        save_p_btn = ctk.CTkButton(
            row2_p,
            text="💵 تأكيد سداد الدين",
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            text_color=THEME["text_light"],
            width=180,
            height=42,
            font=get_font(size=13, weight="bold"),
        )
        save_p_btn.pack(side="left", padx=(0, 10))

        e_pay_notes = ctk.CTkEntry(row2_p, placeholder_text="ملاحظات السند المالي وسداد الذمة...", height=42, font=get_font(size=14), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_pay_notes)
        e_pay_notes.pack(side="right", fill="x", expand=True)

        def save_payment_action():
            try:
                pay_val = _parse_amount(e_pay_val.get())
            except ValueError:
                messagebox.showwarning("تنبيه", "يرجى إدخال مبلغ صحيح للسداد.")
                return
            if pay_val <= 0:
                return

            conn = self.patients_repo.db.get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO patient_accounts 
                        (patient_id, treatment_id, total_amount, paid_amount, remaining_amount, payment_date, payment_status, payment_method)
                        VALUES (%s, NULL, 0, %s, %s, %s, 'Paid', %s);
                        """,
                        (p_id, pay_val, -pay_val, today_str, cb_pay_method.get()),
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    self.open_patient_dashboard(patient)
                except Exception as ex:
                    print(f"Error: {ex}")

        save_p_btn.configure(command=save_payment_action)

        export_toolbar = ctk.CTkFrame(tab_payment, fg_color="transparent")
        export_toolbar.pack(fill="x", padx=12, pady=(4, 6))

        p_export_status = ctk.CTkLabel(export_toolbar, text="", font=get_font(size=13, weight="bold"))
        p_export_status.pack(side="left", padx=10)

        def export_statement(fmt: str):
            ext = ".pdf" if fmt == "pdf" else ".xlsx"
            filetypes = [("PDF Document", "*.pdf")] if fmt == "pdf" else [("Excel Spreadsheet", "*.xlsx")]
            fpath = filedialog.asksaveasfilename(
                defaultextension=ext,
                filetypes=filetypes,
                initialfile=f"Patient_Statement_{p_id}_{today_str}{ext}",
            )
            if not fpath:
                return
            if fmt == "pdf":
                ok, msg = self.statements_repo.export_patient_statement_pdf(p_id, fpath)
            else:
                ok, msg = self.statements_repo.export_patient_statement_excel(p_id, fpath)
            p_export_status.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

        ctk.CTkButton(
            export_toolbar,
            text="📄 استخراج كشف حساب المريض PDF",
            width=230,
            height=38,
            font=get_font(size=13, weight="bold"),
            fg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            text_color=THEME["text_light"],
            command=lambda: export_statement("pdf"),
        ).pack(side="right", padx=(0, 8))

        ctk.CTkButton(
            export_toolbar,
            text="📊 تصدير كشف الحساب Excel",
            width=210,
            height=38,
            font=get_font(size=13, weight="bold"),
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            text_color=THEME["text_light"],
            command=lambda: export_statement("excel"),
        ).pack(side="right", padx=(0, 8))

        scroll_accounts = ctk.CTkScrollableFrame(tab_payment, fg_color="transparent")
        scroll_accounts.pack(fill="both", expand=True, padx=10, pady=6)

        conn = self.patients_repo.db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.invoice_id, a.treatment_id, t.treatment_type, a.total_amount, a.paid_amount, 
                       a.payment_date, a.payment_status, a.payment_method
                FROM patient_accounts a
                LEFT JOIN treatments t ON a.treatment_id = t.treatment_id
                WHERE a.patient_id = %s
                ORDER BY a.invoice_id ASC;
                """,
                (p_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            if not rows:
                ctk.CTkLabel(
                    scroll_accounts,
                    text="لا توجد حركات مالية مسجلة لهذا المريض.",
                    font=get_font(size=14, weight="bold"),
                    text_color=THEME["text_muted"],
                ).pack(pady=25)
                return

            treatments_map = {
                tr[0]: idx + 1 for idx, tr in enumerate(self.treatments_repo.get_treatments_by_patient(p_id))
            }

            running_remain = 0.0
            processed_items = []
            for r in rows:
                inv_id, t_id, t_type, total, paid, p_date, status, method = r
                total_val = float(total or 0)
                paid_val = float(paid or 0)
                row_net = (total_val - paid_val) if t_id else (-paid_val)
                running_remain += row_net
                processed_items.append((inv_id, t_id, t_type, total_val, paid_val, running_remain, p_date, status, method))

            for item in reversed(processed_items):
                inv_id, t_id, t_type, total_val, paid_val, remain_val, p_date, _, method = item

                card = ctk.CTkFrame(scroll_accounts, fg_color=THEME["bg_card_secondary"], corner_radius=10, border_width=1, border_color=THEME["border"])
                card.pack(fill="x", pady=4)

                top_acc = ctk.CTkFrame(card, fg_color="transparent")
                top_acc.pack(fill="x", padx=14, pady=(8, 2))

                if t_id and t_id in treatments_map:
                    title_txt = f"🧾 فاتورة جلسة #{treatments_map[t_id]} ({t_type or 'علاج'}) | التاريخ: {p_date}"
                elif t_id:
                    title_txt = f"🧾 فاتورة علاجية #{t_id} | التاريخ: {p_date}"
                else:
                    title_txt = f"💵 سند قبض وسداد مباشر | التاريخ: {p_date}"

                ctk.CTkLabel(top_acc, text=title_txt, font=get_font(size=14, weight="bold"), text_color=THEME["text_primary"]).pack(side="right")

                stat_acc = ctk.CTkFrame(card, fg_color="transparent")
                stat_acc.pack(fill="x", padx=14, pady=(0, 2))

                remain_color = THEME["success"] if remain_val <= 0 else THEME["danger"]
                ctk.CTkLabel(
                    stat_acc,
                    text=f"التكلفة: {total_val:,.2f} ر.ي   |   المدفوع: {paid_val:,.2f} ر.ي   |   المتبقي: {remain_val:,.2f} ر.ي   |   الطريقة: {method or 'نقداً'}",
                    font=get_font(size=13, weight="bold"),
                    text_color=remain_color,
                ).pack(anchor="e")

                acc_actions = ctk.CTkFrame(card, fg_color="transparent")
                acc_actions.pack(fill="x", padx=14, pady=(4, 8))

                ctk.CTkButton(
                    acc_actions,
                    text="✏️ تعديل الحركة",
                    width=110,
                    height=32,
                    font=get_font(size=12, weight="bold"),
                    fg_color=THEME["primary"],
                    hover_color=THEME["primary_hover"],
                    text_color=THEME["text_light"],
                    command=lambda acc_item=(inv_id, t_id, total_val, paid_val, p_date, method): self.edit_account_row(acc_item, patient),
                ).pack(side="left", padx=2)

                if self.user_role == "admin":
                    ctk.CTkButton(
                        acc_actions,
                        text="🗑️ حذف الحركة",
                        width=100,
                        height=32,
                        font=get_font(size=12, weight="bold"),
                        fg_color=THEME["danger_soft"],
                        hover_color=THEME["danger"],
                        text_color=THEME["danger"],
                        command=lambda iid=inv_id: self.delete_account_action(iid, patient),
                    ).pack(side="left", padx=2)
        except Exception as e:
            print(f"Error: {e}")

    def delete_treatment_action(self, t_id, patient):
        if self.user_role != "admin":
            return
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذه الجلسة العلاجية نهائياً؟"):
            conn = self.treatments_repo.db.get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM patient_accounts WHERE treatment_id = %s;", (t_id,))
                    cursor.execute("DELETE FROM treatments WHERE treatment_id = %s;", (t_id,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    self.open_patient_dashboard(patient)
                except Exception as ex:
                    print(f"Error deleting treatment: {ex}")

    def edit_account_row(self, acc_obj, patient):
        inv_id, t_id, total_val, paid_val, _, method = acc_obj

        top = ctk.CTkToplevel(self)
        top.title(f"تعديل الحركة المالية #{inv_id}")
        top.geometry("380x280")
        top.resizable(False, False)
        top.grab_set()
        top.configure(fg_color=THEME["bg_card"])

        ctk.CTkLabel(top, text=f"✏️ تعديل الحركة المالية (#{inv_id})", font=get_font(size=14, weight="bold"), text_color=THEME["warning"]).pack(pady=15)

        form = ctk.CTkFrame(top, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20)

        ctk.CTkLabel(form, text="المبلغ المدفوع (ر.ي):", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e")
        e_paid = ctk.CTkEntry(form, width=340, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_paid)
        e_paid.pack(anchor="e", pady=(0, 8))
        e_paid.insert(0, f"{float(paid_val or 0):g}")

        ctk.CTkLabel(form, text="طريقة السداد:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e")
        cb_method = ctk.CTkComboBox(form, values=["نقداً", "تحويل بنكي", "شبكة"], width=340, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        cb_method.pack(anchor="e", pady=(0, 15))
        cb_method.set(method or "نقداً")

        def save_acc_edits():
            try:
                new_paid = _parse_amount(e_paid.get())
            except ValueError:
                messagebox.showwarning("تنبيه", "يرجى إدخال مبلغ صحيح.")
                return
            if new_paid < 0:
                return

            conn = self.accounts_repo.db.get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    if t_id is None:
                        new_remain = -new_paid
                        status = "Paid"
                    else:
                        new_remain = max(0.0, float(total_val) - new_paid)
                        status = "Paid" if new_remain <= 0 else ("Partial" if new_paid > 0 else "Unpaid")
                    cursor.execute(
                        "UPDATE patient_accounts SET paid_amount = %s, remaining_amount = %s, payment_status = %s, payment_method = %s WHERE invoice_id = %s;",
                        (new_paid, new_remain, status, cb_method.get(), inv_id),
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    top.destroy()
                    self.open_patient_dashboard(patient)
                except Exception as ex:
                    print(f"Error updating account: {ex}")

        ctk.CTkButton(
            top,
            text="💾 حفظ التعديلات",
            width=150,
            height=34,
            fg_color=THEME["warning"],
            hover_color=THEME["warning_hover"],
            text_color=THEME["text_light"],
            font=get_font(size=12, weight="bold"),
            command=save_acc_edits,
        ).pack(pady=10)

    def delete_account_action(self, inv_id, patient):
        if self.user_role != "admin":
            return
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذه الحركة المالية نهائياً؟"):
            conn = self.accounts_repo.db.get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM patient_accounts WHERE invoice_id = %s;", (inv_id,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    self.open_patient_dashboard(patient)
                except Exception as ex:
                    print(f"Error deleting account: {ex}")
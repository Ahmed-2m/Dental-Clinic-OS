import datetime
import calendar
import customtkinter as ctk
from tkinter import messagebox

from backend.patients_repo import PatientsRepository
from backend.treatments_repo import TreatmentsRepository
from backend.patient_accounts_repo import PatientAccountsRepository
from backend.appointments_repo import AppointmentsRepository
from ui.theme import THEME, get_font, setup_rtl_entry

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

        prev_btn = ctk.CTkButton(nav_frame, text="◀", width=40, height=32, fg_color=THEME["bg_card_secondary"], text_color=THEME["text_primary"], command=self.prev_month)
        prev_btn.pack(side="right")

        self.month_label = ctk.CTkLabel(nav_frame, text="", font=get_font(size=14, weight="bold"), text_color=THEME["primary"])
        self.month_label.pack(side="right", expand=True)

        next_btn = ctk.CTkButton(nav_frame, text="▶", width=40, height=32, fg_color=THEME["bg_card_secondary"], text_color=THEME["text_primary"], command=self.next_month)
        next_btn.pack(side="right")

        self.days_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.days_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.render_calendar()

    def render_calendar(self):
        for w in self.days_frame.winfo_children():
            w.destroy()

        months_ar = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
        self.month_label.configure(text=f"{months_ar[self.current_month - 1]} {self.current_year}")

        days_names = ["سبت", "جمعة", "خميس", "أربعاء", "ثلاثاء", "إثنين", "أحد"]
        for col, d_name in enumerate(days_names):
            lbl = ctk.CTkLabel(self.days_frame, text=d_name, font=get_font(size=11, weight="bold"), text_color=THEME["text_muted"])
            lbl.grid(row=0, column=6 - col, padx=2, pady=2, sticky="nsew")

        cal = calendar.monthcalendar(self.current_year, self.current_month)
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day != 0:
                    btn = ctk.CTkButton(
                        self.days_frame, text=str(day), width=35, height=32,
                        fg_color=THEME["bg_app"] if (day != self.today.day or self.current_month != self.today.month or self.current_year != self.today.year) else THEME["primary"],
                        hover_color=THEME["primary_hover"],
                        font=get_font(size=12, weight="bold"),
                        command=lambda d=day: self.select_date(d)
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

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=0, sticky="nsew")
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        self.selected_patient = None
        self.editing_treatment_id = None
        self.show_search_screen()

    def _clear_content(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def show_search_screen(self):
        self._clear_content()
        container = self.content_area

        center_card = ctk.CTkFrame(
            container, 
            fg_color=THEME["bg_card"], 
            corner_radius=16, 
            border_width=1, 
            border_color=THEME["border_light"]
        )
        center_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.68, relheight=0.68)

        ctk.CTkLabel(
            center_card, 
            text="🔍 ابحث عن المريض لبدء الجلسة الطبية أو مراجعة الحساب", 
            font=get_font(size=16, weight="bold"), 
            text_color=THEME["primary"]
        ).pack(pady=(28, 14))

        search_row = ctk.CTkFrame(center_card, fg_color="transparent")
        search_row.pack(fill="x", padx=40, pady=(0, 10))

        e_search = ctk.CTkEntry(
            search_row, 
            placeholder_text="اكتب اسم المريض أو رقم الهاتف هنا...", 
            height=42, 
            justify="right", 
            font=get_font(size=13),
            fg_color=THEME["bg_app"],
            border_color=THEME["border_focus"],
            border_width=1
        )
        setup_rtl_entry(e_search)
        e_search.pack(fill="x")

        results_scroll = ctk.CTkScrollableFrame(center_card, fg_color=THEME["bg_card_secondary"], corner_radius=10)
        results_scroll.pack(fill="both", expand=True, padx=40, pady=(5, 25))

        all_patients = self.patients_repo.get_all_patients()

        def on_search_key(event=None):
            query = e_search.get().strip().lower()
            for w in results_scroll.winfo_children():
                w.destroy()

            if not query:
                ctk.CTkLabel(
                    results_scroll, 
                    text="اكتب جزءاً من اسم المريض أو رقمه للبدء في البحث...", 
                    font=get_font(size=12),
                    text_color=THEME["text_muted"]
                ).pack(pady=35)
                return

            matched = [p for p in all_patients if query in str(p[1]).lower() or (len(p) > 2 and query in str(p[2] or ""))] if all_patients else []

            if matched:
                for p in matched:
                    p_id, p_name, p_phone = p[0], p[1], p[2] if len(p) > 2 else "بدون هاتف"
                    card_btn = ctk.CTkButton(
                        results_scroll, 
                        text=f"👤  {p_name}    |    📞 {p_phone}    |    الملف #{p_id}",
                        fg_color=THEME["bg_app"],
                        hover_color=THEME["primary"],
                        anchor="e",
                        height=42,
                        corner_radius=8,
                        font=get_font(size=13, weight="bold"),
                        text_color=THEME["text_primary"],
                        command=lambda patient_obj=p: self.open_patient_dashboard(patient_obj)
                    )
                    card_btn.pack(fill="x", pady=4, padx=6)
            else:
                ctk.CTkLabel(
                    results_scroll, 
                    text="عذراً، لم يتم العثور على أي مريض مسجل بهذه البيانات.", 
                    font=get_font(size=12),
                    text_color=THEME["danger"]
                ).pack(pady=35)

        e_search.bind("<KeyRelease>", on_search_key)
        on_search_key()

    def open_patient_dashboard(self, patient):
        self.selected_patient = patient
        self.editing_treatment_id = None
        self._clear_content()
        container = self.content_area

        p_id, p_name = patient[0], patient[1]
        p_phone = patient[2] if len(patient) > 2 else "غير محدد"
        p_address = patient[3] if len(patient) > 3 else "غير محدد"
        med_hist = patient[6] if len(patient) > 6 else (patient[5] if len(patient) > 5 else "لا يوجد")

        conn = self.patients_repo.db.get_connection()
        total_debt = 0.0
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(remaining_amount) FROM patient_accounts WHERE patient_id = %s", (p_id,))
                res = cursor.fetchone()
                if res:
                    total_debt = float(res[0] or 0)
                cursor.close()
                conn.close()
            except Exception:
                pass

        top_profile_card = ctk.CTkFrame(
            container, 
            fg_color=THEME["bg_card"], 
            corner_radius=14, 
            border_width=1, 
            border_color=THEME["border_light"]
        )
        top_profile_card.pack(fill="x", pady=(2, 8))

        top_inner = ctk.CTkFrame(top_profile_card, fg_color="transparent")
        top_inner.pack(fill="x", padx=16, pady=12)

        p_info_frame = ctk.CTkFrame(top_inner, fg_color="transparent")
        p_info_frame.pack(side="right")

        title_line = ctk.CTkLabel(
            p_info_frame, 
            text=f"👤 ملف المريض: {p_name} (#{p_id})", 
            font=get_font(size=17, weight="bold"),
            text_color=THEME["text_primary"]
        )
        title_line.pack(anchor="e")

        sub_info = f"📞 الهاتف: {p_phone}  |  📍 العنوان: {p_address}  |  🩺 التاريخ الطبي: {med_hist}"
        sub_line = ctk.CTkLabel(
            p_info_frame, 
            text=sub_info, 
            font=get_font(size=13),
            text_color=THEME["text_secondary"]
        )
        sub_line.pack(anchor="e")

        actions_side = ctk.CTkFrame(top_inner, fg_color="transparent")
        actions_side.pack(side="left")

        back_btn = ctk.CTkButton(
            actions_side, 
            text="🔙 تغيير المريض", 
            fg_color=THEME["bg_card_secondary"],
            hover_color=THEME["bg_card_hover"],
            border_width=1,
            border_color=THEME["border_light"],
            command=self.show_search_screen, 
            width=140, 
            height=38, 
            font=get_font(size=13, weight="bold")
        )
        back_btn.pack(side="left", padx=8)

        debt_color = THEME["danger"] if total_debt > 0 else THEME["success"]
        debt_text = f"⚠️ إجمالي الديون المتبقية: {total_debt:,.2f} ر.ي" if total_debt > 0 else "● الحساب خالص (لا يوجد دين)"
        debt_badge = ctk.CTkLabel(
            actions_side,
            text=debt_text,
            font=get_font(size=14, weight="bold"),
            text_color=debt_color,
            fg_color=THEME["bg_app"],
            corner_radius=8,
            padx=14,
            pady=6
        )
        debt_badge.pack(side="left")

        tabview = ctk.CTkTabview(
            container, 
            fg_color=THEME["bg_card"],
            corner_radius=14,
            segmented_button_selected_color=THEME["primary"],
            segmented_button_selected_hover_color=THEME["primary_hover"],
            segmented_button_unselected_color=THEME["bg_card_secondary"],
            segmented_button_unselected_hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_light"]
        )
        tabview.pack(fill="both", expand=True)

        tab_payment = tabview.add("💰 كشف الحساب وسداد الديون")
        tab_treatment = tabview.add("🦷 تسجيل جلسة علاجية جديدة")

        tabview.set("🦷 تسجيل جلسة علاجية جديدة")

        # =====================================================================
        # تبويب تسجيل جلسة علاجية (RTL)
        # =====================================================================
        form_t = ctk.CTkFrame(tab_treatment, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        form_t.pack(fill="x", padx=12, pady=(10, 8))

        form_title_label = ctk.CTkLabel(
            form_t,
            text="➕ تسجيل تفاصيل الجلسة العلاجية وترحيل الفاتورة",
            font=get_font(size=15, weight="bold"),
            text_color=THEME["primary"]
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

        today_str = datetime.date.today().strftime("%Y-%m-%d")
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

        def open_visit_calendar():
            CalendarDialog(self, lambda d_str: (e_next_visit.delete(0, 'end'), e_next_visit.insert(0, d_str)))

        cal_btn_v = ctk.CTkButton(
            next_date_row, text="📅 التقويم", width=85, height=38,
            font=get_font(size=11, weight="bold"),
            fg_color=THEME["bg_card_secondary"], hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"], command=open_visit_calendar
        )
        cal_btn_v.pack(side="left")

        row2_t = ctk.CTkFrame(form_t, fg_color="transparent")
        row2_t.pack(fill="x", padx=14, pady=(6, 12))

        save_t_btn = ctk.CTkButton(
            row2_t, 
            text="💾 حفظ الجلسة وترحيل الفاتورة", 
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            width=220, 
            height=42, 
            font=get_font(size=13, weight="bold")
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
            text_color=THEME["text_primary"]
        )

        e_desc = ctk.CTkEntry(row2_t, placeholder_text="وصف الإجراء الطبي، رقم السن، أو تفاصيل المعالجة والوصفة...", height=42, font=get_font(size=14), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_desc)
        e_desc.pack(side="right", fill="x", expand=True)

        def cancel_editing_mode():
            self.editing_treatment_id = None
            form_title_label.configure(text="➕ تسجيل تفاصيل الجلسة العلاجية وترحيل الفاتورة", text_color=THEME["primary"])
            save_t_btn.configure(text="💾 حفظ الجلسة وترحيل الفاتورة", fg_color=THEME["primary"])
            cancel_edit_btn.pack_forget()
            e_type.delete(0, 'end')
            e_cost.delete(0, 'end')
            e_paid.delete(0, 'end')
            e_date.delete(0, 'end')
            e_date.insert(0, today_str)
            e_desc.delete(0, 'end')
            e_next_visit.delete(0, 'end')

        cancel_edit_btn.configure(command=cancel_editing_mode)

        def save_treatment_action():
            try:
                cost = float(e_cost.get().strip() or 0)
                paid = float(e_paid.get().strip() or 0)
            except ValueError:
                return
            if cost <= 0:
                return

            if self.editing_treatment_id:
                conn = self.treatments_repo.db.get_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE treatments SET treatment_type = %s, cost = %s, description = %s, treatment_date = %s WHERE treatment_id = %s;",
                            (e_type.get().strip(), cost, e_desc.get().strip(), e_date.get().strip() or today_str, self.editing_treatment_id)
                        )
                        remain = max(0.0, cost - paid)
                        status = "Paid" if remain <= 0 else ("Partial" if paid > 0 else "Unpaid")
                        cursor.execute(
                            "UPDATE patient_accounts SET total_amount = %s, paid_amount = %s, remaining_amount = %s, payment_status = %s WHERE treatment_id = %s;",
                            (cost, paid, remain, status, self.editing_treatment_id)
                        )
                        conn.commit()
                        cursor.close()
                        conn.close()
                        self.open_patient_dashboard(patient)
                    except Exception as ex:
                        print(f"Error updating treatment: {ex}")
            else:
                t_id, msg_t = self.treatments_repo.add_treatment(
                    patient_id=p_id, emp_id=1, treatment_type=e_type.get().strip(),
                    description=e_desc.get().strip(), cost=cost, treatment_date=e_date.get().strip() or today_str, notes=""
                )
                if not t_id:
                    return

                remain = max(0.0, cost - paid)
                self.accounts_repo.add_invoice_from_treatment(
                    patient_id=p_id, treatment_id=t_id, total_amount=cost,
                    paid_amount=paid, payment_status="Paid" if remain <= 0 else ("Partial" if paid > 0 else "Unpaid"), 
                    payment_method="نقداً", payment_date=e_date.get().strip()
                )

                next_date_val = e_next_visit.get().strip()
                if next_date_val:
                    self.appointments_repo.add_appointment(
                        patient_id=p_id,
                        appointment_date=next_date_val,
                        appointment_time="10:00:00",
                        notes=f"موعد عودة للمريض: {p_name} - جلسة: {e_type.get().strip()}"
                    )

                self.open_patient_dashboard(patient)

        save_t_btn.configure(command=save_treatment_action)

        scroll_treatments = ctk.CTkScrollableFrame(tab_treatment, fg_color="transparent")
        scroll_treatments.pack(fill="both", expand=True, padx=10, pady=6)

        def load_treatment_into_form(tr):
            t_id, emp, t_type, desc, t_cost, t_date, t_notes = tr
            self.editing_treatment_id = t_id
            
            form_title_label.configure(text=f"✏️ تعديل تفاصيل الجلسة العلاجية (#{t_id})", text_color=THEME["warning"])
            save_t_btn.configure(text="💾 حفظ التعديلات", fg_color=THEME["warning"])
            cancel_edit_btn.pack(side="left", padx=(0, 10))

            e_type.delete(0, 'end')
            e_type.insert(0, t_type or "")

            e_cost.delete(0, 'end')
            e_cost.insert(0, str(t_cost or 0))

            e_date.delete(0, 'end')
            e_date.insert(0, str(t_date or today_str))

            e_desc.delete(0, 'end')
            e_desc.insert(0, desc or "")
            e_type.focus()

        treatments_list = self.treatments_repo.get_treatments_by_patient(p_id)
        if treatments_list:
            total_sessions = len(treatments_list)
            for idx, t in enumerate(reversed(treatments_list)):
                t_id, emp, t_type, desc, t_cost, t_date, t_notes = t
                session_num = total_sessions - idx
                
                linked_appt_date = None
                conn_a = self.appointments_repo.db.get_connection()
                if conn_a:
                    try:
                        cur_a = conn_a.cursor()
                        cur_a.execute("SELECT appointment_date, notes FROM appointments WHERE patient_id = %s AND appointment_date >= %s ORDER BY appointment_date ASC LIMIT 1;", (p_id, t_date))
                        res_appt = cur_a.fetchone()
                        if res_appt:
                            linked_appt_date = f"📅 موعد القادم المرتبط: {res_appt[0]} ({res_appt[1] or ''})"
                        cur_a.close()
                        conn_a.close()
                    except Exception:
                        pass

                card = ctk.CTkFrame(scroll_treatments, fg_color=THEME["bg_card_secondary"], corner_radius=10, border_width=1, border_color=THEME["border"])
                card.pack(fill="x", pady=4)
                
                txt_head = f"🦷 جلسة علاجية #{session_num}  |  النوع: {t_type or 'عام'}  |  التكلفة: {t_cost:,.2f} ر.ي  |  التاريخ: {t_date}"
                desc_txt = f"📝 الملاحظات والإجراء: {desc or 'لا يوجد وصف مدون'}"
                
                ctk.CTkLabel(card, text=txt_head, font=get_font(size=14, weight="bold"), text_color=THEME["text_primary"]).pack(anchor="e", padx=14, pady=(8, 2))
                ctk.CTkLabel(card, text=desc_txt, font=get_font(size=13), text_color=THEME["text_secondary"]).pack(anchor="e", padx=14, pady=(0, 2))

                if linked_appt_date:
                    ctk.CTkLabel(card, text=linked_appt_date, font=get_font(size=12, weight="bold"), text_color=THEME["warning"]).pack(anchor="e", padx=14, pady=(0, 2))

                actions_row = ctk.CTkFrame(card, fg_color="transparent")
                actions_row.pack(fill="x", padx=14, pady=(4, 8))

                ctk.CTkButton(
                    actions_row, text="✏️ تعديل الجلسة", width=110, height=32,
                    font=get_font(size=12, weight="bold"), fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                    command=lambda tr=t: load_treatment_into_form(tr)
                ).pack(side="left", padx=2)

                if self.user_role == "admin":
                    ctk.CTkButton(
                        actions_row, text="🗑️ حذف الجلسة", width=100, height=32,
                        font=get_font(size=12, weight="bold"), fg_color=THEME["danger_soft"], hover_color=THEME["danger"],
                        command=lambda tid=t_id: self.delete_treatment_action(tid, patient)
                    ).pack(side="left", padx=2)
        else:
            ctk.CTkLabel(scroll_treatments, text="لا توجد جلسات طبية مسجلة لهذا المريض حتى الآن.", font=get_font(size=14, weight="bold"), text_color=THEME["text_muted"]).pack(pady=25)

        # =====================================================================
        # تبويب كشف الحساب وسداد الديون (RTL) - مع تصحيح الرصيد التراكمي
        # =====================================================================
        form_p = ctk.CTkFrame(tab_payment, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        form_p.pack(fill="x", padx=12, pady=(10, 8))

        ctk.CTkLabel(
            form_p,
            text="💵 سداد دفعة نقدية لتخفيض الذمة والمديونية",
            font=get_font(size=15, weight="bold"),
            text_color=THEME["success"]
        ).pack(anchor="e", padx=16, pady=(12, 6))

        row1_p = ctk.CTkFrame(form_p, fg_color="transparent")
        row1_p.pack(fill="x", padx=14, pady=6)

        ctk.CTkLabel(row1_p, text="المبلغ المراد سداده (ر.ي):", font=get_font(size=13, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        e_pay_val = ctk.CTkEntry(row1_p, placeholder_text="0.00", width=180, height=40, font=get_font(size=14), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_pay_val)
        e_pay_val.pack(side="right", padx=(0, 16))

        payment_methods = ["نقداً", "تحويل بنكي", "شبكة"]
        ctk.CTkLabel(row1_p, text="طريقة السداد:", font=get_font(size=13, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        cb_pay_method = ctk.CTkComboBox(row1_p, values=payment_methods, width=140, height=40, font=get_font(size=13), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        cb_pay_method.pack(side="right", padx=(0, 4))
        cb_pay_method.set("نقداً")

        row2_p = ctk.CTkFrame(form_p, fg_color="transparent")
        row2_p.pack(fill="x", padx=14, pady=(6, 12))

        save_p_btn = ctk.CTkButton(
            row2_p, 
            text="💵 تأكيد سداد الدين", 
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            width=180, 
            height=42, 
            font=get_font(size=13, weight="bold")
        )
        save_p_btn.pack(side="left", padx=(0, 10))

        e_pay_notes = ctk.CTkEntry(row2_p, placeholder_text="ملاحظات السند المالي وسداد الذمة...", height=42, font=get_font(size=14), justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_pay_notes)
        e_pay_notes.pack(side="right", fill="x", expand=True)

        def save_payment_action():
            try:
                pay_val = float(e_pay_val.get().strip() or 0)
            except ValueError:
                return
            if pay_val <= 0:
                return

            conn = self.patients_repo.db.get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    query = """
                        INSERT INTO patient_accounts 
                        (patient_id, treatment_id, total_amount, paid_amount, remaining_amount, payment_date, payment_status, payment_method)
                        VALUES (%s, NULL, 0, %s, %s, %s, 'Paid', %s);
                    """
                    cursor.execute(query, (p_id, pay_val, -pay_val, today_str, cb_pay_method.get()))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    self.open_patient_dashboard(patient)
                except Exception as ex:
                    print(f"Error: {ex}")

        save_p_btn.configure(command=save_payment_action)

        export_toolbar = ctk.CTkFrame(tab_payment, fg_color="transparent")
        export_toolbar.pack(fill="x", padx=12, pady=(4, 6))

        def quick_export_patient_pdf():
            from tkinter import filedialog
            from backend.statements_repo import StatementsRepository
            repo = StatementsRepository()
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            fpath = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Document", "*.pdf")],
                initialfile=f"Patient_Statement_{p_id}_{today_str}.pdf"
            )
            if fpath:
                ok, msg = repo.export_patient_statement_pdf(p_id, fpath)
                p_export_status.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

        def quick_export_patient_excel():
            from tkinter import filedialog
            from backend.statements_repo import StatementsRepository
            repo = StatementsRepository()
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            fpath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Spreadsheet", "*.xlsx")],
                initialfile=f"Patient_Statement_{p_id}_{today_str}.xlsx"
            )
            if fpath:
                ok, msg = repo.export_patient_statement_excel(p_id, fpath)
                p_export_status.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

        ctk.CTkButton(
            export_toolbar, text="📄 استخراج كشف حساب المريض PDF",
            width=230, height=38, font=get_font(size=13, weight="bold"),
            fg_color=THEME["danger"], hover_color=THEME["danger_hover"],
            command=quick_export_patient_pdf
        ).pack(side="right", padx=(0, 8))

        ctk.CTkButton(
            export_toolbar, text="📊 تصدير كشف الحساب Excel",
            width=210, height=38, font=get_font(size=13, weight="bold"),
            fg_color=THEME["success"], hover_color=THEME["success_hover"],
            command=quick_export_patient_excel
        ).pack(side="right", padx=(0, 8))

        p_export_status = ctk.CTkLabel(export_toolbar, text="", font=get_font(size=13, weight="bold"))
        p_export_status.pack(side="left", padx=10)

        scroll_accounts = ctk.CTkScrollableFrame(tab_payment, fg_color="transparent")
        scroll_accounts.pack(fill="both", expand=True, padx=10, pady=6)

        conn = self.patients_repo.db.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = """
                    SELECT a.invoice_id, a.treatment_id, t.treatment_type, a.total_amount, a.paid_amount, 
                           a.payment_date, a.payment_status, a.payment_method
                    FROM patient_accounts a
                    LEFT JOIN treatments t ON a.treatment_id = t.treatment_id
                    WHERE a.patient_id = %s
                    ORDER BY a.invoice_id ASC;
                """
                cursor.execute(query, (p_id,))
                rows = cursor.fetchall()
                cursor.close()
                conn.close()

                if rows:
                    treatments_map = {}
                    t_list = self.treatments_repo.get_treatments_by_patient(p_id)
                    for index, tr in enumerate(t_list):
                        treatments_map[tr[0]] = index + 1

                    # حساب الرصيد التراكمي تسلسلياً (من الأقدم للأحدث لتجميع الحسابات بدقة)
                    running_remain = 0.0
                    processed_items = []
                    for r in rows:
                        inv_id, t_id, t_type, total, paid, p_date, status, method = r
                        total_val = float(total or 0)
                        paid_val = float(paid or 0)

                        if t_id:
                            row_net = total_val - paid_val
                        else:
                            row_net = -paid_val

                        running_remain += row_net
                        remain_val = max(0.0, running_remain) if running_remain > 0 else running_remain

                        processed_items.append((inv_id, t_id, t_type, total_val, paid_val, remain_val, p_date, status, method))

                    # عرض السطور بطريقة تنازلية (الأحدث في الأعلى) مع الاحتفاظ بالرصيد التراكمي الصحيح
                    for item in reversed(processed_items):
                        inv_id, t_id, t_type, total_val, paid_val, remain_val, p_date, status, method = item

                        card = ctk.CTkFrame(scroll_accounts, fg_color=THEME["bg_card_secondary"], corner_radius=10, border_width=1, border_color=THEME["border"])
                        card.pack(fill="x", pady=4)

                        top_acc = ctk.CTkFrame(card, fg_color="transparent")
                        top_acc.pack(fill="x", padx=14, pady=(8, 2))

                        if t_id and t_id in treatments_map:
                            sess_num = treatments_map[t_id]
                            title_txt = f"🧾 فاتورة جلسة #{sess_num} ({t_type or 'علاج'}) | التاريخ: {p_date}"
                        elif t_id:
                            title_txt = f"🧾 فاتورة علاجية #{t_id} | التاريخ: {p_date}"
                        else:
                            title_txt = f"💵 سند قبض وسداد مباشر | التاريخ: {p_date}"

                        ctk.CTkLabel(top_acc, text=title_txt, font=get_font(size=14, weight="bold"), text_color=THEME["text_primary"]).pack(side="right")

                        stat_acc = ctk.CTkFrame(card, fg_color="transparent")
                        stat_acc.pack(fill="x", padx=14, pady=(0, 2))

                        fin_txt = f"التكلفة: {total_val:,.2f} ر.ي   |   المدفوع: {paid_val:,.2f} ر.ي   |   المتبقي: {remain_val:,.2f} ر.ي   |   الطريقة: {method or 'نقداً'}"
                        remain_color = THEME["success"] if remain_val <= 0 else THEME["danger"]

                        ctk.CTkLabel(stat_acc, text=fin_txt, font=get_font(size=13, weight="bold"), text_color=remain_color).pack(anchor="e")

                        acc_actions = ctk.CTkFrame(card, fg_color="transparent")
                        acc_actions.pack(fill="x", padx=14, pady=(4, 8))

                        ctk.CTkButton(
                            acc_actions, text="✏️ تعديل الحركة", width=110, height=32,
                            font=get_font(size=12, weight="bold"), fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                            command=lambda acc_item=(inv_id, t_id, total_val, paid_val, p_date, method): self.edit_account_row(acc_item, patient)
                        ).pack(side="left", padx=2)

                        if self.user_role == "admin":
                            ctk.CTkButton(
                                acc_actions, text="🗑️ حذف الحركة", width=100, height=32,
                                font=get_font(size=12, weight="bold"), fg_color=THEME["danger_soft"], hover_color=THEME["danger"],
                                command=lambda iid=inv_id: self.delete_account_action(iid, patient)
                            ).pack(side="left", padx=2)
                else:
                    ctk.CTkLabel(scroll_accounts, text="لا توجد حركات مالية مسجلة لهذا المريض.", font=get_font(size=14, weight="bold"), text_color=THEME["text_muted"]).pack(pady=25)
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
        inv_id, t_id, total_val, paid_val, p_date, method = acc_obj
        
        top = ctk.CTkToplevel(self)
        top.title(f"تعديل الحركة المالية #{inv_id}")
        top.geometry("380x280")
        top.resizable(False, False)
        top.grab_set()

        ctk.CTkLabel(top, text=f"✏️ تعديل الحركة المالية (#{inv_id})", font=get_font(size=14, weight="bold"), text_color=THEME["warning"]).pack(pady=15)

        form = ctk.CTkFrame(top, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20)

        ctk.CTkLabel(form, text="المبلغ المدفوع (ر.ي):", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e")
        e_paid = ctk.CTkEntry(form, width=340, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        e_paid.pack(anchor="e", pady=(0, 8))
        e_paid.insert(0, str(paid_val))

        ctk.CTkLabel(form, text="طريقة السداد:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e")
        cb_method = ctk.CTkComboBox(form, values=["نقداً", "تحويل بنكي", "شبكة"], width=340, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        cb_method.pack(anchor="e", pady=(0, 15))
        cb_method.set(method or "نقداً")

        def save_acc_edits():
            try:
                new_paid = float(e_paid.get().strip() or 0)
            except ValueError:
                return

            conn = self.accounts_repo.db.get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    new_remain = max(0.0, float(total_val) - new_paid)
                    status = "Paid" if new_remain <= 0 else ("Partial" if new_paid > 0 else "Unpaid")

                    cursor.execute(
                        "UPDATE patient_accounts SET paid_amount = %s, remaining_amount = %s, payment_status = %s, payment_method = %s WHERE invoice_id = %s;",
                        (new_paid, new_remain, status, cb_method.get(), inv_id)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    top.destroy()
                    self.open_patient_dashboard(patient)
                except Exception as ex:
                    print(f"Error updating account: {ex}")

        ctk.CTkButton(
            top, text="💾 حفظ التعديلات", width=150, height=34,
            fg_color=THEME["warning"], hover_color="darkorange",
            font=get_font(size=12, weight="bold"), command=save_acc_edits
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
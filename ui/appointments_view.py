import datetime
import calendar
import customtkinter as ctk
from tkinter import messagebox

from backend.appointments_repo import AppointmentsRepository
from ui.theme import THEME, get_font, setup_rtl_entry


def get_arabic_day_name(date_str):
    """إرجاع اسم اليوم بالعربية بناءً على تاريخ بصيغة YYYY-MM-DD"""
    try:
        if isinstance(date_str, datetime.date):
            dt = date_str
        else:
            dt = datetime.datetime.strptime(str(date_str), "%Y-%m-%d").date()

        days_map = {
            0: "الإثنين",
            1: "الثلاثاء",
            2: "الأربعاء",
            3: "الخميس",
            4: "الجمعة",
            5: "السبت",
            6: "الأحد",
        }
        return days_map.get(dt.weekday(), "")
    except Exception:
        return ""


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

        prev_btn = ctk.CTkButton(
            nav_frame,
            text="◀",
            width=40,
            height=32,
            fg_color=THEME["bg_card_secondary"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            command=self.prev_month,
        )
        prev_btn.pack(side="right")

        self.month_label = ctk.CTkLabel(
            nav_frame,
            text="",
            font=get_font(size=14, weight="bold"),
            text_color=THEME["primary"],
        )
        self.month_label.pack(side="right", expand=True)

        next_btn = ctk.CTkButton(
            nav_frame,
            text="▶",
            width=40,
            height=32,
            fg_color=THEME["bg_card_secondary"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            command=self.next_month,
        )
        next_btn.pack(side="right")

        self.days_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.days_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.render_calendar()

    def render_calendar(self):
        for w in self.days_frame.winfo_children():
            w.destroy()

        months_ar = [
            "يناير",
            "فبراير",
            "مارس",
            "أبريل",
            "مايو",
            "يونيو",
            "يوليو",
            "أغسطس",
            "سبتمبر",
            "أكتوبر",
            "نوفمبر",
            "ديسمبر",
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
                        fg_color=THEME["primary"] if is_today else THEME["bg_card_secondary"],
                        hover_color=THEME["primary_hover"] if is_today else THEME["bg_card_hover"],
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


class AppointmentsView(ctk.CTkFrame):
    def __init__(self, parent, user_role="admin"):
        super().__init__(parent, fg_color="transparent")
        self.user_role = str(user_role).lower()
        self.appointments_repo = AppointmentsRepository()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # عنوان الصفحة
        header_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border"],
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))

        today_date_str = datetime.date.today().strftime("%Y-%m-%d")
        today_day_ar = get_arabic_day_name(today_date_str)
        ctk.CTkLabel(
            header_frame,
            text=f"تاريخ اليوم: {today_date_str} ({today_day_ar})",
            font=get_font(size=13, weight="bold"),
            text_color=THEME["text_secondary"],
        ).pack(side="left", padx=20, pady=15)

        ctk.CTkLabel(
            header_frame,
            text="📅 إدارة المواعيد وجدول المراجعات الشاملة",
            font=get_font(size=17, weight="bold"),
            text_color=THEME["primary"],
            anchor="e",
            justify="right",
        ).pack(side="right", fill="x", expand=True, padx=20, pady=15)

        # المحتوى مقسّم إلى 3 أعمدة متناسقة
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        body_frame.grid_columnconfigure(0, weight=1)
        body_frame.grid_columnconfigure(1, weight=1)
        body_frame.grid_columnconfigure(2, weight=1)
        body_frame.grid_rowconfigure(0, weight=1)

        # =====================================================================
        # القسم الأول: إضافة موعد جديد
        # =====================================================================
        add_card = ctk.CTkFrame(
            body_frame,
            fg_color=THEME["bg_card"],
            corner_radius=14,
            border_width=1,
            border_color=THEME["border"],
        )
        add_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            add_card,
            text="➕ إضافة موعد أو ملاحظة عامة",
            font=get_font(size=15, weight="bold"),
            text_color=THEME["success"],
        ).pack(anchor="e", padx=16, pady=(16, 10))

        form_inner = ctk.CTkFrame(add_card, fg_color="transparent")
        form_inner.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(
            form_inner,
            text="تاريخ الموعد:",
            font=get_font(size=13, weight="bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="e", pady=(0, 4))

        date_row = ctk.CTkFrame(form_inner, fg_color="transparent")
        date_row.pack(fill="x", pady=(0, 14))

        self.e_date = ctk.CTkEntry(
            date_row,
            height=40,
            justify="right",
            font=get_font(size=13),
            fg_color=THEME["bg_app"],
            border_color=THEME["border"],
        )
        setup_rtl_entry(self.e_date)
        self.e_date.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self.e_date.insert(0, today_date_str)

        def open_calendar():
            CalendarDialog(self, lambda d_str: (self.e_date.delete(0, "end"), self.e_date.insert(0, d_str)))

        cal_btn = ctk.CTkButton(
            date_row,
            text="📅 التقويم",
            width=90,
            height=40,
            font=get_font(size=12, weight="bold"),
            fg_color=THEME["bg_card_secondary"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            command=open_calendar,
        )
        cal_btn.pack(side="left")

        ctk.CTkLabel(
            form_inner,
            text="سبب الموعد أو الملاحظة:",
            font=get_font(size=13, weight="bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="e", pady=(0, 4))
        self.e_reason = ctk.CTkEntry(
            form_inner,
            placeholder_text="اكتب سبب الموعد أو الغرض منه...",
            height=42,
            justify="right",
            font=get_font(size=13),
            fg_color=THEME["bg_app"],
            border_color=THEME["border"],
        )
        setup_rtl_entry(self.e_reason)
        self.e_reason.pack(fill="x", pady=(0, 20))

        def save_general_appointment():
            date_val = self.e_date.get().strip()
            reason_val = self.e_reason.get().strip()
            if not date_val or not reason_val:
                messagebox.showerror("خطأ", "يرجى إدخال تاريخ الموعد والسبب على الأقل.")
                return

            conn = self.appointments_repo.db.get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    query = """
                        INSERT INTO appointments (patient_id, appointment_date, appointment_time, status, notes)
                        VALUES (NULL, %s, '10:00:00', 'معلق', %s);
                    """
                    cursor.execute(query, (date_val, reason_val))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    messagebox.showinfo("نجاح", "تم إضافة الموعد بنجاح.")
                    self.e_reason.delete(0, "end")
                    self.load_todays_appointments()
                    self.load_all_upcoming_appointments()
                except Exception as ex:
                    messagebox.showerror("خطأ", f"فشل حفظ الموعد: {ex}")

        ctk.CTkButton(
            add_card,
            text="💾 حفظ الموعد",
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            text_color=THEME["text_light"],
            height=42,
            font=get_font(size=13, weight="bold"),
            command=save_general_appointment,
        ).pack(fill="x", padx=16, pady=10)

        # =====================================================================
        # القسم الثاني: مواعيد اليوم الحالي
        # =====================================================================
        today_card = ctk.CTkFrame(
            body_frame,
            fg_color=THEME["bg_card"],
            corner_radius=14,
            border_width=1,
            border_color=THEME["border"],
        )
        today_card.grid(row=0, column=1, sticky="nsew", padx=4)
        today_card.grid_columnconfigure(0, weight=1)
        today_card.grid_rowconfigure(1, weight=1)

        t_top_row = ctk.CTkFrame(today_card, fg_color="transparent")
        t_top_row.grid(row=0, column=0, sticky="ew", padx=14, pady=(15, 10))

        ctk.CTkLabel(
            t_top_row,
            text="📋 مواعيد اليوم",
            font=get_font(size=15, weight="bold"),
            text_color=THEME["primary"],
        ).pack(side="right")

        ctk.CTkButton(
            t_top_row,
            text="🔄",
            width=36,
            height=32,
            font=get_font(size=12, weight="bold"),
            fg_color=THEME["bg_card_secondary"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            command=lambda: self.load_todays_appointments(),
        ).pack(side="left")

        self.today_scroll = ctk.CTkScrollableFrame(today_card, fg_color=THEME["bg_card_secondary"], corner_radius=10)
        self.today_scroll.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 15))

        # =====================================================================
        # القسم الثالث: جميع المواعيد القادمة (مع فلترة التاريخ وزر التعديل)
        # =====================================================================
        all_card = ctk.CTkFrame(
            body_frame,
            fg_color=THEME["bg_card"],
            corner_radius=14,
            border_width=1,
            border_color=THEME["border"],
        )
        all_card.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        all_card.grid_columnconfigure(0, weight=1)
        all_card.grid_rowconfigure(2, weight=1)

        a_top_row = ctk.CTkFrame(all_card, fg_color="transparent")
        a_top_row.grid(row=0, column=0, sticky="ew", padx=14, pady=(15, 5))

        ctk.CTkLabel(
            a_top_row,
            text="🗓️ جميع المواعيد القادمة",
            font=get_font(size=14, weight="bold"),
            text_color=THEME["warning"],
        ).pack(side="right")

        ctk.CTkButton(
            a_top_row,
            text="🔄",
            width=36,
            height=32,
            font=get_font(size=12, weight="bold"),
            fg_color=THEME["bg_card_secondary"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            command=lambda: self.load_all_upcoming_appointments(),
        ).pack(side="left")

        filter_row = ctk.CTkFrame(all_card, fg_color="transparent")
        filter_row.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))

        self.e_filter_date = ctk.CTkEntry(
            filter_row,
            placeholder_text="اختر أو اكتب تاريخ (YYYY-MM-DD)...",
            height=34,
            justify="right",
            font=get_font(size=11),
            fg_color=THEME["bg_app"],
            border_color=THEME["border"],
        )
        setup_rtl_entry(self.e_filter_date)
        self.e_filter_date.pack(side="right", fill="x", expand=True, padx=(4, 0))

        def open_filter_calendar():
            CalendarDialog(
                self,
                lambda d_str: (
                    self.e_filter_date.delete(0, "end"),
                    self.e_filter_date.insert(0, d_str),
                    self.load_all_upcoming_appointments(),
                ),
            )

        ctk.CTkButton(
            filter_row,
            text="📅",
            width=36,
            height=34,
            font=get_font(size=11, weight="bold"),
            fg_color=THEME["bg_card_secondary"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            command=open_filter_calendar,
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            filter_row,
            text="بحث",
            width=50,
            height=34,
            font=get_font(size=11, weight="bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_light"],
            command=lambda: self.load_all_upcoming_appointments(),
        ).pack(side="left", padx=(4, 0))

        ctk.CTkButton(
            filter_row,
            text="إلغاء الفلتر",
            width=70,
            height=34,
            font=get_font(size=11, weight="bold"),
            fg_color=THEME["bg_card_secondary"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            command=lambda: (self.e_filter_date.delete(0, "end"), self.load_all_upcoming_appointments()),
        ).pack(side="left")

        self.all_scroll = ctk.CTkScrollableFrame(all_card, fg_color=THEME["bg_card_secondary"], corner_radius=10)
        self.all_scroll.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 15))

        self.load_todays_appointments()
        self.load_all_upcoming_appointments()

    def load_todays_appointments(self):
        for w in self.today_scroll.winfo_children():
            w.destroy()

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        day_name_ar = get_arabic_day_name(today_str)
        appointments = self.appointments_repo.get_todays_appointments(today_str)

        if appointments:
            for appt in appointments:
                appt_id, p_id, p_name, p_phone, a_date, a_time, status, notes = appt

                card = ctk.CTkFrame(
                    self.today_scroll,
                    fg_color=THEME["bg_card"],
                    corner_radius=10,
                    border_width=1,
                    border_color=THEME["border"],
                )
                card.pack(fill="x", pady=6, padx=4)

                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.pack(fill="x", padx=10, pady=8)

                ctk.CTkLabel(
                    info_frame,
                    text=f"📅 التاريخ: {a_date} ({day_name_ar})",
                    font=get_font(size=11, weight="bold"),
                    text_color=THEME["teal"],
                ).pack(anchor="e", pady=(0, 2))

                if p_name:
                    patient_display = f"👤 المريض: {p_name}"
                    if p_phone:
                        patient_display += f"  |  📞 {p_phone}"
                    ctk.CTkLabel(
                        info_frame,
                        text=patient_display,
                        font=get_font(size=13, weight="bold"),
                        text_color=THEME["text_primary"],
                    ).pack(anchor="e", pady=(0, 2))
                    details_txt = f"⏰ {a_time} | 📝 السبب: {notes or 'بدون ملاحظات'}"
                    ctk.CTkLabel(
                        info_frame,
                        text=details_txt,
                        font=get_font(size=11),
                        text_color=THEME["text_secondary"],
                    ).pack(anchor="e")
                else:
                    general_txt = f"📝 السبب: {notes or 'بدون تفاصيل'}"
                    ctk.CTkLabel(
                        info_frame,
                        text=general_txt,
                        font=get_font(size=13, weight="bold"),
                        text_color=THEME["text_primary"],
                    ).pack(anchor="e", pady=(0, 2))
                    ctk.CTkLabel(
                        info_frame,
                        text=f"⏰ الوقت: {a_time}",
                        font=get_font(size=11),
                        text_color=THEME["text_secondary"],
                    ).pack(anchor="e")

                actions_row = ctk.CTkFrame(card, fg_color="transparent")
                actions_row.pack(fill="x", padx=10, pady=(0, 8))

                status_color = (
                    THEME["warning"]
                    if status == "معلق"
                    else (THEME["success"] if status == "متم" else THEME["danger"])
                )
                ctk.CTkLabel(
                    actions_row,
                    text=f"الحالة: {status}",
                    font=get_font(size=11, weight="bold"),
                    text_color=status_color,
                ).pack(side="right")

                def update_status(new_status, aid=appt_id):
                    ok, _ = self.appointments_repo.update_appointment_status(aid, new_status)
                    if ok:
                        self.load_todays_appointments()
                        self.load_all_upcoming_appointments()

                ctk.CTkButton(
                    actions_row,
                    text="❌ ملغي",
                    width=55,
                    height=26,
                    font=get_font(size=10),
                    fg_color=THEME["danger_soft"],
                    hover_color=THEME["danger"],
                    text_color=THEME["danger"],
                    command=lambda: update_status("ملغي"),
                ).pack(side="left", padx=1)
                ctk.CTkButton(
                    actions_row,
                    text="✅ متم",
                    width=55,
                    height=26,
                    font=get_font(size=10),
                    fg_color=THEME["success_soft"],
                    hover_color=THEME["success"],
                    text_color=THEME["success"],
                    command=lambda: update_status("متم"),
                ).pack(side="left", padx=1)
        else:
            ctk.CTkLabel(
                self.today_scroll,
                text="لا توجد مواعيد اليوم.",
                font=get_font(size=12),
                text_color=THEME["text_muted"],
            ).pack(pady=30)

    def load_all_upcoming_appointments(self):
        """جلب كافة المواعيد القادمة مع دعم فلترة تاريخ معين وزر تعديل الموعد"""
        for w in self.all_scroll.winfo_children():
            w.destroy()

        filter_date = self.e_filter_date.get().strip() if hasattr(self, "e_filter_date") else ""

        conn = self.appointments_repo.db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            if filter_date:
                query = """
                    SELECT a.appointment_id, a.patient_id, p.full_name, a.appointment_date, a.appointment_time, a.status, a.notes
                    FROM appointments a
                    LEFT JOIN patients p ON a.patient_id = p.patient_id
                    WHERE a.appointment_date = %s
                    ORDER BY a.appointment_time ASC;
                """
                cursor.execute(query, (filter_date,))
            else:
                query = """
                    SELECT a.appointment_id, a.patient_id, p.full_name, a.appointment_date, a.appointment_time, a.status, a.notes
                    FROM appointments a
                    LEFT JOIN patients p ON a.patient_id = p.patient_id
                    WHERE a.appointment_date >= CURDATE()
                    ORDER BY a.appointment_date ASC, a.appointment_time ASC;
                """
                cursor.execute(query)

            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            if rows:
                for appt in rows:
                    appt_id, p_id, p_name, a_date, a_time, status, notes = appt
                    day_name_ar = get_arabic_day_name(a_date)

                    card = ctk.CTkFrame(
                        self.all_scroll,
                        fg_color=THEME["bg_card"],
                        corner_radius=10,
                        border_width=1,
                        border_color=THEME["border"],
                    )
                    card.pack(fill="x", pady=6, padx=4)

                    info_frame = ctk.CTkFrame(card, fg_color="transparent")
                    info_frame.pack(fill="x", padx=10, pady=8)

                    title_txt = f"📅 التاريخ: {a_date} ({day_name_ar})"
                    if p_name:
                        title_txt += f" | 👤 {p_name}"
                    ctk.CTkLabel(
                        info_frame,
                        text=title_txt,
                        font=get_font(size=12, weight="bold"),
                        text_color=THEME["primary"],
                    ).pack(anchor="e", pady=(0, 2))

                    desc_txt = f"📝 السبب: {notes or 'بدون تفاصيل'} ({status})"
                    ctk.CTkLabel(
                        info_frame,
                        text=desc_txt,
                        font=get_font(size=11),
                        text_color=THEME["text_secondary"],
                    ).pack(anchor="e")

                    edit_row = ctk.CTkFrame(card, fg_color="transparent")
                    edit_row.pack(fill="x", padx=10, pady=(0, 8))

                    def open_edit_dialog(aid=appt_id, cur_date=a_date, cur_notes=notes):
                        top = ctk.CTkToplevel(self)
                        top.title("تعديل الموعد")
                        top.geometry("360x260")
                        top.resizable(False, False)
                        top.grab_set()
                        top.configure(fg_color=THEME["bg_card"])

                        ctk.CTkLabel(
                            top,
                            text="✏️ تعديل بيانات الموعد",
                            font=get_font(size=14, weight="bold"),
                            text_color=THEME["primary"],
                        ).pack(pady=15)

                        form = ctk.CTkFrame(top, fg_color="transparent")
                        form.pack(fill="x", padx=20)

                        ctk.CTkLabel(
                            form,
                            text="التاريخ (YYYY-MM-DD):",
                            font=get_font(size=11),
                            text_color=THEME["text_secondary"],
                        ).pack(anchor="e")
                        e_d = ctk.CTkEntry(
                            form,
                            width=320,
                            height=34,
                            justify="right",
                            fg_color=THEME["bg_app"],
                            border_color=THEME["border"],
                        )
                        e_d.pack(anchor="e", pady=(0, 8))
                        e_d.insert(0, str(cur_date))

                        ctk.CTkLabel(
                            form,
                            text="السبب / الملاحظة:",
                            font=get_font(size=11),
                            text_color=THEME["text_secondary"],
                        ).pack(anchor="e")
                        e_n = ctk.CTkEntry(
                            form,
                            width=320,
                            height=34,
                            justify="right",
                            fg_color=THEME["bg_app"],
                            border_color=THEME["border"],
                        )
                        e_n.pack(anchor="e", pady=(0, 15))
                        e_n.insert(0, str(cur_notes or ""))

                        def save_changes():
                            new_d = e_d.get().strip()
                            new_n = e_n.get().strip()
                            if not new_d:
                                return
                            c = self.appointments_repo.db.get_connection()
                            if c:
                                cur = c.cursor()
                                cur.execute(
                                    "UPDATE appointments SET appointment_date = %s, notes = %s WHERE appointment_id = %s",
                                    (new_d, new_n, aid),
                                )
                                c.commit()
                                cur.close()
                                c.close()
                                top.destroy()
                                self.load_todays_appointments()
                                self.load_all_upcoming_appointments()

                        ctk.CTkButton(
                            top,
                            text="💾 حفظ التعديلات",
                            width=140,
                            height=36,
                            fg_color=THEME["warning"],
                            hover_color=THEME["warning_hover"],
                            text_color=THEME["text_light"],
                            font=get_font(size=12, weight="bold"),
                            command=save_changes,
                        ).pack(pady=5)

                    ctk.CTkButton(
                        edit_row,
                        text="✏️ تعديل الموعد",
                        height=28,
                        font=get_font(size=11, weight="bold"),
                        fg_color=THEME["primary"],
                        hover_color=THEME["primary_hover"],
                        text_color=THEME["text_light"],
                        command=open_edit_dialog,
                    ).pack(fill="x")
            else:
                msg_text = (
                    f"لا توجد مواعيد مسجلة بتاريخ ({filter_date})."
                    if filter_date
                    else "لا توجد مواعيد قادمة مسجلة."
                )
                ctk.CTkLabel(
                    self.all_scroll,
                    text=msg_text,
                    font=get_font(size=12),
                    text_color=THEME["text_muted"],
                ).pack(pady=30)
        except Exception as e:
            print(f"Error loading upcoming appointments: {e}")
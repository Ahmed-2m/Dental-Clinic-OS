import datetime
from tkinter import filedialog
from tkcalendar import Calendar
import customtkinter as ctk

from backend.print_branding import load_clinic_profile
from backend.treasury_repo import DailyTreasuryRepository
from ui.theme import THEME, get_font, setup_rtl_entry


class TreasuryView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.repo = DailyTreasuryRepository()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. العنوان العلوي وشريط البحث بالتاريخ
        self._build_header_section()

        # 2. بطاقات الملخص المالي اليومي
        self._build_stats_section()

        # 3. محتوى الحركات (الوارد والصادر)
        self._build_content_section()

        # 4. شريط أزرار العمليات والإغلاق والتصدير
        self._build_action_bar()

        # تحميل بيانات اليوم الحالي افتراضياً
        self.load_treasury_data()

    def _build_header_section(self):
        header_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border_light"],
        )
        header_frame.pack(fill="x", padx=10, pady=(10, 6))

        row = ctk.CTkFrame(header_frame, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            row,
            text="💰 إدارة الخزينة والحركات المالية اليومية",
            font=get_font(size=17, weight="bold"),
            text_color=THEME["primary"],
        ).pack(side="right", padx=(0, 10))

        # أزرار وتاريخ البحث
        ctk.CTkButton(
            row,
            text="🔍 عرض حركة التاريخ",
            width=150,
            height=38,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_light"],
            font=get_font(size=13, weight="bold"),
            command=self.load_treasury_data,
        ).pack(side="left", padx=4)

        self.date_entry = ctk.CTkEntry(
            row,
            width=130,
            height=38,
            justify="center",
            font=get_font(size=13, weight="bold"),
        )
        setup_rtl_entry(self.date_entry)
        self.date_entry.pack(side="left", padx=4)
        self.date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))

        ctk.CTkButton(
            row,
            text="📅",
            width=42,
            height=38,
            fg_color=THEME["bg_app"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            border_width=1,
            border_color=THEME["border"],
            font=get_font(size=15),
            command=self.open_calendar_popup,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            row,
            text="اختر التاريخ:",
            font=get_font(size=13, weight="bold"),
            text_color=THEME["text_secondary"],
        ).pack(side="left", padx=4)

    def open_calendar_popup(self):
        top = ctk.CTkToplevel(self)
        top.title("اختيار التاريخ")
        top.geometry("340x320")
        top.attributes("-topmost", True)
        top.resizable(False, False)
        top.configure(fg_color=THEME["bg_card"])

        today = datetime.date.today()
        cal = Calendar(top, selectmode="day", year=today.year, month=today.month, day=today.day)
        cal.pack(pady=15, padx=15, fill="both", expand=True)

        def set_date():
            selected_date = cal.get_date()
            parsed_date = selected_date
            for fmt in ("%m/%d/%y", "%Y-%m-%d", "%m/%d/%Y"):
                try:
                    parsed_date = datetime.datetime.strptime(selected_date, fmt).strftime("%Y-%m-%d")
                    break
                except Exception:
                    continue

            self.date_entry.delete(0, "end")
            self.date_entry.insert(0, parsed_date)
            top.destroy()
            self.load_treasury_data()

        ctk.CTkButton(
            top,
            text="تأكيد التاريخ",
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_light"],
            height=38,
            font=get_font(size=13, weight="bold"),
            command=set_date,
        ).pack(pady=(0, 15), padx=15, fill="x")

    def _build_stats_section(self):
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=10, pady=(0, 6))

        def create_card(parent, title, val_init, color):
            card = ctk.CTkFrame(
                parent,
                fg_color=THEME["bg_card"],
                corner_radius=12,
                border_width=1,
                border_color=THEME["border"],
            )
            card.pack(side="right", fill="both", expand=True, padx=4)
            ctk.CTkLabel(
                card,
                text=title,
                font=get_font(size=13, weight="bold"),
                text_color=THEME["text_secondary"],
            ).pack(anchor="e", padx=14, pady=(8, 2))

            val_lbl = ctk.CTkLabel(
                card,
                text=val_init,
                font=get_font(size=17, weight="bold"),
                text_color=color,
            )
            val_lbl.pack(anchor="e", padx=14, pady=(0, 8))
            return val_lbl

        self.card_opening = create_card(stats_frame, "📥 رصيد الافتتاح", "0.00 ر.ي", THEME["text_primary"])
        self.card_inflow = create_card(stats_frame, "💵 إجمالي الوارد (قبض)", "0.00 ر.ي", THEME["success"])
        self.card_outflow = create_card(stats_frame, "📤 إجمالي الصادر (صرف)", "0.00 ر.ي", THEME["danger"])
        self.card_net = create_card(stats_frame, "⚖️ صافي الصندوق الختامي", "0.00 ر.ي", THEME["primary"])

    def _build_content_section(self):
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=4)
        content_frame.grid_columnconfigure((0, 1), weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # حاوية الوارد (اليمين)
        in_box = ctk.CTkFrame(
            content_frame,
            fg_color=THEME["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border_light"],
        )
        in_box.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        ctk.CTkLabel(
            in_box,
            text="📥 سجل الوارد النقدي (مقبوضات المرضى)",
            font=get_font(size=14, weight="bold"),
            text_color=THEME["success"],
        ).pack(anchor="e", padx=14, pady=10)

        self.inflow_scroll = ctk.CTkScrollableFrame(in_box, fg_color="transparent")
        self.inflow_scroll.pack(fill="both", expand=True, padx=8, pady=4)

        # حاوية الصادر (اليسار)
        out_box = ctk.CTkFrame(
            content_frame,
            fg_color=THEME["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border_light"],
        )
        out_box.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        ctk.CTkLabel(
            out_box,
            text="📤 سجل الصادر النقدي (معامل ومشتريات وموظفين)",
            font=get_font(size=14, weight="bold"),
            text_color=THEME["danger"],
        ).pack(anchor="e", padx=14, pady=10)

        self.outflow_scroll = ctk.CTkScrollableFrame(out_box, fg_color="transparent")
        self.outflow_scroll.pack(fill="both", expand=True, padx=8, pady=4)

    def _build_action_bar(self):
        action_bar = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border_light"],
        )
        action_bar.pack(fill="x", padx=10, pady=(6, 10))

        # زر الإغلاق اليومي
        ctk.CTkButton(
            action_bar,
            text="🔒 إتمام الإغلاق اليومي",
            width=180,
            height=40,
            fg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            text_color=THEME["text_light"],
            font=get_font(size=13, weight="bold"),
            command=self.perform_daily_closing,
        ).pack(side="right", padx=8, pady=8)

        # زر تصدير PDF
        ctk.CTkButton(
            action_bar,
            text="📄 تصدير PDF",
            width=140,
            height=40,
            fg_color=THEME["indigo"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_light"],
            font=get_font(size=13, weight="bold"),
            command=self.export_pdf,
        ).pack(side="right", padx=4, pady=8)

        # زر تصدير Excel
        ctk.CTkButton(
            action_bar,
            text="📊 تصدير Excel",
            width=140,
            height=40,
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            text_color=THEME["text_light"],
            font=get_font(size=13, weight="bold"),
            command=self.export_excel,
        ).pack(side="right", padx=4, pady=8)

        self.status_lbl = ctk.CTkLabel(action_bar, text="", font=get_font(size=13, weight="bold"))
        self.status_lbl.pack(side="left", padx=14)

    def export_pdf(self):
        target_date = self.date_entry.get().strip() or None
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if file_path:
            c_info = load_clinic_profile()
            ok, msg = self.repo.export_treasury_pdf(target_date, file_path, clinic_info=c_info)
            self.status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

    def export_excel(self):
        target_date = self.date_entry.get().strip() or None
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if file_path:
            c_info = load_clinic_profile()
            ok, msg = self.repo.export_treasury_excel(target_date, file_path, clinic_info=c_info)
            self.status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

    def _populate_transactions_list(self, scroll_frame, items, formatter, empty_text):
        for w in scroll_frame.winfo_children():
            w.destroy()

        if items:
            for item in items:
                card = ctk.CTkFrame(
                    scroll_frame,
                    fg_color=THEME["bg_card_secondary"],
                    corner_radius=10,
                    border_width=1,
                    border_color=THEME["border"],
                )
                card.pack(fill="x", pady=3)
                ctk.CTkLabel(
                    card,
                    text=formatter(item),
                    font=get_font(size=13, weight="bold"),
                    text_color=THEME["text_primary"],
                ).pack(anchor="e", padx=12, pady=8)
        else:
            ctk.CTkLabel(
                scroll_frame,
                text=empty_text,
                font=get_font(size=13),
                text_color=THEME["text_muted"],
            ).pack(pady=25)

    def load_treasury_data(self):
        target_date = self.date_entry.get().strip() or None
        inflows, outflows, summary = self.repo.get_daily_transactions(target_date)

        # تحديث البطاقات
        self.card_opening.configure(text=f"{float(summary.get('opening_balance', 0)):,.2f} ر.ي")
        self.card_inflow.configure(text=f"{float(summary.get('total_inflow', 0)):,.2f} ر.ي")
        self.card_outflow.configure(text=f"{float(summary.get('total_outflow', 0)):,.2f} ر.ي")
        self.card_net.configure(text=f"{float(summary.get('net_cash', 0)):,.2f} ر.ي")

        # تعبئة الوارد والصادر
        self._populate_transactions_list(
            self.inflow_scroll,
            inflows,
            lambda item: f"المصدر: {item['source']}  |  المبلغ: {float(item['amount']):,.2f} ر.ي  |  الطريقة: {item['method']}  |  البيان: {item['notes']}",
            "لا توجد مقبوضات مسجلة في هذا التاريخ.",
        )
        self._populate_transactions_list(
            self.outflow_scroll,
            outflows,
            lambda item: f"المستفيد: {item['source']}  |  المبلغ: {float(item['amount']):,.2f} ر.ي  |  البيان: {item['notes']}",
            "لا توجد مدفوعات أو مصروفات مسجلة في هذا التاريخ.",
        )

    def perform_daily_closing(self):
        target_date = self.date_entry.get().strip() or datetime.date.today().strftime("%Y-%m-%d")
        ok, msg = self.repo.close_day_treasury(target_date, username="Admin", notes="إغلاق يومي تلقائي")
        self.status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])
        if ok:
            self.load_treasury_data()

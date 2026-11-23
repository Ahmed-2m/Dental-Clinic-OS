import datetime
from tkinter import filedialog
from tkcalendar import Calendar
from mysql.connector import Error
import customtkinter as ctk

from backend.statements_repo import StatementsRepository
from ui.theme import THEME, get_font, setup_rtl_entry, setup_rtl_textbox

class StatementsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.repo = StatementsRepository()

        self.selected_patient_id = None
        self.selected_lab_id = None
        self.selected_emp_id = None
        self.selected_supplier_id = None

        self.patient_map = {}
        self.lab_map = {}
        self.emp_map = {}
        self.supplier_map = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # حاوية التبويبات الرئيسية
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
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_staff = self.tabview.add("👥 كشوفات حسابات الموظفين")
        self.tab_labs = self.tabview.add("🔬 كشوفات حسابات المعامل")
        self.tab_purchases = self.tabview.add("📦 كشوفات حسابات المشتريات")
        self.tab_patients = self.tabview.add("👤 كشوفات حسابات المرضى")

        self.tabview.set("👤 كشوفات حسابات المرضى")

        self._build_patients_statement_tab()
        self._build_labs_statement_tab()
        self._build_purchases_statement_tab()
        self._build_staff_statement_tab()

    def open_calendar_popup(self, target_entry):
        top = ctk.CTkToplevel(self)
        top.title("اختيار التاريخ")
        top.geometry("320x300")
        top.attributes("-topmost", True)
        top.resizable(False, False)

        today = datetime.date.today()
        cal = Calendar(top, selectmode="day", year=today.year, month=today.month, day=today.day)
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

    def _create_period_filter_box(self, container, generate_command, theme_color):
        """إنشاء شريط موحد لاختيار الفترة والتاريخ وزر توليد الكشف لجميع الأقسام"""
        filter_box = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        filter_box.pack(fill="x", padx=12, pady=(10, 8))
        
        row2 = ctk.CTkFrame(filter_box, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=10)

        def set_today(start_ent, end_ent):
            t = datetime.date.today().strftime("%Y-%m-%d")
            start_ent.delete(0, "end"); start_ent.insert(0, t)
            end_ent.delete(0, "end"); end_ent.insert(0, t)
            generate_command()

        def set_month(start_ent, end_ent):
            today = datetime.date.today()
            f_day = today.replace(day=1).strftime("%Y-%m-%d")
            t_day = today.strftime("%Y-%m-%d")
            start_ent.delete(0, "end"); start_ent.insert(0, f_day)
            end_ent.delete(0, "end"); end_ent.insert(0, t_day)
            generate_command()

        def set_all(start_ent, end_ent):
            start_ent.delete(0, "end"); end_ent.delete(0, "end")
            generate_command()

        ctk.CTkButton(row2, text="♾️ كامل السجل", width=95, height=32, fg_color=THEME["bg_app"], hover_color=THEME["bg_card_hover"], border_width=1, border_color=THEME["border"], font=get_font(size=11), command=lambda: set_all(start_ent, end_ent)).pack(side="right", padx=(0, 6))
        ctk.CTkButton(row2, text="📆 الشهر الحالي", width=95, height=32, fg_color=THEME["bg_app"], hover_color=THEME["bg_card_hover"], border_width=1, border_color=THEME["border"], font=get_font(size=11), command=lambda: set_month(start_ent, end_ent)).pack(side="right", padx=(0, 6))
        ctk.CTkButton(row2, text="📅 اليوم", width=75, height=32, fg_color=THEME["bg_app"], hover_color=THEME["bg_card_hover"], border_width=1, border_color=THEME["border"], font=get_font(size=11), command=lambda: set_today(start_ent, end_ent)).pack(side="right", padx=(0, 16))

        ctk.CTkLabel(row2, text="من:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        start_ent = ctk.CTkEntry(row2, width=105, height=32, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        start_ent.pack(side="right", padx=(0, 2))
        ctk.CTkButton(row2, text="📅", width=34, height=32, fg_color=THEME["bg_app"], border_width=1, border_color=THEME["border"], command=lambda: self.open_calendar_popup(start_ent)).pack(side="right", padx=(0, 12))

        ctk.CTkLabel(row2, text="إلى:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        end_ent = ctk.CTkEntry(row2, width=105, height=32, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        end_ent.pack(side="right", padx=(0, 2))
        ctk.CTkButton(row2, text="📅", width=34, height=32, fg_color=THEME["bg_app"], border_width=1, border_color=THEME["border"], command=lambda: self.open_calendar_popup(end_ent)).pack(side="right", padx=(0, 14))

        ctk.CTkButton(row2, text="🔍 توليد وعرض الكشف", width=140, height=32, fg_color=theme_color, hover_color=THEME["primary_hover"], font=get_font(size=12, weight="bold"), command=generate_command).pack(side="left")

        return filter_box, start_ent, end_ent

    # =========================================================================
    # 1. تبويب كشوفات حسابات المرضى
    # =========================================================================
    def _build_patients_statement_tab(self):
        container = self.tab_patients
        filter_box = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        filter_box.pack(fill="x", padx=12, pady=(10, 8))

        row1 = ctk.CTkFrame(filter_box, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(10, 6))

        ctk.CTkLabel(row1, text="👤 اختيار المريض:", font=get_font(size=12, weight="bold"), text_color=THEME["primary"]).pack(side="right", padx=(0, 8))
        self.combo_patient = ctk.CTkComboBox(row1, width=320, height=34, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"], command=self._on_patient_selected)
        self.combo_patient.pack(side="right", padx=(0, 16))

        ctk.CTkButton(row1, text="🔄 تحديث المرضى", width=105, height=32, fg_color=THEME["bg_app"], hover_color=THEME["bg_card_hover"], border_width=1, border_color=THEME["border"], command=self.load_patients_list).pack(side="right", padx=(0, 16))

        _, self.p_date_start, self.p_date_end = self._create_period_filter_box(container, self.generate_patient_statement, THEME["primary"])

        self.p_stats_bar = ctk.CTkFrame(container, fg_color="transparent")
        self.p_stats_bar.pack(fill="x", padx=12, pady=(0, 6))

        def create_stat_card(parent, title, val_init, text_color):
            card = ctk.CTkFrame(parent, fg_color=THEME["bg_card_secondary"], corner_radius=10, border_width=1, border_color=THEME["border"])
            card.pack(side="right", fill="both", expand=True, padx=4)
            ctk.CTkLabel(card, text=title, font=get_font(size=10, weight="bold"), text_color=THEME["text_secondary"]).pack(anchor="e", padx=12, pady=(6, 1))
            val_lbl = ctk.CTkLabel(card, text=val_init, font=get_font(size=13, weight="bold"), text_color=text_color)
            val_lbl.pack(anchor="e", padx=12, pady=(0, 6))
            return val_lbl

        self.p_card_name = create_stat_card(self.p_stats_bar, "👤 المريض المحدد:", "يرجى اختيار مريض", THEME["primary"])
        self.p_card_cost = create_stat_card(self.p_stats_bar, "💵 إجمالي تكاليف العلاجات:", "0.00 ر.ي", THEME["indigo"])
        self.p_card_paid = create_stat_card(self.p_stats_bar, "💳 إجمالي المبالغ المسددة:", "0.00 ر.ي", THEME["success"])
        self.p_card_debt = create_stat_card(self.p_stats_bar, "⚠️ صافي الرصيد / المديونية:", "0.00 ر.ي", THEME["warning"])

        self.p_scroll_content = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.p_scroll_content.pack(fill="both", expand=True, padx=12, pady=4)

        p_export_bar = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        p_export_bar.pack(fill="x", padx=12, pady=(4, 10))

        ctk.CTkButton(p_export_bar, text="📄 تصدير كشف حساب رسمي PDF", width=220, height=36, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], font=get_font(size=12, weight="bold"), command=self.export_patient_pdf).pack(side="right", padx=12, pady=8)
        ctk.CTkButton(p_export_bar, text="📊 تصدير كشف حساب Excel", width=200, height=36, fg_color=THEME["success"], hover_color=THEME["success_hover"], font=get_font(size=12, weight="bold"), command=self.export_patient_excel).pack(side="right", padx=4, pady=8)
        self.p_status_lbl = ctk.CTkLabel(p_export_bar, text="", font=get_font(size=11))
        self.p_status_lbl.pack(side="left", padx=14)

        self.load_patients_list()

    def load_patients_list(self):
        patients = self.repo.get_patients_list()
        self.patient_map.clear()
        values = []
        for p in patients:
            p_id, name, phone, debt = p
            debt_str = f"[مدين: {float(debt):,.0f}]" if float(debt) > 0 else "[خالص]"
            display_txt = f"#{p_id} - {name} ({phone}) {debt_str}"
            self.patient_map[display_txt] = p_id
            values.append(display_txt)
        if values:
            self.combo_patient.configure(values=values)
            self.combo_patient.set(values[0])
            self.selected_patient_id = self.patient_map[values[0]]
            self.generate_patient_statement()
        else:
            self.combo_patient.configure(values=["لا يوجد مرضى مسجلين"])
            self.combo_patient.set("لا يوجد مرضى مسجلين")
            self.selected_patient_id = None

    def _on_patient_selected(self, choice):
        if choice in self.patient_map:
            self.selected_patient_id = self.patient_map[choice]
            self.generate_patient_statement()

    def generate_patient_statement(self):
        if not self.selected_patient_id:
            return
        for w in self.p_scroll_content.winfo_children():
            w.destroy()
        s_date = self.p_date_start.get().strip() or None
        e_date = self.p_date_end.get().strip() or None
        p_info, items, summary = self.repo.get_patient_statement(self.selected_patient_id, s_date, e_date)
        if not p_info:
            return
        self.p_card_name.configure(text=f"{p_info['full_name']} (#{p_info['patient_id']})")
        self.p_card_cost.configure(text=f"{summary['total_cost']:,.2f} ر.ي")
        self.p_card_paid.configure(text=f"{summary['total_paid']:,.2f} ر.ي")
        debt_val = summary['net_debt']
        self.p_card_debt.configure(text=f"{debt_val:,.2f} ر.ي" if debt_val > 0 else "الحساب خالص", text_color=THEME["danger"] if debt_val > 0 else THEME["success"])
        
        if items:
            for it in reversed(items):
                card = ctk.CTkFrame(self.p_scroll_content, fg_color=THEME["bg_card_secondary"], corner_radius=8, border_width=1, border_color=THEME["border"])
                card.pack(fill="x", pady=3)
                txt = f"قيد #{it['id']} | التاريخ: {it['date']} - {it['type']} | مدين (تكلفة): {it['cost']:,.2f} | دائن (مسدد): {it['paid']:,.2f} | المتبقي: {it['remain']:,.2f}"
                ctk.CTkLabel(card, text=txt, font=get_font(size=11, weight="bold"), text_color=THEME["text_primary"]).pack(anchor="e", padx=10, pady=8)

    def export_patient_pdf(self):
        if not self.selected_patient_id: return
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if file_path:
            ok, msg = self.repo.export_patient_statement_pdf(self.selected_patient_id, file_path, self.p_date_start.get().strip() or None, self.p_date_end.get().strip() or None)
            self.p_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

    def export_patient_excel(self):
        if not self.selected_patient_id: return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if file_path:
            ok, msg = self.repo.export_patient_statement_excel(self.selected_patient_id, file_path, self.p_date_start.get().strip() or None, self.p_date_end.get().strip() or None)
            self.p_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

    # =========================================================================
    # 2. تبويب كشوفات حسابات المعامل
    # =========================================================================
    def _build_labs_statement_tab(self):
        container = self.tab_labs
        filter_box = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        filter_box.pack(fill="x", padx=12, pady=(10, 8))

        row1 = ctk.CTkFrame(filter_box, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(10, 6))

        ctk.CTkLabel(row1, text="🏢 اختيار المعمل:", font=get_font(size=12, weight="bold"), text_color=THEME["teal"]).pack(side="right", padx=(0, 8))
        self.combo_lab = ctk.CTkComboBox(row1, width=320, height=34, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"], command=self._on_lab_selected)
        self.combo_lab.pack(side="right", padx=(0, 16))
        ctk.CTkButton(row1, text="🔄 تحديث المعامل", width=105, height=32, fg_color=THEME["bg_app"], hover_color=THEME["bg_card_hover"], border_width=1, border_color=THEME["border"], command=self.load_labs_list).pack(side="right", padx=(0, 16))

        _, self.l_date_start, self.l_date_end = self._create_period_filter_box(container, self.generate_lab_statement, THEME["teal"])

        self.l_stats_bar = ctk.CTkFrame(container, fg_color="transparent")
        self.l_stats_bar.pack(fill="x", padx=12, pady=(0, 6))

        def create_l_stat_card(parent, title, val_init, text_color):
            card = ctk.CTkFrame(parent, fg_color=THEME["bg_card_secondary"], corner_radius=10, border_width=1, border_color=THEME["border"])
            card.pack(side="right", fill="both", expand=True, padx=4)
            ctk.CTkLabel(card, text=title, font=get_font(size=10, weight="bold"), text_color=THEME["text_secondary"]).pack(anchor="e", padx=12, pady=(6, 1))
            val_lbl = ctk.CTkLabel(card, text=val_init, font=get_font(size=13, weight="bold"), text_color=text_color)
            val_lbl.pack(anchor="e", padx=12, pady=(0, 6))
            return val_lbl

        self.l_card_name = create_l_stat_card(self.l_stats_bar, "🏢 المعمل المحدد:", "يرجى اختيار معمل", THEME["teal"])
        self.l_card_cost = create_l_stat_card(self.l_stats_bar, "📦 إجمالي أوامر العمل (مدين):", "0.00 ر.ي", THEME["indigo"])
        self.l_card_paid = create_l_stat_card(self.l_stats_bar, "💵 إجمالي المسدد (دائن):", "0.00 ر.ي", THEME["success"])
        self.l_card_debt = create_l_stat_card(self.l_stats_bar, "⚖️ صافي الرصيد المستحق:", "0.00 ر.ي", THEME["warning"])

        self.l_scroll_content = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.l_scroll_content.pack(fill="both", expand=True, padx=12, pady=4)

        l_export_bar = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        l_export_bar.pack(fill="x", padx=12, pady=(4, 10))

        ctk.CTkButton(l_export_bar, text="📄 تصدير كشف حساب المعمل PDF", width=220, height=36, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], font=get_font(size=12, weight="bold"), command=self.export_lab_pdf).pack(side="right", padx=12, pady=8)
        ctk.CTkButton(l_export_bar, text="📊 تصدير كشف حساب المعمل Excel", width=210, height=36, fg_color=THEME["success"], hover_color=THEME["success_hover"], font=get_font(size=12, weight="bold"), command=self.export_lab_excel).pack(side="right", padx=4, pady=8)
        self.l_status_lbl = ctk.CTkLabel(l_export_bar, text="", font=get_font(size=11))
        self.l_status_lbl.pack(side="left", padx=14)

        self.load_labs_list()

    def load_labs_list(self):
        labs = self.repo.get_labs_list()
        self.lab_map.clear()
        values = []
        for l in labs:
            lab_id, name, phone, balance = l
            display_txt = f"#{lab_id} - {name} ({phone})"
            self.lab_map[display_txt] = lab_id
            values.append(display_txt)
        if values:
            self.combo_lab.configure(values=values)
            self.combo_lab.set(values[0])
            self.selected_lab_id = self.lab_map[values[0]]
            self.generate_lab_statement()

    def _on_lab_selected(self, choice):
        if choice in self.lab_map:
            self.selected_lab_id = self.lab_map[choice]
            self.generate_lab_statement()

    def generate_lab_statement(self):
        if not self.selected_lab_id: 
            return
        for w in self.l_scroll_content.winfo_children(): 
            w.destroy()
            
        s_date = self.l_date_start.get().strip() or None
        e_date = self.l_date_end.get().strip() or None
        
        lab_info, orders, payments, summary = self.repo.get_lab_statement(self.selected_lab_id, s_date, e_date)
        if not lab_info: 
            return
            
        # تحديث البطاقات الإحصائية في الواجهة
        self.l_card_name.configure(text=f"{lab_info['lab_name']} (#{lab_info['lab_id']})")
        self.l_card_cost.configure(text=f"{summary['total_orders_cost']:,.2f} ر.ي")
        self.l_card_paid.configure(text=f"{summary['total_paid_amount']:,.2f} ر.ي")
        self.l_card_debt.configure(text=f"{summary['net_balance']:,.2f} ر.ي", text_color=THEME["danger"] if summary['net_balance'] > 0 else THEME["success"])

        # عرض أوامر العمل (مدين)
        if orders:
            ctk.CTkLabel(self.l_scroll_content, text="📋 أوامر العمل والتركيبات الطبية (مدين):", font=get_font(size=12, weight="bold"), text_color=THEME["teal"]).pack(anchor="e", pady=(4, 4))
            for o in orders:
                card = ctk.CTkFrame(self.l_scroll_content, fg_color=THEME["bg_card_secondary"], corner_radius=8, border_width=1, border_color=THEME["border"])
                card.pack(fill="x", pady=2)
                txt = f"أمر عمل #{o['order_id']} | الفاتورة: #{o['invoice_id']} | التاريخ: {o['receive_date']} | المريض: {o['patient_name']} | النوع: {o['work_type']} | التكلفة: {o['cost']:,.2f} ر.ي"
                ctk.CTkLabel(card, text=txt, font=get_font(size=11), text_color=THEME["text_primary"]).pack(anchor="e", padx=10, pady=6)

        # عرض سندات الصرف (دائن)
        if payments:
            ctk.CTkLabel(self.l_scroll_content, text="💵 سندات الصرف والدفعات المالية (دائن):", font=get_font(size=12, weight="bold"), text_color=THEME["success"]).pack(anchor="e", pady=(10, 4))
            for p in payments:
                card = ctk.CTkFrame(self.l_scroll_content, fg_color=THEME["bg_card_secondary"], corner_radius=8, border_width=1, border_color=THEME["border"])
                card.pack(fill="x", pady=2)
                txt = f"سند صرف #{p['voucher_no']} | التاريخ: {p['date']} | المبلغ: {p['amount']:,.2f} ر.ي | البيان: {p['notes']}"
                ctk.CTkLabel(card, text=txt, font=get_font(size=11), text_color=THEME["text_primary"]).pack(anchor="e", padx=10, pady=6)

        if not orders and not payments:
            ctk.CTkLabel(self.l_scroll_content, text="لا توجد حركات مسجلة للمعمل في الفترة المحددة.", font=get_font(size=11), text_color=THEME["text_muted"]).pack(pady=20)

    def export_lab_pdf(self):
        if not self.selected_lab_id: return
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if file_path:
            s_date = self.l_date_start.get().strip() or None
            e_date = self.l_date_end.get().strip() or None
            ok, msg = self.repo.export_lab_statement_pdf(self.selected_lab_id, file_path, s_date, e_date)
            self.l_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

    def export_lab_excel(self):
        if not self.selected_lab_id: return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if file_path:
            s_date = self.l_date_start.get().strip() or None
            e_date = self.l_date_end.get().strip() or None
            ok, msg = self.repo.export_lab_statement_excel(self.selected_lab_id, file_path, s_date, e_date)
            self.l_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

    # =========================================================================
    # 3. تبويب كشوفات حسابات المشتريات
    # =========================================================================
    def _build_purchases_statement_tab(self):
        container = self.tab_purchases
        filter_box = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        filter_box.pack(fill="x", padx=12, pady=(10, 8))

        row1 = ctk.CTkFrame(filter_box, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(10, 6))

        ctk.CTkLabel(row1, text="📦 اختيار المورد لعرض كشف الحساب:", font=get_font(size=12, weight="bold"), text_color=THEME["indigo"]).pack(side="right", padx=(0, 8))
        self.combo_supplier = ctk.CTkComboBox(row1, width=320, height=34, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"], command=self._on_supplier_selected)
        self.combo_supplier.pack(side="right", padx=(0, 16))
        ctk.CTkButton(row1, text="🔄 تحديث الموردين", width=110, height=32, fg_color=THEME["bg_app"], hover_color=THEME["bg_card_hover"], border_width=1, border_color=THEME["border"], command=self.load_suppliers_list).pack(side="right", padx=(0, 16))

        _, self.pur_date_start, self.pur_date_end = self._create_period_filter_box(container, self.generate_purchase_statement, THEME["indigo"])

        self.pur_stats_bar = ctk.CTkFrame(container, fg_color="transparent")
        self.pur_stats_bar.pack(fill="x", padx=12, pady=(0, 6))

        def create_pur_stat_card(parent, title, val_init, text_color):
            card = ctk.CTkFrame(parent, fg_color=THEME["bg_card_secondary"], corner_radius=10, border_width=1, border_color=THEME["border"])
            card.pack(side="right", fill="both", expand=True, padx=4)
            ctk.CTkLabel(card, text=title, font=get_font(size=10, weight="bold"), text_color=THEME["text_secondary"]).pack(anchor="e", padx=12, pady=(6, 1))
            val_lbl = ctk.CTkLabel(card, text=val_init, font=get_font(size=12, weight="bold"), text_color=text_color)
            val_lbl.pack(anchor="e", padx=12, pady=(0, 6))
            return val_lbl

        self.pur_card_name = create_pur_stat_card(self.pur_stats_bar, "📦 المورد المحدد", "يرجى اختيار مورد", THEME["indigo"])
        self.pur_card_total = create_pur_stat_card(self.pur_stats_bar, "💵 إجمالي المشتريات (مدين)", "0.00 ر.ي", THEME["text_primary"])
        self.pur_card_paid = create_pur_stat_card(self.pur_stats_bar, "💳 إجمالي المسدد (دائن)", "0.00 ر.ي", THEME["success"])
        self.pur_card_remain = create_pur_stat_card(self.pur_stats_bar, "⚠️ الرصيد المتبقي", "0.00 ر.ي", THEME["warning"])

        self.pur_scroll_content = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.pur_scroll_content.pack(fill="both", expand=True, padx=12, pady=4)

        pur_export_bar = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        pur_export_bar.pack(fill="x", padx=12, pady=(4, 10))

        ctk.CTkButton(pur_export_bar, text="📄 تصدير كشف حساب المشتريات PDF", width=220, height=36, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], font=get_font(size=12, weight="bold"), command=self.export_purchase_pdf).pack(side="right", padx=12, pady=8)
        ctk.CTkButton(pur_export_bar, text="📊 تصدير كشف حساب المشتريات Excel", width=210, height=36, fg_color=THEME["success"], hover_color=THEME["success_hover"], font=get_font(size=12, weight="bold"), command=self.export_purchase_excel).pack(side="right", padx=4, pady=8)
        self.pur_status_lbl = ctk.CTkLabel(pur_export_bar, text="", font=get_font(size=11))
        self.pur_status_lbl.pack(side="left", padx=14)

        self.load_suppliers_list()

    def load_suppliers_list(self):
        conn = self.repo.get_connection() if hasattr(self.repo, 'get_connection') else None
        if not conn:
            from backend.database import Database
            db = Database()
            conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT supplier_id, supplier_name, phone FROM suppliers ORDER BY supplier_id DESC;")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            self.supplier_map.clear()
            values = []
            for r in rows:
                sup_id, name, phone = r
                display_txt = f"{name} (معرف #{sup_id})"
                self.supplier_map[display_txt] = sup_id
                values.append(display_txt)

            if values:
                self.combo_supplier.configure(values=values)
                self.combo_supplier.set(values[0])
                self.selected_supplier_id = self.supplier_map[values[0]]
                self.generate_purchase_statement()
            else:
                self.combo_supplier.configure(values=["لا توجد موردين مسجلين"])
                self.combo_supplier.set("لا توجد موردين مسجلين")
                self.selected_supplier_id = None
        except Error as e:
            print(f"[خطأ في تحميل الموردين لكشوفات المشتريات]: {e}")

    def _on_supplier_selected(self, choice):
        if choice in self.supplier_map:
            self.selected_supplier_id = self.supplier_map[choice]
            self.generate_purchase_statement()

    def generate_purchase_statement(self):
        if not self.selected_supplier_id:
            return
        for w in self.pur_scroll_content.winfo_children():
            w.destroy()

        s_date = self.pur_date_start.get().strip() or None
        e_date = self.pur_date_end.get().strip() or None

        from backend.database import Database
        db = Database()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            
            inv_query = """
                SELECT purchase_id, COALESCE(invoice_number, '-'), description, purchase_date, total_amount, paid_amount, remaining_amount, payment_status, COALESCE(purchase_type, 'Cash'), COALESCE(supplier_voucher_no, '-')
                FROM purchases
                WHERE supplier_id = %s
            """
            inv_params = [self.selected_supplier_id]
            if s_date:
                inv_query += " AND purchase_date >= %s"
                inv_params.append(s_date)
            if e_date:
                inv_query += " AND purchase_date <= %s"
                inv_params.append(e_date)
            inv_query += " ORDER BY purchase_date DESC, purchase_id DESC;"
            
            cursor.execute(inv_query, tuple(inv_params))
            invoices = cursor.fetchall()

            pay_query = """
                SELECT payment_id, amount, payment_date, COALESCE(supplier_voucher_no, '-'), notes
                FROM supplier_payments
                WHERE supplier_id = %s
            """
            pay_params = [self.selected_supplier_id]
            if s_date:
                pay_query += " AND payment_date >= %s"
                pay_params.append(s_date)
            if e_date:
                pay_query += " AND payment_date <= %s"
                pay_params.append(e_date)
            pay_query += " ORDER BY payment_date DESC, payment_id DESC;"

            cursor.execute(pay_query, tuple(pay_params))
            payments = cursor.fetchall()
            
            cursor.close()
            conn.close()

            total_p = sum(float(r[4] or 0) for r in invoices)
            paid_p = sum(float(r[5] or 0) for r in invoices) + sum(float(p[1] or 0) for p in payments)
            remain_p = sum(float(r[6] or 0) for r in invoices)

            self.pur_card_name.configure(text=f"معرف المورد (#{self.selected_supplier_id})")
            self.pur_card_total.configure(text=f"{total_p:,.2f} ر.ي")
            self.pur_card_paid.configure(text=f"{paid_p:,.2f} ر.ي")
            self.pur_card_remain.configure(text=f"{remain_p:,.2f} ر.ي", text_color=THEME["danger"] if remain_p > 0 else THEME["success"])

            if payments:
                ctk.CTkLabel(self.pur_scroll_content, text="💵 سجل سندات الصرف (دائن):", font=get_font(size=12, weight="bold"), text_color=THEME["success"]).pack(anchor="e", padx=5, pady=(5, 5))
                for pay in payments:
                    pay_id, amount, p_date, vouch_no, notes = pay
                    card = ctk.CTkFrame(self.pur_scroll_content, fg_color=THEME["bg_app"], corner_radius=8, border_width=1, border_color=THEME["border"])
                    card.pack(fill="x", pady=3, padx=5)
                    
                    row = ctk.CTkFrame(card, fg_color="transparent")
                    row.pack(fill="x", padx=12, pady=6)
                    for col in range(5): row.grid_columnconfigure(col, weight=1)

                    ctk.CTkLabel(row, text=f"البيان: {notes or '-'}", font=get_font(size=11), text_color=THEME["text_primary"], anchor="e").grid(row=0, column=0, sticky="e", padx=2)
                    ctk.CTkLabel(row, text=f"التاريخ: {p_date}", font=get_font(size=11), text_color=THEME["text_secondary"], anchor="e").grid(row=0, column=1, sticky="e", padx=2)
                    ctk.CTkLabel(row, text=f"دائن (مسدد): {float(amount):,.2f} ر.ي", font=get_font(size=11, weight="bold"), text_color=THEME["success"], anchor="e").grid(row=0, column=2, sticky="e", padx=2)
                    ctk.CTkLabel(row, text=f"رقم السند: #{vouch_no}", font=get_font(size=11, weight="bold"), text_color=THEME["teal"], anchor="e").grid(row=0, column=3, sticky="e", padx=2)
                    ctk.CTkLabel(row, text=f"سند صرف #{pay_id}", font=get_font(size=11, weight="bold"), text_color=THEME["indigo"], anchor="e").grid(row=0, column=4, sticky="e", padx=2)

            if invoices:
                ctk.CTkLabel(self.pur_scroll_content, text="📋 سجل فواتير المشتريات (مدين):", font=get_font(size=12, weight="bold"), text_color=THEME["indigo"]).pack(anchor="e", padx=5, pady=(15, 5))
                for r in invoices:
                    p_id, inv_num, desc, p_date, total, paid, remain, status, p_type, vouch_no = r
                    card = ctk.CTkFrame(self.pur_scroll_content, fg_color=THEME["bg_app"], corner_radius=8, border_width=1, border_color=THEME["border"])
                    card.pack(fill="x", pady=3, padx=5)

                    status_str = "خالص" if status == "Paid" else ("مسدد جزئياً" if status == "Partial" else "أجل / غير مسدد")
                    status_color = THEME["success"] if status == "Paid" else (THEME["warning"] if status == "Partial" else THEME["danger"])
                    p_type_txt = "آجل" if p_type == 'Credit' else "نقداً"

                    row = ctk.CTkFrame(card, fg_color="transparent")
                    row.pack(fill="x", padx=12, pady=6)
                    for col in range(8): row.grid_columnconfigure(col, weight=1)

                    ctk.CTkLabel(row, text=f"الحالة: {status_str}", font=get_font(size=11, weight="bold"), text_color=status_color, anchor="e").grid(row=0, column=0, sticky="e", padx=2)
                    ctk.CTkLabel(row, text=f"المتبقي: {float(remain):,.2f}", font=get_font(size=11, weight="bold"), text_color=THEME["danger"], anchor="e").grid(row=0, column=1, sticky="e", padx=2)
                    ctk.CTkLabel(row, text=f"المدفوع: {float(paid):,.2f}", font=get_font(size=11), text_color=THEME["success"], anchor="e").grid(row=0, column=2, sticky="e", padx=2)
                    ctk.CTkLabel(row, text=f"إجمالي (مدين): {float(total):,.2f}", font=get_font(size=11), text_color=THEME["text_primary"], anchor="e").grid(row=0, column=3, sticky="e", padx=2)
                    ctk.CTkLabel(row, text=f"رقم السند: #{vouch_no}", font=get_font(size=11), text_color=THEME["teal"], anchor="e").grid(row=0, column=4, sticky="e", padx=2)
                    ctk.CTkLabel(row, text=f"التاريخ: {p_date}", font=get_font(size=11), text_color=THEME["text_secondary"], anchor="e").grid(row=0, column=5, sticky="e", padx=2)
                    ctk.CTkLabel(row, text=f"النوع: {p_type_txt}", font=get_font(size=11), text_color=THEME["purple"], anchor="e").grid(row=0, column=6, sticky="e", padx=2)
                    ctk.CTkLabel(row, text=f"فاتورة: #{inv_num}", font=get_font(size=11, weight="bold"), text_color=THEME["indigo"], anchor="e").grid(row=0, column=7, sticky="e", padx=2)
            
            if not payments and not invoices:
                ctk.CTkLabel(self.pur_scroll_content, text="لا توجد حركات أو فواتير مسجلة لهذا المورد في الفترة المحددة.", font=get_font(size=11), text_color=THEME["text_muted"]).pack(pady=20)
        except Error as e:
            print(f"[خطأ في توليد كشف حساب المشتريات]: {e}")

    def export_purchase_pdf(self):
        if not self.selected_supplier_id:
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if file_path:
            ok, msg = self.repo.export_purchase_statement_pdf(self.selected_supplier_id, file_path)
            self.pur_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

    def export_purchase_excel(self):
        if not self.selected_supplier_id:
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if file_path:
            ok, msg = self.repo.export_purchase_statement_excel(self.selected_supplier_id, file_path)
            self.pur_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

    # =========================================================================
    # 4. تبويب كشوفات حسابات الموظفين
    # =========================================================================
    def _build_staff_statement_tab(self):
        container = self.tab_staff
        filter_box = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        filter_box.pack(fill="x", padx=12, pady=(10, 8))

        row1 = ctk.CTkFrame(filter_box, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(10, 6))

        ctk.CTkLabel(row1, text="👥 اختيار الموظف:", font=get_font(size=12, weight="bold"), text_color=THEME["purple"]).pack(side="right", padx=(0, 8))
        self.combo_staff = ctk.CTkComboBox(row1, width=320, height=34, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"], command=self._on_staff_selected)
        self.combo_staff.pack(side="right", padx=(0, 16))

        ctk.CTkButton(row1, text="🔄 تحديث الموظفين", width=115, height=32, fg_color=THEME["bg_app"], hover_color=THEME["bg_card_hover"], border_width=1, border_color=THEME["border"], command=self.load_staff_list).pack(side="right", padx=(0, 16))

        _, self.s_date_start, self.s_date_end = self._create_period_filter_box(container, self.generate_staff_statement, THEME["purple"])

        self.s_stats_bar = ctk.CTkFrame(container, fg_color="transparent")
        self.s_stats_bar.pack(fill="x", padx=12, pady=(0, 6))

        def create_s_stat_card(parent, title, val_init, text_color):
            card = ctk.CTkFrame(parent, fg_color=THEME["bg_card_secondary"], corner_radius=10, border_width=1, border_color=THEME["border"])
            card.pack(side="right", fill="both", expand=True, padx=3)
            ctk.CTkLabel(card, text=title, font=get_font(size=10, weight="bold"), text_color=THEME["text_secondary"]).pack(anchor="e", padx=10, pady=(6, 1))
            val_lbl = ctk.CTkLabel(card, text=val_init, font=get_font(size=12, weight="bold"), text_color=text_color)
            val_lbl.pack(anchor="e", padx=10, pady=(0, 6))
            return val_lbl

        self.s_card_name = create_s_stat_card(self.s_stats_bar, "👥 الموظف المحدد", "يرجى اختيار موظف", THEME["purple"])
        self.s_card_salary = create_s_stat_card(self.s_stats_bar, "💰 الراتب الأساسي (دائن)", "0.00 ر.ي", THEME["indigo"])
        self.s_card_trans = create_s_stat_card(self.s_stats_bar, "📋 إجمالي الحركات (مدين)", "0.00 ر.ي", THEME["warning"])
        self.s_card_net = create_s_stat_card(self.s_stats_bar, "💵 الراتب المتبقي للصرف", "0.00 ر.ي", THEME["success"])

        self.s_scroll_content = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.s_scroll_content.pack(fill="both", expand=True, padx=12, pady=4)

        s_export_bar = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        s_export_bar.pack(fill="x", padx=12, pady=(4, 10))

        ctk.CTkButton(s_export_bar, text="📄 تصدير كشف حساب الموظف PDF", width=220, height=36, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], font=get_font(size=12, weight="bold"), command=self.export_staff_pdf).pack(side="right", padx=12, pady=8)
        ctk.CTkButton(s_export_bar, text="📊 تصدير كشف حساب الموظف Excel", width=210, height=36, fg_color=THEME["success"], hover_color=THEME["success_hover"], font=get_font(size=12, weight="bold"), command=self.export_staff_excel).pack(side="right", padx=4, pady=8)
        self.s_status_lbl = ctk.CTkLabel(s_export_bar, text="", font=get_font(size=11))
        self.s_status_lbl.pack(side="left", padx=14)

        self.load_staff_list()

    def load_staff_list(self):
        staffs = self.repo.get_staff_list()
        self.emp_map.clear()
        values = []
        for s in staffs:
            emp_id, name, phone, salary = s
            display_txt = f"#{emp_id} - {name} ({phone}) [راتب: {float(salary or 0):,.0f}]"
            self.emp_map[display_txt] = emp_id
            values.append(display_txt)

        if values:
            self.combo_staff.configure(values=values)
            self.combo_staff.set(values[0])
            self.selected_emp_id = self.emp_map[values[0]]
            self.generate_staff_statement()
        else:
            self.combo_staff.configure(values=["لا توجد موظفين مسجلين"])
            self.combo_staff.set("لا توجد موظفين مسجلين")
            self.selected_emp_id = None

    def _on_staff_selected(self, choice):
        if choice in self.emp_map:
            self.selected_emp_id = self.emp_map[choice]
            self.generate_staff_statement()

    def generate_staff_statement(self):
        if not self.selected_emp_id:
            return

        for w in self.s_scroll_content.winfo_children():
            w.destroy()

        s_date = self.s_date_start.get().strip() or None
        e_date = self.s_date_end.get().strip() or None

        emp_info, transactions, summary = self.repo.get_staff_statement(self.selected_emp_id, s_date, e_date)
        if not emp_info:
            ctk.CTkLabel(self.s_scroll_content, text="لم يتم العثور على بيانات لهذا الموظف.", font=get_font(size=12), text_color=THEME["text_muted"]).pack(pady=30)
            return

        base_salary = float(emp_info['base_salary'] or 0)
        total_trans = 0.0
        for tr in transactions:
            t_type = tr['type']
            amt = float(tr['amount'] or 0)
            if t_type in ["سلفة", "خصم", "سحب عهدة", "تسليم راتب"]:
                total_trans += amt
            elif t_type in ["مكافأة"]:
                total_trans -= amt

        net_remaining = base_salary - total_trans

        self.s_card_name.configure(text=f"{emp_info['full_name']} (#{emp_info['emp_id']})")
        self.s_card_salary.configure(text=f"{base_salary:,.2f} ر.ي")
        self.s_card_trans.configure(text=f"{summary['total_transactions']:,.2f} ر.ي")
        self.s_card_net.configure(
            text=f"{net_remaining:,.2f} ر.ي", 
            text_color=THEME["success"] if net_remaining >= 0 else THEME["danger"]
        )

        ctk.CTkLabel(self.s_scroll_content, text="📋 سجل الحركات المالية (مدين / دائن):", font=get_font(size=13, weight="bold"), text_color=THEME["purple"]).pack(anchor="e", pady=(6, 4))

        if transactions:
            for tr in transactions:
                card = ctk.CTkFrame(self.s_scroll_content, fg_color=THEME["bg_card_secondary"], corner_radius=8, border_width=1, border_color=THEME["border"])
                card.pack(fill="x", pady=3)

                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=6)

                t_type = tr['type']
                amt = float(tr['amount'] or 0)
                debit_txt = f"مدين: {amt:,.2f}" if t_type in ["سلفة", "خصم", "سحب عهدة", "تسليم راتب"] else "-"
                credit_txt = f"دائن: {amt:,.2f}" if t_type == "مكافأة" else "-"

                txt = f"🆔 قيد #{tr['transaction_id']} | النوع: {t_type} | التاريخ: {tr['date']} | البيان: {tr['description'] or 'بدون تفاصيل'}"
                ctk.CTkLabel(row, text=txt, font=get_font(size=11), text_color=THEME["text_primary"]).pack(side="right")
                ctk.CTkLabel(row, text=f"{debit_txt} | {credit_txt}", font=get_font(size=11, weight="bold"), text_color=THEME["purple"]).pack(side="left")
        else:
            ctk.CTkLabel(self.s_scroll_content, text="لا توجد حركات مالية مسجلة لهذا الموظف في الفترة المحددة.", font=get_font(size=11), text_color=THEME["text_muted"]).pack(pady=20)

    def export_staff_pdf(self):
        if not self.selected_emp_id: return
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if file_path:
            s_date = self.s_date_start.get().strip() or None
            e_date = self.s_date_end.get().strip() or None
            ok, msg = self.repo.export_staff_statement_pdf(self.selected_emp_id, file_path, s_date, e_date)
            self.s_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])

    def export_staff_excel(self):
        if not self.selected_emp_id: return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if file_path:
            s_date = self.s_date_start.get().strip() or None
            e_date = self.s_date_end.get().strip() or None
            ok, msg = self.repo.export_staff_statement_excel(self.selected_emp_id, file_path, s_date, e_date)
            self.s_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])
import datetime
import os
import sys
import customtkinter as ctk
from PIL import Image

from backend.appointments_repo import AppointmentsRepository
from backend.database import Database
from backend.labs_repo import LabsRepository
from backend.patients_repo import PatientsRepository
from backend.print_branding import load_clinic_profile
from backend.staff_repo import StaffRepository
from backend.treasury_repo import DailyTreasuryRepository

from ui.appointments_view import AppointmentsView
from ui.labs_view import LabsView
from ui.login_view import LoginWindow
from ui.patient_visit_view import PatientVisitView
from ui.patients_view import PatientsView
from ui.purchases_view import PurchasesView
from ui.settings_view import SettingsView
from ui.staff_management_view import StaffManagementView
from ui.statements_view import StatementsView
from ui.theme import THEME, apply_global_styles, get_clinic_logo, get_font, set_appearance_mode_theme
from ui.treasury_view import TreasuryView

# تفعيل النمط العام المحفوظ (داكن أو فاتح) والمحرك العربي
apply_global_styles()


def resource_path(relative_path):
    """الحصول على المسار الصحيح للملفات سواء أثناء التشغيل العادي أو بعد التجميع"""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def apply_window_icon(window):
    """تعيين أيقونة النافذة تلقائياً من ملف app_logo.jpg"""
    base_dir = os.path.abspath(".")
    assets_dir = os.path.join(base_dir, "assets")
    ico_path = os.path.join(base_dir, "app_icon.ico")

    candidate_imgs = [
        os.path.join(base_dir, "app_logo.jpg"),
        os.path.join(assets_dir, "app_logo.jpg"),
    ]

    try:
        if os.path.exists(ico_path):
            window.iconbitmap(ico_path)
            return

        for img_p in candidate_imgs:
            if os.path.exists(img_p):
                img = Image.open(img_p).convert("RGBA")

                w, h = img.size
                if h > 0 and (w / h) > 1.4:
                    crop_box = (int(w * 0.36), int(h * 0.16), int(w * 0.64), int(h * 0.54))
                    img = img.crop(crop_box)

                side = max(img.size)
                square = Image.new("RGBA", (side, side), (255, 255, 255, 0))
                offset = ((side - img.width) // 2, (side - img.height) // 2)
                square.paste(img, offset, img)

                square.save(
                    ico_path,
                    format="ICO",
                    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
                )
                window.iconbitmap(ico_path)
                return
    except Exception as e:
        print(f"[تنبيه عند ضبط أيقونة النافذة]: {e}")


class TayseerClinicApp(ctk.CTk):
    def __init__(self, user_data=None):
        super().__init__()

        self.user_data = user_data or {"role": "admin", "full_name": "مسؤول النظام"}
        self.user_role = str(self.user_data.get("role", "admin")).lower()

        self.title("نظام عيادتي | My Clinic System")
        self.geometry("1320x840")
        self.minsize(1120, 720)

        apply_window_icon(self)

        # مخازن البيانات (Backend Repositories)
        self.db = Database.from_config_file()
        self.staff_repo = StaffRepository()
        self.patients_repo = PatientsRepository()
        self.treasury_repo = DailyTreasuryRepository()
        self.labs_repo = LabsRepository()
        self.appointments_repo = AppointmentsRepository()

        self.nav_buttons = {}
        self.active_tab_key = "dashboard"

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self._rebuild_full_shell(keep_current_tab=False)

    def _rebuild_full_shell(self, keep_current_tab=True):
        """إعادة بناء الهيكل الكامل للواجهة حسب الثيم الحالي (THEME)"""
        self.configure(fg_color=THEME["bg_app"])
        self.nav_buttons = {}

        for child in self.winfo_children():
            child.destroy()

        self._build_sidebar()
        self._build_main_shell()
        self._check_db_status()

        if keep_current_tab:
            self._refresh_current_view()
        else:
            self.show_dashboard()

    def _apply_appearance_live(self, mode_name):
        """تطبيق النمط الجديد على الثيم والنظام بالكامل فوراً"""
        set_appearance_mode_theme(mode_name)
        self.after(10, lambda: self._rebuild_full_shell(keep_current_tab=True))

    def _build_sidebar(self):
        """شريط التبويبات الجانبي الأيمن الاحترافي"""
        self.sidebar_frame = ctk.CTkFrame(
            self,
            width=280,
            corner_radius=0,
            fg_color=THEME["bg_sidebar"],
            border_width=1,
            border_color=THEME["border"],
        )
        self.sidebar_frame.grid(row=0, column=1, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        brand_frame = ctk.CTkFrame(self.sidebar_frame, fg_color=THEME["bg_card_secondary"], corner_radius=0)
        brand_frame.pack(fill="x")

        self.sidebar_logo = get_clinic_logo(variant="emblem", size=(42, 42))
        if self.sidebar_logo:
            ctk.CTkLabel(brand_frame, text="", image=self.sidebar_logo).pack(side="right", padx=(10, 14), pady=12)
        else:
            ctk.CTkLabel(brand_frame, text="🦷", font=ctk.CTkFont(size=30)).pack(side="right", padx=(10, 14), pady=14)

        brand_text_box = ctk.CTkFrame(brand_frame, fg_color="transparent")
        brand_text_box.pack(side="right", fill="x", expand=True, pady=12)

        ctk.CTkLabel(
            brand_text_box,
            text="نظام عيادتي",
            font=get_font(size=15, weight="bold"),
            text_color=THEME["text_primary"],
            anchor="e",
        ).pack(fill="x")

        ctk.CTkLabel(
            brand_text_box,
            text="النظام الإداري والطبي",
            font=get_font(size=11),
            text_color=THEME["text_secondary"],
            anchor="e",
        ).pack(fill="x")

        user_info_frame = ctk.CTkFrame(self.sidebar_frame, fg_color=THEME["bg_card"], corner_radius=0)
        user_info_frame.pack(fill="x")

        u_name = self.user_data.get("full_name", "مستخدم")
        u_role = self.user_data.get("role", "user")
        ctk.CTkLabel(
            user_info_frame,
            text=f"👤  {u_name}  ({u_role})",
            font=get_font(size=12, weight="bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="e", padx=14, pady=(10, 4))

        ctk.CTkButton(
            user_info_frame,
            text="🚪 تسجيل الخروج",
            font=get_font(size=11, weight="bold"),
            height=30,
            fg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            text_color=THEME["text_light"],
            corner_radius=6,
            command=self.logout,
        ).pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkFrame(self.sidebar_frame, height=1, fg_color=THEME["border"], corner_radius=0).pack(fill="x")

        # تثبيت بطاقة حالة قاعدة البيانات في أسفل الشريط الجانبي بعرض كامل
        self.db_card = ctk.CTkFrame(
            self.sidebar_frame,
            fg_color=THEME["bg_card"],
            corner_radius=0,
            border_width=1,
            border_color=THEME["border"],
        )
        self.db_card.pack(side="bottom", fill="x")

        self.db_status_dot = ctk.CTkLabel(
            self.db_card,
            text="●",
            font=ctk.CTkFont(size=13),
            text_color=THEME["warning"],
            width=18,
        )
        self.db_status_dot.pack(side="right", padx=(4, 10), pady=8)

        self.db_status_label = ctk.CTkLabel(
            self.db_card,
            text="فحص قاعدة البيانات...",
            font=get_font(size=11),
            text_color=THEME["text_secondary"],
            anchor="e",
            justify="right",
            wraplength=225,
        )
        self.db_status_label.pack(side="right", fill="x", expand=True, padx=(8, 0), pady=8)

        ctk.CTkLabel(
            self.sidebar_frame,
            text="القائمة الرئيسية",
            font=get_font(size=11),
            text_color=THEME["text_muted"],
            anchor="e",
        ).pack(fill="x", padx=16, pady=(10, 4))

        all_menu_items = [
            ("dashboard", "🏠 لوحة التحكم المركزية", self.show_dashboard),
            ("patients", "👥 إدارة سجلات المرضى", self.show_patients_page),
            ("visits", "🩺 إدارة الجلسات العلاجية", self.show_patient_visit_page),
            ("appointments", "📅 إدارة المواعيد والمراجعات", self.show_appointments_page),
            ("staff_mgmt", "💼 إدارة الموظفين والسلف", self.show_staff_management_page),
            ("purchases", "📦 إدارة المشتريات والموردين", self.show_purchases_page),
            ("labs", "🔬 المعامل والتركيبات الطبية", self.show_labs_page),
            ("treasury", "💰 إدارة الخزينة اليومية", self.show_treasury_page),
            ("statements", "📑 كشوفات الحسابات والتقارير", self.show_statements_page),
            ("settings", "⚙️ الإعدادات العامة للنظام", self.show_settings_page),
        ]

        admin_only_keys = {"staff_mgmt", "purchases", "treasury", "statements", "settings"}
        menu_items = [
            (key, text, cmd)
            for key, text, cmd in all_menu_items
            if not (key in admin_only_keys and self.user_role != "admin")
        ]

        self.nav_container = ctk.CTkScrollableFrame(
            self.sidebar_frame,
            fg_color="transparent",
            scrollbar_button_color=THEME["bg_card_secondary"],
            scrollbar_button_hover_color=THEME["bg_card_hover"],
        )
        self.nav_container.pack(fill="both", expand=True, padx=8, pady=4)

        for key, text, cmd in menu_items:
            btn = ctk.CTkButton(
                self.nav_container,
                text=text,
                command=lambda k=key, c=cmd: self._on_tab_selected(k, c),
                font=get_font(size=13, weight="bold"),
                anchor="e",
                height=40,
                corner_radius=8,
                fg_color=THEME["nav_inactive_bg"],
                text_color=THEME["nav_inactive_fg"],
                hover_color=THEME["nav_hover_bg"],
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = btn

    def logout(self):
        """تسجيل الخروج والعودة لنافذة تسجيل الدخول"""
        self.destroy()

        def on_login_success(user_data):
            app = TayseerClinicApp(user_data)
            app.mainloop()

        login_win = LoginWindow(on_login_success)
        apply_window_icon(login_win)
        login_win.mainloop()

    def _set_active_tab_style(self, active_key):
        self.active_tab_key = active_key
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.configure(
                    fg_color=THEME["primary"],
                    text_color=THEME["text_light"],
                    font=get_font(size=13, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color=THEME["nav_inactive_bg"],
                    text_color=THEME["nav_inactive_fg"],
                    font=get_font(size=13, weight="normal"),
                )

    def _on_tab_selected(self, key, command):
        self._set_active_tab_style(key)
        command()

    def _build_main_shell(self):
        self.main_container = ctk.CTkFrame(self, fg_color=THEME["bg_app"])
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=14, pady=12)
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.header_card = ctk.CTkFrame(
            self.main_container,
            height=74,
            fg_color=THEME["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=THEME["border"],
        )
        self.header_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.header_card.grid_propagate(False)

        ctk.CTkFrame(self.header_card, width=5, fg_color=THEME["primary"], corner_radius=0).pack(side="right", fill="y")

        self.header_actions = ctk.CTkFrame(self.header_card, fg_color="transparent")
        self.header_actions.pack(side="left", padx=14, pady=12)

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        self.date_badge = ctk.CTkLabel(
            self.header_actions,
            text=f"📅  {today_str}",
            font=get_font(size=12, weight="bold"),
            text_color=THEME["teal"],
            fg_color=THEME["teal_soft"],
            corner_radius=8,
            padx=12,
            pady=5,
        )
        self.date_badge.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            self.header_actions,
            text="🔄 تحديث",
            font=get_font(size=12, weight="bold"),
            width=90,
            height=32,
            fg_color=THEME["bg_card_secondary"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_secondary"],
            border_width=1,
            border_color=THEME["border"],
            corner_radius=8,
            command=self._refresh_current_view,
        ).pack(side="left")

        self.header_title_frame = ctk.CTkFrame(self.header_card, fg_color="transparent")
        self.header_title_frame.pack(side="right", fill="x", expand=True, padx=(14, 12), pady=10)

        self.header_title = ctk.CTkLabel(
            self.header_title_frame,
            text="لوحة التحكم المركزية",
            font=get_font(size=17, weight="bold"),
            text_color=THEME["text_primary"],
            anchor="e",
            justify="right",
            wraplength=760,
        )
        self.header_title.pack(fill="x", anchor="e")

        self.header_subtitle = ctk.CTkLabel(
            self.header_title_frame,
            text="نظرة عامة على نشاطات العيادة وإحصائيات العمل اليومية",
            font=get_font(size=11),
            text_color=THEME["text_secondary"],
            anchor="e",
            justify="right",
            wraplength=760,
        )
        self.header_subtitle.pack(fill="x", anchor="e")

        self.content_container = ctk.CTkFrame(self.main_container, fg_color=THEME["bg_app"])
        self.content_container.grid(row=1, column=0, sticky="nsew")

    def _refresh_current_view(self):
        self._check_db_status()
        page_handlers = {
            "dashboard": self.show_dashboard,
            "patients": self.show_patients_page,
            "visits": self.show_patient_visit_page,
            "appointments": self.show_appointments_page,
            "staff_mgmt": self.show_staff_management_page,
            "purchases": self.show_purchases_page,
            "labs": self.show_labs_page,
            "treasury": self.show_treasury_page,
            "statements": self.show_statements_page,
            "settings": self.show_settings_page,
        }
        handler = page_handlers.get(self.active_tab_key)
        if handler:
            handler()

    def _clear_content(self):
        for widget in self.content_container.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self._set_active_tab_style("dashboard")
        self.header_title.configure(text="🏠 لوحة التحكم المركزية")
        self.header_subtitle.configure(text="نظرة شاملة ومباشرة على أداء ونشاط العيادة الطبي والمالي")
        self._clear_content()

        clinic_profile = load_clinic_profile()
        clinic_display_name = clinic_profile.get("name") or "عيادة تيسير لطب وجراحة الأسنان"

        cards_grid = ctk.CTkFrame(self.content_container, fg_color="transparent")
        cards_grid.pack(fill="x", pady=(0, 16))
        for col in range(4):
            cards_grid.columnconfigure(col, weight=1)

        patients_count = self.patients_repo.get_count()
        staff_count = self.staff_repo.get_count()

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        todays_apps = self.appointments_repo.get_todays_appointments(today_str)
        todays_apps_count = len(todays_apps) if todays_apps else 0

        treasury_balance = 0.0
        if self.user_role == "admin":
            _, _, summary = self.treasury_repo.get_daily_transactions()
            treasury_balance = summary.get("net_cash", 0.0)

        self._create_stat_card(cards_grid, col=3, icon="👥", title="ملفات المرضى المسجلين", value=f"{patients_count:,}", accent_color=THEME["success"], sub_text="سجل طبي نشط")
        self._create_stat_card(cards_grid, col=2, icon="📅", title="مواعيد اليوم", value=f"{todays_apps_count:,}", accent_color=THEME["teal"], sub_text="مراجعات وجلسات مسجلة")
        if self.user_role == "admin":
            self._create_stat_card(cards_grid, col=1, icon="💰", title="رصيد الخزينة اليومي", value=f"{treasury_balance:,.0f} ر.ي", accent_color=THEME["primary"], sub_text="صافي الصندوق الحالي")
        else:
            self._create_stat_card(cards_grid, col=1, icon="🩺", title="صلاحية الحساب", value=self.user_data.get("role", "مستخدم"), accent_color=THEME["primary"], sub_text="حساب طبي نشط")

        self._create_stat_card(cards_grid, col=0, icon="👨‍⚕️", title="طاقم العمل والأطباء", value=f"{staff_count:,}", accent_color=THEME["purple"], sub_text="الكوادر المعتمدة")

        body_grid = ctk.CTkFrame(self.content_container, fg_color="transparent")
        body_grid.pack(fill="both", expand=True)
        body_grid.columnconfigure(0, weight=3)
        body_grid.columnconfigure(1, weight=2)

        actions_panel = ctk.CTkFrame(body_grid, fg_color=THEME["bg_card"], corner_radius=14, border_width=1, border_color=THEME["border"])
        actions_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(actions_panel, text="⚡ إجراءات سريعة ومباشرة", font=get_font(size=16, weight="bold"), text_color=THEME["text_primary"]).pack(anchor="e", padx=16, pady=(16, 12))

        quick_btns = [
            ("👤 تسجيل مريض جديد", THEME["success"], self.show_patients_page),
            ("🩺 فتح جلسة وحساب مريض", THEME["primary"], self.show_patient_visit_page),
            ("📅 إدارة المواعيد وجدول اليوم", THEME["teal"], self.show_appointments_page),
        ]
        if self.user_role == "admin":
            quick_btns.extend([
                ("💼 إدارة السلف وصرف الرواتب", THEME["purple"], self.show_staff_management_page),
                ("📦 إدارة المشتريات والموردين", THEME["indigo"], self.show_purchases_page),
                ("💰 إدارة الخزينة والحركات اليومية", THEME["teal"], self.show_treasury_page),
                ("📑 مركز كشوفات الحسابات والتقارير", THEME["warning"], self.show_statements_page),
            ])

        for text, color, cmd in quick_btns:
            ctk.CTkButton(
                actions_panel,
                text=text,
                command=cmd,
                font=get_font(size=13, weight="bold"),
                anchor="e",
                height=40,
                corner_radius=8,
                fg_color=THEME["bg_card_secondary"],
                hover_color=color,
                text_color=THEME["text_primary"],
                border_width=1,
                border_color=THEME["border"],
            ).pack(fill="x", padx=16, pady=4)

        welcome_panel = ctk.CTkFrame(body_grid, fg_color=THEME["bg_card"], corner_radius=14, border_width=1, border_color=THEME["border"])
        welcome_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        welcome_banner = ctk.CTkFrame(
            welcome_panel,
            fg_color=THEME["bg_card_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border_light"],
        )
        welcome_banner.pack(fill="x", padx=14, pady=(14, 8))

        self.dash_logo = get_clinic_logo(variant="full", size=(80, 80))
        if self.dash_logo:
            ctk.CTkLabel(welcome_banner, text="", image=self.dash_logo).pack(side="left", padx=(14, 10), pady=10)

        banner_text = ctk.CTkFrame(welcome_banner, fg_color="transparent")
        banner_text.pack(side="right", fill="x", expand=True, padx=(10, 14), pady=10)

        ctk.CTkLabel(
            banner_text,
            text=f"🌟 أهلاً بك {self.user_data.get('full_name', 'دكتور')} في نظام عيادتي",
            font=get_font(size=16, weight="bold"),
            text_color=THEME["primary"],
            anchor="e",
        ).pack(fill="x", pady=(0, 2))

        ctk.CTkLabel(
            banner_text,
            text="نظام إدارة العيادة الطبي والمالي المتكامل — كفاءة وسرعة ودقة في متابعة المرضى",
            font=get_font(size=12),
            text_color=THEME["text_secondary"],
            anchor="e",
        ).pack(fill="x", pady=(0, 4))

        badge_row = ctk.CTkFrame(banner_text, fg_color="transparent")
        badge_row.pack(fill="x")

        ctk.CTkLabel(
            badge_row,
            text="🟢 النظام متصل وجاهز",
            font=get_font(size=11, weight="bold"),
            text_color=THEME["success"],
            fg_color=THEME["success_soft"],
            corner_radius=6,
            padx=8,
            pady=2,
        ).pack(side="right", padx=(0, 6))

        ctk.CTkLabel(
            badge_row,
            text=f"🏥 {clinic_display_name}",
            font=get_font(size=11),
            text_color=THEME["teal"],
            fg_color=THEME["teal_soft"],
            corner_radius=6,
            padx=8,
            pady=2,
        ).pack(side="right")

        features_box = ctk.CTkScrollableFrame(welcome_panel, fg_color="transparent")
        features_box.pack(fill="both", expand=True, padx=14, pady=(4, 10))

        tips = [
            ("📅 إدارة المواعيد الذكية:", "تم ربط تاريخ عودة المريض مباشرة من شاشة الجلسات العلاجية ليظهر تلقائياً في جدول مواعيد اليوم وإدارة المواعيد المستقلة."),
            ("💰 نظام الخزينة الموحد:", "تم ربط كافة حركات الوارد (المرضى) والصادر (المعامل والمشتريات والموظفين) لتظهر تلقائياً في شاشة الخزينة اليومية بدقة."),
        ]

        for title, desc in tips:
            item_card = ctk.CTkFrame(features_box, fg_color=THEME["bg_card_secondary"], corner_radius=10, border_width=1, border_color=THEME["border"])
            item_card.pack(fill="x", pady=6)
            ctk.CTkLabel(item_card, text=title, font=get_font(size=14, weight="bold"), text_color=THEME["primary"]).pack(anchor="e", padx=14, pady=(8, 2))
            ctk.CTkLabel(item_card, text=desc, font=get_font(size=13), text_color=THEME["text_secondary"], justify="right", wraplength=480).pack(anchor="e", padx=14, pady=(0, 8))

    def _create_stat_card(self, parent, col, icon, title, value, accent_color, sub_text):
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["bg_card"],
            corner_radius=12,
            height=120,
            border_width=1,
            border_color=THEME["border"],
        )
        card.grid(row=0, column=col, padx=6, sticky="ew")
        card.grid_propagate(False)

        ctk.CTkFrame(card, height=4, fg_color=accent_color, corner_radius=0).pack(fill="x")

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=12, pady=(10, 2))

        icon_bg_map = {
            THEME["success"]: THEME["success_soft"],
            THEME["teal"]: THEME["teal_soft"],
            THEME["primary"]: THEME["primary_soft"],
            THEME["purple"]: THEME["purple_soft"],
        }
        icon_bg = icon_bg_map.get(accent_color, THEME["bg_card_secondary"])
        icon_box = ctk.CTkFrame(top_row, width=36, height=36, corner_radius=8, fg_color=icon_bg)
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=ctk.CTkFont(size=16)).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(top_row, text=title, font=get_font(size=12, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right")
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"), text_color=THEME["text_primary"]).pack(anchor="e", padx=12, pady=(2, 0))
        ctk.CTkLabel(card, text=sub_text, font=get_font(size=11), text_color=accent_color).pack(anchor="e", padx=12, pady=(0, 6))

    def show_patients_page(self):
        self._set_active_tab_style("patients")
        self.header_title.configure(text="👥 إدارة وسجلات المرضى")
        self.header_subtitle.configure(text="تسجيل ملفات المرضى، تعديل البيانات، وتصفح الأرشيف الطبي الكامل")
        self._clear_content()
        self.patients_view = PatientsView(self.content_container, user_role=self.user_role)
        self.patients_view.pack(fill="both", expand=True)

    def show_patient_visit_page(self):
        self._set_active_tab_style("visits")
        self.header_title.configure(text="🩺 إدارة الجلسات العلاجية")
        self.header_subtitle.configure(text="تسجيل الجلسات، المعالجات الطبية، ومتابعة الفواتير ومواعيد العودة")
        self._clear_content()
        self.visit_view = PatientVisitView(self.content_container, user_role=self.user_role)
        self.visit_view.pack(fill="both", expand=True)

    def show_appointments_page(self):
        self._set_active_tab_style("appointments")
        self.header_title.configure(text="📅 إدارة المواعيد والمراجعات اليومية")
        self.header_subtitle.configure(text="متابعة مواعيد اليوم، إضافة مواعيد جديدة، وتحديث حالات المراجعات")
        self._clear_content()
        self.appointments_view = AppointmentsView(self.content_container, user_role=self.user_role)
        self.appointments_view.pack(fill="both", expand=True)

    def show_staff_management_page(self):
        if self.user_role != "admin":
            return
        self._set_active_tab_style("staff_mgmt")
        self.header_title.configure(text="💼 إدارة الموظفين وتسجيل السلف والرواتب")
        self.header_subtitle.configure(text="تسجيل سحب السلف، تسليم الرواتب، والمكافآت وترحيلها تلقائياً لكشوفات الحسابات")
        self._clear_content()
        self.staff_management_view = StaffManagementView(self.content_container)
        self.staff_management_view.pack(fill="both", expand=True)

    def show_purchases_page(self):
        if self.user_role != "admin":
            return
        self._set_active_tab_style("purchases")
        self.header_title.configure(text="📦 إدارة المشتريات والموردين")
        self.header_subtitle.configure(text="إدارة الموردين المتعاقد معهم، تسجيل المدفوعات وسندات الصرف، ومتابعة فواتير المشتريات نقد وأجل")
        self._clear_content()
        self.purchases_view = PurchasesView(self.content_container)
        self.purchases_view.pack(fill="both", expand=True)

    def show_labs_page(self):
        self._set_active_tab_style("labs")
        self.header_title.configure(text="🔬 المعامل والتركيبات الطبية")
        self.header_subtitle.configure(text="أوامر صناعة الأسنان، حسابات المعامل المتعاقدة، وكشوفات المدفوعات والذمم")
        self._clear_content()
        self.labs_view = LabsView(self.content_container, user_role=self.user_role)
        self.labs_view.pack(fill="both", expand=True)

    def show_treasury_page(self):
        if self.user_role != "admin":
            return
        self._set_active_tab_style("treasury")
        self.header_title.configure(text="💰 إدارة الخزينة والحركات اليومية")
        self.header_subtitle.configure(text="متابعة السيولة النقدية الواردة والصادرة لحظياً، وتأكيد الإغلاق اليومي للصندوق")
        self._clear_content()
        self.treasury_view = TreasuryView(self.content_container)
        self.treasury_view.pack(fill="both", expand=True)

    def show_statements_page(self):
        if self.user_role != "admin":
            return
        self._set_active_tab_style("statements")
        self.header_title.configure(text="📑 مركز كشوفات الحسابات والتقارير المالية")
        self.header_subtitle.configure(text="استخراج وتصدير كشوفات الحسابات التفصيلية للمرضى والمعامل والموظفين بصيغتي PDF و Excel")
        self._clear_content()
        self.statements_view = StatementsView(self.content_container)
        self.statements_view.pack(fill="both", expand=True)

    def show_settings_page(self):
        if self.user_role != "admin":
            return
        self._set_active_tab_style("settings")
        self.header_title.configure(text="⚙️ إعدادات النظام والتقارير")
        self.header_subtitle.configure(text="إدارة الموظفين والصلاحيات، التقارير الشاملة، والنسخ الاحتياطي")
        self._clear_content()
        self.settings_view = SettingsView(
            self.content_container,
            on_appearance_change=self._apply_appearance_live,
        )
        self.settings_view.pack(fill="both", expand=True)

    def _check_db_status(self):
        is_connected, info = self.db.check_health()
        if is_connected:
            self.db_status_dot.configure(text_color=THEME["success"])
            self.db_status_label.configure(text=f"متصل (MySQL {info})", text_color=THEME["success"])
        else:
            self.db_status_dot.configure(text_color=THEME["danger"])
            self.db_status_label.configure(text="خطأ في الاتصال بقاعدة البيانات!", text_color=THEME["danger"])


if __name__ == "__main__":
    def start_main_app(user_data):
        app = TayseerClinicApp(user_data)
        app.mainloop()

    login_app = LoginWindow(start_main_app)
    apply_window_icon(login_app)
    login_app.mainloop()
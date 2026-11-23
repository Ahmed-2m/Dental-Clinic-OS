import os
from PIL import Image
import customtkinter as ctk
from backend.auth_repo import AuthRepository
from ui.theme import THEME, get_font, setup_rtl_entry, get_clinic_logo


def _load_login_logo(size=(100, 100)):
    """تحميل شعار العيادة المعتمد بدقة عالية لواجهة تسجيل الدخول"""
    logo = get_clinic_logo(variant="full", size=size)
    if not logo:
        logo = get_clinic_logo(variant="emblem", size=size)
    return logo


class LoginWindow(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.auth_repo = AuthRepository()
        self.on_login_success = on_login_success  # دالة تستدعى عند نجاح الدخول لتسليم بيانات المستخدم والـ role

        self.title("تسجيل الدخول - نظام عيادتي | My Clinic")
        self.geometry("480x580")
        self.minsize(440, 540)
        self.resizable(True, True)
        self.configure(fg_color=THEME["bg_app"])

        # تطبيق أيقونة النافذة إن توفرت
        try:
            from main import apply_window_icon
            apply_window_icon(self)
        except Exception:
            pass

        # توسيط النافذة في منتصف الشاشة
        self.eval('tk::PlaceWindow . center')

        # إطار محتوى تسجيل الدخول
        card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=16, border_width=1, border_color=THEME["border"])
        card.pack(fill="both", expand=True, padx=25, pady=25)

        self.logo_img = _load_login_logo(size=(105, 105))
        if self.logo_img:
            ctk.CTkLabel(
                card,
                text="",
                image=self.logo_img,
                fg_color="transparent"
            ).pack(pady=(16, 2))
        else:
            ctk.CTkLabel(
                card,
                text="🦷",
                font=ctk.CTkFont(size=42),
                fg_color="transparent"
            ).pack(pady=(16, 2))

        ctk.CTkLabel(
            card, 
            text="🔐 تسجيل الدخول للنظام", 
            font=get_font(size=19, weight="bold"), 
            text_color=THEME["primary"]
        ).pack(pady=(2, 14))

        # حقل اسم المستخدم
        ctk.CTkLabel(
            card, 
            text="اسم المستخدم:", 
            font=get_font(size=14, weight="bold"), 
            text_color=THEME["text_secondary"]
        ).pack(anchor="e", padx=32, pady=(0, 6))

        self.entry_username = ctk.CTkEntry(
            card, 
            width=350, 
            height=44, 
            justify="right", 
            font=get_font(size=14),
            fg_color=THEME["bg_app"], 
            border_color=THEME["border"]
        )
        setup_rtl_entry(self.entry_username)
        self.entry_username.pack(padx=32, pady=(0, 16))

        # حقل كلمة المرور
        ctk.CTkLabel(
            card, 
            text="كلمة المرور:", 
            font=get_font(size=14, weight="bold"), 
            text_color=THEME["text_secondary"]
        ).pack(anchor="e", padx=32, pady=(0, 6))

        self.entry_password = ctk.CTkEntry(
            card, 
            width=350, 
            height=44, 
            justify="right", 
            show="*", 
            font=get_font(size=14),
            fg_color=THEME["bg_app"], 
            border_color=THEME["border"]
        )
        self.entry_password.pack(padx=32, pady=(0, 22))
        
        # ربط مفتاح Enter بزر الدخول مباشرة
        self.entry_username.bind("<Return>", lambda event: self.entry_password.focus_set())
        self.entry_password.bind("<Return>", lambda event: self.handle_login())

        # زر الدخول
        ctk.CTkButton(
            card, 
            text="دخول للنظام", 
            width=350, 
            height=46, 
            fg_color=THEME["primary"], 
            hover_color=THEME["primary_hover"], 
            font=get_font(size=16, weight="bold"), 
            command=self.handle_login
        ).pack(padx=32, pady=(0, 12))

        # رسالة الخطأ أو النجاح
        self.lbl_msg = ctk.CTkLabel(card, text="", font=get_font(size=13, weight="bold"))
        self.lbl_msg.pack(pady=(4, 10))

    def handle_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            self.lbl_msg.configure(text="الرجاء إدخال اسم المستخدم وكلمة المرور.", text_color=THEME["danger"])
            return

        success, msg, user_data = self.auth_repo.authenticate_user(username, password)
        if success:
            self.lbl_msg.configure(text=msg, text_color=THEME["success"])
            self.after(350, lambda: self.open_main_app(user_data))
        else:
            self.lbl_msg.configure(text=msg, text_color=THEME["danger"])

    def open_main_app(self, user_data):
        self.destroy()  # إغلاق نافذة تسجيل الدخول
        self.on_login_success(user_data)  # تمرير بيانات الموظف والصلاحية (role) للنافذة الرئيسية
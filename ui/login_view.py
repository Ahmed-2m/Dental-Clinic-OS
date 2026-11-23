import os
from PIL import Image
import customtkinter as ctk
from backend.auth_repo import AuthRepository
from ui.theme import THEME, get_font, setup_rtl_entry


def _load_login_logo(size=(76, 76)):
    base_dir = os.path.abspath(".")
    assets_dir = os.path.join(base_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    cache_path = os.path.join(assets_dir, "logo_emblem_transparent.png")

    candidate_imgs = [
        os.path.join(base_dir, "app_logo.png.jpg"),
        os.path.join(base_dir, "app_logo.jpg"),
        os.path.join(assets_dir, "app_logo.png.jpg"),
        os.path.join(assets_dir, "app_logo.jpg"),
    ]

    try:
        if not os.path.exists(cache_path):
            source_path = next((p for p in candidate_imgs if os.path.exists(p)), None)
            if not source_path:
                return None

            img = Image.open(source_path).convert("RGBA")
            w, h = img.size
            if h > 0 and (w / h) > 1.2:
                crop_box = (int(w * 0.36), int(h * 0.16), int(w * 0.64), int(h * 0.54))
                img = img.crop(crop_box)

            new_pixels = []
            for r, g, b, a in img.getdata():
                brightness = (r + g + b) / 3.0
                saturation = max(r, g, b) - min(r, g, b)
                if brightness >= 238 and saturation <= 18:
                    new_pixels.append((r, g, b, 0))
                elif brightness >= 210 and saturation <= 22:
                    alpha = int(max(0, min(255, (238 - brightness) * (255 / 28))))
                    new_pixels.append((r, g, b, alpha))
                else:
                    new_pixels.append((r, g, b, a))

            img.putdata(new_pixels)
            img.save(cache_path, format="PNG")

        pil_img = Image.open(cache_path).convert("RGBA")
        return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
    except Exception:
        return None


class LoginWindow(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.auth_repo = AuthRepository()
        self.on_login_success = on_login_success  # دالة تستدعى عند نجاح الدخول لتسليم بيانات المستخدم والـ role

        self.title("تسجيل الدخول - نظام عيادتي")
        self.geometry("480x540")
        self.minsize(440, 500)
        self.resizable(True, True)
        self.configure(fg_color=THEME["bg_app"])

        # توسيط النافذة في منتصف الشاشة
        self.eval('tk::PlaceWindow . center')

        # إطار محتوى تسجيل الدخول
        card = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=16, border_width=1, border_color=THEME["border"])
        card.pack(fill="both", expand=True, padx=25, pady=25)

        self.logo_img = _load_login_logo(size=(78, 78))
        if self.logo_img:
            ctk.CTkLabel(
                card,
                text="",
                image=self.logo_img,
                fg_color="transparent"
            ).pack(pady=(20, 6))

        ctk.CTkLabel(
            card, 
            text="🔐 تسجيل الدخول للنظام", 
            font=get_font(size=22, weight="bold"), 
            text_color=THEME["primary"]
        ).pack(pady=(4, 18))

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
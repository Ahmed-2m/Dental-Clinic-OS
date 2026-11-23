"""
نظام الثيم الداكن الاحترافي لعيادة تيسير لطب الأسنان
Dark Professional Medical Theme — Tayseer Dental Clinic OS
"""

import os
import unicodedata
from PIL import Image
import customtkinter as ctk

# =========================================================================
# لوحة الألوان الداكنة الطبية الاحترافية
# =========================================================================
THEME = {
    # خلفيات
    "bg_app":            "#0D1B2A",   # خلفية التطبيق الرئيسية (أزرق داكن عميق)
    "bg_sidebar":        "#091624",   # الشريط الجانبي (أعمق)
    "bg_header":         "#0D1B2A",
    "bg_card":           "#132338",   # البطاقات والأقسام
    "bg_card_secondary": "#1A2F4A",   # حقول الإدخال والبطاقات الثانوية
    "bg_card_hover":     "#1E3755",

    # الحدود
    "border":            "#1E3450",
    "border_light":      "#2A4A70",
    "border_focus":      "#38BDF8",

    # النصوص — كلها واضحة على الخلفيات الداكنة
    "text_primary":      "#F0F6FF",   # أبيض مائل للأزرق الفاتح
    "text_secondary":    "#93B4D4",   # أزرق رمادي فاتح
    "text_muted":        "#4A6A8A",   # خافت
    "text_light":        "#FFFFFF",

    # ألوان وظيفية
    "primary":           "#0EA5E9",   # أزرق سماوي طبي
    "primary_hover":     "#0284C7",
    "primary_soft":      "#0C3D5E",

    "teal":              "#14B8A6",   # تيل
    "teal_hover":        "#0D9488",
    "teal_soft":         "#0C3730",

    "success":           "#22C55E",   # أخضر
    "success_hover":     "#16A34A",
    "success_soft":      "#0A2E18",

    "warning":           "#F59E0B",   # برتقالي
    "warning_hover":     "#D97706",
    "warning_soft":      "#3D2200",

    "danger":            "#F43F5E",   # أحمر وردي
    "danger_hover":      "#E11D48",
    "danger_soft":       "#3D0A18",

    "purple":            "#A78BFA",   # بنفسجي
    "purple_hover":      "#7C3AED",
    "purple_soft":       "#2D1458",

    "indigo":            "#818CF8",   # نيلي
    "indigo_hover":      "#4F46E5",
    "indigo_soft":       "#1E1B4B",

    # التنقل
    "nav_active_bg":     "#0EA5E9",
    "nav_active_fg":     "#FFFFFF",
    "nav_inactive_bg":   "transparent",
    "nav_inactive_fg":   "#93B4D4",
    "nav_hover_bg":      "#1A2F4A",

    # التبويبات
    "tabview_bg":        "#0D1B2A",
    "tab_selected":      "#0EA5E9",
    "tab_unselected":    "#132338",
    "tab_hover":         "#1A2F4A",
}

# =========================================================================
# الخطوط
# =========================================================================
FONT_FAMILY = "Segoe UI"
FONT_ARABIC = "Segoe UI"


def get_font(size=14, weight="normal"):
    try:
        req_size = int(size)
    except Exception:
        req_size = 14

    if req_size <= 10:
        actual_size = 12
    elif req_size == 11:
        actual_size = 13
    elif req_size == 12:
        actual_size = 14
    elif req_size == 13:
        actual_size = 14
    elif req_size == 14:
        actual_size = 15
    elif req_size <= 16:
        actual_size = 16
    elif req_size <= 18:
        actual_size = 19
    elif req_size <= 20:
        actual_size = 21
    else:
        actual_size = req_size + 2

    try:
        return ctk.CTkFont(family=FONT_ARABIC, size=actual_size, weight=weight)
    except Exception:
        return ctk.CTkFont(family=FONT_FAMILY, size=actual_size, weight=weight)


def get_bold_font(size=14):
    return get_font(size=size, weight="bold")

def get_title_font(size=20):
    return get_font(size=size, weight="bold")

def get_heading_font(size=16):
    return get_font(size=size, weight="bold")


# =========================================================================
# معالجة النصوص العربية
# =========================================================================
def fix_arabic(text):
    if text is None:
        return ""
    text_str = str(text)
    if not text_str:
        return ""
    return unicodedata.normalize('NFKC', text_str)


def unfix_arabic(text):
    if text is None:
        return ""
    return unicodedata.normalize('NFKC', str(text))


# =========================================================================
# إصلاح عكس النص في CTkComboBox
# =========================================================================
def fix_combobox_rtl(combo):
    """
    إصلاح عكس النص العربي في CTkComboBox.
    تُستدعى بعد إنشاء أي ComboBox يحتوي نصوصاً عربية.
    """
    if combo is None:
        return combo
    try:
        combo.configure(justify="right")
    except Exception:
        pass
    if hasattr(combo, "_entry"):
        try:
            combo._entry.configure(justify="right")
        except Exception:
            pass
    return combo


# =========================================================================
# محرك حقول الإدخال RTL
# =========================================================================
def setup_rtl_entry(entry):
    if entry is None:
        return entry

    try:
        entry.configure(font=get_font(size=13, weight="normal"))
        if hasattr(entry, "cget") and entry.cget("height") < 36:
            entry.configure(height=36)
    except Exception:
        pass

    try:
        entry.configure(justify="right")
    except Exception:
        pass

    if hasattr(entry, "_entry"):
        try:
            entry._entry.configure(justify="right")
        except Exception:
            pass

    def on_focus(event=None):
        try:
            if hasattr(entry, "_entry"):
                entry._entry.configure(justify="right")
                val = entry.get()
                placeholder = getattr(entry, "_placeholder_text", "")
                if not val or val == placeholder:
                    entry._entry.after(10, lambda: entry._entry.icursor("end"))
                    entry._entry.after(10, lambda: entry._entry.xview_moveto(1.0))
        except Exception:
            pass

    for widget in (entry, getattr(entry, "_entry", None)):
        if widget is not None:
            widget.bind("<FocusIn>", on_focus, add="+")
            widget.bind("<Button-1>", lambda e: entry.after(10, on_focus), add="+")

    return entry


def setup_rtl_textbox(textbox):
    if textbox is None:
        return textbox
    try:
        textbox.configure(font=get_font(size=13, weight="normal"))
    except Exception:
        pass
    try:
        textbox.tag_config("rtl_right", justify="right")
        if hasattr(textbox, "_textbox"):
            textbox._textbox.tag_configure("rtl_right", justify="right")

        def apply_rtl_tag(event=None):
            try:
                textbox.tag_add("rtl_right", "1.0", "end")
            except Exception:
                pass

        for widget in (textbox, getattr(textbox, "_textbox", None)):
            if widget is not None:
                widget.bind("<KeyRelease>", apply_rtl_tag, add="+")
                widget.bind("<FocusIn>", apply_rtl_tag, add="+")
                widget.bind("<Button-1>", lambda e: textbox.after(10, apply_rtl_tag), add="+")
        apply_rtl_tag()
    except Exception:
        pass
    return textbox


# =========================================================================
# مساعدات بناء الواجهة
# =========================================================================
def create_card_frame(parent, **kwargs):
    params = {
        "fg_color": THEME["bg_card"],
        "corner_radius": 12,
        "border_width": 1,
        "border_color": THEME["border"],
    }
    params.update(kwargs)
    return ctk.CTkFrame(parent, **params)


def create_badge(parent, text, bg_color, fg_color="#FFFFFF", font_size=12):
    badge = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=10)
    lbl = ctk.CTkLabel(
        badge,
        text=fix_arabic(text),
        font=get_font(size=font_size, weight="bold"),
        text_color=fg_color,
    )
    lbl.pack(padx=10, pady=3)
    return badge


def create_section_header(parent, title, icon="", color=None):
    if color is None:
        color = THEME["primary"]
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(
        frame,
        text=f"{icon}  {title}" if icon else title,
        font=get_font(size=14, weight="bold"),
        text_color=color,
        anchor="e",
    ).pack(anchor="e")
    sep = ctk.CTkFrame(frame, height=2, fg_color=color, corner_radius=1)
    sep.pack(fill="x", pady=(4, 0))
    return frame


# =========================================================================
# ترقية عناصر customtkinter تلقائياً (Widget Patches)
# =========================================================================
_patches_applied = False


def _apply_widget_patches():
    global _patches_applied
    if _patches_applied:
        return
    _patches_applied = True

    # --- Buttons ---
    orig_button_init = ctk.CTkButton.__init__

    def patched_button_init(self, *args, **kwargs):
        if "font" not in kwargs or kwargs["font"] is None:
            kwargs["font"] = get_font(size=13, weight="bold")
        if "height" not in kwargs or kwargs.get("height", 0) < 34:
            kwargs["height"] = 36
        if "corner_radius" not in kwargs:
            kwargs["corner_radius"] = 8
        return orig_button_init(self, *args, **kwargs)

    ctk.CTkButton.__init__ = patched_button_init

    # --- Entries ---
    orig_entry_init = ctk.CTkEntry.__init__

    def patched_entry_init(self, *args, **kwargs):
        if "font" not in kwargs or kwargs["font"] is None:
            kwargs["font"] = get_font(size=13, weight="normal")
        if "height" not in kwargs or kwargs.get("height", 0) < 36:
            kwargs["height"] = 36
        if "justify" not in kwargs:
            kwargs["justify"] = "right"
        if "corner_radius" not in kwargs:
            kwargs["corner_radius"] = 8
        orig_entry_init(self, *args, **kwargs)
        setup_rtl_entry(self)

    ctk.CTkEntry.__init__ = patched_entry_init

    # --- ComboBox — إصلاح عكس النص العربي ---
    orig_combo_init = ctk.CTkComboBox.__init__

    def patched_combo_init(self, *args, **kwargs):
        if "font" not in kwargs or kwargs["font"] is None:
            kwargs["font"] = get_font(size=13, weight="normal")
        if "height" not in kwargs or kwargs.get("height", 0) < 36:
            kwargs["height"] = 36
        if "justify" not in kwargs:
            kwargs["justify"] = "right"
        if "corner_radius" not in kwargs:
            kwargs["corner_radius"] = 8
        orig_combo_init(self, *args, **kwargs)
        fix_combobox_rtl(self)

    ctk.CTkComboBox.__init__ = patched_combo_init


def apply_global_styles():
    """تطبيق النمط الداكن الاحترافي"""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    _apply_widget_patches()


# تطبيق فور الاستيراد
_apply_widget_patches()


# =========================================================================
# إدارة وتحميل شعار العيادة بدقة عالية وتوافق كامل
# =========================================================================
_CLINIC_LOGO_CACHE = {}


def get_clinic_logo(variant="emblem", size=(44, 44)):
    """
    تحميل شعار العيادة بدقة عالية وبشكل متناسق مع النمطين الداكن والفاتح.
    :param variant: 'emblem' (أيقونة السن بدون نصوص) أو 'full' (الشعار كاملاً مع النصوص)
    :param size: أبعاد الشعار العرض والارتفاع tuple (width, height)
    :return: كائن ctk.CTkImage أو None في حال عدم توفر الملف
    """
    base_dir = os.path.abspath(".")
    assets_dir = os.path.join(base_dir, "assets")
    cache_key = (variant, size)
    if cache_key in _CLINIC_LOGO_CACHE:
        return _CLINIC_LOGO_CACHE[cache_key]

    try:
        if variant == "emblem":
            dark_file = os.path.join(assets_dir, "logo_emblem_dark.png")
            light_file = os.path.join(assets_dir, "logo_emblem_transparent.png")
        else:
            dark_file = os.path.join(assets_dir, "logo_full_dark.png")
            light_file = os.path.join(assets_dir, "logo_full_transparent.png")

        if not os.path.exists(dark_file):
            dark_file = os.path.join(assets_dir, "logo_emblem_dark.png")
        if not os.path.exists(light_file):
            light_file = dark_file

        if not os.path.exists(dark_file):
            candidate = os.path.join(assets_dir, "app_logo.jpg")
            if os.path.exists(candidate):
                dark_file = candidate
                light_file = candidate
            else:
                return None

        pil_dark = Image.open(dark_file).convert("RGBA")
        pil_light = Image.open(light_file).convert("RGBA")

        ctk_img = ctk.CTkImage(light_image=pil_light, dark_image=pil_dark, size=size)
        _CLINIC_LOGO_CACHE[cache_key] = ctk_img
        return ctk_img
    except Exception as e:
        print(f"[تحذير عند تحميل شعار العيادة]: {e}")
        return None


import json
import os
import sys


DEFAULT_CLINIC_PROFILE = {
    "name": "عيادة تيسير لطب الأسنان",
    "phone": "770000000",
    "address": "صنعاء - اليمن",
    "logo": "",
    "appearance": "Dark",
}


def get_app_base_dir():
    """إرجاع مجلد التشغيل الأساسي (بجانب .exe عند التوزيع أو جذر المشروع أثناء التطوير)"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")


def get_clinic_profile_path():
    """مسار ملف بيانات العيادة والطباعة المستقل عن ملف اتصال قاعدة البيانات clinic_config.json"""
    return os.path.join(get_app_base_dir(), "clinic_profile.json")


def load_clinic_profile():
    """قراءة بيانات العيادة (الاسم، الهاتف، العنوان، الشعار) لترويسة الكشوفات والتقارير"""
    profile = DEFAULT_CLINIC_PROFILE.copy()
    path = get_clinic_profile_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                # دعم مفاتيح مباشرة أو داخل clinic إن وُجدت
                src = data.get("clinic") if isinstance(data.get("clinic"), dict) else data
                for key in ("name", "phone", "address", "logo", "appearance"):
                    if key in src and src[key] is not None:
                        profile[key] = str(src[key]).strip() if key != "appearance" else str(src[key])
        except Exception:
            pass
    return profile


def save_clinic_profile(name: str, phone: str, address: str, logo: str = ""):
    """حفظ تحديثات بيانات العيادة والشعار في clinic_profile.json دون لمس clinic_config.json"""
    profile = load_clinic_profile()
    profile.update({
        "name": (name or "").strip(),
        "phone": (phone or "").strip(),
        "address": (address or "").strip(),
        "logo": (logo or "").strip(),
    })
    path = get_clinic_profile_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=4)
    return profile


def resolve_report_logo_path(clinic_info: dict | None = None):
    """إيجاد مسار الشعار المعتمد للطباعة (المختار من الإعدادات أولاً ثم الاحتياطي)"""
    info = clinic_info or load_clinic_profile()
    candidates = []

    custom_logo = (info.get("logo") or "").strip()
    if custom_logo:
        candidates.append(custom_logo)
        if not os.path.isabs(custom_logo):
            candidates.append(os.path.join(get_app_base_dir(), custom_logo))

    base_dir = get_app_base_dir()
    candidates.extend([
        os.path.join(base_dir, "assets", "logo_emblem_transparent.png"),
        os.path.join(base_dir, "assets", "app_logo.jpg"),
        os.path.join(base_dir, "app_logo.jpg"),
    ])

    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None


def draw_pdf_clinic_logo(pdf, clinic_info: dict | None = None, x=15, y=8, w=19, h=19):
    """رسم شعار العيادة في ترويسة ملفات FPDF بأمان"""
    logo_path = resolve_report_logo_path(clinic_info)
    if not logo_path:
        return
    try:
        pdf.image(logo_path, x, y, w, h)
    except Exception:
        pass
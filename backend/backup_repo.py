import os
import subprocess
from datetime import datetime
from backend.database import Database

class BackupRepository:
    def __init__(self):
        self.db = Database.from_config_file()
        # إنشاء مجلد تلقائي للنسخ الاحتياطية داخل مشروع العيادة إن لم يكن موجوداً
        self.default_backup_dir = os.path.join(os.getcwd(), "database_backups")
        if not os.path.exists(self.default_backup_dir):
            os.makedirs(self.default_backup_dir)

    def create_automatic_backup(self):
        """أخذ نسخة احتياطية تلقائية وسريعة في مجلد النظام المحلي دون الحاجة لاختيار مجلد"""
        config = self.db.config
        db_user = config.get("user")
        db_password = config.get("password")
        db_name = config.get("database")
        db_host = config.get("host", "localhost")
        db_port = config.get("port", 3306)

        # تسمية الملف تلقائياً بالتاريخ والوقت لضمان عدم تداخل النسخ
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"tayseer_auto_backup_{timestamp}.sql"
        full_path = os.path.join(self.default_backup_dir, filename)

        cmd = [
            "mysqldump",
            f"-h{db_host}",
            f"-P{str(db_port)}",
            f"-u{db_user}",
            f"-p{db_password}",
            db_name
        ]

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                process = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, check=True)
            return True, f"تم حفظ النسخة التلقائية بنجاح في:\n{full_path}"
        except subprocess.CalledProcessError as e:
            return False, f"فشل النسخ التلقائي (تأكد من إعدادات mysqldump):\\n{e.stderr}"
        except Exception as e:
            return False, f"حدث خطأ: {str(e)}"
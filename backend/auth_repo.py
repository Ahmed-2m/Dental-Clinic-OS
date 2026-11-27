import hashlib
from backend.database import Database
from mysql.connector import Error

class AuthRepository:
    def __init__(self):
        self.db = Database.from_config_file()

    def _hash_password(self, password):
        """تشفير كلمة المرور المدخلة بـ SHA256 لمطابقتها مع المخزن في قاعدة البيانات"""
        if not password:
            return ""
        return hashlib.sha256(str(password).strip().encode('utf-8')).hexdigest()

    def authenticate_user(self, username, password):
        """التحقق من بيانات الدخول مباشرة من جدول الموظفين (employees)"""
        conn = self.db.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات.", None
        try:
            cursor = conn.cursor(dictionary=True)
            
            # تشفير كلمة المرور المدخلة لكي تتطابق مع القيمة المشفرة في password_hash
            hashed_password = self._hash_password(password)
            
            # إزالة شرط الstatus الصارم لضمان عدم رفض أي مستخدم صحيح
            query = """
                SELECT emp_id, full_name, username, role, status 
                FROM employees 
                WHERE username = %s AND password_hash = %s;
            """
            cursor.execute(query, (username.strip(), hashed_password))
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()

            if user:
                return True, "تم تسجيل الدخول بنجاح.", user
            else:
                return False, "اسم المستخدم أو كلمة المرور غير صحيحة.", None
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}", None
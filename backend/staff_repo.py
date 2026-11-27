import hashlib
from backend.database import Database
from mysql.connector import Error

class StaffRepository:
    def __init__(self):
        self.db = Database.from_config_file()

    def _hash_password(self, password):
        """تشفير كلمة المرور باستخدام SHA256 لضمان الأمان التام"""
        if not password:
            return ""
        return hashlib.sha256(str(password).strip().encode('utf-8')).hexdigest()

    def get_all(self):
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT emp_id, full_name, phone, address, job_title, salary, hire_date, username, role, status 
                FROM employees 
                ORDER BY emp_id DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"[خطأ]: {e}")
            return []

    def get_all_staff(self):
        """دالة متوافقة مع الواجهات لجلب كافة طاقم العمل"""
        return self.get_all()

    def get_all_doctors(self):
        """جلب الأطباء فقط بناءً على المسمى الوظيفي أو الصلاحية"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT emp_id, full_name, phone, address, job_title, salary, hire_date, username, role, status 
                FROM employees 
                WHERE job_title LIKE '%طبيب%' OR job_title LIKE '%دكتور%' OR role LIKE '%doctor%' OR job_title LIKE '%Doctor%'
                ORDER BY emp_id DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # إذا لم يوجد موظف مسجل بمسمى طبيب، جلب كافة الموظفين حتى لا تظهر القائمة فارغة
            if not rows:
                return self.get_all()
            return rows
        except Error as e:
            print(f"[خطأ في جلب الأطباء]: {e}")
            return self.get_all()

    def add(self, full_name, phone, address, job_title, salary, hire_date, username, password, role, status):
        """إضافة موظف جديد مع تشفير كلمة المرور تلقائياً قبل حفظها"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            
            # تشفير كلمة المرور قبل حفظها في قاعدة البيانات
            pwd_hash = self._hash_password(password)

            query = """
                INSERT INTO employees (full_name, phone, address, job_title, salary, hire_date, username, password_hash, role, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            values = (full_name, phone, address, job_title, salary or 0.0, hire_date or None, username, pwd_hash, role, status)
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم إضافة الموظف وتشفير كلمة المرور بنجاح"
        except Error as e:
            return False, f"خطأ: {e}"

    def update(self, emp_id, full_name, phone, address, job_title, salary, hire_date, username, password, role, status):
        """تعديل بيانات الموظف مع تحديث كلمة المرور فقط إذا تم إدخال كلمة جديدة"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            
            if password and str(password).strip() and password.strip() != "******":
                # إذا أدخل المستخدم كلمة مرور جديدة، نقوم بتشفيرها وتحديثها مع باقي البيانات
                pwd_hash = self._hash_password(password)
                query = """
                    UPDATE employees 
                    SET full_name = %s, phone = %s, address = %s, job_title = %s, salary = %s, 
                        hire_date = %s, username = %s, password_hash = %s, role = %s, status = %s 
                    WHERE emp_id = %s;
                """
                values = (full_name, phone, address, job_title, salary or 0.0, hire_date or None, username, pwd_hash, role, status, emp_id)
            else:
                # إذا لم يكتب كلمة مرور جديدة، نحدث باقي البيانات ونترك كلمة المرور القديمة كما هي
                query = """
                    UPDATE employees 
                    SET full_name = %s, phone = %s, address = %s, job_title = %s, salary = %s, 
                        hire_date = %s, username = %s, role = %s, status = %s 
                    WHERE emp_id = %s;
                """
                values = (full_name, phone, address, job_title, salary or 0.0, hire_date or None, username, role, status, emp_id)

            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم التحديث بنجاح"
        except Error as e:
            return False, f"خطأ: {e}"

    def update_password(self, emp_id, new_password):
        """تحديث وتشفير كلمة المرور للموظف عند الحاجة"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            pwd_hash = self._hash_password(new_password)
            query = "UPDATE employees SET password_hash = %s WHERE emp_id = %s;"
            cursor.execute(query, (pwd_hash, emp_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تحديث وتشفير كلمة المرور بنجاح"
        except Error as e:
            return False, f"خطأ: {e}"

    def delete(self, emp_id):
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM employees WHERE emp_id = %s;", (emp_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم الحذف بنجاح"
        except Error as e:
            return False, f"خطأ: {e}"

    def get_count(self):
        conn = self.db.get_number() if hasattr(self.db, 'get_number') else self.db.get_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM employees;")
            res = cursor.fetchone()
            count = res[0] if res else 0
            cursor.close()
            conn.close()
            return count
        except Error:
            return 0
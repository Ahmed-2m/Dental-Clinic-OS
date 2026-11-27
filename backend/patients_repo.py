from backend.database import Database
from mysql.connector import Error

class PatientsRepository:
    def __init__(self):
        self.db = Database.from_config_file()

    def get_all(self):
        """جلب قائمة جميع المرضى"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT patient_id, full_name, phone, address, gender, date_of_birth, medical_history FROM patients ORDER BY patient_id DESC;")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"[خطأ في جلب المرضى]: {e}")
            return []

    def get_all_patients(self):
        """دالة متوافقة تماماً مع الواجهات لجلب كافة المرضى"""
        return self.get_all()

    def add(self, full_name, phone, address, gender, dob, medical_history):
        """إضافة مريض جديد"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO patients (full_name, phone, address, gender, date_of_birth, medical_history) 
                VALUES (%s, %s, %s, %s, %s, %s);
            """
            db_gender = 'male' if gender == 'ذكر' else 'female'
            values = (full_name, phone, address, db_gender, dob if dob else None, medical_history)
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم إضافة المريض بنجاح"
        except Error as e:
            return False, f"خطأ أثناء الإدخال: {e}"

    def update(self, patient_id, full_name, phone, address, gender, dob, medical_history):
        """تعديل بيانات مريض"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                UPDATE patients 
                SET full_name = %s, phone = %s, address = %s, gender = %s, date_of_birth = %s, medical_history = %s 
                WHERE patient_id = %s;
            """
            db_gender = 'male' if gender == 'ذكر' else 'female'
            values = (full_name, phone, address, db_gender, dob if dob else None, medical_history, patient_id)
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تحديث بيانات المريض بنجاح"
        except Error as e:
            return False, f"خطأ أثناء التعديل: {e}"

    def delete(self, patient_id):
        """حذف مريض"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM patients WHERE patient_id = %s;", (patient_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم حذف المريض بنجاح"
        except Error as e:
            return False, f"خطأ أثناء الحذف: {e}"

    def get_count(self):
        """إجمالي عدد المرضى (للإحصائيات)"""
        conn = self.db.get_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM patients;")
            res = cursor.fetchone()
            count = res[0] if res else 0
            cursor.close()
            conn.close()
            return count
        except Error:
            return 0
from backend.database import Database
from mysql.connector import Error

class TreatmentsRepository:
    def __init__(self):
        self.db = Database.from_config_file()

    def add_treatment(self, patient_id, emp_id, treatment_type, description, cost, treatment_date, notes):
        """إضافة جلسة علاجية جديدة مع حساب رقم الجلسة الخاص بالمريض الحالي حصرياً وبشكل مستقل"""
        conn = self.db.get_connection()
        if not conn:
            return None, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            
            # حساب عدد جلسات هذا المريض المحدد فقط (وليس كل الجدول) وإضافة 1
            cursor.execute("SELECT COUNT(*) FROM treatments WHERE patient_id = %s", (patient_id,))
            result = cursor.fetchone()
            next_session_num = (result[0] if result and result[0] is not None else 0) + 1

            query = """
                INSERT INTO treatments 
                (patient_id, emp_id, treatment_type, description, cost, treatment_date, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (patient_id, emp_id, treatment_type, description, cost, treatment_date, notes))
            conn.commit()
            treatment_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return treatment_id, f"تم تسجيل جلسة المريض رقم {next_session_num} بنجاح"
        except Error as e:
            return None, f"خطأ في قاعدة البيانات: {e}"

    def get_treatments_by_patient(self, patient_id):
        """جلب كافة جلسات وعلاجات مريض معين مرتبة"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT treatment_id, emp_id, treatment_type, description, cost, treatment_date, notes
                FROM treatments
                WHERE patient_id = %s
                ORDER BY treatment_id ASC;
            """
            cursor.execute(query, (patient_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"[خطأ في جلب جلسات المريض]: {e}")
            return []
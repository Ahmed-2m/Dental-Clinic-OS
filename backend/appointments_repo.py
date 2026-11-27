import datetime
from backend.database import Database
from mysql.connector import Error

class AppointmentsRepository:
    def __init__(self):
        self.db = Database.from_config_file()

    def get_todays_appointments(self, target_date=None):
        """جلب مواعيد يوم معين (افتراضياً اليوم الحالي) لتحديث لوحة إدارة المواعيد"""
        if not target_date:
            target_date = datetime.date.today().strftime("%Y-%m-%d")
            
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT a.appointment_id, a.patient_id, p.full_name, p.phone, 
                       a.appointment_date, a.appointment_time, a.status, a.notes
                FROM appointments a
                LEFT JOIN patients p ON a.patient_id = p.patient_id
                WHERE a.appointment_date = %s
                ORDER BY a.appointment_time ASC;
            """
            cursor.execute(query, (target_date,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"[خطأ في جلب مواعيد اليوم]: {e}")
            return []

    def add_appointment(self, patient_id, appointment_date, appointment_time="10:00:00", notes=""):
        """إضافة موعد (تاريخ العودة) جديد للمريض"""
        conn = self.db.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات."
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO appointments (patient_id, appointment_date, appointment_time, status, notes)
                VALUES (%s, %s, %s, 'معلق', %s);
            """
            cursor.execute(query, (patient_id, appointment_date, appointment_time, notes))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تسجيل موعد العودة بنجاح."
        except Error as e:
            return False, f"فشل تسجيل الموعد: {e}"

    def update_appointment_status(self, appointment_id, status):
        """تعديل حالة الموعد (متم، ملغي، معلق)"""
        conn = self.db.get_connection()
        if not conn:
            return False, "تعذر الاتصال بقاعدة البيانات."
        try:
            cursor = conn.cursor()
            query = "UPDATE appointments SET status = %s WHERE appointment_id = %s;"
            cursor.execute(query, (status, appointment_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تحديث حالة الموعد."
        except Error as e:
            return False, f"فشل التحديث: {e}"
from backend.database import Database
from mysql.connector import Error

class LabsRepository:
    def __init__(self):
        self.db = Database()

    def add_lab(self, lab_name, address, phone):
        """إضافة معمل جديد"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO labs (lab_name, address, phone)
                VALUES (%s, %s, %s);
            """
            cursor.execute(query, (lab_name, address, phone))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تسجيل المعمل بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def get_all_labs(self):
        """جلب كافة المعامل المسجلة"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = "SELECT lab_id, lab_name, address, phone FROM labs ORDER BY lab_id DESC;"
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error:
            return []

    def update_lab(self, lab_id, lab_name, address, phone):
        """تعديل بيانات معمل"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                UPDATE labs 
                SET lab_name = %s, address = %s, phone = %s 
                WHERE lab_id = %s;
            """
            cursor.execute(query, (lab_name, address, phone, lab_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تحديث بيانات المعمل بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def delete_lab(self, lab_id):
        """حذف معمل"""
        conn = self.db.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM labs WHERE lab_id = %s;", (lab_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error:
            return False
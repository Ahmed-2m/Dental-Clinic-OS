from backend.database import Database
from mysql.connector import Error

class SuppliersRepository:
    def __init__(self):
        self.db = Database()

    def add_supplier(self, supplier_name, address, phone, notes):
        """إضافة مورد جديد"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO suppliers (supplier_name, address, phone, notes)
                VALUES (%s, %s, %s, %s);
            """
            cursor.execute(query, (supplier_name, address, phone, notes))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تسجيل المورد بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def get_all_suppliers(self):
        """جلب كافة الموردين المسجلين"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = "SELECT supplier_id, supplier_name, address, phone, notes FROM suppliers ORDER BY supplier_id DESC;"
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error:
            return []

    def update_supplier(self, supplier_id, supplier_name, address, phone, notes):
        """تعديل بيانات مورد"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                UPDATE suppliers 
                SET supplier_name = %s, address = %s, phone = %s, notes = %s 
                WHERE supplier_id = %s;
            """
            cursor.execute(query, (supplier_name, address, phone, notes, supplier_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تحديث بيانات المورد بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def delete_supplier(self, supplier_id):
        """حذف مورد"""
        conn = self.db.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM suppliers WHERE supplier_id = %s;", (supplier_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error:
            return False
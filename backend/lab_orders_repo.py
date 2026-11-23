from backend.database import Database
from mysql.connector import Error

class LabOrdersRepository:
    def __init__(self):
        self.db = Database()

    def add_order(self, lab_id, patient_id, emp_id, work_type, total_cost, receive_date, delivery_date, notes, invoice_id=None):
        """إضافة أمر معمل/تركيبة جديد مع التأكد من حفظ الفاتورة والملاحظات بدقة"""
        conn = self.db.get_connection()
        if not conn:
            print("❌ خطأ: فشل الاتصال بقاعدة البيانات أثناء إضافة أمر المعمل")
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO lab_orders (lab_id, patient_id, emp_id, work_type, total_cost, receive_date, delivery_date, notes, invoice_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (lab_id, patient_id, emp_id, work_type, total_cost, receive_date, delivery_date, notes, invoice_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تسجيل أمر المعمل بنجاح"
        except Error as e:
            print(f"❌ خطأ SQL أثناء إضافة أمر المعمل: {e}")
            return False, f"خطأ في قاعدة البيانات: {e}"

    def get_orders_by_date_range(self, start_date, end_date):
        """جلب أوامر المعامل خلال فترة زمنية محددة مع جلب رقم الفاتورة والملاحظات بدقة"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT o.order_id, o.lab_id, COALESCE(l.lab_name, 'معمل غير معروف'), 
                       o.patient_id, COALESCE(p.full_name, 'مريض غير معروف'), 
                       o.emp_id, COALESCE(e.full_name, 'طبيب غير معروف'), 
                       o.work_type, o.total_cost, o.receive_date, o.delivery_date, o.notes, o.invoice_id 
                FROM lab_orders o
                LEFT JOIN labs l ON o.lab_id = l.lab_id
                LEFT JOIN patients p ON o.patient_id = p.patient_id
                LEFT JOIN employees e ON o.emp_id = e.emp_id
                WHERE o.receive_date BETWEEN %s AND %s
                ORDER BY o.receive_date DESC, o.order_id DESC;
            """
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"❌ خطأ SQL أثناء جلب أوامر المعامل: {e}")
            return []

    def update_order(self, order_id, work_type, cost, notes):
        """تعديل بيانات أمر التركيبة أو المعمل"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                UPDATE lab_orders 
                SET work_type = %s, total_cost = %s, notes = %s 
                WHERE order_id = %s;
            """
            cursor.execute(query, (work_type, cost, notes, order_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تحديث أمر المعمل بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def delete_order(self, order_id):
        """حذف أمر معمل"""
        conn = self.db.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM lab_orders WHERE order_id = %s;", (order_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            print(f"❌ خطأ SQL أثناء الحذف: {e}")
            return False
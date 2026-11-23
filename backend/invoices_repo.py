from backend.database import Database
from mysql.connector import Error

class InvoicesRepository:
    def __init__(self):
        self.db = Database()

    def add_invoice(self, patient_id, treatment_id, total_amount, paid_amount, remaining_amount, payment_date, payment_status, payment_method):
        """إضافة فاتورة جديدة أو حركة مالية للمريض"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO invoices (patient_id, treatment_id, total_amount, paid_amount, remaining_amount, payment_date, payment_status, payment_method)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (patient_id, treatment_id, total_amount, paid_amount, remaining_amount, payment_date, payment_status, payment_method))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تسجيل الفاتورة بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def get_invoices_by_date_range(self, start_date, end_date):
        """جلب الفواتير خلال فترة زمنية محددة مع اسم المريض"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT i.invoice_id, i.patient_id, p.full_name as patient_name, i.treatment_id, 
                       i.total_amount, i.paid_amount, i.remaining_amount, i.payment_date, i.payment_status, i.payment_method 
                FROM invoices i
                LEFT JOIN patients p ON i.patient_id = p.patient_id
                WHERE i.payment_date BETWEEN %s AND %s
                ORDER BY i.payment_date DESC, i.invoice_id DESC;
            """
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error:
            return []

    def delete_invoice(self, invoice_id):
        """حذف فاتورة"""
        conn = self.db.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invoices WHERE invoice_id = %s;", (invoice_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error:
            return False
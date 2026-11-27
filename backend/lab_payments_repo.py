from backend.database import Database
from mysql.connector import Error

class LabPaymentsRepository:
    def __init__(self):
        self.db = Database.from_config_file()

    def add_payment(self, lab_id, amount_paid, payment_method, payment_date, notes, receipt_no=None):
        """تسجيل دفعة مالية جديدة للمعمل مع رقم السند"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO lab_payments (lab_id, amount_paid, payment_method, payment_date, notes, receipt_no)
                VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (lab_id, amount_paid, payment_method, payment_date, notes, receipt_no))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تسجيل دفعة المعمل بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def get_payments_by_date_range(self, start_date, end_date):
        """جلب مدفوعات المعامل خلال فترة زمنية محددة مع رقم السند واسم المعمل"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT p.payment_id, p.lab_id, l.lab_name, p.amount_paid, p.payment_method, p.payment_date, p.notes, p.receipt_no 
                FROM lab_payments p
                LEFT JOIN labs l ON p.lab_id = l.lab_id
                WHERE p.payment_date BETWEEN %s AND %s
                ORDER BY p.payment_date DESC, p.payment_id DESC;
            """
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error:
            return []

    def get_labs_financial_summary(self):
        """إرجاع كشف الحساب المالي لكل معمل"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    l.lab_id,
                    l.lab_name,
                    COALESCE(o.total_orders_cost, 0) AS total_cost,
                    COALESCE(p.total_paid_amount, 0) AS total_paid,
                    (COALESCE(o.total_orders_cost, 0) - COALESCE(p.total_paid_amount, 0)) AS remaining_balance
                FROM labs l
                LEFT JOIN (
                    SELECT lab_id, SUM(total_cost) AS total_orders_cost 
                    FROM lab_orders 
                    GROUP BY lab_id
                ) o ON l.lab_id = o.lab_id
                LEFT JOIN (
                    SELECT lab_id, SUM(amount_paid) AS total_paid_amount 
                    FROM lab_payments 
                    GROUP BY lab_id
                ) p ON l.lab_id = p.lab_id;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            print(f"❌ خطأ SQL أثناء جلب ملخص حسابات المعامل: {e}")
            return []

    def update_payment(self, payment_id, amount_paid, receipt_no=None):
        """تعديل قيمة الدفعة المالية ورقم السند للمعمل"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                UPDATE lab_payments 
                SET amount_paid = %s, receipt_no = %s 
                WHERE payment_id = %s;
            """
            cursor.execute(query, (amount_paid, receipt_no, payment_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تحديث الدفعة المالية بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def delete_payment(self, payment_id):
        """حذف حركة دفع للمعمل"""
        conn = self.db.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM lab_payments WHERE payment_id = %s;", (payment_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            print(f"❌ خطأ SQL أثناء حذف الدفعة: {e}")
            return False
    
    def get_payments_by_lab_id(self, lab_id):
        """جلب مدفوعات معمل معين فقط"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT p.payment_id, p.lab_id, l.lab_name, p.amount_paid, p.payment_method, p.payment_date, p.notes, p.receipt_no 
                FROM lab_payments p
                LEFT JOIN labs l ON p.lab_id = l.lab_id
                WHERE p.lab_id = %s
                ORDER BY p.payment_date DESC, p.payment_id DESC;
            """
            cursor.execute(query, (lab_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error:
            return []
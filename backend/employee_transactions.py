from backend.database import Database
from mysql.connector import Error

class EmployeeTransactionsRepository:
    def __init__(self):
        self.db = Database()

    def add_transaction(self, emp_id, transaction_type, amount, transaction_date, description):
        """إضافة معاملة مالية جديدة للموظف (راتب، سلفة، مكافأة...)"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO employee_transactions (emp_id, transaction_type, amount, transaction_date, description)
                VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(query, (emp_id, transaction_type, amount, transaction_date, description))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تسجيل معاملة الموظف بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def get_transactions_by_date_range(self, start_date, end_date):
        """جلب معاملات الموظفين خلال فترة زمنية محددة مع اسم الموظف"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT t.transaction_id, t.emp_id, e.full_name, t.transaction_type, t.amount, t.transaction_date, t.description 
                FROM employee_transactions t
                LEFT JOIN employees e ON t.emp_id = e.emp_id
                WHERE t.transaction_date BETWEEN %s AND %s
                ORDER BY t.transaction_date DESC, t.transaction_id DESC;
            """
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error:
            return []

    def delete_transaction(self, transaction_id):
        """حذف معاملة مالية للموظف"""
        conn = self.db.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM employee_transactions WHERE transaction_id = %s;", (transaction_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error:
            return False
from backend.database import Database
from mysql.connector import Error

class ExpensesRepository:
    def __init__(self):
        self.db = Database()

    def add_expense(self, expense_category, amount, expense_date, emp_id, notes):
        """إضافة مصروف جديد إلى جدول expenses"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO expenses (expense_category, amount, expense_date, emp_id, notes)
                VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(query, (expense_category, amount, expense_date, emp_id or None, notes))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تسجيل المصروف بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def get_expenses_by_date_range(self, start_date, end_date):
        """جلب المصروفات خلال فترة زمنية محددة"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT expense_id, expense_category, amount, expense_date, emp_id, notes 
                FROM expenses 
                WHERE expense_date BETWEEN %s AND %s
                ORDER BY expense_date DESC, expense_id DESC;
            """
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error:
            return []

    def delete_expense(self, expense_id):
        """حذف مصروف"""
        conn = self.db.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE expense_id = %s;", (expense_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error:
            return False
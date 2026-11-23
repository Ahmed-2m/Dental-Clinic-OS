from backend.database import Database
from mysql.connector import Error

class DailyCashRepository:
    def __init__(self):
        self.db = Database()

    def add_cash_entry(self, transaction_type, amount, reference_id, description, emp_id, transaction_date):
        """إضافة حركة نقدية جديدة إلى جدول daily_cash"""
        conn = self.db.get_connection()
        if not conn:
            return False, "فشل الاتصال بقاعدة البيانات"
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO daily_cash (transaction_type, amount, reference_id, description, emp_id, transaction_date)
                VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (transaction_type, amount, reference_id, description, emp_id, transaction_date))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "تم تسجيل الحركة النقدية بنجاح"
        except Error as e:
            return False, f"خطأ في قاعدة البيانات: {e}"

    def get_cash_by_date_range(self, start_date, end_date):
        """جلب الحركات النقدية خلال فترة محددة للعرض في الخزينة والتقارير"""
        conn = self.db.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT cash_id, transaction_type, amount, reference_id, description, emp_id, transaction_date 
                FROM daily_cash 
                WHERE transaction_date BETWEEN %s AND %s
                ORDER BY transaction_date DESC, cash_id DESC;
            """
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error:
            return []

    def get_cash_summary(self, start_date, end_date):
        """حساب إجمالي المقبوضات والمدفوعات وصافي الخزينة"""
        conn = self.db.get_connection()
        if not conn:
            return {"in": 0.0, "out": 0.0, "net": 0.0}
        try:
            cursor = conn.cursor()
            query = """
                SELECT transaction_type, SUM(amount) 
                FROM daily_cash 
                WHERE transaction_date BETWEEN %s AND %s
                GROUP BY transaction_type;
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()
            cursor.close()
            conn.close()

            summary = {"in": 0.0, "out": 0.0}
            for t_type, total in results:
                # افترض أن الأنواع التي تزيد النقدية تسجل كمقبوضات (مثل income أو cash_in)
                # والتي تنقصها تسجل كمدفوعات (مثل expense أو cash_out أو salary)
                t_lower = str(t_type).lower()
                if "in" in t_lower or "income" in t_lower or "قبض" in t_lower:
                    summary["in"] += float(total or 0)
                else:
                    summary["out"] += float(total or 0)

            summary["net"] = summary["in"] - summary["out"]
            return summary
        except Error:
            return {"in": 0.0, "out": 0.0, "net": 0.0}

    def delete_cash_entry(self, cash_id):
        conn = self.db.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM daily_cash WHERE cash_id = %s;", (cash_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error:
            return False
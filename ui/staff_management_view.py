import datetime
from tkinter import filedialog
from tkcalendar import Calendar
import customtkinter as ctk
from backend.database import Database
from ui.theme import THEME, get_font
from mysql.connector import Error


class StaffManagementView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.db = Database.from_config_file()

        self.selected_emp_id = None
        self.editing_transaction_id = None  # لتتبع الحركة التي يتم تعديلها حالياً
        self.emp_map = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. العنوان العلوي
        header_frame = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=12)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header_frame,
            text="👥 إدارة الموظفين وتسجيل وتعديل السحب والسلف",
            font=get_font(size=16, weight="bold"),
            text_color=THEME["primary"],
        ).pack(side="right", padx=15, pady=12)

        # 2. المحتوى الرئيسي
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=10, pady=5)
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_columnconfigure(1, weight=1)

        # ----------------- القسم الأيمن (الإدخال والتسجيل أو التعديل) -----------------
        div_right = ctk.CTkFrame(main_content, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        div_right.pack(side="right", fill="both", expand=True, padx=(5, 5), pady=5)

        self.lbl_form_title = ctk.CTkLabel(div_right, text="🔍 اختيار الموظف وتسجيل حركة مالية جديدة", font=get_font(size=13, weight="bold"), text_color=THEME["text_primary"])
        self.lbl_form_title.pack(anchor="e", padx=15, pady=(12, 5))

        # اختيار الموظف
        f_emp = ctk.CTkFrame(div_right, fg_color="transparent")
        f_emp.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(f_emp, text="الموظف:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 10))
        self.combo_emp = ctk.CTkComboBox(f_emp, width=260, height=34, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"], command=self._on_employee_selected)
        self.combo_emp.pack(side="right", padx=(0, 10))
        ctk.CTkButton(
            f_emp,
            text="🔄",
            width=35,
            height=32,
            fg_color=THEME["bg_app"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            border_width=1,
            border_color=THEME["border"],
            command=self.load_employees_list,
        ).pack(side="right")

        # نوع الحركة
        f_type = ctk.CTkFrame(div_right, fg_color="transparent")
        f_type.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(f_type, text="نوع الحركة:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 10))

        self.trans_types = ["سلفة", "تسليم راتب", "مكافأة", "خصم", "سحب عهدة"]
        self.combo_type = ctk.CTkComboBox(f_type, values=self.trans_types, width=260, height=34, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.combo_type.pack(side="right", padx=(0, 10))
        self.combo_type.set("سلفة")

        # المبلغ
        f_amt = ctk.CTkFrame(div_right, fg_color="transparent")
        f_amt.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(f_amt, text="المبلغ (ر.ي):", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 10))
        self.entry_amount = ctk.CTkEntry(f_amt, width=260, height=34, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.entry_amount.pack(side="right", padx=(0, 10))

        # التاريخ
        f_date = ctk.CTkFrame(div_right, fg_color="transparent")
        f_date.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(f_date, text="تاريخ الحركة:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 10))

        self.entry_date = ctk.CTkEntry(f_date, width=210, height=34, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.entry_date.pack(side="right", padx=(0, 6))
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        self.entry_date.insert(0, today_str)

        ctk.CTkButton(
            f_date,
            text="📅",
            width=40,
            height=34,
            fg_color=THEME["bg_app"],
            hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_primary"],
            border_width=1,
            border_color=THEME["border"],
            command=lambda: self.open_calendar_popup(self.entry_date),
        ).pack(side="right")

        # البيان / السبب
        f_desc = ctk.CTkFrame(div_right, fg_color="transparent")
        f_desc.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(f_desc, text="سبب السحب / البيان:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 10))
        self.entry_desc = ctk.CTkEntry(f_desc, width=260, height=34, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.entry_desc.pack(side="right", padx=(0, 10))

        # أزرار الحفظ وتحديث وإلغاء الوضع
        f_btn = ctk.CTkFrame(div_right, fg_color="transparent")
        f_btn.pack(fill="x", padx=15, pady=15)

        self.btn_save = ctk.CTkButton(
            f_btn,
            text="💾 تسجيل وترحيل العملية المالية",
            width=180,
            height=40,
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            text_color=THEME["text_light"],
            font=get_font(size=12, weight="bold"),
            command=self.save_employee_transaction,
        )
        self.btn_save.pack(side="right", padx=5)

        self.btn_cancel_edit = ctk.CTkButton(
            f_btn,
            text="❌ إلغاء التعديل",
            width=90,
            height=40,
            fg_color=THEME["bg_card_secondary"],
            hover_color=THEME["danger"],
            text_color=THEME["text_primary"],
            font=get_font(size=11),
            command=self.reset_form_to_add_mode,
        )
        # يبدأ مخفياً لحين الضغط على تعديل
        self.btn_cancel_edit.pack_forget()

        self.status_lbl = ctk.CTkLabel(div_right, text="", font=get_font(size=11))
        self.status_lbl.pack(pady=5)

        # ----------------- القسم الأيسر (تفاصيل وسجل الموظف مع أزرار تعديل وحذف) -----------------
        div_left = ctk.CTkFrame(main_content, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        div_left.pack(side="left", fill="both", expand=True, padx=(5, 5), pady=5)

        ctk.CTkLabel(div_left, text="📋 ملخص بيانات الموظف وسجل حركاته الأخيرة", font=get_font(size=13, weight="bold"), text_color=THEME["primary"]).pack(anchor="e", padx=15, pady=(12, 5))

        self.info_frame = ctk.CTkFrame(div_left, fg_color=THEME["bg_card_secondary"], corner_radius=8)
        self.info_frame.pack(fill="x", padx=15, pady=5)
        self.lbl_emp_details = ctk.CTkLabel(self.info_frame, text="يرجى اختيار موظف لعرض التفاصيل", font=get_font(size=11), text_color=THEME["text_secondary"])
        self.lbl_emp_details.pack(padx=10, pady=10, anchor="e")

        ctk.CTkLabel(div_left, text="سجل الحركات السابقة", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(anchor="e", padx=15, pady=(10, 2))

        self.history_scroll = ctk.CTkScrollableFrame(div_left, fg_color="transparent", height=180)
        self.history_scroll.pack(fill="both", expand=True, padx=15, pady=5)

        self.load_employees_list()

    def open_calendar_popup(self, target_entry):
        top = ctk.CTkToplevel(self)
        top.title("اختيار التاريخ")
        top.geometry("320x300")
        top.attributes("-topmost", True)
        top.resizable(False, False)
        top.configure(fg_color=THEME["bg_card"])

        today = datetime.date.today()
        cal = Calendar(top, selectmode="day", year=today.year, month=today.month, day=today.day)
        cal.pack(pady=15, padx=15, fill="both", expand=True)

        def set_date():
            selected_date = cal.get_date()
            try:
                parsed_date = datetime.datetime.strptime(selected_date, "%m/%d/%y").strftime("%Y-%m-%d")
            except Exception:
                try:
                    parsed_date = datetime.datetime.strptime(selected_date, "%Y-%m-%d").strftime("%Y-%m-%d")
                except Exception:
                    parsed_date = selected_date

            target_entry.delete(0, "end")
            target_entry.insert(0, parsed_date)
            top.destroy()

        ctk.CTkButton(
            top,
            text="تأكيد التاريخ",
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_light"],
            height=32,
            command=set_date,
        ).pack(pady=(0, 15), padx=15, fill="x")

    def load_employees_list(self):
        conn = self.db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT emp_id, full_name, phone, salary FROM employees ORDER BY emp_id DESC;")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            self.emp_map.clear()
            values = []
            for r in rows:
                emp_id, name, phone, salary = r
                txt = f"#{emp_id} - {name} ({phone}) [راتب أساسي: {float(salary or 0):,.0f}]"
                self.emp_map[txt] = {
                    "emp_id": emp_id,
                    "name": name,
                    "phone": phone,
                    "salary": float(salary or 0),
                }
                values.append(txt)

            if values:
                self.combo_emp.configure(values=values)
                self.combo_emp.set(values[0])
                self._on_employee_selected(values[0])
            else:
                self.combo_emp.configure(values=["لا توجد موظفين مسجلين"])
                self.combo_emp.set("لا توجد موظفين مسجلين")
                self.selected_emp_id = None
        except Error as e:
            print(f"[خطأ في تحميل الموظفين لإدارة الموظفين]: {e}")

    def _on_employee_selected(self, choice):
        if choice in self.emp_map:
            emp_data = self.emp_map[choice]
            self.selected_emp_id = emp_data["emp_id"]
            details_text = f"👤 الاسم: {emp_data['name']}\n📱 الهاتف: {emp_data['phone']}\n💰 الراتب الأساسي: {emp_data['salary']:,.2f} ر.ي"
            self.lbl_emp_details.configure(text=details_text, text_color=THEME["text_primary"])
            self.reset_form_to_add_mode()
            self.load_employee_history(self.selected_emp_id)

    def load_employee_history(self, emp_id):
        for w in self.history_scroll.winfo_children():
            w.destroy()

        conn = self.db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT transaction_id, transaction_type, amount, transaction_date, description
                FROM employee_transactions
                WHERE emp_id = %s
                ORDER BY transaction_date DESC, transaction_id DESC
                LIMIT 15;
            """, (emp_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            if rows:
                for r in rows:
                    t_id, t_type, amount, t_date, desc = r
                    card = ctk.CTkFrame(self.history_scroll, fg_color=THEME["bg_card_secondary"], corner_radius=6)
                    card.pack(fill="x", pady=3)

                    # محتوى سطر الحركة
                    row_f = ctk.CTkFrame(card, fg_color="transparent")
                    row_f.pack(fill="x", padx=10, pady=6)

                    # أزرار التعديل والحذف على اليسار
                    btn_del = ctk.CTkButton(
                        row_f,
                        text="🗑️ حذف",
                        width=55,
                        height=26,
                        fg_color=THEME["danger"],
                        hover_color=THEME["danger_hover"],
                        text_color=THEME["text_light"],
                        font=get_font(size=10),
                        command=lambda tid=t_id: confirm_delete_transaction(tid),
                    )
                    btn_del.pack(side="left", padx=4)

                    btn_edit = ctk.CTkButton(
                        row_f,
                        text="✏️ تعديل",
                        width=55,
                        height=26,
                        fg_color=THEME["primary"],
                        hover_color=THEME["primary_hover"],
                        text_color=THEME["text_light"],
                        font=get_font(size=10),
                        command=lambda tid=t_id, tt=t_type, amt=amount, dt=str(t_date), dsc=desc: start_edit_transaction(tid, tt, amt, dt, dsc),
                    )
                    btn_edit.pack(side="left", padx=4)

                    # تفاصيل الحركة على اليمين
                    txt = f"🆔 #{t_id} | {t_type}: {float(amount):,.2f} ر.ي | التاريخ: {t_date} | البيان: {desc or 'بدون'}"
                    ctk.CTkLabel(row_f, text=txt, font=get_font(size=10), text_color=THEME["text_primary"]).pack(side="right")
            else:
                ctk.CTkLabel(self.history_scroll, text="لا توجد حركات مالية مسجلة لهذا الموظف.", font=get_font(size=10), text_color=THEME["text_muted"]).pack(pady=20)
        except Error as e:
            print(f"[خطأ في جلب سجل الموظف]: {e}")

        def start_edit_transaction(tid, tt, amt, dt, dsc):
            """وضع الواجهة في وضع التعديل للحركة المحددة"""
            self.editing_transaction_id = tid
            self.lbl_form_title.configure(text=f"✏️ تعديل الحركة المالية رقم #{tid}", text_color=THEME["warning"])

            self.combo_type.set(tt)
            self.entry_amount.delete(0, "end")
            self.entry_amount.insert(0, str(amt))

            self.entry_date.delete(0, "end")
            self.entry_date.insert(0, dt)

            self.entry_desc.delete(0, "end")
            self.entry_desc.insert(0, dsc if dsc else "")

            self.btn_save.configure(text="💾 حفظ التعديلات", fg_color=THEME["warning"], hover_color=THEME["warning_hover"])
            self.btn_cancel_edit.pack(side="right", padx=5)

        def confirm_delete_transaction(tid):
            """حذف الحركة المالية بعد التأكيد"""
            top_del = ctk.CTkToplevel(self)
            top_del.title("تأكيد الحذف")
            top_del.geometry("300x150")
            top_del.attributes("-topmost", True)
            top_del.resizable(False, False)
            top_del.configure(fg_color=THEME["bg_card"])

            ctk.CTkLabel(top_del, text=f"هل أنت متأكد من حذف الحركة #{tid}؟", font=get_font(size=12, weight="bold"), text_color=THEME["danger"]).pack(pady=20)

            def do_delete():
                conn_d = self.db.get_connection()
                if conn_d:
                    try:
                        cur_d = conn_d.cursor()
                        cur_d.execute("DELETE FROM employee_transactions WHERE transaction_id = %s;", (tid,))
                        conn_d.commit()
                        cur_d.close()
                        conn_d.close()
                        self.status_lbl.configure(text=f"🗑️ تم حذف الحركة #{tid} بنجاح!", text_color=THEME["success"])
                        self.load_employee_history(self.selected_emp_id)
                    except Error as ex:
                        self.status_lbl.configure(text=f"❌ خطأ بالحذف: {ex}", text_color=THEME["danger"])
                top_del.destroy()

            f_btns = ctk.CTkFrame(top_del, fg_color="transparent")
            f_btns.pack(fill="x", padx=20)
            ctk.CTkButton(
                f_btns,
                text="تأكيد الحذف",
                fg_color=THEME["danger"],
                hover_color=THEME["danger_hover"],
                text_color=THEME["text_light"],
                width=110,
                command=do_delete,
            ).pack(side="right", padx=5)
            ctk.CTkButton(
                f_btns,
                text="إلغاء",
                fg_color=THEME["bg_card_secondary"],
                hover_color=THEME["bg_card_hover"],
                text_color=THEME["text_primary"],
                width=110,
                command=top_del.destroy,
            ).pack(side="left", padx=5)

    def reset_form_to_add_mode(self):
        """إعادة الحقول لوضع الإضافة الجديدة"""
        self.editing_transaction_id = None
        self.lbl_form_title.configure(text="🔍 اختيار الموظف وتسجيل حركة مالية جديدة", text_color=THEME["text_primary"])
        self.combo_type.set("سلفة")
        self.entry_amount.delete(0, "end")
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.entry_desc.delete(0, "end")
        self.btn_save.configure(text="💾 تسجيل وترحيل العملية المالية", fg_color=THEME["success"], hover_color=THEME["success_hover"])
        self.btn_cancel_edit.pack_forget()

    def save_employee_transaction(self):
        if not self.selected_emp_id:
            self.status_lbl.configure(text="❌ يرجى اختيار موظف أولاً.", text_color=THEME["danger"])
            return

        amt_str = self.entry_amount.get().strip()
        if not amt_str:
            self.status_lbl.configure(text="❌ يرجى إدخال المبلغ.", text_color=THEME["danger"])
            return

        try:
            amount = float(amt_str)
        except ValueError:
            self.status_lbl.configure(text="❌ يرجى إدخال مبلغ صحيح بالأرقام.", text_color=THEME["danger"])
            return

        trans_date = self.entry_date.get().strip()
        if not trans_date:
            self.status_lbl.configure(text="❌ يرجى تحديد تاريخ الحركة.", text_color=THEME["danger"])
            return

        trans_type = self.combo_type.get()
        description = self.entry_desc.get().strip() or trans_type

        conn = self.db.get_connection()
        if not conn:
            self.status_lbl.configure(text="❌ تعذر الاتصال بقاعدة البيانات.", text_color=THEME["danger"])
            return

        try:
            cursor = conn.cursor()
            if self.editing_transaction_id:
                query = """
                    UPDATE employee_transactions 
                    SET transaction_type = %s, amount = %s, transaction_date = %s, description = %s
                    WHERE transaction_id = %s;
                """
                cursor.execute(query, (trans_type, amount, trans_date, description, self.editing_transaction_id))
                msg = "✅ تم تحديث الحركة المالية بنجاح!"
            else:
                query = """
                    INSERT INTO employee_transactions (emp_id, transaction_type, amount, transaction_date, description)
                    VALUES (%s, %s, %s, %s, %s);
                """
                cursor.execute(query, (self.selected_emp_id, trans_type, amount, trans_date, description))
                msg = "✅ تم تسجيل وترحيل الحركة المالية بنجاح!"

            conn.commit()
            cursor.close()
            conn.close()

            self.status_lbl.configure(text=msg, text_color=THEME["success"])
            self.reset_form_to_add_mode()
            self.load_employee_history(self.selected_emp_id)
        except Error as e:
            self.status_lbl.configure(text=f"❌ خطأ أثناء الحفظ: {e}", text_color=THEME["danger"])
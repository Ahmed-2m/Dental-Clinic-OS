import datetime
import customtkinter as ctk
from tkinter import messagebox

from backend.labs_repo import LabsRepository
from backend.lab_orders_repo import LabOrdersRepository
from backend.lab_payments_repo import LabPaymentsRepository
from backend.patients_repo import PatientsRepository
from backend.staff_repo import StaffRepository

from ui.theme import THEME, get_font, setup_rtl_entry

class LabsView(ctk.CTkFrame):
    def __init__(self, parent, user_role="admin"):
        super().__init__(parent, fg_color="transparent")
        self.user_role = str(user_role).lower()
        
        self.labs_repo = LabsRepository()
        self.orders_repo = LabOrdersRepository()
        self.payments_repo = LabPaymentsRepository()
        self.patients_repo = PatientsRepository()
        self.staff_repo = StaffRepository()

        self.tabview = ctk.CTkTabview(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=14,
            segmented_button_selected_color=THEME["primary"],
            segmented_button_selected_hover_color=THEME["primary_hover"],
            segmented_button_unselected_color=THEME["bg_card_secondary"],
            segmented_button_unselected_hover_color=THEME["bg_card_hover"],
            text_color=THEME["text_light"]
        )
        self.tabview.pack(fill="both", expand=True)

        self.tab_labs = self.tabview.add("🏢 المعامل المسجلة")
        self.tab_payments = self.tabview.add("💵 مدفوعات المعامل")
        self.tab_orders = self.tabview.add("📋 أوامر التركيبات والعمل")

        self.tabview.set("📋 أوامر التركيبات والعمل")

        self._build_orders_tab()
        self._build_payments_tab()
        self._build_labs_tab()

    # =========================================================================
    # 1. تبويب أوامر التركيبات والعمل
    # =========================================================================
    def _build_orders_tab(self):
        container = self.tab_orders

        form_frame = ctk.CTkFrame(
            container, 
            fg_color=THEME["bg_card_secondary"], 
            corner_radius=12, 
            border_width=1, 
            border_color=THEME["border_light"]
        )
        form_frame.pack(fill="x", padx=12, pady=(10, 8))

        ctk.CTkLabel(
            form_frame, 
            text="➕ تسجيل أمر تركيبات وعمل جديد", 
            font=get_font(size=14, weight="bold"), 
            text_color=THEME["primary"]
        ).pack(anchor="e", padx=16, pady=(10, 6))

        labs_list = self.labs_repo.get_all_labs()
        patients_list = self.patients_repo.get_all_patients()
        staff_list = self.staff_repo.get_all_doctors()

        lab_names = [l[1] for l in labs_list] if labs_list else ["لا توجد معامل مسجلة"]
        patient_names = [p[1] for p in patients_list] if patients_list else ["لا يوجد مرضى مسجلون"]
        staff_names = [s[1] for s in staff_list] if staff_list else ["لا يوجد أطباء مسجلون"]

        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(row1, text="المعمل:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        cb_lab = ctk.CTkComboBox(row1, values=lab_names, width=170, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        cb_lab.pack(side="right", padx=(0, 16))
        if labs_list: cb_lab.set(lab_names[0])

        ctk.CTkLabel(row1, text="المريض:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        cb_patient = ctk.CTkComboBox(row1, values=patient_names, width=180, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        cb_patient.pack(side="right", padx=(0, 16))
        if patients_list: cb_patient.set(patient_names[0])

        ctk.CTkLabel(row1, text="الطبيب:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        cb_staff = ctk.CTkComboBox(row1, values=staff_names, width=170, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        cb_staff.pack(side="right", padx=(0, 10))
        if staff_list: cb_staff.set(staff_names[0])

        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(row2, text="نوع العمل:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        e_work = ctk.CTkEntry(row2, placeholder_text="مثال: زركون / إيماكس / جسر", width=190, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_work)
        e_work.pack(side="right", padx=(0, 12))

        ctk.CTkLabel(row2, text="التكلفة (ر.ي):", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        e_cost = ctk.CTkEntry(row2, placeholder_text="0.00", width=95, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_cost)
        e_cost.pack(side="right", padx=(0, 12))

        ctk.CTkLabel(row2, text="رقم الفاتورة:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        e_invoice = ctk.CTkEntry(row2, placeholder_text="رقم الفاتورة", width=95, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_invoice)
        e_invoice.pack(side="right", padx=(0, 12))

        today_str = datetime.date.today().strftime("%Y-%m-%d")

        ctk.CTkLabel(row2, text="تاريخ الإرسال:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        e_receive = ctk.CTkEntry(row2, width=90, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_receive)
        e_receive.pack(side="right", padx=(0, 12))
        e_receive.insert(0, today_str)

        ctk.CTkLabel(row2, text="الاستلام:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        e_delivery = ctk.CTkEntry(row2, width=90, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_delivery)
        e_delivery.pack(side="right", padx=(0, 4))
        e_delivery.insert(0, today_str)

        row3 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row3.pack(fill="x", padx=14, pady=(6, 12))

        save_btn = ctk.CTkButton(
            row3, 
            text="💾 حفظ أمر التركيبة", 
            fg_color=THEME["primary"], 
            hover_color=THEME["primary_hover"], 
            width=150, 
            height=34, 
            font=get_font(size=12, weight="bold")
        )
        save_btn.pack(side="left", padx=(0, 10))

        e_notes = ctk.CTkEntry(row3, placeholder_text="ملاحظات تفصيلية حول أمر العمل ومواصفات القياسات واللون...", justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_notes)
        e_notes.pack(side="right", fill="x", expand=True)

        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=6)

        def load_orders():
            for w in scroll.winfo_children():
                w.destroy()
            orders = self.orders_repo.get_orders_by_date_range("2020-01-01", "2035-12-31")
            if orders:
                for o in orders:
                    card = ctk.CTkFrame(scroll, fg_color=THEME["bg_card_secondary"], corner_radius=10, border_width=1, border_color=THEME["border"])
                    card.pack(fill="x", pady=4)

                    inv_text = f" | الفاتورة: #{o[12]}" if len(o) > 12 and o[12] else ""
                    notes_text = f" | ملاحظات: {o[11]}" if len(o) > 11 and o[11] else ""
                    
                    header_txt = f"🔬 أمر تشغيل #{o[0]} | المعمل: {o[2]} | المريض: {o[4]} | الطبيب: {o[6]}"
                    body_txt = f"🦷 العمل: {o[7]} | 💰 التكلفة: {o[8]:,.2f} ر.ي{inv_text} | 📅 الإرسال: {o[9]} - الاستلام: {o[10]}{notes_text}"

                    ctk.CTkLabel(card, text=header_txt, font=get_font(size=12, weight="bold"), text_color=THEME["teal"]).pack(anchor="e", padx=14, pady=(8, 2))
                    ctk.CTkLabel(card, text=body_txt, font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e", padx=14, pady=(0, 2))

                    act_row = ctk.CTkFrame(card, fg_color="transparent")
                    act_row.pack(fill="x", padx=14, pady=(2, 8))

                    ctk.CTkButton(
                        act_row, text="✏️ تعديل", width=80, height=26,
                        font=get_font(size=10), fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                        command=lambda order_item=o: self._edit_order_dialog(order_item)
                    ).pack(side="left", padx=2)

                    if self.user_role == "admin":
                        ctk.CTkButton(
                            act_row, text="🗑️ حذف", width=80, height=26,
                            font=get_font(size=10), fg_color=THEME["danger_soft"], hover_color=THEME["danger"],
                            command=lambda order_id=o[0]: self._delete_order(order_id)
                        ).pack(side="left", padx=2)
            else:
                ctk.CTkLabel(scroll, text="لا توجد أوامر معامل مسجلة حالياً.", font=get_font(size=12), text_color=THEME["text_muted"]).pack(pady=25)

        def save_order():
            try:
                selected_lab_name = cb_lab.get()
                selected_patient_name = cb_patient.get()
                selected_staff_name = cb_staff.get()

                lab_id = next((l[0] for l in labs_list if l[1] == selected_lab_name), None)
                patient_id = next((p[0] for p in patients_list if p[1] == selected_patient_name), None)
                emp_id = next((s[0] for s in staff_list if s[1] == selected_staff_name), None)

                if not lab_id or not patient_id:
                    return

                work_type = e_work.get().strip()
                cost = float(e_cost.get().strip() or 0)
                invoice_id = e_invoice.get().strip()
                invoice_val = int(invoice_id) if invoice_id.isdigit() else None
                receive_date = e_receive.get().strip()
                delivery_date = e_delivery.get().strip()
                notes = e_notes.get().strip()

                success, msg = self.orders_repo.add_order(lab_id, patient_id, emp_id, work_type, cost, receive_date, delivery_date, notes, invoice_val)
                if success:
                    e_work.delete(0, "end")
                    e_cost.delete(0, "end")
                    e_invoice.delete(0, "end")
                    e_notes.delete(0, "end")
                    load_orders()
            except Exception as ex:
                print(f"Error saving order: {ex}")

        save_btn.configure(command=save_order)
        load_orders()

    def _edit_order_dialog(self, order_obj):
        order_id = order_obj[0]
        top = ctk.CTkToplevel(self)
        top.title(f"تعديل أمر العمل #{order_id}")
        top.geometry("400x340")
        top.resizable(False, False)
        top.grab_set()

        ctk.CTkLabel(top, text=f"✏️ تعديل أمر العمل #{order_id}", font=get_font(size=14, weight="bold"), text_color=THEME["warning"]).pack(pady=15)

        form = ctk.CTkFrame(top, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20)

        ctk.CTkLabel(form, text="نوع العمل:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e")
        e_w = ctk.CTkEntry(form, width=360, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        e_w.pack(anchor="e", pady=(0, 6))
        e_w.insert(0, order_obj[7] or "")

        ctk.CTkLabel(form, text="التكلفة (ر.ي):", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e")
        e_c = ctk.CTkEntry(form, width=360, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        e_c.pack(anchor="e", pady=(0, 6))
        e_c.insert(0, str(order_obj[8] or 0))

        ctk.CTkLabel(form, text="رقم الفاتورة:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e")
        e_inv = ctk.CTkEntry(form, width=360, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        e_inv.pack(anchor="e", pady=(0, 6))
        e_inv.insert(0, str(order_obj[12] or "") if len(order_obj) > 12 else "")

        ctk.CTkLabel(form, text="ملاحظات:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e")
        e_n = ctk.CTkEntry(form, width=360, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        e_n.pack(anchor="e", pady=(0, 12))
        e_n.insert(0, order_obj[11] or "")

        def save_edits():
            try:
                new_cost = float(e_c.get().strip() or 0)
                inv_val = int(e_inv.get().strip()) if e_inv.get().strip().isdigit() else None
                conn = self.orders_repo.db.get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE lab_orders SET work_type = %s, total_cost = %s, invoice_id = %s, notes = %s WHERE order_id = %s;", (e_w.get().strip(), new_cost, inv_val, e_n.get().strip(), order_id))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    top.destroy()
                    self._build_orders_tab()
            except Exception as ex:
                print(f"Error: {ex}")

        ctk.CTkButton(top, text="💾 حفظ التعديلات", width=150, height=34, fg_color=THEME["warning"], hover_color="darkorange", font=get_font(size=12, weight="bold"), command=save_edits).pack(pady=10)

    def _delete_order(self, order_id):
        if self.user_role != "admin":
            return
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف أمر العمل هذا؟"):
            self.orders_repo.delete_order(order_id)
            self._build_orders_tab()

    # =========================================================================
    # 2. تبويب مدفوعات المعامل (مع كشف المديونية الفوري وعرض دفعات المعمل المحدد)
    # =========================================================================
    def _build_payments_tab(self):
        container = self.tab_payments
        for w in container.winfo_children():
            w.destroy()

        search_card = ctk.CTkFrame(
            container, 
            fg_color=THEME["bg_card_secondary"], 
            corner_radius=12, 
            border_width=1, 
            border_color=THEME["border_light"]
        )
        search_card.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            search_card, 
            text="🔍 اختر المعمل المطلوب لمعرفة رصيده وسداد دفعاته", 
            font=get_font(size=14, weight="bold"), 
            text_color=THEME["teal"]
        ).pack(anchor="e", padx=16, pady=(10, 4))

        labs_list = self.labs_repo.get_all_labs()
        lab_names = [l[1] for l in labs_list] if labs_list else ["لا توجد معامل مسجلة"]

        select_row = ctk.CTkFrame(search_card, fg_color="transparent")
        select_row.pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkLabel(select_row, text="اختر المعمل:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        cb_select_lab = ctk.CTkComboBox(select_row, values=lab_names, width=280, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        cb_select_lab.pack(side="right", padx=(0, 16))
        if labs_list: cb_select_lab.set(lab_names[0])

        # بطاقة عرض الرصيد المتبقي على العيادة للمعمل المحدد
        balance_card = ctk.CTkFrame(search_card, fg_color=THEME["bg_card"], corner_radius=10, border_width=1, border_color=THEME["border"])
        balance_card.pack(fill="x", padx=14, pady=(0, 12))

        lbl_balance_info = ctk.CTkLabel(
            balance_card, 
            text="📊 إجمالي طلبات المعمل: 0 ر.ي | المدفوع: 0 ر.ي | المتبقي على العيادة: 0 ر.ي", 
            font=get_font(size=12, weight="bold"), 
            text_color=THEME["warning"]
        )
        lbl_balance_info.pack(anchor="e", padx=16, pady=8)

        form_frame = ctk.CTkFrame(
            container, 
            fg_color=THEME["bg_card_secondary"], 
            corner_radius=12, 
            border_width=1, 
            border_color=THEME["border_light"]
        )
        form_frame.pack(fill="x", padx=12, pady=(4, 8))

        ctk.CTkLabel(
            form_frame, 
            text="💵 تسجيل سند وسداد دفعة مالية للمعمل المحدد", 
            font=get_font(size=14, weight="bold"), 
            text_color=THEME["success"]
        ).pack(anchor="e", padx=16, pady=(10, 6))

        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(row1, text="رقم السند:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        e_receipt = ctk.CTkEntry(row1, placeholder_text="رقم سند الصرف", width=120, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_receipt)
        e_receipt.pack(side="right", padx=(0, 16))

        ctk.CTkLabel(row1, text="المبلغ المدفوع (ر.ي):", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        e_amount = ctk.CTkEntry(row1, placeholder_text="0.00", width=120, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_amount)
        e_amount.pack(side="right", padx=(0, 16))

        payment_methods = ["نقداً", "تحويل بنكي", "شيك"]
        ctk.CTkLabel(row1, text="طريقة الدفع:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        cb_method = ctk.CTkComboBox(row1, values=payment_methods, width=110, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        cb_method.pack(side="right", padx=(0, 16))
        cb_method.set("نقداً")

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        ctk.CTkLabel(row1, text="التاريخ:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        e_date = ctk.CTkEntry(row1, width=100, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_date)
        e_date.pack(side="right", padx=(0, 4))
        e_date.insert(0, today_str)

        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(6, 12))

        save_p_btn = ctk.CTkButton(
            row2, 
            text="💾 تأكيد وحفظ الدفعة", 
            fg_color=THEME["success"], 
            hover_color=THEME["success_hover"], 
            width=160, 
            height=34, 
            font=get_font(size=12, weight="bold")
        )
        save_p_btn.pack(side="left", padx=(0, 10))

        e_notes = ctk.CTkEntry(row2, placeholder_text="ملاحظات إضافية حول السداد...", justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_notes)
        e_notes.pack(side="right", fill="x", expand=True)

        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=6)

        def update_lab_financial_info(lab_id):
            """جلب وعرض الحساب المالي للمعمل المحدد لتوضيح المبلغ المتبقي على العيادة"""
            summaries = self.payments_repo.get_labs_financial_summary()
            target_summary = next((s for s in summaries if s[0] == lab_id), None)
            if target_summary:
                # target_summary = (lab_id, lab_name, total_cost, total_paid, remaining_balance)
                total_c = float(target_summary[2] or 0)
                total_p = float(target_summary[3] or 0)
                remaining = float(target_summary[4] or 0)
                lbl_balance_info.configure(
                    text=f"📊 إجمالي تكلفة طلبات المعمل: {total_c:,.2f} ر.ي  |  المدفوع: {total_p:,.2f} ر.ي  |  المتبقي على العيادة: {remaining:,.2f} ر.ي"
                )
            else:
                lbl_balance_info.configure(text="📊 إجمالي طلبات المعمل: 0 ر.ي | المدفوع: 0 ر.ي | المتبقي على العيادة: 0 ر.ي")

        def load_payments(event=None):
            for w in scroll.winfo_children():
                w.destroy()
            
            selected_lab_name = cb_select_lab.get()
            selected_lab = next((l for l in labs_list if l[1] == selected_lab_name), None)
            
            if not selected_lab:
                ctk.CTkLabel(scroll, text="يرجى اختيار المعمل.", font=get_font(size=12), text_color=THEME["text_muted"]).pack(pady=25)
                return

            lab_id = selected_lab[0]
            
            # تحديث ملخص الحساب المالي للمعمل المختار
            update_lab_financial_info(lab_id)

            # جلب دفعات هذا المعمل المحدد فقط
            payments = self.payments_repo.get_payments_by_lab_id(lab_id)

            if payments:
                for p in payments:
                    card = ctk.CTkFrame(scroll, fg_color=THEME["bg_card_secondary"], corner_radius=10, border_width=1, border_color=THEME["border"])
                    card.pack(fill="x", pady=4)
                    
                    receipt_str = f" | السند: #{p[7]}" if len(p) > 7 and p[7] else ""
                    txt = f"💵 دفعة #{p[0]}{receipt_str} | المعمل: {p[2]} | المبلغ: {float(p[3] or 0):,.2f} ر.ي | الطريقة: {p[4]} | التاريخ: {p[5]}"
                    ctk.CTkLabel(card, text=txt, font=get_font(size=12), text_color=THEME["text_primary"]).pack(anchor="e", padx=15, pady=(8, 2))

                    act_row = ctk.CTkFrame(card, fg_color="transparent")
                    act_row.pack(fill="x", padx=14, pady=(2, 8))

                    ctk.CTkButton(
                        act_row, text="✏️ تعديل", width=80, height=26,
                        font=get_font(size=10), fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                        command=lambda pay_item=p: self._edit_payment_dialog(pay_item)
                    ).pack(side="left", padx=2)

                    if self.user_role == "admin":
                        ctk.CTkButton(
                            act_row, text="🗑️ حذف", width=80, height=26,
                            font=get_font(size=10), fg_color=THEME["danger_soft"], hover_color=THEME["danger"],
                            command=lambda pay_id=p[0]: self._delete_payment(pay_id)
                        ).pack(side="left", padx=2)
            else:
                ctk.CTkLabel(scroll, text=f"لا توجد مدفوعات مسجلة للمعمل ({selected_lab_name}) حالياً.", font=get_font(size=12), text_color=THEME["text_muted"]).pack(pady=25)

        # ربط حدث تغير اختيار المعمل في القائمة لتحديث السجل والرصيد فوراً
        cb_select_lab.configure(command=load_payments)

        def save_payment():
            try:
                selected_lab_name = cb_select_lab.get()
                lab_id = next((l[0] for l in labs_list if l[1] == selected_lab_name), None)
                if not lab_id:
                    return

                amount = float(e_amount.get().strip() or 0)
                if amount <= 0:
                    return

                receipt_no = e_receipt.get().strip()
                method = cb_method.get()
                pay_date = e_date.get().strip()
                notes = e_notes.get().strip()

                success, msg = self.payments_repo.add_payment(lab_id, amount, method, pay_date, notes, receipt_no)
                if success:
                    e_amount.delete(0, "end")
                    e_receipt.delete(0, "end")
                    e_notes.delete(0, "end")
                    load_payments()
            except Exception as ex:
                print(f"Error saving payment: {ex}")

        save_p_btn.configure(command=save_payment)
        load_payments()

    def _edit_payment_dialog(self, pay_obj):
        pay_id = pay_obj[0]
        top = ctk.CTkToplevel(self)
        top.title(f"تعديل الدفعة #{pay_id}")
        top.geometry("380x280")
        top.resizable(False, False)
        top.grab_set()

        ctk.CTkLabel(top, text=f"✏️ تعديل الدفعة المالية #{pay_id}", font=get_font(size=14, weight="bold"), text_color=THEME["warning"]).pack(pady=15)

        form = ctk.CTkFrame(top, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20)

        ctk.CTkLabel(form, text="رقم السند:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e")
        e_rec = ctk.CTkEntry(form, width=340, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        e_rec.pack(anchor="e", pady=(0, 8))
        e_rec.insert(0, str(pay_obj[7] or "") if len(pay_obj) > 7 else "")

        ctk.CTkLabel(form, text="المبلغ المدفوع (ر.ي):", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e")
        e_amt = ctk.CTkEntry(form, width=340, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        e_amt.pack(anchor="e", pady=(0, 15))
        e_amt.insert(0, str(pay_obj[3] or 0))

        def save_edits():
            try:
                new_amt = float(e_amt.get().strip() or 0)
                new_rec = e_rec.get().strip()
                success, msg = self.payments_repo.update_payment(pay_id, new_amt, new_rec)
                if success:
                    top.destroy()
                    self._build_payments_tab()
            except Exception as ex:
                print(f"Error: {ex}")

        ctk.CTkButton(top, text="💾 حفظ التعديلات", width=150, height=34, fg_color=THEME["warning"], hover_color="darkorange", font=get_font(size=12, weight="bold"), command=save_edits).pack(pady=10)

    def _delete_payment(self, pay_id):
        if self.user_role != "admin":
            return
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذه الدفعة المالية؟"):
            self.payments_repo.delete_payment(pay_id)
            self._build_payments_tab()

    # =========================================================================
    # 3. تبويب المعامل المسجلة
    # =========================================================================
    def _build_labs_tab(self):
        container = self.tab_labs
        for w in container.winfo_children():
            w.destroy()

        form_frame = ctk.CTkFrame(
            container, 
            fg_color=THEME["bg_card_secondary"], 
            corner_radius=12, 
            border_width=1, 
            border_color=THEME["border_light"]
        )
        form_frame.pack(fill="x", padx=12, pady=(10, 8))

        ctk.CTkLabel(
            form_frame, 
            text="🏢 إضافة معمل صناعة أسنان جديد", 
            font=get_font(size=14, weight="bold"), 
            text_color=THEME["teal"]
        ).pack(anchor="e", padx=16, pady=(10, 6))

        row = ctk.CTkFrame(form_frame, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkLabel(row, text="اسم المعمل:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        e_name = ctk.CTkEntry(row, placeholder_text="اسم المعمل الرسمي", width=200, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_name)
        e_name.pack(side="right", padx=(0, 14))

        ctk.CTkLabel(row, text="العنوان:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        e_addr = ctk.CTkEntry(row, placeholder_text="المنطقة أو الشارع", width=200, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_addr)
        e_addr.pack(side="right", padx=(0, 14))

        ctk.CTkLabel(row, text="رقم الهاتف:", font=get_font(size=11, weight="bold"), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 4))
        e_phone = ctk.CTkEntry(row, placeholder_text="77xxxxxxx", width=140, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        setup_rtl_entry(e_phone)
        e_phone.pack(side="right", padx=(0, 14))

        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=6)

        def load_labs():
            for w in scroll.winfo_children():
                w.destroy()
            labs = self.labs_repo.get_all_labs()
            if labs:
                for l in labs:
                    card = ctk.CTkFrame(scroll, fg_color=THEME["bg_card_secondary"], corner_radius=10, border_width=1, border_color=THEME["border"])
                    card.pack(fill="x", pady=4)
                    
                    txt = f"🏢 المعمل: {l[1]}   |   📍 العنوان: {l[2] or 'غير متوفر'}   |   📞 الهاتف: {l[3] or 'غير متوفر'}"
                    ctk.CTkLabel(card, text=txt, font=get_font(size=12), text_color=THEME["text_primary"]).pack(anchor="e", padx=15, pady=(8, 2))

                    act_row = ctk.CTkFrame(card, fg_color="transparent")
                    act_row.pack(fill="x", padx=14, pady=(2, 8))

                    ctk.CTkButton(
                        act_row, text="✏️ تعديل المعمل", width=95, height=26,
                        font=get_font(size=10), fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                        command=lambda lab_item=l: self._edit_lab_dialog(lab_item)
                    ).pack(side="left", padx=2)

                    if self.user_role == "admin":
                        ctk.CTkButton(
                            act_row, text="🗑️ حذف المعمل", width=95, height=26,
                            font=get_font(size=10), fg_color=THEME["danger_soft"], hover_color=THEME["danger"],
                            command=lambda lab_id=l[0]: self._delete_lab(lab_id)
                        ).pack(side="left", padx=2)
            else:
                ctk.CTkLabel(scroll, text="لا توجد معامل مسجلة حالياً.", font=get_font(size=12), text_color=THEME["text_muted"]).pack(pady=25)

        def save_lab():
            name = e_name.get().strip()
            if not name:
                return
            self.labs_repo.add_lab(name, e_addr.get().strip(), e_phone.get().strip())
            e_name.delete(0, "end")
            e_addr.delete(0, "end")
            e_phone.delete(0, "end")
            load_labs()

        save_btn = ctk.CTkButton(
            row, 
            text="➕ إضافة المعمل", 
            fg_color=THEME["teal"], 
            hover_color=THEME["teal_hover"], 
            command=save_lab, 
            width=130, 
            height=34, 
            font=get_font(size=12, weight="bold")
        )
        save_btn.pack(side="left")

        load_labs()

    def _edit_lab_dialog(self, lab_obj):
        lab_id = lab_obj[0]
        top = ctk.CTkToplevel(self)
        top.title(f"تعديل المعمل #{lab_id}")
        top.geometry("380x280")
        top.resizable(False, False)
        top.grab_set()

        ctk.CTkLabel(top, text=f"✏️ تعديل بيانات المعمل", font=get_font(size=14, weight="bold"), text_color=THEME["warning"]).pack(pady=15)

        form = ctk.CTkFrame(top, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20)

        ctk.CTkLabel(form, text="اسم المعمل:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e")
        e_l_name = ctk.CTkEntry(form, width=340, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        e_l_name.pack(anchor="e", pady=(0, 8))
        e_l_name.insert(0, lab_obj[1] or "")

        ctk.CTkLabel(form, text="رقم الهاتف:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(anchor="e")
        e_l_phone = ctk.CTkEntry(form, width=340, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        e_l_phone.pack(anchor="e", pady=(0, 15))
        e_l_phone.insert(0, lab_obj[3] or "")

        def save_edits():
            try:
                success, msg = self.labs_repo.update_lab(lab_id, e_l_name.get().strip(), lab_obj[2] or "", e_l_phone.get().strip())
                if success:
                    top.destroy()
                    self._build_labs_tab()
            except Exception as ex:
                print(f"Error: {ex}")

        ctk.CTkButton(top, text="💾 حفظ التعديلات", width=150, height=34, fg_color=THEME["warning"], hover_color="darkorange", font=get_font(size=12, weight="bold"), command=save_edits).pack(pady=10)

    def _delete_lab(self, lab_id):
        if self.user_role != "admin":
            return
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذا المعمل نهائياً؟"):
            self.labs_repo.delete_lab(lab_id)
            self._build_labs_tab()
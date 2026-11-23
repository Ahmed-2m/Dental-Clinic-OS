import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk

from backend.purchases_repo import PurchasesRepository
from ui.theme import THEME, get_font

class PurchasesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.repo = PurchasesRepository()

        self.selected_supplier_id = None
        self.selected_purchase_id = None
        self.selected_payment_id = None
        
        self.supplier_map = {}
        self.purchase_map = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # حاوية التبويبات الرئيسية لإدارة المشتريات والموردين
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
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # إنشاء التبويبات الثلاثة
        self.tab_suppliers = self.tabview.add("👥 إدارة الموردين")
        self.tab_payments = self.tabview.add("💵 مدفوعات وسندات الموردين")
        self.tab_invoices = self.tabview.add("📦 فواتير المشتريات (نقد وأجل)")

        self.tabview.set("👥 إدارة الموردين")

        self._build_suppliers_tab()
        self._build_payments_tab()
        self._build_invoices_tab()

    # =========================================================================
    # 1. تبويب إدارة الموردين (إضافة، تعديل، حذف)
    # =========================================================================
    def _build_suppliers_tab(self):
        container = self.tab_suppliers

        form_box = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        form_box.pack(fill="x", padx=12, pady=(10, 8))

        self.sup_form_title_lbl = ctk.CTkLabel(form_box, text="➕ إضافة مورد جديد المتعاقد معهم:", font=get_font(size=13, weight="bold"), text_color=THEME["primary"])
        self.sup_form_title_lbl.pack(anchor="e", padx=16, pady=(10, 6))

        row1 = ctk.CTkFrame(form_box, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=6)

        ctk.CTkLabel(row1, text="اسم المورد:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.sup_name_entry = ctk.CTkEntry(row1, width=200, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.sup_name_entry.pack(side="right", padx=(0, 16))

        ctk.CTkLabel(row1, text="رقم الهاتف:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.sup_phone_entry = ctk.CTkEntry(row1, width=150, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.sup_phone_entry.pack(side="right", padx=(0, 16))

        ctk.CTkLabel(row1, text="العنوان:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.sup_address_entry = ctk.CTkEntry(row1, width=180, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.sup_address_entry.pack(side="right", padx=(0, 16))

        row2 = ctk.CTkFrame(form_box, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(6, 12))

        ctk.CTkLabel(row2, text="ملاحظات:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.sup_notes_entry = ctk.CTkEntry(row2, width=350, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.sup_notes_entry.pack(side="right", padx=(0, 16))

        self.btn_save_sup = ctk.CTkButton(row2, text="💾 حفظ المورد", width=130, height=32, fg_color=THEME["success"], hover_color=THEME["success_hover"], font=get_font(size=12, weight="bold"), command=self.save_new_supplier)
        self.btn_save_sup.pack(side="left", padx=5)

        self.btn_cancel_sup = ctk.CTkButton(row2, text="❌ إلغاء التعديل", width=110, height=32, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], font=get_font(size=11), command=self.reset_supplier_form)

        self.sup_status_lbl = ctk.CTkLabel(row2, text="", font=get_font(size=11))
        self.sup_status_lbl.pack(side="left", padx=10)

        list_box = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        list_box.pack(fill="both", expand=True, padx=12, pady=(4, 10))

        ctk.CTkLabel(list_box, text="📋 سجل الموردين المتعاقد معهم:", font=get_font(size=13, weight="bold"), text_color=THEME["primary"]).pack(anchor="e", padx=16, pady=(10, 4))

        self.sup_scroll = ctk.CTkScrollableFrame(list_box, fg_color="transparent")
        self.sup_scroll.pack(fill="both", expand=True, padx=10, pady=6)

        self.load_suppliers_view()

    def save_new_supplier(self):
        name = self.sup_name_entry.get().strip()
        phone = self.sup_phone_entry.get().strip()
        address = self.sup_address_entry.get().strip()
        notes = self.sup_notes_entry.get().strip()

        if not name:
            self.sup_status_lbl.configure(text="يرجى إدخال اسم المورد على الأقل.", text_color=THEME["danger"])
            return

        if self.selected_supplier_id:
            ok, msg = self.repo.update_supplier(self.selected_supplier_id, name, address, phone, notes)
        else:
            ok, msg = self.repo.add_supplier(name, address, phone, notes)

        self.sup_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])
        if ok:
            self.reset_supplier_form()
            self.load_suppliers_view()
            self.load_suppliers_dropdowns()

    def reset_supplier_form(self):
        self.selected_supplier_id = None
        self.sup_name_entry.delete(0, "end")
        self.sup_phone_entry.delete(0, "end")
        self.sup_address_entry.delete(0, "end")
        self.sup_notes_entry.delete(0, "end")
        self.sup_form_title_lbl.configure(text="➕ إضافة مورد جديد المتعاقد معهم:")
        self.btn_save_sup.configure(text="💾 حفظ المورد", fg_color=THEME["success"])
        self.btn_cancel_sup.pack_forget()

    def edit_supplier_row(self, s):
        self.selected_supplier_id = s[0]
        self.sup_name_entry.delete(0, "end")
        self.sup_name_entry.insert(0, s[1] or "")
        self.sup_address_entry.delete(0, "end")
        self.sup_address_entry.insert(0, s[2] or "")
        self.sup_phone_entry.delete(0, "end")
        self.sup_phone_entry.insert(0, s[3] or "")
        self.sup_notes_entry.delete(0, "end")
        self.sup_notes_entry.insert(0, s[4] or "")

        self.sup_form_title_lbl.configure(text=f"✏️ تعديل بيانات المورد (معرف #{s[0]}):")
        self.btn_save_sup.configure(text="💾 حفظ التعديلات", fg_color=THEME["warning"])
        self.btn_cancel_sup.pack(side="left", padx=5)

    def delete_supplier_row(self, sup_id, sup_name):
        if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف المورد ({sup_name}) نهائياً؟"):
            ok, msg = self.repo.delete_supplier(sup_id)
            if ok:
                self.load_suppliers_view()
                self.load_suppliers_dropdowns()
            else:
                messagebox.showerror("خطأ", msg)

    def load_suppliers_view(self):
        self.update_idletasks()
        for w in self.sup_scroll.winfo_children():
            w.destroy()
        suppliers = self.repo.get_suppliers_list()
        if suppliers:
            for s in suppliers:
                card = ctk.CTkFrame(self.sup_scroll, fg_color=THEME["bg_app"], corner_radius=8, border_width=1, border_color=THEME["border"])
                card.pack(fill="x", pady=3, padx=5)
                
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=6)
                
                txt = f"#{s[0]} | المورد: {s[1]} | هاتف: {s[3]} | العنوان: {s[2]} | المديونية المتبقية: {float(s[5]):,.2f} ر.ي"
                ctk.CTkLabel(row, text=txt, font=get_font(size=11, weight="bold"), text_color=THEME["text_primary"], anchor="e").pack(side="right", padx=5)

                btn_del = ctk.CTkButton(row, text="🗑️ حذف", width=65, height=28, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], font=get_font(size=10), command=lambda sid=s[0], sname=s[1]: self.delete_supplier_row(sid, sname))
                btn_del.pack(side="left", padx=3)

                btn_edit = ctk.CTkButton(row, text="✏️ تعديل", width=65, height=28, fg_color=THEME["warning"], hover_color="darkorange", font=get_font(size=10), command=lambda sup_obj=s: self.edit_supplier_row(sup_obj))
                btn_edit.pack(side="left", padx=3)
        else:
            ctk.CTkLabel(self.sup_scroll, text="لا توجد موردين مسجلين حالياً.", font=get_font(size=11), text_color=THEME["text_muted"]).pack(pady=20)

    # =========================================================================
    # 2. تبويب مدفوعات وسندات صرف الموردين (إضافة، تعديل، حذف)
    # =========================================================================
    def _build_payments_tab(self):
        container = self.tab_payments

        form_box = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        form_box.pack(fill="x", padx=12, pady=(10, 8))

        self.pay_form_title_lbl = ctk.CTkLabel(form_box, text="💵 تسجيل دفعة مالية وسند صرف للمورد:", font=get_font(size=13, weight="bold"), text_color=THEME["success"])
        self.pay_form_title_lbl.pack(anchor="e", padx=16, pady=(10, 6))

        row1 = ctk.CTkFrame(form_box, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=6)

        ctk.CTkLabel(row1, text="اختر المورد:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.combo_pay_supplier = ctk.CTkComboBox(row1, width=280, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"], command=lambda e: self.load_payments_history())
        self.combo_pay_supplier.pack(side="right", padx=(0, 16))

        ctk.CTkLabel(row1, text="رقم سند المورد:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.pay_voucher_entry = ctk.CTkEntry(row1, width=150, height=32, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.pay_voucher_entry.pack(side="right", padx=(0, 16))

        ctk.CTkButton(row1, text="🔄 تحديث", width=90, height=32, fg_color=THEME["bg_app"], hover_color=THEME["bg_card_hover"], border_width=1, border_color=THEME["border"], command=self.load_payment_suppliers_dropdown).pack(side="right", padx=(0, 10))

        row2 = ctk.CTkFrame(form_box, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(6, 12))

        ctk.CTkLabel(row2, text="المبلغ المراد سداده:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.pay_amount_entry = ctk.CTkEntry(row2, width=150, height=32, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.pay_amount_entry.pack(side="right", padx=(0, 16))

        ctk.CTkLabel(row2, text="تاريخ السداد:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.pay_date_entry = ctk.CTkEntry(row2, width=130, height=32, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.pay_date_entry.pack(side="right", padx=(0, 16))
        self.pay_date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))

        self.btn_save_pay = ctk.CTkButton(row2, text="✅ تأكيد وحفظ الدفعة والسند", width=170, height=32, fg_color=THEME["success"], hover_color=THEME["success_hover"], font=get_font(size=12, weight="bold"), command=self.save_supplier_payment)
        self.btn_save_pay.pack(side="left", padx=5)

        self.btn_cancel_pay = ctk.CTkButton(row2, text="❌ إلغاء", width=100, height=32, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], font=get_font(size=11), command=self.reset_payment_form)

        self.pay_status_lbl = ctk.CTkLabel(row2, text="", font=get_font(size=11))
        self.pay_status_lbl.pack(side="left", padx=10)

        list_box = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        list_box.pack(fill="both", expand=True, padx=12, pady=(4, 10))

        self.summary_row = ctk.CTkFrame(list_box, fg_color="transparent")
        self.summary_row.pack(fill="x", padx=16, pady=(10, 4))
        
        self.summary_lbl = ctk.CTkLabel(self.summary_row, text="", font=get_font(size=12, weight="bold"), text_color=THEME["teal"])
        self.summary_lbl.pack(anchor="e")

        ctk.CTkLabel(list_box, text="📋 سجل سندات الصرف وفواتير المورد:", font=get_font(size=13, weight="bold"), text_color=THEME["success"]).pack(anchor="e", padx=16, pady=(4, 4))

        self.pay_scroll = ctk.CTkScrollableFrame(list_box, fg_color="transparent")
        self.pay_scroll.pack(fill="both", expand=True, padx=10, pady=6)

        self.load_payment_suppliers_dropdown()

    def load_payment_suppliers_dropdown(self):
        suppliers = self.repo.get_suppliers_list()
        self.supplier_pay_map = {}
        values = []
        for s in suppliers:
            display_txt = f"{s[1]} (معرف #{s[0]})"
            self.supplier_pay_map[display_txt] = s[0]
            values.append(display_txt)
        
        if values:
            self.combo_pay_supplier.configure(values=values)
            self.combo_pay_supplier.set(values[0])
        else:
            self.combo_pay_supplier.configure(values=["لا توجد موردين مسجلين"])
            self.combo_pay_supplier.set("لا توجد موردين مسجلين")
        
        self.load_payments_history()

    def save_supplier_payment(self):
        choice = self.combo_pay_supplier.get()
        if choice not in self.supplier_pay_map:
            self.pay_status_lbl.configure(text="يرجى اختيار مورد صحيح.", text_color=THEME["danger"])
            return
        
        supplier_id = self.supplier_pay_map[choice]
        try:
            amount_to_pay = float(self.pay_amount_entry.get().strip())
        except ValueError:
            self.pay_status_lbl.configure(text="يرجى إدخال مبلغ صحيح للسداد.", text_color=THEME["danger"])
            return

        voucher_no = self.pay_voucher_entry.get().strip() or None
        if not voucher_no:
            self.pay_status_lbl.configure(text="يرجى إدخال رقم سند المورد.", text_color=THEME["danger"])
            return

        p_date = self.pay_date_entry.get().strip() or datetime.date.today().strftime("%Y-%m-%d")

        if self.selected_payment_id:
            # تعديل سند صرف موجود
            ok, msg = self.repo.update_supplier_payment(self.selected_payment_id, amount_to_pay, p_date, voucher_no)
            self.pay_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])
            if ok:
                self.reset_payment_form()
                self.load_payments_history()
                self.load_invoices_history()
                self.load_suppliers_view()
        else:
            # إضافة دفعة جديدة وتوزيعها على الفواتير المتبقية
            invoices = self.repo.get_purchases_list()
            supplier_invoices = [inv for inv in invoices if inv[2] == supplier_id and float(inv[8]) > 0]

            if not supplier_invoices:
                self.pay_status_lbl.configure(text="هذا المورد ليس عليه أي فواتير بقيمة متبقية.", text_color=THEME["warning"])
                return

            remaining_payment = amount_to_pay
            success = False
            last_msg = ""

            for inv in supplier_invoices:
                if remaining_payment <= 0:
                    break
                pur_id = inv[0]
                inv_remain = float(inv[8])
                pay_for_this = min(remaining_payment, inv_remain)

                ok, msg = self.repo.make_supplier_payment(pur_id, pay_for_this, p_date, voucher_no)
                if ok:
                    success = True
                    remaining_payment -= pay_for_this
                else:
                    last_msg = msg

            if success:
                self.pay_status_lbl.configure(text="تم تسجيل السند وتوثيق الدفعة بنجاح.", text_color=THEME["success"])
                self.pay_amount_entry.delete(0, "end")
                self.pay_voucher_entry.delete(0, "end")
                self.load_payments_history()
                self.load_invoices_history()
                self.load_suppliers_view()
            else:
                self.pay_status_lbl.configure(text=last_msg or "فشل تسجيل السند.", text_color=THEME["danger"])

    def reset_payment_form(self):
        self.selected_payment_id = None
        self.pay_amount_entry.delete(0, "end")
        self.pay_voucher_entry.delete(0, "end")
        self.pay_form_title_lbl.configure(text="💵 تسجيل دفعة مالية وسند صرف للمورد:")
        self.btn_save_pay.configure(text="✅ تأكيد وحفظ الدفعة والسند", fg_color=THEME["success"])
        self.btn_cancel_pay.pack_forget()

    def edit_payment_row(self, pay):
        self.selected_payment_id = pay[0]
        self.pay_amount_entry.delete(0, "end")
        self.pay_amount_entry.insert(0, str(pay[3]))
        self.pay_date_entry.delete(0, "end")
        self.pay_date_entry.insert(0, str(pay[4]))
        self.pay_voucher_entry.delete(0, "end")
        self.pay_voucher_entry.insert(0, str(pay[5]) if pay[5] != '-' else "")

        self.pay_form_title_lbl.configure(text=f"✏️ تعديل سند الصرف (معرف #{pay[0]}):")
        self.btn_save_pay.configure(text="💾 حفظ تعديل السند", fg_color=THEME["warning"])
        self.btn_cancel_pay.pack(side="left", padx=5)

    def delete_payment_row(self, payment_id):
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف سند الصرف هذا واستعادة المبلغ للمديونية؟"):
            ok, msg = self.repo.delete_supplier_payment(payment_id)
            if ok:
                self.load_payments_history()
                self.load_invoices_history()
                self.load_suppliers_view()
            else:
                messagebox.showerror("خطأ", msg)

    def load_payments_history(self):
        self.update_idletasks()
        for w in self.pay_scroll.winfo_children():
            w.destroy()
        
        choice = getattr(self, 'combo_pay_supplier', None) and self.combo_pay_supplier.get()
        if not choice or choice not in getattr(self, 'supplier_pay_map', {}):
            self.summary_lbl.configure(text="إجمالي المشتريات: 0.00 | إجمالي المدفوع: 0.00 | المتبقي الصافي: 0.00 ر.ي")
            return

        selected_sup_id = self.supplier_pay_map[choice]
        invoices = self.repo.get_purchases_list()
        sup_invoices = [inv for inv in invoices if inv[2] == selected_sup_id]

        total_sum = sum(float(inv[6]) for inv in sup_invoices)
        paid_sum = sum(float(inv[7]) for inv in sup_invoices)
        remain_sum = sum(float(inv[8]) for inv in sup_invoices)

        self.summary_lbl.configure(
            text=f"📊 ملخص حساب المورد: إجمالي المشتريات ({total_sum:,.2f}) | إجمالي المدفوع ({paid_sum:,.2f}) | 🔴 المتبقي الصافي ({remain_sum:,.2f} ر.ي)"
        )

        payments = self.repo.get_supplier_payments_list(selected_sup_id)
        if payments:
            ctk.CTkLabel(self.pay_scroll, text="💵 سجل سندات الصرف والدفعات المالية (مع خيارات التعديل والحذف):", font=get_font(size=12, weight="bold"), text_color=THEME["success"]).pack(anchor="e", padx=5, pady=(5, 5))
            for pay in payments:
                card = ctk.CTkFrame(self.pay_scroll, fg_color=THEME["bg_app"], corner_radius=8, border_width=1, border_color=THEME["border"])
                card.pack(fill="x", pady=3, padx=5)
                
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=6)
                
                for col in range(5):
                    row.grid_columnconfigure(col, weight=1)

                ctk.CTkLabel(row, text=f"البيان: {pay[6] or '-'}", font=get_font(size=11), text_color=THEME["text_primary"], anchor="e").grid(row=0, column=0, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"التاريخ: {pay[4]}", font=get_font(size=11), text_color=THEME["text_secondary"], anchor="e").grid(row=0, column=1, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"المبلغ المسدد: {float(pay[3]):,.2f} ر.ي", font=get_font(size=11, weight="bold"), text_color=THEME["success"], anchor="e").grid(row=0, column=2, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"رقم سند المورد: {pay[5]}", font=get_font(size=11, weight="bold"), text_color=THEME["teal"], anchor="e").grid(row=0, column=3, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"سند صرف #{pay[0]}", font=get_font(size=11, weight="bold"), text_color=THEME["indigo"], anchor="e").grid(row=0, column=4, sticky="e", padx=2)

                btn_p_box = ctk.CTkFrame(card, fg_color="transparent")
                btn_p_box.pack(fill="x", padx=12, pady=(0, 6))

                btn_del_p = ctk.CTkButton(btn_p_box, text="🗑️ حذف السند", width=85, height=26, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], font=get_font(size=10), command=lambda pid=pay[0]: self.delete_payment_row(pid))
                btn_del_p.pack(side="left", padx=3)

                btn_edit_p = ctk.CTkButton(btn_p_box, text="✏️ تعديل السند", width=85, height=26, fg_color=THEME["warning"], hover_color="darkorange", font=get_font(size=10), command=lambda p_obj=pay: self.edit_payment_row(p_obj))
                btn_edit_p.pack(side="left", padx=3)

        if sup_invoices:
            ctk.CTkLabel(self.pay_scroll, text="📋 سجل فواتير المشتريات:", font=get_font(size=12, weight="bold"), text_color=THEME["indigo"]).pack(anchor="e", padx=5, pady=(15, 5))
            for inv in sup_invoices:
                card = ctk.CTkFrame(self.pay_scroll, fg_color=THEME["bg_app"], corner_radius=8, border_width=1, border_color=THEME["border"])
                card.pack(fill="x", pady=3, padx=5)
                
                status_str = "خالص" if inv[10] == "Paid" else ("مسدد جزئياً" if inv[10] == "Partial" else "أجل / غير مسدد")
                status_color = THEME["success"] if inv[10] == "Paid" else (THEME["warning"] if inv[10] == "Partial" else THEME["danger"])
                p_type_txt = "آجل" if (len(inv) > 9 and inv[9] == 'Credit') else "نقداً"

                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=6)
                
                for col in range(7):
                    row.grid_columnconfigure(col, weight=1)

                ctk.CTkLabel(row, text=f"الحالة: {status_str}", font=get_font(size=11, weight="bold"), text_color=status_color, anchor="e").grid(row=0, column=0, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"المتبقي: {float(inv[8]):,.2f}", font=get_font(size=11, weight="bold"), text_color=THEME["danger"], anchor="e").grid(row=0, column=1, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"المدفوع: {float(inv[7]):,.2f}", font=get_font(size=11), text_color=THEME["success"], anchor="e").grid(row=0, column=2, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"الإجمالي: {float(inv[6]):,.2f}", font=get_font(size=11), text_color=THEME["text_primary"], anchor="e").grid(row=0, column=3, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"التاريخ: {inv[5]}", font=get_font(size=11), text_color=THEME["text_secondary"], anchor="e").grid(row=0, column=4, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"النوع: {p_type_txt}", font=get_font(size=11), text_color=THEME["purple"], anchor="e").grid(row=0, column=5, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"فاتورة: {inv[1]}", font=get_font(size=11, weight="bold"), text_color=THEME["indigo"], anchor="e").grid(row=0, column=6, sticky="e", padx=2)
        
        if not payments and not sup_invoices:
            ctk.CTkLabel(self.pay_scroll, text="لا توجد حركات مسجلة لهذا المورد.", font=get_font(size=11), text_color=THEME["text_muted"]).pack(pady=20)

    # =========================================================================
    # 3. تبويب فواتير المشتريات (إضافة، تعديل، حذف)
    # =========================================================================
    def _build_invoices_tab(self):
        container = self.tab_invoices

        form_box = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        form_box.pack(fill="x", padx=12, pady=(10, 8))

        self.inv_form_title_lbl = ctk.CTkLabel(form_box, text="📦 إدخال فاتورة مشتريات جديدة (نقد أو أجل):", font=get_font(size=13, weight="bold"), text_color=THEME["indigo"])
        self.inv_form_title_lbl.pack(anchor="e", padx=16, pady=(10, 6))

        row1 = ctk.CTkFrame(form_box, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=6)

        ctk.CTkLabel(row1, text="رقم الفاتورة:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.inv_id_entry = ctk.CTkEntry(row1, width=90, height=32, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.inv_id_entry.pack(side="right", padx=(0, 12))

        ctk.CTkLabel(row1, text="نوع الفاتورة:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.combo_inv_type = ctk.CTkComboBox(row1, values=["نقداً (Cash)", "آجل (Credit)"], width=130, height=32, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"], command=self._on_invoice_type_changed)
        self.combo_inv_type.pack(side="right", padx=(0, 12))
        self.combo_inv_type.set("نقداً (Cash)")

        ctk.CTkLabel(row1, text="المورد:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.combo_inv_supplier = ctk.CTkComboBox(row1, width=190, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.combo_inv_supplier.pack(side="right", padx=(0, 12))

        ctk.CTkLabel(row1, text="إجمالي الفاتورة:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.inv_total_entry = ctk.CTkEntry(row1, width=110, height=32, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.inv_total_entry.pack(side="right", padx=(0, 12))

        ctk.CTkLabel(row1, text="المبلغ المدفوع:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.inv_paid_entry = ctk.CTkEntry(row1, width=110, height=32, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.inv_paid_entry.pack(side="right", padx=(0, 6))

        row2 = ctk.CTkFrame(form_box, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(6, 12))

        ctk.CTkLabel(row2, text="تاريخ الفاتورة:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.inv_date_entry = ctk.CTkEntry(row2, width=130, height=32, justify="center", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.inv_date_entry.pack(side="right", padx=(0, 16))
        self.inv_date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))

        ctk.CTkLabel(row2, text="البيان والتفاصيل:", font=get_font(size=11), text_color=THEME["text_secondary"]).pack(side="right", padx=(0, 6))
        self.inv_desc_entry = ctk.CTkEntry(row2, width=300, height=32, justify="right", fg_color=THEME["bg_app"], border_color=THEME["border"])
        self.inv_desc_entry.pack(side="right", padx=(0, 16))

        self.btn_save_inv = ctk.CTkButton(row2, text="💾 حفظ الفاتورة", width=130, height=32, fg_color=THEME["indigo"], hover_color=THEME["primary_hover"], font=get_font(size=12, weight="bold"), command=self.save_purchase_invoice)
        self.btn_save_inv.pack(side="left", padx=5)

        self.btn_cancel_inv = ctk.CTkButton(row2, text="❌ إلغاء", width=100, height=32, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], font=get_font(size=11), command=self.reset_invoice_form)

        self.inv_status_lbl = ctk.CTkLabel(row2, text="", font=get_font(size=11))
        self.inv_status_lbl.pack(side="left", padx=10)

        list_box = ctk.CTkFrame(container, fg_color=THEME["bg_card_secondary"], corner_radius=12, border_width=1, border_color=THEME["border_light"])
        list_box.pack(fill="both", expand=True, padx=12, pady=(4, 10))

        ctk.CTkLabel(list_box, text="📋 سجل فواتير المشتريات التفصيلي:", font=get_font(size=13, weight="bold"), text_color=THEME["indigo"]).pack(anchor="e", padx=16, pady=(10, 4))

        self.inv_scroll = ctk.CTkScrollableFrame(list_box, fg_color="transparent")
        self.inv_scroll.pack(fill="both", expand=True, padx=10, pady=6)

        self.load_suppliers_dropdowns()
        self.load_invoices_history()

    def _on_invoice_type_changed(self, choice):
        if "نقداً" in choice:
            total_val = self.inv_total_entry.get().strip()
            if total_val:
                self.inv_paid_entry.delete(0, "end")
                self.inv_paid_entry.insert(0, total_val)
        else:
            self.inv_paid_entry.delete(0, "end")

    def load_suppliers_dropdowns(self):
        suppliers = self.repo.get_suppliers_list()
        self.supplier_map.clear()
        values = []
        for s in suppliers:
            display_txt = f"{s[1]} (#{s[0]})"
            self.supplier_map[display_txt] = s[0]
            values.append(display_txt)
        if values:
            self.combo_inv_supplier.configure(values=values)
            self.combo_inv_supplier.set(values[0])
        else:
            self.combo_inv_supplier.configure(values=["لا توجد موردين مسجلين"])
            self.combo_inv_supplier.set("لا توجد موردين مسجلين")

        self.load_payment_suppliers_dropdown()

    def save_purchase_invoice(self):
        inv_num = self.inv_id_entry.get().strip()
        sup_choice = self.combo_inv_supplier.get()
        if sup_choice not in self.supplier_map:
            self.inv_status_lbl.configure(text="يرجى اختيار مورد صحيح.", text_color=THEME["danger"])
            return

        supplier_id = self.supplier_map[sup_choice]
        type_choice = self.combo_inv_type.get()
        purchase_type = 'Cash' if "نقداً" in type_choice else 'Credit'

        try:
            total = float(self.inv_total_entry.get().strip() or 0)
            paid_str = self.inv_paid_entry.get().strip()
            paid = float(paid_str) if paid_str else 0.0
        except ValueError:
            self.inv_status_lbl.configure(text="يرجى إدخال أرقام صحيحة للمبالغ.", text_color=THEME["danger"])
            return

        if purchase_type == 'Cash' and paid < total:
            paid = total

        description = self.inv_desc_entry.get().strip()
        p_date = self.inv_date_entry.get().strip() or datetime.date.today().strftime("%Y-%m-%d")

        if self.selected_purchase_id:
            ok, msg = self.repo.update_purchase_invoice(self.selected_purchase_id, inv_num, supplier_id, description, p_date, total, paid, purchase_type)
        else:
            ok, msg = self.repo.add_purchase_invoice(inv_num, supplier_id, description, p_date, total, paid, purchase_type)

        self.inv_status_lbl.configure(text=msg, text_color=THEME["success"] if ok else THEME["danger"])
        if ok:
            self.reset_invoice_form()
            self.load_invoices_history()
            self.load_payments_history()
            self.load_payment_suppliers_dropdown()
            self.load_suppliers_view()

    def reset_invoice_form(self):
        self.selected_purchase_id = None
        self.inv_id_entry.delete(0, "end")
        self.inv_total_entry.delete(0, "end")
        self.inv_paid_entry.delete(0, "end")
        self.inv_desc_entry.delete(0, "end")
        self.inv_form_title_lbl.configure(text="📦 إدخال فاتورة مشتريات جديدة (نقد أو أجل):")
        self.btn_save_inv.configure(text="💾 حفظ الفاتورة", fg_color=THEME["indigo"])
        self.btn_cancel_inv.pack_forget()

    def edit_invoice_row(self, inv):
        self.selected_purchase_id = inv[0]
        self.inv_id_entry.delete(0, "end")
        self.inv_id_entry.insert(0, inv[1] or "")
        self.inv_total_entry.delete(0, "end")
        self.inv_total_entry.insert(0, str(inv[6]))
        self.inv_paid_entry.delete(0, "end")
        self.inv_paid_entry.insert(0, str(inv[7]))
        self.inv_date_entry.delete(0, "end")
        self.inv_date_entry.insert(0, inv[5] or "")
        self.inv_desc_entry.delete(0, "end")
        self.inv_desc_entry.insert(0, inv[4] or "")

        p_type = inv[9] if len(inv) > 9 else 'Cash'
        if p_type == 'Credit':
            self.combo_inv_type.set("آجل (Credit)")
        else:
            self.combo_inv_type.set("نقداً (Cash)")

        for k, v in self.supplier_map.items():
            if v == inv[2]:
                self.combo_inv_supplier.set(k)
                break

        self.inv_form_title_lbl.configure(text=f"✏️ تعديل فاتورة المشتريات (رقم المعرف #{inv[0]}):")
        self.btn_save_inv.configure(text="💾 حفظ التعديلات", fg_color=THEME["warning"])
        self.btn_cancel_inv.pack(side="left", padx=5)

    def delete_invoice_row(self, pur_id):
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف فاتورة المشتريات هذه نهائياً؟"):
            ok, msg = self.repo.delete_purchase_invoice(pur_id)
            if ok:
                self.load_invoices_history()
                self.load_payments_history()
                self.load_suppliers_view()
            else:
                messagebox.showerror("خطأ", msg)

    def load_invoices_history(self):
        self.update_idletasks()
        for w in self.inv_scroll.winfo_children():
            w.destroy()
        invoices = self.repo.get_purchases_list()
        if invoices:
            for inv in invoices:
                card = ctk.CTkFrame(self.inv_scroll, fg_color=THEME["bg_app"], corner_radius=8, border_width=1, border_color=THEME["border"])
                card.pack(fill="x", pady=4, padx=5)
                
                status_str = "خالص" if inv[10] == "Paid" else ("مسدد جزئياً" if inv[10] == "Partial" else "أجل / غير مسدد")
                status_color = THEME["success"] if inv[10] == "Paid" else (THEME["warning"] if inv[10] == "Partial" else THEME["danger"])
                p_type_txt = "آجل" if (len(inv) > 9 and inv[9] == 'Credit') else "نقداً"

                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=8)
                
                for col in range(8):
                    row.grid_columnconfigure(col, weight=1)

                ctk.CTkLabel(row, text=f"الحالة: {status_str}", font=get_font(size=11, weight="bold"), text_color=status_color, anchor="e").grid(row=0, column=0, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"المتبقي: {float(inv[8]):,.2f}", font=get_font(size=11, weight="bold"), text_color=THEME["danger"], anchor="e").grid(row=0, column=1, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"المدفوع: {float(inv[7]):,.2f}", font=get_font(size=11), text_color=THEME["success"], anchor="e").grid(row=0, column=2, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"الإجمالي: {float(inv[6]):,.2f}", font=get_font(size=11), text_color=THEME["text_primary"], anchor="e").grid(row=0, column=3, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"التاريخ: {inv[5]}", font=get_font(size=11), text_color=THEME["text_secondary"], anchor="e").grid(row=0, column=4, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"النوع: {p_type_txt}", font=get_font(size=11), text_color=THEME["purple"], anchor="e").grid(row=0, column=5, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"المورد: {inv[3]}", font=get_font(size=11, weight="bold"), text_color=THEME["teal"], anchor="e").grid(row=0, column=6, sticky="e", padx=2)
                ctk.CTkLabel(row, text=f"فاتورة: {inv[1]}", font=get_font(size=11, weight="bold"), text_color=THEME["indigo"], anchor="e").grid(row=0, column=7, sticky="e", padx=2)

                btn_box = ctk.CTkFrame(card, fg_color="transparent")
                btn_box.pack(fill="x", padx=12, pady=(0, 6))

                btn_del = ctk.CTkButton(btn_box, text="🗑️ حذف الفاتورة", width=90, height=26, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], font=get_font(size=10), command=lambda pid=inv[0]: self.delete_invoice_row(pid))
                btn_del.pack(side="left", padx=3)

                btn_edit = ctk.CTkButton(btn_box, text="✏️ تعديل الفاتورة", width=90, height=26, fg_color=THEME["warning"], hover_color="darkorange", font=get_font(size=10), command=lambda i_obj=inv: self.edit_invoice_row(i_obj))
                btn_edit.pack(side="left", padx=3)
        else:
            ctk.CTkLabel(self.inv_scroll, text="لا توجد فواتير مشتريات مسجلة.", font=get_font(size=11), text_color=THEME["text_muted"]).pack(pady=20)
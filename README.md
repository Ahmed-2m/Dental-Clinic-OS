# Dental-Clinic-OS
**منظومة تشغيل وإدارة متكاملة لعيادات ومراكز طب الأسنان**

**Dental-Clinic-OS** هو نظام متكامل مبني بلغة Python ومجهّز كنسخة سطح مكتب مستقلة قابلة للتشغيل على Windows[span_0](start_span)[span_0](end_span)، صُمّم لهندسة وأتمتة الدورة التشغيلية والسريرية والمحاسبية الكاملة داخل عيادات ومراكز طب الأسنان[span_1](start_span)[span_1](end_span)[span_2](start_span)[span_2](end_span)[span_3](start_span)[span_3](end_span). يجمع النظام بين سهولة الاستخدام للطاقم الطبي والإداري، والدقة المحاسبية في تتبع التدفقات النقدية، الفواتير، ذمم المرضى، المشتريات، المختبرات، ومعاملات الموظفين[span_4](start_span)[span_4](end_span)[span_5](start_span)[span_5](end_span)[span_6](start_span)[span_6](end_span)، مع دعم التنسيقات الإقليمية للغة العربية[span_7](start_span)[span_7](end_span)، هوية بصرية موحدة[span_8](start_span)[span_8](end_span)[span_9](start_span)[span_9](end_span)، وملف إعدادات مخصص للعيادة[span_10](start_span)[span_10](end_span).

---

## أبرز المزايا والقدرات الهندسية

* **جاهزية تشغيل مباشرة:** يتضمن حزمة تشغيل مجمّعة على Windows دون الحاجة لتعقيدات الإعداد على أجهزة التشغيل[span_11](start_span)[span_11](end_span).
* **فصل معماري منظم:** يفصل بين طبقة منطق الأعمال والوصول للبيانات (`backend`) عبر وحدات مستقلة (`Repositories`)[span_12](start_span)[span_12](end_span)[span_13](start_span)[span_13](end_span)، وطبقة واجهات المستخدم والهوية البصرية (`ui` و`assets`)[span_14](start_span)[span_14](end_span)[span_15](start_span)[span_15](end_span).
* **منظومة محاسبية ومالية متكاملة:** يغطي الفواتير، حسابات المرضى، كشوفات الحساب، الصندوق اليومي، الخزينة، المصروفات، المشتريات، الموردين، ومدفوعات المختبرات[span_16](start_span)[span_16](end_span)[span_17](start_span)[span_17](end_span)[span_18](start_span)[span_18](end_span).
* **متابعة سريرية ومخبرية شاملة:** ينظّم بيانات المرضى، المواعيد، الزيارات العلاجية، العلاجات، والمختبرات وأوامر العمل المرتبطة بها[span_19](start_span)[span_19](end_span)[span_20](start_span)[span_20](end_span).
* **إدارة الموارد البشرية والحوكمة:** يشمل إدارة الموظفين ومعاملاتهم المالية، نظام تسجيل الدخول، إعدادات العيادة (`clinic_config.json`)، والتقارير[span_21](start_span)[span_21](end_span)[span_22](start_span)[span_22](end_span)[span_23](start_span)[span_23](end_span).
* **حماية البيانات والاستمرارية:** يدعم النسخ الاحتياطي التلقائي لقاعدة البيانات بصيغة SQL لحماية السجلات[span_24](start_span)[span_24](end_span).

---

## الوحدات الأساسية للنظام

### 1. المرضى والمواعيد والزيارات العلاجية
* **المرضى (`Patients`):** إدارة سجل المرضى وحساباتهم وأرصدتهم[span_25](start_span)[span_25](end_span)[span_26](start_span)[span_26](end_span).
* **المواعيد (`Appointments`):** جدولة وتنظيم مواعيد المراجعين[span_27](start_span)[span_27](end_span)[span_28](start_span)[span_28](end_span).
* **الزيارات والعلاجات (`Patient Visits & Treatments`):** توثيق الزيارات والإجراءات العلاجية المقدمة[span_29](start_span)[span_29](end_span)[span_30](start_span)[span_30](end_span).

### 2. المختبرات الخارجية
* **المختبرات (`Labs`):** إدارة بيانات المختبرات المتعاقد معها[span_31](start_span)[span_31](end_span)[span_32](start_span)[span_32](end_span).
* **أوامر العمل المخبرية (`Lab Orders`):** متابعة الطلبات والحالات المرسلة للمختبرات[span_33](start_span)[span_33](end_span).
* **مدفوعات المختبرات (`Lab Payments`):** تسجيل وضبط المستحقات والدفعات المالية للمختبرات[span_34](start_span)[span_34](end_span).

### 3. النظام المالي والمحاسبي
* **الفواتير وحسابات المرضى (`Invoices & Patient Accounts`):** إصدار الفواتير ومتابعة أرصدة وحسابات المرضى[span_35](start_span)[span_35](end_span).
* **الخزينة والصندوق اليومي (`Treasury & Daily Cash`):** متابعة حركة النقد والصندوق اليومي والخزينة[span_36](start_span)[span_36](end_span)[span_37](start_span)[span_37](end_span).
* **كشوفات الحساب (`Statements`):** إعداد ومراجعة كشوفات الحساب[span_38](start_span)[span_38](end_span)[span_39](start_span)[span_39](end_span)[span_40](start_span)[span_40](end_span).
* **المصروفات (`Expenses`):** تسجيل ومتابعة مصروفات العيادة[span_41](start_span)[span_41](end_span).

### 4. المشتريات والموردون والموظفون
* **المشتريات والموردون (`Purchases & Suppliers`):** إدارة عمليات الشراء وحسابات الموردين[span_42](start_span)[span_42](end_span)[span_43](start_span)[span_43](end_span).
* **الموظفون ومعاملاتهم (`Staff & Employee Transactions`):** إدارة بيانات الموظفين ومعاملاتهم المالية[span_44](start_span)[span_44](end_span)[span_45](start_span)[span_45](end_span).

### 5. الأمان والتقارير والنسخ الاحتياطي
* **المصادقة والإعدادات (`Authentication & Settings`):** تسجيل الدخول وضبط إعدادات النظام والعيادة[span_46](start_span)[span_46](end_span)[span_47](start_span)[span_47](end_span)[span_48](start_span)[span_48](end_span).
* **التقارير (`Reports`):** استخراج التقارير التشغيلية والمالية[span_49](start_span)[span_49](end_span).
* **النسخ الاحتياطي (`Database Backups`):** حفظ نسخ احتياطية تلقائية لقاعدة البيانات بصيغة SQL[span_50](start_span)[span_50](end_span).

---

## هيكلة المشروع

```text
Dental-Clinic-OS/
├── main.py                      # نقطة تشغيل التطبيق الرئيسية
├── clinic_config.json           # ملف إعدادات العيادة
├── backend/                     # طبقة منطق الأعمال والوصول للبيانات
│   ├── database.py              # الاتصال وإدارة قاعدة البيانات
│   ├── auth_repo.py             # المصادقة وتسجيل الدخول
│   ├── patients_repo.py         # بيانات المرضى
│   ├── patient_accounts_repo.py # حسابات المرضى
│   ├── appointments_repo.py     # المواعيد
│   ├── treatments_repo.py       # العلاجات
│   ├── labs_repo.py             # المختبرات
│   ├── lab_orders_repo.py       # أوامر المختبرات
│   ├── lab_payments_repo.py     # مدفوعات المختبرات
│   ├── invoices_repo.py         # الفواتير
│   ├── statements_repo.py       # كشوفات الحساب
│   ├── daily_cash_repo.py       # الصندوق اليومي
│   ├── treasury_repo.py         # الخزينة
│   ├── expenses_repo.py         # المصروفات
│   ├── purchases_repo.py        # المشتريات
│   ├── suppliers_repo.py        # الموردون
│   ├── staff_repo.py            # الموظفون
│   ├── employee_transactions.py # معاملات الموظفين
│   ├── reports_repo.py          # التقارير
│   └── backup_repo.py           # النسخ الاحتياطي
├── ui/                          # واجهات المستخدم والسمات
│   ├── theme.py                 # تنسيق السمات والواجهة
│   └── *_view.py                # شاشات وواجهات النظام
├── assets/                      # الشعارات والأيقونات والملفات البصرية
├── database_backups/            # ملفات النسخ الاحتياطي لقاعدة البيانات (SQL)
└── dist/                        # نسخة التشغيل المجمّعة لنظام Windows

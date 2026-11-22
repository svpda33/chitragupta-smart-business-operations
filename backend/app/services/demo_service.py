import json
from datetime import date, datetime, time, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.customer import Customer
from app.models.expense import Expense
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.payment import Payment
from app.models.setting import Setting
from app.services.setting_service import DEFAULT_EXPENSES
from app.utils.money import paise_to_rupees_text, rupees_to_paise


def _to_utc_dt(d: date) -> datetime:
    return datetime.combine(d, time(10, 0), tzinfo=timezone.utc)


def seed_synthetic_demo_data(
    db: Session,
    today: date | None = None,
    force: bool = False,
    business_id: int | None = None,
) -> dict:
    if today is None:
        today = date.today()

    # Idempotent guard: do not destroy existing data unless explicitly confirmed with force=True
    if not force:
        cust_q = select(Customer.id)
        inv_q = select(Invoice.id)
        if business_id is not None:
            cust_q = cust_q.where(Customer.business_id == business_id)
            inv_q = inv_q.where(Invoice.business_id == business_id)
        has_customers = db.scalar(cust_q.limit(1)) is not None
        has_invoices = db.scalar(inv_q.limit(1)) is not None
        if has_customers or has_invoices:
            return {
                "status": "skipped",
                "message": "Database already contains records. Pass force=true to reset demo data.",
                "customers_seeded": 0,
                "invoices_seeded": 0,
                "expenses_seeded": 0,
            }

    # Clear existing data ONLY for this business_id (never other businesses!)
    if business_id is not None:
        biz_inv_ids = list(
            db.scalars(select(Invoice.id).where(Invoice.business_id == business_id)).all()
        )
        db.query(Payment).filter(Payment.business_id == business_id).delete()
        if biz_inv_ids:
            db.query(InvoiceItem).filter(InvoiceItem.invoice_id.in_(biz_inv_ids)).delete(
                synchronize_session=False
            )
        db.query(Invoice).filter(Invoice.business_id == business_id).delete()
        db.query(Customer).filter(Customer.business_id == business_id).delete()
        db.query(Expense).filter(Expense.business_id == business_id).delete()
        db.query(Setting).filter(Setting.business_id == business_id).delete()
    else:
        db.query(Payment).delete()
        db.query(InvoiceItem).delete()
        db.query(Invoice).delete()
        db.query(Customer).delete()
        db.query(AuditEvent).delete()
        db.query(Expense).delete()
        db.query(Setting).delete()
    db.commit()

    # 1. Initialize Settings
    settings = Setting(
        business_id=business_id,
        business_name="Chitragupta Operations Consulting",
        owner_name="Aditi Sharma",
        email="aditi.sharma@chitragupta.local",
        phone="+91 98765 43210",
        address="102, 12th Main, HAL 2nd Stage, Indiranagar, Bengaluru, Karnataka 560038",
        gstin="29AAAAA1234A1Z8",
        upi_id="aditi.consulting@okhdfcbank",
        bank_name="HDFC Bank",
        bank_account="50100456789012",
        bank_ifsc="HDFC0001234",
        default_payment_terms_days=15,
        default_tax_percent=18,
        initial_cash_balance_paise=25000000,  # ₹2,50,000.00
        monthly_recurring_expenses_paise=6500000,  # ₹65,000.00
        safety_cash_threshold_paise=5000000,  # ₹50,000.00
        expenses_json=json.dumps(DEFAULT_EXPENSES),
    )
    db.add(settings)
    db.commit()

    # 2. Customers
    customers_data = [
        {
            "name": "TechNova Solutions Pvt Ltd",
            "email": "accounts@technovasolutions.in",
            "phone": "+91 98450 12345",
            "address": "EcoWorld Tech Park, Outer Ring Road, Bengaluru",
            "notes": "Enterprise software client. 30-day payment cycle.",
        },
        {
            "name": "GreenLeaf Wellness Clinic",
            "email": "dr.meera@greenleafclinic.org",
            "phone": "+91 97401 23456",
            "address": "45 Lavelle Road, Shanthala Nagar, Bengaluru",
            "notes": "Clinic operations & appointment automation client.",
        },
        {
            "name": "Zenith Retail & Supermarket",
            "email": "billing@zenithretail.co.in",
            "phone": "+91 98860 34567",
            "address": "12 Commercial Street, Tasker Town, Bengaluru",
            "notes": "Retail store chain. Pays on 15-day terms.",
        },
        {
            "name": "Apex Learning Academy",
            "email": "finance@apexlearning.edu.in",
            "phone": "+91 99000 45678",
            "address": "88 Jayanagar 4th Block, Bengaluru",
            "notes": "Coaching institute. Occasional payment follow-up needed.",
        },
        {
            "name": "Urban Craft Architects",
            "email": "studio@urbancraft.design",
            "phone": "+91 96111 56789",
            "address": "77 Koramangala 5th Block, Bengaluru",
            "notes": "Boutique architecture studio.",
        },
        {
            "name": "Metro Logistics Hub",
            "email": "dispatch@metrologistics.in",
            "phone": "+91 98452 67890",
            "address": "Plot 14, Peenya Industrial Area, Bengaluru",
            "notes": "Fleet dispatch software setup.",
        },
    ]

    customer_objs = {}
    for c_data in customers_data:
        cust = Customer(
            business_id=business_id,
            name=c_data["name"],
            email=c_data["email"],
            phone=c_data["phone"],
            address=c_data["address"],
            notes=c_data["notes"],
        )
        db.add(cust)
        db.commit()
        db.refresh(cust)
        customer_objs[c_data["name"]] = cust

    # 3. Create Invoices
    # We will create a rich spread of:
    # - Paid invoices
    # - Partially paid invoices
    # - Overdue invoices (1 gentle, 1 firm, 1 urgent)
    # - Pending invoices due in future
    # - Draft invoices
    invoices_def = [
        # INV-0001: Paid invoice
        {
            "customer": "TechNova Solutions Pvt Ltd",
            "invoice_number": "INV-0001",
            "invoice_date": today - timedelta(days=45),
            "due_date": today - timedelta(days=30),
            "description": "Backend API Architecture & Optimization",
            "tax_percent": 18,
            "items": [
                {"description": "Core API sprint consulting (80 hrs)", "quantity": 1, "unit_price": "80000.00"},
                {"description": "Database indexing & query tuning", "quantity": 1, "unit_price": "20000.00"},
            ],
            "lifecycle": "sent",
            "payments": [
                {"amount": "118000.00", "days_ago": 32, "method": "bank_transfer", "ref": "NEFT/HDFC/20260212"}
            ],
        },
        # INV-0002: Paid invoice
        {
            "customer": "GreenLeaf Wellness Clinic",
            "invoice_number": "INV-0002",
            "invoice_date": today - timedelta(days=35),
            "due_date": today - timedelta(days=20),
            "description": "Patient Booking WhatsApp Flow & Dashboard",
            "tax_percent": 18,
            "items": [
                {"description": "WhatsApp Business API integration", "quantity": 1, "unit_price": "35000.00"},
                {"description": "Staff training & handover", "quantity": 1, "unit_price": "10000.00"},
            ],
            "lifecycle": "sent",
            "payments": [
                {"amount": "53100.00", "days_ago": 18, "method": "upi", "ref": "UPI/2026/02/771829"}
            ],
        },
        # INV-0003: Partially Paid invoice
        {
            "customer": "Zenith Retail & Supermarket",
            "invoice_number": "INV-0003",
            "invoice_date": today - timedelta(days=25),
            "due_date": today + timedelta(days=5),
            "description": "POS Inventory Synchronization Module",
            "tax_percent": 18,
            "items": [
                {"description": "Barcode sync scanner script", "quantity": 2, "unit_price": "25000.00"},
                {"description": "Cloud database connector", "quantity": 1, "unit_price": "15000.00"},
            ],
            "lifecycle": "sent",
            "payments": [
                # Subtotal = 65,000, Tax 18% = 11,700, Total = 76,700. Paid 40,000
                {"amount": "40000.00", "days_ago": 10, "method": "bank_transfer", "ref": "IMPS/98172635"}
            ],
        },
        # INV-0004: Urgent Overdue Invoice (28 days overdue)
        {
            "customer": "Apex Learning Academy",
            "invoice_number": "INV-0004",
            "invoice_date": today - timedelta(days=45),
            "due_date": today - timedelta(days=28),
            "description": "Student Fee Tracking & Automated Receipts",
            "tax_percent": 18,
            "items": [
                {"description": "Fee portal automation script", "quantity": 1, "unit_price": "60000.00"},
                {"description": "SMS gateway integration", "quantity": 1, "unit_price": "12000.00"},
            ],
            "lifecycle": "sent",
            "payments": [],  # Subtotal 72,000 + 12,960 = 84,960 outstanding!
        },
        # INV-0005: Firm Overdue Invoice (12 days overdue)
        {
            "customer": "Urban Craft Architects",
            "invoice_number": "INV-0005",
            "invoice_date": today - timedelta(days=27),
            "due_date": today - timedelta(days=12),
            "description": "3D CAD Cloud Asset Repository Setup",
            "tax_percent": 18,
            "items": [
                {"description": "Storage bucket & backup scripts", "quantity": 1, "unit_price": "40000.00"},
                {"description": "Access control & user groups", "quantity": 1, "unit_price": "10000.00"},
            ],
            "lifecycle": "sent",
            "payments": [],  # Total 59,000 outstanding!
        },
        # INV-0006: Gentle Overdue Invoice (4 days overdue)
        {
            "customer": "Metro Logistics Hub",
            "invoice_number": "INV-0006",
            "invoice_date": today - timedelta(days=19),
            "due_date": today - timedelta(days=4),
            "description": "Fleet Driver Mobile App API Services",
            "tax_percent": 18,
            "items": [
                {"description": "GPS endpoint optimization", "quantity": 1, "unit_price": "30000.00"},
            ],
            "lifecycle": "sent",
            "payments": [],  # Total 35,400 outstanding!
        },
        # INV-0007: Pending Invoice (due in 2 days - upcoming reminder!)
        {
            "customer": "TechNova Solutions Pvt Ltd",
            "invoice_number": "INV-0007",
            "invoice_date": today - timedelta(days=13),
            "due_date": today + timedelta(days=2),
            "description": "Monthly DevOps Maintenance Retainer (Feb 2026)",
            "tax_percent": 18,
            "items": [
                {"description": "Monthly Kubernetes & AWS cluster ops", "quantity": 1, "unit_price": "50000.00"},
            ],
            "lifecycle": "sent",
            "payments": [],  # Total 59,000
        },
        # INV-0008: Pending Invoice (due in 14 days)
        {
            "customer": "GreenLeaf Wellness Clinic",
            "invoice_number": "INV-0008",
            "invoice_date": today - timedelta(days=1),
            "due_date": today + timedelta(days=14),
            "description": "Tele-Consultation Video Portal Addon",
            "tax_percent": 18,
            "items": [
                {"description": "WebRTC server config & custom domain", "quantity": 1, "unit_price": "45000.00"},
            ],
            "lifecycle": "sent",
            "payments": [],  # Total 53,100
        },
        # INV-0009: Draft Invoice (ready to review & send)
        {
            "customer": "Urban Craft Architects",
            "invoice_number": "INV-0009",
            "invoice_date": today,
            "due_date": today + timedelta(days=15),
            "description": "BIM Model Collaboration Server Setup",
            "tax_percent": 18,
            "items": [
                {"description": "Private Git repository & backup sync", "quantity": 1, "unit_price": "35000.00"},
                {"description": "Documentation & security audit", "quantity": 1, "unit_price": "15000.00"},
            ],
            "lifecycle": "draft",
            "payments": [],
        },
        # INV-0010: Draft Invoice
        {
            "customer": "Zenith Retail & Supermarket",
            "invoice_number": "INV-0010",
            "invoice_date": today,
            "due_date": today + timedelta(days=15),
            "description": "Customer Loyalty Points QR Integration",
            "tax_percent": 18,
            "items": [
                {"description": "Dynamic QR generator API", "quantity": 1, "unit_price": "28000.00"},
            ],
            "lifecycle": "draft",
            "payments": [],
        },
    ]

    for inv_def in invoices_def:
        cust = customer_objs[inv_def["customer"]]
        # Compute items
        lines = []
        subtotal = 0
        for it in inv_def["items"]:
            qty = it["quantity"]
            unit_paise = rupees_to_paise(it["unit_price"])
            lt = qty * unit_paise
            subtotal += lt
            lines.append((it["description"], qty, unit_paise, lt))

        tax = (subtotal * inv_def["tax_percent"] + 50) // 100
        total = subtotal + tax

        inv = Invoice(
            business_id=business_id,
            customer_id=cust.id,
            invoice_number=inv_def["invoice_number"],
            invoice_date=inv_def["invoice_date"],
            due_date=inv_def["due_date"],
            description=inv_def["description"],
            tax_percent=inv_def["tax_percent"],
            subtotal_paise=subtotal,
            tax_paise=tax,
            total_paise=total,
            lifecycle=inv_def["lifecycle"],
            sent_at=_to_utc_dt(inv_def["invoice_date"]) if inv_def["lifecycle"] == "sent" else None,
            notes="Thank you for partnering with Chitragupta Operations Consulting.",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        # Add invoice items
        for pos, (desc, qty, up, lt) in enumerate(lines, start=1):
            item = InvoiceItem(
                invoice_id=inv.id,
                position=pos,
                description=desc,
                quantity=qty,
                unit_price_paise=up,
                line_total_paise=lt,
            )
            db.add(item)

        # Audit event for invoice creation
        db.add(AuditEvent(
            entity_type="invoice",
            entity_id=inv.id,
            action="created",
            summary=f"Invoice {inv.invoice_number} created.",
            created_at=_to_utc_dt(inv_def["invoice_date"]),
        ))

        if inv.lifecycle == "sent":
            db.add(AuditEvent(
                entity_type="invoice",
                entity_id=inv.id,
                action="sent",
                summary=f"Invoice {inv.invoice_number} marked as sent.",
                created_at=_to_utc_dt(inv_def["invoice_date"]),
            ))

        db.commit()

        # Add payments
        for pmt_def in inv_def.get("payments", []):
            pmt_date = today - timedelta(days=pmt_def["days_ago"])
            pmt_paise = rupees_to_paise(pmt_def["amount"])
            pmt = Payment(
                business_id=business_id,
                invoice_id=inv.id,
                customer_id=cust.id,
                amount_paise=pmt_paise,
                payment_date=pmt_date,
                method=pmt_def["method"],
                reference=pmt_def.get("ref"),
                notes="Payment received and credited.",
                status="active",
            )
            db.add(pmt)
            db.commit()
            db.refresh(pmt)

            db.add(AuditEvent(
                entity_type="invoice",
                entity_id=inv.id,
                action="payment_recorded",
                summary=f"Payment of ₹{paise_to_rupees_text(pmt_paise)} recorded ({pmt_def['method']}).",
                created_at=_to_utc_dt(pmt_date),
            ))
            db.add(AuditEvent(
                entity_type="payment",
                entity_id=pmt.id,
                action="payment_recorded",
                summary=f"Payment #{pmt.id} recorded for invoice {inv.invoice_number}.",
                created_at=_to_utc_dt(pmt_date),
            ))
            db.commit()

    # Also add 1 reversed payment on INV-0001 to demonstrate payment audit & reversal capability!
    inv1_q = db.query(Invoice).filter(Invoice.invoice_number == "INV-0001")
    if business_id is not None:
        inv1_q = inv1_q.filter(Invoice.business_id == business_id)
    inv1 = inv1_q.first()
    if inv1:
        rev_date = today - timedelta(days=40)
        rev_pmt = Payment(
            business_id=business_id,
            invoice_id=inv1.id,
            customer_id=inv1.customer_id,
            amount_paise=2500000,  # ₹25,000
            payment_date=rev_date,
            method="bank_transfer",
            reference="CHQ/BOUNCE/0091",
            notes="Initial cheque deposit.",
            status="reversed",
            reversed_at=_to_utc_dt(today - timedelta(days=38)),
            reversal_reason="Cheque returned unpaid by clearing house due to signature mismatch.",
        )
        db.add(rev_pmt)
        db.commit()
        db.refresh(rev_pmt)

        db.add(AuditEvent(
            entity_type="payment",
            entity_id=rev_pmt.id,
            action="payment_reversed",
            summary=f"Payment #{rev_pmt.id} reversed: Cheque returned unpaid.",
            created_at=_to_utc_dt(today - timedelta(days=38)),
        ))
        db.commit()

    # 4. Seed Business Expenses
    sample_expenses = [
        {
            "name": "Indiranagar Office Rent",
            "category": "Rent",
            "amount_paise": 2500000,
            "expense_date": today.replace(day=5) if today.day <= 5 else (today + timedelta(days=20)).replace(day=5),
            "is_recurring": True,
            "day_of_month": 5,
            "notes": "Co-working space private desk lease.",
        },
        {
            "name": "Cloud Infrastructure & SaaS Suite",
            "category": "Software",
            "amount_paise": 1000000,
            "expense_date": today.replace(day=10) if today.day <= 10 else (today + timedelta(days=20)).replace(day=10),
            "is_recurring": True,
            "day_of_month": 10,
            "notes": "AWS, GitHub, Google Workspace, Accounting tools.",
        },
        {
            "name": "Assistant Operations Stipend",
            "category": "Payroll",
            "amount_paise": 2000000,
            "expense_date": today.replace(day=1) if today.day <= 1 else (today + timedelta(days=25)).replace(day=1),
            "is_recurring": True,
            "day_of_month": 1,
            "notes": "Part-time operations assistant stipend.",
        },
        {
            "name": "High-Speed Internet & Fiber Line",
            "category": "Utilities",
            "amount_paise": 1000000,
            "expense_date": today.replace(day=15) if today.day <= 15 else (today + timedelta(days=20)).replace(day=15),
            "is_recurring": True,
            "day_of_month": 15,
            "notes": "ACT Fibernet commercial broadband.",
        },
        {
            "name": "Hardware Server UPS Battery Replacement",
            "category": "Equipment",
            "amount_paise": 1500000,
            "expense_date": today + timedelta(days=6),
            "is_recurring": False,
            "day_of_month": None,
            "notes": "One-off backup power unit maintenance.",
        },
    ]

    for exp_data in sample_expenses:
        exp = Expense(
            business_id=business_id,
            name=exp_data["name"],
            category=exp_data["category"],
            amount_paise=exp_data["amount_paise"],
            expense_date=exp_data["expense_date"],
            is_recurring=exp_data["is_recurring"],
            day_of_month=exp_data["day_of_month"],
            notes=exp_data["notes"],
        )
        db.add(exp)
    db.commit()

    return {
        "status": "success",
        "message": "Synthetic demonstration data successfully seeded.",
        "customers_seeded": len(customers_data),
        "invoices_seeded": len(invoices_def),
        "expenses_seeded": len(sample_expenses),
    }

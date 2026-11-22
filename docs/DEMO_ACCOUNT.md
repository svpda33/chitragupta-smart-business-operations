# Chitragupta — Demonstration Accounts & Complete Seed Reference

> This is the **single authoritative document** for Chitragupta's two independent demonstration businesses. All product records, inventory balances, valuations, customers, invoices, payments, expenses, and notes below are generated directly from the live seeded SQLite database.

## Demo Login Instructions

1. Open Chitragupta at **http://127.0.0.1:5180**.
2. Click **Sign In** (or navigate to `/login`).
3. Sign in with either demonstration account below. Each account is completely isolated by `business_id` across Dashboard, Customers, Catalogue, Inventory, Invoices, Payments, Cash Flow, Reminders, Notepad, AI Finance Copilot, and Settings.

| Business | Owner | Email | Password | Category | Location |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Urban Stationery & Office Supplies** | Rahul Sharma | `demo@chitragupta.in` | `ChitraDemo@2026!` | Retail / Stationery and Office Supplies | Hyderabad, Telangana, India |
| **Oakwood Furniture Studio** | Arjun Mehta | `furniture.demo@chitragupta.in` | `FurnitureDemo@2026!` | Retail / Home and Office Furniture | Hyderabad, Telangana, India |

> **Security Notice:** These credentials are public demonstration accounts only. Plaintext passwords are never stored in application source code and are securely hashed with `scrypt` in SQLite. Never reuse demo credentials for real production or administrative accounts.

### Controlled Re-Seeding Command

Demo data is **never** recreated automatically on server startup and **never** modifies or deletes real user accounts.

```powershell
.\backend\.venv\Scripts\python.exe backend\scripts\seed_dual_demo.py ^
  --stationery-password "<STATIONERY_DEMO_PASSWORD>" ^
  --furniture-password "<FURNITURE_DEMO_PASSWORD>" ^
  --reset-demo --write-docs
```

---

## 1. Business A — Urban Stationery & Office Supplies

### Business Profile & Live Financial Snapshot

- **Business Name:** Urban Stationery & Office Supplies
- **Owner:** Rahul Sharma (`demo@chitragupta.in`)
- **Category:** Retail / Stationery and Office Supplies
- **Address:** Shop 14 & 15, Tilak Road, Abids, Hyderabad, Telangana 500001
- **GSTIN:** `36AABCU9603R1ZM` · **Currency:** `INR`
- **Products:** 50 active products (2057 units on hand)
- **Inventory Valuation (Purchase Cost):** ₹260,568.00
- **Low-Stock Products:** 6 · **Out-of-Stock Products:** 2
- **Total Outstanding Receivables:** ₹64,763.40 (Overdue: ₹25,971.80)
- **Total Collected All-Time:** ₹71,532.80
- **Estimated Cash on Hand:** ₹223,282.80 (Runway: ~100 days)

### Category Breakdown

| Category | Product Count |
| :--- | :---: |
| Art and stationery accessories | 10 |
| Office equipment | 10 |
| Office supplies | 10 |
| Paper and notebooks | 10 |
| Pens and writing supplies | 10 |

### Complete Product Catalogue (50 Products)

| SKU | Product Name | Category | Purchase Cost (₹) | Selling Price (₹) | GST | Unit | Opening Stock | Current Stock | Min Threshold | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `STN-ART-001` | A3 Spiral Sketchbook 140 GSM (50 Sheets) | Art and stationery accessories | 165.00 | 280.00 | 12% | pcs | 40 | **28** | 10 | `in_stock` |
| `STN-ART-002` | Artist Watercolor Cake Set (24 Shades) | Art and stationery accessories | 190.00 | 340.00 | 12% | set | 26 | **18** | 8 | `in_stock` |
| `STN-ART-003` | Acrylic Paint Tube Set 12ml (18 Colors) | Art and stationery accessories | 265.00 | 440.00 | 18% | set | 22 | **22** | 6 | `in_stock` |
| `STN-ART-004` | Oil Pastels Artist Box (36 Shades) | Art and stationery accessories | 145.00 | 250.00 | 12% | set | 34 | **24** | 8 | `in_stock` |
| `STN-ART-005` | Fine Synthetic Brush Set (10 Assorted Sizes) | Art and stationery accessories | 135.00 | 240.00 | 12% | set | 30 | **20** | 8 | `in_stock` |
| `STN-ART-006` | Mathematical Geometry & Compass Box | Art and stationery accessories | 92.00 | 165.00 | 12% | set | 48 | **48** | 12 | `in_stock` |
| `STN-ART-007` | Stainless Steel 30cm Measuring Ruler | Art and stationery accessories | 35.00 | 65.00 | 18% | pcs | 75 | **60** | 15 | `in_stock` |
| `STN-ART-008` | Mesh Metal 6-Compartment Desk Organizer | Art and stationery accessories | 195.00 | 340.00 | 18% | pcs | 24 | **22** | 8 | `in_stock` |
| `STN-ART-009` | A3 Self-Healing Cutting Mat (Green) | Art and stationery accessories | 285.00 | 480.00 | 18% | pcs | 4 | **4** | 6 | `low_stock` |
| `STN-ART-010` | Heavy-Duty Snap-Off Craft Utility Knife | Art and stationery accessories | 58.00 | 105.00 | 18% | pcs | 44 | **32** | 10 | `in_stock` |
| `STN-EQP-001` | 12-Digit Dual-Power Desktop Calculator | Office equipment | 295.00 | 490.00 | 18% | pcs | 36 | **26** | 10 | `in_stock` |
| `STN-EQP-002` | Heavy-Duty Metal Desktop Stapler (24/6) | Office equipment | 185.00 | 320.00 | 18% | pcs | 42 | **34** | 10 | `in_stock` |
| `STN-EQP-003` | Two-Hole Heavy Paper Punch (30 Sheets) | Office equipment | 175.00 | 295.00 | 18% | pcs | 32 | **32** | 8 | `in_stock` |
| `STN-EQP-004` | Stainless Steel Office Scissors 21cm | Office equipment | 65.00 | 115.00 | 18% | pcs | 58 | **48** | 15 | `in_stock` |
| `STN-EQP-005` | A4 Thermal Laminating Machine (Hot & Cold) | Office equipment | 1,450.00 | 2,250.00 | 18% | pcs | 9 | **7** | 4 | `in_stock` |
| `STN-EQP-006` | Cross-Cut Personal Paper Shredder (8-Sheet) | Office equipment | 2,850.00 | 4,250.00 | 18% | pcs | 5 | **3** | 3 | `low_stock` |
| `STN-EQP-007` | A4 Guillotine Paper Trimmer (12-Sheet) | Office equipment | 890.00 | 1,450.00 | 18% | pcs | 10 | **8** | 4 | `in_stock` |
| `STN-EQP-008` | Magnetic Aluminum Whiteboard 3x2 ft | Office equipment | 920.00 | 1,490.00 | 18% | pcs | 3 | **3** | 5 | `low_stock` |
| `STN-EQP-009` | Weighted Desktop Tape Dispenser (24mm) | Office equipment | 120.00 | 210.00 | 18% | pcs | 28 | **28** | 8 | `in_stock` |
| `STN-EQP-010` | Self-Inking Date & Received Stamp | Office equipment | 160.00 | 280.00 | 18% | pcs | 0 | **0** | 6 | `out_of_stock` |
| `STN-OFF-001` | Heavy-Duty Lever Arch Box File (A4) | Office supplies | 88.00 | 145.00 | 18% | pcs | 85 | **85** | 20 | `in_stock` |
| `STN-OFF-002` | Clear L-Shaped Document Folders (Pack of 25) | Office supplies | 130.00 | 215.00 | 18% | pack | 60 | **45** | 15 | `in_stock` |
| `STN-OFF-003` | Expanding 12-Pocket Accordion File Folder | Office supplies | 165.00 | 275.00 | 18% | pcs | 38 | **28** | 10 | `in_stock` |
| `STN-OFF-004` | Metal Binder Clips 32mm (Box of 12) | Office supplies | 42.00 | 75.00 | 18% | box | 100 | **85** | 20 | `in_stock` |
| `STN-OFF-005` | Stainless Steel Paper Clips 28mm (Box of 100) | Office supplies | 24.00 | 45.00 | 18% | box | 140 | **140** | 25 | `in_stock` |
| `STN-OFF-006` | Standard No. 10 Staples (Pack of 10 Boxes) | Office supplies | 95.00 | 160.00 | 18% | pack | 70 | **70** | 15 | `in_stock` |
| `STN-OFF-007` | 24/6 Office Staples (Pack of 10 Boxes) | Office supplies | 145.00 | 235.00 | 18% | pack | 55 | **55** | 15 | `in_stock` |
| `STN-OFF-008` | Clear Adhesive BOPP Packing Tape 48mm (Pack of 6) | Office supplies | 210.00 | 330.00 | 18% | pack | 48 | **30** | 12 | `in_stock` |
| `STN-OFF-009` | Glue Stick 21g Non-Toxic (Pack of 5) | Office supplies | 110.00 | 185.00 | 18% | pack | 52 | **42** | 12 | `in_stock` |
| `STN-OFF-010` | Kraft Brown A4 Document Envelopes (Pack of 50) | Office supplies | 150.00 | 245.00 | 12% | pack | 10 | **10** | 15 | `low_stock` |
| `STN-PAP-001` | A4 Copier Paper 75 GSM (500 Sheets) | Paper and notebooks | 235.00 | 320.00 | 12% | ream | 120 | **105** | 25 | `in_stock` |
| `STN-PAP-002` | A4 Copier Paper 80 GSM Premium Ream | Paper and notebooks | 275.00 | 370.00 | 12% | ream | 75 | **55** | 20 | `in_stock` |
| `STN-PAP-003` | A3 Copier Paper 80 GSM (500 Sheets) | Paper and notebooks | 520.00 | 690.00 | 12% | ream | 24 | **11** | 10 | `in_stock` |
| `STN-PAP-004` | A5 Hardcover Ruled Notebook (192 Pages) | Paper and notebooks | 110.00 | 185.00 | 12% | pcs | 90 | **51** | 20 | `in_stock` |
| `STN-PAP-005` | Spiral Conference Notebook A4 (200 Pages) | Paper and notebooks | 78.00 | 130.00 | 12% | pcs | 80 | **50** | 18 | `in_stock` |
| `STN-PAP-006` | Sticky Notes Cube 3x3 Neon (400 Sheets) | Paper and notebooks | 58.00 | 95.00 | 12% | pack | 65 | **53** | 15 | `in_stock` |
| `STN-PAP-007` | Legal Ruled Writing Pad (80 Sheets) | Paper and notebooks | 42.00 | 75.00 | 12% | pcs | 55 | **35** | 15 | `in_stock` |
| `STN-PAP-008` | Ledger Register Book 300 Pages (Hardbound) | Paper and notebooks | 145.00 | 240.00 | 12% | pcs | 12 | **12** | 15 | `low_stock` |
| `STN-PAP-009` | Glossy Photo Paper A4 180 GSM (50 Sheets) | Paper and notebooks | 195.00 | 310.00 | 12% | pack | 18 | **18** | 10 | `in_stock` |
| `STN-PAP-010` | Thermal Billing Paper Rolls 80mm (Pack of 10) | Paper and notebooks | 310.00 | 450.00 | 18% | pack | 0 | **0** | 12 | `out_of_stock` |
| `STN-PEN-001` | SmoothFlow Blue Ballpoint Pens (Box of 20) | Pens and writing supplies | 115.00 | 180.00 | 12% | box | 110 | **118** | 25 | `in_stock` |
| `STN-PEN-002` | SmoothFlow Black Ballpoint Pens (Box of 20) | Pens and writing supplies | 115.00 | 180.00 | 12% | box | 85 | **73** | 20 | `in_stock` |
| `STN-PEN-003` | GelPro 0.5mm Waterproof Gel Pens (Pack of 10) | Pens and writing supplies | 95.00 | 160.00 | 12% | pack | 95 | **75** | 20 | `in_stock` |
| `STN-PEN-004` | Executive Metal Rollerball Pen (Gift Box) | Pens and writing supplies | 210.00 | 380.00 | 18% | pcs | 30 | **30** | 8 | `in_stock` |
| `STN-PEN-005` | HB Graphite Pencils with Eraser (Box of 12) | Pens and writing supplies | 38.00 | 65.00 | 12% | box | 130 | **105** | 25 | `in_stock` |
| `STN-PEN-006` | Mechanical Pencil 0.7mm with Lead Tube | Pens and writing supplies | 45.00 | 85.00 | 12% | pcs | 60 | **45** | 15 | `in_stock` |
| `STN-PEN-007` | Chisel-Tip Highlighter Set (Pack of 5) | Pens and writing supplies | 72.00 | 125.00 | 12% | set | 70 | **70** | 15 | `in_stock` |
| `STN-PEN-008` | Whiteboard Dry-Erase Markers (Pack of 4) | Pens and writing supplies | 68.00 | 120.00 | 18% | pack | 14 | **14** | 18 | `low_stock` |
| `STN-PEN-009` | Permanent Fine-Tip Markers Black (Pack of 10) | Pens and writing supplies | 125.00 | 210.00 | 18% | pack | 45 | **30** | 12 | `in_stock` |
| `STN-PEN-010` | Correction Tape Roller 5mm x 8m (Pack of 3) | Pens and writing supplies | 84.00 | 145.00 | 18% | pack | 50 | **50** | 12 | `in_stock` |

### Customers (9)

| Customer Name | Email | Phone | Outstanding (₹) | Overdue (₹) |
| :--- | :--- | :--- | :---: | :---: |
| CarePlus Diagnostics Lab | admin@careplusdiag.in | +91 98660 55667 | 10,289.60 | 0.00 |
| Charminar Print & Copy Hub | orders@charminarprint.in | +91 97010 33445 | 0.00 | 0.00 |
| Deccan Tech Park Admin | procurement@deccantechpark.in | +91 98480 11223 | 0.00 | 0.00 |
| Gachibowli CoWork Spaces | ops@gachibowlicowork.in | +91 91002 99001 | 11,830.00 | 0.00 |
| Hyderabad Public Coaching Centre | accounts@hpcoaching.edu.in | +91 98490 22334 | 6,524.00 | 0.00 |
| Kukatpally Legal Associates | office@kplegal.in | +91 90001 66778 | 12,401.80 | 12,401.80 |
| Nizam College Fine Arts Dept | artsdept@nizamcollege.edu.in | +91 94401 88990 | 0.00 | 0.00 |
| Secunderabad Logistics Corp | billing@seclogistics.in | +91 98482 77889 | 13,570.00 | 13,570.00 |
| Vignan Architecture Studio | studio@vignanarch.in | +91 99490 44556 | 10,148.00 | 0.00 |

### Invoices (11)

| Invoice # | Customer | Lifecycle | Status | Total (₹) | Paid (₹) | Outstanding (₹) | Due Date |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `INV-0011` | Hyderabad Public Coaching Centre | draft | `draft` | 5,152.00 | 0.00 | 5,152.00 | 2026-12-07 |
| `INV-0010` | Deccan Tech Park Admin | draft | `draft` | 5,770.20 | 0.00 | 5,770.20 | 2026-12-07 |
| `INV-0009` | CarePlus Diagnostics Lab | sent | `pending` | 10,289.60 | 0.00 | 10,289.60 | 2026-12-04 |
| `INV-0008` | Vignan Architecture Studio | sent | `pending` | 10,148.00 | 0.00 | 10,148.00 | 2026-11-25 |
| `INV-0005` | Gachibowli CoWork Spaces | sent | `partially_paid` | 21,830.00 | 10,000.00 | 11,830.00 | 2026-11-28 |
| `INV-0004` | Hyderabad Public Coaching Centre | sent | `partially_paid` | 17,024.00 | 10,500.00 | 6,524.00 | 2026-11-27 |
| `INV-0007` | Secunderabad Logistics Corp | sent | `overdue` | 13,570.00 | 0.00 | 13,570.00 | 2026-11-14 |
| `INV-0003` | Nizam College Fine Arts Dept | sent | `paid` | 12,297.60 | 12,297.60 | 0.00 | 2026-11-13 |
| `INV-0002` | Charminar Print & Copy Hub | sent | `paid` | 25,222.40 | 25,222.40 | 0.00 | 2026-11-09 |
| `INV-0006` | Kukatpally Legal Associates | sent | `overdue` | 12,401.80 | 0.00 | 12,401.80 | 2026-11-03 |
| `INV-0001` | Deccan Tech Park Admin | sent | `paid` | 13,512.80 | 13,512.80 | 0.00 | 2026-11-02 |

### Payments (6)

| Invoice # | Customer | Amount (₹) | Method | Reference | Date |
| :--- | :--- | :---: | :---: | :--- | :---: |
| `INV-0004` | Hyderabad Public Coaching Centre | 4,500.00 | bank_transfer | IMPS/HPCC/102 | 2026-11-18 |
| `INV-0005` | Gachibowli CoWork Spaces | 10,000.00 | bank_transfer | NEFT/GCW/771 | 2026-11-16 |
| `INV-0003` | Nizam College Fine Arts Dept | 12,297.60 | bank_transfer | NEFT/NCFA/3319 | 2026-11-11 |
| `INV-0004` | Hyderabad Public Coaching Centre | 6,000.00 | upi | UPI/HPCC/101 | 2026-11-10 |
| `INV-0002` | Charminar Print & Copy Hub | 25,222.40 | upi | UPI/CPH/4410 | 2026-11-07 |
| `INV-0001` | Deccan Tech Park Admin | 13,512.80 | bank_transfer | NEFT/DTP/8821 | 2026-10-31 |

### Scheduled Expenses (4)

| Expense | Category | Amount (₹) | Type |
| :--- | :--- | :---: | :---: |
| Store Staff Salaries (2 Assistants) | Payroll | 32,000.00 | Recurring (Day 1) |
| Abids Retail Shop & Godown Rent | Rent | 28,000.00 | Recurring (Day 5) |
| Local Delivery Tempo Fuel & Maintenance | Logistics | 4,800.00 | One-off (2026-11-28) |
| Electricity, Broadband & POS Software | Utilities | 6,500.00 | Recurring (Day 12) |

### Business Notes (5)

- **Overdue Follow-ups — Hyderabad B2B** [Customers] *(Pinned)*: Kukatpally Legal Associates and Secunderabad Logistics Corp invoices are past due. Send polite WhatsApp reminders with UPI ID.
- **Urgent Restock List — This Week** [Suppliers] *(Pinned)*: Thermal POS rolls (STN-PAP-010) and Self-Inking Stamps (STN-EQP-010) are out of stock. Call Balaji Paper Agencies and Kores distributor today.
- **GST Return Preparation Checklist** [Finance]: Compile GSTR-1 B2B invoice summary by the 10th of the month.
- **Monthly Stock Audit Findings** [Operations]: Completed shelf audit for Paper & Notebooks section. Adjusted 4 damaged hardcover notebooks and moved 2 mesh organizers to front display.
- **Back-to-School & Exam Bulk Pricing** [Finance]: Offer 6% volume discount on orders above ₹25,000 for coaching centres while preserving minimum 22% gross margin.

### Inventory Scenarios & Recent Stock Movements

| Product | SKU | Type | Change | Balance After | Reason |
| :--- | :--- | :---: | :---: | :---: | :--- |
| Glue Stick 21g Non-Toxic (Pack of 5) | `STN-OFF-009` | `sale` | **-10** | 42 | Sold via invoice INV-0009 |
| SmoothFlow Blue Ballpoint Pens (Box of 20) | `STN-PEN-001` | `sale` | **-12** | 118 | Sold via invoice INV-0009 |
| 12-Digit Dual-Power Desktop Calculator | `STN-EQP-001` | `sale` | **-4** | 26 | Sold via invoice INV-0009 |
| Expanding 12-Pocket Accordion File Folder | `STN-OFF-003` | `sale` | **-10** | 28 | Sold via invoice INV-0009 |
| Stainless Steel 30cm Measuring Ruler | `STN-ART-007` | `sale` | **-15** | 60 | Sold via invoice INV-0008 |
| Mechanical Pencil 0.7mm with Lead Tube | `STN-PEN-006` | `sale` | **-15** | 45 | Sold via invoice INV-0008 |
| A4 Guillotine Paper Trimmer (12-Sheet) | `STN-EQP-007` | `sale` | **-2** | 8 | Sold via invoice INV-0008 |
| A3 Copier Paper 80 GSM (500 Sheets) | `STN-PAP-003` | `sale` | **-5** | 11 | Sold via invoice INV-0008 |
| Heavy-Duty Snap-Off Craft Utility Knife | `STN-ART-010` | `sale` | **-12** | 32 | Sold via invoice INV-0007 |
| Stainless Steel Office Scissors 21cm | `STN-EQP-004` | `sale` | **-10** | 48 | Sold via invoice INV-0007 |
| Permanent Fine-Tip Markers Black (Pack of 10) | `STN-PEN-009` | `sale` | **-15** | 30 | Sold via invoice INV-0007 |
| Clear Adhesive BOPP Packing Tape 48mm (Pack of 6) | `STN-OFF-008` | `sale` | **-18** | 30 | Sold via invoice INV-0007 |
| SmoothFlow Black Ballpoint Pens (Box of 20) | `STN-PEN-002` | `sale` | **-12** | 73 | Sold via invoice INV-0006 |
| Legal Ruled Writing Pad (80 Sheets) | `STN-PAP-007` | `sale` | **-20** | 35 | Sold via invoice INV-0006 |
| Clear L-Shaped Document Folders (Pack of 25) | `STN-OFF-002` | `sale` | **-15** | 45 | Sold via invoice INV-0006 |

---

## 2. Business B — Oakwood Furniture Studio

### Business Profile & Live Financial Snapshot

- **Business Name:** Oakwood Furniture Studio
- **Owner:** Arjun Mehta (`furniture.demo@chitragupta.in`)
- **Category:** Retail / Home and Office Furniture
- **Address:** Plot 42, Road No. 36, Jubilee Hills, Hyderabad, Telangana 500033
- **GSTIN:** `36AAECO4412K1Z9` · **Currency:** `INR`
- **Products:** 50 active products (329 units on hand)
- **Inventory Valuation (Purchase Cost):** ₹3,663,800.00
- **Low-Stock Products:** 5 · **Out-of-Stock Products:** 2
- **Total Outstanding Receivables:** ₹738,972.00 (Overdue: ₹374,060.00)
- **Total Collected All-Time:** ₹782,992.00
- **Estimated Cash on Hand:** ₹1,311,992.00 (Runway: ~162 days)

### Category Breakdown

| Category | Product Count |
| :--- | :---: |
| Home and office furniture accessories | 5 |
| Beds and bedroom furniture | 10 |
| Office furniture | 10 |
| Sofas and seating | 10 |
| Storage and cabinets | 5 |
| Tables and dining furniture | 10 |

### Complete Product Catalogue (50 Products)

| SKU | Product Name | Category | Purchase Cost (₹) | Selling Price (₹) | GST | Unit | Opening Stock | Current Stock | Min Threshold | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `OAK-ACC-001` | Full-Length Wooden Floor Standing Mirror | Home and office furniture accessories | 4,400.00 | 7,200.00 | 18% | unit | 10 | **9** | 3 | `in_stock` |
| `OAK-ACC-002` | Floating Wall Display Shelves (Set of 3) | Home and office furniture accessories | 2,100.00 | 3,600.00 | 18% | set | 15 | **15** | 4 | `in_stock` |
| `OAK-ACC-003` | Handwoven Cotton Living Room Rug (5x7 ft) | Home and office furniture accessories | 3,400.00 | 5,600.00 | 12% | unit | 12 | **10** | 3 | `in_stock` |
| `OAK-ACC-004` | Freestanding Wooden Coat & Hat Stand | Home and office furniture accessories | 2,400.00 | 3,950.00 | 18% | unit | 2 | **2** | 4 | `low_stock` |
| `OAK-ACC-005` | Ergonomic Under-Desk Wooden Footrest | Home and office furniture accessories | 1,450.00 | 2,500.00 | 18% | unit | 16 | **16** | 4 | `in_stock` |
| `OAK-BED-001` | Heritage Solid Teak Wooden Bed (Queen) | Beds and bedroom furniture | 24,000.00 | 37,500.00 | 18% | unit | 7 | **6** | 2 | `in_stock` |
| `OAK-BED-002` | Royal Hydraulic Queen-Size Storage Bed | Beds and bedroom furniture | 29,500.00 | 45,900.00 | 18% | unit | 6 | **4** | 2 | `in_stock` |
| `OAK-BED-003` | Imperial King-Size Upholstered Bed | Beds and bedroom furniture | 36,000.00 | 55,500.00 | 18% | unit | 5 | **4** | 2 | `in_stock` |
| `OAK-BED-004` | Compact Single Solid Wood Bed | Beds and bedroom furniture | 11,500.00 | 18,500.00 | 18% | unit | 10 | **10** | 3 | `in_stock` |
| `OAK-BED-005` | Oakwood 2-Drawer Bedside Table | Beds and bedroom furniture | 4,200.00 | 6,900.00 | 18% | unit | 14 | **10** | 4 | `in_stock` |
| `OAK-BED-006` | 3-Door Sliding Mirror Wardrobe | Beds and bedroom furniture | 31,000.00 | 48,500.00 | 18% | unit | 4 | **3** | 2 | `in_stock` |
| `OAK-BED-007` | 2-Door Hinged Solid Wood Wardrobe | Beds and bedroom furniture | 19,500.00 | 30,500.00 | 18% | unit | 6 | **6** | 2 | `in_stock` |
| `OAK-BED-008` | Dressing Table with Full Mirror & Stool | Beds and bedroom furniture | 11,800.00 | 18,900.00 | 18% | set | 6 | **6** | 2 | `in_stock` |
| `OAK-BED-009` | 5-Drawer Tall Chest of Drawers | Beds and bedroom furniture | 12,500.00 | 19,800.00 | 18% | unit | 2 | **2** | 3 | `low_stock` |
| `OAK-BED-010` | Orthopedic Memory Foam Queen Mattress (8-inch) | Beds and bedroom furniture | 13,200.00 | 21,500.00 | 18% | unit | 9 | **7** | 3 | `in_stock` |
| `OAK-OFF-001` | Apex Pro Executive Office Desk (5 ft) | Office furniture | 16,500.00 | 25,900.00 | 18% | unit | 8 | **5** | 3 | `in_stock` |
| `OAK-OFF-002` | Compact Home Study & Work Desk (4 ft) | Office furniture | 7,800.00 | 12,600.00 | 18% | unit | 12 | **8** | 3 | `in_stock` |
| `OAK-OFF-003` | ErgoMesh High-Back Executive Chair | Office furniture | 9,400.00 | 15,500.00 | 18% | unit | 14 | **14** | 4 | `in_stock` |
| `OAK-OFF-004` | Director Leatherette Boss Swivel Chair | Office furniture | 13,800.00 | 21,900.00 | 18% | unit | 6 | **4** | 2 | `in_stock` |
| `OAK-OFF-005` | 8-Seater Boardroom Conference Table (8 ft) | Office furniture | 38,000.00 | 59,500.00 | 18% | unit | 3 | **2** | 2 | `low_stock` |
| `OAK-OFF-006` | 3-Drawer Lockable Metal Filing Cabinet | Office furniture | 6,200.00 | 9,800.00 | 18% | unit | 11 | **7** | 3 | `in_stock` |
| `OAK-OFF-007` | 4-Drawer Vertical Legal File Cabinet | Office furniture | 10,400.00 | 16,800.00 | 18% | unit | 5 | **5** | 2 | `in_stock` |
| `OAK-OFF-008` | Dual-Motor Electric Standing Desk (5 ft) | Office furniture | 24,500.00 | 38,900.00 | 18% | unit | 0 | **0** | 2 | `out_of_stock` |
| `OAK-OFF-009` | Reception Counter Desk (6 ft) | Office furniture | 27,000.00 | 42,500.00 | 18% | unit | 3 | **2** | 1 | `in_stock` |
| `OAK-OFF-010` | Visitor Cantilever Office Chairs (Set of 2) | Office furniture | 6,900.00 | 11,200.00 | 18% | set | 12 | **9** | 3 | `in_stock` |
| `OAK-SOF-001` | Verona 2-Seater Fabric Sofa | Sofas and seating | 18,500.00 | 28,900.00 | 18% | unit | 8 | **9** | 3 | `in_stock` |
| `OAK-SOF-002` | Verona 3-Seater Fabric Sofa | Sofas and seating | 26,000.00 | 39,500.00 | 18% | unit | 7 | **6** | 3 | `in_stock` |
| `OAK-SOF-003` | Nordic L-Shaped Sectional Sofa (5-Seater) | Sofas and seating | 44,000.00 | 68,500.00 | 18% | unit | 4 | **3** | 2 | `in_stock` |
| `OAK-SOF-004` | CloudRest Single Recliner Chair | Sofas and seating | 14,500.00 | 22,900.00 | 18% | unit | 9 | **7** | 3 | `in_stock` |
| `OAK-SOF-005` | Chesterfield Faux-Leather 3-Seater Sofa | Sofas and seating | 34,000.00 | 52,000.00 | 18% | unit | 3 | **3** | 2 | `in_stock` |
| `OAK-SOF-006` | Accent Wingback Lounge Chair | Sofas and seating | 9,800.00 | 15,800.00 | 18% | unit | 10 | **7** | 3 | `in_stock` |
| `OAK-SOF-007` | Fold-Out Sofa Cum Bed (Queen) | Sofas and seating | 23,500.00 | 36,500.00 | 18% | unit | 5 | **5** | 2 | `in_stock` |
| `OAK-SOF-008` | Upholstered Storage Ottoman Bench | Sofas and seating | 5,200.00 | 8,400.00 | 18% | unit | 11 | **11** | 3 | `in_stock` |
| `OAK-SOF-009` | Solid Sheesham Wood Rocking Chair | Sofas and seating | 8,200.00 | 13,200.00 | 18% | unit | 2 | **2** | 3 | `low_stock` |
| `OAK-SOF-010` | Leatherette Pouffe Footstool (Set of 2) | Sofas and seating | 3,600.00 | 5,900.00 | 18% | set | 0 | **0** | 4 | `out_of_stock` |
| `OAK-STR-001` | Modern Floating TV Unit (up to 65-inch) | Storage and cabinets | 11,200.00 | 17,900.00 | 18% | unit | 8 | **7** | 3 | `in_stock` |
| `OAK-STR-002` | 5-Tier Solid Wood Open Bookshelf | Storage and cabinets | 8,900.00 | 14,500.00 | 18% | unit | 9 | **7** | 3 | `in_stock` |
| `OAK-STR-003` | 3-Door Ventilated Wooden Shoe Rack (18 Pairs) | Storage and cabinets | 6,800.00 | 11,200.00 | 18% | unit | 10 | **9** | 3 | `in_stock` |
| `OAK-STR-004` | Glass-Front Crockery Display Cabinet | Storage and cabinets | 16,500.00 | 26,500.00 | 18% | unit | 2 | **2** | 2 | `low_stock` |
| `OAK-STR-005` | Multi-Purpose Utility Storage Cabinet | Storage and cabinets | 9,600.00 | 15,400.00 | 18% | unit | 7 | **5** | 2 | `in_stock` |
| `OAK-TAB-001` | Solstice 6-Seater Solid Wood Dining Table | Tables and dining furniture | 25,500.00 | 39,800.00 | 18% | unit | 6 | **5** | 2 | `in_stock` |
| `OAK-TAB-002` | Bistro 4-Seater Compact Dining Table | Tables and dining furniture | 14,800.00 | 23,500.00 | 18% | unit | 8 | **6** | 2 | `in_stock` |
| `OAK-TAB-003` | Cushioned Wooden Dining Chairs (Set of 2) | Tables and dining furniture | 6,400.00 | 10,500.00 | 18% | set | 16 | **15** | 4 | `in_stock` |
| `OAK-TAB-004` | Marble-Top Center Coffee Table | Tables and dining furniture | 9,200.00 | 14,900.00 | 18% | unit | 9 | **7** | 3 | `in_stock` |
| `OAK-TAB-005` | Solid Oak Coffee Table with Lower Shelf | Tables and dining furniture | 7,400.00 | 11,900.00 | 18% | unit | 11 | **10** | 3 | `in_stock` |
| `OAK-TAB-006` | Nesting Side Tables (Set of 3) | Tables and dining furniture | 5,100.00 | 8,500.00 | 18% | set | 12 | **12** | 3 | `in_stock` |
| `OAK-TAB-007` | Entryway Console Table with 2 Drawers | Tables and dining furniture | 8,600.00 | 13,800.00 | 18% | unit | 7 | **7** | 2 | `in_stock` |
| `OAK-TAB-008` | 4-Door Dining Sideboard & Crockery Buffet | Tables and dining furniture | 19,200.00 | 29,900.00 | 18% | unit | 3 | **3** | 2 | `in_stock` |
| `OAK-TAB-009` | Industrial Metal & Wood Bar Stools (Set of 2) | Tables and dining furniture | 5,800.00 | 9,400.00 | 18% | set | 10 | **10** | 3 | `in_stock` |
| `OAK-TAB-010` | Round Glass-Top Cafe Table (4-Seater) | Tables and dining furniture | 12,400.00 | 19,500.00 | 18% | unit | 5 | **5** | 2 | `in_stock` |

### Customers (9)

| Customer Name | Email | Phone | Outstanding (₹) | Overdue (₹) |
| :--- | :--- | :--- | :---: | :---: |
| Ananya & Karthik Villa Project | karthik.reddy@gmail.com | +91 97012 30303 | 54,538.00 | 0.00 |
| Banjara Boutique Hotel | gm@banjaraboutique.in | +91 99492 40404 | 213,108.00 | 213,108.00 |
| CyberTowers Startup Labs | facilities@cybertowerslabs.in | +91 98492 20202 | 0.00 | 0.00 |
| Gachibowli Dental & Wellness | clinic@gachibowlidental.in | +91 98483 70707 | 0.00 | 0.00 |
| Jubilee Hills Residency Interiors | projects@jhinteriors.in | +91 98481 10101 | 0.00 | 0.00 |
| Madhapur Design Co-Op | accounts@madhapurdesign.in | +91 91003 90909 | 133,340.00 | 0.00 |
| Manikonda Modern Homes | buyers@manikondahomes.in | +91 90002 60606 | 94,990.00 | 0.00 |
| Secunderabad Heritage Club | secretary@secheritageclub.org | +91 94402 80808 | 160,952.00 | 160,952.00 |
| Telangana FinServe Advisory | admin@tsfinserve.in | +91 98662 50505 | 82,044.00 | 0.00 |

### Invoices (11)

| Invoice # | Customer | Lifecycle | Status | Total (₹) | Paid (₹) | Outstanding (₹) | Due Date |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `INV-0022` | CyberTowers Startup Labs | draft | `draft` | 57,348.00 | 0.00 | 57,348.00 | 2026-12-07 |
| `INV-0021` | Jubilee Hills Residency Interiors | draft | `draft` | 75,284.00 | 0.00 | 75,284.00 | 2026-12-07 |
| `INV-0020` | Madhapur Design Co-Op | sent | `pending` | 133,340.00 | 0.00 | 133,340.00 | 2026-12-05 |
| `INV-0019` | Manikonda Modern Homes | sent | `pending` | 94,990.00 | 0.00 | 94,990.00 | 2026-11-26 |
| `INV-0016` | Telangana FinServe Advisory | sent | `partially_paid` | 172,044.00 | 90,000.00 | 82,044.00 | 2026-11-30 |
| `INV-0015` | Ananya & Karthik Villa Project | sent | `partially_paid` | 199,538.00 | 145,000.00 | 54,538.00 | 2026-11-29 |
| `INV-0014` | Gachibowli Dental & Wellness | sent | `paid` | 117,764.00 | 117,764.00 | 0.00 | 2026-11-15 |
| `INV-0018` | Secunderabad Heritage Club | sent | `overdue` | 160,952.00 | 0.00 | 160,952.00 | 2026-11-13 |
| `INV-0013` | CyberTowers Startup Labs | sent | `paid` | 247,682.00 | 247,682.00 | 0.00 | 2026-11-07 |
| `INV-0017` | Banjara Boutique Hotel | sent | `overdue` | 213,108.00 | 0.00 | 213,108.00 | 2026-11-04 |
| `INV-0012` | Jubilee Hills Residency Interiors | sent | `paid` | 182,546.00 | 182,546.00 | 0.00 | 2026-10-30 |

### Payments (6)

| Invoice # | Customer | Amount (₹) | Method | Reference | Date |
| :--- | :--- | :---: | :---: | :--- | :---: |
| `INV-0015` | Ananya & Karthik Villa Project | 65,000.00 | bank_transfer | NEFT/AKVP/002 | 2026-11-17 |
| `INV-0016` | Telangana FinServe Advisory | 90,000.00 | bank_transfer | RTGS/TSF/221 | 2026-11-15 |
| `INV-0014` | Gachibowli Dental & Wellness | 117,764.00 | upi | UPI/GDW/6612 | 2026-11-12 |
| `INV-0015` | Ananya & Karthik Villa Project | 80,000.00 | bank_transfer | RTGS/AKVP/001 | 2026-11-07 |
| `INV-0013` | CyberTowers Startup Labs | 247,682.00 | bank_transfer | NEFT/CTSL/4420 | 2026-11-05 |
| `INV-0012` | Jubilee Hills Residency Interiors | 182,546.00 | bank_transfer | RTGS/JHRI/9901 | 2026-10-28 |

### Scheduled Expenses (4)

| Expense | Category | Amount (₹) | Type |
| :--- | :--- | :---: | :---: |
| Carpenters, Polishers & Showroom Payroll | Payroll | 125,000.00 | Recurring (Day 1) |
| Jubilee Hills Showroom & Warehouse Lease | Rent | 95,000.00 | Recurring (Day 5) |
| White-Glove Furniture Delivery Truck Service | Logistics | 18,500.00 | One-off (2026-11-27) |
| Showroom Lighting, AC & ERP Subscriptions | Utilities | 22,000.00 | Recurring (Day 12) |

### Business Notes (5)

- **Banjara Boutique Hotel Payment Follow-up** [Customers] *(Pinned)*: Suite refurbishment invoice is 18 days overdue. Speak with GM regarding NEFT release before next room batch.
- **Workshop Production & Out-of-Stock Priority** [Operations] *(Pinned)*: Dual-Motor Electric Standing Desk (OAK-OFF-008) and Leatherette Pouffe Footstool (OAK-SOF-010) are out of stock. Confirm motor shipment ETA.
- **Showroom Floor Refresh Ideas** [Ideas]: Create a dedicated Ergonomic Home Office corner showcasing Apex Pro Desk + ErgoMesh Chair + Under-Desk Footrest.
- **White-Glove Delivery Schedule** [Operations]: Coordinate elevator booking for Ananya & Karthik Villa Project once final balance clears.
- **Timber & Upholstery Vendor Rate Lock** [Suppliers]: Locked Grade-A Burma teak and walnut veneer pricing with Telangana Timber Mart through Q2.

### Inventory Scenarios & Recent Stock Movements

| Product | SKU | Type | Change | Balance After | Reason |
| :--- | :--- | :---: | :---: | :---: | :--- |
| 5-Tier Solid Wood Open Bookshelf | `OAK-STR-002` | `sale` | **-2** | 7 | Sold via invoice INV-0020 |
| Visitor Cantilever Office Chairs (Set of 2) | `OAK-OFF-010` | `sale` | **-3** | 9 | Sold via invoice INV-0020 |
| Compact Home Study & Work Desk (4 ft) | `OAK-OFF-002` | `sale` | **-4** | 8 | Sold via invoice INV-0020 |
| 3-Door Ventilated Wooden Shoe Rack (18 Pairs) | `OAK-STR-003` | `sale` | **-1** | 9 | Sold via invoice INV-0019 |
| Solid Oak Coffee Table with Lower Shelf | `OAK-TAB-005` | `sale` | **-1** | 10 | Sold via invoice INV-0019 |
| Modern Floating TV Unit (up to 65-inch) | `OAK-STR-001` | `sale` | **-1** | 7 | Sold via invoice INV-0019 |
| Verona 3-Seater Fabric Sofa | `OAK-SOF-002` | `sale` | **-1** | 6 | Sold via invoice INV-0019 |
| Accent Wingback Lounge Chair | `OAK-SOF-006` | `sale` | **-3** | 7 | Sold via invoice INV-0018 |
| Cushioned Wooden Dining Chairs (Set of 2) | `OAK-TAB-003` | `sale` | **-4** | 15 | Sold via invoice INV-0018 |
| Bistro 4-Seater Compact Dining Table | `OAK-TAB-002` | `sale` | **-2** | 6 | Sold via invoice INV-0018 |
| CloudRest Single Recliner Chair | `OAK-SOF-004` | `sale` | **-2** | 7 | Sold via invoice INV-0017 |
| Orthopedic Memory Foam Queen Mattress (8-inch) | `OAK-BED-010` | `sale` | **-2** | 7 | Sold via invoice INV-0017 |
| Royal Hydraulic Queen-Size Storage Bed | `OAK-BED-002` | `sale` | **-2** | 4 | Sold via invoice INV-0017 |
| Reception Counter Desk (6 ft) | `OAK-OFF-009` | `sale` | **-1** | 2 | Sold via invoice INV-0016 |
| Director Leatherette Boss Swivel Chair | `OAK-OFF-004` | `sale` | **-2** | 4 | Sold via invoice INV-0016 |

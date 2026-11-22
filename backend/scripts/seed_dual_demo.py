"""Controlled, repeatable, idempotent seeding script for TWO independent Chitragupta
demonstration businesses (100 products total: 50 Stationery + 50 Furniture).

Safety guarantees:
- NEVER runs automatically on server startup.
- NEVER touches, modifies, or deletes any real user accounts or businesses.
- Only manages `demo@chitragupta.in` and `furniture.demo@chitragupta.in`.
- Does NOT hardcode plaintext passwords in source code; pass via env vars or CLI flags.

Usage (from project root):
    .\\backend\\.venv\\Scripts\\python.exe backend\\scripts\\seed_dual_demo.py ^
        --stationery-password "<PASSWORD_A>" ^
        --furniture-password "<PASSWORD_B>" ^
        --reset-demo --write-docs
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import os
from pathlib import Path
import sys

# Ensure backend/ is importable and cwd is backend/ so relative SQLite path always targets backend/instance/chitragupta.db
BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if __name__ == "__main__":
    os.chdir(BACKEND_DIR)

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.security import hash_password
from app.database.init_db import create_all_tables
from app.database.session import SessionLocal
from app.models.ai_conversation import AiConversation
from app.models.business import Business
from app.models.customer import Customer
from app.models.expense import Expense
from app.models.inventory_movement import InventoryMovement
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.note import BusinessNote
from app.models.payment import Payment
from app.models.product import Product
from app.models.setting import Setting
from app.models.user import User, UserSession
from app.schemas.customer import CustomerIn
from app.schemas.expense import ExpenseIn
from app.schemas.invoice import InvoiceIn, ItemIn
from app.schemas.note import NoteIn
from app.schemas.payment import PaymentCreate
from app.schemas.product import ProductIn, StockAdjustIn
from app.services import (
    customer_service,
    dashboard_service,
    expense_service,
    inventory_service,
    invoice_service,
    note_service,
    payment_service,
)
from app.utils.money import paise_to_rupees_text

STATIONERY_EMAIL = "demo@chitragupta.in"
FURNITURE_EMAIL = "furniture.demo@chitragupta.in"

# ---------------------------------------------------------------------------
# BUSINESS A — URBAN STATIONERY & OFFICE SUPPLIES (50 Products)
# Format: (sku, name, category, description, cost, price, gst, unit, opening_stock, min_thresh)
# ---------------------------------------------------------------------------
STATIONERY_PRODUCTS: list[tuple] = [
    # Paper and notebooks — 10 products
    ("STN-PAP-001", "A4 Copier Paper 75 GSM (500 Sheets)", "Paper and notebooks", "Bright white multi-purpose A4 printing paper ream.", "235.00", "320.00", 12, "ream", 120, 25),
    ("STN-PAP-002", "A4 Copier Paper 80 GSM Premium Ream", "Paper and notebooks", "High-opacity 80 GSM A4 paper for duplex laser printing.", "275.00", "370.00", 12, "ream", 75, 20),
    ("STN-PAP-003", "A3 Copier Paper 80 GSM (500 Sheets)", "Paper and notebooks", "Wide-format A3 bond paper for architectural and chart prints.", "520.00", "690.00", 12, "ream", 24, 10),
    ("STN-PAP-004", "A5 Hardcover Ruled Notebook (192 Pages)", "Paper and notebooks", "Thread-bound 90 GSM ivory ruled business journal.", "110.00", "185.00", 12, "pcs", 90, 20),
    ("STN-PAP-005", "Spiral Conference Notebook A4 (200 Pages)", "Paper and notebooks", "Micro-perforated spiral pad with poly cover.", "78.00", "130.00", 12, "pcs", 80, 18),
    ("STN-PAP-006", "Sticky Notes Cube 3x3 Neon (400 Sheets)", "Paper and notebooks", "Repositionable neon adhesive note block for desks.", "58.00", "95.00", 12, "pack", 65, 15),
    ("STN-PAP-007", "Legal Ruled Writing Pad (80 Sheets)", "Paper and notebooks", "Top-bound canary yellow legal note pad.", "42.00", "75.00", 12, "pcs", 55, 15),
    ("STN-PAP-008", "Ledger Register Book 300 Pages (Hardbound)", "Paper and notebooks", "Numbered accounts register with durable cloth spine.", "145.00", "240.00", 12, "pcs", 12, 15),
    ("STN-PAP-009", "Glossy Photo Paper A4 180 GSM (50 Sheets)", "Paper and notebooks", "Quick-dry inkjet glossy photo sheets for brochures.", "195.00", "310.00", 12, "pack", 18, 10),
    ("STN-PAP-010", "Thermal Billing Paper Rolls 80mm (Pack of 10)", "Paper and notebooks", "BPA-free POS receipt rolls for retail counters.", "310.00", "450.00", 18, "pack", 0, 12),

    # Pens and writing supplies — 10 products
    ("STN-PEN-001", "SmoothFlow Blue Ballpoint Pens (Box of 20)", "Pens and writing supplies", "0.7mm low-viscosity ink everyday office ball pens.", "115.00", "180.00", 12, "box", 110, 25),
    ("STN-PEN-002", "SmoothFlow Black Ballpoint Pens (Box of 20)", "Pens and writing supplies", "Smudge-free black ink ballpoint pens for forms.", "115.00", "180.00", 12, "box", 85, 20),
    ("STN-PEN-003", "GelPro 0.5mm Waterproof Gel Pens (Pack of 10)", "Pens and writing supplies", "Precision needle-tip gel pens with rubber grip.", "95.00", "160.00", 12, "pack", 95, 20),
    ("STN-PEN-004", "Executive Metal Rollerball Pen (Gift Box)", "Pens and writing supplies", "Brushed matte-black signature pen with refill.", "210.00", "380.00", 18, "pcs", 30, 8),
    ("STN-PEN-005", "HB Graphite Pencils with Eraser (Box of 12)", "Pens and writing supplies", "Break-resistant dark lead hexagonal wooden pencils.", "38.00", "65.00", 12, "box", 130, 25),
    ("STN-PEN-006", "Mechanical Pencil 0.7mm with Lead Tube", "Pens and writing supplies", "Refillable drafting pencil with cushioned grip.", "45.00", "85.00", 12, "pcs", 60, 15),
    ("STN-PEN-007", "Chisel-Tip Highlighter Set (Pack of 5)", "Pens and writing supplies", "Fluorescent yellow, pink, green, orange, and blue set.", "72.00", "125.00", 12, "set", 70, 15),
    ("STN-PEN-008", "Whiteboard Dry-Erase Markers (Pack of 4)", "Pens and writing supplies", "Low-odor bullet-tip markers for conference boards.", "68.00", "120.00", 18, "pack", 14, 18),
    ("STN-PEN-009", "Permanent Fine-Tip Markers Black (Pack of 10)", "Pens and writing supplies", "Waterproof ink markers for cartons, CDs, and labels.", "125.00", "210.00", 18, "pack", 45, 12),
    ("STN-PEN-010", "Correction Tape Roller 5mm x 8m (Pack of 3)", "Pens and writing supplies", "Instant dry white correction tape dispenser.", "84.00", "145.00", 18, "pack", 50, 12),

    # Office supplies — 10 products
    ("STN-OFF-001", "Heavy-Duty Lever Arch Box File (A4)", "Office supplies", "Laminated board arch file with finger ring and label.", "88.00", "145.00", 18, "pcs", 85, 20),
    ("STN-OFF-002", "Clear L-Shaped Document Folders (Pack of 25)", "Office supplies", "Transparent polypropylene sleeves for reports.", "130.00", "215.00", 18, "pack", 60, 15),
    ("STN-OFF-003", "Expanding 12-Pocket Accordion File Folder", "Office supplies", "Indexed portable organizer with elastic closure.", "165.00", "275.00", 18, "pcs", 38, 10),
    ("STN-OFF-004", "Metal Binder Clips 32mm (Box of 12)", "Office supplies", "Tempered steel fold-back clips for thick stacks.", "42.00", "75.00", 18, "box", 100, 20),
    ("STN-OFF-005", "Stainless Steel Paper Clips 28mm (Box of 100)", "Office supplies", "Rust-resistant smooth wire paper clips.", "24.00", "45.00", 18, "box", 140, 25),
    ("STN-OFF-006", "Standard No. 10 Staples (Pack of 10 Boxes)", "Office supplies", "Galvanized 1000-pin boxes for compact staplers.", "95.00", "160.00", 18, "pack", 70, 15),
    ("STN-OFF-007", "24/6 Office Staples (Pack of 10 Boxes)", "Office supplies", "Standard heavy-office stapler pins.", "145.00", "235.00", 18, "pack", 55, 15),
    ("STN-OFF-008", "Clear Adhesive BOPP Packing Tape 48mm (Pack of 6)", "Office supplies", "High-tack 65m transparent dispatch tape rolls.", "210.00", "330.00", 18, "pack", 48, 12),
    ("STN-OFF-009", "Glue Stick 21g Non-Toxic (Pack of 5)", "Office supplies", "Washable smooth-glide paper adhesive sticks.", "110.00", "185.00", 18, "pack", 52, 12),
    ("STN-OFF-010", "Kraft Brown A4 Document Envelopes (Pack of 50)", "Office supplies", "100 GSM peel-and-seal courier envelopes.", "150.00", "245.00", 12, "pack", 10, 15),

    # Office equipment — 10 products
    ("STN-EQP-001", "12-Digit Dual-Power Desktop Calculator", "Office equipment", "Large angled LCD check-and-correct GST calculator.", "295.00", "490.00", 18, "pcs", 36, 10),
    ("STN-EQP-002", "Heavy-Duty Metal Desktop Stapler (24/6)", "Office equipment", "All-steel body stapler for up to 30 sheets.", "185.00", "320.00", 18, "pcs", 42, 10),
    ("STN-EQP-003", "Two-Hole Heavy Paper Punch (30 Sheets)", "Office equipment", "Precision steel punch with adjustable paper guide.", "175.00", "295.00", 18, "pcs", 32, 8),
    ("STN-EQP-004", "Stainless Steel Office Scissors 21cm", "Office equipment", "Ergonomic soft-grip multi-purpose desk scissors.", "65.00", "115.00", 18, "pcs", 58, 15),
    ("STN-EQP-005", "A4 Thermal Laminating Machine (Hot & Cold)", "Office equipment", "Quick warm-up 2-roller desktop laminator.", "1450.00", "2250.00", 18, "pcs", 9, 4),
    ("STN-EQP-006", "Cross-Cut Personal Paper Shredder (8-Sheet)", "Office equipment", "15-litre bin security shredder for office desks.", "2850.00", "4250.00", 18, "pcs", 5, 3),
    ("STN-EQP-007", "A4 Guillotine Paper Trimmer (12-Sheet)", "Office equipment", "Hardened steel blade cutter with safety guard.", "890.00", "1450.00", 18, "pcs", 10, 4),
    ("STN-EQP-008", "Magnetic Aluminum Whiteboard 3x2 ft", "Office equipment", "Melamine dry-erase board with marker tray.", "920.00", "1490.00", 18, "pcs", 3, 5),
    ("STN-EQP-009", "Weighted Desktop Tape Dispenser (24mm)", "Office equipment", "Anti-skid weighted base with serrated steel blade.", "120.00", "210.00", 18, "pcs", 28, 8),
    ("STN-EQP-010", "Self-Inking Date & Received Stamp", "Office equipment", "Adjustable 10-year date band with dual-color pad.", "160.00", "280.00", 18, "pcs", 0, 6),

    # Art and stationery accessories — 10 products
    ("STN-ART-001", "A3 Spiral Sketchbook 140 GSM (50 Sheets)", "Art and stationery accessories", "Acid-free cartridge drawing sheets for charcoal and ink.", "165.00", "280.00", 12, "pcs", 40, 10),
    ("STN-ART-002", "Artist Watercolor Cake Set (24 Shades)", "Art and stationery accessories", "High-pigment travel watercolor palette with brush.", "190.00", "340.00", 12, "set", 26, 8),
    ("STN-ART-003", "Acrylic Paint Tube Set 12ml (18 Colors)", "Art and stationery accessories", "Fast-drying satin acrylic paints for canvas and wood.", "265.00", "440.00", 18, "set", 22, 6),
    ("STN-ART-004", "Oil Pastels Artist Box (36 Shades)", "Art and stationery accessories", "Rich blendable pastel sticks in hard storage case.", "145.00", "250.00", 12, "set", 34, 8),
    ("STN-ART-005", "Fine Synthetic Brush Set (10 Assorted Sizes)", "Art and stationery accessories", "Round, flat, and filbert brushes for detail painting.", "135.00", "240.00", 12, "set", 30, 8),
    ("STN-ART-006", "Mathematical Geometry & Compass Box", "Art and stationery accessories", "Die-cast metal compass, divider, protractor, and set squares.", "92.00", "165.00", 12, "set", 48, 12),
    ("STN-ART-007", "Stainless Steel 30cm Measuring Ruler", "Art and stationery accessories", "Etched metric and imperial markings with cork backing.", "35.00", "65.00", 18, "pcs", 75, 15),
    ("STN-ART-008", "Mesh Metal 6-Compartment Desk Organizer", "Art and stationery accessories", "Powder-coated black wire caddy for pens and cards.", "195.00", "340.00", 18, "pcs", 24, 8),
    ("STN-ART-009", "A3 Self-Healing Cutting Mat (Green)", "Art and stationery accessories", "3mm 5-ply grid mat for precision craft and design cutting.", "285.00", "480.00", 18, "pcs", 4, 6),
    ("STN-ART-010", "Heavy-Duty Snap-Off Craft Utility Knife", "Art and stationery accessories", "18mm auto-lock blade cutter with 5 spare blades.", "58.00", "105.00", 18, "pcs", 44, 10),
]

# ---------------------------------------------------------------------------
# BUSINESS B — OAKWOOD FURNITURE STUDIO (50 Products)
# Format: (sku, name, category, description, cost, price, gst, unit, opening_stock, min_thresh)
# ---------------------------------------------------------------------------
FURNITURE_PRODUCTS: list[tuple] = [
    # Sofas and seating — 10 products
    ("OAK-SOF-001", "Verona 2-Seater Fabric Sofa", "Sofas and seating", "Kiln-dried solid teak frame with high-density foam in warm oatmeal weave.", "18500.00", "28900.00", 18, "unit", 8, 3),
    ("OAK-SOF-002", "Verona 3-Seater Fabric Sofa", "Sofas and seating", "Spacious 3-seater living room sofa with removable cushion covers.", "26000.00", "39500.00", 18, "unit", 7, 3),
    ("OAK-SOF-003", "Nordic L-Shaped Sectional Sofa (5-Seater)", "Sofas and seating", "Left-aligned modular corner lounger with solid oak legs.", "44000.00", "68500.00", 18, "unit", 4, 2),
    ("OAK-SOF-004", "CloudRest Single Recliner Chair", "Sofas and seating", "Manual push-back ergonomic recliner in charcoal linen.", "14500.00", "22900.00", 18, "unit", 9, 3),
    ("OAK-SOF-005", "Chesterfield Faux-Leather 3-Seater Sofa", "Sofas and seating", "Deep-tufted cognac upholstery with rolled arms.", "34000.00", "52000.00", 18, "unit", 3, 2),
    ("OAK-SOF-006", "Accent Wingback Lounge Chair", "Sofas and seating", "High-back reading armchair in emerald velvet.", "9800.00", "15800.00", 18, "unit", 10, 3),
    ("OAK-SOF-007", "Fold-Out Sofa Cum Bed (Queen)", "Sofas and seating", "Dual-purpose guest sleeper sofa with hidden bedding box.", "23500.00", "36500.00", 18, "unit", 5, 2),
    ("OAK-SOF-008", "Upholstered Storage Ottoman Bench", "Sofas and seating", "Lift-top tufted bench ideal for living rooms or bedrooms.", "5200.00", "8400.00", 18, "unit", 11, 3),
    ("OAK-SOF-009", "Solid Sheesham Wood Rocking Chair", "Sofas and seating", "Classic slatted-back rocking chair with seat cushion.", "8200.00", "13200.00", 18, "unit", 2, 3),
    ("OAK-SOF-010", "Leatherette Pouffe Footstool (Set of 2)", "Sofas and seating", "Compact cushioned round stools with stitched trim.", "3600.00", "5900.00", 18, "set", 0, 4),

    # Beds and bedroom furniture — 10 products
    ("OAK-BED-001", "Heritage Solid Teak Wooden Bed (Queen)", "Beds and bedroom furniture", "Hand-finished honey teak platform bed with slatted headboard.", "24000.00", "37500.00", 18, "unit", 7, 2),
    ("OAK-BED-002", "Royal Hydraulic Queen-Size Storage Bed", "Beds and bedroom furniture", "Engineered walnut bed with full hydraulic under-bed lift.", "29500.00", "45900.00", 18, "unit", 6, 2),
    ("OAK-BED-003", "Imperial King-Size Upholstered Bed", "Beds and bedroom furniture", "Padded linen headboard king bed with reinforced steel slats.", "36000.00", "55500.00", 18, "unit", 5, 2),
    ("OAK-BED-004", "Compact Single Solid Wood Bed", "Beds and bedroom furniture", "Sturdy single bed ideal for kids or guest rooms.", "11500.00", "18500.00", 18, "unit", 10, 3),
    ("OAK-BED-005", "Oakwood 2-Drawer Bedside Table", "Beds and bedroom furniture", "Soft-close nightstand with brushed brass handles.", "4200.00", "6900.00", 18, "unit", 14, 4),
    ("OAK-BED-006", "3-Door Sliding Mirror Wardrobe", "Beds and bedroom furniture", "Full-height bedroom wardrobe with hanging rail and shelves.", "31000.00", "48500.00", 18, "unit", 4, 2),
    ("OAK-BED-007", "2-Door Hinged Solid Wood Wardrobe", "Beds and bedroom furniture", "Compact teak-finish wardrobe with lockable drawer.", "19500.00", "30500.00", 18, "unit", 6, 2),
    ("OAK-BED-008", "Dressing Table with Full Mirror & Stool", "Beds and bedroom furniture", "Vanity unit with 4 organizer drawers and cushioned stool.", "11800.00", "18900.00", 18, "set", 6, 2),
    ("OAK-BED-009", "5-Drawer Tall Chest of Drawers", "Beds and bedroom furniture", "Vertical bedroom dresser with smooth ball-bearing runners.", "12500.00", "19800.00", 18, "unit", 2, 3),
    ("OAK-BED-010", "Orthopedic Memory Foam Queen Mattress (8-inch)", "Beds and bedroom furniture", "Dual-layer cool-gel memory foam and high-resilience base.", "13200.00", "21500.00", 18, "unit", 9, 3),

    # Tables and dining furniture — 10 products
    ("OAK-TAB-001", "Solstice 6-Seater Solid Wood Dining Table", "Tables and dining furniture", "Spacious rectangular walnut dining table with tapered legs.", "25500.00", "39800.00", 18, "unit", 6, 2),
    ("OAK-TAB-002", "Bistro 4-Seater Compact Dining Table", "Tables and dining furniture", "Space-saving oak dining table for urban apartments.", "14800.00", "23500.00", 18, "unit", 8, 2),
    ("OAK-TAB-003", "Cushioned Wooden Dining Chairs (Set of 2)", "Tables and dining furniture", "Curved ergonomic backrest dining chairs in teak finish.", "6400.00", "10500.00", 18, "set", 16, 4),
    ("OAK-TAB-004", "Marble-Top Center Coffee Table", "Tables and dining furniture", "White veined faux-marble top with matte gold steel base.", "9200.00", "14900.00", 18, "unit", 9, 3),
    ("OAK-TAB-005", "Solid Oak Coffee Table with Lower Shelf", "Tables and dining furniture", "Warm natural oak center table with open magazine tier.", "7400.00", "11900.00", 18, "unit", 11, 3),
    ("OAK-TAB-006", "Nesting Side Tables (Set of 3)", "Tables and dining furniture", "Stackable round accent tables in walnut veneer.", "5100.00", "8500.00", 18, "set", 12, 3),
    ("OAK-TAB-007", "Entryway Console Table with 2 Drawers", "Tables and dining furniture", "Slim hallway table for keys, lamps, and decor.", "8600.00", "13800.00", 18, "unit", 7, 2),
    ("OAK-TAB-008", "4-Door Dining Sideboard & Crockery Buffet", "Tables and dining furniture", "Storage credenza with adjustable glass and plate shelves.", "19200.00", "29900.00", 18, "unit", 3, 2),
    ("OAK-TAB-009", "Industrial Metal & Wood Bar Stools (Set of 2)", "Tables and dining furniture", "Counter-height swivel stools with footrest ring.", "5800.00", "9400.00", 18, "set", 10, 3),
    ("OAK-TAB-010", "Round Glass-Top Cafe Table (4-Seater)", "Tables and dining furniture", "10mm tempered glass top on crossed ash-wood legs.", "12400.00", "19500.00", 18, "unit", 5, 2),

    # Storage and cabinets — 5 products
    ("OAK-STR-001", "Modern Floating TV Unit (up to 65-inch)", "Storage and cabinets", "Walnut and matte-white entertainment console with cable ports.", "11200.00", "17900.00", 18, "unit", 8, 3),
    ("OAK-STR-002", "5-Tier Solid Wood Open Bookshelf", "Storage and cabinets", "Tall display bookcase with anti-tip wall anchor.", "8900.00", "14500.00", 18, "unit", 9, 3),
    ("OAK-STR-003", "3-Door Ventilated Wooden Shoe Rack (18 Pairs)", "Storage and cabinets", "Louvered-door entryway shoe cabinet with top drawer.", "6800.00", "11200.00", 18, "unit", 10, 3),
    ("OAK-STR-004", "Glass-Front Crockery Display Cabinet", "Storage and cabinets", "Tempered glass doors with 4 interior display shelves.", "16500.00", "26500.00", 18, "unit", 2, 2),
    ("OAK-STR-005", "Multi-Purpose Utility Storage Cabinet", "Storage and cabinets", "Lockable 2-door engineered wood storage cupboard.", "9600.00", "15400.00", 18, "unit", 7, 2),

    # Home and office furniture accessories — 5 products
    ("OAK-ACC-001", "Full-Length Wooden Floor Standing Mirror", "Home and office furniture accessories", "Minimalist oak-framed tiltable dressing mirror.", "4400.00", "7200.00", 18, "unit", 10, 3),
    ("OAK-ACC-002", "Floating Wall Display Shelves (Set of 3)", "Home and office furniture accessories", "Concealed-bracket walnut shelves for books and frames.", "2100.00", "3600.00", 18, "set", 15, 4),
    ("OAK-ACC-003", "Handwoven Cotton Living Room Rug (5x7 ft)", "Home and office furniture accessories", "Geometric neutral flatweave area rug.", "3400.00", "5600.00", 12, "unit", 12, 3),
    ("OAK-ACC-004", "Freestanding Wooden Coat & Hat Stand", "Home and office furniture accessories", "8-hook tripod coat tree in walnut polish.", "2400.00", "3950.00", 18, "unit", 2, 4),
    ("OAK-ACC-005", "Ergonomic Under-Desk Wooden Footrest", "Home and office furniture accessories", "Angled non-slip footrest for long work sessions.", "1450.00", "2500.00", 18, "unit", 16, 4),

    # Office furniture — 10 products
    ("OAK-OFF-001", "Apex Pro Executive Office Desk (5 ft)", "Office furniture", "Walnut veneer work desk with side return and grommets.", "16500.00", "25900.00", 18, "unit", 8, 3),
    ("OAK-OFF-002", "Compact Home Study & Work Desk (4 ft)", "Office furniture", "Steel-frame oak-top desk with keyboard shelf.", "7800.00", "12600.00", 18, "unit", 12, 3),
    ("OAK-OFF-003", "ErgoMesh High-Back Executive Chair", "Office furniture", "Breathable mesh chair with adjustable lumbar and headrest.", "9400.00", "15500.00", 18, "unit", 14, 4),
    ("OAK-OFF-004", "Director Leatherette Boss Swivel Chair", "Office furniture", "High-back cushioned executive chair with chrome base.", "13800.00", "21900.00", 18, "unit", 6, 2),
    ("OAK-OFF-005", "8-Seater Boardroom Conference Table (8 ft)", "Office furniture", "Cable-managed walnut conference table with steel legs.", "38000.00", "59500.00", 18, "unit", 3, 2),
    ("OAK-OFF-006", "3-Drawer Lockable Metal Filing Cabinet", "Office furniture", "Powder-coated under-desk mobile pedestal with casters.", "6200.00", "9800.00", 18, "unit", 11, 3),
    ("OAK-OFF-007", "4-Drawer Vertical Legal File Cabinet", "Office furniture", "Heavy-gauge steel archive cabinet with anti-tilt lock.", "10400.00", "16800.00", 18, "unit", 5, 2),
    ("OAK-OFF-008", "Dual-Motor Electric Standing Desk (5 ft)", "Office furniture", "Height-adjustable sit-stand desk with 4 memory presets.", "24500.00", "38900.00", 18, "unit", 0, 2),
    ("OAK-OFF-009", "Reception Counter Desk (6 ft)", "Office furniture", "L-shaped front-office welcome desk with LED accent.", "27000.00", "42500.00", 18, "unit", 3, 1),
    ("OAK-OFF-010", "Visitor Cantilever Office Chairs (Set of 2)", "Office furniture", "Chrome-frame padded guest chairs for cabins and lobbies.", "6900.00", "11200.00", 18, "set", 12, 3),
]

STATIONERY_CUSTOMERS = [
    ("Deccan Tech Park Admin", "procurement@deccantechpark.in", "+91 98480 11223", "HITEC City, Madhapur, Hyderabad, Telangana 500081", "Monthly corporate stationery account."),
    ("Hyderabad Public Coaching Centre", "accounts@hpcoaching.edu.in", "+91 98490 22334", "Ameerpet Main Road, Hyderabad, Telangana 500016", "Bulk paper and exam stationery buyer."),
    ("Charminar Print & Copy Hub", "orders@charminarprint.in", "+91 97010 33445", "Abids Circle, Hyderabad, Telangana 500001", "Weekly A4/A3 ream replenishment."),
    ("Vignan Architecture Studio", "studio@vignanarch.in", "+91 99490 44556", "Banjara Hills Road No. 12, Hyderabad, Telangana 500034", "Orders sketchbooks, A3 paper, and cutting mats."),
    ("CarePlus Diagnostics Lab", "admin@careplusdiag.in", "+91 98660 55667", "Somajiguda, Hyderabad, Telangana 500082", "Files, thermal rolls, and office supplies."),
    ("Kukatpally Legal Associates", "office@kplegal.in", "+91 90001 66778", "KPHB Phase 3, Kukatpally, Hyderabad, Telangana 500072", "Legal pads, arch files, and envelopes."),
    ("Secunderabad Logistics Corp", "billing@seclogistics.in", "+91 98482 77889", "Paradise Circle, Secunderabad, Telangana 500003", "Packing tapes, markers, and dispatch registers."),
    ("Nizam College Fine Arts Dept", "artsdept@nizamcollege.edu.in", "+91 94401 88990", "Basheerbagh, Hyderabad, Telangana 500001", "Art sets, brushes, and drawing supplies."),
    ("Gachibowli CoWork Spaces", "ops@gachibowlicowork.in", "+91 91002 99001", "Financial District, Gachibowli, Hyderabad, Telangana 500032", "Whiteboards, markers, shredders, and pantry stationery."),
]

FURNITURE_CUSTOMERS = [
    ("Jubilee Hills Residency Interiors", "projects@jhinteriors.in", "+91 98481 10101", "Road No. 36, Jubilee Hills, Hyderabad, Telangana 500033", "Turnkey luxury residential interior partner."),
    ("CyberTowers Startup Labs", "facilities@cybertowerslabs.in", "+91 98492 20202", "Kondapur, Hyderabad, Telangana 500084", "Orders desks, ergonomic chairs, and conference tables."),
    ("Ananya & Karthik Villa Project", "karthik.reddy@gmail.com", "+91 97012 30303", "Kokapet, Gandipet, Hyderabad, Telangana 500075", "Full 4BHK custom home furniture order."),
    ("Banjara Boutique Hotel", "gm@banjaraboutique.in", "+91 99492 40404", "Banjara Hills Road No. 1, Hyderabad, Telangana 500034", "Bedroom sets, mattresses, and lobby seating."),
    ("Telangana FinServe Advisory", "admin@tsfinserve.in", "+91 98662 50505", "Begumpet, Hyderabad, Telangana 500016", "Executive office cabins and reception counter."),
    ("Manikonda Modern Homes", "buyers@manikondahomes.in", "+91 90002 60606", "Manikonda Jagir, Hyderabad, Telangana 500089", "Model flat staging furniture."),
    ("Gachibowli Dental & Wellness", "clinic@gachibowlidental.in", "+91 98483 70707", "Gachibowli, Hyderabad, Telangana 500032", "Waiting lounge sofas and storage cabinets."),
    ("Secunderabad Heritage Club", "secretary@secheritageclub.org", "+91 94402 80808", "Marredpally, Secunderabad, Telangana 500026", "Dining tables, chairs, and lounge seating."),
    ("Madhapur Design Co-Op", "accounts@madhapurdesign.in", "+91 91003 90909", "Madhapur, Hyderabad, Telangana 500081", "Recurring commercial office fit-out client."),
]


def _delete_demo_user_if_exists(db: Session, email: str) -> None:
    user = db.scalar(select(User).where(User.email == email.lower()).limit(1))
    if user is None:
        return
    businesses = list(db.scalars(select(Business).where(Business.owner_user_id == user.id)).all())
    for biz in businesses:
        inv_ids = list(db.scalars(select(Invoice.id).where(Invoice.business_id == biz.id)).all())
        db.query(Payment).filter(Payment.business_id == biz.id).delete()
        db.query(InventoryMovement).filter(InventoryMovement.business_id == biz.id).delete()
        if inv_ids:
            db.query(InvoiceItem).filter(InvoiceItem.invoice_id.in_(inv_ids)).delete(synchronize_session=False)
        db.query(Invoice).filter(Invoice.business_id == biz.id).delete()
        db.query(Customer).filter(Customer.business_id == biz.id).delete()
        db.query(Product).filter(Product.business_id == biz.id).delete()
        db.query(Expense).filter(Expense.business_id == biz.id).delete()
        db.query(BusinessNote).filter(BusinessNote.business_id == biz.id).delete()
        db.query(Setting).filter(Setting.business_id == biz.id).delete()
        convs = list(db.scalars(select(AiConversation).where(AiConversation.business_id == biz.id)).all())
        for c in convs:
            db.delete(c)
        db.delete(biz)
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    db.delete(user)
    db.commit()


def _seed_business(
    db: Session,
    *,
    email: str,
    password: str,
    owner_name: str,
    business_name: str,
    category: str,
    description: str,
    phone: str,
    address: str,
    gstin: str,
    upi_id: str,
    bank_name: str,
    bank_account: str,
    bank_ifsc: str,
    initial_cash_paise: int,
    monthly_exp_paise: int,
    safety_paise: int,
    products_def: list[tuple],
    customers_def: list[tuple],
    restocks: list[tuple],
    adjustments: list[tuple],
    invoices_spec: list[dict],
    expenses_spec: list[dict],
    notes_spec: list[dict],
    today: date,
    reset: bool,
) -> dict:
    existing = db.scalar(select(User).where(User.email == email.lower()).limit(1))
    if existing is not None:
        if not reset:
            biz = db.scalar(select(Business).where(Business.owner_user_id == existing.id).limit(1))
            return {"status": "skipped", "email": email, "business_id": biz.id if biz else None}
        _delete_demo_user_if_exists(db, email)

    # 1. Create User + Business + Settings
    user = User(
        full_name=owner_name,
        email=email.lower(),
        password_hash=hash_password(password),
        is_active=True,
    )
    db.add(user)
    db.flush()

    biz = Business(
        owner_user_id=user.id,
        name=business_name,
        category=category,
        description=description,
        owner_name=owner_name,
        email=email.lower(),
        phone=phone,
        address=address,
        gstin=gstin,
        currency="INR",
        upi_id=upi_id,
        bank_name=bank_name,
        bank_account=bank_account,
        bank_ifsc=bank_ifsc,
        default_payment_terms_days=15,
        default_tax_percent=18,
        initial_cash_balance_paise=initial_cash_paise,
        monthly_recurring_expenses_paise=monthly_exp_paise,
        safety_cash_threshold_paise=safety_paise,
        allow_negative_stock=False,
        onboarding_completed=True,
    )
    db.add(biz)
    db.flush()

    setting = Setting(
        business_id=biz.id,
        business_name=business_name,
        owner_name=owner_name,
        email=email.lower(),
        phone=phone,
        address=address,
        gstin=gstin,
        upi_id=upi_id,
        bank_name=bank_name,
        bank_account=bank_account,
        bank_ifsc=bank_ifsc,
        default_payment_terms_days=15,
        default_tax_percent=18,
        initial_cash_balance_paise=initial_cash_paise,
        monthly_recurring_expenses_paise=monthly_exp_paise,
        safety_cash_threshold_paise=safety_paise,
        expenses_json="[]",
    )
    db.add(setting)
    db.commit()
    db.refresh(biz)

    # 2. Seed 50 Products via inventory_service (automatically creates `initial` movements)
    sku_to_product: dict[str, dict] = {}
    for sku, name, cat, desc, cost, price, gst, unit, stock, min_t in products_def:
        p = inventory_service.create_product(
            db,
            biz.id,
            ProductIn(
                item_type="product",
                sku=sku,
                name=name,
                category=cat,
                description=desc,
                cost_price=cost,
                selling_price=price,
                tax_percent=gst,
                unit=unit,
                stock_quantity=stock,
                min_stock_threshold=min_t,
                is_active=True,
            ),
        )
        sku_to_product[sku] = p

    # 3. Seed Restock & Adjustment Movements via inventory_service
    for sku, qty, reason, ref in restocks:
        prod = sku_to_product[sku]
        inventory_service.adjust_stock(
            db,
            biz,
            prod["id"],
            StockAdjustIn(movement_type="restock", quantity_change=qty, reason=reason, reference=ref),
        )

    for sku, qty, reason, ref in adjustments:
        prod = sku_to_product[sku]
        inventory_service.adjust_stock(
            db,
            biz,
            prod["id"],
            StockAdjustIn(movement_type="adjustment", quantity_change=qty, reason=reason, reference=ref),
        )

    # 4. Seed Customers via customer_service
    name_to_customer: dict[str, dict] = {}
    for cname, cemail, cphone, caddr, cnotes in customers_def:
        c = customer_service.create_customer(
            db,
            CustomerIn(name=cname, email=cemail, phone=cphone, address=caddr, notes=cnotes),
            business_id=biz.id,
        )
        name_to_customer[cname] = c

    # 5. Seed Invoices & Payments via invoice_service + payment_service
    seeded_invoices = []
    seeded_payments = []
    for spec in invoices_spec:
        cust = name_to_customer[spec["customer"]]
        inv_date = today - timedelta(days=spec["days_ago"])
        due_date = inv_date + timedelta(days=spec["terms"])
        items_in = []
        for sku, qty in spec["items"]:
            prod = sku_to_product[sku]
            items_in.append(
                ItemIn(
                    product_id=prod["id"],
                    description=prod["name"],
                    quantity=qty,
                    unit_price=f"{prod['selling_price_paise'] / 100:.2f}",
                )
            )
        inv = invoice_service.create_invoice(
            db,
            InvoiceIn(
                customer_id=cust["id"],
                invoice_date=inv_date,
                due_date=due_date,
                description=spec["description"],
                tax_percent=spec.get("tax_percent", 18),
                notes=spec.get("notes", f"Thank you for choosing {business_name}."),
                items=items_in,
            ),
            today=today,
            business_id=biz.id,
        )
        if spec.get("send", True):
            inv = invoice_service.send_invoice(db, inv["id"], today=today, business_id=biz.id)

        for pmt_spec in spec.get("payments", []):
            p_date = today - timedelta(days=pmt_spec["days_ago"])
            if pmt_spec["amount"] == "FULL":
                amt_str = f"{inv['outstanding_paise'] / 100:.2f}"
            else:
                amt_str = pmt_spec["amount"]
            pmt = payment_service.record_payment(
                db,
                PaymentCreate(
                    invoice_id=inv["id"],
                    amount=amt_str,
                    payment_date=p_date,
                    method=pmt_spec["method"],
                    reference=pmt_spec.get("ref"),
                    notes=pmt_spec.get("notes"),
                ),
                today=today,
                business_id=biz.id,
            )
            seeded_payments.append(pmt)
            inv = invoice_service.get_invoice_detail(db, inv["id"], today=today, business_id=biz.id)

        seeded_invoices.append(inv)

    # 6. Seed Expenses via expense_service
    seeded_expenses = []
    for exp in expenses_spec:
        e = expense_service.create_expense(
            db,
            ExpenseIn(
                name=exp["name"],
                category=exp["category"],
                amount=exp["amount"],
                expense_date=today + timedelta(days=exp["offset_days"]),
                is_recurring=exp["is_recurring"],
                day_of_month=exp.get("day_of_month"),
                notes=exp.get("notes"),
            ),
            business_id=biz.id,
        )
        seeded_expenses.append(e)

    # 7. Seed Business Notes via note_service
    seeded_notes = []
    for note in notes_spec:
        n = note_service.create_note(
            db,
            biz.id,
            NoteIn(
                title=note["title"],
                category=note["category"],
                content=note["content"],
                is_pinned=note.get("is_pinned", False),
                checklist=note.get("checklist", []),
            ),
        )
        seeded_notes.append(n)

    return {
        "status": "seeded",
        "email": email,
        "business_id": biz.id,
        "business_name": business_name,
        "products": len(sku_to_product),
        "customers": len(name_to_customer),
        "invoices": len(seeded_invoices),
        "payments": len(seeded_payments),
        "expenses": len(seeded_expenses),
        "notes": len(seeded_notes),
    }


def seed_all_demo_businesses(
    db: Session,
    *,
    stationery_password: str,
    furniture_password: str,
    today: date | None = None,
    reset: bool = False,
) -> dict:
    today = today or date.today()

    stationery_restocks = [
        ("STN-PAP-001", 40, "Monthly mill restock — TNPL A4 75 GSM", "PO-STN-2026-011"),
        ("STN-PEN-001", 30, "Bulk refill shipment from distributor", "PO-STN-2026-014"),
        ("STN-OFF-001", 25, "Arch file restock for corporate orders", "PO-STN-2026-019"),
    ]
    stationery_adjustments = [
        ("STN-PAP-004", -4, "Damaged covers written off during stock audit", "AUD-STN-001"),
        ("STN-ART-008", -2, "Display shelf samples moved to showroom", "AUD-STN-002"),
    ]
    stationery_invoices = [
        # 3 Paid invoices
        {
            "customer": "Deccan Tech Park Admin",
            "days_ago": 35,
            "terms": 15,
            "description": "Monthly Corporate Stationery Replenishment",
            "tax_percent": 12,
            "items": [("STN-PAP-001", 25), ("STN-PEN-001", 10), ("STN-OFF-004", 15), ("STN-PAP-006", 12)],
            "payments": [{"amount": "FULL", "days_ago": 22, "method": "bank_transfer", "ref": "NEFT/DTP/8821", "notes": "Settled in full."}],
        },
        {
            "customer": "Charminar Print & Copy Hub",
            "days_ago": 28,
            "terms": 15,
            "description": "Bulk A4 & A3 Copier Paper Supply",
            "tax_percent": 12,
            "items": [("STN-PAP-001", 30), ("STN-PAP-002", 20), ("STN-PAP-003", 8)],
            "payments": [{"amount": "FULL", "days_ago": 15, "method": "upi", "ref": "UPI/CPH/4410", "notes": "Paid via business UPI."}],
        },
        {
            "customer": "Nizam College Fine Arts Dept",
            "days_ago": 24,
            "terms": 15,
            "description": "Semester Art & Drawing Kit Supply",
            "tax_percent": 12,
            "items": [("STN-ART-001", 12), ("STN-ART-002", 8), ("STN-ART-004", 10), ("STN-ART-005", 10)],
            "payments": [{"amount": "FULL", "days_ago": 11, "method": "bank_transfer", "ref": "NEFT/NCFA/3319"}],
        },
        # 2 Partially paid invoices (including multi-instalment)
        {
            "customer": "Hyderabad Public Coaching Centre",
            "days_ago": 20,
            "terms": 25,
            "description": "Exam Season Notebooks, Pens & Registers",
            "tax_percent": 12,
            "items": [("STN-PAP-004", 35), ("STN-PAP-005", 30), ("STN-PEN-003", 20), ("STN-PEN-005", 25)],
            "payments": [
                {"amount": "6000.00", "days_ago": 12, "method": "upi", "ref": "UPI/HPCC/101", "notes": "First instalment"},
                {"amount": "4500.00", "days_ago": 4, "method": "bank_transfer", "ref": "IMPS/HPCC/102", "notes": "Second instalment"},
            ],
        },
        {
            "customer": "Gachibowli CoWork Spaces",
            "days_ago": 14,
            "terms": 20,
            "description": "New Floor Office Equipment Setup",
            "tax_percent": 18,
            "items": [("STN-EQP-005", 2), ("STN-EQP-006", 2), ("STN-EQP-001", 6), ("STN-EQP-002", 8)],
            "payments": [
                {"amount": "10000.00", "days_ago": 6, "method": "bank_transfer", "ref": "NEFT/GCW/771", "notes": "Advance 50% payment"},
            ],
        },
        # 2 Overdue invoices
        {
            "customer": "Kukatpally Legal Associates",
            "days_ago": 34,
            "terms": 15,
            "description": "Quarterly Case Files, Legal Pads & Envelopes",
            "tax_percent": 18,
            "items": [("STN-OFF-001", 25), ("STN-OFF-002", 15), ("STN-PAP-007", 20), ("STN-PEN-002", 12)],
            "payments": [],
        },
        {
            "customer": "Secunderabad Logistics Corp",
            "days_ago": 23,
            "terms": 15,
            "description": "Warehouse Dispatch Tapes & Permanent Markers",
            "tax_percent": 18,
            "items": [("STN-OFF-008", 18), ("STN-PEN-009", 15), ("STN-EQP-004", 10), ("STN-ART-010", 12)],
            "payments": [],
        },
        # 2 Pending invoices (due soon / future)
        {
            "customer": "Vignan Architecture Studio",
            "days_ago": 12,
            "terms": 15,
            "description": "Drafting Pencils, A3 Paper & Trimmer",
            "tax_percent": 18,
            "items": [("STN-PAP-003", 5), ("STN-EQP-007", 2), ("STN-PEN-006", 15), ("STN-ART-007", 15)],
            "payments": [],
        },
        {
            "customer": "CarePlus Diagnostics Lab",
            "days_ago": 3,
            "terms": 15,
            "description": "Lab Reception Folders, Calculators & Pens",
            "tax_percent": 18,
            "items": [("STN-OFF-003", 10), ("STN-EQP-001", 4), ("STN-PEN-001", 12), ("STN-OFF-009", 10)],
            "payments": [],
        },
        # 2 Draft invoices (do NOT deduct stock!)
        {
            "customer": "Deccan Tech Park Admin",
            "days_ago": 0,
            "terms": 15,
            "description": "Next Month Desk Organizers & Highlighters",
            "tax_percent": 18,
            "send": False,
            "items": [("STN-ART-008", 6), ("STN-PEN-007", 10), ("STN-OFF-006", 10)],
            "payments": [],
        },
        {
            "customer": "Hyderabad Public Coaching Centre",
            "days_ago": 0,
            "terms": 15,
            "description": "Draft Quote — Geometry Boxes & Pencils",
            "tax_percent": 12,
            "send": False,
            "items": [("STN-ART-006", 20), ("STN-PEN-005", 20)],
            "payments": [],
        },
    ]
    stationery_expenses = [
        {"name": "Abids Retail Shop & Godown Rent", "category": "Rent", "amount": "28000.00", "offset_days": 4, "is_recurring": True, "day_of_month": 5, "notes": "Monthly shop lease."},
        {"name": "Store Staff Salaries (2 Assistants)", "category": "Payroll", "amount": "32000.00", "offset_days": 1, "is_recurring": True, "day_of_month": 1, "notes": "Billing & stock assistant salaries."},
        {"name": "Electricity, Broadband & POS Software", "category": "Utilities", "amount": "6500.00", "offset_days": 10, "is_recurring": True, "day_of_month": 12, "notes": "Commercial power and fiber line."},
        {"name": "Local Delivery Tempo Fuel & Maintenance", "category": "Logistics", "amount": "4800.00", "offset_days": 6, "is_recurring": False, "day_of_month": None, "notes": "Hyderabad B2B delivery runs."},
    ]
    stationery_notes = [
        {
            "title": "Urgent Restock List — This Week",
            "category": "Suppliers",
            "content": "Thermal POS rolls (STN-PAP-010) and Self-Inking Stamps (STN-EQP-010) are out of stock. Call Balaji Paper Agencies and Kores distributor today.",
            "is_pinned": True,
            "checklist": [
                {"id": "1", "text": "Order 30 packs of 80mm thermal rolls", "done": False},
                {"id": "2", "text": "Confirm A4 75 GSM rate revision with mill", "done": True},
                {"id": "3", "text": "Restock whiteboard markers (STN-PEN-008)", "done": False},
            ],
        },
        {
            "title": "Overdue Follow-ups — Hyderabad B2B",
            "category": "Customers",
            "content": "Kukatpally Legal Associates and Secunderabad Logistics Corp invoices are past due. Send polite WhatsApp reminders with UPI ID.",
            "is_pinned": True,
            "checklist": [
                {"id": "1", "text": "Follow up with Kukatpally Legal Associates", "done": False},
                {"id": "2", "text": "Call Secunderabad Logistics billing desk", "done": False},
            ],
        },
        {
            "title": "Back-to-School & Exam Bulk Pricing",
            "category": "Finance",
            "content": "Offer 6% volume discount on orders above ₹25,000 for coaching centres while preserving minimum 22% gross margin.",
            "is_pinned": False,
            "checklist": [],
        },
        {
            "title": "Monthly Stock Audit Findings",
            "category": "Operations",
            "content": "Completed shelf audit for Paper & Notebooks section. Adjusted 4 damaged hardcover notebooks and moved 2 mesh organizers to front display.",
            "is_pinned": False,
            "checklist": [{"id": "1", "text": "Reconcile ledger register stock count", "done": True}],
        },
        {
            "title": "GST Return Preparation Checklist",
            "category": "Finance",
            "content": "Compile GSTR-1 B2B invoice summary by the 10th of the month.",
            "is_pinned": False,
            "checklist": [
                {"id": "1", "text": "Verify GSTIN on all corporate invoices", "done": True},
                {"id": "2", "text": "Export invoice register for CA", "done": False},
            ],
        },
    ]

    # Business B — Oakwood Furniture Studio specs
    furniture_restocks = [
        ("OAK-SOF-001", 3, "Workshop batch completion — Verona 2-Seater", "PO-OAK-2026-004"),
        ("OAK-OFF-003", 6, "Ergonomic mesh chair import container arrival", "PO-OAK-2026-009"),
        ("OAK-TAB-003", 6, "Teak dining chair sets polished & QC passed", "PO-OAK-2026-012"),
    ]
    furniture_adjustments = [
        ("OAK-TAB-004", -1, "Showroom display scratch — moved to clearance", "AUD-OAK-001"),
        ("OAK-ACC-001", -1, "Transit glass crack written off", "AUD-OAK-002"),
    ]
    furniture_invoices = [
        # 3 Paid high-value invoices
        {
            "customer": "Jubilee Hills Residency Interiors",
            "days_ago": 38,
            "terms": 15,
            "description": "Living & Dining Suite — Villa 14",
            "tax_percent": 18,
            "items": [("OAK-SOF-003", 1), ("OAK-TAB-001", 1), ("OAK-TAB-003", 3), ("OAK-TAB-004", 1)],
            "payments": [{"amount": "FULL", "days_ago": 25, "method": "bank_transfer", "ref": "RTGS/JHRI/9901", "notes": "Full RTGS settlement."}],
        },
        {
            "customer": "CyberTowers Startup Labs",
            "days_ago": 30,
            "terms": 15,
            "description": "Startup Floor Workstations & Chairs",
            "tax_percent": 18,
            "items": [("OAK-OFF-001", 3), ("OAK-OFF-003", 6), ("OAK-OFF-006", 4)],
            "payments": [{"amount": "FULL", "days_ago": 17, "method": "bank_transfer", "ref": "NEFT/CTSL/4420"}],
        },
        {
            "customer": "Gachibowli Dental & Wellness",
            "days_ago": 22,
            "terms": 15,
            "description": "Clinic Waiting Lounge & Storage Cabinets",
            "tax_percent": 18,
            "items": [("OAK-SOF-001", 2), ("OAK-STR-005", 2), ("OAK-ACC-003", 2)],
            "payments": [{"amount": "FULL", "days_ago": 10, "method": "upi", "ref": "UPI/GDW/6612"}],
        },
        # 2 Partially paid invoices (multi-instalment to prove zero duplicate stock deduction!)
        {
            "customer": "Ananya & Karthik Villa Project",
            "days_ago": 18,
            "terms": 25,
            "description": "Master & Guest Bedroom Furniture Package",
            "tax_percent": 18,
            "items": [("OAK-BED-003", 1), ("OAK-BED-001", 1), ("OAK-BED-005", 4), ("OAK-BED-006", 1)],
            "payments": [
                {"amount": "80000.00", "days_ago": 15, "method": "bank_transfer", "ref": "RTGS/AKVP/001", "notes": "Booking advance"},
                {"amount": "65000.00", "days_ago": 5, "method": "bank_transfer", "ref": "NEFT/AKVP/002", "notes": "Pre-delivery instalment"},
            ],
        },
        {
            "customer": "Telangana FinServe Advisory",
            "days_ago": 12,
            "terms": 20,
            "description": "Boardroom & Director Cabin Fit-Out",
            "tax_percent": 18,
            "items": [("OAK-OFF-005", 1), ("OAK-OFF-004", 2), ("OAK-OFF-009", 1)],
            "payments": [
                {"amount": "90000.00", "days_ago": 7, "method": "bank_transfer", "ref": "RTGS/TSF/221", "notes": "50% milestone payment"},
            ],
        },
        # 2 Overdue invoices
        {
            "customer": "Banjara Boutique Hotel",
            "days_ago": 33,
            "terms": 15,
            "description": "Suite Refurbishment — Beds, Mattresses & Recliners",
            "tax_percent": 18,
            "items": [("OAK-BED-002", 2), ("OAK-BED-010", 2), ("OAK-SOF-004", 2)],
            "payments": [],
        },
        {
            "customer": "Secunderabad Heritage Club",
            "days_ago": 24,
            "terms": 15,
            "description": "Clubhouse Dining & Lounge Furniture",
            "tax_percent": 18,
            "items": [("OAK-TAB-002", 2), ("OAK-TAB-003", 4), ("OAK-SOF-006", 3)],
            "payments": [],
        },
        # 2 Pending invoices
        {
            "customer": "Manikonda Modern Homes",
            "days_ago": 11,
            "terms": 15,
            "description": "Model Flat Living Room & TV Console",
            "tax_percent": 18,
            "items": [("OAK-SOF-002", 1), ("OAK-STR-001", 1), ("OAK-TAB-005", 1), ("OAK-STR-003", 1)],
            "payments": [],
        },
        {
            "customer": "Madhapur Design Co-Op",
            "days_ago": 2,
            "terms": 15,
            "description": "Studio Work Desks & Visitor Seating",
            "tax_percent": 18,
            "items": [("OAK-OFF-002", 4), ("OAK-OFF-010", 3), ("OAK-STR-002", 2)],
            "payments": [],
        },
        # 2 Draft invoices (do NOT deduct stock)
        {
            "customer": "Jubilee Hills Residency Interiors",
            "days_ago": 0,
            "terms": 15,
            "description": "Draft Quote — Study & Dressing Suite",
            "tax_percent": 18,
            "send": False,
            "items": [("OAK-BED-008", 1), ("OAK-BED-007", 1), ("OAK-ACC-001", 2)],
            "payments": [],
        },
        {
            "customer": "CyberTowers Startup Labs",
            "days_ago": 0,
            "terms": 15,
            "description": "Draft Quote — Archive Cabinets & Footrests",
            "tax_percent": 18,
            "send": False,
            "items": [("OAK-OFF-007", 2), ("OAK-ACC-005", 6)],
            "payments": [],
        },
    ]
    furniture_expenses = [
        {"name": "Jubilee Hills Showroom & Warehouse Lease", "category": "Rent", "amount": "95000.00", "offset_days": 4, "is_recurring": True, "day_of_month": 5, "notes": "Showroom floor + Banjara warehouse."},
        {"name": "Carpenters, Polishers & Showroom Payroll", "category": "Payroll", "amount": "125000.00", "offset_days": 1, "is_recurring": True, "day_of_month": 1, "notes": "6 workshop & showroom team members."},
        {"name": "Showroom Lighting, AC & ERP Subscriptions", "category": "Utilities", "amount": "22000.00", "offset_days": 10, "is_recurring": True, "day_of_month": 12, "notes": "3-phase showroom electricity & internet."},
        {"name": "White-Glove Furniture Delivery Truck Service", "category": "Logistics", "amount": "18500.00", "offset_days": 5, "is_recurring": False, "day_of_month": None, "notes": "Hydraulic lift inspection and padding."},
    ]
    furniture_notes = [
        {
            "title": "Workshop Production & Out-of-Stock Priority",
            "category": "Operations",
            "content": "Dual-Motor Electric Standing Desk (OAK-OFF-008) and Leatherette Pouffe Footstool (OAK-SOF-010) are out of stock. Confirm motor shipment ETA.",
            "is_pinned": True,
            "checklist": [
                {"id": "1", "text": "Confirm electric standing desk frame delivery", "done": False},
                {"id": "2", "text": "Queue 4 Sheesham rocking chairs in carpentry bay", "done": False},
                {"id": "3", "text": "Inspect final lacquer finish on Verona sofas", "done": True},
            ],
        },
        {
            "title": "Banjara Boutique Hotel Payment Follow-up",
            "category": "Customers",
            "content": "Suite refurbishment invoice is 18 days overdue. Speak with GM regarding NEFT release before next room batch.",
            "is_pinned": True,
            "checklist": [
                {"id": "1", "text": "Send firm reminder via Email & WhatsApp", "done": False},
                {"id": "2", "text": "Confirm delivery sign-off copies attached", "done": True},
            ],
        },
        {
            "title": "Timber & Upholstery Vendor Rate Lock",
            "category": "Suppliers",
            "content": "Locked Grade-A Burma teak and walnut veneer pricing with Telangana Timber Mart through Q2.",
            "is_pinned": False,
            "checklist": [],
        },
        {
            "title": "White-Glove Delivery Schedule",
            "category": "Operations",
            "content": "Coordinate elevator booking for Ananya & Karthik Villa Project once final balance clears.",
            "is_pinned": False,
            "checklist": [{"id": "1", "text": "Verify staircase clearance for King-size bed", "done": True}],
        },
        {
            "title": "Showroom Floor Refresh Ideas",
            "category": "Ideas",
            "content": "Create a dedicated Ergonomic Home Office corner showcasing Apex Pro Desk + ErgoMesh Chair + Under-Desk Footrest.",
            "is_pinned": False,
            "checklist": [],
        },
    ]

    res_a = _seed_business(
        db,
        email=STATIONERY_EMAIL,
        password=stationery_password,
        owner_name="Rahul Sharma",
        business_name="Urban Stationery & Office Supplies",
        category="Retail / Stationery and Office Supplies",
        description="Complete B2B and retail stationery, copier paper, writing instruments, office equipment, and fine art supplies in Hyderabad.",
        phone="+91 98480 55110",
        address="Shop 14 & 15, Tilak Road, Abids, Hyderabad, Telangana 500001",
        gstin="36AABCU9603R1ZM",
        upi_id="urbanstationery@okhdfcbank",
        bank_name="HDFC Bank",
        bank_account="50200078123456",
        bank_ifsc="HDFC0000512",
        initial_cash_paise=18500000,   # ₹1,85,000
        monthly_exp_paise=6650000,     # ₹66,500
        safety_paise=5000000,          # ₹50,000
        products_def=STATIONERY_PRODUCTS,
        customers_def=STATIONERY_CUSTOMERS,
        restocks=stationery_restocks,
        adjustments=stationery_adjustments,
        invoices_spec=stationery_invoices,
        expenses_spec=stationery_expenses,
        notes_spec=stationery_notes,
        today=today,
        reset=reset,
    )

    res_b = _seed_business(
        db,
        email=FURNITURE_EMAIL,
        password=furniture_password,
        owner_name="Arjun Mehta",
        business_name="Oakwood Furniture Studio",
        category="Retail / Home and Office Furniture",
        description="Handcrafted solid-wood living room, bedroom, dining, storage, and ergonomic office furniture studio in Hyderabad.",
        phone="+91 98490 88220",
        address="Plot 42, Road No. 36, Jubilee Hills, Hyderabad, Telangana 500033",
        gstin="36AAECO4412K1Z9",
        upi_id="oakwoodstudio@okicici",
        bank_name="ICICI Bank",
        bank_account="00080501234567",
        bank_ifsc="ICIC0000008",
        initial_cash_paise=65000000,   # ₹6,50,000
        monthly_exp_paise=24200000,    # ₹2,42,000
        safety_paise=15000000,         # ₹1,50,000
        products_def=FURNITURE_PRODUCTS,
        customers_def=FURNITURE_CUSTOMERS,
        restocks=furniture_restocks,
        adjustments=furniture_adjustments,
        invoices_spec=furniture_invoices,
        expenses_spec=furniture_expenses,
        notes_spec=furniture_notes,
        today=today,
        reset=reset,
    )

    return {"stationery": res_a, "furniture": res_b}


def generate_demo_doc(
    db: Session,
    *,
    stationery_password: str,
    furniture_password: str,
    output_path: Path,
) -> None:
    """Write the single authoritative docs/DEMO_ACCOUNT.md synchronized with live DB records."""
    today = date.today()
    sections = [
        "# Chitragupta — Demonstration Accounts & Complete Seed Reference",
        "",
        "> This is the **single authoritative document** for Chitragupta's two independent demonstration businesses. All product records, inventory balances, valuations, customers, invoices, payments, expenses, and notes below are generated directly from the live seeded SQLite database.",
        "",
        "## Demo Login Instructions",
        "",
        "1. Open Chitragupta at **http://127.0.0.1:5180**.",
        "2. Click **Sign In** (or navigate to `/login`).",
        "3. Sign in with either demonstration account below. Each account is completely isolated by `business_id` across Dashboard, Customers, Catalogue, Inventory, Invoices, Payments, Cash Flow, Reminders, Notepad, AI Finance Copilot, and Settings.",
        "",
        "| Business | Owner | Email | Password | Category | Location |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| **Urban Stationery & Office Supplies** | Rahul Sharma | `{STATIONERY_EMAIL}` | `{stationery_password}` | Retail / Stationery and Office Supplies | Hyderabad, Telangana, India |",
        f"| **Oakwood Furniture Studio** | Arjun Mehta | `{FURNITURE_EMAIL}` | `{furniture_password}` | Retail / Home and Office Furniture | Hyderabad, Telangana, India |",
        "",
        "> **Security Notice:** These credentials are public demonstration accounts only. Plaintext passwords are never stored in application source code and are securely hashed with `scrypt` in SQLite. Never reuse demo credentials for real production or administrative accounts.",
        "",
        "### Controlled Re-Seeding Command",
        "",
        "Demo data is **never** recreated automatically on server startup and **never** modifies or deletes real user accounts.",
        "",
        "```powershell",
        ".\\backend\\.venv\\Scripts\\python.exe backend\\scripts\\seed_dual_demo.py ^",
        "  --stationery-password \"<STATIONERY_DEMO_PASSWORD>\" ^",
        "  --furniture-password \"<FURNITURE_DEMO_PASSWORD>\" ^",
        "  --reset-demo --write-docs",
        "```",
        "",
    ]

    opening_lookup = {
        STATIONERY_EMAIL: {row[0]: row[8] for row in STATIONERY_PRODUCTS},
        FURNITURE_EMAIL: {row[0]: row[8] for row in FURNITURE_PRODUCTS},
    }

    for idx, (label, email) in enumerate(
        [
            ("Business A — Urban Stationery & Office Supplies", STATIONERY_EMAIL),
            ("Business B — Oakwood Furniture Studio", FURNITURE_EMAIL),
        ],
        start=1,
    ):
        user = db.scalar(select(User).where(User.email == email).limit(1))
        biz = db.scalar(select(Business).where(Business.owner_user_id == user.id).limit(1))
        dash = dashboard_service.get_dashboard_summary(db, today=today, business_id=biz.id)
        inv_sum = inventory_service.get_inventory_summary(db, business_id=biz.id)
        prods = inventory_service.list_products(db, business_id=biz.id, include_inactive=True)
        prods.sort(key=lambda p: (p["sku"] or ""))
        custs, _ = customer_service.list_customers(db, page=1, page_size=100, business_id=biz.id)
        invs, _ = invoice_service.list_invoices(db, page=1, page_size=100, today=today, business_id=biz.id)
        pmts, _ = payment_service.list_payments(db, page=1, page_size=100, business_id=biz.id)
        exps = expense_service.list_expenses(db, business_id=biz.id)
        notes = note_service.list_notes(db, business_id=biz.id)

        cat_counts: dict[str, int] = {}
        for p in prods:
            cat_counts[p["category"]] = cat_counts.get(p["category"], 0) + 1

        sections.extend([
            "---",
            "",
            f"## {idx}. {label}",
            "",
            "### Business Profile & Live Financial Snapshot",
            "",
            f"- **Business Name:** {biz.name}",
            f"- **Owner:** {biz.owner_name} (`{biz.email}`)",
            f"- **Category:** {biz.category}",
            f"- **Address:** {biz.address}",
            f"- **GSTIN:** `{biz.gstin}` · **Currency:** `{biz.currency}`",
            f"- **Products:** {inv_sum['total_active_products']} active products ({inv_sum['total_stock_units']} units on hand)",
            f"- **Inventory Valuation (Purchase Cost):** ₹{paise_to_rupees_text(inv_sum['inventory_valuation_paise'])}",
            f"- **Low-Stock Products:** {inv_sum['low_stock_count']} · **Out-of-Stock Products:** {inv_sum['out_of_stock_count']}",
            f"- **Total Outstanding Receivables:** ₹{paise_to_rupees_text(dash['total_outstanding_paise'])} (Overdue: ₹{paise_to_rupees_text(dash['total_overdue_paise'])})",
            f"- **Total Collected All-Time:** ₹{paise_to_rupees_text(dash['total_collected_all_time_paise'])}",
            f"- **Estimated Cash on Hand:** ₹{paise_to_rupees_text(dash['cash_on_hand_paise'])} (Runway: ~{dash['runway_days']} days)",
            "",
            "### Category Breakdown",
            "",
            "| Category | Product Count |",
            "| :--- | :---: |",
        ])
        for cat_name, cnt in cat_counts.items():
            sections.append(f"| {cat_name} | {cnt} |")

        sections.extend([
            "",
            f"### Complete Product Catalogue ({len(prods)} Products)",
            "",
            "| SKU | Product Name | Category | Purchase Cost (₹) | Selling Price (₹) | GST | Unit | Opening Stock | Current Stock | Min Threshold | Status |",
            "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])
        for p in prods:
            op_stk = opening_lookup[email].get(p["sku"], p["stock_quantity"])
            sections.append(
                f"| `{p['sku']}` | {p['name']} | {p['category']} | "
                f"{paise_to_rupees_text(p['cost_price_paise'] or 0)} | "
                f"{paise_to_rupees_text(p['selling_price_paise'])} | "
                f"{p['tax_percent']}% | {p['unit']} | {op_stk} | **{p['stock_quantity']}** | "
                f"{p['min_stock_threshold']} | `{p['stock_status']}` |"
            )

        sections.extend([
            "",
            f"### Customers ({len(custs)})",
            "",
            "| Customer Name | Email | Phone | Outstanding (₹) | Overdue (₹) |",
            "| :--- | :--- | :--- | :---: | :---: |",
        ])
        for c in custs:
            sections.append(
                f"| {c['name']} | {c['email'] or '—'} | {c['phone'] or '—'} | "
                f"{paise_to_rupees_text(c['outstanding_paise'])} | {paise_to_rupees_text(c['overdue_paise'])} |"
            )

        sections.extend([
            "",
            f"### Invoices ({len(invs)})",
            "",
            "| Invoice # | Customer | Lifecycle | Status | Total (₹) | Paid (₹) | Outstanding (₹) | Due Date |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ])
        for inv in invs:
            sections.append(
                f"| `{inv['invoice_number']}` | {inv['customer_name']} | {inv['lifecycle']} | "
                f"`{inv['status']}` | {paise_to_rupees_text(inv['total_paise'])} | "
                f"{paise_to_rupees_text(inv['paid_paise'])} | {paise_to_rupees_text(inv['outstanding_paise'])} | "
                f"{inv['due_date']} |"
            )

        sections.extend([
            "",
            f"### Payments ({len(pmts)})",
            "",
            "| Invoice # | Customer | Amount (₹) | Method | Reference | Date |",
            "| :--- | :--- | :---: | :---: | :--- | :---: |",
        ])
        for pm in pmts:
            sections.append(
                f"| `{pm['invoice_number']}` | {pm['customer_name']} | "
                f"{paise_to_rupees_text(pm['amount_paise'])} | {pm['method']} | "
                f"{pm['reference'] or '—'} | {pm['payment_date']} |"
            )

        sections.extend([
            "",
            f"### Scheduled Expenses ({len(exps)})",
            "",
            "| Expense | Category | Amount (₹) | Type |",
            "| :--- | :--- | :---: | :---: |",
        ])
        for e in exps:
            etype = f"Recurring (Day {e.day_of_month})" if e.is_recurring else f"One-off ({e.expense_date})"
            sections.append(f"| {e.name} | {e.category} | {paise_to_rupees_text(e.amount_paise)} | {etype} |")

        sections.extend([
            "",
            f"### Business Notes ({len(notes)})",
            "",
        ])
        for n in notes:
            pin_tag = " *(Pinned)*" if n["is_pinned"] else ""
            sections.append(f"- **{n['title']}** [{n['category']}]{pin_tag}: {n['content']}")

        sections.extend([
            "",
            "### Inventory Scenarios & Recent Stock Movements",
            "",
            "| Product | SKU | Type | Change | Balance After | Reason |",
            "| :--- | :--- | :---: | :---: | :---: | :--- |",
        ])
        for m in inv_sum["recent_movements"][:15]:
            chg = f"+{m['quantity_change']}" if m["quantity_change"] > 0 else str(m["quantity_change"])
            sections.append(
                f"| {m['product_name']} | `{m['sku']}` | `{m['movement_type']}` | "
                f"**{chg}** | {m['balance_after']} | {m['reason'] or '—'} |"
            )
        sections.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(sections), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed two independent Chitragupta demo businesses.")
    parser.add_argument(
        "--stationery-password",
        default=os.environ.get("CHITRA_DEMO_STATIONERY_PASSWORD"),
        help="Password for demo@chitragupta.in (or set CHITRA_DEMO_STATIONERY_PASSWORD).",
    )
    parser.add_argument(
        "--furniture-password",
        default=os.environ.get("CHITRA_DEMO_FURNITURE_PASSWORD"),
        help="Password for furniture.demo@chitragupta.in (or set CHITRA_DEMO_FURNITURE_PASSWORD).",
    )
    parser.add_argument(
        "--reset-demo",
        action="store_true",
        help="Safely replace ONLY the two demo businesses without touching any other user.",
    )
    parser.add_argument(
        "--write-docs",
        action="store_true",
        help="Regenerate docs/DEMO_ACCOUNT.md synchronized with seeded DB data.",
    )
    args = parser.parse_args()

    if not args.stationery_password or not args.furniture_password:
        parser.error(
            "Both --stationery-password and --furniture-password (or env vars "
            "CHITRA_DEMO_STATIONERY_PASSWORD / CHITRA_DEMO_FURNITURE_PASSWORD) are required."
        )

    create_all_tables()
    db = SessionLocal()
    try:
        result = seed_all_demo_businesses(
            db,
            stationery_password=args.stationery_password,
            furniture_password=args.furniture_password,
            reset=args.reset_demo,
        )
        print("Seed result:", result)
        if args.write_docs:
            doc_path = PROJECT_ROOT / "docs" / "DEMO_ACCOUNT.md"
            generate_demo_doc(
                db,
                stationery_password=args.stationery_password,
                furniture_password=args.furniture_password,
                output_path=doc_path,
            )
            print(f"Generated {doc_path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

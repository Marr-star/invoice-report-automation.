"""Produce deterministic fake PDFs; never uses customer data."""
from decimal import Decimal
from pathlib import Path
from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent / "samples" / "invoices"
ROOT.mkdir(parents=True, exist_ok=True)
VENDORS = ["Northwind Supplies", "Bright Harbor LLC", "Maple Office Co", "Bluebird Parts", "Evergreen Trading", "Solaris Paper"]
for i in range(1, 14):
    vendor = VENDORS[(i - 1) % len(VENDORS)]
    invoice_id = f"DEMO-{i:03d}" if i != 12 else "DEMO-001"  # duplicate for same vendor
    if i == 12:
        vendor = VENDORS[0]
    currency = ["USD", "EUR", "EGP"][i % 3]
    subtotal = Decimal(i * 50)
    tax = subtotal * Decimal("0.14")
    total = subtotal + tax
    fields = [f"Vendor: {vendor}", f"Invoice No: {invoice_id}", f"Invoice Date: 2026-10-{i:02d}", f"Currency: {currency}", f"Subtotal: {subtotal:.2f}", f"Tax: {tax:.2f}", f"Grand Total: {total:.2f}"]
    if i == 10:
        fields = [f for f in fields if not f.startswith("Currency:")]
    if i == 11:
        fields[-1] = "Grand Total: 999.00"
    if i == 13:
        fields[2] = "Invoice Date: 2026-88-12"
    if i % 3 == 0:
        fields = [f.replace('Vendor:', 'Supplier:').replace('Invoice No:', 'Bill No:').replace('Invoice Date:', 'Date Issued:').replace('Grand Total:', 'Amount Due:') for f in fields]
    elif i % 3 == 1:
        fields = [f.replace('Vendor:', 'Seller:').replace('Subtotal:', 'Net Amount:').replace('Tax:', 'VAT:') for f in fields]
        fields = list(reversed(fields))
    # Vary layouts, fonts, and header placement without changing the contractual labels.
    c = canvas.Canvas(str(ROOT / f"invoice_{i:02d}.pdf"), pagesize=(595, 842))
    c.setTitle(f"Fictional invoice sample {i}")
    c.setFont("Helvetica-Bold", 17)
    c.drawString(48 + 9 * (i % 3), 794, "SAMPLE INVOICE - NOT VALID FOR PAYMENT")
    c.setFont("Helvetica", 11 + (i % 2))
    y = 730 - 13 * (i % 4)
    for j, field in enumerate(fields):
        c.drawString(48 + (j % 2) * (i % 5) * 7, y, field)
        y -= 30 if i % 2 else 38
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(48, 72, "Synthetic demonstration only. No real businesses or customers.")
    c.save()
print(f"Generated {len(list(ROOT.glob('*.pdf')))} fictional PDFs in {ROOT}")

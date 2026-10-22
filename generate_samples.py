"""Generate 13 fictional invoices across three reusable layout templates."""
from decimal import Decimal
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white

ROOT = Path(__file__).parent / 'samples' / 'invoices'
VENDORS = ['Northwind Supplies', 'Bright Harbor LLC', 'Maple Office Co', 'Bluebird Parts', 'Evergreen Trading', 'Solaris Paper']


def generate():
    ROOT.mkdir(parents=True, exist_ok=True)
    for i in range(1, 14):
        vendor = VENDORS[(i - 1) % len(VENDORS)]
        invoice_id = f'DEMO-{i:03d}'
        if i == 12:
            vendor, invoice_id = VENDORS[0], 'DEMO-001'
        currency = ['USD', 'EUR', 'EGP'][i % 3]
        subtotal = Decimal(i * 50)
        tax = subtotal * Decimal('0.14')
        total = subtotal + tax if i != 11 else Decimal('999')
        date = f'2026-10-{i:02d}' if i != 13 else '2026-88-12'
        variant = (i - 1) % 3
        accent = ['#2458D3', '#087F8C', '#7353BA'][variant]
        c = canvas.Canvas(str(ROOT / f'invoice_{i:02d}.pdf'), pagesize=(595, 700), invariant=1)
        c.setTitle(f'{vendor} | {invoice_id} | Synthetic sample')
        def text(x, y, value, size=10, color='#263348', bold=False):
            c.setFillColor(HexColor(color))
            c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
            c.drawString(x, y, value)
        c.setFillColor(HexColor(accent)); c.rect(0, 692, 595, 8, fill=1, stroke=0)
        if variant == 1:
            c.setFillColor(HexColor('#11283B')); c.rect(0, 565, 595, 127, fill=1, stroke=0)
        text(38, 652, vendor, 21, '#FFFFFF' if variant == 1 else '#152238', True)
        text(38, 628, 'BUSINESS SUPPLIES / DEMONSTRATION ACCOUNT', 8, '#BDD9E4' if variant == 1 else '#6A778B')
        text(38, 590, 'INVOICE', 27, '#FFFFFF' if variant == 1 else accent, True)
        text(38, 531, f'Invoice No: {invoice_id}', 10, '#263348', True)
        text(38, 510, f'Invoice Date: {date}', 9, '#263348')
        text(38, 552, ['Vendor', 'Supplier', 'Seller'][variant] + f': {vendor}', 10, '#263348', True)
        text(330, 478, 'Bill to: Demo Business Ltd', 10)
        text(38, 457, 'Account: SYNTHETIC-CLIENT', 9, '#6A778B')
        if i != 10:
            text(38, 489, f'Currency: {currency}', 10, accent, True)
        c.setFillColor(HexColor(accent)); c.roundRect(38, 420, 519, 31, 3, fill=1, stroke=0)
        for x, value in [(50,'DESCRIPTION'), (328,'QTY'), (390,'UNIT PRICE'), (488,'AMOUNT')]:
            text(x, 431, value, 8, '#FFFFFF', True)
        rows = [('Office and workshop supplies', '1', f'{subtotal:.2f}', f'{subtotal:.2f}'), ('Standard delivery', '1', '0.00', '0.00')]
        for n, row in enumerate(rows):
            y=393-n*33
            for x,value in zip((50,335,405,492),row): text(x,y,value,9)
            c.setStrokeColor(HexColor('#E3E8F0')); c.line(38,y-12,557,y-12)
        text(338, 306, f'Subtotal: {subtotal:.2f}', 11)
        text(338, 282, f'Tax: {tax:.2f}', 11)
        c.setFillColor(HexColor('#EDF3FF' if variant == 0 else '#F0F3F6'))
        c.roundRect(322, 222, 235, 40, 4, fill=1, stroke=0)
        text(338, 237, f'Grand Total: {total:.2f}', 15, accent, True)
        text(38, 160, 'Payment terms', 10, '#263348', True)
        text(38, 141, 'Demonstration document. No payment is requested.', 9, '#6A778B')
        c.setStrokeColor(HexColor('#E3E8F0')); c.line(38,86,557,86)
        text(38, 65, 'SYNTHETIC SAMPLE / NOT VALID FOR PAYMENT', 8, accent, True)
        text(38, 48, 'All business names and transaction details are fictional.', 8, '#6A778B')
        c.save()
    print(f'Generated 13 synthetic invoices in {ROOT}')


if __name__ == '__main__':
    generate()

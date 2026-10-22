"""Conservative labeled-field extraction. Unsupported values require review."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import fitz

LABELS = {
    'invoice_id': r'(?:invoice\s*(?:number|no\.?|\#|id)|bill\s*(?:no\.?|\#))',
    'invoice_date': r'(?:invoice\s*date|date\s*issued|issued\s*on|date)',
    'vendor': r'(?:vendor|supplier|from|seller)',
    'currency': r'currency',
    'subtotal': r'(?:subtotal|sub\s+total|net\s*amount)',
    'tax': r'(?:vat|tax(?:\s*amount)?)',
    'total': r'(?:grand\s*total|amount\s*due|invoice\s*total|total\s*due|total)',
}
MONEY = {'subtotal', 'tax', 'total'}
REQUIRED = ('vendor', 'invoice_id', 'invoice_date', 'currency', 'subtotal', 'tax', 'total')
SYMBOLS = {'$': 'USD', '€': 'EUR', '£': 'GBP'}


def field(text: str, key: str) -> str | None:
    # Capture the complete value, never a valid-looking prefix of invalid data.
    pattern = rf'^\s*{LABELS[key]}(?:\s*:\s*|\s+)([^\n]*)$'
    values = [m.strip() for m in re.findall(pattern, text, re.I | re.M)]
    return values[0] if values and values[0] and len(set(values)) == 1 else None


def extract_text(pdf: Path) -> str:
    with fitz.open(pdf) as doc:
        if doc.needs_pass:
            raise ValueError('encrypted PDF')
        return '\n'.join(page.get_text(sort=True) for page in doc)


def parse_invoice(text: str, filename: str = '') -> tuple[dict, list[str]]:
    errors: list[str] = []
    record: dict = {'source_file': filename}
    raw = {key: field(text, key) for key in REQUIRED}
    for key, val in raw.items():
        record[key] = None
        if val is None:
            errors.append(f'missing_or_ambiguous_{key}')
            continue
        if key in MONEY:
            if not re.fullmatch(r'[-+]?[$€£]?\s*(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?', val):
                errors.append(f'invalid_{key}')
                continue
            try:
                amount = Decimal(re.sub(r'[$€£,\s]', '', val))
            except InvalidOperation:
                errors.append(f'invalid_{key}')
                continue
            record[key] = amount
            if amount < 0:
                errors.append(f'negative_{key}')
            for symbol, currency in SYMBOLS.items():
                if symbol in val and raw['currency'] and raw['currency'].upper() != currency:
                    errors.append(f'currency_symbol_mismatch_{key}')
        elif key == 'invoice_date':
            formats = (('%Y-%m-%d', r'\d{4}-\d{2}-\d{2}'),
                       ('%d/%m/%Y', r'\d{2}/\d{2}/\d{4}'),
                       ('%d-%m-%Y', r'\d{2}-\d{2}-\d{4}'))
            try:
                fmt = next(fmt for fmt, pattern in formats if re.fullmatch(pattern, val))
                record[key] = datetime.strptime(val, fmt).date().isoformat()
            except (ValueError, StopIteration):
                errors.append('invalid_invoice_date')
        elif key == 'invoice_id':
            if re.fullmatch(r'[A-Z0-9][A-Z0-9/_-]*', val, re.I):
                record[key] = val.upper()
            else:
                errors.append('invalid_invoice_id')
        elif key == 'currency':
            if val.upper() in {'USD', 'EUR', 'GBP', 'EGP'}:
                record[key] = val.upper()
            else:
                errors.append('unsupported_currency')
        else:
            record[key] = ' '.join(val.split())
            if len(record[key]) < 2:
                errors.append('invalid_vendor')
    if all(record.get(k) is not None for k in MONEY):
        if abs(record['subtotal'] + record['tax'] - record['total']) > Decimal('0.01'):
            errors.append('total_does_not_match_subtotal_plus_tax')
    if not text.strip():
        errors.append('no_extractable_text_scanned_pdf_possible')
    return record, errors

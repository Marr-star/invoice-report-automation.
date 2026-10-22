"""Batch processing with explicit review queue and deterministic outputs."""
import json
from openpyxl.styles import Font, PatternFill
from decimal import Decimal
from pathlib import Path
import argparse
import pandas as pd
from .extractor import extract_text, parse_invoice

COLUMNS = ["source_file", "vendor", "invoice_id", "invoice_date", "currency", "subtotal", "tax", "total"]


def process_folder(input_dir: Path, output_dir: Path) -> dict:
    if not input_dir.is_dir():
        raise ValueError(f"Input folder does not exist: {input_dir}")
    if input_dir.resolve() == output_dir.resolve():
        raise ValueError("Use separate input and output folders")
    files = sorted(p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")
    if not files:
        raise ValueError(f"No PDFs found in {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    good, review = [], []
    seen: set[tuple[str, str]] = set()
    for pdf in files:
        try:
            record, errors = parse_invoice(extract_text(pdf), pdf.name)
        except Exception as exc:
            record, errors = {"source_file": pdf.name}, [f"pdf_read_error: {type(exc).__name__}: {exc}"]
        if not errors:
            key = (record["vendor"].strip().casefold(), record["invoice_id"].strip().casefold())
            if key in seen:
                errors.append("duplicate_vendor_invoice_id")
            else:
                seen.add(key)
        if errors:
            review.append({**record, "errors": "; ".join(errors)})
        else:
            good.append(record)
    df = pd.DataFrame(good, columns=COLUMNS)
    error_df = pd.DataFrame(review, columns=COLUMNS + ["errors"])
    # Preserve all data in CSV, but avoid Excel interpreting a text cell as a formula.
    def safe_text(val):
        return "'" + val if isinstance(val, str) and val.startswith(("=", "+", "-", "@")) else val
    for frame in (df, error_df):
        for col in frame.columns:
            frame[col] = frame[col].map(safe_text)
    df.to_csv(output_dir / "invoices.csv", index=False)
    error_df.to_csv(output_dir / "processing_errors.csv", index=False)
    summary_rows = []
    for currency, group in df.groupby("currency"):
        summary_rows.append({"currency": currency, "invoice_count": len(group), "total": sum((Decimal(str(v)) for v in group["total"]), Decimal("0.00"))})
    summary = pd.DataFrame(summary_rows, columns=["currency", "invoice_count", "total"])
    summary.to_csv(output_dir / "summary_by_currency.csv", index=False)
    with pd.ExcelWriter(output_dir / "invoice_report.xlsx", engine="openpyxl") as writer:
        def numeric(frame):
            copy = frame.copy()
            for col in ("subtotal", "tax", "total"):
                if col in copy:
                    copy[col] = copy[col].map(lambda v: float(v) if isinstance(v, Decimal) else v)
            return copy
        numeric(df).to_excel(writer, index=False, sheet_name="Invoices")
        numeric(error_df).to_excel(writer, index=False, sheet_name="Needs Review")
        numeric(summary).to_excel(writer, index=False, sheet_name="Currency Summary")
        for sheet in writer.book:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for cell in sheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="17365D")
            for column in sheet.columns:
                from openpyxl.utils import get_column_letter
                letter = get_column_letter(column[0].column)
                sheet.column_dimensions[letter].width = min(54, max(16, max(len(str(c.value or "")) for c in column) + 2))
    result = {"processed": len(files), "accepted": len(good), "review": len(review), "totals_by_currency": {r["currency"]: str(r["total"]) for r in summary_rows}}

    (output_dir / "processing_summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    p = argparse.ArgumentParser(description="Extract invoices from text-based PDF files")
    p.add_argument("--input", type=Path, default=Path("samples/invoices"))
    p.add_argument("--output", type=Path, default=Path("output"))
    args = p.parse_args()
    try:
        result = process_folder(args.input, args.output)
    except ValueError as exc:
        p.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

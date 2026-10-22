"""Build README previews from the actual sample PDFs and exported CSV data."""
from pathlib import Path
import csv
import fitz
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'

def font(size, bold=False):
    return ImageFont.truetype('DejaVuSans' + ('-Bold' if bold else '') + '.ttf', size)

# A close, legible view of three full invoices.
preview = Image.new('RGB', (1500, 680), '#EDF1F7')
for j in range(3):
    with fitz.open(ROOT / f'samples/invoices/invoice_{j+1:02d}.pdf') as pdf:
        pix=pdf[0].get_pixmap(matrix=fitz.Matrix(.88,.88))
        page=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        page.thumbnail((470,630))
        preview.paste(page,(20+j*495,25))
preview.save(DOCS / 'sample-layouts.png')
rows=list(csv.DictReader((ROOT / 'samples/output/invoices.csv').open()))
review=list(csv.DictReader((ROOT / 'samples/output/processing_errors.csv').open()))
im=Image.new('RGB',(1440,880),'#F3F6FA'); d=ImageDraw.Draw(im)
d.rectangle((0,0,1440,180),fill='#12233D')
d.text((52,33),'INVOICE REPORT AUTOMATION',font=font(16,True),fill='#83ACFF')
d.text((52,73),'From PDF invoices to a clear financial report',font=font(35,True),fill='white')
d.text((52,131),'Extract fields  /  Validate records  /  Flag duplicates  /  Export Excel & CSV',font=font(18),fill='#C5D3E7')
for j,(label,value,color) in enumerate([('PDFS PROCESSED',str(len(rows)+len(review)),'#2458D3'),('ACCEPTED',str(len(rows)),'#087F75'),('NEEDS REVIEW',str(len(review)),'#B96B16')]):
    x=52+j*455
    d.rounded_rectangle((x,211,x+425,330),radius=12,fill='white')
    d.text((x+24,232),label,font=font(15,True),fill='#63728A')
    d.text((x+24,257),value,font=font(39,True),fill=color)
d.text((52,362),'Accepted invoices',font=font(23,True),fill='#12233D')
d.text((1135,369),'SAMPLE OUTPUT',font=font(14,True),fill='#63728A')
d.rounded_rectangle((52,408,1388,707),radius=10,fill='white')
d.rectangle((52,408,1388,452),fill='#E4EBF6')
cols=[('Vendor',76),('Invoice ID',535),('Date',775),('Currency',1005),('Total',1210)]
for label,x in cols:d.text((x,421),label,font=font(16,True),fill='#304260')
for j,row in enumerate(rows[:5]):
    y=470+j*45
    for value,(_,x) in zip([row['vendor'],row['invoice_id'],row['invoice_date'],row['currency'],f"{float(row['total']):,.2f}"],cols):
        d.text((x,y),value,font=font(17),fill='#263348')
    d.line((76,y+32,1364,y+32),fill='#EDF1F7')
d.text((52,745),'Review queue',font=font(21,True),fill='#12233D')
d.text((52,782),'Missing currency  /  Total mismatch  /  Duplicate invoice  /  Invalid date',font=font(18),fill='#866023')
d.text((52,837),'Actual pipeline results from 13 synthetic invoices. Amounts are summarized separately by currency.',font=font(15),fill='#63728A')
im.save(DOCS / 'report-preview.png')

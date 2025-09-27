
import csv, sys, re, os, io, html

OUT_HEADERS = [
    "Handle","Title","Body (HTML)","Vendor","Type","Tags","Published",
    "Option1 Name","Option1 Value","Option2 Name","Option2 Value","Option3 Name","Option3 Value",
    "Variant SKU","Variant Grams","Variant Inventory Tracker","Variant Inventory Qty","Variant Inventory Policy","Variant Fulfillment Service",
    "Variant Price","Variant Compare-at Price","Variant Requires Shipping","Variant Taxable","Variant Barcode",
    "Image Src","Image Alt Text"
]

PREFERRED_ORDER = [
    "Serial Number","Crystal Type","Authenticity / Reference #","Case Type","Dial","Hands","Model",
    "Markers","Marks on Dial","Complications","Water Resistant","Case Dimensions","Country of Origin",
    "Gender","Accompanied by","Bracelet/Strap Type","Bracelet/Strap Size","SKU"
]

def sniff_delimiter(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        s = f.read(4000)
    return '\t' if s.count('\t') >= s.count(',') else ','

def norm_header(h):
    if h is None: return ""
    h = str(h).strip().lower()
    if h.startswith('\\ufeff'): h = h.lstrip('\\ufeff')
    h = h.replace('*','').replace(':','')
    h = re.sub(r'[^a-z0-9]+','',h)
    return h

def norm_text(v):
    if v is None: return ""
    s = str(v)
    s = s.replace('\\xa0',' ').strip()
    s = re.sub(r'\\s+',' ', s)
    return s

def slugify(s):
    s = norm_text(s).lower()
    s = re.sub(r'[^a-z0-9\\-]+','-', s)
    s = re.sub(r'-+','-', s).strip('-')
    return s

def pick_price(row, idx):
    for key in ('buyitnowprice','startprice'):
        rawk = idx.get(key)
        if rawk and row.get(rawk):
            try:
                v = float(str(row[rawk]).replace(',','').strip())
                if v > 0: return f"{v:.2f}"
            except: pass
    return ""

def split_picurls(s):
    if not s: return []
    return [u.strip() for u in str(s).split('|') if u.strip()]

def index_columns(fieldnames):
    idx = {}
    for raw in fieldnames:
        n = norm_header(raw)
        if n: idx[n] = raw
    return idx

def extract_item_details_from_html(desc_html):
    details = {}
    if not desc_html: return details
    # normalize weird quotes and decode html entities
    html_str = html.unescape(str(desc_html))
    # find att_title/att_value pairs
    pattern = re.compile(r'<td[^>]*class="att_title"[^>]*>\\s*([^<:]+)\\s*:?</td>\\s*<td[^>]*class="att_value"[^>]*>\\s*([^<]+)\\s*</td>', re.I)
    for label, value in pattern.findall(html_str):
        label = norm_text(label).rstrip(':')
        value = norm_text(value)
        if label and value:
            details[label] = value
    return details

def build_tags(row, idx):
    candidates = [
        'cbrand','brand','cmodel','model','creferencenumber','referencenumber',
        'cmovement','movement','ccasematerial','casematerial','cbandmaterial','bandmaterial',
        'cdialcolor','dialcolor','cyearmanufactured','yearmanufactured','cdepartment','department',
        'ctype','type','ccasesize','casesize'
    ]
    vals = []; seen = set()
    for k in candidates:
        raw = idx.get(k)
        if raw and row.get(raw):
            v = norm_text(row[raw])
            if v and len(v) <= 80 and v.lower() not in seen:
                seen.add(v.lower()); vals.append(v)
    return ", ".join(vals)

def make_simple_description(row, idx, details):
    brand = norm_text(row.get(idx.get('cbrand') or idx.get('brand'), ""))
    model = norm_text(row.get(idx.get('cmodel') or idx.get('model'), ""))
    refno = norm_text(row.get(idx.get('creferencenumber') or idx.get('referencenumber'), ""))
    casematerial = norm_text(row.get(idx.get('ccasematerial') or idx.get('casematerial'), ""))
    casesize = norm_text(row.get(idx.get('ccasesize') or idx.get('casesize'), ""))
    movement = norm_text(row.get(idx.get('cmovement') or idx.get('movement'), ""))
    era = norm_text(row.get(idx.get('cyearmanufactured') or idx.get('yearmanufactured'), ""))

    bits = []
    if brand or model:
        bits.append(f"Preowned {brand} {model}".strip())
    if refno:
        bits.append(f"ref. {refno}")
    if casematerial or casesize:
        mat_size = " ".join([x for x in [casematerial, casesize] if x])
        if mat_size: bits.append(mat_size)
    if movement:
        bits.append(movement)
    if era:
        bits.append(era)

    sentence = ", ".join([b for b in bits if b]) + "." if bits else ""
    if not sentence:
        # Fallback: trim first paragraph from HTML (if present) later
        pass
    return sentence

def build_body_html(simple_desc, details, sku):
    # Filter details to preferred set and order
    rows = []
    for label in PREFERRED_ORDER:
        if label in details and details[label]:
            rows.append((label, details[label]))
    # Ensure SKU appears (from CustomLabel) if not already in details
    have_sku = any(k.lower() == 'sku' for k,_ in rows)
    if not have_sku and sku:
        rows.append(("SKU", sku))

    # Build clean HTML
    parts = []
    if simple_desc:
        parts.append(f"<p>{html.escape(simple_desc)}</p>")
    if rows:
        parts.append("<h3>Item Details</h3>")
        parts.append('<table class="item-details">')
        for k,v in rows:
            parts.append(f"<tr><td><strong>{html.escape(k)}:</strong></td><td>{html.escape(v)}</td></tr>")
        parts.append("</table>")
    return "".join(parts)

def sanitize_cr_only(s):
    if s is None: return ""
    return str(s).replace("\\r\\n","\\r").replace("\\n","\\r")

def main(inp, outp):
    # Read raw with detected delimiter
    with open(inp, 'r', encoding='utf-8', errors='ignore', newline='') as f:
        sample = f.read(4000)
    delim = '\\t' if sample.count('\\t') >= sample.count(',') else ','

    with open(inp, 'r', encoding='utf-8', errors='ignore', newline='') as f:
        reader = csv.reader(f, delimiter=delim)
        raw_rows = list(reader)

    # Skip template lines until we find a header that contains at least 'title' or 'customlabel'
    header_row = None
    start_idx = 0
    for i, row in enumerate(raw_rows):
        joined = ",".join(row).lower()
        if "title" in joined or "customlabel" in joined:
            header_row = row
            start_idx = i + 1
            break
    if header_row is None:
        print("No valid header row found.")
        sys.exit(1)

    headers = header_row
    idx = index_columns(headers)

    dict_rows = [dict(zip(headers, r)) for r in raw_rows[start_idx:] if any(c.strip() for c in r)]

    out_rows = []
    kept = 0

    for row in dict_rows:
        # Title
        title_raw_key = idx.get('title')
        title = norm_text(row.get(title_raw_key, "")) if title_raw_key else ""
        if not title: 
            continue

        # SKU/Handle
        sku_key = idx.get('customlabel') or idx.get('sku')
        sku = norm_text(row.get(sku_key, "")) if sku_key else ""
        handle = sku.lower() if sku else slugify(title)

        # Vendor/Type/Tags
        vendor_key = idx.get('cbrand') or idx.get('brand')
        vendor = norm_text(row.get(vendor_key, "")) if vendor_key else ""
        tags = build_tags(row, idx)

        # Description HTML
        desc_key = idx.get('description')
        desc_html = row.get(desc_key, "") if desc_key else ""

        details_from_html = extract_item_details_from_html(desc_html)

        # Fallback details from CSV columns
        fallback = {
            "Authenticity / Reference #": norm_text(row.get(idx.get('creferencenumber'), "")) if idx.get('creferencenumber') else "",
            "Case Type": norm_text(row.get(idx.get('ccasematerial'), "")) if idx.get('ccasematerial') else "",
            "Dial": norm_text(row.get(idx.get('cdialcolor'), "")) if idx.get('cdialcolor') else "",
            "Model": norm_text(row.get(idx.get('cmodel'), "")) if idx.get('cmodel') else "",
            "Water Resistant": norm_text(row.get(idx.get('cwaterresistance'), "")) if idx.get('cwaterresistance') else "",
            "Case Dimensions": norm_text(row.get(idx.get('ccasesize'), "")) if idx.get('ccasesize') else "",
            "Country of Origin": norm_text(row.get(idx.get('ccountryregionofmanufacture'), "")) if idx.get('ccountryregionofmanufacture') else "",
            "Gender": norm_text(row.get(idx.get('cdepartment'), "")) if idx.get('cdepartment') else ""
        }

        # Merge HTML details first, then fallback
        details = {}
        details.update(details_from_html)
        for k,v in fallback.items():
            if k not in details or not details[k]:
                details[k] = v

        # Build simple description
        simple_desc = make_simple_description(row, idx, details)
        if not simple_desc and desc_html:
            # rudimentary clean paragraph fallback: strip tags, take first 2 sentences before "International Buyers"
            text = re.sub(r'<[^>]+>', ' ', desc_html)
            text = text.split("International Buyers")[0]
            text = re.sub(r'\\s+', ' ', text).strip()
            # take first ~250 chars
            simple_desc = text[:250] + ("..." if len(text) > 250 else "")

        # Compose Body (HTML)
        body = build_body_html(simple_desc, details, sku)

        # Price & images
        price = pick_price(row, idx)
        pic_key = idx.get('picurl') or idx.get('pictureurl') or idx.get('picurl1')
        pics = split_picurls(row.get(pic_key, "")) if pic_key else []

        base = {
            "Handle": handle,
            "Title": title,
            "Body (HTML)": body,
            "Vendor": vendor,
            "Type": "Watch",
            "Tags": tags,
            "Published": "TRUE",
            "Option1 Name": "Title",
            "Option1 Value": "Default Title",
            "Option2 Name": "",
            "Option2 Value": "",
            "Option3 Name": "",
            "Option3 Value": "",
            "Variant SKU": sku,
            "Variant Grams": "",
            "Variant Inventory Tracker": "",
            "Variant Inventory Qty": "",
            "Variant Inventory Policy": "deny",
            "Variant Fulfillment Service": "manual",
            "Variant Price": price,
            "Variant Compare-at Price": "",
            "Variant Requires Shipping": "TRUE",
            "Variant Taxable": "FALSE",
            "Variant Barcode": "",
            "Image Src": pics[0] if pics else "",
            "Image Alt Text": title
        }
        out_rows.append(base); kept += 1

        if len(pics) > 1:
            for extra in pics[1:]:
                out_rows.append({
                    "Handle": handle, "Title": "", "Body (HTML)": "", "Vendor": "", "Type": "", "Tags": "", "Published": "",
                    "Option1 Name": "", "Option1 Value": "", "Option2 Name": "", "Option2 Value": "", "Option3 Name": "", "Option3 Value": "",
                    "Variant SKU": "", "Variant Grams": "", "Variant Inventory Tracker": "", "Variant Inventory Qty": "", "Variant Inventory Policy": "", "Variant Fulfillment Service": "",
                    "Variant Price": "", "Variant Compare-at Price": "", "Variant Requires Shipping": "", "Variant Taxable": "", "Variant Barcode": "",
                    "Image Src": extra, "Image Alt Text": title
                })

    # Write CR-only, quote-all, sanitize embedded newlines to CR
    with open(outp, 'w', encoding='utf-8', newline='') as f:
        # header
        f.write(",".join(f'"{h}"' for h in OUT_HEADERS) + "\r")
        for r in out_rows:
            sanitized = {k: (str(r.get(k,"")).replace("\r\n","\r").replace("\n","\r")) for k in OUT_HEADERS}
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=OUT_HEADERS, quoting=csv.QUOTE_ALL)
            w.writerow(sanitized)
            content = buf.getvalue().replace("\r\n","\r").replace("\n","\r")
            f.write(content)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ebay_to_shopify_v5.py input.csv output.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])


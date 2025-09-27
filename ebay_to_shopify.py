
import csv, sys, re, html

def sniff_delimiter(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        sample = f.read(5000)
    # Prefer tab, else comma
    return '\t' if '\t' in sample and sample.count('\t') > sample.count(',') else ','

def normalize(s):
    if s is None:
        return ""
    # Trim and collapse internal whitespace
    return re.sub(r'\s+', ' ', str(s).strip())

def slugify(s):
    s = normalize(s).lower()
    s = re.sub(r'[^a-z0-9\-]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s

def choose_price(row):
    # Prefer BuyItNowPrice, else StartPrice
    for key in ['BuyItNowPrice', '*StartPrice', 'StartPrice']:
        if key in row and row[key]:
            try:
                val = float(str(row[key]).replace(',', '').strip())
                if val > 0:
                    return f"{val:.2f}"
            except:
                continue
    return ""

def split_pic_urls(s):
    if not s:
        return []
    # Split on pipe variants
    parts = [u.strip() for u in str(s).split('|') if u.strip()]
    return parts

def build_tags(row):
    # Collect reasonable product tags from eBay columns
    keys = [
        '*C:Brand', 'C:Brand', '*C:Model', 'C:Model', '*C:Reference Number', 'C:Reference Number',
        '*C:Movement', 'C:Movement', '*C:Case Material', 'C:Case Material',
        '*C:Band Material', 'C:Band Material', '*C:Dial Color', 'C:Dial Color',
        '*C:Year Manufactured', 'C:Year Manufactured', '*C:Department', 'C:Department',
        '*C:Type', 'C:Type'
    ]
    vals = []
    for k in keys:
        if k in row and row[k]:
            v = normalize(row[k])
            # Guard against super long HTML-ish junk
            if len(v) <= 80:
                vals.append(v)
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for v in vals:
        if v.lower() not in seen:
            seen.add(v.lower())
            deduped.append(v)
    return ", ".join(deduped)

def main(inp, outp):
    delim = sniff_delimiter(inp)
    with open(inp, 'r', encoding='utf-8', errors='ignore', newline='') as f:
        reader = csv.DictReader(f, delimiter=delim)
        rows = list(reader)

    headers = [
        "Handle","Title","Body (HTML)","Vendor","Type","Tags","Status",
        "Option1 Name","Option1 Value",
        "Variant SKU","Variant Price",
        "Image Src","Image Alt Text"
    ]
    out_rows = []

    for row in rows:
        if not row: 
            continue
        title = normalize(row.get('*Title') or row.get('Title'))
        if not title:
            # Skip lines without a Title (Shopify requires Title for create)
            continue

        # Use CustomLabel as SKU and Handle if present; else slug from title
        sku = normalize(row.get('CustomLabel'))
        handle = sku.lower() if sku else slugify(title)

        vendor = normalize(row.get('*C:Brand') or row.get('C:Brand'))
        prod_type = "Watch"  # Can be adjusted to "Preowned Watch", etc.
        tags = build_tags(row)

        body = row.get('*Description') or row.get('Description') or ""
        # Keep HTML as-is; ensure it's a string
        body = str(body)

        price = choose_price(row)

        pic_urls = split_pic_urls(row.get('PicURL') or row.get('PictureURL') or row.get('PicURL1'))

        # Base row (first image if any)
        base = {
            "Handle": handle,
            "Title": title,
            "Body (HTML)": body,
            "Vendor": vendor,
            "Type": prod_type,
            "Tags": tags,
            "Status": "active",
            "Option1 Name": "Title",
            "Option1 Value": "Default Title",
            "Variant SKU": sku,
            "Variant Price": price,
            "Image Src": pic_urls[0] if pic_urls else "",
            "Image Alt Text": title
        }
        out_rows.append(base)

        # Additional image rows: only Handle + Image Src (+ Alt Text optional)
        if pic_urls and len(pic_urls) > 1:
            for extra in pic_urls[1:]:
                out_rows.append({
                    "Handle": handle,
                    "Title": "",
                    "Body (HTML)": "",
                    "Vendor": "",
                    "Type": "",
                    "Tags": "",
                    "Status": "",
                    "Option1 Name": "",
                    "Option1 Value": "",
                    "Variant SKU": "",
                    "Variant Price": "",
                    "Image Src": extra,
                    "Image Alt Text": title
                })

    with open(outp, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in out_rows:
            writer.writerow(r)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ebay_to_shopify.py input.csv output.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])

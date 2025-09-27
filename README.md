# eBay → Shopify CSV Converter

A small, single-file Python utility that converts an **eBay File Exchange** CSV (the format you export from FileMaker for eBay) into a **Shopify Product Import CSV** tailored for **single, unique, preowned watches**.

- ✅ Uses your `CustomLabel` as both **SKU** and **Handle** (stable, unique).
- ✅ Preserves your HTML-rich eBay `*Description` as Shopify **Body (HTML)**.
- ✅ Prefers `BuyItNowPrice`, falls back to `*StartPrice` → **Variant Price**.
- ✅ Splits `PicURL` (`url1 | url2 | ...`) into multiple Shopify **Image Src** rows.
- ✅ Sets **Status** to `active` (configurable).
- ✅ Omits inventory columns (no tracking) by default—ideal for one-of-a-kind items.

> Built for: Palisade Jewelers’ catalog of **single** preowned watches (Rolex, Cartier, Patek, etc.), but easy to adapt for similar catalogs.

---

## Contents
- [Requirements](#requirements)
- [Installation](#installation)
- [Input Expectations](#input-expectations)
- [Shopify Output](#shopify-output)
- [Field Mapping](#field-mapping)
- [Usage](#usage)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Customization](#customization)
- [FAQ](#faq)
- [License](#license)

---

## Requirements
- Python **3.8+**
- No third-party packages (uses only the Python standard library).

---

## Installation
1. Download `ebay_to_shopify.py` into your project folder.
2. (Optional) Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

---

## Input Expectations

Your eBay CSV should include at least the following headers (names are case-sensitive and must match exactly as exported by File Exchange/FileMaker):

- `CustomLabel` — your SKU (e.g., `48123`).
- `*Title` — product title.
- `*Description` — HTML description (full eBay template is okay).
- `C:Brand` or `*C:Brand` — used as Shopify **Vendor**.
- `BuyItNowPrice` and/or `*StartPrice` — used for Shopify **Variant Price**.
- `PicURL` — one or more image URLs, separated by the pipe character (`|`).

The script **auto-detects** delimiter:
- Tab (`\t`) or comma (`,`). No need to change exports.

### Sample (abbreviated) eBay CSV

```csv
CustomLabel,*Title,*Description,C:Brand,BuyItNowPrice,*StartPrice,PicURL
48123,"Men's S/S Rolex Datejust, MOP, Ref. 116200","<html>...","Rolex",12350,9500,"https://.../48123-1.jpg | https://.../48123-2.jpg"
```

> You can include many more eBay columns; the converter will ignore what it doesn’t need and safely derive **Tags** from selected watch attributes (brand, model, ref, movement, era, gender, etc.).

---

## Shopify Output

The converter writes a **Shopify Product CSV** with **safe, minimal** columns for single-variant products. Columns:

- `Handle`
- `Title`
- `Body (HTML)`
- `Vendor`
- `Type`
- `Tags`
- `Status`
- `Option1 Name`
- `Option1 Value`
- `Variant SKU`
- `Variant Price`
- `Image Src`
- `Image Alt Text`

Key behaviors:
- **Multiple images**: Shopify requires additional image rows with only `Handle`, `Image Src` (and optionally `Image Alt Text`). The converter handles this automatically.
- **No inventory tracking**: by default, we omit inventory columns so Shopify won’t track quantity (ideal for one-of-a-kind items).

---

## Field Mapping

| eBay column | Shopify column | Notes |
|---|---|---|
| `CustomLabel` | `Handle` | Stable & unique; great for updates/overwrites. |
| `CustomLabel` | `Variant SKU` | Uses the same CustomLabel as SKU. |
| `*Title` | `Title` | Required by Shopify. |
| `*Description` | `Body (HTML)` | HTML preserved as-is. |
| `C:Brand` / `*C:Brand` | `Vendor` | e.g., Rolex, Cartier, Patek Philippe. |
| _(constant)_ | `Type` | Defaults to `Watch`. |
| _(derived: brand/model/ref/movement/size/era/gender)_ | `Tags` | Clean, short, comma-separated list. |
| `BuyItNowPrice` (fallback `*StartPrice`) | `Variant Price` | Uses BIN if positive; else StartPrice. |
| `PicURL` | `Image Src` | Splits on `|` into multiple rows. |
| _(constant)_ | `Status` | `active` by default. |
| _(constant)_ | `Option1 Name` | `Title` (required even for single-variant). |
| _(constant)_ | `Option1 Value` | `Default Title` (required even for single-variant). |

---

## Usage

```bash
python ebay_to_shopify.py input.csv shopify_products.csv
```

- `input.csv`: your eBay File Exchange export (tab- or comma-delimited).
- `shopify_products.csv`: the output file to import into Shopify.

### Import into Shopify
1. Go to **Shopify Admin → Products → Import**.
2. Upload `shopify_products.csv`.
3. (If updating existing items) check **“Overwrite products with matching handles.”**
4. Confirm and import.

---

## Examples

**Basic run:**

```bash
python ebay_to_shopify.py palisade_ebay_export.csv shopify_products.csv
```

**Then import** `shopify_products.csv` into Shopify. The products will be created **active** with images attached and your HTML description preserved.

---

## Troubleshooting

- **Illegal quoting / invalid CSV**: Ensure your input is **UTF-8** and columns aren’t broken by unescaped quotes. The output is always UTF-8.
- **Missing images**: Verify each `PicURL` is accessible over HTTPS. Use the full public URL.
- **Titles or prices missing**: Make sure `*Title` exists, and either `BuyItNowPrice` or `*StartPrice` has a numeric value.
- **Too many tags**: Keep tags short; avoid symbols like `|` or `;`. The script already filters and deduplicates common fields.
- **Inventory behavior**: By default, inventory is **not tracked**. If you want Shopify to show “sold out” automatically, see the customization section below.

---

## Customization

Open `ebay_to_shopify.py` and adjust constants near the top of the script:
- **Product Type**: change from `"Watch"` to `"Preowned Watch"` or a Shopify product category if you prefer.
- **Status**: set to `"draft"` during testing.
- **Tag sources**: edit the `build_tags()` key list to include/exclude attributes.
- **Inventory tracking**: if you want Shopify to track `1` unit and sell out:
  - Add columns: `Variant Inventory Tracker` = `shopify`, `Variant Inventory Policy` = `deny`, `Variant Inventory Qty` = `1`.
  - Optionally add `Published` and `Published Scope` if you manage sales channels explicitly.

---

## FAQ

**Q: Can I import Collections via CSV?**  
Shopify doesn’t have a first-class `Collection` column in the product CSV. Best practice: add tags (e.g., `Rolex`, `Datejust`, `2000-2009`) and create **Smart Collections** that include products matching those tags.

**Q: Can I update products later?**  
Yes. Keep the same `Handle` (we use `CustomLabel`) and choose “Overwrite products with matching handles” during import.

**Q: Can I include barcodes, grams, compare-at price, etc.?**  
Yes—extend the output columns in the script and map your eBay data accordingly.

---

## License

MIT © Palisade Jewelers / Ralph Esposito

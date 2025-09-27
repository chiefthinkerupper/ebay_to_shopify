# ebay_to_shopify Converter

A Python script that transforms your **eBay File Exchange export** into a **Shopify-ready CSV**, purpose-built for **unique preowned watches** sold by Palisade Jewelers.

---

## 🧭 Overview

This tool takes your **raw eBay export** (directly from FileMaker or eBay File Exchange) and outputs a **Shopify-compatible product CSV** that imports cleanly — no Excel editing required.

Version **v5** includes:
- ✅ Auto-detects and skips eBay template metadata rows  
- ✅ Fuzzy header mapping (handles `*Title`, `PicURL`, `C:Brand`, etc.)  
- ✅ Builds a **minimal, clean description** with a short intro sentence  
- ✅ Extracts **Item Details** (Serial, Model, Case, Dial, Size, SKU, etc.)  
- ✅ Removes long HTML boilerplate from eBay descriptions  
- ✅ Writes **CR-only (`\r`) line endings** and **quotes all fields** (Shopify requires this)  
- ✅ Works with one-of-a-kind products (no inventory tracking)

---

## 📦 Folder Structure

You only need:
```
/Users/ralph/Documents/ebay_to_shopify_script/
│
├── ebay_to_shopify_v5.py   ← the converter script  
├── input.csv               ← your eBay export file  
└── shopify_products.csv    ← output (Shopify-ready CSV)
```

> 💡 You can name `input.csv` whatever you want — just update the path when running the script.

---

## ⚙️ What the Script Does

- Cleans eBay HTML, keeping only **plain text + structured item details**
- Generates a **Shopify-ready CSV** with these key columns:
  - `Handle, Title, Body (HTML), Vendor, Type, Tags, Published, Option1 Name, Option1 Value, Variant SKU, Variant Price, Image Src, Image Alt Text`
- Each product row includes:
  - a short **description line** (e.g., “Preowned Rolex Datejust ref. 116200 36mm Automatic.”)
  - an **Item Details table** extracted from your eBay listing

---

## 🚀 How to Run It

### 🧠 Prerequisites
- Python **3.9+**
- Your eBay export saved as `input.csv`

### 💻 Command (macOS)
```bash
python /Users/ralph/Documents/ebay_to_shopify_script/ebay_to_shopify_v5.py /Users/ralph/Documents/ebay_to_shopify_script/input.csv /Users/ralph/Documents/ebay_to_shopify_script/shopify_products.csv
```

### 💻 Command (Windows PowerShell)
```powershell
python "C:\Users\Ralph\Documents\ebay_to_shopify_script\ebay_to_shopify_v5.py" `
       "C:\Users\Ralph\Documents\ebay_to_shopify_script\input.csv" `
       "C:\Users\Ralph\Documents\ebay_to_shopify_script\shopify_products.csv"
```

> ✅ The script will auto-detect tabs or commas and remove eBay’s header metadata automatically.

---

## 🛍️ Shopify Import Steps

1. Go to **Shopify Admin → Products → Import**
2. Upload **`shopify_products.csv`**  
   ⚠️ Do *not* open or re-save it in Excel/Numbers first
3. Preview → Import

You should see:
- Active products
- Images populated from URLs
- Descriptions with item details table

---

## 🧩 Key Behaviors

| Feature | Description |
|----------|--------------|
| **Images** | Uses `PicURL` (pipe-separated) |
| **SKU** | From `CustomLabel` |
| **Price** | From `BuyItNowPrice` or `StartPrice` |
| **Vendor** | From `C:Brand` |
| **Inventory** | Not tracked (unique items) |
| **Type** | Always “Watch” |
| **Tags** | Auto-built from key attributes |

---

## 🧱 Output Description Structure

Example:
```html
<p>Preowned Rolex Datejust ref. 116200 36mm Automatic.</p>
<h3>Item Details</h3>
<table class="item-details">
  <tr><td><strong>Serial Number:</strong></td><td>Z54xxxx</td></tr>
  <tr><td><strong>Model:</strong></td><td>Datejust</td></tr>
  <tr><td><strong>Case Type:</strong></td><td>Stainless Steel</td></tr>
  <tr><td><strong>Dial:</strong></td><td>Mother-of-Pearl</td></tr>
  ...
</table>
```

---

## 🧠 Troubleshooting

| Issue | Solution |
|-------|-----------|
| **No products generated** | Input missing recognizable headers — check that the header row contains `*Title`, `CustomLabel`, etc. |
| **Header mismatch error** | Always upload output CSV **without re-saving** in Excel. |
| **Newline errors** | v5 writes CR-only (`\r`) line endings — works with strict Shopify importers. |
| **"No inventory data" warning** | Expected (one-of-a-kind items, not tracked). |

---

## 🔧 Optional Enhancements
I can easily enable:
- ✅ **Auto sell-out** → `Variant Inventory Tracker = shopify`, `Qty = 1`, `Policy = deny`
- ✅ **Auto category** → `Standard Product Type = Watches in Jewelry`
- ✅ **Category metafields** → Age Group, Gender, Display, Features

Just ask and I’ll patch them into v6.

---

## 🧾 License
Recommended: **MIT License** (simple, permissive, perfect for internal use)

---

## 📄 Related Files

| File | Purpose |
|------|----------|
| `ebay_to_shopify_v5.py` | Main script |
| `input.csv` | Your eBay export |
| `shopify_products.csv` | Final Shopify import file |
| `ONE-PAGER.pdf` / `.docx` | Quick start documentation |

---

© 2025 Ralph Esposito – Custom Shopify Integration

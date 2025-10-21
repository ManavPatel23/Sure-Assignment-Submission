# 💳 Credit Card Statement Parser

A Python-based utility to **automatically parse and extract financial data** from credit card statements of multiple Indian and international banks.  
It supports automatic detection of the issuer, field extraction using regex, and JSON/CLI table output.

---

## 🏦 Supported Banks
- ICICI Bank  
- Axis Bank  
- IDFC FIRST Bank  
- RBL Bank  
- American Express  

---

## 📦 Requirements

Install dependencies using:

```bash
pip install PyPDF2 pdfplumber pandas tabulate
```

---

## ⚙️ Usage

You can parse individual or multiple PDF statements directly from the terminal.

### 1️⃣ Parse specific files
```bash
python parser.py statement1.pdf statement2.pdf
```

### 2️⃣ Parse all statements from a directory
```bash
python parser.py --dir ./statements/
```

### 3️⃣ Export parsed data as JSON
```bash
python parser.py statement.pdf --json output.json
```

### 4️⃣ Display output in a specific format
```bash
python parser.py statement.pdf --format summary
python parser.py statement.pdf --format table
python parser.py statement.pdf --format both
```

---

## 🧠 Features

- ✅ **Auto issuer detection** (ICICI, Axis, RBL, IDFC FIRST, AmEx)
- 🔍 **Regex-based field extraction**
- 📄 **PDF text extraction using `pdfplumber`**
- 📊 **Tabular and summary CLI views**
- 🖾 **Optional JSON export**
- ⚡ **Batch processing of multiple statements**
- 🧱 **Dataclass-based structured output**

---

## 🗳 Example Output

### CLI Summary:
```
Processing: icici_statement.pdf...
  ✓ ICICI Bank - success

================================================================================
PARSING SUMMARY
================================================================================

File: icici_statement.pdf
Issuer: ICICI Bank
Status: SUCCESS
--------------------------------------------------------------------------------
  Card Number         : 4375XXXXXXXX1234
  Statement Date      : 10 Oct 2024
  Payment Due Date    : 25 Oct 2024
  Total Amount Due    : ₹12,345.00
  Minimum Amount Due  : ₹500.00
  Credit Limit        : ₹1,00,000.00
  Available Credit    : ₹87,655.00
```

### Tabular Format:
```
================================================================================
PARSED DATA TABLE
================================================================================

+-----------------------+---------------+---------------------+-----------------+-------------------+--------------------+--------------------+----------------+
| file_name             | issuer        | card_number         | statement_date  | payment_due_date  | total_amount_due   | minimum_amount_due | parsing_status |
+-----------------------+---------------+---------------------+-----------------+-------------------+--------------------+--------------------+----------------+
| icici_statement.pdf   | ICICI Bank    | 4375XXXXXXXX1234    | 10 Oct 2024     | 25 Oct 2024       | 12,345.00          | 500.00             | success        |
+-----------------------+---------------+---------------------+-----------------+-------------------+--------------------+--------------------+----------------+
```

---

## 🧹 JSON Output Example
```json
[
  {
    "file_name": "icici_statement.pdf",
    "issuer": "ICICI Bank",
    "card_number": "4375XXXXXXXX1234",
    "statement_date": "10 Oct 2024",
    "payment_due_date": "25 Oct 2024",
    "total_amount_due": "12345.00",
    "minimum_amount_due": "500.00",
    "credit_limit": "100000.00",
    "available_credit": "87655.00",
    "previous_balance": null,
    "parsing_status": "success",
    "errors": []
  }
]
```

---

## 📁 Project Structure

```
├── parser.py
├── README.md
├── requirements.txt
└── statements/
    ├── icici_statement.pdf
    ├── axis_statement.pdf
    └── ...
```

---

## 🚀 Future Enhancements
- 🔹 Add OCR extraction for scanned PDFs (using Gemini or Tesseract)
- 🔹 Support for HDFC, SBI, and other banks
- 🔹 Web dashboard or API interface
- 🔹 Export to CSV/Excel formats

---

## 👨‍💻 Author
**Manav Patel**

📧 Email: [manav.p2305@gmail.com]  

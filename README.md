# 🚗 T-Comparto Monthly Kilometer Report Automation

This Python project automates the extraction, processing, and reporting of event data and travel distances for a monthly **kilometer report** for the T-Comparto app (you must have access to this application in order for this program to work). It integrates data from an Android device and Google Maps to calculate distances between event locations, generating both PDF and TXT reports.

---

## 🚀 Key Features

### 🔹 Data Extraction & Processing

- Connects to an Android device using UI automation tools to extract:
  - Event times
  - Event addresses
  - Participant names
- Cleans and standardizes address data.
- Calculates travel distances between consecutive events using **Google Maps**, automated via **Selenium** and a headless browser.

### 🔹 Reporting & Output

- Stores event data and calculated distances in `.txt` files for record-keeping.
- Generates structured **PDF reports** using **PyMuPDF**, including:
  - Event date
  - Address (origin → destination)
  - Distance
  - Total kilometers per report
- Automatically paginates multi-page reports and inserts page numbers.
- Implements caching to avoid redundant Google Maps queries.

### 🔹 Error Handling & Validation

- Validates user input (e.g. valid month).
- Handles data inconsistencies and missing fields gracefully.
- Provides console logs and supports GUI status updates during processing.

---

## 🛠️ How to Run

1. **Install dependencies**:
   ```bash
   pip install selenium pymupdf
   ```

2. **Prepare your environment**:

   * Install USB drivers for your device.
   * Connect a compatible Android device via USB with developer mode and USB debugging enabled.
   * Install necessary automation tools (e.g. `uiautomator`).
   * Set up the project directory structure (see below).

4. **Run the application**:

   ```bash
   python main_gui.py
   ```

   * A GUI will open where you can select the target month.
   * The program will extract the data and generate the kilometraje reports.

---

## 📁 Project Structure

```
project/
│
├── main_gui.py                # GUI entry point (Tkinter)
├── process_events.py          # Main event handling logic
├── km_utils.py                # Distance & PDF writing utilities
├── gmaps_utils.py             # Google Maps automation with Selenium
├── android_ui_utils.py        # Android device automation
├── file_utils.py              # File and folder manipulation functions
├── files/
│   ├── input/
│   │   └── km_document_model.pdf  # PDF template
│   └── output/
│       ├── kilometre_reports_pdf/
│       └── kilometre_reports_txt/
└── README.md
```

---

## 📌 Notes

* The app requires **Google Maps access**, which is automated through a headless Firefox browser.
* You can adapt the code to other regions or add additional event filters as needed.

---

## 📄 Example Output

* `km_06_2025.txt`

  ```
  15/06/2025; Calle Falsa 123; Avenida Siempre Viva 742; 8.5 km
  ...
  ```

* `06_2025_page_1.pdf`
  A visually structured PDF showing event details and total kilometers.

---

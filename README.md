# BH Auction Scraper

This is a Python scraper for **BHAuction.com**, specifically for scraping auction lot details and auction-level information.  
It extracts structured data for each lot, including vehicle details, price, currency, images, and auction metadata.

---

## Features

- Scrapes **auction-level information**:
  - Auction title
  - Auction date
  - Auction location
  - Auctioneer name

- Scrapes **lot-level information**:
  - Lot number
  - Lot title & description
  - Estimate price (low, high) and currency
  - Price type (sold / highest bid)
  - Vehicle information:
    - Chassis number
    - Mileage
    - Year
    - Body color
    - Transmission type
    - Steering position
    - Convertible status
  - Images (all non-logo images)

- Handles special cases:
  - Lots marked **"SOLD AFTER AUCTION"**
  - Lots with no estimate
  - Multiline price formatting with `<br>` tags

- Produces a **JSON output** with structured fields following a schema.

---

## Setup Instructions

Follow these steps to run the scraper in a clean Python environment.

### 1. Clone the repository

```bash
git https://github.com/Kaleb-Abiy/lot-scraper
cd lot-scraper
```

### 2. Create and activate virtual environment

- For Linux

```
python3 -m venv venv
source venv/bin/activate
```

- For Windows
```
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Run the scraper

```
python main.py
```






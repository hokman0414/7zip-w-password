# Job Tracker (local PC)

Simple job application tracker that runs on your computer. All data stays in a local SQLite file — nothing is uploaded.

## What it does

- Add / edit / delete applications
- Track status: Wishlist → Applied → Screening → Interview → Offer / Rejected / Withdrawn
- Search and filter
- Store company, role, location, job URL, salary, follow-up date, notes
- Highlight overdue follow-ups

## Run on Windows / Mac / Linux

1. Install [Python 3](https://www.python.org/downloads/) (on Windows, check **Add Python to PATH**).
2. Open a terminal in this folder.
3. Install and start:

```bash
python -m pip install -r requirements.txt
python app.py
```

4. Open **http://127.0.0.1:5050** in your browser.

Data file: `data/applications.db`

## Windows quick start

Double-click `start.bat`, or from Command Prompt:

```bat
python -m pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5050

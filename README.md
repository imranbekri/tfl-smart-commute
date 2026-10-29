# TfL Smart Commute

A practical London commute companion built with **Python**, **FastAPI** and **Jinja2**.

Quickly see live status for Tube, Overground, Elizabeth line and DLR, and check whether your saved journeys are affected by disruptions.

## Features

- [x] Live TfL line status with clean summary and detailed list
- [x] Filter: All lines / Disruptions only
- [x] Save, edit and delete personal journeys
- [x] Live status shown for the lines used by each saved journey
- [x] Clear indicator showing whether each saved journey is affected
- [x] Persistent storage with SQLite
- [x] Load journeys from SQLite on startup

## Tech Stack

- Python 3.11+
- FastAPI
- Jinja2
- httpx (TfL API)
- SQLite
- TfL Unified API

## Getting Started

```bash
git clone https://github.com/imranbek22-afk/tfl-smart-commute.git
cd tfl-smart-commute
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000

**Note:** Journeys are stored in a local SQLite database (`journeys.db`). They are loaded from the database when the application starts and survive server restarts. New journeys are saved to the database, and deleted journeys are removed from it. Edits are also saved to the database.

## Project Structure

```
tfl-smart-commute/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── tfl.py
│   └── templates/
│       └── index.html
├── requirements.txt
└── README.md
```

## Licence

Personal project / educational use.

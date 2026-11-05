# TfL Smart Commute

A practical London commute companion built with **Python**, **FastAPI** and **Jinja2**.

Quickly see live status for Tube, Overground, Elizabeth line and DLR, and check whether your saved journeys are affected by disruptions.

## Features

- Live TfL line status with clean summary and detailed list
- Filter: All lines / Disruptions only
- Save, edit and delete personal journeys
- Live status shown for the lines used by each saved journey
- Clear indicator showing whether each saved journey is affected
- Persistent storage with SQLite (journeys survive server restarts)
- Graceful handling of TfL API timeouts, outages and database errors

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- Jinja2 templates
- httpx (TfL Unified API client)
- SQLite

No API key is required for the public line-status endpoint used by this app.

## Getting Started

```bash
git clone https://github.com/imranbek22-afk/tfl-smart-commute.git
cd tfl-smart-commute
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000)

**Note:** Journeys are stored in a local SQLite database (`journeys.db`) in the project root. They are loaded automatically on startup and persist across server restarts. The database file is excluded from version control.

## Project Structure

```
tfl-smart-commute/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and routes
│   ├── database.py      # SQLite persistence helpers
│   ├── tfl.py           # TfL API client
│   └── templates/
│       └── index.html   # Single-page UI
├── requirements.txt
├── .gitignore
└── README.md
```

## Author

Built by Imran Bekri — a practical tool for London commuters.

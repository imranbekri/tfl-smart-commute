from datetime import datetime

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from app.tfl import get_line_statuses, TfLError, TfLTimeoutError, TfLUnavailableError
from app.database import init_db

app = FastAPI(title="TfL Smart Commute")
templates = Jinja2Templates(directory="app/templates")

# Initialise the SQLite database and journeys table on startup
init_db()

# Simple in-memory store for journeys (will be replaced by SQLite)
journeys: list[dict] = []


def _severity_from_description(desc: str) -> str:
    """Map TfL status description to a severity class used by the UI."""
    if desc == "Good Service":
        return "good"
    if desc in ["Minor Delays", "Reduced Service", "Special Service", "Change of frequency"]:
        return "minor"
    if desc in ["Severe Delays", "Part Suspended", "Suspended", "Part Closure", "Part Closed", "Issues Reported"]:
        return "severe"
    if desc in ["Closed", "Planned Closure", "No Service", "Not Running"]:
        return "closed"
    return "minor"


def build_status_lookup(lines: list) -> dict[str, dict]:
    """Build a case-insensitive lookup of line name → status info."""
    lookup: dict[str, dict] = {}
    for line in lines:
        name = (line.get("name") or "").strip()
        if not name:
            continue
        statuses = line.get("lineStatuses") or []
        status = statuses[0] if statuses else {}
        desc = status.get("statusSeverityDescription") or "Unknown"
        reason = status.get("reason") or ""
        lookup[name.lower()] = {
            "name": name,
            "description": desc,
            "reason": reason,
            "severity": _severity_from_description(desc),
        }
    return lookup


def enrich_journeys(journeys_list: list[dict], status_lookup: dict[str, dict]) -> list[dict]:
    """Attach live line status info to each journey."""
    enriched: list[dict] = []
    for journey in journeys_list:
        j = journey.copy()
        line_statuses: list[dict] = []
        for raw_name in journey.get("lines") or []:
            key = raw_name.lower().strip()
            info = status_lookup.get(key)
            # Soft match: strip common suffixes or partial containment
            if not info:
                cleaned = key.removesuffix(" line").strip()
                info = status_lookup.get(cleaned)
            if not info:
                for lk, lv in status_lookup.items():
                    if key in lk or lk in key or cleaned in lk:
                        info = lv
                        break
            if info:
                line_statuses.append(info)
            else:
                line_statuses.append({
                    "name": raw_name,
                    "description": "Unknown",
                    "reason": "",
                    "severity": "unknown",
                })
        j["line_statuses"] = line_statuses
        # Overall journey health
        severities = {ls["severity"] for ls in line_statuses}
        if "severe" in severities or "closed" in severities:
            j["overall"] = "severe"
        elif "minor" in severities:
            j["overall"] = "minor"
        elif line_statuses and all(s == "good" for s in severities):
            j["overall"] = "good"
        else:
            j["overall"] = "unknown"
        # Specific disrupted lines so journey cards can show exactly which ones are affected
        j["disrupted_lines"] = [
            ls["name"]
            for ls in line_statuses
            if ls["severity"] in ("minor", "severe", "closed")
        ]
        enriched.append(j)
    return enriched


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    lines: list = []
    error: str | None = None

    try:
        lines = await get_line_statuses()
    except TfLTimeoutError as e:
        error = e.user_message
    except TfLUnavailableError as e:
        error = e.user_message
    except TfLError as e:
        error = e.user_message
    except Exception:
        # Catch-all so the page never crashes
        error = "Something went wrong while fetching line statuses. Please try again later."

    status_lookup = build_status_lookup(lines)
    enriched = enrich_journeys(journeys, status_lookup)

    # Simple success messages from redirects
    message = None
    msg_type = None
    if request.query_params.get("saved"):
        message = "Journey saved."
        msg_type = "success"
    elif request.query_params.get("deleted"):
        message = "Journey deleted."
        msg_type = "success"
    elif request.query_params.get("edited"):
        message = "Journey updated."
        msg_type = "success"

    last_updated = datetime.now().strftime("%H:%M")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "lines": lines,
            "error": error,
            "journeys": enriched,
            "message": message,
            "msg_type": msg_type,
            "last_updated": last_updated,
        },
    )


@app.post("/add-journey")
async def add_journey(
    request: Request,
    name: str = Form(...),
    origin: str = Form(...),
    destination: str = Form(...),
    lines: str = Form(""),
):
    """Store a new journey in memory with validation."""
    name = name.strip()
    origin = origin.strip()
    destination = destination.strip()
    lines_list = [line.strip() for line in lines.split(",") if line.strip()]

    form_errors: list[str] = []

    if len(name) < 2:
        form_errors.append("Journey name must be at least 2 characters.")
    if len(origin) < 2:
        form_errors.append("Origin must be at least 2 characters.")
    if len(destination) < 2:
        form_errors.append("Destination must be at least 2 characters.")
    if origin.lower() == destination.lower():
        form_errors.append("Origin and destination cannot be the same.")

    if form_errors:
        # Re-render the page with form errors and previous values
        lines_data: list = []
        error: str | None = None
        try:
            lines_data = await get_line_statuses()
        except (TfLTimeoutError, TfLUnavailableError, TfLError) as e:
            error = e.user_message
        except Exception:
            error = "Something went wrong while fetching line statuses. Please try again later."

        status_lookup = build_status_lookup(lines_data)
        enriched = enrich_journeys(journeys, status_lookup)

        last_updated = datetime.now().strftime("%H:%M")

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "lines": lines_data,
                "error": error,
                "journeys": enriched,
                "form_errors": form_errors,
                "form_data": {
                    "name": name,
                    "origin": origin,
                    "destination": destination,
                    "lines": lines,
                },
                "last_updated": last_updated,
            },
            status_code=400,
        )

    journey = {
        "name": name,
        "origin": origin,
        "destination": destination,
        "lines": lines_list,
    }
    journeys.append(journey)
    return RedirectResponse(url="/?saved=1", status_code=303)


@app.post("/delete-journey")
async def delete_journey(index: int = Form(...)):
    """Remove a journey from memory by its list index."""
    try:
        if 0 <= index < len(journeys):
            journeys.pop(index)
    except (ValueError, IndexError):
        pass  # Ignore invalid indices
    return RedirectResponse(url="/?deleted=1", status_code=303)


@app.post("/edit-journey")
async def edit_journey(
    request: Request,
    index: int = Form(...),
    name: str = Form(...),
    origin: str = Form(...),
    destination: str = Form(...),
    lines: str = Form(""),
):
    """Update an existing journey (name, route and lines) with validation."""
    name = name.strip()
    origin = origin.strip()
    destination = destination.strip()
    lines_list = [line.strip() for line in lines.split(",") if line.strip()]

    form_errors: list[str] = []

    if not (0 <= index < len(journeys)):
        form_errors.append("Invalid journey.")
    if len(name) < 2:
        form_errors.append("Journey name must be at least 2 characters.")
    if len(origin) < 2:
        form_errors.append("Origin must be at least 2 characters.")
    if len(destination) < 2:
        form_errors.append("Destination must be at least 2 characters.")
    if origin.lower() == destination.lower():
        form_errors.append("Origin and destination cannot be the same.")

    if form_errors:
        # Re-render with errors
        lines_data: list = []
        error: str | None = None
        try:
            lines_data = await get_line_statuses()
        except (TfLTimeoutError, TfLUnavailableError, TfLError) as e:
            error = e.user_message
        except Exception:
            error = "Something went wrong while fetching line statuses. Please try again later."

        status_lookup = build_status_lookup(lines_data)
        enriched = enrich_journeys(journeys, status_lookup)
        last_updated = datetime.now().strftime("%H:%M")

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "lines": lines_data,
                "error": error,
                "journeys": enriched,
                "form_errors": form_errors,
                "last_updated": last_updated,
            },
            status_code=400,
        )

    journeys[index]["name"] = name
    journeys[index]["origin"] = origin
    journeys[index]["destination"] = destination
    journeys[index]["lines"] = lines_list
    return RedirectResponse(url="/?edited=1", status_code=303)

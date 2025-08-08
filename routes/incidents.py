import json
import time
from pathlib import Path
from flask import Blueprint, request, render_template, redirect, url_for, flash
from services.incident_validator import REQUIRED_BY_TYPE, compute_completeness, validate_record

DATA_DIR = Path("data")
INCIDENTS_JSON = DATA_DIR / "incidents.json"
incidents_bp = Blueprint("incidents", __name__, template_folder="../templates")

def load_incidents():
    if INCIDENTS_JSON.exists():
        return json.loads(INCIDENTS_JSON.read_text())
    return {}

def save_incidents(obj):
    INCIDENTS_JSON.write_text(json.dumps(obj, indent=2))

@incidents_bp.get("/")
def list_incidents():
    items = load_incidents()
    rows = []
    for iid, rec in items.items():
        rows.append({
            "id": iid,
            "type": rec.get("type"),
            "created_ts": rec.get("created_ts"),
            "completeness": compute_completeness(rec),
            "status": rec.get("status", "draft"),
        })
    rows = sorted(rows, key=lambda r: r["created_ts"], reverse=True)
    return render_template("incidents_list.html", rows=rows, required_by_type=REQUIRED_BY_TYPE)

@incidents_bp.route("/new", methods=["GET", "POST"])
def new_incident():
    if request.method == "GET":
        return render_template("incident_new.html")
    data = {
        "id": str(int(time.time()*1000)),
        "type": request.form.get("type") or "other",
        "answers": {
            "people": request.form.get("people") or "",
            "environment": request.form.get("environment") or "",
            "cost": request.form.get("cost") or "",
            "legal": request.form.get("legal") or "",
            "reputation": request.form.get("reputation") or "",
        },
        "created_ts": time.time(),
        "status": "draft"
    }
    items = load_incidents()
    items[data["id"]] = data
    save_incidents(items)
    flash("Incident created (draft). Continue filling it.", "success")
    return redirect(url_for("incidents.edit_incident", iid=data["id"]))

@incidents_bp.route("/<iid>/edit", methods=["GET", "POST"])
def edit_incident(iid):
    items = load_incidents()
    rec = items.get(iid)
    if not rec:
        flash("Incident not found", "danger")
        return redirect(url_for("incidents.list_incidents"))

    if request.method == "POST":
        rec["type"] = request.form.get("type") or rec["type"]
        for cat in ["people", "environment", "cost", "legal", "reputation"]:
            rec["answers"][cat] = request.form.get(cat) or rec["answers"].get(cat, "")
        # Try validation
        ok, missing = validate_record(rec)
        rec["status"] = "complete" if ok else "incomplete"
        items[iid] = rec
        save_incidents(items)
        if ok:
            flash("Incident validated and marked complete ✔", "success")
        else:
            flash(f"Missing required categories for type {rec['type']}: {', '.join(missing)}", "warning")
        return redirect(url_for("incidents.edit_incident", iid=iid))

    completeness = compute_completeness(rec)
    ok, missing = validate_record(rec)
    return render_template(
        "incident_edit.html",
        rec=rec, completeness=completeness, ok=ok, missing=missing, required_by_type=REQUIRED_BY_TYPE
    )


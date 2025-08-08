import json
import time
from pathlib import Path
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify

safety_concerns_bp = Blueprint("safety_concerns", __name__)

@safety_concerns_bp.route("/")
def concerns_list():
    concerns = load_safety_concerns()
    # Convert to list and sort by created date
    concern_list = sorted(concerns.values(), key=lambda x: x.get("created_date", 0), reverse=True)
    return render_template("safety_concerns_list.html", concerns=concern_list)

@safety_concerns_bp.route("/new", methods=["GET", "POST"])
def new_concern():
    if request.method == "GET":
        concern_type = request.args.get("type", "concern")
        return render_template("safety_concern_new.html", concern_type=concern_type)
    
    concern_data = {
        "id": str(int(time.time() * 1000)),
        "type": request.form.get("type", "concern"),
        "title": request.form.get("title", ""),
        "description": request.form.get("description", ""),
        "location": request.form.get("location", ""),
        "hazard_type": request.form.get("hazard_type", ""),
        "immediate_action": request.form.get("immediate_action", ""),
        "anonymous": request.form.get("anonymous") == "on",
        "reporter": "" if request.form.get("anonymous") == "on" else request.form.get("reporter", ""),
        "created_date": time.time(),
        "status": "reported",
        "assigned_to": "",
        "risk_level": request.form.get("risk_level", "medium"),
        "priority": "medium"
    }
    
    save_safety_concern(concern_data)
    flash("Safety concern submitted successfully. Thank you for speaking up!", "success")
    
    if concern_data["anonymous"]:
        return redirect(url_for("safety_concerns.concerns_list"))
    else:
        return redirect(url_for("safety_concerns.concern_detail", concern_id=concern_data["id"]))

@safety_concerns_bp.route("/<concern_id>")
def concern_detail(concern_id):
    concerns = load_safety_concerns()
    concern = concerns.get(concern_id)
    if not concern:
        flash("Safety concern not found", "error")
        return redirect(url_for("safety_concerns.concerns_list"))
    return render_template("safety_concern_detail.html", concern=concern)

@safety_concerns_bp.route("/<concern_id>/update", methods=["POST"])
def update_concern(concern_id):
    concerns = load_safety_concerns()
    concern = concerns.get(concern_id)
    
    if not concern:
        flash("Safety concern not found", "error")
        return redirect(url_for("safety_concerns.concerns_list"))
    
    # Add update to history
    update = {
        "timestamp": time.time(),
        "user": request.form.get("updated_by", "System"),
        "comment": request.form.get("comment", ""),
        "status_change": request.form.get("status") != concern.get("status"),
        "old_status": concern.get("status"),
        "new_status": request.form.get("status")
    }
    
    if "updates" not in concern:
        concern["updates"] = []
    concern["updates"].append(update)
    
    # Update fields
    concern["status"] = request.form.get("status", concern["status"])
    concern["assigned_to"] = request.form.get("assigned_to", concern["assigned_to"])
    concern["priority"] = request.form.get("priority", concern["priority"])
    
    concerns[concern_id] = concern
    save_safety_concerns(concerns)
    
    flash("Safety concern updated successfully", "success")
    return redirect(url_for("safety_concerns.concern_detail", concern_id=concern_id))

def save_safety_concern(concern_data):
    data_dir = Path("data")
    concerns_file = data_dir / "safety_concerns.json"
    
    if concerns_file.exists():
        concerns = json.loads(concerns_file.read_text())
    else:
        concerns = {}
    
    concerns[concern_data["id"]] = concern_data
    save_safety_concerns(concerns)

def save_safety_concerns(concerns):
    data_dir = Path("data")
    concerns_file = data_dir / "safety_concerns.json"
    data_dir.mkdir(exist_ok=True)
    concerns_file.write_text(json.dumps(concerns, indent=2))

def load_safety_concerns():
    concerns_file = Path("data/safety_concerns.json")
    if concerns_file.exists():
        return json.loads(concerns_file.read_text())
    return {}

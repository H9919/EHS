# routes/chatbot.py - AI Chatbot Interface
from flask import Blueprint, request, jsonify, render_template
from services.ehs_chatbot import EHSChatbot

chatbot_bp = Blueprint("chatbot", __name__)
chatbot = EHSChatbot()

@chatbot_bp.route("/chat", methods=["GET", "POST"])
def chat_interface():
    if request.method == "GET":
        return render_template("chatbot.html")
    
    data = request.get_json()
    user_message = data.get("message", "")
    user_id = data.get("user_id")
    
    response = chatbot.process_message(user_message, user_id)
    return jsonify(response)

@chatbot_bp.route("/chat/history")
def chat_history():
    return jsonify(chatbot.conversation_history[-20:])

@chatbot_bp.route("/chat/summary")
def chat_summary():
    return jsonify(chatbot.get_conversation_summary())

# routes/safety_concerns.py - Safety Concern Reporting (OSCR)
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

# routes/risk.py - Risk Management
from flask import Blueprint
from services.risk_matrix import LIKELIHOOD_SCALE, SEVERITY_SCALE, calculate_risk_score, get_risk_level

risk_bp = Blueprint("risk", __name__)

@risk_bp.route("/assess", methods=["GET", "POST"])
def risk_assessment():
    if request.method == "GET":
        return render_template("risk_assessment.html", 
                             likelihood_scale=LIKELIHOOD_SCALE,
                             severity_scale=SEVERITY_SCALE)
    
    likelihood = int(request.form.get("likelihood", 0))
    severity_scores = {
        "people": int(request.form.get("severity_people", 0)),
        "environment": int(request.form.get("severity_environment", 0)),
        "cost": int(request.form.get("severity_cost", 0)),
        "reputation": int(request.form.get("severity_reputation", 0)),
        "legal": int(request.form.get("severity_legal", 0))
    }
    
    risk_score = calculate_risk_score(likelihood, severity_scores)
    risk_level = get_risk_level(risk_score)
    
    risk_data = {
        "id": str(int(time.time() * 1000)),
        "title": request.form.get("title", ""),
        "description": request.form.get("description", ""),
        "likelihood": likelihood,
        "severity_scores": severity_scores,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "created_date": time.time(),
        "created_by": request.form.get("created_by", "Current User"),
        "status": "active"
    }
    
    save_risk_assessment(risk_data)
    flash(f"Risk assessment completed. Risk Level: {risk_level} (Score: {risk_score})", "info")
    
    return render_template("risk_result.html", 
                         risk_data=risk_data,
                         likelihood_scale=LIKELIHOOD_SCALE,
                         severity_scale=SEVERITY_SCALE)

@risk_bp.route("/register")
def risk_register():
    risks = load_risk_assessments()
    risk_list = sorted(risks.values(), key=lambda x: x.get("created_date", 0), reverse=True)
    return render_template("risk_register.html", risks=risk_list)

@risk_bp.route("/<risk_id>")
def risk_detail(risk_id):
    risks = load_risk_assessments()
    risk = risks.get(risk_id)
    if not risk:
        flash("Risk assessment not found", "error")
        return redirect(url_for("risk.risk_register"))
    return render_template("risk_detail.html", risk=risk)

def save_risk_assessment(risk_data):
    data_dir = Path("data")
    risk_file = data_dir / "risk_assessments.json"
    
    if risk_file.exists():
        risks = json.loads(risk_file.read_text())
    else:
        risks = {}
    
    risks[risk_data["id"]] = risk_data
    
    data_dir.mkdir(exist_ok=True)
    risk_file.write_text(json.dumps(risks, indent=2))

def load_risk_assessments():
    risk_file = Path("data/risk_assessments.json")
    if risk_file.exists():
        return json.loads(risk_file.read_text())
    return {}

# routes/audits.py - Audits & Inspections
audits_bp = Blueprint("audits", __name__)

@audits_bp.route("/")
def audits_list():
    audits = load_audits()
    audit_list = sorted(audits.values(), key=lambda x: x.get("created_date", 0), reverse=True)
    return render_template("audits_list.html", audits=audit_list)

@audits_bp.route("/new", methods=["GET", "POST"])
def new_audit():
    if request.method == "GET":
        audit_templates = get_audit_templates()
        return render_template("audit_new.html", templates=audit_templates)
    
    audit_data = {
        "id": str(int(time.time() * 1000)),
        "title": request.form.get("title"),
        "type": request.form.get("type"),
        "template": request.form.get("template"),
        "auditor": request.form.get("auditor"),
        "location": request.form.get("location"),
        "scheduled_date": request.form.get("scheduled_date"),
        "status": "scheduled",
        "created_date": time.time(),
        "checklist_items": get_checklist_for_template(request.form.get("template")),
        "findings": [],
        "score": 0
    }
    
    save_audit(audit_data)
    flash(f"Audit {audit_data['id']} scheduled successfully", "success")
    return redirect(url_for("audits.audit_detail", audit_id=audit_data["id"]))

@audits_bp.route("/<audit_id>")
def audit_detail(audit_id):
    audits = load_audits()
    audit = audits.get(audit_id)
    if not audit:
        flash("Audit not found", "error")
        return redirect(url_for("audits.audits_list"))

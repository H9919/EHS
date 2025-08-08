# routes/capa.py - Corrective and Preventive Actions
import json
import time
from pathlib import Path
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from services.capa_manager import CAPAManager

capa_bp = Blueprint("capa", __name__)
capa_manager = CAPAManager()

@capa_bp.route("/")
def capa_list():
    capas = capa_manager.load_capas()
    return render_template("capa_list.html", capas=capas.values())

@capa_bp.route("/new", methods=["GET", "POST"])
def new_capa():
    if request.method == "GET":
        return render_template("capa_new.html")
    
    capa_data = {
        "title": request.form.get("title"),
        "description": request.form.get("description"),
        "type": request.form.get("type"),
        "assignee": request.form.get("assignee"),
        "due_date": request.form.get("due_date"),
        "priority": request.form.get("priority"),
        "created_by": request.form.get("created_by", "Current User")
    }
    
    capa_id = capa_manager.create_capa(capa_data)
    flash(f"CAPA {capa_id} created successfully", "success")
    return redirect(url_for("capa.capa_detail", capa_id=capa_id))

@capa_bp.route("/<capa_id>")
def capa_detail(capa_id):
    capas = capa_manager.load_capas()
    capa = capas.get(capa_id)
    if not capa:
        flash("CAPA not found", "error")
        return redirect(url_for("capa.capa_list"))
    return render_template("capa_detail.html", capa=capa)

@capa_bp.route("/<capa_id>/update", methods=["POST"])
def update_capa(capa_id):
    update_data = {
        "status": request.form.get("status"),
        "comment": request.form.get("comment"),
        "updated_by": request.form.get("updated_by", "Current User")
    }
    
    if capa_manager.update_capa(capa_id, update_data):
        flash("CAPA updated successfully", "success")
    else:
        flash("Failed to update CAPA", "error")
    
    return redirect(url_for("capa.capa_detail", capa_id=capa_id))

@capa_bp.route("/dashboard")
def capa_dashboard():
    capas = capa_manager.load_capas()
    overdue = capa_manager.get_overdue_capas()
    
    stats = {
        "total": len(capas),
        "open": len([c for c in capas.values() if c["status"] == "open"]),
        "in_progress": len([c for c in capas.values() if c["status"] == "in_progress"]),
        "overdue": len(overdue)
    }
    
    return render_template("capa_dashboard.html", stats=stats, overdue=overdue)

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
    
    # Process risk assessment form
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
    
    # Save risk assessment
    risk_data = {
        "id": str(int(time.time() * 1000)),
        "title": request.form.get("title", ""),
        "description": request.form.get("description", ""),
        "likelihood": likelihood,
        "severity_scores": severity_scores,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "created_date": time.time(),
        "created_by": request.form.get("created_by", "Current User")
    }
    
    # Save to file (similar to incidents)
    save_risk_assessment(risk_data)
    
    return render_template("risk_result.html", 
                         risk_data=risk_data,
                         likelihood_scale=LIKELIHOOD_SCALE,
                         severity_scale=SEVERITY_SCALE)

@risk_bp.route("/register")
def risk_register():
    risks = load_risk_assessments()
    return render_template("risk_register.html", risks=risks)

def save_risk_assessment(risk_data):
    """Save risk assessment to JSON file"""
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
    """Load risk assessments from JSON file"""
    risk_file = Path("data/risk_assessments.json")
    if risk_file.exists():
        return json.loads(risk_file.read_text())
    return {}

# routes/safety_concerns.py - Safety Concern Reporting (OSCR)
safety_concerns_bp = Blueprint("safety_concerns", __name__)

@safety_concerns_bp.route("/")
def concerns_list():
    concerns = load_safety_concerns()
    return render_template("safety_concerns_list.html", concerns=concerns.values())

@safety_concerns_bp.route("/new", methods=["GET", "POST"])
def new_concern():
    if request.method == "GET":
        return render_template("safety_concern_new.html")
    
    concern_data = {
        "id": str(int(time.time() * 1000)),
        "type": request.form.get("type", "concern"),  # concern, recognition
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
        "risk_level": "medium"
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

def save_safety_concern(concern_data):
    """Save safety concern to JSON file"""
    data_dir = Path("data")
    concerns_file = data_dir / "safety_concerns.json"
    
    if concerns_file.exists():
        concerns = json.loads(concerns_file.read_text())
    else:
        concerns = {}
    
    concerns[concern_data["id"]] = concern_data
    
    data_dir.mkdir(exist_ok=True)
    concerns_file.write_text(json.dumps(concerns, indent=2))

def load_safety_concerns():
    """Load safety concerns from JSON file"""
    concerns_file = Path("data/safety_concerns.json")
    if concerns_file.exists():
        return json.loads(concerns_file.read_text())
    return {}

# routes/audits.py - Audits & Inspections
audits_bp = Blueprint("audits", __name__)

@audits_bp.route("/")
def audits_list():
    audits = load_audits()
    return render_template("audits_list.html", audits=audits.values())

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
    return render_template("audit_detail.html", audit=audit)

@audits_bp.route("/<audit_id>/conduct", methods=["GET", "POST"])
def conduct_audit(audit_id):
    audits = load_audits()
    audit = audits.get(audit_id)
    
    if not audit:
        flash("Audit not found", "error")
        return redirect(url_for("audits.audits_list"))
    
    if request.method == "GET":
        return render_template("audit_conduct.html", audit=audit)
    
    # Process audit responses
    responses = {}
    findings = []
    total_score = 0
    max_score = 0
    
    for item in audit["checklist_items"]:
        response = request.form.get(f"item_{item['id']}")
        responses[item["id"]] = response
        
        if response == "yes":
            total_score += item.get("points", 1)
        elif response == "no":
            finding = {
                "item": item["question"],
                "severity": request.form.get(f"severity_{item['id']}", "medium"),
                "action_required": request.form.get(f"action_{item['id']}", "")
            }
            findings.append(finding)
        
        max_score += item.get("points", 1)
    
    # Update audit
    audit["status"] = "completed"
    audit["completed_date"] = time.time()
    audit["responses"] = responses
    audit["findings"] = findings
    audit["score"] = round((total_score / max_score) * 100) if max_score > 0 else 0
    audit["completion_notes"] = request.form.get("completion_notes", "")
    
    audits[audit_id] = audit
    save_audits(audits)
    
    flash(f"Audit completed with score: {audit['score']}%", "success")
    return redirect(url_for("audits.audit_detail", audit_id=audit_id))

def get_audit_templates():
    """Get available audit templates"""
    return [
        {"id": "safety_walk", "name": "Safety Walk-through", "description": "General safety inspection"},
        {"id": "chemical_audit", "name": "Chemical Management Audit", "description": "Chemical storage and handling"},
        {"id": "equipment_check", "name": "Equipment Safety Check", "description": "Equipment and machinery safety"},
        {"id": "emergency_prep", "name": "Emergency Preparedness", "description": "Emergency procedures and equipment"}
    ]

def get_checklist_for_template(template_id):
    """Get checklist items for a specific template"""
    checklists = {
        "safety_walk": [
            {"id": "sw_1", "question": "Are all walkways clear of obstacles?", "points": 2},
            {"id": "sw_2", "question": "Are emergency exits clearly marked and unobstructed?", "points": 3},
            {"id": "sw_3", "question": "Are all required safety signs posted and visible?", "points": 2},
            {"id": "sw_4", "question": "Is personal protective equipment available and in good condition?", "points": 3}
        ],
        "chemical_audit": [
            {"id": "ca_1", "question": "Are all chemicals properly labeled?", "points": 3},
            {"id": "ca_2", "question": "Are SDS readily accessible for all chemicals?", "points": 3},
            {"id": "ca_3", "question": "Are incompatible chemicals stored separately?", "points": 4},
            {"id": "ca_4", "question": "Are secondary containment systems in place?", "points": 3}
        ],
        "equipment_check": [
            {"id": "ec_1", "question": "Are all guards and safety devices in place?", "points": 4},
            {"id": "ec_2", "question": "Are lockout/tagout procedures followed?", "points": 4},
            {"id": "ec_3", "question": "Is equipment properly maintained per schedule?", "points": 3},
            {"id": "ec_4", "question": "Are operators trained on equipment safety?", "points": 3}
        ],
        "emergency_prep": [
            {"id": "ep_1", "question": "Are fire extinguishers charged and accessible?", "points": 3},
            {"id": "ep_2", "question": "Are emergency contact numbers posted?", "points": 2},
            {"id": "ep_3", "question": "Are evacuation routes clearly marked?", "points": 3},
            {"id": "ep_4", "question": "Is emergency equipment functional?", "points": 4}
        ]
    }
    return checklists.get(template_id, [])

def save_audit(audit_data):
    """Save audit to JSON file"""
    data_dir = Path("data")
    audits_file = data_dir / "audits.json"
    
    if audits_file.exists():
        audits = json.loads(audits_file.read_text())
    else:
        audits = {}
    
    audits[audit_data["id"]] = audit_data
    save_audits(audits)

def save_audits(audits):
    """Save audits dictionary to file"""
    data_dir = Path("data")
    audits_file = data_dir / "audits.json"
    data_dir.mkdir(exist_ok=True)
    audits_file.write_text(json.dumps(audits, indent=2))

def load_audits():
    """Load audits from JSON file"""
    audits_file = Path("data/audits.json")
    if audits_file.exists():
        return json.loads(audits_file.read_text())
    return {}

# Updated app.py with all modules
from flask import Flask, render_template
from routes.sds import sds_bp
from routes.incidents import incidents_bp
from routes.chatbot import chatbot_bp
from routes.capa import capa_bp
from routes.risk import risk_bp
from routes.safety_concerns import safety_concerns_bp
from routes.audits import audits_bp

def create_app():
    ensure_dirs()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
    
    # Register all blueprints
    app.register_blueprint(sds_bp, url_prefix="/

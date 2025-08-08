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
                "action_required": request.form.get(f"action_{item['id']}", ""),
                "photo": request.form.get(f"photo_{item['id']}", "")
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
    
    # Auto-generate CAPAs for high severity findings
    if findings:
        auto_generate_capas_from_audit(audit_id, findings)
    
    flash(f"Audit completed with score: {audit['score']}%. {len(findings)} findings identified.", "info")
    return redirect(url_for("audits.audit_detail", audit_id=audit_id))

def auto_generate_capas_from_audit(audit_id, findings):
    """Auto-generate CAPAs for audit findings"""
    from services.capa_manager import CAPAManager
    capa_manager = CAPAManager()
    
    for finding in findings:
        if finding["severity"] in ["high", "critical"]:
            capa_data = {
                "title": f"Address audit finding: {finding['item'][:50]}...",
                "description": f"Audit Finding: {finding['item']}\nAction Required: {finding['action_required']}",
                "type": "corrective",
                "source": "audit",
                "source_id": audit_id,
                "priority": "high" if finding["severity"] == "critical" else "medium",
                "assignee": "TBD",
                "due_date": (datetime.now() + timedelta(days=30)).isoformat()[:10]
            }
            capa_manager.create_capa(capa_data)

def get_audit_templates():
    """Get available audit templates"""
    return [
        {"id": "safety_walk", "name": "Safety Walk-through", "description": "General safety inspection"},
        {"id": "chemical_audit", "name": "Chemical Management Audit", "description": "Chemical storage and handling"},
        {"id": "equipment_check", "name": "Equipment Safety Check", "description": "Equipment and machinery safety"},
        {"id": "emergency_prep", "name": "Emergency Preparedness", "description": "Emergency procedures and equipment"},
        {"id": "contractor_safety", "name": "Contractor Safety Audit", "description": "Contractor compliance verification"},
        {"id": "environmental", "name": "Environmental Compliance", "description": "Environmental regulations check"}
    ]

def get_checklist_for_template(template_id):
    """Get checklist items for a specific template"""
    checklists = {
        "safety_walk": [
            {"id": "sw_1", "question": "Are all walkways clear of obstacles?", "points": 2, "category": "housekeeping"},
            {"id": "sw_2", "question": "Are emergency exits clearly marked and unobstructed?", "points": 3, "category": "emergency"},
            {"id": "sw_3", "question": "Are all required safety signs posted and visible?", "points": 2, "category": "signage"},
            {"id": "sw_4", "question": "Is personal protective equipment available and in good condition?", "points": 3, "category": "ppe"},
            {"id": "sw_5", "question": "Are spill kits accessible and properly stocked?", "points": 2, "category": "emergency"}
        ],
        "chemical_audit": [
            {"id": "ca_1", "question": "Are all chemicals properly labeled with hazard information?", "points": 3, "category": "labeling"},
            {"id": "ca_2", "question": "Are SDS readily accessible for all chemicals on site?", "points": 3, "category": "documentation"},
            {"id": "ca_3", "question": "Are incompatible chemicals stored separately?", "points": 4, "category": "storage"},
            {"id": "ca_4", "question": "Are secondary containment systems in place and functional?", "points": 3, "category": "containment"},
            {"id": "ca_5", "question": "Is chemical inventory accurate and up to date?", "points": 2, "category": "inventory"}
        ],
        "equipment_check": [
            {"id": "ec_1", "question": "Are all guards and safety devices in place and functional?", "points": 4, "category": "guarding"},
            {"id": "ec_2", "question": "Are lockout/tagout procedures properly implemented?", "points": 4, "category": "loto"},
            {"id": "ec_3", "question": "Is equipment properly maintained per manufacturer schedule?", "points": 3, "category": "maintenance"},
            {"id": "ec_4", "question": "Are operators trained and competent on equipment safety?", "points": 3, "category": "training"},
            {"id": "ec_5", "question": "Are inspection records current and properly documented?", "points": 2, "category": "documentation"}
        ],
        "emergency_prep": [
            {"id": "ep_1", "question": "Are fire extinguishers charged and accessible?", "points": 3, "category": "fire_safety"},
            {"id": "ep_2", "question": "Are emergency contact numbers posted and current?", "points": 2, "category": "communication"},
            {"id": "ep_3", "question": "Are evacuation routes clearly marked and unobstructed?", "points": 3, "category": "evacuation"},
            {"id": "ep_4", "question": "Is emergency equipment functional and inspected?", "points": 4, "category": "equipment"},
            {"id": "ep_5", "question": "Are personnel trained on emergency procedures?", "points": 3, "category": "training"}
        ]
    }
    return checklists.get(template_id, [])

def save_audit(audit_data):
    """Save audit to JSON file"""
    audits = load_audits()
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

# routes/contractors.py - Contractor and Visitor Management
contractors_bp = Blueprint("contractors", __name__)

@contractors_bp.route("/")
def contractors_list():
    contractors = load_contractors()
    contractor_list = sorted(contractors.values(), key=lambda x: x.get("created_date", 0), reverse=True)
    return render_template("contractors_list.html", contractors=contractor_list)

@contractors_bp.route("/register", methods=["GET", "POST"])
def register_contractor():
    if request.method == "GET":
        return render_template("contractor_register.html")
    
    contractor_data = {
        "id": str(int(time.time() * 1000)),
        "company_name": request.form.get("company_name"),
        "contact_person": request.form.get("contact_person"),
        "phone": request.form.get("phone"),
        "email": request.form.get("email"),
        "work_description": request.form.get("work_description"),
        "insurance_expiry": request.form.get("insurance_expiry"),
        "safety_training_completed": False,
        "status": "pending_approval",
        "created_date": time.time(),
        "requirements": {
            "insurance": request.form.get("insurance_file") is not None,
            "safety_training": False,
            "competency_verification": False,
            "site_orientation": False
        }
    }
    
    save_contractor(contractor_data)
    flash("Contractor registration submitted. Safety orientation required before site access.", "info")
    return redirect(url_for("contractors.contractor_detail", contractor_id=contractor_data["id"]))

@contractors_bp.route("/<contractor_id>")
def contractor_detail(contractor_id):
    contractors = load_contractors()
    contractor = contractors.get(contractor_id)
    if not contractor:
        flash("Contractor not found", "error")
        return redirect(url_for("contractors.contractors_list"))
    return render_template("contractor_detail.html", contractor=contractor)

@contractors_bp.route("/<contractor_id>/orientation", methods=["GET", "POST"])
def safety_orientation(contractor_id):
    contractors = load_contractors()
    contractor = contractors.get(contractor_id)
    
    if not contractor:
        flash("Contractor not found", "error")
        return redirect(url_for("contractors.contractors_list"))
    
    if request.method == "GET":
        return render_template("safety_orientation.html", contractor=contractor)
    
    # Process orientation completion
    contractor["requirements"]["site_orientation"] = True
    contractor["requirements"]["safety_training"] = True
    contractor["orientation_completed"] = time.time()
    contractor["orientation_completed_by"] = request.form.get("supervisor", "System")
    
    # Check if all requirements met
    if all(contractor["requirements"].values()):
        contractor["status"] = "approved"
        contractor["approval_date"] = time.time()
    
    contractors[contractor_id] = contractor
    save_contractors(contractors)
    
    flash("Safety orientation completed successfully", "success")
    return redirect(url_for("contractors.contractor_detail", contractor_id=contractor_id))

@contractors_bp.route("/visitors/checkin", methods=["GET", "POST"])
def visitor_checkin():
    if request.method == "GET":
        return render_template("visitor_checkin.html")
    
    visitor_data = {
        "id": str(int(time.time() * 1000)),
        "name": request.form.get("name"),
        "company": request.form.get("company"),
        "purpose": request.form.get("purpose"),
        "host": request.form.get("host"),
        "areas_authorized": request.form.getlist("areas"),
        "safety_briefing_completed": request.form.get("safety_briefing") == "on",
        "checkin_time": time.time(),
        "status": "checked_in"
    }
    
    save_visitor(visitor_data)
    flash(f"Visitor {visitor_data['name']} checked in successfully", "success")
    return render_template("visitor_badge.html", visitor=visitor_data)

def save_contractor(contractor_data):
    contractors = load_contractors()
    contractors[contractor_data["id"]] = contractor_data
    save_contractors(contractors)

def save_contractors(contractors):
    data_dir = Path("data")
    contractors_file = data_dir / "contractors.json"
    data_dir.mkdir(exist_ok=True)
    contractors_file.write_text(json.dumps(contractors, indent=2))

def load_contractors():
    contractors_file = Path("data/contractors.json")
    if contractors_file.exists():
        return json.loads(contractors_file.read_text())
    return {}

def save_visitor(visitor_data):
    data_dir = Path("data")
    visitors_file = data_dir / "visitors.json"
    
    if visitors_file.exists():
        visitors = json.loads(visitors_file.read_text())
    else:
        visitors = {}
    
    visitors[visitor_data["id"]] = visitor_data
    
    data_dir.mkdir(exist_ok=True)
    visitors_file.write_text(json.dumps(visitors, indent=2))

# Enhanced services/capa_manager.py
class CAPAManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.capa_file = self.data_dir / "capa.json"
        
    def load_capas(self) -> Dict:
        if self.capa_file.exists():
            return json.loads(self.capa_file.read_text())
        return {}
    
    def save_capas(self, capas: Dict):
        self.data_dir.mkdir(exist_ok=True)
        self.capa_file.write_text(json.dumps(capas, indent=2))
    
    def create_capa(self, data: Dict) -> str:
        capas = self.load_capas()
        capa_id = str(int(time.time() * 1000))
        
        capa = {
            "id": capa_id,
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "type": data.get("type", "corrective"),  # corrective, preventive
            "source": data.get("source", "manual"),  # manual, incident, audit, risk
            "source_id": data.get("source_id"),
            "assignee": data.get("assignee", ""),
            "due_date": data.get("due_date", ""),
            "priority": data.get("priority", "medium"),  # low, medium, high, critical
            "status": "open",
            "created_date": datetime.now().isoformat(),
            "created_by": data.get("created_by", ""),
            "updates": [],
            "risk_level": data.get("risk_level", "medium"),
            "effectiveness_review_required": True,
            "verification_evidence": []
        }
        
        capas[capa_id] = capa
        self.save_capas(capas)
        return capa_id
    
    def update_capa(self, capa_id: str, update_data: Dict) -> bool:
        capas = self.load_capas()
        if capa_id not in capas:
            return False
            
        capa = capas[capa_id]
        
        # Add update to history
        update = {
            "timestamp": datetime.now().isoformat(),
            "user": update_data.get("updated_by", ""),
            "comment": update_data.get("comment", ""),
            "status_change": update_data.get("status") != capa.get("status"),
            "old_status": capa.get("status"),
            "new_status": update_data.get("status")
        }
        
        capa["updates"].append(update)
        
        # Update fields
        for key, value in update_data.items():
            if key in ["status", "assignee", "due_date", "priority"]:
                capa[key] = value
        
        # Auto-close if completed
        if update_data.get("status") == "completed":
            capa["completion_date"] = datetime.now().isoformat()
            
        capas[capa_id] = capa
        self.save_capas(capas)
        return True
    
    def get_overdue_capas(self) -> List[Dict]:
        capas = self.load_capas()
        overdue = []
        today = datetime.now().date()
        
        for capa in capas.values():
            if capa["status"] in ["open", "in_progress"]:
                try:
                    due_date = datetime.fromisoformat(capa["due_date"]).date()
                    if due_date < today:
                        days_overdue = (today - due_date).days
                        capa["days_overdue"] = days_overdue
                        overdue.append(capa)
                except (ValueError, TypeError):
                    continue
                    
        return sorted(overdue, key=lambda x: x.get("days_overdue", 0), reverse=True)
    
    def get_capas_by_source(self, source_type: str, source_id: str) -> List[Dict]:
        """Get CAPAs linked to a specific source (incident, audit, etc.)"""
        capas = self.load_capas()
        return [capa for capa in capas.values() 
                if capa.get("source") == source_type and capa.get("source_id") == source_id]

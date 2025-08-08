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
    app.register_blueprint(sds_bp, url_prefix="/sds")
    app.register_blueprint(incidents_bp, url_prefix="/incidents")
    app.register_blueprint(chatbot_bp, url_prefix="/")
    app.register_blueprint(capa_bp, url_prefix="/capa")
    app.register_blueprint(risk_bp, url_prefix="/risk")
    app.register_blueprint(safety_concerns_bp, url_prefix="/safety-concerns")
    app.register_blueprint(audits_bp, url_prefix="/audits")

    @app.route("/")
    def index():
        # Enhanced dashboard with AI chatbot integration
        return render_template("enhanced_dashboard.html")

    @app.route("/dashboard")
    def dashboard():
        # Get summary statistics for dashboard
        from services.dashboard_stats import get_dashboard_statistics
        stats = get_dashboard_statistics()
        return render_template("dashboard_with_stats.html", stats=stats)

    return app

# services/dashboard_stats.py - Dashboard Statistics
def get_dashboard_statistics():
    """Get comprehensive dashboard statistics"""
    from pathlib import Path
    import json
    
    stats = {
        "incidents": {"total": 0, "open": 0, "this_month": 0},
        "safety_concerns": {"total": 0, "open": 0, "this_month": 0},
        "capas": {"total": 0, "overdue": 0, "completed": 0},
        "audits": {"scheduled": 0, "completed": 0, "avg_score": 0},
        "sds": {"total": 0, "updated_this_month": 0},
        "risk_assessments": {"high_risk": 0, "total": 0}
    }
    
    # Load incidents
    incidents_file = Path("data/incidents.json")
    if incidents_file.exists():
        incidents = json.loads(incidents_file.read_text())
        stats["incidents"]["total"] = len(incidents)
        stats["incidents"]["open"] = len([i for i in incidents.values() 
                                        if i.get("status") != "complete"])
    
    # Load safety concerns
    concerns_file = Path("data/safety_concerns.json")
    if concerns_file.exists():
        concerns = json.loads(concerns_file.read_text())
        stats["safety_concerns"]["total"] = len(concerns)
        stats["safety_concerns"]["open"] = len([c for c in concerns.values() 
                                              if c.get("status") in ["reported", "in_progress"]])
    
    # Load CAPAs
    capa_file = Path("data/capa.json")
    if capa_file.exists():
        capas = json.loads(capa_file.read_text())
        stats["capas"]["total"] = len(capas)
        stats["capas"]["completed"] = len([c for c in capas.values() 
                                         if c.get("status") == "completed"])
        # Calculate overdue (simplified)
        from datetime import datetime
        today = datetime.now().date()
        overdue = 0
        for capa in capas.values():
            if capa.get("status") in ["open", "in_progress"]:
                try:
                    due_date = datetime.fromisoformat(capa.get("due_date", "")).date()
                    if due_date < today:
                        overdue += 1
                except:
                    pass
        stats["capas"]["overdue"] = overdue
    
    # Load audits
    audits_file = Path("data/audits.json")
    if audits_file.exists():
        audits = json.loads(audits_file.read_text())
        stats["audits"]["scheduled"] = len([a for a in audits.values() 
                                          if a.get("status") == "scheduled"])
        completed_audits = [a for a in audits.values() 
                           if a.get("status") == "completed"]
        stats["audits"]["completed"] = len(completed_audits)
        if completed_audits:
            avg_score = sum(a.get("score", 0) for a in completed_audits) / len(completed_audits)
            stats["audits"]["avg_score"] = round(avg_score, 1)
    
    # Load SDS
    sds_file = Path("data/sds/index.json")
    if sds_file.exists():
        sds_index = json.loads(sds_file.read_text())
        stats["sds"]["total"] = len(sds_index)
    
    # Load risk assessments
    risk_file = Path("data/risk_assessments.json")
    if risk_file.exists():
        risks = json.loads(risk_file.read_text())
        stats["risk_assessments"]["total"] = len(risks)
        stats["risk_assessments"]["high_risk"] = len([r for r in risks.values() 
                                                    if r.get("risk_level") in ["High", "Critical"]])
    
    return stats

# services/notification_manager.py - SLA and Alert Management
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

class NotificationManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.notifications_file = self.data_dir / "notifications.json"
    
    def check_sla_violations(self) -> List[Dict]:
        """Check for SLA violations across all modules"""
        violations = []
        
        # Check CAPA overdue items
        violations.extend(self._check_capa_sla())
        
        # Check safety concern response times
        violations.extend(self._check_safety_concern_sla())
        
        # Check incident investigation deadlines
        violations.extend(self._check_incident_sla())
        
        # Check audit scheduling
        violations.extend(self._check_audit_sla())
        
        return violations
    
    def _check_capa_sla(self) -> List[Dict]:
        """Check CAPA SLA violations"""
        violations = []
        capa_file = self.data_dir / "capa.json"
        
        if not capa_file.exists():
            return violations
            
        capas = json.loads(capa_file.read_text())
        today = datetime.now().date()
        
        for capa in capas.values():
            if capa.get("status") in ["open", "in_progress"]:
                try:
                    due_date = datetime.fromisoformat(capa.get("due_date", "")).date()
                    if due_date < today:
                        days_overdue = (today - due_date).days
                        violations.append({
                            "type": "CAPA Overdue",
                            "id": capa["id"],
                            "title": capa.get("title", ""),
                            "assignee": capa.get("assignee", ""),
                            "days_overdue": days_overdue,
                            "priority": capa.get("priority", "medium"),
                            "url": f"/capa/{capa['id']}"
                        })
                except:
                    pass
        
        return violations
    
    def _check_safety_concern_sla(self) -> List[Dict]:
        """Check safety concern response SLA"""
        violations = []
        concerns_file = self.data_dir / "safety_concerns.json"
        
        if not concerns_file.exists():
            return violations
            
        concerns = json.loads(concerns_file.read_text())
        
        # SLA: 24 hours for initial response, 3 business days for triage
        now = datetime.now()
        
        for concern in concerns.values():
            created_date = datetime.fromtimestamp(concern.get("created_date", 0))
            status = concern.get("status", "")
            
            # Check 24-hour response SLA
            if status == "reported" and (now - created_date).total_seconds() > 24 * 3600:
                violations.append({
                    "type": "Safety Concern - No Response",
                    "id": concern["id"],
                    "title": concern.get("title", ""),
                    "hours_overdue": int((now - created_date).total_seconds() / 3600 - 24),
                    "priority": "high",
                    "url": f"/safety-concerns/{concern['id']}"
                })
        
        return violations
    
    def _check_incident_sla(self) -> List[Dict]:
        """Check incident investigation SLA"""
        violations = []
        incidents_file = self.data_dir / "incidents.json"
        
        if not incidents_file.exists():
            return violations
            
        incidents = json.loads(incidents_file.read_text())
        
        # SLA varies by incident type
        sla_days = {
            "injury": 7,
            "environmental": 5,
            "security": 3,
            "vehicle": 7,
            "other": 10
        }
        
        now = datetime.now()
        
        for incident in incidents.values():
            if incident.get("status") != "complete":
                created_date = datetime.fromtimestamp(incident.get("created_ts", 0))
                incident_type = incident.get("type", "other")
                sla_deadline = created_date + timedelta(days=sla_days.get(incident_type, 10))
                
                if now > sla_deadline:
                    days_overdue = (now - sla_deadline).days
                    violations.append({
                        "type": "Incident Investigation Overdue",
                        "id": incident["id"],
                        "incident_type": incident_type,
                        "days_overdue": days_overdue,
                        "priority": "high",
                        "url": f"/incidents/{incident['id']}/edit"
                    })
        
        return violations
    
    def _check_audit_sla(self) -> List[Dict]:
        """Check audit scheduling SLA"""
        violations = []
        # Implementation would check for overdue scheduled audits
        return violations
    
    def send_notifications(self, violations: List[Dict]):
        """Send notifications for SLA violations"""
        # This would integrate with email/Slack/etc.
        # For now, just log to file
        if violations:
            notification_data = {
                "timestamp": datetime.now().isoformat(),
                "violations": violations
            }
            
            self.data_dir.mkdir(exist_ok=True)
            
            # Load existing notifications
            if self.notifications_file.exists():
                notifications = json.loads(self.notifications_file.read_text())
            else:
                notifications = []
            
            notifications.append(notification_data)
            
            # Keep only last 100 notifications
            notifications = notifications[-100:]
            
            self.notifications_file.write_text(json.dumps(notifications, indent=2))

# Enhanced dashboard template content for templates/enhanced_dashboard.html
ENHANCED_DASHBOARD_TEMPLATE = '''
{% extends "base.html" %}
{% block content %}
<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex justify-content-between align-items-center">
            <h2>Smart EHS Dashboard</h2>
            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#chatModal">
                <i class="bi bi-robot"></i> Ask EHS Assistant
            </button>
        </div>
    </div>
</div>

<!-- Quick Stats Row -->
<div class="row g-3 mb-4">
    <div class="col-md-2">
        <div class="card bg-primary text-white">
            <div class="card-body text-center">
                <h3 class="mb-0">{{ stats.incidents.total|default(0) }}</h3>
                <small>Total Incidents</small>
            </div>
        </div>
    </div>
    <div class="col-md-2">
        <div class="card bg-warning text-white">
            <div class="card-body text-center">
                <h3 class="mb-0">{{ stats.capas.overdue|default(0) }}</h3>
                <small>Overdue CAPAs</small>
            </div>
        </div>
    </div>
    <div class="col-md-2">
        <div class="card bg-success text-white">
            <div class="card-body text-center">
                <h3 class="mb-0">{{ stats.audits.avg_score|default(0) }}%</h3>
                <small>Avg Audit Score</small>
            </div>
        </div>
    </div>
    <div class="col-md-2">
        <div class="card bg-info text-white">
            <div class="card-body text-center">
                <h3 class="mb-0">{{ stats.safety_concerns.total|default(0) }}</h3>
                <small>Safety Concerns</small>
            </div>
        </div>
    </div>
    <div class="col-md-2">
        <div class="card bg-danger text-white">
            <div class="card-body text-center">
                <h3 class="mb-0">{{ stats.risk_assessments.high_risk|default(0) }}</h3>
                <small>High Risk Items</small>
            </div>
        </div>
    </div>
    <div class="col-md-2">
        <div class="card bg-secondary text-white">
            <div class="card-body text-center">
                <h3 class="mb-0">{{ stats.sds.total|default(0) }}</h3>
                <small>SDS Library</small>
            </div>
        </div>
    </div>
</div>

<!-- Main Content Row -->
<div class="row g-3 mb-4">
    <!-- Quick Actions -->
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header">
                <h5><i class="bi bi-lightning"></i> Quick Actions</h5>
            </div>
            <div class="card-body">
                <div class="row g-2">
                    <div class="col-6">
                        <a href="{{ url_for('incidents.new_incident') }}" class="btn btn-outline-danger w-100">
                            <i class="bi bi-exclamation-triangle"></i><br>Report Incident
                        </a>
                    </div>
                    <div class="col-6">
                        <a href="{{ url_for('safety_concerns.new_concern') }}" class="btn btn-outline-warning w-100">
                            <i class="bi bi-shield-exclamation"></i><br>Safety Concern
                        </a>
                    </div>
                    <div class="col-6">
                        <a href="{{ url_for('risk.risk_assessment') }}" class="btn btn-outline-info w-100">
                            <i class="bi bi-graph-up"></i><br>Risk Assessment
                        </a>
                    </div>
                    <div class="col-6">
                        <a href="{{ url_for('audits.new_audit') }}" class="btn btn-outline-primary w-100">
                            <i class="bi bi-clipboard-check"></i><br>Start Audit
                        </a>
                    </div>
                    <div class="col-6">
                        <a href="{{ url_for('sds.sds_list') }}" class="btn btn-outline-success w-100">
                            <i class="bi bi-file-earmark-text"></i><br>SDS Library
                        </a>
                    </div>
                    <div class="col-6">
                        <a href="{{ url_for('capa.new_capa') }}" class="btn btn-outline-secondary w-100">
                            <i class="bi bi-arrow-repeat"></i><br>Create CAPA
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Recent Activity -->
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header">
                <h5><i class="bi bi-clock"></i> Recent Activity</h5>
            </div>
            <div class="card-body">
                <div class="activity-feed">
                    <!-- This would be populated with actual recent activities -->
                    <div class="activity-item mb-2">
                        <small class="text-muted">2 hours ago</small><br>
                        <strong>New incident reported:</strong> Minor injury in Building A
                    </div>
                    <div class="activity-item mb-2">
                        <small class="text-muted">1 day ago</small><br>
                        <strong>CAPA completed:</strong> Emergency exit signage update
                    </div>
                    <div class="activity-item mb-2">
                        <small class="text-muted">2 days ago</small><br>
                        <strong>Audit completed:</strong> Chemical storage audit - 95% score
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- AI Assistant Modal -->
<div class="modal fade" id="chatModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="bi bi-robot"></i> EHS Assistant
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body p-0">
                <iframe src="/chat" style="width: 100%; height: 500px; border: none;"></iframe>
            </div>
        </div>
    </div>
</div>

<style>
.activity-item {
    padding: 0.5rem;
    border-left: 3px solid #e2e8f0;
    margin-left: 0.5rem;
}

.activity-item:hover {
    background-color: #f8fafc;
    border-left-color: #3b82f6;
}

.card {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    transition: box-shadow 0.2s;
}

.card:hover {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.btn-outline-danger:hover, .btn-outline-warning:hover,
.btn-outline-info:hover, .btn-outline-primary:hover,
.btn-outline-success:hover, .btn-outline-secondary:hover {
    transform: translateY(-1px);
}
</style>
{% endblock %}
'''

# Add these missing route handlers to your existing route files

# routes/safety_concerns.py - Add missing templates and handlers
import json
import time
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify

safety_concerns_bp = Blueprint("safety_concerns", __name__)

@safety_concerns_bp.route("/")
def concerns_list():
    """List all safety concerns"""
    concerns = load_safety_concerns()
    # Convert to list and sort by created date
    concern_list = sorted(concerns.values(), key=lambda x: x.get("created_date", 0), reverse=True)
    
    # Calculate stats
    stats = {
        "total": len(concern_list),
        "open": len([c for c in concern_list if c.get("status") in ["reported", "investigating"]]),
        "resolved": len([c for c in concern_list if c.get("status") == "resolved"]),
        "this_month": len([c for c in concern_list if c.get("created_date", 0) > time.time() - (30 * 24 * 3600)])
    }
    
    return render_template("safety_concerns_list.html", concerns=concern_list, stats=stats)

@safety_concerns_bp.route("/new", methods=["GET", "POST"])
def new_concern():
    """Create new safety concern"""
    if request.method == "GET":
        concern_type = request.args.get("type", "concern")
        anonymous = request.args.get("anonymous", "false").lower() == "true"
        return render_template("safety_concern_new.html", 
                             concern_type=concern_type, 
                             anonymous=anonymous)
    
    # Process form submission
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
        "priority": determine_priority(request.form.get("hazard_type", ""), request.form.get("risk_level", "medium")),
        "updates": []
    }
    
    save_safety_concern(concern_data)
    
    if concern_data["anonymous"]:
        flash("Anonymous safety concern submitted successfully. Thank you for speaking up!", "success")
        return redirect(url_for("safety_concerns.concerns_list"))
    else:
        flash("Safety concern submitted successfully. Thank you for speaking up!", "success")
        return redirect(url_for("safety_concerns.concern_detail", concern_id=concern_data["id"]))

@safety_concerns_bp.route("/<concern_id>")
def concern_detail(concern_id):
    """View safety concern details"""
    concerns = load_safety_concerns()
    concern = concerns.get(concern_id)
    if not concern:
        flash("Safety concern not found", "error")
        return redirect(url_for("safety_concerns.concerns_list"))
    
    return render_template("safety_concern_detail.html", concern=concern)

@safety_concerns_bp.route("/<concern_id>/update", methods=["POST"])
def update_concern(concern_id):
    """Update safety concern"""
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

def determine_priority(hazard_type, risk_level):
    """Determine priority based on hazard type and risk level"""
    high_risk_hazards = ["electrical", "chemical", "fall_from_height", "machinery"]
    
    if hazard_type in high_risk_hazards or risk_level == "high":
        return "high"
    elif risk_level == "medium":
        return "medium"
    else:
        return "low"

def save_safety_concern(concern_data):
    """Save safety concern to JSON file"""
    data_dir = Path("data")
    concerns_file = data_dir / "safety_concerns.json"
    
    if concerns_file.exists():
        concerns = json.loads(concerns_file.read_text())
    else:
        concerns = {}
    
    concerns[concern_data["id"]] = concern_data
    save_safety_concerns(concerns)

def save_safety_concerns(concerns):
    """Save safety concerns dictionary to file"""
    data_dir = Path("data")
    concerns_file = data_dir / "safety_concerns.json"
    data_dir.mkdir(exist_ok=True)
    concerns_file.write_text(json.dumps(concerns, indent=2))

def load_safety_concerns():
    """Load safety concerns from JSON file"""
    concerns_file = Path("data/safety_concerns.json")
    if concerns_file.exists():
        try:
            return json.loads(concerns_file.read_text())
        except:
            return {}
    return {}

# routes/risk.py - Enhanced risk management
import json
import time
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from services.risk_matrix import LIKELIHOOD_SCALE, SEVERITY_SCALE, calculate_risk_score, get_risk_level

risk_bp = Blueprint("risk", __name__)

@risk_bp.route("/assess", methods=["GET", "POST"])
def risk_assessment():
    """Conduct risk assessment"""
    if request.method == "GET":
        return render_template("risk_assessment.html", 
                             likelihood_scale=LIKELIHOOD_SCALE,
                             severity_scale=SEVERITY_SCALE)
    
    # Process assessment
    likelihood = int(request.form.get("likelihood", 0))
    severity_scores = {}
    
    for category in SEVERITY_SCALE.keys():
        severity_scores[category] = int(request.form.get(f"severity_{category}", 0))
    
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
    """View risk register"""
    risks = load_risk_assessments()
    risk_list = sorted(risks.values(), key=lambda x: x.get("created_date", 0), reverse=True)
    
    # Calculate statistics
    stats = {
        "total": len(risk_list),
        "critical": len([r for r in risk_list if r.get("risk_level") == "Critical"]),
        "high": len([r for r in risk_list if r.get("risk_level") == "High"]),
        "medium": len([r for r in risk_list if r.get("risk_level") == "Medium"]),
        "low": len([r for r in risk_list if r.get("risk_level") in ["Low", "Very Low"]])
    }
    
    return render_template("risk_register.html", risks=risk_list, stats=stats)

@risk_bp.route("/<risk_id>")
def risk_detail(risk_id):
    """View risk assessment details"""
    risks = load_risk_assessments()
    risk = risks.get(risk_id)
    if not risk:
        flash("Risk assessment not found", "error")
        return redirect(url_for("risk.risk_register"))
    return render_template("risk_detail.html", risk=risk)

def save_risk_assessment(risk_data):
    """Save risk assessment to file"""
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
    """Load risk assessments from file"""
    risk_file = Path("data/risk_assessments.json")
    if risk_file.exists():
        try:
            return json.loads(risk_file.read_text())
        except:
            return {}
    return {}

# routes/audits.py - Enhanced audit management
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify

audits_bp = Blueprint("audits", __name__)

@audits_bp.route("/")
def audits_list():
    """List all audits"""
    audits = load_audits()
    audit_list = sorted(audits.values(), key=lambda x: x.get("created_date", 0), reverse=True)
    
    # Calculate statistics
    stats = {
        "total": len(audit_list),
        "scheduled": len([a for a in audit_list if a.get("status") == "scheduled"]),
        "completed": len([a for a in audit_list if a.get("status") == "completed"]),
        "in_progress": len([a for a in audit_list if a.get("status") == "in_progress"]),
        "avg_score": calculate_average_score(audit_list)
    }
    
    return render_template("audits_list.html", audits=audit_list, stats=stats)

@audits_bp.route("/new", methods=["GET", "POST"])
def new_audit():
    """Create new audit"""
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
    flash(f"Audit {audit_data['id'][:8]} scheduled successfully", "success")
    return redirect(url_for("audits.audit_detail", audit_id=audit_data["id"]))

@audits_bp.route("/<audit_id>")
def audit_detail(audit_id):
    """View audit details"""
    audits = load_audits()
    audit = audits.get(audit_id)
    if not audit:
        flash("Audit not found", "error")
        return redirect(url_for("audits.audits_list"))
    return render_template("audit_detail.html", audit=audit)

@audits_bp.route("/<audit_id>/conduct", methods=["GET", "POST"])
def conduct_audit(audit_id):
    """Conduct audit"""
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
    try:
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
    except ImportError:
        pass  # CAPA manager not available

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
        ]
    }
    return checklists.get(template_id, [])

def calculate_average_score(audits):
    """Calculate average audit score"""
    completed_audits = [a for a in audits if a.get("status") == "completed" and a.get("score")]
    if not completed_audits:
        return 0
    return round(sum(a["score"] for a in completed_audits) / len(completed_audits), 1)

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
        try:
            return json.loads(audits_file.read_text())
        except:
            return {}
    return {}

# routes/contractors.py - Enhanced contractor management
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify

contractors_bp = Blueprint("contractors", __name__)

@contractors_bp.route("/")
def contractors_list():
    """List all contractors"""
    contractors = load_contractors()
    contractor_list = sorted(contractors.values(), key=lambda x: x.get("created_date", 0), reverse=True)
    
    # Calculate statistics
    stats = {
        "total": len(contractor_list),
        "active": len([c for c in contractor_list if c.get("status") == "approved"]),
        "pending": len([c for c in contractor_list if c.get("status") == "pending_approval"]),
        "training_required": len([c for c in contractor_list if not c.get("safety_training_completed")])
    }
    
    return render_template("contractors_list.html", contractors=contractor_list, stats=stats)

@contractors_bp.route("/register", methods=["GET", "POST"])
def register_contractor():
    """Register new contractor"""
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
            "insurance": request.files.get("insurance_file") is not None,
            "safety_training": False,
            "competency_verification": False,
            "site_orientation": False
        },
        "work_locations": request.form.getlist("work_locations"),
        "hazard_exposure": request.form.getlist("hazard_exposure")
    }
    
    save_contractor(contractor_data)
    flash("Contractor registration submitted. Safety orientation required before site access.", "info")
    return redirect(url_for("contractors.contractor_detail", contractor_id=contractor_data["id"]))

@contractors_bp.route("/<contractor_id>")
def contractor_detail(contractor_id):
    """View contractor details"""
    contractors = load_contractors()
    contractor = contractors.get(contractor_id)
    if not contractor:
        flash("Contractor not found", "error")
        return redirect(url_for("contractors.contractors_list"))
    return render_template("contractor_detail.html", contractor=contractor)

@contractors_bp.route("/visitors/checkin", methods=["GET", "POST"])
def visitor_checkin():
    """Visitor check-in system"""
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
        "status": "checked_in",
        "expected_duration": request.form.get("duration"),
        "emergency_contact": request.form.get("emergency_contact"),
        "has_ppe": request.form.get("has_ppe") == "on"
    }
    
    save_visitor(visitor_data)
    flash(f"Visitor {visitor_data['name']} checked in successfully", "success")
    return render_template("visitor_badge.html", visitor=visitor_data)

def save_contractor(contractor_data):
    """Save contractor data"""
    contractors = load_contractors()
    contractors[contractor_data["id"]] = contractor_data
    save_contractors(contractors)

def save_contractors(contractors):
    """Save contractors dictionary to file"""
    data_dir = Path("data")
    contractors_file = data_dir / "contractors.json"
    data_dir.mkdir(exist_ok=True)
    contractors_file.write_text(json.dumps(contractors, indent=2))

def load_contractors():
    """Load contractors from JSON file"""
    contractors_file = Path("data/contractors.json")
    if contractors_file.exists():
        try:
            return json.loads(contractors_file.read_text())
        except:
            return {}
    return {}

def save_visitor(visitor_data):
    """Save visitor data"""
    data_dir = Path("data")
    visitors_file = data_dir / "visitors.json"
    
    if visitors_file.exists():
        visitors = json.loads(visitors_file.read_text())
    else:
        visitors = {}
    
    visitors[visitor_data["id"]] = visitor_data
    
    data_dir.mkdir(exist_ok=True)
    visitors_file.write_text(json.dumps(visitors, indent=2))

def load_visitors():
    """Load visitors from JSON file"""
    visitors_file = Path("data/visitors.json")
    if visitors_file.exists():
        try:
            return json.loads(visitors_file.read_text())
        except:
            return {}
    return {}

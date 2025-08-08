# services/capa_manager.py - Complete CAPA Management Service
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

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
            "verification_evidence": [],
            "root_cause": data.get("root_cause", ""),
            "implementation_plan": data.get("implementation_plan", "")
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
            "new_status": update_data.get("status"),
            "fields_changed": []
        }
        
        # Track field changes
        for key, value in update_data.items():
            if key in ["status", "assignee", "due_date", "priority"] and capa.get(key) != value:
                update["fields_changed"].append({
                    "field": key,
                    "old_value": capa.get(key),
                    "new_value": value
                })
                capa[key] = value
        
        capa["updates"].append(update)
        
        # Auto-close if completed
        if update_data.get("status") == "completed":
            capa["completion_date"] = datetime.now().isoformat()
            capa["completed_by"] = update_data.get("updated_by", "")
            
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
    
    def get_capa_statistics(self) -> Dict:
        """Get CAPA statistics for dashboard"""
        capas = self.load_capas()
        stats = {
            "total": len(capas),
            "open": 0,
            "in_progress": 0,
            "completed": 0,
            "overdue": 0,
            "by_priority": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            "by_type": {"corrective": 0, "preventive": 0},
            "by_source": {}
        }
        
        today = datetime.now().date()
        for capa in capas.values():
            status = capa.get("status", "open")
            priority = capa.get("priority", "medium")
            capa_type = capa.get("type", "corrective")
            source = capa.get("source", "manual")
            
            # Count by status
            stats[status] = stats.get(status, 0) + 1
            
            # Count by priority
            stats["by_priority"][priority] += 1
            
            # Count by type
            stats["by_type"][capa_type] += 1
            
            # Count by source
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            
            # Count overdue
            if status in ["open", "in_progress"]:
                try:
                    due_date = datetime.fromisoformat(capa.get("due_date", "")).date()
                    if due_date < today:
                        stats["overdue"] += 1
                except (ValueError, TypeError):
                    pass
        
        return stats

# Complete routes/capa.py
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from services.capa_manager import CAPAManager

capa_bp = Blueprint("capa", __name__)
capa_manager = CAPAManager()

@capa_bp.route("/")
def capa_list():
    capas = capa_manager.load_capas()
    capa_list = sorted(capas.values(), key=lambda x: x.get("created_date", ""), reverse=True)
    return render_template("capa_list.html", capas=capa_list)

@capa_bp.route("/new", methods=["GET", "POST"])
def new_capa():
    if request.method == "GET":
        # Check if linked to another entity
        source = request.args.get("source")
        source_id = request.args.get("source_id")
        return render_template("capa_new.html", source=source, source_id=source_id)
    
    capa_data = {
        "title": request.form.get("title"),
        "description": request.form.get("description"),
        "type": request.form.get("type"),
        "assignee": request.form.get("assignee"),
        "due_date": request.form.get("due_date"),
        "priority": request.form.get("priority"),
        "created_by": request.form.get("created_by", "Current User"),
        "source": request.form.get("source", "manual"),
        "source_id": request.form.get("source_id"),
        "root_cause": request.form.get("root_cause", ""),
        "implementation_plan": request.form.get("implementation_plan", "")
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
        "updated_by": request.form.get("updated_by", "Current User"),
        "assignee": request.form.get("assignee"),
        "due_date": request.form.get("due_date"),
        "priority": request.form.get("priority")
    }
    
    if capa_manager.update_capa(capa_id, update_data):
        flash("CAPA updated successfully", "success")
    else:
        flash("Failed to update CAPA", "error")
    
    return redirect(url_for("capa.capa_detail", capa_id=capa_id))

@capa_bp.route("/dashboard")
def capa_dashboard():
    stats = capa_manager.get_capa_statistics()
    overdue = capa_manager.get_overdue_capas()
    
    return render_template("capa_dashboard.html", stats=stats, overdue=overdue)

@capa_bp.route("/assigned")
def assigned_capas():
    """View CAPAs assigned to current user"""
    # In a real system, you'd filter by actual user
    current_user = request.args.get("user", "Current User")
    capas = capa_manager.load_capas()
    
    assigned = [capa for capa in capas.values() 
                if capa.get("assignee") == current_user and capa.get("status") != "completed"]
    
    return render_template("capa_assigned.html", capas=assigned, user=current_user)

@capa_bp.route("/api/stats")
def api_capa_stats():
    """API endpoint for CAPA statistics"""
    try:
        stats = capa_manager.get_capa_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Complete routes/contractors.py
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify

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
        },
        "work_locations": request.form.getlist("work_locations"),
        "hazard_exposure": request.form.getlist("hazard_exposure")
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
    contractor["orientation_score"] = request.form.get("score", 100)
    contractor["orientation_notes"] = request.form.get("notes", "")
    
    # Check if all requirements met
    if all(contractor["requirements"].values()):
        contractor["status"] = "approved"
        contractor["approval_date"] = time.time()
        contractor["badge_issued"] = True
        contractor["access_expires"] = (datetime.now() + timedelta(days=365)).timestamp()
    
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
        "status": "checked_in",
        "expected_duration": request.form.get("duration"),
        "emergency_contact": request.form.get("emergency_contact"),
        "has_ppe": request.form.get("has_ppe") == "on"
    }
    
    save_visitor(visitor_data)
    flash(f"Visitor {visitor_data['name']} checked in successfully", "success")
    return render_template("visitor_badge.html", visitor=visitor_data)

@contractors_bp.route("/visitors/<visitor_id>/checkout", methods=["POST"])
def visitor_checkout(visitor_id):
    visitors = load_visitors()
    visitor = visitors.get(visitor_id)
    
    if visitor:
        visitor["checkout_time"] = time.time()
        visitor["status"] = "checked_out"
        save_visitors(visitors)
        flash(f"Visitor {visitor['name']} checked out successfully", "success")
    
    return redirect(url_for("contractors.visitors_list"))

@contractors_bp.route("/visitors")
def visitors_list():
    visitors = load_visitors()
    # Filter to show only today's visitors
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    
    todays_visitors = [v for v in visitors.values() 
                      if v.get("checkin_time", 0) >= today_start]
    
    return render_template("visitors_list.html", visitors=todays_visitors)

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
    visitors = load_visitors()
    visitors[visitor_data["id"]] = visitor_data
    save_visitors(visitors)

def save_visitors(visitors):
    data_dir = Path("data")
    visitors_file = data_dir / "visitors.json"
    data_dir.mkdir(exist_ok=True)
    visitors_file.write_text(json.dumps(visitors, indent=2))

def load_visitors():
    visitors_file = Path("data/visitors.json")
    if visitors_file.exists():
        return json.loads(visitors_file.read_text())
    return {}

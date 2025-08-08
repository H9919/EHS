# services/dashboard_stats.py - Enhanced Dashboard Statistics
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

def get_dashboard_statistics() -> Dict:
    """Get comprehensive dashboard statistics"""
    stats = {
        "incidents": {"total": 0, "open": 0, "this_month": 0, "by_type": {}},
        "safety_concerns": {"total": 0, "open": 0, "this_month": 0, "by_type": {}},
        "capas": {"total": 0, "overdue": 0, "completed": 0, "by_priority": {}},
        "audits": {"scheduled": 0, "completed": 0, "avg_score": 0, "this_month": 0},
        "sds": {"total": 0, "updated_this_month": 0},
        "risk_assessments": {"high_risk": 0, "total": 0, "by_level": {}},
        "contractors": {"active": 0, "pending_orientation": 0},
        "trends": {
            "incidents_6_months": [],
            "risk_distribution": {},
            "top_hazard_types": []
        }
    }
    
    # Calculate date ranges
    now = datetime.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    six_months_ago = now - timedelta(days=180)
    
    # Load and analyze incidents
    incidents_file = Path("data/incidents.json")
    if incidents_file.exists():
        incidents = json.loads(incidents_file.read_text())
        stats["incidents"]["total"] = len(incidents)
        
        for incident in incidents.values():
            created_date = datetime.fromtimestamp(incident.get("created_ts", 0))
            incident_type = incident.get("type", "other")
            
            # Count open incidents
            if incident.get("status") != "complete":
                stats["incidents"]["open"] += 1
            
            # Count this month incidents
            if created_date >= this_month_start:
                stats["incidents"]["this_month"] += 1
            
            # Count by type
            stats["incidents"]["by_type"][incident_type] = stats["incidents"]["by_type"].get(incident_type, 0) + 1
    
    # Load and analyze safety concerns
    concerns_file = Path("data/safety_concerns.json")
    if concerns_file.exists():
        concerns = json.loads(concerns_file.read_text())
        stats["safety_concerns"]["total"] = len(concerns)
        
        for concern in concerns.values():
            created_date = datetime.fromtimestamp(concern.get("created_date", 0))
            concern_type = concern.get("type", "concern")
            
            # Count open concerns
            if concern.get("status") in ["reported", "in_progress"]:
                stats["safety_concerns"]["open"] += 1
            
            # Count this month concerns
            if created_date >= this_month_start:
                stats["safety_concerns"]["this_month"] += 1
            
            # Count by type
            stats["safety_concerns"]["by_type"][concern_type] = stats["safety_concerns"]["by_type"].get(concern_type, 0) + 1
    
    # Load and analyze CAPAs
    capa_file = Path("data/capa.json")
    if capa_file.exists():
        capas = json.loads(capa_file.read_text())
        stats["capas"]["total"] = len(capas)
        
        today = datetime.now().date()
        for capa in capas.values():
            priority = capa.get("priority", "medium")
            stats["capas"]["by_priority"][priority] = stats["capas"]["by_priority"].get(priority, 0) + 1
            
            if capa.get("status") == "completed":
                stats["capas"]["completed"] += 1
            elif capa.get("status") in ["open", "in_progress"]:
                try:
                    due_date = datetime.fromisoformat(capa.get("due_date", "")).date()
                    if due_date < today:
                        stats["capas"]["overdue"] += 1
                except (ValueError, TypeError):
                    pass
    
    # Load and analyze audits
    audits_file = Path("data/audits.json")
    if audits_file.exists():
        audits = json.loads(audits_file.read_text())
        
        completed_audits = []
        for audit in audits.values():
            if audit.get("status") == "scheduled":
                stats["audits"]["scheduled"] += 1
            elif audit.get("status") == "completed":
                completed_audits.append(audit)
                completed_date = datetime.fromtimestamp(audit.get("completed_date", 0))
                if completed_date >= this_month_start:
                    stats["audits"]["this_month"] += 1
        
        stats["audits"]["completed"] = len(completed_audits)
        if completed_audits:
            avg_score = sum(audit.get("score", 0) for audit in completed_audits) / len(completed_audits)
            stats["audits"]["avg_score"] = round(avg_score, 1)
    
    # Load SDS statistics
    sds_file = Path("data/sds/index.json")
    if sds_file.exists():
        sds_index = json.loads(sds_file.read_text())
        stats["sds"]["total"] = len(sds_index)
        
        # Count recently updated SDS
        for sds in sds_index.values():
            created_date = datetime.fromtimestamp(sds.get("created_ts", 0))
            if created_date >= this_month_start:
                stats["sds"]["updated_this_month"] += 1
    
    # Load and analyze risk assessments
    risk_file = Path("data/risk_assessments.json")
    if risk_file.exists():
        risks = json.loads(risk_file.read_text())
        stats["risk_assessments"]["total"] = len(risks)
        
        for risk in risks.values():
            risk_level = risk.get("risk_level", "Low")
            stats["risk_assessments"]["by_level"][risk_level] = stats["risk_assessments"]["by_level"].get(risk_level, 0) + 1
            
            if risk_level in ["High", "Critical"]:
                stats["risk_assessments"]["high_risk"] += 1
    
    # Load contractor statistics
    contractors_file = Path("data/contractors.json")
    if contractors_file.exists():
        contractors = json.loads(contractors_file.read_text())
        
        for contractor in contractors.values():
            if contractor.get("status") == "approved":
                stats["contractors"]["active"] += 1
            elif contractor.get("status") == "pending_approval":
                stats["contractors"]["pending_orientation"] += 1
    
    # Generate trend data for charts
    stats["trends"] = generate_trend_data(six_months_ago, now)
    
    return stats

def generate_trend_data(start_date: datetime, end_date: datetime) -> Dict:
    """Generate trend data for dashboard charts"""
    trends = {
        "incidents_6_months": [],
        "risk_distribution": {"Low": 0, "Medium": 0, "High": 0, "Critical": 0},
        "top_hazard_types": []
    }
    
    # Generate monthly incident data for the last 6 months
    current_

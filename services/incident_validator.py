# services/incident_validator.py - Enhanced with scoring, 5 Whys, and CAPA generation
import json
import time
from typing import Dict, Tuple, List, Optional
from pathlib import Path
from datetime import datetime

# Enhanced required category coverage by incident type
REQUIRED_BY_TYPE = {
    "injury": ["people", "legal"],
    "vehicle": ["people", "cost", "legal", "reputation"],
    "security": ["legal", "reputation", "cost"],
    "environmental": ["environment", "legal", "reputation"],
    "depot": ["people", "cost", "legal", "reputation"],
    "near_miss": ["people", "environment"],
    "property": ["cost", "legal"],
    "emergency": ["people", "environment", "cost", "legal", "reputation"],
    "other": ["people", "environment", "cost", "legal", "reputation"],
}

ALL_CATEGORIES = ["people", "environment", "cost", "legal", "reputation"]

# Scoring lookup tables for severity and likelihood
SEVERITY_LOOKUP = {
    "people": {
        "first_aid": 2,
        "medical_treatment": 4,
        "lost_time": 6,
        "hospitalization": 8,
        "fatality": 10,
        "multiple_fatalities": 10
    },
    "environment": {
        "no_release": 0,
        "minor_contained": 2,
        "moderate_reportable": 4,
        "major_offsite": 6,
        "significant_impact": 8,
        "catastrophic": 10
    },
    "cost": {
        "under_1k": 2,
        "1k_to_10k": 4,
        "10k_to_100k": 6,
        "100k_to_1m": 8,
        "over_1m": 10
    },
    "legal": {
        "compliant": 0,
        "minor_deviation": 2,
        "citation_risk": 4,
        "violation_issued": 6,
        "enforcement_action": 8,
        "criminal_charges": 10
    },
    "reputation": {
        "internal_only": 0,
        "client_awareness": 2,
        "partner_concern": 4,
        "media_attention": 6,
        "public_crisis": 8,
        "brand_damage": 10
    }
}

LIKELIHOOD_LOOKUP = {
    0: "impossible",
    2: "rare", 
    4: "unlikely",
    6: "possible",
    8: "likely",
    10: "almost_certain"
}

class IncidentScoring:
    """Enhanced incident scoring using ERC matrix and heuristics"""
    
    def __init__(self):
        self.severity_keywords = {
            "people": {
                "fatality": ["death", "died", "fatal", "killed", "fatality"],
                "hospitalization": ["hospital", "admitted", "surgery", "severe", "serious"],
                "lost_time": ["lost time", "days off", "restricted duty", "modified work"],
                "medical_treatment": ["medical", "doctor", "clinic", "treatment", "stitches"],
                "first_aid": ["first aid", "band-aid", "minor", "superficial"]
            },
            "environment": {
                "catastrophic": ["major spill", "widespread", "contamination", "ecosystem"],
                "significant_impact": ["offsite", "groundwater", "soil contamination"],
                "major_offsite": ["reported to EPA", "regulatory", "TCEQ"],
                "moderate_reportable": ["reportable", "notification required"],
                "minor_contained": ["contained", "cleaned up", "minor release"]
            },
            "cost": {
                "over_1m": ["million", "extensive damage", "total loss"],
                "100k_to_1m": ["hundred thousand", "major repair", "replacement"],
                "10k_to_100k": ["significant", "repair", "downtime"],
                "1k_to_10k": ["minor repair", "small damage"],
                "under_1k": ["minimal", "cosmetic", "negligible"]
            }
        }
        
        self.likelihood_keywords = {
            "almost_certain": ["frequent", "common", "regular", "expected"],
            "likely": ["probable", "often", "recurring"],
            "possible": ["occasional", "sometimes", "periodic"],
            "unlikely": ["rare", "infrequent", "isolated"],
            "rare": ["very rare", "unusual", "exceptional"]
        }
    
    def compute_severity_likelihood(self, incident_data: Dict) -> Dict:
        """Compute severity and likelihood scores using semantic analysis"""
        
        # Extract text for analysis
        answers = incident_data.get("answers", {})
        incident_type = incident_data.get("type", "other")
        
        combined_text = " ".join([
            answers.get("people", ""),
            answers.get("environment", ""),
            answers.get("cost", ""), 
            answers.get("legal", ""),
            answers.get("reputation", "")
        ]).lower()
        
        # Calculate severity scores for each category
        severity_scores = {}
        for category in ALL_CATEGORIES:
            category_text = answers.get(category, "").lower()
            severity_scores[category] = self._analyze_severity(category, category_text, combined_text)
        
        # Calculate likelihood score
        likelihood_score = self._analyze_likelihood(combined_text, incident_type)
        
        # Calculate overall risk score (likelihood * max severity)
        max_severity = max(severity_scores.values()) if severity_scores else 0
        risk_score = likelihood_score * max_severity
        
        # Determine risk level
        risk_level = self._get_risk_level(risk_score)
        
        return {
            "severity_scores": severity_scores,
            "likelihood_score": likelihood_score,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "rationale": self._generate_rationale(severity_scores, likelihood_score, incident_type)
        }
    
    def _analyze_severity(self, category: str, category_text: str, full_text: str) -> int:
        """Analyze severity for a specific category"""
        if not category_text.strip():
            return 0
        
        keywords = self.severity_keywords.get(category, {})
        
        # Check for specific severity indicators
        for severity_level, terms in keywords.items():
            for term in terms:
                if term in category_text or term in full_text:
                    return SEVERITY_LOOKUP[category].get(severity_level, 2)
        
        # Default scoring based on text length and content
        if len(category_text) > 100:
            return 4  # Detailed description suggests moderate severity
        elif len(category_text) > 20:
            return 2  # Some description suggests minor severity
        else:
            return 1  # Minimal description
    
    def _analyze_likelihood(self, text: str, incident_type: str) -> int:
        """Analyze likelihood of recurrence"""
        
        # Check for likelihood keywords
        for likelihood_level, terms in self.likelihood_keywords.items():
            for term in terms:
                if term in text:
                    # Convert likelihood level to score
                    for score, level in LIKELIHOOD_LOOKUP.items():
                        if level == likelihood_level:
                            return score
        
        # Default likelihood based on incident type
        type_defaults = {
            "injury": 6,        # Possible
            "near_miss": 8,     # Likely (indicates system weakness)
            "environmental": 4, # Unlikely (usually isolated)
            "vehicle": 6,       # Possible
            "property": 4,      # Unlikely
            "security": 2       # Rare
        }
        
        return type_defaults.get(incident_type, 4)  # Default to "unlikely"
    
    def _get_risk_level(self, risk_score: int) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 80:
            return "Critical"
        elif risk_score >= 60:
            return "High"
        elif risk_score >= 40:
            return "Medium"
        elif risk_score >= 20:
            return "Low"
        else:
            return "Very Low"
    
    def _generate_rationale(self, severity_scores: Dict, likelihood_score: int, incident_type: str) -> str:
        """Generate human-readable rationale for the scoring"""
        max_category = max(severity_scores, key=severity_scores.get) if severity_scores else "none"
        max_severity = severity_scores.get(max_category, 0)
        
        likelihood_level = LIKELIHOOD_LOOKUP.get(likelihood_score, "unknown")
        
        rationale = f"Primary impact category: {max_category} (severity: {max_severity}/10). "
        rationale += f"Likelihood of recurrence: {likelihood_level} ({likelihood_score}/10). "
        rationale += f"Incident type: {incident_type}."
        
        return rationale

class RootCauseAnalysis:
    """5 Whys implementation for root cause analysis"""
    
    def __init__(self):
        self.guided_prompts = {
            1: "What happened? (Immediate cause)",
            2: "Why did this immediate cause occur?",
            3: "Why did that underlying condition exist?",
            4: "Why wasn't this prevented by existing controls?",
            5: "Why do our systems allow this root cause to persist?"
        }
    
    def generate_5_whys_prompts(self, incident_description: str) -> List[Dict]:
        """Generate guided prompts for 5 Whys analysis"""
        prompts = []
        
        for level, question in self.guided_prompts.items():
            prompts.append({
                "level": level,
                "question": question,
                "guidance": self._get_guidance_for_level(level),
                "examples": self._get_examples_for_level(level)
            })
        
        return prompts
    
    def _get_guidance_for_level(self, level: int) -> str:
        """Get guidance text for each Why level"""
        guidance = {
            1: "Describe the direct, immediate cause of the incident.",
            2: "Look for the conditions or actions that led to the immediate cause.",
            3: "Identify system, process, or organizational factors.",
            4: "Examine why existing safety controls didn't prevent this.",
            5: "Find the fundamental organizational or cultural root cause."
        }
        return guidance.get(level, "")
    
    def _get_examples_for_level(self, level: int) -> List[str]:
        """Get example answers for each Why level"""
        examples = {
            1: ["Employee slipped and fell", "Chemical spilled", "Equipment malfunctioned"],
            2: ["Floor was wet", "Container leaked", "Maintenance was overdue"],
            3: ["No wet floor signs", "Inspection missed defect", "Work order delayed"],
            4: ["Procedure not followed", "Warning system failed", "Training insufficient"],
            5: ["Safety culture weak", "Resource constraints", "Communication breakdown"]
        }
        return examples.get(level, [])

class CAPAGenerator:
    """CAPA suggestion generator using SBERT similarity"""
    
    def __init__(self):
        self.capa_templates = {
            "training": [
                "Provide additional safety training on {topic}",
                "Conduct refresher training for {department}",
                "Develop job-specific safety training for {role}",
                "Implement competency verification for {skill}"
            ],
            "procedure": [
                "Update procedure to include {requirement}",
                "Create new work instruction for {task}",
                "Revise safety protocol for {process}",
                "Establish clear guidelines for {situation}"
            ],
            "engineering": [
                "Install additional safety equipment: {equipment}",
                "Modify equipment to prevent {hazard}",
                "Implement engineering controls for {risk}",
                "Upgrade safety systems in {area}"
            ],
            "inspection": [
                "Increase inspection frequency for {equipment}",
                "Add safety checkpoints to {process}",
                "Implement condition monitoring for {system}",
                "Create inspection checklist for {area}"
            ],
            "communication": [
                "Improve communication of {information}",
                "Establish notification system for {event}",
                "Create awareness campaign about {topic}",
                "Implement toolbox talks on {subject}"
            ]
        }
        
        # SBERT similarity (if available)
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.sbert_available = True
        except ImportError:
            self.sbert_available = False
    
    def suggest_capas(self, incident_data: Dict, root_causes: List[str]) -> List[Dict]:
        """Generate CAPA suggestions based on incident and root causes"""
        suggestions = []
        
        incident_type = incident_data.get("type", "other")
        description = incident_data.get("answers", {}).get("people", "") + " " + \
                     incident_data.get("answers", {}).get("environment", "")
        
        # Rule-based suggestions
        rule_suggestions = self._generate_rule_based_capas(incident_type, description, root_causes)
        suggestions.extend(rule_suggestions)
        
        # SBERT-based suggestions (if available)
        if self.sbert_available:
            sbert_suggestions = self._generate_sbert_capas(description, root_causes)
            suggestions.extend(sbert_suggestions)
        
        # Remove duplicates and rank by relevance
        unique_suggestions = self._deduplicate_and_rank(suggestions)
        
        return unique_suggestions[:5]  # Return top 5 suggestions
    
    def _generate_rule_based_capas(self, incident_type: str, description: str, root_causes: List[str]) -> List[Dict]:
        """Generate CAPAs using rule-based logic"""
        suggestions = []
        description_lower = description.lower()
        
        # Incident type specific suggestions
        type_suggestions = {
            "injury": [
                {"type": "training", "action": "Provide additional safety training on injury prevention", "priority": "high"},
                {"type": "engineering", "action": "Install additional safety equipment", "priority": "medium"}
            ],
            "environmental": [
                {"type": "procedure", "action": "Update spill response procedures", "priority": "high"},
                {"type": "engineering", "action": "Install secondary containment", "priority": "high"}
            ],
            "near_miss": [
                {"type": "inspection", "action": "Increase safety inspections", "priority": "medium"},
                {"type": "communication", "action": "Improve hazard communication", "priority": "medium"}
            ]
        }
        
        suggestions.extend(type_suggestions.get(incident_type, []))
        
        # Keyword-based suggestions
        if "training" in description_lower or "procedure" in description_lower:
            suggestions.append({
                "type": "training",
                "action": "Conduct additional safety training",
                "priority": "high"
            })
        
        if "equipment" in description_lower or "maintenance" in description_lower:
            suggestions.append({
                "type": "inspection",
                "action": "Implement preventive maintenance program",
                "priority": "medium"
            })
        
        return suggestions
    
    def _generate_sbert_capas(self, description: str, root_causes: List[str]) -> List[Dict]:
        """Generate CAPAs using SBERT similarity (placeholder)"""
        # This would implement semantic similarity against a database of previous CAPAs
        # For now, return empty list
        return []
    
    def _deduplicate_and_rank(self, suggestions: List[Dict]) -> List[Dict]:
        """Remove duplicates and rank suggestions"""
        unique_suggestions = []
        seen_actions = set()
        
        # Priority order
        priority_order = {"high": 3, "medium": 2, "low": 1}
        
        for suggestion in sorted(suggestions, key=lambda x: priority_order.get(x.get("priority", "low"), 1), reverse=True):
            action = suggestion.get("action", "")
            if action not in seen_actions:
                seen_actions.add(action)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions

# Enhanced validation functions
def compute_completeness(rec: Dict) -> int:
    """Compute completeness percentage with enhanced criteria"""
    answers = rec.get("answers", {})
    
    # Basic field completion (40% weight)
    filled_categories = sum(1 for c in ALL_CATEGORIES if (answers.get(c) or "").strip())
    basic_score = (filled_categories / len(ALL_CATEGORIES)) * 40
    
    # Required category completion (30% weight)
    incident_type = (rec.get("type") or "other").lower().replace(" ", "_")
    required = REQUIRED_BY_TYPE.get(incident_type, ALL_CATEGORIES)
    required_filled = sum(1 for c in required if (answers.get(c) or "").strip())
    required_score = (required_filled / len(required)) * 30 if required else 0
    
    # Additional metadata completion (30% weight)
    metadata_fields = ["location", "timestamp", "reporter", "witness_info", "photos"]
    metadata_filled = sum(1 for field in metadata_fields if rec.get(field))
    metadata_score = (metadata_filled / len(metadata_fields)) * 30
    
    return int(basic_score + required_score + metadata_score)

def validate_record(rec: Dict) -> Tuple[bool, List[str]]:
    """Enhanced validation with detailed feedback"""
    incident_type = (rec.get("type") or "other").lower().replace(" ", "_")
    required = REQUIRED_BY_TYPE.get(incident_type, REQUIRED_BY_TYPE["other"])
    answers = rec.get("answers", {})
    
    missing = []
    warnings = []
    
    # Check required categories
    for category in required:
        content = (answers.get(category) or "").strip()
        if not content:
            missing.append(category)
        elif len(content) < 10:
            warnings.append(f"{category} (needs more detail)")
    
    # Check for critical missing information
    if incident_type == "injury" and not rec.get("severity"):
        missing.append("injury severity")
    
    if incident_type == "environmental" and not rec.get("chemical_info"):
        missing.append("chemical information")
    
    is_valid = len(missing) == 0
    return is_valid, missing, warnings

def generate_scoring_and_capas(incident_data: Dict) -> Dict:
    """Generate comprehensive scoring and CAPA suggestions"""
    
    # Initialize components
    scorer = IncidentScoring()
    rca = RootCauseAnalysis()
    capa_gen = CAPAGenerator()
    
    # Compute risk scoring
    scoring_result = scorer.compute_severity_likelihood(incident_data)
    
    # Generate 5 Whys prompts
    description = incident_data.get("answers", {}).get("people", "") or \
                 incident_data.get("answers", {}).get("environment", "") or \
                 "Incident occurred"
    
    whys_prompts = rca.generate_5_whys_prompts(description)
    
    # Generate CAPA suggestions (using dummy root causes for now)
    root_causes = ["Procedure not followed", "Training insufficient", "Equipment malfunction"]
    capa_suggestions = capa_gen.suggest_capas(incident_data, root_causes)
    
    return {
        "scoring": scoring_result,
        "five_whys_prompts": whys_prompts,
        "capa_suggestions": capa_suggestions,
        "completeness": compute_completeness(incident_data),
        "validation": validate_record(incident_data)
    }

# services/ehs_chatbot.py - Enhanced with slot filling and intent classification
import json
import re
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False

class IntentClassifier:
    """Hybrid rules + SBERT classifier for intent detection"""
    
    def __init__(self):
        self.rule_patterns = {
            'incident_reporting': [
                r'report.*incident', r'incident.*report', r'workplace.*incident',
                r'accident', r'injury', r'hurt', r'injured', r'damaged', r'spill', 
                r'collision', r'crash', r'fall', r'slip', r'trip', r'cut', r'burn',
                r'emergency.*happened', r'something.*happened', r'need.*report.*incident',
                r'someone.*hurt', r'property.*damage', r'environmental.*spill'
            ],
            'safety_concern': [
                r'safety.*concern', r'unsafe.*condition', r'hazard', r'dangerous',
                r'near.*miss', r'almost.*accident', r'safety.*issue', r'concern.*about',
                r'worried.*about', r'observed.*unsafe', r'potential.*danger',
                r'safety.*observation', r'unsafe.*behavior', r'safety.*violation'
            ],
            'sds_lookup': [
                r'sds', r'safety.*data.*sheet', r'chemical.*info', r'material.*safety',
                r'find.*chemical', r'lookup.*chemical', r'chemical.*safety',
                r'msds', r'chemical.*properties', r'hazard.*information'
            ],
            'risk_assessment': [
                r'risk.*assessment', r'evaluate.*risk', r'risk.*analysis',
                r'how.*risky', r'what.*risk', r'assess.*risk', r'risk.*level',
                r'likelihood', r'severity', r'risk.*matrix'
            ],
            'capa_management': [
                r'corrective.*action', r'preventive.*action', r'capa',
                r'fix.*problem', r'prevent.*future', r'action.*plan', r'follow.*up',
                r'root.*cause', r'why.*happen', r'improvement'
            ]
        }
        
        if SBERT_AVAILABLE:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            # Training examples for SBERT
            self.training_examples = {
                'incident_reporting': [
                    "I need to report a workplace injury",
                    "There was an accident at the facility",
                    "Someone got hurt on the job",
                    "Property damage occurred",
                    "Chemical spill happened"
                ],
                'safety_concern': [
                    "I observed unsafe working conditions",
                    "There's a potential safety hazard",
                    "I'm concerned about workplace safety",
                    "Near miss incident observed",
                    "Unsafe behavior noticed"
                ],
                'sds_lookup': [
                    "I need the safety data sheet for acetone",
                    "Where can I find chemical information",
                    "Looking for SDS documents",
                    "Chemical safety information needed",
                    "Material safety data required"
                ]
            }
            self._build_sbert_index()
    
    def _build_sbert_index(self):
        """Build SBERT embeddings for training examples"""
        if not SBERT_AVAILABLE:
            return
            
        self.intent_embeddings = {}
        for intent, examples in self.training_examples.items():
            embeddings = self.model.encode(examples)
            self.intent_embeddings[intent] = embeddings
    
    def classify_intent(self, message: str) -> Tuple[str, float]:
        """Classify intent using hybrid approach"""
        message_lower = message.lower().strip()
        
        # First try rule-based classification
        for intent, patterns in self.rule_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent, 0.9  # High confidence for rule matches
        
        # If no rule match, try SBERT classification
        if SBERT_AVAILABLE and self.intent_embeddings:
            return self._sbert_classify(message)
        
        # Default fallback
        return 'general_inquiry', 0.3
    
    def _sbert_classify(self, message: str) -> Tuple[str, float]:
        """SBERT-based classification"""
        message_embedding = self.model.encode([message])[0]
        
        best_intent = 'general_inquiry'
        best_score = 0.0
        
        for intent, embeddings in self.intent_embeddings.items():
            similarities = np.dot(embeddings, message_embedding)
            max_similarity = np.max(similarities)
            
            if max_similarity > best_score:
                best_score = max_similarity
                best_intent = intent
        
        # Threshold for confidence
        confidence = best_score if best_score > 0.5 else 0.3
        return best_intent, confidence

class SlotFillingPolicy:
    """Slot filling policies for different incident types"""
    
    def __init__(self):
        self.incident_slots = {
            'injury': {
                'required': ['description', 'location', 'injured_person', 'injury_type', 'body_part', 'severity'],
                'optional': ['witnesses', 'ppe_worn', 'immediate_care', 'photos']
            },
            'vehicle': {
                'required': ['description', 'location', 'vehicles_involved', 'damage_estimate', 'injuries'],
                'optional': ['weather_conditions', 'photos', 'police_report']
            },
            'environmental': {
                'required': ['description', 'location', 'chemical_name', 'spill_volume', 'containment'],
                'optional': ['sds_available', 'environmental_impact', 'cleanup_actions']
            },
            'near_miss': {
                'required': ['description', 'location', 'potential_consequences'],
                'optional': ['contributing_factors', 'lessons_learned']
            },
            'property': {
                'required': ['description', 'location', 'damage_description', 'estimated_cost'],
                'optional': ['equipment_involved', 'photos']
            }
        }
        
        self.slot_questions = {
            'description': "Please describe what happened in detail:",
            'location': "Where did this incident occur? (Building, area, specific location)",
            'injured_person': "Who was injured? (Name or 'Anonymous' if preferred)",
            'injury_type': "What type of injury occurred? (Cut, burn, strain, etc.)",
            'body_part': "Which part of the body was affected?",
            'severity': "How severe was the injury? (First aid only, Medical treatment, Lost time, etc.)",
            'witnesses': "Were there any witnesses? (Names or 'None')",
            'ppe_worn': "What personal protective equipment was being worn?",
            'chemical_name': "What chemical was involved?",
            'spill_volume': "Approximately how much was spilled? (Include units)",
            'vehicles_involved': "Which vehicles were involved?",
            'damage_estimate': "What's the estimated damage cost?",
            'potential_consequences': "What could have happened if conditions were slightly different?"
        }

class EHSChatbot:
    """Enhanced EHS Chatbot with slot filling and mode detection"""
    
    def __init__(self):
        self.conversation_history = []
        self.current_mode = 'general'  # general, incident, safety_concern, sds_qa
        self.current_context = {}
        self.slot_filling_state = {}
        self.intent_classifier = IntentClassifier()
        self.slot_policy = SlotFillingPolicy()
        
    def process_message(self, user_message: str, user_id: str = None, context: Dict = None) -> Dict:
        """Main message processing with mode detection and slot filling"""
        context = context or {}
        user_id = user_id or "default_user"
        
        # Handle file uploads
        uploaded_file = context.get("uploaded_file")
        if uploaded_file:
            return self.handle_file_upload(user_message, uploaded_file, context)
        
        # Emergency detection (highest priority)
        if self.is_emergency(user_message):
            return self.handle_emergency()
        
        # Intent classification
        intent, confidence = self.intent_classifier.classify_intent(user_message)
        
        # Mode switching based on intent
        if confidence > 0.7:
            self.switch_mode(intent)
        
        # Process based on current mode
        if self.current_mode == 'incident':
            response = self.process_incident_mode(user_message, intent, confidence)
        elif self.current_mode == 'safety_concern':
            response = self.process_safety_concern_mode(user_message, intent, confidence)
        elif self.current_mode == 'sds_qa':
            response = self.process_sds_mode(user_message, intent, confidence)
        else:
            response = self.process_general_mode(user_message, intent, confidence)
        
        # Store conversation
        self.conversation_history.append({
            "user": user_message,
            "bot": response.get("message", ""),
            "intent": intent,
            "confidence": confidence,
            "mode": self.current_mode,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def switch_mode(self, intent: str):
        """Switch chatbot mode based on detected intent"""
        mode_mapping = {
            'incident_reporting': 'incident',
            'safety_concern': 'safety_concern',
            'sds_lookup': 'sds_qa',
            'risk_assessment': 'general',
            'capa_management': 'general'
        }
        
        new_mode = mode_mapping.get(intent, 'general')
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.current_context = {}
            self.slot_filling_state = {}
    
    def process_incident_mode(self, message: str, intent: str, confidence: float) -> Dict:
        """Process messages in incident reporting mode with slot filling"""
        
        # If no incident type selected yet, ask for it
        if 'incident_type' not in self.current_context:
            detected_type = self.detect_incident_type(message)
            if detected_type:
                self.current_context['incident_type'] = detected_type
                self.slot_filling_state = {'filled': [], 'current_slot': None}
                return self.start_slot_filling(detected_type)
            else:
                return self.ask_incident_type()
        
        # Continue slot filling
        return self.continue_slot_filling(message)
    
    def detect_incident_type(self, message: str) -> Optional[str]:
        """Detect specific incident type from message"""
        type_patterns = {
            'injury': [r'injur', r'hurt', r'cut', r'burn', r'strain', r'medical'],
            'vehicle': [r'vehicle', r'car', r'truck', r'collision', r'crash', r'accident.*vehicle'],
            'environmental': [r'spill', r'chemical', r'environmental', r'leak', r'release'],
            'near_miss': [r'near.*miss', r'almost', r'could.*have', r'close.*call'],
            'property': [r'damage', r'broken', r'property', r'equipment.*damage']
        }
        
        message_lower = message.lower()
        for incident_type, patterns in type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return incident_type
        
        return None
    
    def ask_incident_type(self) -> Dict:
        """Ask user to specify incident type"""
        return {
            "message": "🚨 **I'll help you report this incident.**\n\nTo ensure proper documentation, what type of incident occurred?",
            "type": "incident_type_selection",
            "actions": [
                {
                    "text": "🩹 Injury/Medical",
                    "action": "continue_conversation",
                    "message": "This involves a workplace injury"
                },
                {
                    "text": "🚗 Vehicle Incident",
                    "action": "continue_conversation",
                    "message": "This involves a vehicle accident"
                },
                {
                    "text": "🌊 Environmental Spill",
                    "action": "continue_conversation",
                    "message": "This involves a chemical spill or environmental release"
                },
                {
                    "text": "⚠️ Near Miss",
                    "action": "continue_conversation",
                    "message": "This was a near miss incident"
                },
                {
                    "text": "💔 Property Damage",
                    "action": "continue_conversation",
                    "message": "This involves property or equipment damage"
                },
                {
                    "text": "📝 Other Incident",
                    "action": "navigate",
                    "url": "/incidents/new"
                }
            ],
            "guidance": "**Remember:** If anyone needs immediate medical attention, call 911 first. Report to the system after ensuring everyone's safety."
        }
    
    def start_slot_filling(self, incident_type: str) -> Dict:
        """Start the slot filling process for an incident type"""
        slots = self.slot_policy.incident_slots.get(incident_type, {})
        required_slots = slots.get('required', [])
        
        if required_slots:
            first_slot = required_slots[0]
            self.slot_filling_state['current_slot'] = first_slot
            question = self.slot_policy.slot_questions.get(first_slot, f"Please provide {first_slot}:")
            
            return {
                "message": f"📝 **{incident_type.title()} Incident Report**\n\n{question}",
                "type": "slot_filling",
                "slot": first_slot,
                "progress": f"Step 1 of {len(required_slots)}",
                "guidance": "I'll guide you through each required field step by step."
            }
        
        return self.complete_incident_report()
    
    def continue_slot_filling(self, message: str) -> Dict:
        """Continue slot filling process"""
        current_slot = self.slot_filling_state.get('current_slot')
        if not current_slot:
            return self.complete_incident_report()
        
        # Store the answer
        self.current_context[current_slot] = message
        self.slot_filling_state['filled'].append(current_slot)
        
        # Get next slot
        incident_type = self.current_context.get('incident_type')
        slots = self.slot_policy.incident_slots.get(incident_type, {})
        required_slots = slots.get('required', [])
        
        remaining_slots = [slot for slot in required_slots if slot not in self.slot_filling_state['filled']]
        
        if remaining_slots:
            next_slot = remaining_slots[0]
            self.slot_filling_state['current_slot'] = next_slot
            question = self.slot_policy.slot_questions.get(next_slot, f"Please provide {next_slot}:")
            
            step_num = len(self.slot_filling_state['filled']) + 1
            total_steps = len(required_slots)
            
            return {
                "message": f"✅ Got it.\n\n**Next:** {question}",
                "type": "slot_filling",
                "slot": next_slot,
                "progress": f"Step {step_num} of {total_steps}",
                "filled_slots": len(self.slot_filling_state['filled']),
                "total_slots": total_steps
            }
        
        return self.complete_incident_report()
    
    def complete_incident_report(self) -> Dict:
        """Complete the incident report and show summary"""
        # Calculate severity and likelihood scores
        risk_assessment = self.auto_assess_risk()
        
        # Generate summary
        incident_type = self.current_context.get('incident_type', 'unknown')
        incident_id = self.generate_incident_id()
        
        # Store incident data
        self.save_incident_data(incident_id, risk_assessment)
        
        summary = self.generate_incident_summary()
        
        return {
            "message": f"✅ **Incident Report Completed**\n\n**Incident ID:** `{incident_id}`\n\n{summary}\n\n**Risk Assessment:**\n• **Severity:** {risk_assessment['severity']}\n• **Likelihood:** {risk_assessment['likelihood']}\n• **Overall Risk:** {risk_assessment['risk_level']}",
            "type": "incident_completed",
            "incident_id": incident_id,
            "actions": [
                {
                    "text": "📄 Generate PDF Report",
                    "action": "navigate",
                    "url": f"/incidents/{incident_id}/pdf"
                },
                {
                    "text": "✏️ Edit Details",
                    "action": "navigate",
                    "url": f"/incidents/{incident_id}/edit"
                },
                {
                    "text": "🔄 Create Follow-up CAPA",
                    "action": "navigate",
                    "url": f"/capa/new?source=incident&source_id={incident_id}"
                },
                {
                    "text": "📊 View Dashboard",
                    "action": "navigate",
                    "url": "/dashboard"
                }
            ],
            "guidance": "Your incident has been recorded and assigned a unique ID. You can generate a PDF report, make edits, or create corrective actions as needed."
        }
    
    def auto_assess_risk(self) -> Dict:
        """Auto-assess risk based on incident details using semantic analysis"""
        incident_type = self.current_context.get('incident_type', 'other')
        description = self.current_context.get('description', '').lower()
        
        # Simple rule-based assessment (could be enhanced with ML)
        severity_indicators = {
            'high': ['severe', 'hospitalization', 'major', 'serious', 'significant'],
            'medium': ['moderate', 'medical treatment', 'minor', 'first aid'],
            'low': ['superficial', 'negligible', 'trivial']
        }
        
        likelihood_indicators = {
            'high': ['frequently', 'often', 'regularly', 'common'],
            'medium': ['occasionally', 'sometimes', 'periodic'],
            'low': ['rarely', 'unusual', 'isolated', 'unique']
        }
        
        # Assess severity
        severity = 'medium'  # default
        for level, indicators in severity_indicators.items():
            if any(indicator in description for indicator in indicators):
                severity = level
                break
        
        # Assess likelihood  
        likelihood = 'medium'  # default
        for level, indicators in likelihood_indicators.items():
            if any(indicator in description for indicator in indicators):
                likelihood = level
                break
        
        # Calculate overall risk
        risk_matrix = {
            ('high', 'high'): 'Critical',
            ('high', 'medium'): 'High',
            ('high', 'low'): 'Medium',
            ('medium', 'high'): 'High',
            ('medium', 'medium'): 'Medium',
            ('medium', 'low'): 'Low',
            ('low', 'high'): 'Medium',
            ('low', 'medium'): 'Low',
            ('low', 'low'): 'Very Low'
        }
        
        risk_level = risk_matrix.get((severity, likelihood), 'Medium')
        
        return {
            'severity': severity.title(),
            'likelihood': likelihood.title(),
            'risk_level': risk_level,
            'rationale': f"Based on incident type: {incident_type} and description analysis"
        }
    
    def generate_incident_id(self) -> str:
        """Generate unique incident ID"""
        timestamp = str(int(time.time() * 1000))
        incident_type = self.current_context.get('incident_type', 'INC')[:3].upper()
        return f"{incident_type}-{timestamp[-8:]}"
    
    def save_incident_data(self, incident_id: str, risk_assessment: Dict):
        """Save incident data to file system"""
        try:
            # Load existing incidents
            incidents_file = Path("data/incidents.json")
            incidents_file.parent.mkdir(exist_ok=True)
            
            if incidents_file.exists():
                incidents = json.loads(incidents_file.read_text())
            else:
                incidents = {}
            
            # Create incident record
            incident_data = {
                "id": incident_id,
                "type": self.current_context.get('incident_type', 'other'),
                "created_ts": time.time(),
                "status": "complete",
                "answers": {
                    "people": self.extract_people_info(),
                    "environment": self.extract_environment_info(),
                    "cost": self.extract_cost_info(),
                    "legal": self.extract_legal_info(),
                    "reputation": self.extract_reputation_info()
                },
                "chatbot_data": self.current_context,
                "risk_assessment": risk_assessment,
                "reported_via": "chatbot"
            }
            
            incidents[incident_id] = incident_data
            incidents_file.write_text(json.dumps(incidents, indent=2))
            
        except Exception as e:
            print(f"Error saving incident: {e}")
    
    def extract_people_info(self) -> str:
        """Extract people-related information from context"""
        people_fields = ['injured_person', 'injury_type', 'body_part', 'severity', 'witnesses', 'ppe_worn']
        people_info = []
        
        for field in people_fields:
            if field in self.current_context:
                people_info.append(f"{field.replace('_', ' ').title()}: {self.current_context[field]}")
        
        return "\n".join(people_info) if people_info else "N/A"
    
    def extract_environment_info(self) -> str:
        """Extract environment-related information from context"""
        env_fields = ['chemical_name', 'spill_volume', 'containment', 'environmental_impact']
        env_info = []
        
        for field in env_fields:
            if field in self.current_context:
                env_info.append(f"{field.replace('_', ' ').title()}: {self.current_context[field]}")
        
        return "\n".join(env_info) if env_info else "N/A"
    
    def extract_cost_info(self) -> str:
        """Extract cost-related information from context"""
        cost_fields = ['damage_estimate', 'estimated_cost', 'equipment_involved']
        cost_info = []
        
        for field in cost_fields:
            if field in self.current_context:
                cost_info.append(f"{field.replace('_', ' ').title()}: {self.current_context[field]}")
        
        return "\n".join(cost_info) if cost_info else "N/A"
    
    def extract_legal_info(self) -> str:
        """Extract legal-related information from context"""
        legal_fields = ['police_report', 'regulatory_notification', 'legal_action']
        legal_info = []
        
        # Auto-determine if reportable
        incident_type = self.current_context.get('incident_type')
        if incident_type in ['injury', 'environmental']:
            legal_info.append("Reportability: May require regulatory notification - review with EHS team")
        
        for field in legal_fields:
            if field in self.current_context:
                legal_info.append(f"{field.replace('_', ' ').title()}: {self.current_context[field]}")
        
        return "\n".join(legal_info) if legal_info else "To be determined"
    
    def extract_reputation_info(self) -> str:
        """Extract reputation-related information from context"""
        reputation_fields = ['public_exposure', 'media_attention', 'client_impact']
        reputation_info = []
        
        for field in reputation_fields:
            if field in self.current_context:
                reputation_info.append(f"{field.replace('_', ' ').title()}: {self.current_context[field]}")
        
        return "\n".join(reputation_info) if reputation_info else "Low impact expected"
    
    def generate_incident_summary(self) -> str:
        """Generate human-readable summary of incident"""
        incident_type = self.current_context.get('incident_type', 'Unknown')
        description = self.current_context.get('description', 'No description provided')
        location = self.current_context.get('location', 'Location not specified')
        
        summary = f"**Type:** {incident_type.title()}\n"
        summary += f"**Location:** {location}\n"
        summary += f"**Description:** {description[:200]}{'...' if len(description) > 200 else ''}"
        
        return summary
    
    def process_safety_concern_mode(self, message: str, intent: str, confidence: float) -> Dict:
        """Process safety concern reporting mode"""
        # Similar slot filling for safety concerns but lighter
        return {
            "message": "🛡️ **Safety Concern Noted**\n\nThank you for speaking up! I'll help you document this safety observation.",
            "type": "safety_concern",
            "actions": [
                {
                    "text": "📝 Complete Safety Report",
                    "action": "navigate", 
                    "url": "/safety-concerns/new"
                },
                {
                    "text": "📞 Anonymous Report",
                    "action": "navigate",
                    "url": "/safety-concerns/new?anonymous=true"
                }
            ]
        }
    
    def process_sds_mode(self, message: str, intent: str, confidence: float) -> Dict:
        """Process SDS Q&A mode"""
        # Implement SDS chat functionality
        return {
            "message": "📄 **SDS Q&A Mode**\n\nI can help you find and chat with Safety Data Sheets. What chemical are you looking for?",
            "type": "sds_qa",
            "actions": [
                {
                    "text": "🔍 Search SDS Library",
                    "action": "navigate",
                    "url": "/sds"
                },
                {
                    "text": "📤 Upload New SDS",
                    "action": "navigate",
                    "url": "/sds/upload"
                }
            ]
        }
    
    def process_general_mode(self, message: str, intent: str, confidence: float) -> Dict:
        """Process general inquiries and other intents"""
        if intent == 'risk_assessment':
            return {
                "message": "📊 **Risk Assessment**\n\nI'll help you evaluate workplace risks using our ERC matrix.",
                "type": "risk_guide",
                "actions": [
                    {
                        "text": "🎯 Start Risk Assessment",
                        "action": "navigate",
                        "url": "/risk/assess"
                    },
                    {
                        "text": "📋 View Risk Register",
                        "action": "navigate",
                        "url": "/risk/register"
                    }
                ]
            }
        elif intent == 'capa_management':
            return {
                "message": "🔄 **CAPA Management**\n\nI can help you with Corrective and Preventive Actions.",
                "type": "capa_guide",
                "actions": [
                    {
                        "text": "➕ Create CAPA",
                        "action": "navigate",
                        "url": "/capa/new"
                    },
                    {
                        "text": "📊 CAPA Dashboard",
                        "action": "navigate",
                        "url": "/capa/dashboard"
                    }
                ]
            }
        else:
            return self.get_general_help_response()
    
    def handle_file_upload(self, message: str, file_info: Dict, context: Dict) -> Dict:
        """Handle file uploads with intelligent routing"""
        filename = file_info.get("filename", "")
        file_type = file_info.get("type", "")
        file_path = file_info.get("path", "")
        
        # Store file in context for later use
        self.current_context["uploaded_file"] = file_info
        
        if file_type.startswith('image/'):
            # Analyze image for incident evidence
            image_analysis = self.analyze_incident_image(file_path)
            
            return {
                "message": f"📸 **Image received: {filename}**\n\n{image_analysis['message']}\n\nI can help you use this image for incident reporting. What happened?",
                "type": "image_upload_incident",
                "actions": [
                    {
                        "text": "🚨 Use for Incident Report",
                        "action": "continue_conversation",
                        "message": "I want to report an incident with this photo as evidence"
                    },
                    {
                        "text": "🛡️ Use for Safety Concern",
                        "action": "continue_conversation",
                        "message": "I want to report a safety concern with this photo"
                    }
                ],
                "image_analysis": image_analysis
            }
            
        elif file_type == 'application/pdf':
            # Check if it's an SDS
            sds_analysis = self.analyze_potential_sds(file_path)
            
            return {
                "message": f"📄 **PDF received: {filename}**\n\n{sds_analysis['message']}",
                "type": "pdf_upload_sds",
                "actions": [
                    {
                        "text": "📋 Add to SDS Library",
                        "action": "navigate",
                        "url": f"/sds/upload?file={file_path}"
                    },
                    {
                        "text": "💬 Chat with SDS Content",
                        "action": "continue_conversation",
                        "message": "I want to ask questions about this SDS document"
                    }
                ],
                "sds_analysis": sds_analysis
            }
        
        return {
            "message": f"📎 **File received: {filename}**\n\nHow would you like to use this in the EHS system?",
            "type": "general_upload",
            "actions": [
                {
                    "text": "📝 Use for Incident Report",
                    "action": "continue_conversation",
                    "message": "I want to use this file for an incident report"
                },
                {
                    "text": "📚 Add to Documentation",
                    "action": "continue_conversation",
                    "message": "This is supporting documentation"
                }
            ]
        }
    
    def analyze_incident_image(self, file_path: str) -> Dict:
        """Analyze uploaded image for incident evidence (basic implementation)"""
        # In a real implementation, this could use computer vision
        # For now, provide basic guidance based on common incident types
        
        return {
            "message": "This appears to be photographic evidence that could be valuable for incident documentation.",
            "tags": ["evidence", "photo"],
            "suggestions": [
                "Document the scene and conditions",
                "Show any safety hazards or damage",
                "Capture equipment or PPE involved"
            ]
        }
    
    def analyze_potential_sds(self, file_path: str) -> Dict:
        """Analyze uploaded PDF to determine if it's an SDS"""
        # In a real implementation, this would extract text and analyze content
        # For now, provide guidance for SDS handling
        
        return {
            "message": "This PDF could be a Safety Data Sheet or related chemical documentation.",
            "likely_sds": True,
            "suggestions": [
                "Add to searchable SDS library",
                "Enable AI chat functionality", 
                "Generate QR codes for easy access"
            ]
        }
    
    def is_emergency(self, message: str) -> bool:
        """Detect emergency situations"""
        emergency_keywords = [
            "emergency", "911", "fire", "bleeding", "unconscious", "heart attack",
            "severe injury", "immediate danger", "life threatening", "call ambulance",
            "help", "urgent", "critical", "serious injury"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in emergency_keywords)
    
    def handle_emergency(self) -> Dict:
        """Emergency response with clear instructions"""
        return {
            "message": "🚨 **EMERGENCY DETECTED** 🚨\n\n**FOR LIFE-THREATENING EMERGENCIES:**\n📞 **CALL 911 IMMEDIATELY**\n\n**Site Emergency Contacts:**\n• Site Emergency: (555) 123-4567\n• Security: (555) 123-4568\n• EHS Hotline: (555) 123-4569\n\n**After ensuring everyone's safety, I can help you document this incident.**",
            "type": "emergency",
            "priority": "critical",
            "actions": [
                {
                    "text": "📝 Report Emergency Incident",
                    "action": "continue_conversation",
                    "message": "I need to report an emergency incident that just occurred"
                },
                {
                    "text": "🚨 Call Site Emergency",
                    "action": "external",
                    "url": "tel:5551234567"
                }
            ],
            "guidance": "**REMEMBER:** Life safety comes first. Only use this system AFTER addressing immediate emergency needs."
        }
    
    def get_general_help_response(self) -> Dict:
        """General help and navigation response"""
        return {
            "message": "🤖 **I'm your Smart EHS Assistant!**\n\nI can help you with:\n\n• 🚨 **Report incidents** and safety concerns\n• 📊 **Conduct risk assessments** using ERC matrix\n• 🔄 **Manage CAPAs** and corrective actions\n• 📄 **Find safety data sheets** and chemical info\n• 📋 **Complete audits** and inspections\n• 📈 **View dashboards** and urgent items\n\nWhat would you like to work on?",
            "type": "help_menu",
            "actions": [
                {
                    "text": "🚨 Report Incident",
                    "action": "continue_conversation",
                    "message": "I need to report a workplace incident"
                },
                {
                    "text": "🛡️ Safety Concern",
                    "action": "continue_conversation",
                    "message": "I want to report a safety concern"
                },
                {
                    "text": "📊 View Dashboard",
                    "action": "navigate",
                    "url": "/dashboard"
                },
                {
                    "text": "📄 Find SDS",
                    "action": "navigate",
                    "url": "/sds"
                }
            ],
            "quick_replies": [
                "Report an incident",
                "Safety concern",
                "Risk assessment",
                "Find SDS",
                "What's urgent?"
            ]
        }
    
    def get_conversation_summary(self) -> Dict:
        """Get conversation summary with analytics"""
        if not self.conversation_history:
            return {"summary": "No conversation yet", "message_count": 0}
        
        intent_counts = {}
        for exchange in self.conversation_history:
            intent = exchange.get("intent", "unknown")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        last_intent = self.conversation_history[-1].get("intent") if self.conversation_history else None
        
        return {
            "message_count": len(self.conversation_history),
            "last_intent": last_intent,
            "current_mode": self.current_mode,
            "intent_distribution": intent_counts,
            "timestamp": datetime.now().isoformat(),
            "active_context": bool(self.current_context),
            "slot_filling_active": bool(self.slot_filling_state)
        }

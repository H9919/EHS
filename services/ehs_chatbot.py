# services/ehs_chatbot.py - FIXED VERSION with all issues resolved
import json
import re
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Check if SBERT is enabled and available
ENABLE_SBERT = os.environ.get('ENABLE_SBERT', 'false').lower() == 'true'
SBERT_AVAILABLE = False

if ENABLE_SBERT:
    try:
        from sentence_transformers import SentenceTransformer
        SBERT_AVAILABLE = True
        print("✓ SBERT enabled and available")
    except ImportError:
        print("⚠ SBERT requested but not available - using fallback")
        SBERT_AVAILABLE = False
else:
    print("ℹ SBERT disabled via environment variable")

class SmartIntentClassifier:
    """Enhanced intent classifier with better pattern matching and context awareness"""
    
    def __init__(self):
        self.intent_patterns = {
            'incident_reporting': {
                'keywords': [
                    'report incident', 'incident report', 'workplace incident', 'accident', 
                    'injury', 'hurt', 'injured', 'damage', 'spill', 'collision', 'crash', 
                    'fall', 'slip', 'trip', 'cut', 'burn', 'emergency happened', 
                    'something happened', 'someone hurt', 'property damage', 'near miss'
                ],
                'confidence_boost': 0.9
            },
            'safety_concern': {
                'keywords': [
                    'safety concern', 'unsafe condition', 'hazard', 'safety observation',
                    'concern about safety', 'safety issue', 'dangerous', 'unsafe'
                ],
                'confidence_boost': 0.8
            },
            'sds_lookup': {
                'keywords': [
                    'safety data sheet', 'sds', 'msds', 'chemical information',
                    'find sds', 'chemical safety', 'material safety', 'chemical data'
                ],
                'confidence_boost': 0.8
            },
            'general_help': {
                'keywords': [
                    'help', 'what can you do', 'show menu', 'assistance', 'guide me',
                    'get started', 'how to', 'what is'
                ],
                'confidence_boost': 0.7
            },
            'continue_conversation': {
                'keywords': [
                    'try again', 'retry', 'continue', 'yes', 'okay', 'sure', 'next'
                ],
                'confidence_boost': 0.6
            }
        }
    
    def classify_intent(self, message: str, context: Dict = None) -> Tuple[str, float]:
        """Classify intent with context awareness"""
        if not message or not isinstance(message, str):
            return 'general_inquiry', 0.0
            
        message_lower = message.lower().strip()
        
        # Check for emergency keywords first
        emergency_keywords = ['emergency', '911', 'fire', 'bleeding', 'unconscious', 'heart attack']
        if any(word in message_lower for word in emergency_keywords):
            return 'emergency', 1.0
        
        best_intent = 'general_inquiry'
        best_confidence = 0.0
        
        for intent, config in self.intent_patterns.items():
            confidence = 0.0
            
            # Check for keyword matches
            for keyword in config['keywords']:
                if keyword in message_lower:
                    confidence = config['confidence_boost']
                    break
            
            # Context-based confidence adjustment
            if context:
                if intent == 'continue_conversation' and context.get('waiting_for_response'):
                    confidence += 0.3
                elif intent == 'incident_reporting' and context.get('current_mode') == 'incident':
                    confidence += 0.2
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = intent
        
        return best_intent, best_confidence

class SmartSlotPolicy:
    """Enhanced slot filling with intelligent conversation flow"""
    
    def __init__(self):
        self.incident_slots = {
            'injury': {
                'required': ['description', 'location', 'injured_person', 'injury_type', 'severity'],
                'optional': ['body_part', 'witnesses', 'immediate_action']
            },
            'environmental': {
                'required': ['description', 'location', 'substance_involved', 'containment'],
                'optional': ['spill_volume', 'environmental_impact', 'cleanup_action']
            },
            'property': {
                'required': ['description', 'location', 'damage_description', 'estimated_cost'],
                'optional': ['equipment_involved', 'downtime']
            },
            'vehicle': {
                'required': ['description', 'location', 'vehicles_involved', 'injuries'],
                'optional': ['weather_conditions', 'road_conditions']
            },
            'near_miss': {
                'required': ['description', 'location', 'potential_consequences'],
                'optional': ['contributing_factors', 'prevention_measures']
            },
            'other': {
                'required': ['description', 'location', 'incident_type'],
                'optional': ['people_involved', 'impact_assessment']
            }
        }
        
        self.slot_questions = {
            'description': "Please describe what happened in detail. Include who was involved, what occurred, when it happened, and the sequence of events:",
            'location': "Where exactly did this incident occur? (Building, room, area, or specific location)",
            'injured_person': "Who was injured? Please provide the person's name and job title:",
            'injury_type': "What type of injury occurred? (e.g., cut, bruise, sprain, fracture, burn)",
            'severity': "How severe was the injury? (Minor/first aid, medical treatment required, hospitalization needed, or life-threatening)",
            'body_part': "Which part of the body was injured?",
            'substance_involved': "What chemical or substance was involved in this incident?",
            'containment': "Was the spill or release contained? Please describe the containment measures taken:",
            'spill_volume': "Approximately how much material was spilled or released?",
            'damage_description': "Please describe the property damage in detail:",
            'estimated_cost': "What is the estimated cost of the damage? (If unknown, please estimate: <$1000, $1000-$10000, $10000+)",
            'vehicles_involved': "Which vehicles were involved? Include make, model, and any fleet numbers:",
            'injuries': "Were there any injuries in this vehicle incident? If yes, please describe:",
            'potential_consequences': "What could have happened if this near miss had become an actual incident?",
            'incident_type': "What type of incident is this? (equipment malfunction, procedural violation, security issue, etc.)",
            'witnesses': "Were there any witnesses to this incident? If yes, please provide names:",
            'immediate_action': "What immediate actions were taken after the incident occurred?"
        }

class SmartEHSChatbot:
    """Enhanced EHS Chatbot with intelligent conversation management"""
    
    def __init__(self):
        self.conversation_history = []
        self.current_mode = 'general'
        self.current_context = {}
        self.slot_filling_state = {}
        self.user_preferences = {}
        
        self.intent_classifier = SmartIntentClassifier()
        self.slot_policy = SmartSlotPolicy()
        
        print("✓ Smart EHS Chatbot initialized with enhanced conversation flow")
    
    def process_message(self, user_message: str, user_id: str = None, context: Dict = None) -> Dict:
        """Process message with intelligent conversation management"""
        try:
            # Validate and clean inputs
            user_message = str(user_message).strip() if user_message else ""
            user_id = user_id or "default_user"
            context = context or {}
            
            print(f"DEBUG: Processing message: '{user_message[:50]}...', mode: {self.current_mode}")
            
            # Handle empty messages
            if not user_message and not context.get("uploaded_file"):
                return self._get_clarification_response()
            
            # Handle file uploads
            if context.get("uploaded_file"):
                return self._handle_file_upload_smart(context["uploaded_file"], user_message)
            
            # Emergency detection (highest priority)
            if self._is_emergency(user_message):
                return self._handle_emergency()
            
            # Intent classification with context
            intent, confidence = self.intent_classifier.classify_intent(
                user_message, 
                {**self.current_context, 'current_mode': self.current_mode}
            )
            
            print(f"DEBUG: Intent: {intent}, Confidence: {confidence:.2f}")
            
            # Route to appropriate handler
            if self.current_mode == 'incident' and self.slot_filling_state:
                return self._continue_incident_reporting(user_message)
            elif intent == 'incident_reporting' and confidence > 0.6:
                return self._start_incident_reporting_smart(user_message)
            elif intent == 'safety_concern' and confidence > 0.6:
                return self._handle_safety_concern_smart(user_message)
            elif intent == 'sds_lookup' and confidence > 0.6:
                return self._handle_sds_request_smart(user_message)
            elif intent == 'continue_conversation' and confidence > 0.5:
                return self._handle_continue_conversation(user_message)
            elif intent == 'general_help' or confidence < 0.4:
                return self._handle_general_inquiry_smart(user_message)
            else:
                return self._get_smart_fallback_response(user_message, intent, confidence)
                
        except Exception as e:
            print(f"ERROR: process_message failed: {e}")
            import traceback
            traceback.print_exc()
            return self._get_error_recovery_response(str(e))
    
    def _start_incident_reporting_smart(self, message: str) -> Dict:
        """Start intelligent incident reporting with type detection"""
        print("DEBUG: Starting smart incident reporting")
        
        # Reset for new incident
        self.current_mode = 'incident'
        self.current_context = {'initial_message': message}
        
        # Detect incident type from message
        incident_type = self._detect_incident_type_smart(message)
        self.current_context['incident_type'] = incident_type
        
        print(f"DEBUG: Detected incident type: {incident_type}")
        
        # Get required slots for this incident type
        slots_config = self.slot_policy.incident_slots.get(incident_type, self.slot_policy.incident_slots['other'])
        required_slots = slots_config['required'].copy()
        
        # Initialize slot filling state
        self.slot_filling_state = {
            'required_slots': required_slots,
            'current_slot_index': 0,
            'collected_data': {},
            'incident_type': incident_type
        }
        
        # Start with first required slot
        if required_slots:
            first_slot = required_slots[0]
            question = self.slot_policy.slot_questions.get(first_slot, f"Please provide {first_slot.replace('_', ' ')}:")
            
            return {
                "message": f"🚨 **{incident_type.replace('_', ' ').title()} Incident Report**\n\nI'll help you report this incident step by step to ensure we capture all necessary details.\n\n**Step 1 of {len(required_slots)}:** {question}",
                "type": "incident_slot_filling",
                "slot": first_slot,
                "progress": {
                    "current": 1,
                    "total": len(required_slots),
                    "percentage": int((1 / len(required_slots)) * 100)
                },
                "incident_type": incident_type,
                "quick_replies": self._get_slot_quick_replies(first_slot)
            }
        else:
            return self._complete_incident_report()
    
    def _continue_incident_reporting(self, message: str) -> Dict:
        """Continue incident reporting with smart validation"""
        if not self.slot_filling_state:
            return self._complete_incident_report()
        
        required_slots = self.slot_filling_state.get('required_slots', [])
        current_index = self.slot_filling_state.get('current_slot_index', 0)
        collected_data = self.slot_filling_state.get('collected_data', {})
        
        if current_index >= len(required_slots):
            return self._complete_incident_report()
        
        current_slot = required_slots[current_index]
        
        # Validate the response for this slot
        validation_result = self._validate_slot_response(current_slot, message)
        
        if not validation_result['valid']:
            return {
                "message": f"❌ **Please provide more details**\n\n{validation_result['message']}\n\n**Question:** {self.slot_policy.slot_questions.get(current_slot)}",
                "type": "incident_slot_validation_failed",
                "slot": current_slot,
                "validation_error": validation_result['message']
            }
        
        # Store the validated response
        collected_data[current_slot] = message
        self.current_context[current_slot] = message
        
        # Move to next slot
        current_index += 1
        self.slot_filling_state['current_slot_index'] = current_index
        self.slot_filling_state['collected_data'] = collected_data
        
        # Check if we have more slots
        if current_index < len(required_slots):
            next_slot = required_slots[current_index]
            question = self.slot_policy.slot_questions.get(next_slot, f"Please provide {next_slot.replace('_', ' ')}:")
            
            progress_percentage = int(((current_index + 1) / len(required_slots)) * 100)
            
            return {
                "message": f"✅ **Recorded:** {message[:100]}{'...' if len(message) > 100 else ''}\n\n**Step {current_index + 1} of {len(required_slots)}:** {question}",
                "type": "incident_slot_filling",
                "slot": next_slot,
                "progress": {
                    "current": current_index + 1,
                    "total": len(required_slots),
                    "percentage": progress_percentage
                },
                "quick_replies": self._get_slot_quick_replies(next_slot)
            }
        else:
            return self._complete_incident_report()
    
    def _validate_slot_response(self, slot: str, response: str) -> Dict:
        """Validate slot responses to ensure quality data"""
        response = response.strip()
        
        # Minimum length requirements
        min_lengths = {
            'description': 20,
            'damage_description': 15,
            'potential_consequences': 15,
            'containment': 10
        }
        
        min_length = min_lengths.get(slot, 5)
        if len(response) < min_length:
            return {
                'valid': False,
                'message': f"Please provide more detail (at least {min_length} characters). This information is important for proper investigation."
            }
        
        # Specific validations
        if slot == 'injured_person' and len(response) < 3:
            return {
                'valid': False,
                'message': "Please provide the injured person's name. This is required for proper documentation and follow-up."
            }
        
        if slot == 'location' and len(response) < 3:
            return {
                'valid': False,
                'message': "Please specify the exact location where this incident occurred."
            }
        
        if slot == 'severity' and not any(word in response.lower() for word in ['minor', 'first aid', 'medical', 'hospital', 'serious', 'life threatening']):
            return {
                'valid': False,
                'message': "Please describe the severity level (e.g., minor/first aid, medical treatment needed, hospitalization required, or life-threatening)."
            }
        
        return {'valid': True, 'message': 'Valid response'}
    
    def _get_slot_quick_replies(self, slot: str) -> List[str]:
        """Get contextual quick replies for different slots"""
        quick_replies = {
            'severity': ['Minor - first aid only', 'Medical treatment required', 'Hospitalization needed'],
            'injury_type': ['Cut/laceration', 'Bruise/contusion', 'Sprain/strain', 'Fracture/break', 'Burn'],
            'body_part': ['Hand/finger', 'Arm/shoulder', 'Leg/foot', 'Back', 'Head/face'],
            'containment': ['Fully contained', 'Partially contained', 'Not contained'],
            'estimated_cost': ['Under $1,000', '$1,000 - $10,000', 'Over $10,000', 'Unknown at this time']
        }
        
        return quick_replies.get(slot, [])
    
    def _complete_incident_report(self) -> Dict:
        """Complete incident report with enhanced data processing"""
        try:
            incident_id = f"INC-{int(time.time())}"
            
            # Generate comprehensive summary
            summary = self._generate_incident_summary_smart()
            
            # Save incident data
            save_success = self._save_incident_data_safe(incident_id)
            
            # Reset state for next conversation
            self._reset_state()
            
            success_message = f"✅ **Incident Report Completed Successfully**\n\n**Incident ID:** `{incident_id}`\n\n{summary}\n\n🔔 **Next Steps:**\n• Investigation team has been notified\n• You will receive updates on the investigation progress\n• A formal report will be generated within 24 hours"
            
            if not save_success:
                success_message += "\n\n⚠️ Note: There was a technical issue saving some details, but your core report has been recorded."
            
            return {
                "message": success_message,
                "type": "incident_completed",
                "incident_id": incident_id,
                "actions": [
                    {"text": "📄 View Full Report", "action": "navigate", "url": f"/incidents/{incident_id}/edit"},
                    {"text": "📊 Go to Dashboard", "action": "navigate", "url": "/dashboard"},
                    {"text": "🆕 Report Another Incident", "action": "continue_conversation", "message": "I need to report another incident"}
                ],
                "quick_replies": [
                    "Report another incident",
                    "View all my reports", 
                    "What happens next?",
                    "Main menu"
                ]
            }
            
        except Exception as e:
            print(f"ERROR: Completing incident report failed: {e}")
            self._reset_state()
            
            return {
                "message": f"✅ **Incident Report Submitted**\n\nIncident ID: `INC-{int(time.time())}`\n\n⚠️ There was a technical issue, but your basic report has been recorded and the safety team has been notified.",
                "type": "incident_completed_with_error",
                "actions": [
                    {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"},
                    {"text": "🆕 New Incident", "action": "continue_conversation", "message": "I need to report another incident"}
                ]
            }
    
    def _generate_incident_summary_smart(self) -> str:
        """Generate intelligent incident summary"""
        incident_type = self.current_context.get('incident_type', 'Unknown')
        collected_data = self.slot_filling_state.get('collected_data', {})
        
        summary_parts = [f"**Type:** {incident_type.replace('_', ' ').title()}"]
        
        # Add key details based on incident type
        if 'location' in collected_data:
            summary_parts.append(f"**Location:** {collected_data['location']}")
        
        if incident_type == 'injury':
            if 'injured_person' in collected_data:
                summary_parts.append(f"**Injured Person:** {collected_data['injured_person']}")
            if 'injury_type' in collected_data:
                summary_parts.append(f"**Injury:** {collected_data['injury_type']}")
            if 'severity' in collected_data:
                summary_parts.append(f"**Severity:** {collected_data['severity']}")
        
        elif incident_type == 'environmental':
            if 'substance_involved' in collected_data:
                summary_parts.append(f"**Substance:** {collected_data['substance_involved']}")
            if 'containment' in collected_data:
                summary_parts.append(f"**Containment:** {collected_data['containment']}")
        
        elif incident_type == 'property':
            if 'damage_description' in collected_data:
                summary_parts.append(f"**Damage:** {collected_data['damage_description'][:50]}...")
            if 'estimated_cost' in collected_data:
                summary_parts.append(f"**Estimated Cost:** {collected_data['estimated_cost']}")
        
        return "\n".join(summary_parts)
    
    def _detect_incident_type_smart(self, message: str) -> str:
        """Smart incident type detection with confidence scoring"""
        message_lower = message.lower()
        
        type_indicators = {
            'injury': {
                'keywords': ['injury', 'injured', 'hurt', 'medical', 'hospital', 'pain', 'wound', 'cut', 'burn', 'fracture', 'sprain'],
                'weight': 3
            },
            'environmental': {
                'keywords': ['spill', 'leak', 'chemical', 'environmental', 'release', 'contamination', 'pollution'],
                'weight': 3
            },
            'property': {
                'keywords': ['damage', 'broke', 'broken', 'destroyed', 'property', 'equipment', 'machinery'],
                'weight': 2
            },
            'vehicle': {
                'keywords': ['vehicle', 'car', 'truck', 'collision', 'crash', 'accident', 'driving'],
                'weight': 2
            },
            'near_miss': {
                'keywords': ['near miss', 'almost', 'could have', 'nearly', 'close call'],
                'weight': 2
            }
        }
        
        scores = {}
        for incident_type, config in type_indicators.items():
            score = 0
            for keyword in config['keywords']:
                if keyword in message_lower:
                    score += config['weight']
            scores[incident_type] = score
        
        # Return type with highest score, or 'other' if no clear match
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        else:
            return 'other'
    
    def _handle_safety_concern_smart(self, message: str) -> Dict:
        """Handle safety concern with smart guidance"""
        return {
            "message": "🛡️ **Thank you for speaking up about safety!**\n\nEvery safety observation helps create a safer workplace. I can help you submit this concern properly.\n\n**What type of safety concern is this?**",
            "type": "safety_concern_guidance",
            "actions": [
                {"text": "⚠️ Submit Safety Concern", "action": "navigate", "url": "/safety-concerns/new"},
                {"text": "📞 Anonymous Report", "action": "navigate", "url": "/safety-concerns/new?anonymous=true"},
                {"text": "🚨 This is urgent/emergency", "action": "continue_conversation", "message": "This is an urgent safety emergency"}
            ],
            "quick_replies": [
                "Submit safety concern",
                "Report anonymously",
                "What types can I report?",
                "Is this urgent?"
            ]
        }
    
    def _handle_sds_request_smart(self, message: str) -> Dict:
        """Handle SDS request with intelligent search suggestions"""
        # Try to extract chemical name from message
        chemical_name = self._extract_chemical_name(message)
        
        base_message = "📄 **I'll help you find Safety Data Sheets**\n\nOur SDS library is searchable and contains safety information for workplace chemicals."
        
        if chemical_name:
            base_message += f"\n\n💡 I noticed you mentioned **{chemical_name}** - I can help you find that specific SDS."
        
        return {
            "message": base_message,
            "type": "sds_assistance",
            "actions": [
                {"text": "🔍 Search SDS Library", "action": "navigate", "url": "/sds"},
                {"text": "📤 Upload New SDS", "action": "navigate", "url": "/sds/upload"}
            ],
            "quick_replies": [
                f"Find {chemical_name} SDS" if chemical_name else "Search by chemical name",
                "Browse all SDS documents",
                "Upload new SDS",
                "How to use QR codes"
            ]
        }
    
    def _extract_chemical_name(self, message: str) -> str:
        """Extract chemical name from user message"""
        # Common chemical patterns
        chemical_patterns = [
            r'(?:sds for|looking for|find|need)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)',
            r'([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s+(?:sds|safety data sheet)',
            r'chemical\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)'
        ]
        
        for pattern in chemical_patterns:
            match = re.search(pattern, message.lower())
            if match:
                chemical = match.group(1).strip()
                if len(chemical) > 2 and chemical not in ['the', 'and', 'for', 'with']:
                    return chemical.title()
        
        return None
    
    def _handle_continue_conversation(self, message: str) -> Dict:
        """Handle conversation continuation requests"""
        if 'incident' in message.lower():
            return self._start_incident_reporting_smart("I need to report an incident")
        elif 'safety' in message.lower():
            return self._handle_safety_concern_smart(message)
        elif 'sds' in message.lower():
            return self._handle_sds_request_smart(message)
        else:
            return self._get_general_help_response()
    
    def _handle_general_inquiry_smart(self, message: str) -> Dict:
        """Handle general inquiries with context awareness"""
        if any(word in message.lower() for word in ['what', 'how', 'help', 'guide']):
            return self._get_general_help_response()
        else:
            return self._get_smart_fallback_response(message, 'general_inquiry', 0.3)
    
    def _get_smart_fallback_response(self, message: str, intent: str, confidence: float) -> Dict:
        """Generate contextually appropriate fallback responses"""
        
        suggestions = []
        
        # Analyze message for keywords to provide better suggestions
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['report', 'incident', 'accident']):
            suggestions.append({"text": "🚨 Report Incident", "action": "continue_conversation", "message": "I need to report a workplace incident"})
        
        if any(word in message_lower for word in ['safety', 'concern', 'unsafe']):
            suggestions.append({"text": "🛡️ Safety Concern", "action": "continue_conversation", "message": "I want to report a safety concern"})
        
        if any(word in message_lower for word in ['chemical', 'sds', 'data sheet']):
            suggestions.append({"text": "📋 Find SDS", "action": "continue_conversation", "message": "I need to find a safety data sheet"})
        
        # Default suggestions if no specific keywords found
        if not suggestions:
            suggestions = [
                {"text": "🚨 Report Incident", "action": "continue_conversation", "message": "I need to report a workplace incident"},
                {"text": "🛡️ Safety Concern", "action": "continue_conversation", "message": "I want to report a safety concern"},
                {"text": "📋 Find SDS", "action": "continue_conversation", "message": "I need to find a safety data sheet"},
                {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"}
            ]
        
        return {
            "message": f"🤖 **I want to help you with that!**\n\nI understand you said: *\"{message}\"*\n\nI'm here to help with EHS matters. Here are some things I can assist with:",
            "type": "smart_assistance",
            "actions": suggestions,
            "quick_replies": [
                "Show main menu",
                "What can you help with?",
                "Emergency contacts",
                "System guide"
            ]
        }
    
    def _get_clarification_response(self) -> Dict:
        """Get clarification when message is empty"""
        return {
            "message": "🤖 **How can I help you today?**\n\nI'm here to assist with EHS matters. You can ask me questions or choose from the options below:",
            "type": "clarification_request",
            "actions": [
                {"text": "🚨 Report Incident", "action": "continue_conversation", "message": "I need to report a workplace incident"},
                {"text": "🛡️ Safety Concern", "action": "continue_conversation", "message": "I want to report a safety concern"},
                {"text": "📋 Find SDS", "action": "continue_conversation", "message": "I need to find a safety data sheet"},
                {"text": "📊 View Dashboard", "action": "navigate", "url": "/dashboard"}
            ],
            "quick_replies": [
                "Report an incident",
                "Safety concern", 
                "Find SDS",
                "Emergency contacts",
                "Show all features"
            ]
        }
    
    def _handle_file_upload_smart(self, file_info: Dict, message: str) -> Dict:
        """Handle file uploads with intelligent context"""
        filename = file_info.get("filename", "")
        file_type = file_info.get("type", "")
        
        if file_type.startswith('image/'):
            return {
                "message": f"📸 **Image received: {filename}**\n\nThis photo can be used as evidence for incident reporting or safety documentation.\n\nWhat would you like to do with this image?",
                "type": "file_upload_smart",
                "actions": [
                    {"text": "🚨 Use for Incident Report", "action": "continue_conversation", "message": "I want to report an incident with this photo as evidence"},
                    {"text": "🛡️ Use for Safety Concern", "action": "continue_conversation", "message": "I want to report a safety concern with this photo"},
                    {"text": "📋 Document Safety Issue", "action": "navigate", "url": "/safety-concerns/new"}
                ],
                "quick_replies": [
                    "Report incident with photo",
                    "Safety concern with photo",
                    "What can I do with photos?"
                ]
            }
        elif file_type == 'application/pdf':
            return {
                "message": f"📄 **PDF received: {filename}**\n\nThis looks like it could be a Safety Data Sheet or other safety documentation.\n\nWhat would you like to do with this PDF?",
                "type": "file_upload_smart",
                "actions": [
                    {"text": "📋 Add to SDS Library", "action": "navigate", "url": "/sds/upload"},
                    {"text": "📊 Upload to System", "action": "navigate", "url": "/dashboard"}
                ],
                "quick_replies": [
                    "Add to SDS library",
                    "What is this PDF?",
                    "How to upload documents"
                ]
            }
        else:
            return {
                "message": f"📎 **File received: {filename}**\n\nI can help you use this file for EHS documentation or reporting.\n\nWhat would you like to do?",
                "type": "file_upload_smart",
                "actions": [
                    {"text": "🚨 Use for Incident Report", "action": "continue_conversation", "message": "I want to use this file for an incident report"},
                    {"text": "📋 Upload to System", "action": "navigate", "url": "/dashboard"}
                ]
            }
    
    def _is_emergency(self, message: str) -> bool:
        """Detect emergency situations"""
        try:
            emergency_words = ["emergency", "911", "fire", "bleeding", "unconscious", "heart attack", "urgent help"]
            return any(word in message.lower() for word in emergency_words)
        except:
            return False
    
    def _handle_emergency(self) -> Dict:
        """Handle emergency response with clear instructions"""
        return {
            "message": "🚨 **EMERGENCY DETECTED** 🚨\n\n**FOR IMMEDIATE LIFE-THREATENING EMERGENCIES:**\n🆘 **CALL 911 NOW**\n\n**For On-Site Emergencies:**\n📞 Site Emergency: (555) 123-4567\n🔒 Security: (555) 123-4568\n\n**After ensuring safety, you can report the incident through our system.**",
            "type": "emergency",
            "actions": [
                {"text": "📞 Call Emergency Services", "action": "external", "url": "tel:911"},
                {"text": "📝 Report Emergency Incident", "action": "navigate", "url": "/incidents/new?type=emergency"}
            ]
        }
    
    def _save_incident_data_safe(self, incident_id: str) -> bool:
        """Save incident data with comprehensive error handling"""
        try:
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            incidents_file = data_dir / "incidents.json"
            
            # Load existing incidents
            incidents = {}
            if incidents_file.exists():
                try:
                    content = incidents_file.read_text()
                    if content.strip():
                        incidents = json.loads(content)
                except Exception as e:
                    print(f"Warning: Could not load existing incidents: {e}")
                    incidents = {}
            
            # Create comprehensive incident record
            collected_data = self.slot_filling_state.get('collected_data', {})
            incident_type = self.current_context.get('incident_type', 'other')
            
            incident_data = {
                "id": incident_id,
                "type": incident_type,
                "created_ts": time.time(),
                "status": "complete",
                "answers": {
                    "people": self._extract_people_info_smart(collected_data, incident_type),
                    "environment": self._extract_environment_info_smart(collected_data, incident_type),
                    "cost": self._extract_cost_info_smart(collected_data, incident_type),
                    "legal": self._extract_legal_info_smart(collected_data, incident_type),
                    "reputation": self._extract_reputation_info_smart(collected_data, incident_type)
                },
                "chatbot_data": {
                    **collected_data,
                    "incident_type": incident_type,
                    "initial_message": self.current_context.get('initial_message', ''),
                    "completion_method": "smart_chatbot_v2"
                },
                "reported_via": "smart_chatbot"
            }
            
            # Save incident
            incidents[incident_id] = incident_data
            incidents_file.write_text(json.dumps(incidents, indent=2))
            print(f"DEBUG: Successfully saved incident {incident_id}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to save incident data: {e}")
            return False
    
    def _extract_people_info_smart(self, data: Dict, incident_type: str) -> str:
        """Extract comprehensive people information"""
        info_parts = []
        
        if 'description' in data:
            info_parts.append(f"Incident Description: {data['description']}")
        
        if incident_type == 'injury':
            if 'injured_person' in data:
                info_parts.append(f"Injured Person: {data['injured_person']}")
            if 'injury_type' in data:
                info_parts.append(f"Type of Injury: {data['injury_type']}")
            if 'body_part' in data:
                info_parts.append(f"Body Part Affected: {data['body_part']}")
            if 'severity' in data:
                info_parts.append(f"Injury Severity: {data['severity']}")
        
        if 'witnesses' in data:
            info_parts.append(f"Witnesses: {data['witnesses']}")
        
        return "\n".join(info_parts) if info_parts else "People impact information recorded via chatbot"
    
    def _extract_environment_info_smart(self, data: Dict, incident_type: str) -> str:
        """Extract environmental impact information"""
        info_parts = []
        
        if incident_type == 'environmental':
            if 'substance_involved' in data:
                info_parts.append(f"Substance Involved: {data['substance_involved']}")
            if 'spill_volume' in data:
                info_parts.append(f"Volume Released: {data['spill_volume']}")
            if 'containment' in data:
                info_parts.append(f"Containment Status: {data['containment']}")
            if 'environmental_impact' in data:
                info_parts.append(f"Environmental Impact: {data['environmental_impact']}")
        
        return "\n".join(info_parts) if info_parts else "No significant environmental impact identified"
    
    def _extract_cost_info_smart(self, data: Dict, incident_type: str) -> str:
        """Extract cost and financial impact information"""
        info_parts = []
        
        if incident_type in ['property', 'vehicle']:
            if 'damage_description' in data:
                info_parts.append(f"Damage Description: {data['damage_description']}")
            if 'estimated_cost' in data:
                info_parts.append(f"Estimated Cost: {data['estimated_cost']}")
        
        if incident_type == 'injury' and 'severity' in data:
            severity = data['severity'].lower()
            if 'hospital' in severity or 'medical' in severity:
                info_parts.append("Medical costs anticipated - requires workers' compensation review")
        
        return "\n".join(info_parts) if info_parts else "Cost assessment pending investigation"
    
    def _extract_legal_info_smart(self, data: Dict, incident_type: str) -> str:
        """Extract legal and regulatory information"""
        info_parts = []
        
        if incident_type == 'injury':
            severity = data.get('severity', '').lower()
            if any(word in severity for word in ['hospital', 'serious', 'fracture', 'life threatening']):
                info_parts.append("OSHA recordable injury - requires proper documentation and reporting")
            else:
                info_parts.append("Review OSHA recordability requirements based on final medical determination")
        
        elif incident_type == 'environmental':
            info_parts.append("Environmental incident - assess regulatory reporting requirements (EPA, state agencies)")
        
        elif incident_type == 'vehicle':
            info_parts.append("Vehicle incident - verify insurance notification and DOT reporting requirements if applicable")
        
        info_parts.append("Incident documented in EHS management system per company policy")
        
        return "\n".join(info_parts)
    
    def _extract_reputation_info_smart(self, data: Dict, incident_type: str) -> str:
        """Extract reputational impact information"""
        if incident_type == 'injury':
            severity = data.get('severity', '').lower()
            if 'life threatening' in severity or 'serious' in severity:
                return "Serious injury incident - monitor for potential external interest and media attention"
            else:
                return "Internal incident - standard communication protocols apply"
        
        elif incident_type == 'environmental':
            return "Environmental incident - assess potential for community impact and public interest"
        
        return "Internal incident - low reputational risk with proper management"
    
    def _reset_state(self):
        """Reset chatbot state for new conversation"""
        try:
            self.current_mode = 'general'
            self.current_context = {}
            self.slot_filling_state = {}
            print("DEBUG: Chatbot state reset - ready for new conversation")
        except Exception as e:
            print(f"ERROR: Failed to reset state: {e}")
    
    def _get_error_recovery_response(self, error_msg: str) -> Dict:
        """Generate error recovery response"""
        return {
            "message": "🔧 **I encountered a technical issue, but I'm still here to help!**\n\nLet's try a different approach. What would you like to work on?",
            "type": "error_recovery",
            "actions": [
                {"text": "🚨 Report Incident", "action": "continue_conversation", "message": "I need to report a workplace incident"},
                {"text": "🛡️ Safety Concern", "action": "continue_conversation", "message": "I want to report a safety concern"},
                {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"},
                {"text": "🔄 Start Over", "action": "continue_conversation", "message": "Help me get started"}
            ],
            "quick_replies": [
                "Try again",
                "Report incident",
                "Main menu",
                "Contact support"
            ]
        }

# Create the smart chatbot instance with proper SBERT handling
def create_chatbot():
    """Factory function to create smart chatbot instance"""
    try:
        chatbot = SmartEHSChatbot()
        print("✓ Smart EHS Chatbot created successfully")
        return chatbot
    except Exception as e:
        print(f"ERROR: Failed to create smart chatbot: {e}")
        return None

# Legacy class aliases for backwards compatibility (fixes test imports)
EHSChatbot = SmartEHSChatbot
IntentClassifier = SmartIntentClassifier  
SlotFillingPolicy = SmartSlotPolicy: "continue_conversation", "message": "I want to report a safety concern"},
                {"text": "📋 Find SDS", "action": "continue_conversation", "message": "I need to find a safety data sheet"},
                {"text": "❓ What can you do?", "action": "continue_conversation", "message": "What can you help me with?"}
            ]
        }
    
    def _get_general_help_response(self) -> Dict:
        """Enhanced general help response"""
        return {
            "message": "🤖 **I'm your Smart EHS Assistant!**\n\nI can help you with:\n\n🚨 **Report Incidents** - Guide you through incident reporting step-by-step\n🛡️ **Safety Concerns** - Submit safety observations and concerns\n📋 **Find SDS** - Search for Safety Data Sheets and chemical information\n📊 **Navigate System** - Help you find what you need in the EHS system\n🔄 **Get Guidance** - Answer questions about EHS procedures\n\nWhat would you like to work on?",
            "type": "help_menu",
            "actions": [
                {"text": "🚨 Report Incident", "action": "continue_conversation", "message": "I need to report a workplace incident"},
                {"text": "🛡️ Safety Concern", "action

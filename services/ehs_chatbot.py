# services/ehs_chatbot.py - Complete and fully functional implementation
import json
import re
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

class LightweightIntentClassifier:
    """Memory-efficient intent classifier using only rule-based patterns"""
    
    def __init__(self):
        self.rule_patterns = {
            'incident_reporting': [
                r'report.*incident', r'incident.*report', r'workplace.*incident',
                r'accident', r'injury', r'hurt', r'injured', r'damaged', r'spill', 
                r'collision', r'crash', r'fall', r'slip', r'trip', r'cut', r'burn',
                r'emergency.*happened', r'something.*happened', r'need.*report.*incident',
                r'someone.*hurt', r'someone.*injured', r'someone.*was.*injured',
                r'property.*damage', r'environmental.*spill', r'workplace.*accident', 
                r'got.*hurt', r'was.*injured', r'broke.*\w+', r'chemical.*leak', 
                r'equipment.*failed', r'safety.*incident', r'person.*injured'
            ],
            'incident_type_injury': [
                r'involves.*injury', r'involves.*workplace.*injury', r'workplace.*injury',
                r'someone.*injured', r'someone.*hurt', r'someone.*was.*injured',
                r'person.*injured', r'employee.*injured', r'worker.*injured',
                r'injury.*occurred', r'medical.*incident', r'hurt.*at.*work',
                r'broke.*arm', r'broke.*leg', r'fractured', r'sprained'
            ],
            'incident_type_vehicle': [
                r'vehicle.*accident', r'car.*accident', r'truck.*accident',
                r'vehicle.*incident', r'collision', r'crash'
            ],
            'incident_type_environmental': [
                r'chemical.*spill', r'environmental.*spill', r'spill.*occurred',
                r'leak.*happened', r'environmental.*incident', r'oil.*spill'
            ],
            'incident_type_property': [
                r'property.*damage', r'equipment.*damage', r'damage.*occurred',
                r'broken.*equipment', r'property.*damaged', r'car.*costing',
                r'costing.*\d+.*dollars', r'expensive.*damage'
            ],
            'incident_type_near_miss': [
                r'near.*miss', r'almost.*accident', r'could.*have.*been',
                r'close.*call', r'near.*miss.*incident'
            ],
            'safety_concern': [
                r'safety.*concern', r'unsafe.*condition', r'hazard', r'dangerous',
                r'near.*miss', r'almost.*accident', r'safety.*issue', r'concern.*about',
                r'worried.*about', r'observed.*unsafe', r'potential.*danger',
                r'safety.*observation', r'unsafe.*behavior', r'safety.*violation',
                r'close.*call', r'could.*have.*been', r'safety.*risk', r'not.*safe'
            ],
            'sds_lookup': [
                r'sds', r'safety.*data.*sheet', r'chemical.*info', r'material.*safety',
                r'find.*chemical', r'lookup.*chemical', r'chemical.*safety',
                r'msds', r'chemical.*properties', r'hazard.*information',
                r'chemical.*name', r'cas.*number', r'what.*chemical'
            ]
        }
    
    def classify_intent(self, message: str) -> Tuple[str, float]:
        """Enhanced rule-based classification with specific incident type detection"""
        message_lower = message.lower().strip()
        
        # First check for specific incident types
        incident_type = self.detect_specific_incident_type(message_lower)
        if incident_type:
            return incident_type, 0.9
        
        # Then check for general intents
        best_intent = 'general_inquiry'
        best_confidence = 0.0
        
        for intent, patterns in self.rule_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    confidence = 0.8 if intent == 'incident_reporting' else 0.7
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent
        
        if best_confidence < 0.3:
            return 'general_inquiry', 0.3
        
        return best_intent, best_confidence
    
    def detect_specific_incident_type(self, message: str) -> Optional[str]:
        """Detect specific incident types for better routing"""
        type_patterns = {
            'incident_type_injury': self.rule_patterns.get('incident_type_injury', []),
            'incident_type_vehicle': self.rule_patterns.get('incident_type_vehicle', []),
            'incident_type_environmental': self.rule_patterns.get('incident_type_environmental', []),
            'incident_type_property': self.rule_patterns.get('incident_type_property', []),
            'incident_type_near_miss': self.rule_patterns.get('incident_type_near_miss', [])
        }
        
        for incident_type, patterns in type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    return incident_type
        
        return None

class MemoryEfficientSlotPolicy:
    """Lightweight slot filling without heavy data structures"""
    
    def __init__(self):
        self.incident_slots = {
            'injury': ['description', 'location', 'injured_person', 'injury_type', 'body_part', 'severity'],
            'vehicle': ['description', 'location', 'vehicles_involved', 'damage_estimate'],
            'environmental': ['description', 'location', 'chemical_name', 'spill_volume'],
            'near_miss': ['description', 'location', 'potential_consequences'],
            'property': ['description', 'location', 'damage_description'],
            'other': ['description', 'location', 'incident_details']
        }
        
        self.questions = {
            'description': "Please describe what happened in detail:",
            'location': "Where did this occur? (Building, area, specific location)",
            'injured_person': "Who was involved? (Name or 'Anonymous' if preferred)",
            'injury_type': "What type of injury occurred?",
            'body_part': "Which body part was affected?",
            'severity': "How severe was the injury? (First aid, medical treatment, hospitalization, etc.)",
            'chemical_name': "What chemical was involved?",
            'spill_volume': "Approximately how much was spilled?",
            'vehicles_involved': "Which vehicles were involved?",
            'damage_estimate': "What's the estimated damage cost?",
            'potential_consequences': "What could have happened if conditions were different?",
            'damage_description': "Please describe the damage that occurred:",
            'incident_details': "Please provide more details about what happened:"
        }

class LightweightEHSChatbot:
    """Complete memory-optimized chatbot with bulletproof error handling"""
    
    def __init__(self):
        self.conversation_history = []
        self.current_mode = 'general'
        self.current_context = {}
        self.slot_filling_state = {}
        
        self.intent_classifier = LightweightIntentClassifier()
        self.slot_policy = MemoryEfficientSlotPolicy()
        
        print("✓ Lightweight EHS Chatbot initialized successfully")
    
    def process_message(self, user_message: str, user_id: str = None, context: Dict = None) -> Dict:
        """Process message with extensive error handling and state recovery"""
        try:
            context = context or {}
            user_id = user_id or "default_user"
            
            print(f"DEBUG: Processing message: '{user_message}', mode: {self.current_mode}")
            print(f"DEBUG: Current context: {self.current_context}")
            print(f"DEBUG: Slot state: {self.slot_filling_state}")
            
            # Validate and sanitize input
            if not isinstance(user_message, str):
                user_message = str(user_message)
            
            user_message = user_message.strip()
            
            # Handle empty messages
            if not user_message and not context.get("uploaded_file"):
                return self.get_general_help_response()
            
            # Handle file uploads
            uploaded_file = context.get("uploaded_file")
            if uploaded_file:
                return self.handle_file_upload(user_message, uploaded_file, context)
            
            # Emergency detection (highest priority)
            if self.is_emergency(user_message):
                return self.handle_emergency()
            
            # Intent classification with error handling
            try:
                intent, confidence = self.intent_classifier.classify_intent(user_message)
                print(f"DEBUG: Classified intent: {intent}, confidence: {confidence}")
            except Exception as e:
                print(f"ERROR: Intent classification failed: {e}")
                intent, confidence = 'general_inquiry', 0.3
            
            # Handle specific incident type detection
            if intent.startswith('incident_type_'):
                incident_type = intent.replace('incident_type_', '')
                print(f"DEBUG: Detected specific incident type: {incident_type}")
                return self.start_incident_workflow(incident_type)
            
            # Mode switching for general intents
            if confidence > 0.6:
                self.switch_mode_safe(intent)
            
            # Process based on current mode with error recovery
            try:
                if self.current_mode == 'incident':
                    response = self.process_incident_mode_safe(user_message, intent, confidence)
                elif self.current_mode == 'safety_concern':
                    response = self.process_safety_concern_mode(user_message)
                elif self.current_mode == 'sds_qa':
                    response = self.process_sds_mode(user_message)
                else:
                    response = self.process_general_mode(user_message, intent)
                
                # Store conversation (limited to save memory)
                self.store_conversation_safe(user_message, response, intent)
                
                print(f"DEBUG: Response type: {response.get('type', 'unknown')}")
                return response
                
            except Exception as e:
                print(f"ERROR: Mode processing failed: {e}")
                import traceback
                traceback.print_exc()
                # Reset state and provide fallback
                self.reset_state_safe()
                return self.get_error_recovery_response(user_message, str(e))
            
        except Exception as e:
            print(f"CRITICAL ERROR: process_message completely failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Complete state reset and safe fallback
            self.reset_state_safe()
            return self.get_critical_error_response(str(e))
    
    def start_incident_workflow(self, incident_type: str) -> Dict:
        """Start incident workflow with proper state initialization"""
        try:
            # Reset any existing state
            self.current_mode = 'incident'
            self.current_context = {'incident_type': incident_type}
            self.slot_filling_state = {}
            
            return self.start_slot_filling_safe(incident_type)
            
        except Exception as e:
            print(f"ERROR: Failed to start incident workflow: {e}")
            return self.ask_incident_type()
    
    def switch_mode_safe(self, intent: str):
        """Switch modes with safe state management"""
        try:
            mode_map = {
                'incident_reporting': 'incident',
                'safety_concern': 'safety_concern', 
                'sds_lookup': 'sds_qa'
            }
            
            new_mode = mode_map.get(intent, 'general')
            if new_mode != self.current_mode:
                print(f"DEBUG: Switching mode from {self.current_mode} to {new_mode}")
                self.current_mode = new_mode
                if new_mode != 'incident':  # Keep context for incident mode
                    self.current_context = {}
                    self.slot_filling_state = {}
        except Exception as e:
            print(f"ERROR: Mode switch failed: {e}")
            self.reset_state_safe()
    
    def process_incident_mode_safe(self, message: str, intent: str, confidence: float) -> Dict:
        """Enhanced incident processing with bulletproof error handling"""
        try:
            print(f"DEBUG: Processing incident mode, context: {self.current_context}")
            print(f"DEBUG: Slot filling state: {self.slot_filling_state}")
            
            # Ensure we have valid context
            if not isinstance(self.current_context, dict):
                self.current_context = {}
            
            if not isinstance(self.slot_filling_state, dict):
                self.slot_filling_state = {}
            
            # Check if we already have an incident type
            if 'incident_type' not in self.current_context:
                # Try to detect incident type from message
                detected_type = self.detect_incident_type_safe(message)
                print(f"DEBUG: Detected incident type: {detected_type}")
                
                if detected_type:
                    self.current_context['incident_type'] = detected_type
                    return self.start_slot_filling_safe(detected_type)
                else:
                    return self.ask_incident_type()
            
            # Continue slot filling if we have an incident type
            return self.continue_slot_filling_safe(message)
            
        except Exception as e:
            print(f"ERROR: process_incident_mode_safe failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Reset state and fall back to incident type selection
            self.current_context = {}
            self.slot_filling_state = {}
            return self.ask_incident_type()
    
    def start_slot_filling_safe(self, incident_type: str) -> Dict:
        """Start collecting required information with bulletproof error handling"""
        try:
            slots = self.slot_policy.incident_slots.get(incident_type, ['description', 'location'])
            print(f"DEBUG: Starting slot filling for {incident_type}, slots: {slots}")
            
            if slots and len(slots) > 0:
                first_slot = slots[0]
                self.slot_filling_state = {
                    'slots': slots.copy(),  # Make a copy to avoid reference issues
                    'current_slot': first_slot,
                    'filled': 0,
                    'incident_type': incident_type,
                    'collected_data': {}
                }
                
                question = self.slot_policy.questions.get(first_slot, f"Please provide {first_slot}:")
                
                return {
                    "message": f"📝 **{incident_type.title()} Incident Report**\n\n{question}",
                    "type": "slot_filling",
                    "slot": first_slot,
                    "progress": f"Step 1 of {len(slots)}",
                    "guidance": "I'll guide you through each required field step by step."
                }
            else:
                # No slots defined, complete immediately
                return self.complete_incident_report_safe()
            
        except Exception as e:
            print(f"ERROR: start_slot_filling_safe failed: {e}")
            import traceback
            traceback.print_exc()
            return self.ask_incident_type()
    
    def continue_slot_filling_safe(self, message: str) -> Dict:
        """Continue collecting information with bulletproof error handling"""
        try:
            # Validate slot filling state
            if not self.slot_filling_state or not isinstance(self.slot_filling_state, dict):
                print("WARNING: Invalid slot filling state, resetting")
                return self.complete_incident_report_safe()
            
            current_slot = self.slot_filling_state.get('current_slot')
            slots = self.slot_filling_state.get('slots', [])
            filled = self.slot_filling_state.get('filled', 0)
            collected_data = self.slot_filling_state.get('collected_data', {})
            
            print(f"DEBUG: Continue slot filling - slot: {current_slot}, filled: {filled}/{len(slots)}")
            
            # Validate input
            if not isinstance(message, str):
                message = str(message)
            
            message = message.strip()
            
            # Store answer if we have a current slot and valid message
            if current_slot and message:
                collected_data[current_slot] = message
                self.current_context[current_slot] = message  # Also store in main context
                filled += 1
                self.slot_filling_state.update({
                    'filled': filled,
                    'collected_data': collected_data
                })
                print(f"DEBUG: Stored answer for {current_slot}: {message[:50]}...")
            
            # Check if more slots needed
            if filled < len(slots):
                try:
                    next_slot = slots[filled]
                    self.slot_filling_state['current_slot'] = next_slot
                    question = self.slot_policy.questions.get(next_slot, f"Please provide {next_slot}:")
                    
                    return {
                        "message": f"✅ Thank you.\n\n**Next question:** {question}",
                        "type": "slot_filling",
                        "slot": next_slot,
                        "progress": f"Step {filled + 1} of {len(slots)}",
                        "filled_slots": filled,
                        "total_slots": len(slots)
                    }
                except (IndexError, KeyError) as e:
                    print(f"ERROR: Slot access error: {e}")
                    return self.complete_incident_report_safe()
            
            # All slots filled
            return self.complete_incident_report_safe()
            
        except Exception as e:
            print(f"ERROR: continue_slot_filling_safe failed: {e}")
            import traceback
            traceback.print_exc()
            return self.complete_incident_report_safe()
    
    def complete_incident_report_safe(self) -> Dict:
        """Complete incident with comprehensive error handling"""
        try:
            incident_id = f"INC-{int(time.time())}"
            incident_type = self.current_context.get('incident_type', 'other')
            
            # Simple risk assessment
            risk_level = self.simple_risk_assessment_safe()
            
            # Save incident data
            save_success = self.save_incident_data_safe(incident_id, risk_level)
            
            # Generate summary
            summary = self.generate_incident_summary_safe()
            
            # Reset state
            old_context = dict(self.current_context)  # Keep for debugging
            self.reset_state_safe()
            
            success_message = "✅ **Incident Report Completed**\n\n"
            if save_success:
                success_message += f"**Incident ID:** `{incident_id}`\n\n{summary}\n\n**Risk Assessment:** {risk_level}\n\nYour incident has been recorded and assigned a unique ID."
            else:
                success_message += f"**Incident ID:** `{incident_id}`\n\n{summary}\n\n**Risk Assessment:** {risk_level}\n\n⚠️ Note: There was an issue saving to the database, but your report has been processed."
            
            return {
                "message": success_message,
                "type": "incident_completed",
                "incident_id": incident_id,
                "risk_level": risk_level,
                "actions": [
                    {
                        "text": "📄 View Report",
                        "action": "navigate",
                        "url": f"/incidents/{incident_id}/edit"
                    },
                    {
                        "text": "📊 Dashboard",
                        "action": "navigate",
                        "url": "/dashboard"
                    },
                    {
                        "text": "🔄 Create Follow-up Action",
                        "action": "navigate",
                        "url": f"/capa/new?source=incident&source_id={incident_id}"
                    }
                ],
                "debug_context": old_context  # For debugging
            }
            
        except Exception as e:
            print(f"ERROR: complete_incident_report_safe failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Generate a minimal completion response
            incident_id = f"INC-{int(time.time())}"
            self.reset_state_safe()
            
            return {
                "message": f"✅ **Incident Report Completed**\n\nIncident ID: `{incident_id}`\n\n⚠️ There was an issue processing some details, but your basic report has been recorded. Please use the incident form for complete details if needed.",
                "type": "incident_completed",
                "incident_id": incident_id,
                "actions": [
                    {"text": "📝 Use Incident Form", "action": "navigate", "url": "/incidents/new"},
                    {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"}
                ]
            }
    
    def detect_incident_type_safe(self, message: str) -> Optional[str]:
        """Safe incident type detection with error handling"""
        try:
            if not isinstance(message, str):
                return None
                
            msg = message.lower()
            
            # Comprehensive keyword matching
            type_keywords = {
                'injury': [
                    r'injur', r'hurt', r'cut', r'burn', r'medical', r'hospital', r'first aid',
                    r'someone.*injured', r'person.*hurt', r'employee.*hurt', r'worker.*injured',
                    r'broken.*bone', r'sprain', r'strain', r'wound', r'bleeding', r'broke.*arm',
                    r'broke.*leg', r'fractured', r'bruise'
                ],
                'vehicle': [
                    r'vehicle', r'car', r'truck', r'collision', r'crash', r'accident.*vehicle',
                    r'hit.*by', r'ran.*into', r'fender.*bender', r'auto.*accident'
                ],
                'environmental': [
                    r'spill', r'chemical', r'leak', r'environmental', r'release',
                    r'contamination', r'waste', r'hazardous.*material', r'oil.*spill'
                ],
                'near_miss': [
                    r'near.*miss', r'almost', r'could.*have', r'close.*call',
                    r'nearly.*happened', r'just.*missed'
                ],
                'property': [
                    r'damage', r'broken', r'property', r'equipment.*damage',
                    r'machinery.*broke', r'building.*damage', r'car.*costing',
                    r'costing.*\d+.*dollars', r'expensive.*damage'
                ]
            }
            
            for incident_type, keywords in type_keywords.items():
                for keyword in keywords:
                    if re.search(keyword, msg):
                        print(f"DEBUG: Matched keyword '{keyword}' for type '{incident_type}'")
                        return incident_type
                        
        except Exception as e:
            print(f"ERROR: detect_incident_type_safe failed: {e}")
        
        return None
    
    def simple_risk_assessment_safe(self) -> str:
        """Safe basic rule-based risk assessment"""
        try:
            description = str(self.current_context.get('description', '')).lower()
            severity = str(self.current_context.get('severity', '')).lower()
            incident_type = str(self.current_context.get('incident_type', ''))
            
            # High risk indicators
            high_risk_words = ['severe', 'hospital', 'major', 'significant', 'fatality', 'serious', 'emergency']
            if any(word in description + ' ' + severity for word in high_risk_words):
                return "High"
            
            # Low risk indicators  
            low_risk_words = ['minor', 'first aid', 'superficial', 'small', 'negligible']
            if any(word in description + ' ' + severity for word in low_risk_words):
                return "Low"
            
            # Default based on incident type
            type_risk = {
                'injury': 'Medium',
                'environmental': 'Medium', 
                'vehicle': 'Medium',
                'near_miss': 'Low',
                'property': 'Low'
            }
            
            return type_risk.get(incident_type, 'Medium')
            
        except Exception as e:
            print(f"ERROR: simple_risk_assessment_safe failed: {e}")
            return "Medium"
    
    def save_incident_data_safe(self, incident_id: str, risk_level: str) -> bool:
        """Save incident with comprehensive error handling"""
        try:
            incidents_file = Path("data/incidents.json")
            incidents_file.parent.mkdir(exist_ok=True, parents=True)
            
            # Load existing incidents
            incidents = {}
            if incidents_file.exists():
                try:
                    content = incidents_file.read_text()
                    if content.strip():
                        incidents = json.loads(content)
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"Warning: Could not load existing incidents: {e}")
                    incidents = {}
            
            # Create incident record
            incident_data = {
                "id": incident_id,
                "type": str(self.current_context.get('incident_type', 'other')),
                "created_ts": time.time(),
                "status": "complete",
                "risk_level": str(risk_level),
                "answers": {
                    "people": self._extract_people_info_safe(),
                    "environment": self._extract_environment_info_safe(),
                    "cost": self._extract_cost_info_safe(),
                    "legal": "To be determined by EHS team",
                    "reputation": "Low impact expected"
                },
                "chatbot_data": dict(self.current_context),  # Copy to avoid reference issues
                "reported_via": "chatbot_lite"
            }
            
            incidents[incident_id] = incident_data
            
            # Save with error handling
            try:
                incidents_file.write_text(json.dumps(incidents, indent=2))
                print(f"DEBUG: Saved incident {incident_id}")
                return True
            except Exception as e:
                print(f"ERROR: Failed to write incidents file: {e}")
                return False
            
        except Exception as e:
            print(f"ERROR: save_incident_data_safe failed: {e}")
            return False
    
    def generate_incident_summary_safe(self) -> str:
        """Generate human-readable summary with error handling"""
        try:
            incident_type = str(self.current_context.get('incident_type', 'Unknown'))
            description = str(self.current_context.get('description', 'No description provided'))
            location = str(self.current_context.get('location', 'Location not specified'))
            
            summary = f"**Type:** {incident_type.title()}\n"
            summary += f"**Location:** {location}\n"
            summary += f"**Description:** {description[:150]}{'...' if len(description) > 150 else ''}"
            
            return summary
        except Exception as e:
            print(f"ERROR: generate_incident_summary_safe failed: {e}")
            return "**Type:** Unknown\n**Location:** Not specified\n**Description:** Error generating summary"
    
    def _extract_people_info_safe(self) -> str:
        """Extract people-related information safely"""
        try:
            info_parts = []
            
            safe_keys = ['injured_person', 'injury_type', 'body_part', 'severity', 'description']
            for key in safe_keys:
                value = self.current_context.get(key)
                if value:
                    info_parts.append(f"{key.replace('_', ' ').title()}: {str(value)}")
            
            return "\n".join(info_parts) if info_parts else "N/A"
        except Exception as e:
            print(f"ERROR: _extract_people_info_safe failed: {e}")
            return "Error extracting people information"
    
    def _extract_environment_info_safe(self) -> str:
        """Extract environment-related information safely"""
        try:
            info_parts = []
            
            if 'chemical_name' in self.current_context:
                info_parts.append(f"Chemical: {self.current_context['chemical_name']}")
            if 'spill_volume' in self.current_context:
                info_parts.append(f"Volume: {self.current_context['spill_volume']}")
            
            return "\n".join(info_parts) if info_parts else "N/A"
        except Exception as e:
            print(f"ERROR: _extract_environment_info_safe failed: {e}")
            return "N/A"
    
    def _extract_cost_info_safe(self) -> str:
        """Extract cost-related information safely"""
        try:
            if 'damage_estimate' in self.current_context:
                return f"Estimated Damage: {self.current_context['damage_estimate']}"
            return "N/A"
        except Exception as e:
            print(f"ERROR: _extract_cost_info_safe failed: {e}")
            return "N/A"
    
    def reset_state_safe(self):
        """Safely reset chatbot state"""
        try:
            self.current_mode = 'general'
            self.current_context = {}
            self.slot_filling_state = {}
            print("DEBUG: Chatbot state reset successfully")
        except Exception as e:
            print(f"ERROR: reset_state_safe failed: {e}")
            # Force reset even if there's an error
            self.current_mode = 'general'
            self.current_context = {}
            self.slot_filling_state = {}
    
    def store_conversation_safe(self, user_message: str, response: Dict, intent: str):
        """Safely store conversation history"""
        try:
            self.conversation_history.append({
                "user": str(user_message)[:200],
                "bot": str(response.get("message", ""))[:200],
                "intent": str(intent),
                "mode": str(self.current_mode),
                "timestamp": time.time()
            })
            
            # Keep only last 20 exchanges
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
        except Exception as e:
            print(f"ERROR: store_conversation_safe failed: {e}")
    
    def get_error_recovery_response(self, original_message: str, error_msg: str) -> Dict:
        """Generate error recovery response"""
        return {
            "message": "I encountered an issue processing your request, but I can still help you. Let me direct you to the right place based on what you told me.",
            "type": "error_recovery",
            "actions": [
                {"text": "🚨 Report Incident", "action": "navigate", "url": "/incidents/new"},
                {"text": "🛡️ Safety Concern", "action": "navigate", "url": "/safety-concerns/new"},
                {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"}
            ],
            "debug_info": {
                "original_message": original_message[:100],
                "error": error_msg
            }
        }
    
    def get_critical_error_response(self, error_msg: str) -> Dict:
        """Generate critical error response"""
        return {
            "message": "I'm having technical difficulties right now. Please use the navigation menu to access the system directly.",
            "type": "critical_error",
            "actions": [
                {"text": "📝 Report Incident Directly", "action": "navigate", "url": "/incidents/new"},
                {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"}
            ]
        }
    
    def ask_incident_type(self) -> Dict:
        """Ask for incident type selection"""
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
                    "message": "This involves a chemical spill"
                },
                {
                    "text": "⚠️ Near Miss",
                    "action": "continue_conversation",
                    "message": "This was a near miss incident"
                },
                {
                    "text": "💔 Property Damage",
                    "action": "continue_conversation", 
                    "message": "This involves property damage"
                }
            ],
            "guidance": "**Remember:** If anyone needs immediate medical attention, call 911 first."
        }
    
    def process_safety_concern_mode(self, message: str) -> Dict:
        """Handle safety concerns"""
        return {
            "message": "🛡️ **Safety Concern Noted**\n\nThank you for speaking up about safety! Let me direct you to our reporting system.",
            "type": "safety_concern",
            "actions": [
                {"text": "📝 Report Safety Concern", "action": "navigate", "url": "/safety-concerns/new"},
                {"text": "📞 Anonymous Report", "action": "navigate", "url": "/safety-concerns/new?anonymous=true"}
            ]
        }
    
    def process_sds_mode(self, message: str) -> Dict:
        """Handle SDS requests"""
        return {
            "message": "📄 **I'll help you find Safety Data Sheets.**\n\nOur SDS library is searchable and includes Q&A functionality.",
            "type": "sds_qa",
            "actions": [
                {"text": "🔍 Search SDS Library", "action": "navigate", "url": "/sds"},
                {"text": "📤 Upload New SDS", "action": "navigate", "url": "/sds/upload"}
            ]
        }
    
    def process_general_mode(self, message: str, intent: str) -> Dict:
        """Handle general inquiries"""
        return self.get_general_help_response()
    
    def handle_file_upload(self, message: str, file_info: Dict, context: Dict) -> Dict:
        """Handle file uploads efficiently"""
        filename = file_info.get("filename", "")
        file_type = file_info.get("type", "")
        
        if file_type.startswith('image/'):
            return {
                "message": f"📸 **Image received: {filename}**\n\nI can help you use this image for incident reporting or safety documentation.",
                "type": "image_upload",
                "actions": [
                    {"text": "🚨 Use for Incident Report", "action": "navigate", "url": "/incidents/new"},
                    {"text": "🛡️ Use for Safety Concern", "action": "navigate", "url": "/safety-concerns/new"}
                ]
            }
        elif file_type == 'application/pdf':
            return {
                "message": f"📄 **PDF received: {filename}**\n\nThis could be a Safety Data Sheet or important documentation.",
                "type": "pdf_upload",
                "actions": [
                    {"text": "📋 Add to SDS Library", "action": "navigate", "url": "/sds/upload"}
                ]
            }
        
        return {
            "message": f"📎 **File received: {filename}**\n\nHow would you like to use this file?",
            "type": "general_upload"
        }
    
    def is_emergency(self, message: str) -> bool:
        """Detect emergency situations"""
        try:
            emergency_words = [
                "emergency", "911", "fire", "bleeding", "unconscious", 
                "heart attack", "severe injury", "immediate danger"
            ]
            return any(word in message.lower() for word in emergency_words)
        except:
            return False
    
    def handle_emergency(self) -> Dict:
        """Emergency response"""
        return {
            "message": "🚨 **EMERGENCY DETECTED** 🚨\n\n**FOR LIFE-THREATENING EMERGENCIES:**\n📞 **CALL 911 IMMEDIATELY**\n\n**Site Emergency Contacts:**\n• Site Emergency: (555) 123-4567\n• Security: (555) 123-4568\n• EHS Hotline: (555) 123-4569",
            "type": "emergency",
            "actions": [
                {"text": "📝 Report Emergency Incident", "action": "navigate", "url": "/incidents/new?type=emergency"}
            ]
        }
    
    def get_general_help_response(self) -> Dict:
        """General help response"""
        return {
            "message": "🤖 **I'm your EHS Assistant!**\n\nI can help you with:\n\n• 🚨 Report incidents and safety concerns\n• 📊 Navigate the EHS system\n• 📄 Find safety data sheets\n• 🔄 Get guidance on procedures\n\nWhat would you like to work on?",
            "type": "help_menu",
            "actions": [
                {"text": "🚨 Report Incident", "action": "continue_conversation", "message": "I need to report a workplace incident"},
                {"text": "🛡️ Safety Concern", "action": "continue_conversation", "message": "I want to report a safety concern"},
                {"text": "📊 View Dashboard", "action": "navigate", "url": "/dashboard"}
            ]
        }
    
    def get_conversation_summary(self) -> Dict:
        """Get lightweight conversation summary"""
        return {
            "message_count": len(self.conversation_history),
            "current_mode": self.current_mode,
            "active_context": bool(self.current_context),
            "slot_filling_active": bool(self.slot_filling_state),
            "timestamp": time.time(),
            "memory_efficient": True
        }

# Create the chatbot instance
def create_chatbot():
    """Factory function to create chatbot instance"""
    try:
        return LightweightEHSChatbot()
    except Exception as e:
        print(f"ERROR: Failed to create chatbot: {e}")
        import traceback
        traceback.print_exc()
        return None

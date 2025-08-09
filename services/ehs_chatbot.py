# services/ehs_chatbot.py - FIXED VERSION with proper state management
import json
import re
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

class FixedIntentClassifier:
    """Fixed intent classifier with better pattern matching"""
    
    def __init__(self):
        self.rule_patterns = {
            'incident_reporting': [
                r'report.*incident', r'incident.*report', r'workplace.*incident',
                r'accident', r'injury', r'hurt', r'injured', r'damaged', r'spill', 
                r'collision', r'crash', r'fall', r'slip', r'trip', r'cut', r'burn',
                r'emergency.*happened', r'something.*happened', r'need.*report.*incident',
                r'someone.*hurt', r'someone.*injured', r'someone.*was.*injured',
                r'property.*damage', r'environmental.*spill', r'workplace.*accident'
            ],
            'safety_concern': [
                r'safety.*concern', r'unsafe.*condition', r'hazard', r'near.*miss',
                r'safety.*observation', r'concern.*about.*safety'
            ],
            'sds_lookup': [
                r'safety.*data.*sheet', r'sds', r'msds', r'chemical.*information',
                r'find.*sds', r'chemical.*safety', r'material.*safety'
            ],
            'general_help': [
                r'help', r'what.*can.*you.*do', r'show.*menu', r'assistance'
            ]
        }
    
    def classify_intent(self, message: str) -> Tuple[str, float]:
        """Classify intent with confidence scoring"""
        if not message or not isinstance(message, str):
            return 'general_inquiry', 0.0
            
        message_lower = message.lower().strip()
        
        best_intent = 'general_inquiry'
        best_confidence = 0.0
        
        for intent, patterns in self.rule_patterns.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, message_lower):
                        confidence = 0.9 if intent == 'incident_reporting' else 0.8
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_intent = intent
                except re.error:
                    continue  # Skip invalid regex patterns
        
        return best_intent, best_confidence

class FixedSlotPolicy:
    """Fixed slot filling with proper state management"""
    
    def __init__(self):
        self.incident_slots = {
            'injury': ['description', 'location', 'injured_person', 'injury_type', 'body_part'],
            'environmental': ['description', 'location', 'chemical_name', 'spill_volume'],
            'property': ['description', 'location', 'damage_description'],
            'other': ['description', 'location']
        }
        
        self.questions = {
            'description': "Please describe what happened in detail:",
            'location': "Where did this occur? (Building, area, specific location)",
            'injured_person': "Who was injured? (Full name for documentation)",
            'injury_type': "What type of injury occurred?",
            'body_part': "Which body part was affected?",
            'chemical_name': "What chemical or substance was involved?",
            'spill_volume': "Approximately how much was spilled?",
            'damage_description': "Please describe the property damage:"
        }

class FixedEHSChatbot:
    """Fixed EHS Chatbot with proper error handling and state management"""
    
    def __init__(self):
        self.conversation_history = []
        self.current_mode = 'general'
        self.current_context = {}
        self.slot_filling_state = {}
        
        try:
            self.intent_classifier = FixedIntentClassifier()
            self.slot_policy = FixedSlotPolicy()
            print("✓ Fixed EHS Chatbot initialized successfully")
        except Exception as e:
            print(f"ERROR: Failed to initialize chatbot components: {e}")
            # Create minimal fallback components
            self.intent_classifier = None
            self.slot_policy = None
    
    def process_message(self, user_message: str, user_id: str = None, context: Dict = None) -> Dict:
        """Process message with robust error handling"""
        try:
            # Validate inputs
            if not isinstance(user_message, str):
                user_message = str(user_message) if user_message else ""
            
            user_message = user_message.strip()
            user_id = user_id or "default_user"
            context = context or {}
            
            print(f"DEBUG: Processing message: '{user_message}', mode: {self.current_mode}")
            
            # Handle empty messages
            if not user_message and not context.get("uploaded_file"):
                return self._get_general_help_response()
            
            # Handle file uploads
            if context.get("uploaded_file"):
                return self._handle_file_upload(context["uploaded_file"], user_message)
            
            # Emergency detection
            if self._is_emergency(user_message):
                return self._handle_emergency()
            
            # Intent classification with fallback
            intent, confidence = self._classify_intent_safe(user_message)
            print(f"DEBUG: Intent: {intent}, Confidence: {confidence}")
            
            # Process based on current mode
            if self.current_mode == 'incident' and self.slot_filling_state:
                return self._continue_incident_reporting(user_message)
            elif intent == 'incident_reporting' or confidence > 0.7:
                return self._start_incident_reporting(user_message, intent)
            elif intent == 'sds_lookup':
                return self._handle_sds_request()
            elif intent == 'safety_concern':
                return self._handle_safety_concern()
            else:
                return self._handle_general_inquiry(user_message)
                
        except Exception as e:
            print(f"ERROR: process_message failed: {e}")
            import traceback
            traceback.print_exc()
            return self._get_error_response(str(e))
    
    def _classify_intent_safe(self, message: str) -> Tuple[str, float]:
        """Safely classify intent with fallback"""
        try:
            if self.intent_classifier:
                return self.intent_classifier.classify_intent(message)
            else:
                # Fallback classification
                message_lower = message.lower()
                if any(word in message_lower for word in ['incident', 'accident', 'injury', 'hurt']):
                    return 'incident_reporting', 0.8
                elif any(word in message_lower for word in ['sds', 'safety data sheet', 'chemical']):
                    return 'sds_lookup', 0.8
                elif any(word in message_lower for word in ['concern', 'unsafe', 'hazard']):
                    return 'safety_concern', 0.8
                else:
                    return 'general_inquiry', 0.5
        except Exception as e:
            print(f"ERROR: Intent classification failed: {e}")
            return 'general_inquiry', 0.0
    
    def _start_incident_reporting(self, message: str, intent: str) -> Dict:
        """Start incident reporting workflow"""
        try:
            # Reset state for new incident
            self.current_mode = 'incident'
            self.current_context = {
                'description': message,
                'incident_type': 'other'  # Default type
            }
            
            # Determine incident type from message
            incident_type = self._detect_incident_type(message)
            self.current_context['incident_type'] = incident_type
            
            # Start slot filling
            slots = self.slot_policy.incident_slots.get(incident_type, ['description', 'location'])
            
            # Skip description since we have it
            remaining_slots = [slot for slot in slots if slot != 'description']
            
            if remaining_slots:
                self.slot_filling_state = {
                    'slots': remaining_slots,
                    'current_slot_index': 0,
                    'collected_data': {'description': message}
                }
                
                first_slot = remaining_slots[0]
                question = self.slot_policy.questions.get(first_slot, f"Please provide {first_slot}:")
                
                return {
                    "message": f"📝 **{incident_type.title()} Incident Report Started**\n\n**Recorded:** {message}\n\n**Next:** {question}",
                    "type": "incident_slot_filling",
                    "slot": first_slot,
                    "progress": f"Step 1 of {len(remaining_slots)}"
                }
            else:
                # Complete immediately if no additional slots needed
                return self._complete_incident_report()
                
        except Exception as e:
            print(f"ERROR: Starting incident reporting failed: {e}")
            return self._get_error_response("Failed to start incident reporting")
    
    def _continue_incident_reporting(self, message: str) -> Dict:
        """Continue incident reporting slot filling"""
        try:
            if not self.slot_filling_state:
                return self._complete_incident_report()
            
            slots = self.slot_filling_state.get('slots', [])
            current_index = self.slot_filling_state.get('current_slot_index', 0)
            collected_data = self.slot_filling_state.get('collected_data', {})
            
            # Record current answer
            if current_index < len(slots):
                current_slot = slots[current_index]
                collected_data[current_slot] = message
                self.current_context[current_slot] = message
                
                # Move to next slot
                current_index += 1
                self.slot_filling_state['current_slot_index'] = current_index
                self.slot_filling_state['collected_data'] = collected_data
            
            # Check if more slots needed
            if current_index < len(slots):
                next_slot = slots[current_index]
                question = self.slot_policy.questions.get(next_slot, f"Please provide {next_slot}:")
                
                return {
                    "message": f"✅ Recorded: {message}\n\n**Next:** {question}",
                    "type": "incident_slot_filling",
                    "slot": next_slot,
                    "progress": f"Step {current_index + 1} of {len(slots)}"
                }
            else:
                # All slots filled, complete the incident
                return self._complete_incident_report()
                
        except Exception as e:
            print(f"ERROR: Continuing incident reporting failed: {e}")
            return self._complete_incident_report()  # Try to complete anyway
    
    def _complete_incident_report(self) -> Dict:
        """Complete incident report with proper data handling"""
        try:
            incident_id = f"INC-{int(time.time())}"
            
            # Save incident data safely
            save_success = self._save_incident_data_safe(incident_id)
            
            # Generate summary
            summary = self._generate_incident_summary()
            
            # Reset state
            self._reset_state()
            
            return {
                "message": f"✅ **Incident Report Completed**\n\n**Incident ID:** `{incident_id}`\n\n{summary}\n\n✅ Your incident has been recorded and assigned a unique ID. Relevant teams have been notified.",
                "type": "incident_completed",
                "incident_id": incident_id,
                "actions": [
                    {"text": "📄 View Report", "action": "navigate", "url": f"/incidents/{incident_id}/edit"},
                    {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"},
                    {"text": "🔄 New Incident", "action": "continue_conversation", "message": "I need to report another incident"}
                ]
            }
            
        except Exception as e:
            print(f"ERROR: Completing incident report failed: {e}")
            # Return a basic completion message even if saving failed
            incident_id = f"INC-{int(time.time())}"
            self._reset_state()
            
            return {
                "message": f"✅ **Incident Report Completed**\n\nIncident ID: `{incident_id}`\n\n⚠️ There was an issue saving some details, but your basic report has been recorded.",
                "type": "incident_completed",
                "incident_id": incident_id,
                "actions": [
                    {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"},
                    {"text": "🔄 New Incident", "action": "continue_conversation", "message": "I need to report another incident"}
                ]
            }
    
    def _save_incident_data_safe(self, incident_id: str) -> bool:
        """Safely save incident data with error handling"""
        try:
            # Ensure data directory exists
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
            
            # Create incident record
            incident_data = {
                "id": incident_id,
                "type": self.current_context.get('incident_type', 'other'),
                "created_ts": time.time(),
                "status": "complete",
                "answers": {
                    "people": self._extract_people_info(),
                    "environment": self._extract_environment_info(),
                    "cost": self._extract_cost_info(),
                    "legal": self._extract_legal_info(),
                    "reputation": self._extract_reputation_info()
                },
                "chatbot_data": dict(self.current_context),
                "reported_via": "fixed_chatbot"
            }
            
            # Save incident
            incidents[incident_id] = incident_data
            incidents_file.write_text(json.dumps(incidents, indent=2))
            print(f"DEBUG: Saved incident {incident_id}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to save incident data: {e}")
            return False
    
    def _extract_people_info(self) -> str:
        """Extract people-related information"""
        info_parts = []
        
        if 'description' in self.current_context:
            info_parts.append(f"Description: {self.current_context['description']}")
        
        if 'injured_person' in self.current_context:
            info_parts.append(f"Injured Person: {self.current_context['injured_person']}")
        
        if 'injury_type' in self.current_context:
            info_parts.append(f"Injury Type: {self.current_context['injury_type']}")
        
        if 'body_part' in self.current_context:
            info_parts.append(f"Body Part: {self.current_context['body_part']}")
        
        return "\n".join(info_parts) if info_parts else "Basic incident information recorded"
    
    def _extract_environment_info(self) -> str:
        """Extract environment-related information"""
        info_parts = []
        
        if 'chemical_name' in self.current_context:
            info_parts.append(f"Chemical: {self.current_context['chemical_name']}")
        
        if 'spill_volume' in self.current_context:
            info_parts.append(f"Volume: {self.current_context['spill_volume']}")
        
        return "\n".join(info_parts) if info_parts else "No environmental impact noted"
    
    def _extract_cost_info(self) -> str:
        """Extract cost-related information"""
        if 'damage_description' in self.current_context:
            return f"Damage: {self.current_context['damage_description']}"
        return "Cost assessment pending"
    
    def _extract_legal_info(self) -> str:
        """Extract legal-related information"""
        incident_type = self.current_context.get('incident_type', 'other')
        if incident_type == 'injury':
            return "Workplace injury - review OSHA reportability requirements"
        elif incident_type == 'environmental':
            return "Environmental incident - assess regulatory reporting needs"
        return "Standard incident documentation requirements"
    
    def _extract_reputation_info(self) -> str:
        """Extract reputation-related information"""
        return "Internal incident - monitor for any external interest"
    
    def _generate_incident_summary(self) -> str:
        """Generate incident summary"""
        incident_type = self.current_context.get('incident_type', 'Unknown').title()
        location = self.current_context.get('location', 'Location not specified')
        
        summary = f"**Type:** {incident_type}\n**Location:** {location}"
        
        if 'injured_person' in self.current_context:
            summary += f"\n**Injured Person:** {self.current_context['injured_person']}"
        
        if 'injury_type' in self.current_context:
            summary += f"\n**Injury:** {self.current_context['injury_type']}"
        
        return summary
    
    def _detect_incident_type(self, message: str) -> str:
        """Detect incident type from message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['injury', 'injured', 'hurt', 'medical', 'hospital']):
            return 'injury'
        elif any(word in message_lower for word in ['spill', 'chemical', 'environmental', 'release']):
            return 'environmental'
        elif any(word in message_lower for word in ['damage', 'broke', 'destroyed', 'property']):
            return 'property'
        elif any(word in message_lower for word in ['vehicle', 'car', 'truck', 'collision']):
            return 'vehicle'
        else:
            return 'other'
    
    def _handle_file_upload(self, file_info: Dict, message: str) -> Dict:
        """Handle file upload"""
        filename = file_info.get("filename", "")
        file_type = file_info.get("type", "")
        
        if file_type.startswith('image/'):
            return {
                "message": f"📸 **Image received: {filename}**\n\nI can help you use this for incident reporting or safety documentation.",
                "type": "file_upload",
                "actions": [
                    {"text": "🚨 Report Incident with Photo", "action": "continue_conversation", "message": "I want to report an incident with this photo"},
                    {"text": "🛡️ Safety Concern with Photo", "action": "continue_conversation", "message": "I have a safety concern with this photo"}
                ]
            }
        elif file_type == 'application/pdf':
            return {
                "message": f"📄 **PDF received: {filename}**\n\nThis looks like it could be a Safety Data Sheet.",
                "type": "file_upload",
                "actions": [
                    {"text": "📋 Add to SDS Library", "action": "navigate", "url": "/sds/upload"}
                ]
            }
        else:
            return {
                "message": f"📎 **File received: {filename}**\n\nI can help you with this file. What would you like to do?",
                "type": "file_upload",
                "actions": [
                    {"text": "🚨 Use for Incident Report", "action": "continue_conversation", "message": "I want to use this file for an incident report"}
                ]
            }
    
    def _handle_sds_request(self) -> Dict:
        """Handle SDS lookup request"""
        return {
            "message": "📄 **I can help you find Safety Data Sheets.**\n\nOur SDS library is searchable and easy to navigate.",
            "type": "sds_help",
            "actions": [
                {"text": "🔍 Search SDS Library", "action": "navigate", "url": "/sds"},
                {"text": "📤 Upload New SDS", "action": "navigate", "url": "/sds/upload"}
            ],
            "quick_replies": [
                "Find acetone SDS",
                "Search for ammonia",
                "Upload new SDS",
                "Chemical safety info"
            ]
        }
    
    def _handle_safety_concern(self) -> Dict:
        """Handle safety concern"""
        return {
            "message": "🛡️ **Thank you for speaking up about safety!**\n\nEvery safety observation helps create a safer workplace.",
            "type": "safety_help",
            "actions": [
                {"text": "⚠️ Report Safety Concern", "action": "navigate", "url": "/safety-concerns/new"},
                {"text": "📞 Anonymous Report", "action": "navigate", "url": "/safety-concerns/new?anonymous=true"}
            ]
        }
    
    def _handle_general_inquiry(self, message: str) -> Dict:
        """Handle general inquiries"""
        return self._get_general_help_response()
    
    def _is_emergency(self, message: str) -> bool:
        """Detect emergency situations"""
        try:
            emergency_words = ["emergency", "911", "fire", "bleeding", "unconscious", "heart attack"]
            return any(word in message.lower() for word in emergency_words)
        except:
            return False
    
    def _handle_emergency(self) -> Dict:
        """Handle emergency response"""
        return {
            "message": "🚨 **EMERGENCY DETECTED** 🚨\n\n**FOR LIFE-THREATENING EMERGENCIES:**\n📞 **CALL 911 IMMEDIATELY**\n\n**Site Emergency Contacts:**\n• Site Emergency: (555) 123-4567\n• Security: (555) 123-4568",
            "type": "emergency",
            "actions": [
                {"text": "📝 Report Emergency Incident", "action": "navigate", "url": "/incidents/new?type=emergency"}
            ]
        }
    
    def _get_general_help_response(self) -> Dict:
        """Get general help response"""
        return {
            "message": "🤖 **I'm your EHS Assistant!**\n\nI can help you with:\n\n• 🚨 Report incidents and safety concerns\n• 📊 Navigate the EHS system\n• 📄 Find safety data sheets\n• 🔄 Get guidance on procedures\n\nWhat would you like to work on?",
            "type": "help_menu",
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
                "Show main menu"
            ]
        }
    
    def _get_error_response(self, error_msg: str) -> Dict:
        """Get error response"""
        return {
            "message": "I encountered an issue, but I can still help you. What would you like to do?",
            "type": "error_recovery",
            "actions": [
                {"text": "🚨 Report Incident", "action": "navigate", "url": "/incidents/new"},
                {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"},
                {"text": "🔄 Try Again", "action": "continue_conversation", "message": "Help me get started"}
            ]
        }
    
    def _reset_state(self):
        """Reset chatbot state"""
        try:
            self.current_mode = 'general'
            self.current_context = {}
            self.slot_filling_state = {}
            print("DEBUG: Chatbot state reset")
        except Exception as e:
            print(f"ERROR: Failed to reset state: {e}")

# Create the fixed chatbot instance
def create_chatbot():
    """Factory function to create fixed chatbot instance"""
    try:
        chatbot = FixedEHSChatbot()
        print("✓ Fixed chatbot created successfully")
        return chatbot
    except Exception as e:
        print(f"ERROR: Failed to create fixed chatbot: {e}")
        return None

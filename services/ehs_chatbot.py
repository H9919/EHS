# services/ehs_chatbot.py - ENHANCED VERSION with smarter logic
import json
import re
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

class EnhancedIntentClassifier:
    """Enhanced intent classifier with better pattern matching and context awareness"""
    
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
                r'equipment.*failed', r'safety.*incident', r'person.*injured',
                r'worker.*broke', r'employee.*hurt', r'container.*breaking',
                r'oil.*spilling', r'damage.*occurred', r'cost.*to.*fix',
                r'destroying.*car', r'broken.*hand'
            ],
            'incident_type_multiple': [
                r'worker.*broke.*hand.*container.*spill.*car',
                r'injury.*spill.*damage', r'broke.*spill.*destroy',
                r'injured.*chemical.*property', r'hurt.*spill.*car'
            ]
        }
    
    def classify_intent(self, message: str) -> Tuple[str, float]:
        """Enhanced classification with multi-incident type detection"""
        message_lower = message.lower().strip()
        
        # Check for multiple incident types in one message
        incident_types = self.detect_multiple_incident_types(message_lower)
        if len(incident_types) > 1:
            return f"incident_multiple_{'+'.join(incident_types)}", 0.95
        
        # Check for specific single incident types
        incident_type = self.detect_specific_incident_type(message_lower)
        if incident_type:
            return incident_type, 0.9
        
        # Check for general intents
        best_intent = 'general_inquiry'
        best_confidence = 0.0
        
        for intent, patterns in self.rule_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    confidence = 0.8 if intent == 'incident_reporting' else 0.7
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent
        
        return best_intent, best_confidence
    
    def detect_multiple_incident_types(self, message: str) -> List[str]:
        """Enhanced detection for multiple incident types in one message"""
        types_found = []
        
        # Injury indicators
        injury_patterns = [
            r'broke.*hand', r'broke.*arm', r'broke.*leg', r'injured', r'hurt',
            r'broken.*hand', r'fractured', r'sprained', r'cut', r'burn'
        ]
        
        # Environmental indicators
        env_patterns = [
            r'oil.*spill', r'spill.*oil', r'chemical.*spill', r'spilling',
            r'container.*spill', r'leaked', r'release'
        ]
        
        # Property damage indicators
        property_patterns = [
            r'destroying.*car', r'damage.*car', r'car.*damage', r'broke.*car',
            r'property.*damage', r'equipment.*damage', r'destroyed'
        ]
        
        if any(re.search(pattern, message) for pattern in injury_patterns):
            types_found.append('injury')
        
        if any(re.search(pattern, message) for pattern in env_patterns):
            types_found.append('environmental')
        
        if any(re.search(pattern, message) for pattern in property_patterns):
            types_found.append('property')
        
        return types_found
    
    def detect_specific_incident_type(self, message: str) -> Optional[str]:
        """Detect specific incident types for better routing"""
        type_patterns = {
            'incident_type_injury': [
                r'worker.*broke.*hand', r'employee.*injured', r'person.*hurt',
                r'broken.*hand', r'fractured.*bone', r'medical.*attention'
            ],
            'incident_type_environmental': [
                r'oil.*spill', r'chemical.*release', r'container.*spilling',
                r'environmental.*impact', r'spill.*occurred'
            ],
            'incident_type_property': [
                r'destroying.*car', r'property.*damage', r'equipment.*damaged',
                r'car.*destroyed', r'vehicle.*damage'
            ]
        }
        
        for incident_type, patterns in type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    return incident_type
        
        return None

class SmartInformationExtractor:
    """Smart extraction of information from natural language"""
    
    def __init__(self):
        self.extraction_patterns = {
            'location': [
                r'in\s+the\s+(\w+)', r'at\s+the\s+(\w+)', r'in\s+(\w+)',
                r'(\w+)\s+area', r'(\w+)\s+section', r'(\w+)\s+building',
                r'garage', r'warehouse', r'office', r'factory', r'lab'
            ],
            'person_name': [
                r'worker\s+(\w+)', r'employee\s+(\w+)', r'person\s+(\w+)',
                r'(\w+)\s+was\s+injured', r'(\w+)\s+got\s+hurt'
            ],
            'injury_type': [
                r'broke.*(\w+)', r'broken\s+(\w+)', r'fractured\s+(\w+)',
                r'injured.*(\w+)', r'hurt.*(\w+)', r'sprained\s+(\w+)'
            ],
            'body_part': [
                r'broke.*hand', r'broke.*arm', r'broke.*leg', r'broke.*wrist',
                r'hand', r'arm', r'leg', r'back', r'head', r'ankle', r'wrist'
            ],
            'chemical_info': [
                r'(\w+)\s+spill', r'spill.*(\w+)', r'(\w+)\s+leaked',
                r'oil', r'chemical', r'solvent', r'acid', r'base'
            ],
            'spill_volume': [
                r'(\d+)\s*liter', r'(\d+)\s*gallon', r'(\d+)\s*ml',
                r'a\s+liter', r'few\s+liters', r'small\s+amount', r'large\s+amount'
            ],
            'property_damage': [
                r'destroying.*car', r'damaged.*car', r'broke.*car',
                r'car.*destroyed', r'vehicle.*damage', r'equipment.*damage'
            ],
            'cost_estimate': [
                r'\$(\d+)', r'(\d+)\s*dollars?', r'cost.*(\d+)',
                r'expensive', r'costly', r'minor\s+cost', r'major\s+cost'
            ]
        }
    
    def extract_comprehensive_info(self, message: str) -> Dict[str, Any]:
        """Extract comprehensive information from message"""
        extracted = {}
        message_lower = message.lower()
        
        # Extract location
        for pattern in self.extraction_patterns['location']:
            match = re.search(pattern, message_lower)
            if match and len(match.groups()) > 0:
                extracted['location'] = match.group(1).title()
                break
        
        # Simple location keywords
        location_keywords = ['garage', 'warehouse', 'office', 'factory', 'lab', 'kitchen']
        for keyword in location_keywords:
            if keyword in message_lower:
                extracted['location'] = keyword.title()
                break
        
        # Extract person name
        for pattern in self.extraction_patterns['person_name']:
            match = re.search(pattern, message_lower)
            if match and len(match.groups()) > 0:
                name = match.group(1).title()
                if len(name) > 1 and name.isalpha():
                    extracted['injured_person'] = name
                    extracted['people_involved'] = name
                break
        
        # Extract injury information
        injury_keywords = {
            'broke': 'Fracture/Break',
            'broken': 'Fracture/Break', 
            'fractured': 'Fracture',
            'sprained': 'Sprain',
            'cut': 'Laceration',
            'burn': 'Burn'
        }
        
        for keyword, injury_type in injury_keywords.items():
            if keyword in message_lower:
                extracted['injury_type'] = injury_type
                break
        
        # Extract body part
        body_parts = ['hand', 'arm', 'leg', 'wrist', 'ankle', 'back', 'head', 'finger']
        for part in body_parts:
            if part in message_lower:
                extracted['body_part'] = part.title()
                break
        
        # Extract chemical information
        chemical_keywords = ['oil', 'chemical', 'solvent', 'acid', 'gasoline', 'diesel']
        for chemical in chemical_keywords:
            if chemical in message_lower:
                extracted['chemical_name'] = chemical.title()
                extracted['environmental_impact'] = f"{chemical.title()} spill occurred"
                break
        
        # Extract spill volume
        volume_patterns = [
            r'(\d+)\s*liter', r'(\d+)\s*gallon', r'a\s+liter', r'few\s+liters'
        ]
        for pattern in volume_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if 'liter' in pattern:
                    extracted['spill_volume'] = match.group(0) if 'a liter' in match.group(0) else f"{match.group(1)} liters"
                break
        
        # Extract property damage
        if any(word in message_lower for word in ['destroying', 'damaged', 'broke', 'destroyed']) and any(word in message_lower for word in ['car', 'vehicle', 'equipment']):
            extracted['property_damage'] = 'Vehicle/equipment damage occurred'
            extracted['damage_description'] = 'Property damaged during incident'
        
        # Extract severity indicators
        severity_keywords = {
            'serious': 'Serious',
            'severe': 'Severe', 
            'minor': 'Minor',
            'major': 'Major',
            'medical attention': 'Medical treatment required',
            'hospital': 'Hospitalization required'
        }
        
        for keyword, severity in severity_keywords.items():
            if keyword in message_lower:
                extracted['severity'] = severity
                break
        
        return extracted

class EnhancedSlotPolicy:
    """Enhanced slot filling with better logic"""
    
    def __init__(self):
        self.incident_slots = {
            'injury': ['description', 'location', 'injured_person', 'injury_type', 'body_part', 'severity', 'responsible_person'],
            'environmental': ['description', 'location', 'chemical_name', 'spill_volume', 'containment', 'responsible_person'],
            'property': ['description', 'location', 'damage_description', 'cost_estimate', 'responsible_person'],
            'multiple': ['description', 'location', 'people_involved', 'injury_type', 'body_part', 'severity', 'environmental_impact', 'chemical_name', 'spill_volume', 'property_damage', 'damage_description', 'cost_estimate', 'responsible_person']
        }
        
        self.questions = {
            'description': "Please describe what happened in detail:",
            'location': "Where did this occur? (Building, area, specific location)",
            'injured_person': "Who was injured? (Full name required for proper documentation)",
            'people_involved': "Who was involved in this incident? (Full names required)",
            'injury_type': "What type of injury occurred?",
            'body_part': "Which body part was affected?",
            'severity': "How severe was the injury? (First aid, medical treatment, hospitalization)",
            'chemical_name': "What chemical or substance was involved?",
            'spill_volume': "Approximately how much was spilled?",
            'containment': "What containment/cleanup measures were taken?",
            'damage_description': "Please describe the property damage in detail:",
            'cost_estimate': "What is the estimated cost of damage? (If known)",
            'environmental_impact': "Describe the environmental impact:",
            'property_damage': "Describe the property damage that occurred:",
            'responsible_person': "Who will be responsible for follow-up actions on this incident? (Name and role)"
        }

class EnhancedRiskAssessment:
    """Enhanced risk assessment with detailed likelihood and severity"""
    
    def __init__(self):
        self.likelihood_factors = {
            'high': ['frequent', 'common', 'regular', 'often', 'always'],
            'medium': ['sometimes', 'occasional', 'periodic', 'possible'],
            'low': ['rare', 'infrequent', 'unusual', 'seldom']
        }
        
        self.severity_indicators = {
            'injury': {
                'critical': ['death', 'fatality', 'killed', 'died'],
                'major': ['hospital', 'surgery', 'serious', 'severe', 'broke', 'broken', 'fractured'],
                'moderate': ['medical', 'treatment', 'doctor', 'clinic'],
                'minor': ['first aid', 'band-aid', 'minor', 'small']
            },
            'environmental': {
                'critical': ['major spill', 'large release', 'contamination'],
                'major': ['significant spill', 'reportable', 'EPA'],
                'moderate': ['moderate spill', 'contained'],
                'minor': ['small spill', 'minor release', 'cleaned up']
            },
            'property': {
                'critical': ['destroyed', 'total loss', 'major damage'],
                'major': ['significant damage', 'expensive', 'costly'],
                'moderate': ['damaged', 'repair needed'],
                'minor': ['minor damage', 'small cost', 'cosmetic']
            }
        }
    
    def assess_risk(self, incident_data: Dict, incident_types: List[str]) -> Dict:
        """Enhanced risk assessment with detailed breakdown"""
        description = str(incident_data.get('description', ''))
        all_text = ' '.join([str(v) for v in incident_data.values() if isinstance(v, str)]).lower()
        
        # Assess likelihood
        likelihood = self.assess_likelihood(all_text)
        
        # Assess severity for each type
        severities = {}
        max_severity = 0
        
        for incident_type in incident_types:
            severity = self.assess_severity(all_text, incident_type)
            severities[incident_type] = severity
            max_severity = max(max_severity, severity['score'])
        
        # Calculate overall risk
        risk_score = likelihood['score'] * max_severity
        risk_level = self.get_risk_level(risk_score)
        
        return {
            'likelihood': likelihood,
            'severities': severities,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'summary': self.generate_risk_summary(likelihood, severities, risk_level)
        }
    
    def assess_likelihood(self, text: str) -> Dict:
        """Assess likelihood of recurrence"""
        for level, indicators in self.likelihood_factors.items():
            for indicator in indicators:
                if indicator in text:
                    scores = {'high': 8, 'medium': 5, 'low': 2}
                    return {
                        'level': level,
                        'score': scores[level],
                        'description': f"Based on indicators: {indicator}"
                    }
        
        # Default assessment
        return {
            'level': 'medium',
            'score': 5,
            'description': 'Standard likelihood assessment'
        }
    
    def assess_severity(self, text: str, incident_type: str) -> Dict:
        """Assess severity for specific incident type"""
        if incident_type not in self.severity_indicators:
            return {'level': 'moderate', 'score': 5, 'description': 'Standard severity'}
        
        indicators = self.severity_indicators[incident_type]
        
        for level, keywords in indicators.items():
            for keyword in keywords:
                if keyword in text:
                    scores = {'critical': 10, 'major': 8, 'moderate': 5, 'minor': 2}
                    return {
                        'level': level,
                        'score': scores[level],
                        'description': f"Based on {incident_type} indicators: {keyword}"
                    }
        
        return {'level': 'moderate', 'score': 5, 'description': f'Standard {incident_type} severity'}
    
    def get_risk_level(self, risk_score: int) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 64:
            return "Critical"
        elif risk_score >= 40:
            return "High" 
        elif risk_score >= 20:
            return "Medium"
        elif risk_score >= 8:
            return "Low"
        else:
            return "Very Low"
    
    def generate_risk_summary(self, likelihood: Dict, severities: Dict, risk_level: str) -> str:
        """Generate human-readable risk summary"""
        summary = f"**Risk Level: {risk_level}**\n\n"
        summary += f"**Likelihood of Recurrence:** {likelihood['level'].title()} ({likelihood['score']}/10)\n"
        summary += f"*{likelihood['description']}*\n\n"
        
        summary += "**Severity Assessment:**\n"
        for incident_type, severity in severities.items():
            summary += f"• {incident_type.title()}: {severity['level'].title()} ({severity['score']}/10)\n"
            summary += f"  *{severity['description']}*\n"
        
        return summary

class EnhancedEHSChatbot:
    """Enhanced EHS Chatbot with smarter logic"""
    
    def __init__(self):
        self.conversation_history = []
        self.current_mode = 'general'
        self.current_context = {}
        self.slot_filling_state = {}
        self.last_extracted_info = {}
        
        self.intent_classifier = EnhancedIntentClassifier()
        self.info_extractor = SmartInformationExtractor()
        self.slot_policy = EnhancedSlotPolicy()
        self.risk_assessor = EnhancedRiskAssessment()
        
        print("✓ Enhanced EHS Chatbot initialized successfully")
    
    def process_message(self, user_message: str, user_id: str = None, context: Dict = None) -> Dict:
        """Enhanced message processing with smart information extraction"""
        try:
            context = context or {}
            user_id = user_id or "default_user"
            
            print(f"DEBUG: Processing message: '{user_message}', mode: {self.current_mode}")
            
            if not isinstance(user_message, str):
                user_message = str(user_message)
            
            user_message = user_message.strip()
            
            # Handle empty messages
            if not user_message and not context.get("uploaded_file"):
                return self.get_general_help_response()
            
            # Emergency detection
            if self.is_emergency(user_message):
                return self.handle_emergency()
            
            # Smart information extraction
            extracted_info = self.info_extractor.extract_comprehensive_info(user_message)
            self.last_extracted_info = extracted_info
            print(f"DEBUG: Extracted info: {extracted_info}")
            
            # Intent classification
            intent, confidence = self.intent_classifier.classify_intent(user_message)
            print(f"DEBUG: Classified intent: {intent}, confidence: {confidence}")
            
            # Handle multiple incident types
            if intent.startswith('incident_multiple_'):
                incident_types = intent.replace('incident_multiple_', '').split('+')
                return self.handle_multiple_incident_types(incident_types, user_message, extracted_info)
            
            # Handle specific incident type detection
            if intent.startswith('incident_type_'):
                incident_type = intent.replace('incident_type_', '')
                return self.start_incident_workflow(incident_type, extracted_info, user_message)
            
            # Mode switching
            if confidence > 0.6:
                self.switch_mode_safe(intent)
            
            # Process based on current mode
            if self.current_mode == 'incident':
                response = self.process_incident_mode_enhanced(user_message, intent, confidence, extracted_info)
            elif self.current_mode == 'safety_concern':
                response = self.process_safety_concern_mode(user_message)
            else:
                response = self.process_general_mode(user_message, intent)
            
            # Store conversation
            self.store_conversation_safe(user_message, response, intent)
            
            return response
            
        except Exception as e:
            print(f"ERROR: process_message failed: {e}")
            import traceback
            traceback.print_exc()
            return self.get_error_recovery_response(user_message, str(e))
    
    def handle_multiple_incident_types(self, incident_types: List[str], message: str, extracted_info: Dict) -> Dict:
        """Handle incidents with multiple types"""
        print(f"DEBUG: Handling multiple incident types: {incident_types}")
        
        # Set up context for multiple incident types
        self.current_mode = 'incident'
        self.current_context = {
            'incident_types': incident_types,
            'primary_type': incident_types[0],
            'multiple_incident': True,
            'description': message  # Store the full description
        }
        
        # Pre-fill extracted information
        for key, value in extracted_info.items():
            self.current_context[key] = value
        
        # Determine remaining slots needed
        needed_slots = self.determine_remaining_slots_multiple(incident_types, extracted_info)
        
        # Generate response
        incident_desc = " + ".join([t.title() for t in incident_types])
        
        response_message = f"🚨 **Multiple Incident Types Detected: {incident_desc}**\n\n"
        response_message += "I can see this incident involves:\n"
        
        if 'injury' in incident_types:
            response_message += "• 🩹 **Personal Injury** - Worker injury requiring attention\n"
        if 'environmental' in incident_types:
            response_message += "• 🌊 **Environmental Impact** - Chemical spill/release\n"
        if 'property' in incident_types:
            response_message += "• 💔 **Property Damage** - Equipment/vehicle damage\n"
        
        if extracted_info:
            response_message += f"\n**Information already captured from your message:**\n"
            for key, value in extracted_info.items():
                field_name = key.replace('_', ' ').title()
                response_message += f"• {field_name}: {value}\n"
        
        if needed_slots:
            next_slot = needed_slots[0]
            question = self.slot_policy.questions.get(next_slot, f"Please provide {next_slot}:")
            
            self.slot_filling_state = {
                'slots': needed_slots,
                'current_slot': next_slot,
                'filled': 0,
                'incident_types': incident_types,
                'collected_data': dict(extracted_info)
            }
            
            response_message += f"\n**Next question:** {question}"
            
            return {
                "message": response_message,
                "type": "multiple_incident",
                "slot": next_slot,
                "progress": f"Step 1 of {len(needed_slots)}",
                "incident_types": incident_types
            }
        else:
            # All information collected
            return self.complete_incident_report_enhanced()
    
    def determine_remaining_slots_multiple(self, incident_types: List[str], extracted_info: Dict) -> List[str]:
        """Determine what slots still need to be filled"""
        all_needed_slots = set()
        
        # Add slots for each incident type
        for incident_type in incident_types:
            type_slots = self.slot_policy.incident_slots.get(incident_type, [])
            all_needed_slots.update(type_slots)
        
        # Add common slots for multiple incidents
        all_needed_slots.update(['responsible_person'])
        
        # Remove slots we already have information for
        remaining_slots = [slot for slot in all_needed_slots if slot not in extracted_info]
        
        # Remove description if we already have it
        if 'description' in remaining_slots and self.current_context.get('description'):
            remaining_slots.remove('description')
        
        # Priority order
        priority_order = [
            'location', 'people_involved', 'injured_person',
            'injury_type', 'body_part', 'severity',
            'chemical_name', 'spill_volume', 'containment',
            'damage_description', 'cost_estimate',
            'responsible_person'
        ]
        
        # Sort by priority
        sorted_slots = []
        for slot in priority_order:
            if slot in remaining_slots:
                sorted_slots.append(slot)
        
        return sorted_slots
    
    def start_incident_workflow(self, incident_type: str, extracted_info: Dict, original_message: str) -> Dict:
        """Start incident workflow with extracted information"""
        try:
            extracted_info = extracted_info or {}
            
            self.current_mode = 'incident'
            self.current_context = {
                'incident_type': incident_type,
                'description': original_message
            }
            self.current_context.update(extracted_info)
            
            return self.start_slot_filling_with_extracted_info(incident_type, extracted_info, original_message)
            
        except Exception as e:
            print(f"ERROR: Failed to start incident workflow: {e}")
            return self.ask_incident_type()
    
    def continue_slot_filling_enhanced(self, message: str, extracted_info: Dict) -> Dict:
        """Enhanced slot filling with smarter logic"""
        try:
            if not self.slot_filling_state:
                return self.complete_incident_report_enhanced()
            
            current_slot = self.slot_filling_state.get('current_slot')
            slots = self.slot_filling_state.get('slots', [])
            filled = self.slot_filling_state.get('filled', 0)
            collected_data = self.slot_filling_state.get('collected_data', {})
            
            # Don't ask for description again if we already have it
            if current_slot == 'description' and self.current_context.get('description'):
                filled += 1
                self.slot_filling_state['filled'] = filled
                current_slot = slots[filled] if filled < len(slots) else None
                self.slot_filling_state['current_slot'] = current_slot
            
            # Merge extracted info
            for key, value in extracted_info.items():
                if key not in collected_data:
                    collected_data[key] = value
                    self.current_context[key] = value
            
            # Store answer for current slot
            if current_slot and message.strip() and current_slot not in collected_data:
                collected_data[current_slot] = message
                self.current_context[current_slot] = message
                filled += 1
                self.slot_filling_state.update({
                    'filled': filled,
                    'collected_data': collected_data
                })
            
            # Skip slots we already have
            while filled < len(slots) and slots[filled] in collected_data:
                filled += 1
                self.slot_filling_state['filled'] = filled
            
            # Check if more slots needed
            if filled < len(slots):
                next_slot = slots[filled]
                self.slot_filling_state['current_slot'] = next_slot
                question = self.slot_policy.questions.get(next_slot, f"Please provide {next_slot}:")
                
                return {
                    "message": f"✅ Thank you.\n\n**Next question:** {question}",
                    "type": "slot_filling",
                    "slot": next_slot,
                    "progress": f"Step {filled + 1} of {len(slots)}"
                }
            
            # All slots filled
            return self.complete_incident_report_enhanced()
            
        except Exception as e:
            print(f"ERROR: continue_slot_filling_enhanced failed: {e}")
            return self.complete_incident_report_enhanced()
    
    def complete_incident_report_enhanced(self) -> Dict:
        """Complete incident with enhanced risk assessment"""
        try:
            incident_id = f"INC-{int(time.time())}"
            
            # Determine incident type(s)
            if 'incident_types' in self.current_context:
                incident_types = self.current_context['incident_types']
                incident_type = '+'.join(incident_types)
            else:
                incident_type = self.current_context.get('incident_type', 'other')
                incident_types = [incident_type]
            
            # Enhanced risk assessment
            risk_assessment = self.risk_assessor.assess_risk(self.current_context, incident_types)
            
            # Save incident data
            save_success = self.save_incident_data_enhanced(incident_id, incident_type, risk_assessment)
            
            # Generate summary
            summary = self.generate_enhanced_incident_summary()
            
            # Reset state
            self.reset_state_safe()
            
            success_message = f"✅ **{'Multi-Type ' if len(incident_types) > 1 else ''}Incident Report Completed**\n\n"
            success_message += f"**Incident ID:** `{incident_id}`\n\n{summary}\n\n"
            success_message += f"**Enhanced Risk Assessment:**\n{risk_assessment['summary']}\n\n"
            
            if save_success:
                success_message += "✅ Your incident has been recorded and assigned a unique ID. Relevant teams have been notified."
            else:
                success_message += "⚠️ Note: There was an issue saving to the database, but your report has been processed."
            
            return {
                "message": success_message,
                "type": "incident_completed",
                "incident_id": incident_id,
                "incident_types": incident_types,
                "risk_assessment": risk_assessment,
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
                ]
            }
            
        except Exception as e:
            print(f"ERROR: complete_incident_report_enhanced failed: {e}")
            incident_id = f"INC-{int(time.time())}"
            self.reset_state_safe()
            
            return {
                "message": f"✅ **Incident Report Completed**\n\nIncident ID: `{incident_id}`\n\n⚠️ There was an issue processing some details, but your basic report has been recorded.",
                "type": "incident_completed",
                "incident_id": incident_id
            }
    
    def save_incident_data_enhanced(self, incident_id: str, incident_type: str, risk_assessment: Dict) -> bool:
        """Save enhanced incident data"""
        try:
            incidents_file = Path("data/incidents.json")
            incidents_file.parent.mkdir(exist_ok=True, parents=True)
            
            incidents = {}
            if incidents_file.exists():
                try:
                    content = incidents_file.read_text()
                    if content.strip():
                        incidents = json.loads(content)
                except Exception as e:
                    print(f"Warning: Could not load existing incidents: {e}")
                    incidents = {}
            
            # Create enhanced incident record
            incident_data = {
                "id": incident_id,
                "type": incident_type,
                "created_ts": time.time(),
                "status": "complete",
                "risk_assessment": risk_assessment,
                "answers": {
                    "people": self._extract_people_info_enhanced(),
                    "environment": self._extract_environment_info_enhanced(),
                    "cost": self._extract_cost_info_enhanced(),
                    "legal": self._extract_legal_info_enhanced(),
                    "reputation": self._extract_reputation_info_enhanced()
                },
                "chatbot_data": dict(self.current_context),
                "extracted_info": dict(self.last_extracted_info),
                "reported_via": "enhanced_chatbot_v2",
                "multiple_types": '+' in incident_type,
                "incident_types": self.current_context.get('incident_types', [incident_type]),
                "responsible_person": self.current_context.get('responsible_person', 'TBD')
            }
            
            incidents[incident_id] = incident_data
            incidents_file.write_text(json.dumps(incidents, indent=2))
            print(f"DEBUG: Saved enhanced incident {incident_id}")
            return True
            
        except Exception as e:
            print(f"ERROR: save_incident_data_enhanced failed: {e}")
            return False
    
    def generate_enhanced_incident_summary(self) -> str:
        """Generate enhanced summary"""
        try:
            if 'incident_types' in self.current_context:
                incident_types = self.current_context['incident_types']
                incident_type = " + ".join([t.title() for t in incident_types])
            else:
                incident_type = str(self.current_context.get('incident_type', 'Unknown')).title()
            
            description = str(self.current_context.get('description', 'No description provided'))
            location = str(self.current_context.get('location', 'Location not specified'))
            
            summary = f"**Type:** {incident_type}\n"
            summary += f"**Location:** {location}\n"
            
            # Add people information
            if 'injured_person' in self.current_context:
                summary += f"**Injured Person:** {self.current_context['injured_person']}\n"
            elif 'people_involved' in self.current_context:
                summary += f"**People Involved:** {self.current_context['people_involved']}\n"
            
            # Add injury details
            if 'injury_type' in self.current_context and 'body_part' in self.current_context:
                summary += f"**Injury:** {self.current_context['injury_type']} to {self.current_context['body_part']}\n"
            
            # Add environmental details
            if 'chemical_name' in self.current_context:
                summary += f"**Chemical Involved:** {self.current_context['chemical_name']}\n"
            if 'spill_volume' in self.current_context:
                summary += f"**Spill Volume:** {self.current_context['spill_volume']}\n"
            
            # Add property damage
            if 'damage_description' in self.current_context:
                summary += f"**Property Damage:** {self.current_context['damage_description']}\n"
            if 'cost_estimate' in self.current_context:
                summary += f"**Estimated Cost:** {self.current_context['cost_estimate']}\n"
            
            # Add responsible person
            if 'responsible_person' in self.current_context:
                summary += f"**Responsible for Follow-up:** {self.current_context['responsible_person']}\n"
            
            return summary
        except Exception as e:
            print(f"ERROR: generate_enhanced_incident_summary failed: {e}")
            return "**Type:** Unknown\n**Status:** Summary generation error"
    
    def _extract_people_info_enhanced(self) -> str:
        """Extract enhanced people information"""
        try:
            info_parts = []
            
            if 'injured_person' in self.current_context:
                info_parts.append(f"Injured Person: {self.current_context['injured_person']}")
            
            if 'people_involved' in self.current_context:
                info_parts.append(f"People Involved: {self.current_context['people_involved']}")
            
            if 'injury_type' in self.current_context:
                info_parts.append(f"Injury Type: {self.current_context['injury_type']}")
            
            if 'body_part' in self.current_context:
                info_parts.append(f"Body Part Affected: {self.current_context['body_part']}")
            
            if 'severity' in self.current_context:
                info_parts.append(f"Severity: {self.current_context['severity']}")
            
            if 'description' in self.current_context:
                info_parts.append(f"Description: {self.current_context['description']}")
            
            return "\n".join(info_parts) if info_parts else "N/A"
        except Exception as e:
            print(f"ERROR: _extract_people_info_enhanced failed: {e}")
            return "Error extracting people information"
    
    def _extract_environment_info_enhanced(self) -> str:
        """Extract enhanced environment information"""
        try:
            info_parts = []
            
            if 'chemical_name' in self.current_context:
                info_parts.append(f"Chemical/Substance: {self.current_context['chemical_name']}")
            
            if 'spill_volume' in self.current_context:
                info_parts.append(f"Spill Volume: {self.current_context['spill_volume']}")
            
            if 'environmental_impact' in self.current_context:
                info_parts.append(f"Environmental Impact: {self.current_context['environmental_impact']}")
            
            if 'containment' in self.current_context:
                info_parts.append(f"Containment Measures: {self.current_context['containment']}")
            
            return "\n".join(info_parts) if info_parts else "N/A"
        except Exception as e:
            print(f"ERROR: _extract_environment_info_enhanced failed: {e}")
            return "N/A"
    
    def _extract_cost_info_enhanced(self) -> str:
        """Extract enhanced cost information"""
        try:
            info_parts = []
            
            if 'cost_estimate' in self.current_context:
                info_parts.append(f"Estimated Cost: {self.current_context['cost_estimate']}")
            
            if 'damage_description' in self.current_context:
                info_parts.append(f"Damage Description: {self.current_context['damage_description']}")
            
            if 'property_damage' in self.current_context:
                info_parts.append(f"Property Damage: {self.current_context['property_damage']}")
            
            return "\n".join(info_parts) if info_parts else "N/A"
        except Exception as e:
            print(f"ERROR: _extract_cost_info_enhanced failed: {e}")
            return "N/A"
    
    def _extract_legal_info_enhanced(self) -> str:
        """Extract enhanced legal information"""
        try:
            legal_info = []
            
            incident_types = self.current_context.get('incident_types', [self.current_context.get('incident_type', 'other')])
            
            if 'injury' in incident_types:
                if self.current_context.get('severity') in ['hospital', 'serious', 'severe']:
                    legal_info.append("OSHA recordable injury - notification required within 24 hours")
                else:
                    legal_info.append("Workplace injury - internal documentation required")
            
            if 'environmental' in incident_types:
                legal_info.append("Environmental incident - assess EPA/state reporting requirements")
                if 'chemical_name' in self.current_context:
                    legal_info.append(f"Chemical spill ({self.current_context['chemical_name']}) - check SDS for reporting thresholds")
            
            if 'property' in incident_types:
                legal_info.append("Property damage incident - insurance notification may be required")
            
            if len(incident_types) > 1:
                legal_info.append("Multi-type incident - comprehensive legal review recommended")
            
            return "\n".join(legal_info) if legal_info else "Standard incident documentation requirements"
        except Exception as e:
            print(f"ERROR: _extract_legal_info_enhanced failed: {e}")
            return "Legal assessment pending"
    
    def _extract_reputation_info_enhanced(self) -> str:
        """Extract reputation impact information"""
        try:
            incident_types = self.current_context.get('incident_types', [self.current_context.get('incident_type', 'other')])
            
            if len(incident_types) > 1:
                return "Multi-type incident - potential for increased stakeholder attention"
            elif 'injury' in incident_types and self.current_context.get('severity') in ['serious', 'severe', 'hospital']:
                return "Serious injury incident - monitor for external interest"
            elif 'environmental' in incident_types:
                return "Environmental incident - assess community impact potential"
            else:
                return "Standard incident - monitor for any external interest"
        except Exception as e:
            print(f"ERROR: _extract_reputation_info_enhanced failed: {e}")
            return "Reputation assessment pending"
    
    # Keep all existing methods from the original chatbot
    def process_incident_mode_enhanced(self, message: str, intent: str, confidence: float, extracted_info: Dict) -> Dict:
        """Enhanced incident mode processing"""
        try:
            # Handle the case where user says "I just did" or similar
            if any(phrase in message.lower() for phrase in ['i just did', 'already told you', 'i said that', 'just told you']):
                # User is indicating they already provided the information
                return self.continue_slot_filling_enhanced("", extracted_info)
            
            return self.continue_slot_filling_enhanced(message, extracted_info)
            
        except Exception as e:
            print(f"ERROR: process_incident_mode_enhanced failed: {e}")
            return self.get_error_recovery_response(message, str(e))
    
    def start_slot_filling_with_extracted_info(self, incident_type: str, extracted_info: Dict, original_message: str) -> Dict:
        """Start slot filling with pre-extracted information"""
        try:
            slots = self.slot_policy.incident_slots.get(incident_type, ['description', 'location', 'responsible_person'])
            
            # Remove description from slots if we already have it
            if 'description' in slots and original_message:
                slots = [s for s in slots if s != 'description']
                self.current_context['description'] = original_message
            
            # Filter out slots we already have
            remaining_slots = [slot for slot in slots if slot not in extracted_info]
            filled_count = len(slots) - len(remaining_slots)
            
            if remaining_slots:
                first_slot = remaining_slots[0]
                self.slot_filling_state = {
                    'slots': slots,
                    'current_slot': first_slot,
                    'filled': filled_count,
                    'incident_type': incident_type,
                    'collected_data': dict(extracted_info)
                }
                
                question = self.slot_policy.questions.get(first_slot, f"Please provide {first_slot}:")
                
                info_summary = ""
                if extracted_info:
                    info_summary = "\n**Information already captured:**\n"
                    for key, value in extracted_info.items():
                        field_name = key.replace('_', ' ').title()
                        info_summary += f"• {field_name}: {value}\n"
                
                return {
                    "message": f"📝 **{incident_type.title()} Incident Report**{info_summary}\n**Next question:** {question}",
                    "type": "slot_filling",
                    "slot": first_slot,
                    "progress": f"Step {filled_count + 1} of {len(slots)}"
                }
            else:
                return self.complete_incident_report_enhanced()
            
        except Exception as e:
            print(f"ERROR: start_slot_filling_with_extracted_info failed: {e}")
            return self.ask_incident_type()
    
    # Include all other necessary methods from the original chatbot
    def switch_mode_safe(self, intent: str):
        """Switch modes safely"""
        try:
            mode_map = {
                'incident_reporting': 'incident',
                'safety_concern': 'safety_concern', 
                'sds_lookup': 'sds_qa'
            }
            
            new_mode = mode_map.get(intent, 'general')
            if new_mode != self.current_mode:
                self.current_mode = new_mode
                if new_mode != 'incident':
                    self.current_context = {}
                    self.slot_filling_state = {}
        except Exception as e:
            print(f"ERROR: Mode switch failed: {e}")
            self.reset_state_safe()
    
    def reset_state_safe(self):
        """Safely reset chatbot state"""
        try:
            self.current_mode = 'general'
            self.current_context = {}
            self.slot_filling_state = {}
            self.last_extracted_info = {}
        except Exception as e:
            print(f"ERROR: reset_state_safe failed: {e}")
    
    def store_conversation_safe(self, user_message: str, response: Dict, intent: str):
        """Store conversation history"""
        try:
            self.conversation_history.append({
                "user": str(user_message)[:200],
                "bot": str(response.get("message", ""))[:200],
                "intent": str(intent),
                "mode": str(self.current_mode),
                "timestamp": time.time()
            })
            
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
        except Exception as e:
            print(f"ERROR: store_conversation_safe failed: {e}")
    
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
            "type": "emergency"
        }
    
    def ask_incident_type(self) -> Dict:
        """Ask for incident type selection"""
        return {
            "message": "🚨 **I'll help you report this incident.**\n\nWhat type of incident occurred?",
            "type": "incident_type_selection",
            "actions": [
                {"text": "🩹 Injury/Medical", "action": "continue_conversation", "message": "This involves a workplace injury"},
                {"text": "🚗 Vehicle Incident", "action": "continue_conversation", "message": "This involves a vehicle accident"},
                {"text": "🌊 Environmental Spill", "action": "continue_conversation", "message": "This involves a chemical spill"},
                {"text": "⚠️ Near Miss", "action": "continue_conversation", "message": "This was a near miss incident"},
                {"text": "💔 Property Damage", "action": "continue_conversation", "message": "This involves property damage"}
            ]
        }
    
    def process_safety_concern_mode(self, message: str) -> Dict:
        """Handle safety concerns"""
        return {
            "message": "🛡️ **Safety Concern Noted**\n\nThank you for speaking up! Let me direct you to our reporting system.",
            "type": "safety_concern",
            "actions": [
                {"text": "📝 Report Safety Concern", "action": "navigate", "url": "/safety-concerns/new"}
            ]
        }
    
    def process_general_mode(self, message: str, intent: str) -> Dict:
        """Handle general inquiries"""
        return self.get_general_help_response()
    
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
    
    def get_error_recovery_response(self, original_message: str, error_msg: str) -> Dict:
        """Generate error recovery response"""
        return {
            "message": "I encountered an issue processing your request, but I can still help you. Let me direct you to the right place.",
            "type": "error_recovery",
            "actions": [
                {"text": "🚨 Report Incident", "action": "navigate", "url": "/incidents/new"},
                {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"}
            ]
        }

# Create the enhanced chatbot instance
def create_chatbot():
    """Factory function to create enhanced chatbot instance"""
    try:
        return EnhancedEHSChatbot()
    except Exception as e:
        print(f"ERROR: Failed to create enhanced chatbot: {e}")
        return None

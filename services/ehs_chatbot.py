# services/ehs_chatbot.py - FIXED VERSION with enhanced logic
import json
import re
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

class LightweightIntentClassifier:
    """Enhanced intent classifier with better pattern matching"""
    
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
                r'oil.*spilling', r'damage.*occurred', r'cost.*to.*fix'
            ],
            'incident_type_injury': [
                r'involves.*injury', r'involves.*workplace.*injury', r'workplace.*injury',
                r'someone.*injured', r'someone.*hurt', r'someone.*was.*injured',
                r'person.*injured', r'employee.*injured', r'worker.*injured',
                r'injury.*occurred', r'medical.*incident', r'hurt.*at.*work',
                r'broke.*arm', r'broke.*leg', r'fractured', r'sprained',
                r'worker.*broke.*arm', r'employee.*broke'
            ],
            'incident_type_environmental': [
                r'spill.*oil', r'oil.*spill', r'chemical.*spill', r'environmental.*spill',
                r'spill.*occurred', r'leak.*happened', r'environmental.*incident',
                r'container.*spilling', r'oil.*all.*over'
            ],
            'incident_type_property': [
                r'property.*damage', r'equipment.*damage', r'damage.*occurred',
                r'broken.*equipment', r'property.*damaged', r'car.*damage',
                r'breaking.*car', r'cost.*to.*fix', r'dollars.*cost',
                r'expensive.*damage', r'\$?\d+.*damage', r'\d+.*dollar'
            ],
            'safety_concern': [
                r'safety.*concern', r'unsafe.*condition', r'hazard', r'dangerous',
                r'near.*miss', r'almost.*accident', r'safety.*issue', r'concern.*about',
                r'worried.*about', r'observed.*unsafe', r'potential.*danger'
            ],
            'sds_lookup': [
                r'sds', r'safety.*data.*sheet', r'chemical.*info', r'material.*safety',
                r'find.*chemical', r'lookup.*chemical', r'chemical.*safety'
            ]
        }
    
    def classify_intent(self, message: str) -> Tuple[str, float]:
        """Enhanced classification with multi-incident type detection"""
        message_lower = message.lower().strip()
        
        # First check for specific incident types in complex scenarios
        incident_types = self.detect_multiple_incident_types(message_lower)
        if incident_types:
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
        """Detect when message contains multiple incident types"""
        types_found = []
        
        # Check for injury + environmental + property damage pattern
        if (re.search(r'worker.*broke.*arm', message) and 
            re.search(r'spill.*oil', message) and 
            re.search(r'damage.*car|car.*damage|\d+.*dollar', message)):
            return ['injury', 'environmental', 'property']
        
        # Check individual types
        type_patterns = {
            'injury': self.rule_patterns.get('incident_type_injury', []),
            'environmental': self.rule_patterns.get('incident_type_environmental', []),
            'property': self.rule_patterns.get('incident_type_property', [])
        }
        
        for incident_type, patterns in type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    if incident_type not in types_found:
                        types_found.append(incident_type)
                    break
        
        return types_found if len(types_found) > 1 else []
    
    def detect_specific_incident_type(self, message: str) -> Optional[str]:
        """Detect specific incident types for better routing"""
        type_patterns = {
            'incident_type_injury': self.rule_patterns.get('incident_type_injury', []),
            'incident_type_environmental': self.rule_patterns.get('incident_type_environmental', []),
            'incident_type_property': self.rule_patterns.get('incident_type_property', [])
        }
        
        for incident_type, patterns in type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    return incident_type
        
        return None

class MemoryEfficientSlotPolicy:
    """Enhanced slot filling with better data extraction"""
    
    def __init__(self):
        self.incident_slots = {
            'injury': ['description', 'location', 'injured_person', 'injury_type', 'body_part', 'severity'],
            'environmental': ['description', 'location', 'chemical_name', 'spill_volume', 'containment'],
            'property': ['description', 'location', 'damage_description', 'cost_estimate'],
            'multiple': ['description', 'location', 'people_involved', 'environmental_impact', 'property_damage', 'cost_estimate'],
            'other': ['description', 'location', 'incident_details']
        }
        
        self.questions = {
            'description': "Please describe what happened in detail:",
            'location': "Where did this occur? (Building, area, specific location)",
            'injured_person': "Who was involved? (Name or 'Anonymous' if preferred)",
            'injury_type': "What type of injury occurred?",
            'body_part': "Which body part was affected?",
            'severity': "How severe was the injury? (First aid, medical treatment, hospitalization)",
            'chemical_name': "What chemical or substance was involved?",
            'spill_volume': "Approximately how much was spilled?",
            'containment': "What containment measures were taken?",
            'damage_description': "Please describe the property damage:",
            'cost_estimate': "What is the estimated cost of damage?",
            'people_involved': "Who was involved in this incident?",
            'environmental_impact': "Describe any environmental impact (spills, releases):",
            'property_damage': "Describe any property damage that occurred:",
            'incident_details': "Please provide more details about what happened:"
        }
    
    def extract_info_from_message(self, message: str) -> Dict[str, str]:
        """Extract information from user messages intelligently"""
        extracted = {}
        message_lower = message.lower()
        
        # Extract location information
        location_patterns = [
            r'in\s+the\s+(\w+)', r'at\s+(\w+)', r'near\s+(\w+)',
            r'(\w+)\s+area', r'(\w+)\s+section', r'(\w+)\s+building'
        ]
        for pattern in location_patterns:
            match = re.search(pattern, message_lower)
            if match:
                extracted['location'] = match.group(1).title()
                break
        
        # Extract cost information
        cost_patterns = [
            r'\$?(\d+,?\d*)\s*dollars?', r'(\d+,?\d*)\s*\$',
            r'cost.*(\d+,?\d*)', r'(\d+,?\d*)\s*cost'
        ]
        for pattern in cost_patterns:
            match = re.search(pattern, message)
            if match:
                extracted['cost_estimate'] = f"${match.group(1)}"
                break
        
        # Extract injury information
        injury_patterns = [
            r'broke.*(\w+)', r'fractured.*(\w+)', r'injured.*(\w+)',
            r'(\w+).*broken', r'(\w+).*fractured'
        ]
        for pattern in injury_patterns:
            match = re.search(pattern, message_lower)
            if match:
                body_part = match.group(1)
                if body_part in ['arm', 'leg', 'wrist', 'ankle', 'back', 'head']:
                    extracted['body_part'] = body_part.title()
                    extracted['injury_type'] = 'Fracture/Break'
                break
        
        # Extract environmental information
        if re.search(r'spill.*oil|oil.*spill', message_lower):
            extracted['chemical_name'] = 'Oil'
            extracted['environmental_impact'] = 'Oil spill occurred'
        
        # Extract property damage
        if re.search(r'broke.*car|car.*damage|breaking.*car', message_lower):
            extracted['property_damage'] = 'Vehicle damage'
            extracted['damage_description'] = 'Car damaged during incident'
        
        return extracted

class LightweightEHSChatbot:
    """Enhanced chatbot with smarter processing and error recovery"""
    
    def __init__(self):
        self.conversation_history = []
        self.current_mode = 'general'
        self.current_context = {}
        self.slot_filling_state = {}
        self.last_extracted_info = {}
        
        self.intent_classifier = LightweightIntentClassifier()
        self.slot_policy = MemoryEfficientSlotPolicy()
        
        print("✓ Enhanced EHS Chatbot initialized successfully")
    
    def process_message(self, user_message: str, user_id: str = None, context: Dict = None) -> Dict:
        """Enhanced message processing with smart information extraction"""
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
            
            # Extract information from message
            extracted_info = self.slot_policy.extract_info_from_message(user_message)
            self.last_extracted_info = extracted_info
            print(f"DEBUG: Extracted info: {extracted_info}")
            
            # Intent classification with error handling
            try:
                intent, confidence = self.intent_classifier.classify_intent(user_message)
                print(f"DEBUG: Classified intent: {intent}, confidence: {confidence}")
            except Exception as e:
                print(f"ERROR: Intent classification failed: {e}")
                intent, confidence = 'general_inquiry', 0.3
            
            # Handle multiple incident types
            if intent.startswith('incident_multiple_'):
                incident_types = intent.replace('incident_multiple_', '').split('+')
                return self.handle_multiple_incident_types(incident_types, user_message, extracted_info)
            
            # Handle specific incident type detection
            if intent.startswith('incident_type_'):
                incident_type = intent.replace('incident_type_', '')
                print(f"DEBUG: Detected specific incident type: {incident_type}")
                return self.start_incident_workflow(incident_type, extracted_info)
            
            # Mode switching for general intents
            if confidence > 0.6:
                self.switch_mode_safe(intent)
            
            # Process based on current mode with enhanced logic
            try:
                if self.current_mode == 'incident':
                    response = self.process_incident_mode_enhanced(user_message, intent, confidence, extracted_info)
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
    
    def handle_multiple_incident_types(self, incident_types: List[str], message: str, extracted_info: Dict) -> Dict:
        """Handle incidents with multiple types (injury + environmental + property)"""
        print(f"DEBUG: Handling multiple incident types: {incident_types}")
        
        # Set up context for multiple incident types
        self.current_mode = 'incident'
        self.current_context = {
            'incident_types': incident_types,
            'primary_type': incident_types[0],
            'multiple_incident': True
        }
        
        # Pre-fill extracted information
        for key, value in extracted_info.items():
            self.current_context[key] = value
        
        # Generate comprehensive response
        incident_desc = " + ".join([t.title() for t in incident_types])
        
        response_message = f"🚨 **Multiple Incident Types Detected: {incident_desc}**\n\n"
        response_message += "I can see this incident involves:\n"
        
        if 'injury' in incident_types:
            response_message += "• 🩹 **Personal Injury** - Worker injury requiring medical attention\n"
        if 'environmental' in incident_types:
            response_message += "• 🌊 **Environmental Impact** - Spill or chemical release\n"
        if 'property' in incident_types:
            response_message += "• 💔 **Property Damage** - Equipment or vehicle damage\n"
        
        response_message += f"\n**Information already captured:**\n"
        
        # Show what we've already extracted
        if extracted_info:
            for key, value in extracted_info.items():
                field_name = key.replace('_', ' ').title()
                response_message += f"• {field_name}: {value}\n"
        
        # Determine what still needs to be collected
        needed_slots = self.determine_remaining_slots_multiple(incident_types, extracted_info)
        
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
                "incident_types": incident_types,
                "guidance": "This is a complex incident with multiple impacts. I'll guide you through each required field."
            }
        else:
            # All information collected
            return self.complete_incident_report_safe()
    
    def determine_remaining_slots_multiple(self, incident_types: List[str], extracted_info: Dict) -> List[str]:
        """Determine what slots still need to be filled for multiple incident types"""
        all_needed_slots = set()
        
        # Add slots for each incident type
        for incident_type in incident_types:
            type_slots = self.slot_policy.incident_slots.get(incident_type, [])
            all_needed_slots.update(type_slots)
        
        # Add additional slots for multiple incidents
        if len(incident_types) > 1:
            all_needed_slots.update(['people_involved', 'environmental_impact', 'property_damage'])
        
        # Remove slots we already have information for
        remaining_slots = [slot for slot in all_needed_slots if slot not in extracted_info]
        
        # Prioritize critical slots
        priority_order = [
            'description', 'location', 'injured_person', 'people_involved',
            'injury_type', 'body_part', 'severity',
            'environmental_impact', 'chemical_name', 'spill_volume',
            'property_damage', 'damage_description', 'cost_estimate'
        ]
        
        # Sort remaining slots by priority
        sorted_slots = []
        for slot in priority_order:
            if slot in remaining_slots:
                sorted_slots.append(slot)
        
        # Add any remaining slots not in priority list
        for slot in remaining_slots:
            if slot not in sorted_slots:
                sorted_slots.append(slot)
        
        return sorted_slots
    
    def process_incident_mode_enhanced(self, message: str, intent: str, confidence: float, extracted_info: Dict) -> Dict:
        """Enhanced incident processing with smart information extraction"""
        try:
            print(f"DEBUG: Enhanced incident processing, context: {self.current_context}")
            print(f"DEBUG: Extracted info: {extracted_info}")
            
            # Merge extracted info into context
            for key, value in extracted_info.items():
                if key not in self.current_context:
                    self.current_context[key] = value
            
            # Check if we have incident type(s)
            if 'incident_types' in self.current_context:
                # Multiple incident handling
                return self.continue_multiple_incident_filling(message, extracted_info)
            elif 'incident_type' not in self.current_context:
                # Try to detect incident type from message and extracted info
                detected_type = self.detect_incident_type_from_context(message, extracted_info)
                print(f"DEBUG: Detected incident type from context: {detected_type}")
                
                if detected_type:
                    self.current_context['incident_type'] = detected_type
                    return self.start_slot_filling_with_extracted_info(detected_type, extracted_info)
                else:
                    return self.ask_incident_type()
            
            # Continue slot filling if we have an incident type
            return self.continue_slot_filling_enhanced(message, extracted_info)
            
        except Exception as e:
            print(f"ERROR: process_incident_mode_enhanced failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Reset state and fall back to incident type selection
            self.current_context = {}
            self.slot_filling_state = {}
            return self.ask_incident_type()
    
    def continue_multiple_incident_filling(self, message: str, extracted_info: Dict) -> Dict:
        """Continue filling slots for multiple incident types"""
        try:
            # Merge new extracted info
            for key, value in extracted_info.items():
                self.current_context[key] = value
                if 'collected_data' in self.slot_filling_state:
                    self.slot_filling_state['collected_data'][key] = value
            
            # Get current slot
            current_slot = self.slot_filling_state.get('current_slot')
            slots = self.slot_filling_state.get('slots', [])
            filled = self.slot_filling_state.get('filled', 0)
            
            # If user provided a direct answer for current slot, store it
            if current_slot and message.strip():
                self.current_context[current_slot] = message
                self.slot_filling_state['collected_data'][current_slot] = message
                filled += 1
                self.slot_filling_state['filled'] = filled
            
            # Check if more slots needed
            if filled < len(slots):
                next_slot = slots[filled]
                self.slot_filling_state['current_slot'] = next_slot
                
                # Skip slot if we already have info from extraction
                while (filled < len(slots) and 
                       slots[filled] in self.slot_filling_state.get('collected_data', {})):
                    filled += 1
                    self.slot_filling_state['filled'] = filled
                
                if filled < len(slots):
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
            
            # All slots filled
            return self.complete_incident_report_safe()
            
        except Exception as e:
            print(f"ERROR: continue_multiple_incident_filling failed: {e}")
            return self.complete_incident_report_safe()
    
    def detect_incident_type_from_context(self, message: str, extracted_info: Dict) -> Optional[str]:
        """Detect incident type from context and extracted information"""
        # Check extracted info for clues
        if 'injury_type' in extracted_info or 'body_part' in extracted_info:
            return 'injury'
        
        if 'chemical_name' in extracted_info or 'environmental_impact' in extracted_info:
            return 'environmental'
        
        if 'property_damage' in extracted_info or 'cost_estimate' in extracted_info:
            return 'property'
        
        # Fall back to message analysis
        return self.detect_incident_type_safe(message)
    
    def start_slot_filling_with_extracted_info(self, incident_type: str, extracted_info: Dict) -> Dict:
        """Start slot filling with pre-extracted information"""
        try:
            slots = self.slot_policy.incident_slots.get(incident_type, ['description', 'location'])
            print(f"DEBUG: Starting slot filling for {incident_type}, slots: {slots}")
            
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
                    "progress": f"Step {filled_count + 1} of {len(slots)}",
                    "guidance": "I've captured some details already. Let me get the remaining information."
                }
            else:
                # All slots already filled from extraction
                return self.complete_incident_report_safe()
            
        except Exception as e:
            print(f"ERROR: start_slot_filling_with_extracted_info failed: {e}")
            return self.ask_incident_type()
    
    def continue_slot_filling_enhanced(self, message: str, extracted_info: Dict) -> Dict:
        """Enhanced slot filling with smart information handling"""
        try:
            # Validate slot filling state
            if not self.slot_filling_state or not isinstance(self.slot_filling_state, dict):
                print("WARNING: Invalid slot filling state, resetting")
                return self.complete_incident_report_safe()
            
            current_slot = self.slot_filling_state.get('current_slot')
            slots = self.slot_filling_state.get('slots', [])
            filled = self.slot_filling_state.get('filled', 0)
            collected_data = self.slot_filling_state.get('collected_data', {})
            
            print(f"DEBUG: Enhanced slot filling - slot: {current_slot}, filled: {filled}/{len(slots)}")
            
            # Merge extracted info
            for key, value in extracted_info.items():
                if key not in collected_data:
                    collected_data[key] = value
                    self.current_context[key] = value
            
            # Store direct answer if we have a current slot and valid message
            if current_slot and message.strip():
                collected_data[current_slot] = message
                self.current_context[current_slot] = message
                filled += 1
                self.slot_filling_state.update({
                    'filled': filled,
                    'collected_data': collected_data
                })
                print(f"DEBUG: Stored answer for {current_slot}: {message[:50]}...")
            
            # Skip slots we have from extraction
            while filled < len(slots) and slots[filled] in collected_data:
                filled += 1
                self.slot_filling_state['filled'] = filled
            
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
            print(f"ERROR: continue_slot_filling_enhanced failed: {e}")
            import traceback
            traceback.print_exc()
            return self.complete_incident_report_safe()
    
    # [Previous methods remain the same: start_incident_workflow, switch_mode_safe, etc.]
    def start_incident_workflow(self, incident_type: str, extracted_info: Dict = None) -> Dict:
        """Start incident workflow with extracted information"""
        try:
            extracted_info = extracted_info or {}
            
            # Reset any existing state
            self.current_mode = 'incident'
            self.current_context = {'incident_type': incident_type}
            self.current_context.update(extracted_info)
            self.slot_filling_state = {}
            
            return self.start_slot_filling_with_extracted_info(incident_type, extracted_info)
            
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
    
    def detect_incident_type_safe(self, message: str) -> Optional[str]:
        """Safe incident type detection with error handling"""
        try:
            if not isinstance(message, str):
                return None
                
            msg = message.lower()
            
            # Enhanced keyword matching with context awareness
            type_keywords = {
                'injury': [
                    r'injur', r'hurt', r'cut', r'burn', r'medical', r'hospital', r'first aid',
                    r'someone.*injured', r'person.*hurt', r'employee.*hurt', r'worker.*injured',
                    r'broken.*bone', r'sprain', r'strain', r'wound', r'bleeding', r'broke.*arm',
                    r'broke.*leg', r'fractured', r'bruise', r'worker.*broke'
                ],
                'vehicle': [
                    r'vehicle', r'car', r'truck', r'collision', r'crash', r'accident.*vehicle',
                    r'hit.*by', r'ran.*into', r'fender.*bender', r'auto.*accident'
                ],
                'environmental': [
                    r'spill', r'chemical', r'leak', r'environmental', r'release',
                    r'contamination', r'waste', r'hazardous.*material', r'oil.*spill',
                    r'spill.*oil', r'oil.*all.*over'
                ],
                'near_miss': [
                    r'near.*miss', r'almost', r'could.*have', r'close.*call',
                    r'nearly.*happened', r'just.*missed'
                ],
                'property': [
                    r'damage', r'broken', r'property', r'equipment.*damage',
                    r'machinery.*broke', r'building.*damage', r'car.*costing',
                    r'costing.*\d+.*dollars', r'expensive.*damage', r'breaking.*car',
                    r'cost.*to.*fix', r'\$?\d+.*damage'
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
    
    def complete_incident_report_safe(self) -> Dict:
        """Complete incident with comprehensive error handling"""
        try:
            incident_id = f"INC-{int(time.time())}"
            
            # Determine incident type(s)
            if 'incident_types' in self.current_context:
                incident_types = self.current_context['incident_types']
                incident_type = '+'.join(incident_types)
                primary_type = incident_types[0]
            else:
                incident_type = self.current_context.get('incident_type', 'other')
                primary_type = incident_type
                incident_types = [incident_type]
            
            # Enhanced risk assessment
            risk_level = self.enhanced_risk_assessment_safe(incident_types)
            
            # Save incident data
            save_success = self.save_incident_data_enhanced(incident_id, incident_type, risk_level)
            
            # Generate enhanced summary
            summary = self.generate_enhanced_incident_summary()
            
            # Reset state
            old_context = dict(self.current_context)
            self.reset_state_safe()
            
            success_message = "✅ **Multi-Type Incident Report Completed**\n\n" if len(incident_types) > 1 else "✅ **Incident Report Completed**\n\n"
            success_message += f"**Incident ID:** `{incident_id}`\n\n{summary}\n\n**Risk Assessment:** {risk_level}\n\n"
            
            if len(incident_types) > 1:
                success_message += "**⚠️ Multiple Impact Types Detected:**\n"
                for itype in incident_types:
                    success_message += f"• {itype.title()} incident protocols activated\n"
                success_message += "\n"
            
            if save_success:
                success_message += "Your incident has been recorded and assigned a unique ID. Relevant teams have been notified."
            else:
                success_message += "⚠️ Note: There was an issue saving to the database, but your report has been processed."
            
            return {
                "message": success_message,
                "type": "incident_completed",
                "incident_id": incident_id,
                "incident_types": incident_types,
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
                "guidance": "Given the complexity of this incident, please ensure all affected parties are notified and follow-up actions are scheduled.",
                "debug_context": old_context
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
    
    def enhanced_risk_assessment_safe(self, incident_types: List[str]) -> str:
        """Enhanced risk assessment for multiple incident types"""
        try:
            risk_factors = []
            
            # Check description and context for severity indicators
            description = str(self.current_context.get('description', '')).lower()
            all_text = ' '.join([str(v) for v in self.current_context.values() if isinstance(v, str)]).lower()
            
            # High risk indicators
            high_risk_words = ['severe', 'hospital', 'major', 'significant', 'emergency', 'broke.*arm', 'fractured']
            medium_risk_words = ['medical', 'treatment', 'spill.*oil', 'damage.*car', 'cost.*\d+']
            
            risk_score = 0
            
            # Base score by incident type
            type_scores = {
                'injury': 40,
                'environmental': 30,
                'property': 20,
                'vehicle': 25,
                'near_miss': 15
            }
            
            for incident_type in incident_types:
                risk_score += type_scores.get(incident_type, 20)
            
            # Severity modifiers
            for word in high_risk_words:
                if re.search(word, all_text):
                    risk_score += 20
                    risk_factors.append(f"High severity indicator: {word}")
            
            for word in medium_risk_words:
                if re.search(word, all_text):
                    risk_score += 10
                    risk_factors.append(f"Medium severity indicator: {word}")
            
            # Multiple incident type penalty
            if len(incident_types) > 1:
                risk_score += 15
                risk_factors.append("Multiple incident types")
            
            # Cost factor
            if 'cost_estimate' in self.current_context:
                cost_text = self.current_context['cost_estimate']
                if re.search(r'\d{5,}', cost_text):  # $10,000+
                    risk_score += 15
                    risk_factors.append("High cost impact")
            
            # Determine risk level
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
                
        except Exception as e:
            print(f"ERROR: enhanced_risk_assessment_safe failed: {e}")
            return "Medium"
    
    def save_incident_data_enhanced(self, incident_id: str, incident_type: str, risk_level: str) -> bool:
        """Save enhanced incident data with multiple types"""
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
            
            # Create enhanced incident record
            incident_data = {
                "id": incident_id,
                "type": incident_type,
                "created_ts": time.time(),
                "status": "complete",
                "risk_level": str(risk_level),
                "answers": {
                    "people": self._extract_people_info_enhanced(),
                    "environment": self._extract_environment_info_enhanced(),
                    "cost": self._extract_cost_info_enhanced(),
                    "legal": self._extract_legal_info_enhanced(),
                    "reputation": "To be assessed by management"
                },
                "chatbot_data": dict(self.current_context),
                "extracted_info": dict(self.last_extracted_info),
                "reported_via": "enhanced_chatbot",
                "multiple_types": '+' in incident_type,
                "incident_types": self.current_context.get('incident_types', [incident_type])
            }
            
            incidents[incident_id] = incident_data
            
            # Save with error handling
            try:
                incidents_file.write_text(json.dumps(incidents, indent=2))
                print(f"DEBUG: Saved enhanced incident {incident_id}")
                return True
            except Exception as e:
                print(f"ERROR: Failed to write incidents file: {e}")
                return False
            
        except Exception as e:
            print(f"ERROR: save_incident_data_enhanced failed: {e}")
            return False
    
    def generate_enhanced_incident_summary(self) -> str:
        """Generate enhanced human-readable summary"""
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
            
            # Add specific details based on what we have
            if 'injured_person' in self.current_context:
                summary += f"**Injured Person:** {self.current_context['injured_person']}\n"
            
            if 'body_part' in self.current_context:
                summary += f"**Injury:** {self.current_context.get('injury_type', 'Injury')} to {self.current_context['body_part']}\n"
            
            if 'chemical_name' in self.current_context:
                summary += f"**Chemical Involved:** {self.current_context['chemical_name']}\n"
            
            if 'cost_estimate' in self.current_context:
                summary += f"**Estimated Cost:** {self.current_context['cost_estimate']}\n"
            
            summary += f"**Description:** {description[:150]}{'...' if len(description) > 150 else ''}"
            
            return summary
        except Exception as e:
            print(f"ERROR: generate_enhanced_incident_summary failed: {e}")
            return "**Type:** Unknown\n**Location:** Not specified\n**Description:** Error generating summary"
    
    def _extract_people_info_enhanced(self) -> str:
        """Extract enhanced people-related information"""
        try:
            info_parts = []
            
            safe_keys = ['injured_person', 'people_involved', 'injury_type', 'body_part', 'severity', 'description']
            for key in safe_keys:
                value = self.current_context.get(key)
                if value:
                    info_parts.append(f"{key.replace('_', ' ').title()}: {str(value)}")
            
            # Add extracted info
            if self.last_extracted_info:
                for key, value in self.last_extracted_info.items():
                    if key in safe_keys and key not in [k.split(':')[0].lower().replace(' ', '_') for k in info_parts]:
                        info_parts.append(f"{key.replace('_', ' ').title()}: {str(value)}")
            
            return "\n".join(info_parts) if info_parts else "N/A"
        except Exception as e:
            print(f"ERROR: _extract_people_info_enhanced failed: {e}")
            return "Error extracting people information"
    
    def _extract_environment_info_enhanced(self) -> str:
        """Extract enhanced environment-related information"""
        try:
            info_parts = []
            
            env_keys = ['chemical_name', 'spill_volume', 'environmental_impact', 'containment']
            for key in env_keys:
                value = self.current_context.get(key)
                if value:
                    info_parts.append(f"{key.replace('_', ' ').title()}: {str(value)}")
            
            # Check for environmental indicators in extracted info
            if 'environmental_impact' in self.last_extracted_info:
                info_parts.append(f"Environmental Impact: {self.last_extracted_info['environmental_impact']}")
            
            return "\n".join(info_parts) if info_parts else "N/A"
        except Exception as e:
            print(f"ERROR: _extract_environment_info_enhanced failed: {e}")
            return "N/A"
    
    def _extract_cost_info_enhanced(self) -> str:
        """Extract enhanced cost-related information"""
        try:
            cost_parts = []
            
            if 'cost_estimate' in self.current_context:
                cost_parts.append(f"Estimated Damage: {self.current_context['cost_estimate']}")
            
            if 'damage_description' in self.current_context:
                cost_parts.append(f"Damage Description: {self.current_context['damage_description']}")
            
            if 'property_damage' in self.current_context:
                cost_parts.append(f"Property Damage: {self.current_context['property_damage']}")
            
            return "\n".join(cost_parts) if cost_parts else "N/A"
        except Exception as e:
            print(f"ERROR: _extract_cost_info_enhanced failed: {e}")
            return "N/A"
    
    def _extract_legal_info_enhanced(self) -> str:
        """Extract enhanced legal information"""
        try:
            # Determine legal implications based on incident type and severity
            legal_info = []
            
            if 'incident_types' in self.current_context:
                incident_types = self.current_context['incident_types']
            else:
                incident_types = [self.current_context.get('incident_type', 'other')]
            
            if 'injury' in incident_types:
                if any(word in str(self.current_context.get('severity', '')).lower() for word in ['hospital', 'severe', 'medical']):
                    legal_info.append("OSHA recordable injury - notification required")
                else:
                    legal_info.append("Workplace injury - internal documentation required")
            
            if 'environmental' in incident_types:
                legal_info.append("Environmental spill - assess reporting requirements")
            
            if 'property' in incident_types:
                cost_text = str(self.current_context.get('cost_estimate', ''))
                if re.search(r'\d{4,}', cost_text):  # $1000+
                    legal_info.append("Significant property damage - insurance notification may be required")
            
            if len(incident_types) > 1:
                legal_info.append("Multi-type incident - comprehensive legal review recommended")
            
            return "\n".join(legal_info) if legal_info else "Standard incident documentation requirements"
        except Exception as e:
            print(f"ERROR: _extract_legal_info_enhanced failed: {e}")
            return "Legal assessment pending"
    
    def reset_state_safe(self):
        """Safely reset chatbot state"""
        try:
            self.current_mode = 'general'
            self.current_context = {}
            self.slot_filling_state = {}
            self.last_extracted_info = {}
            print("DEBUG: Enhanced chatbot state reset successfully")
        except Exception as e:
            print(f"ERROR: reset_state_safe failed: {e}")
            # Force reset even if there's an error
            self.current_mode = 'general'
            self.current_context = {}
            self.slot_filling_state = {}
            self.last_extracted_info = {}
    
    def store_conversation_safe(self, user_message: str, response: Dict, intent: str):
        """Safely store conversation history"""
        try:
            self.conversation_history.append({
                "user": str(user_message)[:200],
                "bot": str(response.get("message", ""))[:200],
                "intent": str(intent),
                "mode": str(self.current_mode),
                "timestamp": time.time(),
                "extracted_info": dict(self.last_extracted_info)
            })
            
            # Keep only last 20 exchanges
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
        except Exception as e:
            print(f"ERROR: store_conversation_safe failed: {e}")
    
    # [Keep all other existing methods: get_error_recovery_response, get_critical_error_response, etc.]
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

# Create the chatbot instance
def create_chatbot():
    """Factory function to create enhanced chatbot instance"""
    try:
        return LightweightEHSChatbot()
    except Exception as e:
        print(f"ERROR: Failed to create enhanced chatbot: {e}")
        import traceback
        traceback.print_exc()
        return None

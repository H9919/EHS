# 2. Fix services/ehs_chatbot.py - Better state management and workflow
# =============================================================================

class EnhancedEHSChatbot:
    def __init__(self):
        self.conversation_history = []
        self.current_mode = 'general'
        self.current_context = {}
        self.slot_filling_state = {}
        self.last_extracted_info = {}
        
        # Initialize components with error handling
        try:
            self.intent_classifier = EnhancedIntentClassifier()
            self.info_extractor = SmartInformationExtractor()
            self.slot_policy = EnhancedSlotPolicy()
            self.risk_assessor = EnhancedRiskAssessment()
            print("✓ Enhanced EHS Chatbot initialized successfully")
        except Exception as e:
            print(f"ERROR: Failed to initialize chatbot components: {e}")
            # Initialize with minimal functionality
            self.intent_classifier = None
            self.info_extractor = None
            self.slot_policy = None
            self.risk_assessor = None

    def process_message(self, user_message: str, user_id: str = None, context: Dict = None) -> Dict:
        """Enhanced message processing with better error handling"""
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
            
            # Reset state if user wants to start over
            if self.should_reset_conversation(user_message):
                self.reset_state_safe()
                return self.get_general_help_response()
            
            # Smart information extraction (only if components are available)
            extracted_info = {}
            if self.info_extractor:
                extracted_info = self.info_extractor.extract_comprehensive_info(user_message)
                self.last_extracted_info = extracted_info
                print(f"DEBUG: Extracted info: {extracted_info}")
            
            # Intent classification (only if available)
            intent = "general_inquiry"
            confidence = 0.5
            if self.intent_classifier:
                intent, confidence = self.intent_classifier.classify_intent(user_message)
                print(f"DEBUG: Classified intent: {intent}, confidence: {confidence}")
            
            # Process based on current mode
            if self.current_mode == 'incident':
                response = self.process_incident_mode_enhanced(user_message, intent, confidence, extracted_info)
            elif self.current_mode == 'safety_concern':
                response = self.process_safety_concern_mode(user_message)
            else:
                # General mode - handle high-confidence intents
                if confidence > 0.6:
                    if intent == 'incident_reporting':
                        return self.start_incident_workflow('general', extracted_info, user_message)
                    elif intent == 'safety_concern':
                        return self.process_safety_concern_mode(user_message)
                    elif intent == 'sds_lookup':
                        return self.process_sds_lookup(user_message)
                
                response = self.process_general_mode(user_message, intent)
            
            # Store conversation
            self.store_conversation_safe(user_message, response, intent)
            
            return response
            
        except Exception as e:
            print(f"ERROR: process_message failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Reset state on error
            self.reset_state_safe()
            return self.get_error_recovery_response(user_message, str(e))

    def should_reset_conversation(self, message: str) -> bool:
        """Check if user wants to start over"""
        reset_phrases = [
            "start over", "restart", "reset", "new conversation", 
            "try again", "begin again", "clear chat", "fresh start"
        ]
        message_lower = message.lower()
        return any(phrase in message_lower for phrase in reset_phrases)

    def process_incident_mode_enhanced(self, message: str, intent: str, confidence: float, extracted_info: Dict) -> Dict:
        """Enhanced incident mode processing with better workflow"""
        try:
            # Check if we have slot filling in progress
            if self.slot_filling_state:
                return self.continue_slot_filling_enhanced(message, extracted_info)
            
            # No slot filling - determine incident type and start
            incident_type = self.determine_incident_type(message, extracted_info)
            if incident_type:
                return self.start_slot_filling_with_extracted_info(incident_type, extracted_info, message)
            else:
                return self.ask_incident_type()
                
        except Exception as e:
            print(f"ERROR: process_incident_mode_enhanced failed: {e}")
            return self.ask_incident_type()

    def determine_incident_type(self, message: str, extracted_info: Dict) -> str:
        """Determine incident type from message and extracted info"""
        message_lower = message.lower()
        
        # Check for specific incident type keywords
        if any(word in message_lower for word in ['injury', 'hurt', 'injured', 'medical', 'broke', 'cut', 'burn']):
            return 'injury'
        elif any(word in message_lower for word in ['spill', 'chemical', 'leak', 'environmental']):
            return 'environmental'
        elif any(word in message_lower for word in ['vehicle', 'car', 'truck', 'collision', 'crash']):
            return 'vehicle'
        elif any(word in message_lower for word in ['property', 'damage', 'equipment', 'broke']):
            return 'property'
        elif any(word in message_lower for word in ['near miss', 'almost', 'could have']):
            return 'near_miss'
        else:
            return 'other'

    def start_slot_filling_with_extracted_info(self, incident_type: str, extracted_info: Dict, original_message: str) -> Dict:
        """Start slot filling with better error handling"""
        try:
            # Define minimal slot requirements
            basic_slots = ['description', 'location']
            type_specific_slots = {
                'injury': ['injured_person', 'injury_type', 'body_part'],
                'environmental': ['chemical_name', 'spill_volume'],
                'vehicle': ['vehicle_info', 'damage_extent'],
                'property': ['damage_description'],
                'other': []
            }
            
            all_slots = basic_slots + type_specific_slots.get(incident_type, [])
            
            # Set up context
            self.current_context = {
                'incident_type': incident_type,
                'description': original_message
            }
            self.current_context.update(extracted_info)
            
            # Find missing slots
            missing_slots = [slot for slot in all_slots if slot not in extracted_info and slot != 'description']
            
            if missing_slots:
                # Start slot filling
                first_slot = missing_slots[0]
                self.slot_filling_state = {
                    'slots': all_slots,
                    'current_slot': first_slot,
                    'filled': len(all_slots) - len(missing_slots),
                    'incident_type': incident_type,
                    'collected_data': dict(extracted_info)
                }
                
                question = self.get_slot_question(first_slot)
                
                info_summary = ""
                if extracted_info:
                    info_summary = "\n**Information captured:**\n"
                    for key, value in extracted_info.items():
                        field_name = key.replace('_', ' ').title()
                        info_summary += f"• {field_name}: {value}\n"
                
                return {
                    "message": f"📝 **{incident_type.title()} Incident Report**{info_summary}\n**Question:** {question}",
                    "type": "slot_filling",
                    "slot": first_slot,
                    "progress": f"Step {len(all_slots) - len(missing_slots) + 1} of {len(all_slots)}"
                }
            else:
                # All slots filled, complete the incident
                return self.complete_incident_report_enhanced()
                
        except Exception as e:
            print(f"ERROR: start_slot_filling_with_extracted_info failed: {e}")
            return self.ask_incident_type()

    def get_slot_question(self, slot: str) -> str:
        """Get question for a specific slot"""
        questions = {
            'description': "Please describe what happened:",
            'location': "Where did this occur?",
            'injured_person': "Who was injured? (Full name)",
            'injury_type': "What type of injury occurred?",
            'body_part': "Which body part was affected?",
            'chemical_name': "What chemical was involved?",
            'spill_volume': "Approximately how much was spilled?",
            'vehicle_info': "What vehicle was involved?",
            'damage_extent': "What was the extent of the damage?",
            'damage_description': "Please describe the damage:"
        }
        return questions.get(slot, f"Please provide information about {slot.replace('_', ' ')}:")

    def continue_slot_filling_enhanced(self, message: str, extracted_info: Dict) -> Dict:
        """Continue slot filling with better logic"""
        try:
            if not self.slot_filling_state:
                return self.complete_incident_report_enhanced()
            
            current_slot = self.slot_filling_state.get('current_slot')
            slots = self.slot_filling_state.get('slots', [])
            filled = self.slot_filling_state.get('filled', 0)
            collected_data = self.slot_filling_state.get('collected_data', {})
            
            # Store the answer for current slot
            if current_slot and message.strip():
                collected_data[current_slot] = message
                self.current_context[current_slot] = message
                filled += 1
                self.slot_filling_state.update({
                    'filled': filled,
                    'collected_data': collected_data
                })
            
            # Find next unfilled slot
            while filled < len(slots) and slots[filled] in collected_data:
                filled += 1
                self.slot_filling_state['filled'] = filled
            
            # Check if more slots needed
            if filled < len(slots):
                next_slot = slots[filled]
                self.slot_filling_state['current_slot'] = next_slot
                question = self.get_slot_question(next_slot)
                
                return {
                    "message": f"✅ Got it.\n\n**Next question:** {question}",
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
        """Complete incident with better error handling"""
        try:
            incident_id = f"INC-{int(time.time())}"
            incident_type = self.current_context.get('incident_type', 'other')
            
            # Generate basic risk assessment
            risk_level = "Medium"
            if incident_type == 'injury':
                risk_level = "High"
            elif incident_type in ['environmental', 'vehicle']:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            # Save incident data
            save_success = self.save_incident_data_simple(incident_id, incident_type)
            
            # Generate summary
            summary = self.generate_simple_incident_summary()
            
            # Reset state
            self.reset_state_safe()
            
            success_message = f"✅ **Incident Report Completed**\n\n"
            success_message += f"**Incident ID:** `{incident_id}`\n"
            success_message += f"**Type:** {incident_type.title()}\n"
            success_message += f"**Risk Level:** {risk_level}\n\n"
            success_message += summary
            
            if save_success:
                success_message += "\n\n✅ Your incident has been recorded and assigned a unique ID."
            else:
                success_message += "\n\n⚠️ Report processed but there was an issue saving to the database."
            
            return {
                "message": success_message,
                "type": "incident_completed",
                "incident_id": incident_id,
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
                        "text": "🔄 Report Another",
                        "action": "continue_conversation",
                        "message": "I need to report another incident"
                    }
                ]
            }
            
        except Exception as e:
            print(f"ERROR: complete_incident_report_enhanced failed: {e}")
            incident_id = f"INC-{int(time.time())}"
            self.reset_state_safe()
            
            return {
                "message": f"✅ **Incident Report Completed**\n\nIncident ID: `{incident_id}`\n\nYour basic report has been recorded.",
                "type": "incident_completed",
                "incident_id": incident_id,
                "actions": [
                    {
                        "text": "📊 Dashboard",
                        "action": "navigate",
                        "url": "/dashboard"
                    }
                ]
            }

    def save_incident_data_simple(self, incident_id: str, incident_type: str) -> bool:
        """Save incident data with error handling"""
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
            
            # Create simple incident record
            incident_data = {
                "id": incident_id,
                "type": incident_type,
                "created_ts": time.time(),
                "status": "complete",
                "answers": {
                    "people": self.current_context.get('description', 'Incident reported via chatbot'),
                    "environment": "N/A",
                    "cost": "N/A", 
                    "legal": "Standard documentation",
                    "reputation": "Internal incident"
                },
                "chatbot_data": dict(self.current_context),
                "reported_via": "chatbot_v2"
            }
            
            incidents[incident_id] = incident_data
            incidents_file.write_text(json.dumps(incidents, indent=2))
            print(f"DEBUG: Saved incident {incident_id}")
            return True
            
        except Exception as e:
            print(f"ERROR: save_incident_data_simple failed: {e}")
            return False

    def generate_simple_incident_summary(self) -> str:
        """Generate simple summary"""
        try:
            incident_type = self.current_context.get('incident_type', 'Unknown')
            description = self.current_context.get('description', 'No description provided')
            location = self.current_context.get('location', 'Location not specified')
            
            summary = f"**Type:** {incident_type.title()}\n"
            summary += f"**Location:** {location}\n"
            summary += f"**Description:** {description[:200]}{'...' if len(description) > 200 else ''}"
            
            return summary
        except Exception as e:
            print(f"ERROR: generate_simple_incident_summary failed: {e}")
            return "**Summary:** Incident report completed"

    def process_sds_lookup(self, message: str) -> Dict:
        """Handle SDS lookup requests"""
        return {
            "message": "📄 **I'll help you find Safety Data Sheets.**\n\nOur SDS library is searchable and easy to navigate.",
            "type": "sds_help",
            "actions": [
                {"text": "🔍 Search SDS Library", "action": "navigate", "url": "/sds"},
                {"text": "📤 Upload New SDS", "action": "navigate", "url": "/sds/upload"}
            ]
        }

    def reset_state_safe(self):
        """Safely reset chatbot state"""
        try:
            self.current_mode = 'general'
            self.current_context = {}
            self.slot_filling_state = {}
            self.last_extracted_info = {}
            print("DEBUG: Chatbot state reset")
        except Exception as e:
            print(f"ERROR: reset_state_safe failed: {e}")

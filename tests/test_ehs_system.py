# tests/test_ehs_system.py - Comprehensive testing framework
import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from services.ehs_chatbot import EHSChatbot, IntentClassifier, SlotFillingPolicy
from services.incident_validator import (
    compute_completeness, validate_record, 
    IncidentScoring, RootCauseAnalysis, CAPAGenerator
)

class TestIntentClassification(unittest.TestCase):
    """Test intent classification functionality"""
    
    def setUp(self):
        self.classifier = IntentClassifier()
    
    def test_incident_classification(self):
        """Test incident reporting intent detection"""
        test_cases = [
            ("I need to report a workplace injury", "incident_reporting"),
            ("Someone got hurt at work", "incident_reporting"),
            ("There was an accident", "incident_reporting"),
            ("Property damage occurred", "incident_reporting"),
            ("Chemical spill happened", "incident_reporting")
        ]
        
        for message, expected_intent in test_cases:
            with self.subTest(message=message):
                intent, confidence = self.classifier.classify_intent(message)
                self.assertEqual(intent, expected_intent)
                self.assertGreater(confidence, 0.7)
    
    def test_safety_concern_classification(self):
        """Test safety concern intent detection"""
        test_cases = [
            ("I observed unsafe working conditions", "safety_concern"),
            ("There's a potential safety hazard", "safety_concern"),
            ("I'm concerned about workplace safety", "safety_concern"),
            ("Near miss incident", "safety_concern"),
            ("Unsafe behavior noticed", "safety_concern")
        ]
        
        for message, expected_intent in test_cases:
            with self.subTest(message=message):
                intent, confidence = self.classifier.classify_intent(message)
                self.assertEqual(intent, expected_intent)
                self.assertGreater(confidence, 0.5)
    
    def test_sds_classification(self):
        """Test SDS lookup intent detection"""
        test_cases = [
            ("I need the safety data sheet for acetone", "sds_lookup"),
            ("Where can I find chemical information", "sds_lookup"),
            ("Looking for SDS documents", "sds_lookup"),
            ("Chemical safety information needed", "sds_lookup"),
            ("Find SDS for ammonia", "sds_lookup")
        ]
        
        for message, expected_intent in test_cases:
            with self.subTest(message=message):
                intent, confidence = self.classifier.classify_intent(message)
                self.assertEqual(intent, expected_intent)
                self.assertGreater(confidence, 0.5)

class TestSlotFilling(unittest.TestCase):
    """Test slot filling policies and logic"""
    
    def setUp(self):
        self.slot_policy = SlotFillingPolicy()
    
    def test_injury_slots(self):
        """Test injury incident slot requirements"""
        injury_slots = self.slot_policy.incident_slots["injury"]
        required_slots = injury_slots["required"]
        
        expected_required = ['description', 'location', 'injured_person', 'injury_type', 'body_part', 'severity']
        self.assertEqual(set(required_slots), set(expected_required))
    
    def test_environmental_slots(self):
        """Test environmental incident slot requirements"""
        env_slots = self.slot_policy.incident_slots["environmental"]
        required_slots = env_slots["required"]
        
        expected_required = ['description', 'location', 'chemical_name', 'spill_volume', 'containment']
        self.assertEqual(set(required_slots), set(expected_required))
    
    def test_slot_questions(self):
        """Test that all required slots have questions"""
        for incident_type, slots in self.slot_policy.incident_slots.items():
            for slot in slots["required"]:
                with self.subTest(incident_type=incident_type, slot=slot):
                    self.assertIn(slot, self.slot_policy.slot_questions)
                    self.assertIsInstance(self.slot_policy.slot_questions[slot], str)
                    self.assertGreater(len(self.slot_policy.slot_questions[slot]), 10)

class TestChatbotIntegration(unittest.TestCase):
    """Test full chatbot integration and workflows"""
    
    def setUp(self):
        self.chatbot = EHSChatbot()
        # Create temporary data directory
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    @patch('services.ehs_chatbot.Path')
    def test_incident_reporting_workflow(self, mock_path):
        """Test complete incident reporting workflow"""
        # Mock the data directory
        mock_path.return_value = self.data_dir / "incidents.json"
        
        # Start incident reporting
        response1 = self.chatbot.process_message("I need to report a workplace injury")
        self.assertEqual(self.chatbot.current_mode, "incident")
        
        # Should ask for incident type
        self.assertIn("incident", response1["message"].lower())
        
        # Specify injury type
        response2 = self.chatbot.process_message("This involves a workplace injury")
        self.assertEqual(self.chatbot.current_context.get("incident_type"), "injury")
        
        # Fill required slots
        responses = []
        test_answers = [
            "Employee slipped and fell in warehouse",
            "Warehouse section B",
            "John Smith", 
            "Sprained ankle",
            "Right ankle",
            "Medical treatment required"
        ]
        
        for answer in test_answers:
            response = self.chatbot.process_message(answer)
            responses.append(response)
        
        # Final response should complete the incident
        final_response = responses[-1]
        self.assertEqual(final_response["type"], "incident_completed")
        self.assertIn("incident_id", final_response)
    
    def test_file_upload_handling(self):
        """Test file upload processing"""
        # Test image upload
        image_file = {
            "filename": "incident_photo.jpg",
            "type": "image/jpeg",
            "path": "/tmp/incident_photo.jpg",
            "size": 1024000
        }
        
        response = self.chatbot.process_message("", context={"uploaded_file": image_file})
        self.assertEqual(response["type"], "image_upload_incident")
        self.assertIn("photo", response["message"].lower())
        
        # Test PDF upload
        pdf_file = {
            "filename": "acetone_sds.pdf", 
            "type": "application/pdf",
            "path": "/tmp/acetone_sds.pdf",
            "size": 2048000
        }
        
        response = self.chatbot.process_message("", context={"uploaded_file": pdf_file})
        self.assertEqual(response["type"], "pdf_upload_sds")
        self.assertIn("sds", response["message"].lower())
    
    def test_emergency_detection(self):
        """Test emergency situation detection"""
        emergency_messages = [
            "Emergency! Someone is bleeding badly",
            "Call 911 now!",
            "Fire in the building",
            "Someone is unconscious",
            "Heart attack in progress"
        ]
        
        for message in emergency_messages:
            with self.subTest(message=message):
                response = self.chatbot.process_message(message)
                self.assertEqual(response["type"], "emergency")
                self.assertIn("911", response["message"])

class TestIncidentScoring(unittest.TestCase):
    """Test incident scoring and risk assessment"""
    
    def setUp(self):
        self.scorer = IncidentScoring()
    
    def test_severity_analysis(self):
        """Test severity scoring for different categories"""
        # Test people category
        people_text = "employee hospitalized with severe burns"
        severity = self.scorer._analyze_severity("people", people_text, people_text)
        self.assertGreaterEqual(severity, 6)  # Should be high severity
        
        # Test environment category
        env_text = "minor chemical spill contained immediately"
        severity = self.scorer._analyze_severity("environment", env_text, env_text)
        self.assertLessEqual(severity, 4)  # Should be low-medium severity
    
    def test_likelihood_analysis(self):
        """Test likelihood scoring"""
        high_likelihood_text = "this happens frequently in our operations"
        likelihood = self.scorer._analyze_likelihood(high_likelihood_text, "injury")
        self.assertGreaterEqual(likelihood, 6)
        
        low_likelihood_text = "this is a very rare occurrence"
        likelihood = self.scorer._analyze_likelihood(low_likelihood_text, "injury")
        self.assertLessEqual(likelihood, 4)
    
    def test_risk_level_calculation(self):
        """Test overall risk level calculation"""
        # High risk scenario
        high_risk_score = 80
        risk_level = self.scorer._get_risk_level(high_risk_score)
        self.assertEqual(risk_level, "Critical")
        
        # Low risk scenario
        low_risk_score = 15
        risk_level = self.scorer._get_risk_level(low_risk_score)
        self.assertEqual(risk_level, "Very Low")
    
    def test_complete_scoring(self):
        """Test complete scoring workflow"""
        incident_data = {
            "type": "injury",
            "answers": {
                "people": "Employee fell from ladder and broke arm, required hospitalization",
                "environment": "No environmental impact",
                "cost": "Medical costs estimated at $15,000",
                "legal": "OSHA reportable injury",
                "reputation": "Internal incident only"
            }
        }
        
        result = self.scorer.compute_severity_likelihood(incident_data)
        
        self.assertIn("severity_scores", result)
        self.assertIn("likelihood_score", result)
        self.assertIn("risk_score", result)
        self.assertIn("risk_level", result)
        self.assertIn("rationale", result)
        
        # People should have highest severity for this scenario
        self.assertGreater(result["severity_scores"]["people"], 6)

class TestRootCauseAnalysis(unittest.TestCase):
    """Test 5 Whys root cause analysis"""
    
    def setUp(self):
        self.rca = RootCauseAnalysis()
    
    def test_5_whys_prompts_generation(self):
        """Test generation of 5 Whys prompts"""
        description = "Employee slipped on wet floor"
        prompts = self.rca.generate_5_whys_prompts(description)
        
        self.assertEqual(len(prompts), 5)
        
        for i, prompt in enumerate(prompts, 1):
            self.assertEqual(prompt["level"], i)
            self.assertIn("question", prompt)
            self.assertIn("guidance", prompt)
            self.assertIn("examples", prompt)
            self.assertIsInstance(prompt["examples"], list)
    
    def test_guidance_quality(self):
        """Test quality of guidance for each level"""
        prompts = self.rca.generate_5_whys_prompts("Test incident")
        
        # Level 1 should focus on immediate cause
        self.assertIn("immediate", prompts[0]["guidance"].lower())
        
        # Level 5 should focus on organizational/cultural
        self.assertIn("organizational", prompts[4]["guidance"].lower())

class TestCAPAGeneration(unittest.TestCase):
    """Test CAPA suggestion generation"""
    
    def setUp(self):
        self.capa_gen = CAPAGenerator()
    
    def test_rule_based_suggestions(self):
        """Test rule-based CAPA generation"""
        incident_data = {
            "type": "injury",
            "answers": {
                "people": "Employee not wearing proper PPE when injury occurred"
            }
        }
        root_causes = ["Training insufficient", "PPE not available"]
        
        suggestions = self.capa_gen.suggest_capas(incident_data, root_causes)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Should suggest training-related CAPA
        training_suggested = any("training" in s.get("action", "").lower() for s in suggestions)
        self.assertTrue(training_suggested)
    
    def test_capa_deduplication(self):
        """Test CAPA suggestion deduplication"""
        duplicate_suggestions = [
            {"action": "Provide safety training", "priority": "high"},
            {"action": "Provide safety training", "priority": "medium"},  # Duplicate
            {"action": "Install safety equipment", "priority": "high"}
        ]
        
        unique_suggestions = self.capa_gen._deduplicate_and_rank(duplicate_suggestions)
        
        self.assertEqual(len(unique_suggestions), 2)  # Should remove one duplicate
        
        # Should keep higher priority version
        training_capa = next(s for s in unique_suggestions if "training" in s["action"])
        self.assertEqual(training_capa["priority"], "high")

class TestIncidentValidation(unittest.TestCase):
    """Test incident validation and completeness"""
    
    def test_completeness_calculation(self):
        """Test incident completeness scoring"""
        # Complete incident
        complete_incident = {
            "type": "injury",
            "answers": {
                "people": "Detailed people information here",
                "environment": "Environmental details", 
                "cost": "Cost information",
                "legal": "Legal considerations",
                "reputation": "Reputation impact"
            },
            "location": "Building A",
            "timestamp": "2023-01-01",
            "reporter": "John Doe"
        }
        
        completeness = compute_completeness(complete_incident)
        self.assertGreater(completeness, 80)
        
        # Incomplete incident
        incomplete_incident = {
            "type": "injury",
            "answers": {
                "people": "Brief info"
            }
        }
        
        completeness = compute_completeness(incomplete_incident)
        self.assertLess(completeness, 50)
    
    def test_validation_logic(self):
        """Test incident validation logic"""
        # Valid injury incident
        valid_incident = {
            "type": "injury",
            "answers": {
                "people": "Detailed injury information provided here",
                "legal": "OSHA reportable, notification sent"
            }
        }
        
        is_valid, missing, warnings = validate_record(valid_incident)
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)
        
        # Invalid incident (missing required fields)
        invalid_incident = {
            "type": "injury", 
            "answers": {
                "environment": "Some info"  # Missing required people and legal
            }
        }
        
        is_valid, missing, warnings = validate_record(invalid_incident)
        self.assertFalse(is_valid)
        self.assertIn("people", missing)
        self.assertIn("legal", missing)

class TestSDSSystem(unittest.TestCase):
    """Test SDS ingestion and search functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sds_dir = Path(self.temp_dir) / "sds"
        self.sds_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    @patch('services.sds_ingest.sds_dir', new_callable=lambda: Path(tempfile.mkdtemp()) / "sds")
    def test_product_name_cleaning(self, mock_sds_dir):
        """Test product name cleaning and normalization"""
        from services.sds_ingest import _clean_product_name
        
        test_cases = [
            ("ACETONE SAFETY DATA SHEET VERSION 2.1", "Acetone"),
            ("Material Safety Data Sheet - Ammonia Rev 3", "Ammonia"),
            ("  Ethanol   Product   Data  Sheet  ", "Ethanol Product Data"),
            ("SDS Methanol 2023-01-15", "Methanol")
        ]
        
        for raw_name, expected_clean in test_cases:
            with self.subTest(raw_name=raw_name):
                cleaned = _clean_product_name(raw_name)
                self.assertIn(expected_clean.lower(), cleaned.lower())
    
    def test_cas_number_extraction(self):
        """Test CAS number extraction from text"""
        from services.sds_ingest import _extract_chemical_info
        
        test_text = """
        Chemical Name: Acetone
        CAS Number: 67-64-1
        Other identifiers: CAS 108-88-3 (toluene)
        """
        
        chemical_info = _extract_chemical_info(test_text)
        
        self.assertIn("67-64-1", chemical_info["cas_numbers"])
        self.assertIn("108-88-3", chemical_info["cas_numbers"])
    
    def test_hazard_statement_extraction(self):
        """Test hazard statement extraction"""
        from services.sds_ingest import _extract_chemical_info
        
        test_text = """
        H225: Highly flammable liquid and vapour
        H319: Causes serious eye irritation
        H336: May cause drowsiness or dizziness
        """
        
        chemical_info = _extract_chemical_info(test_text)
        
        self.assertTrue(any("flammable" in stmt.lower() for stmt in chemical_info["hazard_statements"]))
        self.assertTrue(any("eye irritation" in stmt.lower() for stmt in chemical_info["hazard_statements"]))

class TestEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end workflows"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.chatbot = EHSChatbot()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    @patch('services.ehs_chatbot.Path')
    def test_complete_injury_incident_workflow(self, mock_path):
        """Test complete injury incident reporting workflow"""
        # Mock file paths
        mock_path.return_value = self.data_dir / "incidents.json"
        
        # Test messages in sequence
        test_sequence = [
            ("I need to report a workplace injury", "incident"),
            ("This involves a workplace injury", None),
            ("Employee fell from ladder while changing light bulb", None),
            ("Warehouse section B near loading dock", None),
            ("Jane Smith", None),
            ("Broken wrist", None),
            ("Left wrist", None),
            ("Required emergency room visit and surgery", None)
        ]
        
        responses = []
        for message, expected_mode in test_sequence:
            response = self.chatbot.process_message(message)
            responses.append(response)
            
            if expected_mode:
                self.assertEqual(self.chatbot.current_mode, expected_mode)
        
        # Final response should complete incident
        final_response = responses[-1]
        self.assertEqual(final_response["type"], "incident_completed")
        self.assertIn("incident_id", final_response)
        
        # Should have generated risk assessment
        self.assertIn("Risk Assessment", final_response["message"])
    
    @patch('services.ehs_chatbot.Path')
    def test_anonymous_safety_concern_workflow(self, mock_path):
        """Test anonymous safety concern reporting"""
        mock_path.return_value = self.data_dir / "safety_concerns.json"
        
        # Start safety concern
        response1 = self.chatbot.process_message("I want to report a safety concern anonymously")
        self.assertEqual(self.chatbot.current_mode, "safety_concern")
        
        # Should guide to safety concern form
        self.assertIn("safety", response1["message"].lower())
        self.assertIn("concern", response1["message"].lower())
    
    def test_multi_file_upload_workflow(self):
        """Test handling multiple file uploads in sequence"""
        # Upload incident photo
        photo_response = self.chatbot.process_message(
            "Here's a photo of the incident scene",
            context={"uploaded_file": {
                "filename": "incident.jpg",
                "type": "image/jpeg", 
                "path": "/tmp/incident.jpg"
            }}
        )
        
        self.assertEqual(photo_response["type"], "image_upload_incident")
        
        # Follow up with incident report
        incident_response = self.chatbot.process_message("I want to report an incident with this photo as evidence")
        self.assertEqual(self.chatbot.current_mode, "incident")
        
        # Should maintain file context
        self.assertIn("uploaded_file", self.chatbot.current_context)

class TestSystemIntegration(unittest.TestCase):
    """Test integration between different system components"""
    
    def test_incident_to_capa_integration(self):
        """Test automatic CAPA generation from incidents"""
        from services.incident_validator import generate_scoring_and_capas
        
        incident_data = {
            "type": "injury",
            "answers": {
                "people": "Employee not wearing safety harness fell from height, required hospitalization",
                "legal": "OSHA reportable, citation likely",
                "cost": "Medical costs over $50,000, workers comp claim"
            }
        }
        
        result = generate_scoring_and_capas(incident_data)
        
        # Should have generated CAPAs
        self.assertIn("capa_suggestions", result)
        self.assertGreater(len(result["capa_suggestions"]), 0)
        
        # Should include training CAPA for safety equipment
        capa_actions = [capa.get("action", "") for capa in result["capa_suggestions"]]
        training_capa_exists = any("training" in action.lower() for action in capa_actions)
        self.assertTrue(training_capa_exists)
    
    def test_risk_scoring_consistency(self):
        """Test consistency of risk scoring across different scenarios"""
        from services.incident_validator import IncidentScoring
        
        scorer = IncidentScoring()
        
        # High severity scenarios should consistently score high
        high_severity_incidents = [
            {
                "type": "injury",
                "answers": {"people": "fatality occurred", "legal": "criminal investigation"}
            },
            {
                "type": "environmental", 
                "answers": {"environment": "major chemical release to groundwater", "legal": "EPA enforcement action"}
            }
        ]
        
        for incident in high_severity_incidents:
            result = scorer.compute_severity_likelihood(incident)
            self.assertIn(result["risk_level"], ["High", "Critical"])
    
    def test_sds_chat_integration(self):
        """Test SDS chat integration with incident reporting"""
        # This would test the flow where someone asks about an SDS
        # and then needs to report an incident related to that chemical
        pass

def run_all_tests():
    """Run all test suites"""
    # Create test suite
    test_classes = [
        TestIntentClassification,
        TestSlotFilling, 
        TestChatbotIntegration,
        TestIncidentScoring,
        TestRootCauseAnalysis,
        TestCAPAGeneration,
        TestIncidentValidation,
        TestSDSSystem,
        TestEndToEndWorkflows,
        TestSystemIntegration
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"TEST RESULTS SUMMARY")
    print(f"{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

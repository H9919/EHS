# app.py - FIXED VERSION with all routes properly registered
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for
import traceback

def ensure_dirs():
    """Ensure all required directories exist"""
    directories = [
        "data/sds",
        "data/tmp", 
        "data/pdf",
        "static/qr",
        "static/uploads"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def create_app():
    ensure_dirs()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
    
    # Memory optimization: Only import modules when they exist
    # Core blueprints with graceful error handling
    blueprints_loaded = []
    
    # CRITICAL: Register all blueprints with proper error handling
    try:
        from routes.sds import sds_bp
        app.register_blueprint(sds_bp, url_prefix="/sds")
        blueprints_loaded.append("SDS")
        print("✓ SDS module loaded")
    except ImportError as e:
        print(f"⚠ SDS module not available: {e}")
    
    try:
        from routes.incidents import incidents_bp
        app.register_blueprint(incidents_bp, url_prefix="/incidents")
        blueprints_loaded.append("Incidents")
        print("✓ Incidents module loaded")
    except ImportError as e:
        print(f"⚠ Incidents module not available: {e}")
    
    # Enhanced chatbot module with lazy loading
    try:
        from routes.chatbot import chatbot_bp
        app.register_blueprint(chatbot_bp, url_prefix="/")
        blueprints_loaded.append("Enhanced Chatbot")
        print("✓ Enhanced Chatbot module loaded")
    except ImportError as e:
        print(f"⚠ Chatbot module not available: {e}")
        # Fallback basic chat route if chatbot fails to load
        @app.route("/chat", methods=["GET", "POST"])
        def fallback_chat():
            if request.method == "GET":
                return render_template("enhanced_dashboard.html")
            return jsonify({
                "message": "Chat service temporarily unavailable. Please use the navigation menu.",
                "type": "error",
                "actions": [
                    {"text": "📝 Report Incident", "action": "navigate", "url": "/incidents/new"},
                    {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"}
                ]
            })
    
    # FIXED: Register all missing blueprints properly
    try:
        from routes.capa import capa_bp
        app.register_blueprint(capa_bp, url_prefix="/capa")
        blueprints_loaded.append("CAPA")
        print("✓ CAPA module loaded")
    except ImportError as e:
        print(f"⚠ CAPA module not available: {e}")
        # Create fallback CAPA routes
        @app.route("/capa")
        def fallback_capa_list():
            return render_template("fallback_module.html", 
                                 module_name="CAPA Management",
                                 description="Corrective and Preventive Actions module is not available.")
        
        @app.route("/capa/new")
        def fallback_capa_new():
            return redirect(url_for('fallback_capa_list'))
    
    try:
        from routes.risk import risk_bp  
        app.register_blueprint(risk_bp, url_prefix="/risk")
        blueprints_loaded.append("Risk Management")
        print("✓ Risk module loaded")
    except ImportError as e:
        print(f"⚠ Risk module not available: {e}")
        # Create fallback risk routes
        @app.route("/risk/assess")
        @app.route("/risk/register")
        def fallback_risk():
            return render_template("fallback_module.html",
                                 module_name="Risk Management",
                                 description="Risk assessment module is not available.")
    
    try:
        from routes.safety_concerns import safety_concerns_bp
        app.register_blueprint(safety_concerns_bp, url_prefix="/safety-concerns")
        blueprints_loaded.append("Safety Concerns")
        print("✓ Safety concerns module loaded")
    except ImportError as e:
        print(f"⚠ Safety concerns module not available: {e}")
        # Create fallback safety concerns routes
        @app.route("/safety-concerns")
        @app.route("/safety-concerns/new")
        def fallback_safety_concerns():
            return render_template("fallback_module.html",
                                 module_name="Safety Concerns",
                                 description="Safety concerns module is not available.")
    
    try:
        from routes.audits import audits_bp
        app.register_blueprint(audits_bp, url_prefix="/audits")
        blueprints_loaded.append("Audits & Inspections")
        print("✓ Audits module loaded")
    except ImportError as e:
        print(f"⚠ Audits module not available: {e}")
        # Create fallback audit routes
        @app.route("/audits")
        @app.route("/audits/new")
        def fallback_audits():
            return render_template("fallback_module.html",
                                 module_name="Audits & Inspections",
                                 description="Audits module is not available.")
    
    try:
        from routes.contractors import contractors_bp
        app.register_blueprint(contractors_bp, url_prefix="/contractors")
        blueprints_loaded.append("Contractor Management")
        print("✓ Contractors module loaded")
    except ImportError as e:
        print(f"⚠ Contractors module not available: {e}")
        # Create fallback contractor routes
        @app.route

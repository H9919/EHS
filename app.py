# app.py - Fixed version with better error handling and routing
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
    
    # Memory-optimized chatbot module with lazy loading
    try:
        from routes.chatbot import chatbot_bp
        app.register_blueprint(chatbot_bp, url_prefix="/")
        blueprints_loaded.append("Chatbot (Memory-Optimized)")
        print("✓ Memory-optimized Chatbot module loaded")
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
    
    # Other EHS modules with memory-conscious loading and fallbacks
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
        blueprints_loaded.append("Risk")
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
        blueprints_loaded.append("Audits")
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
        blueprints_loaded.append("Contractors")
        print("✓ Contractors module loaded")
    except ImportError as e:
        print(f"⚠ Contractors module not available: {e}")
        
        # Create fallback contractor routes
        @app.route("/contractors")
        @app.route("/contractors/register")
        def fallback_contractors():
            return render_template("fallback_module.html",
                                 module_name="Contractor Management",
                                 description="Contractor management module is not available.")

    @app.route("/")
    def index():
        """Main chat interface - enhanced dashboard"""
        try:
            # Try to load stats, but don't fail if service unavailable
            try:
                from services.dashboard_stats import get_dashboard_statistics
                stats = get_dashboard_statistics()
            except ImportError:
                print("⚠ Dashboard stats service not available - using defaults")
                stats = create_default_stats()
            except Exception as e:
                print(f"⚠ Error loading stats: {e}")
                stats = create_default_stats()
        except Exception as e:
            print(f"⚠ Error in index route: {e}")
            stats = create_default_stats()
        
        return render_template("enhanced_dashboard.html", stats=stats)

    @app.route("/dashboard")
    def dashboard():
        """Traditional dashboard view"""
        try:
            try:
                from services.dashboard_stats import get_dashboard_statistics
                stats = get_dashboard_statistics()
            except ImportError:
                stats = create_default_stats()
            except Exception as e:
                print(f"Error loading dashboard stats: {e}")
                stats = create_default_stats()
        except Exception as e:
            print(f"Error in dashboard route: {e}")
            stats = create_default_stats()
            
        return render_template("dashboard.html", stats=stats)
    
    # Memory-efficient API endpoints with better error handling
    @app.route("/api/stats")
    def api_stats():
        """API endpoint for dashboard statistics"""
        try:
            try:
                from services.dashboard_stats import get_dashboard_statistics
                stats = get_dashboard_statistics()
                return jsonify(stats)
            except ImportError:
                # Return basic stats if service not available
                stats = create_default_stats()
                stats["message"] = "Stats service not available in memory-optimized mode"
                stats["memory_optimized"] = True
                return jsonify(stats)
        except Exception as e:
            print(f"Error in api_stats: {e}")
            return jsonify({
                "error": "Unable to load statistics",
                "incidents": {"total": 0, "open": 0},
                "safety_concerns": {"total": 0, "open": 0},
                "capas": {"total": 0, "overdue": 0},
                "sds": {"total": 0}
            }), 500
    
    @app.route("/api/recent-activity")
    def api_recent_activity():
        """API endpoint for recent activity feed"""
        try:
            try:
                from services.dashboard_stats import get_recent_activity
                activity = get_recent_activity()
                return jsonify(activity)
            except ImportError:
                return jsonify({
                    "activities": [],
                    "message": "Activity service not available"
                })
        except Exception as e:
            print(f"Error in api_recent_activity: {e}")
            return jsonify({
                "activities": [],
                "error": "Unable to load recent activity"
            }), 500
    
    @app.route("/api/notifications")
    def api_notifications():
        """API endpoint for SLA notifications and alerts"""
        try:
            try:
                # Only load if available to save memory
                from services.notification_manager import NotificationManager
                notifier = NotificationManager()
                violations = notifier.check_sla_violations()
                return jsonify(violations)
            except ImportError:
                return jsonify({
                    "message": "Notification service not available in memory-optimized mode"
                })
        except Exception as e:
            print(f"Error in api_notifications: {e}")
            return jsonify({
                "error": "Unable to load notifications"
            }), 500
    
    @app.route("/api/search")
    def api_search():
        """Lightweight global search"""
        query = request.args.get("q", "").strip()
        if len(query) < 2:
            return jsonify({"results": [], "message": "Query too short"})
        
        try:
            results = perform_lightweight_search(query)
            return jsonify({"results": results, "query": query})
        except Exception as e:
            print(f"Error in api_search: {e}")
            return jsonify({"error": "Search temporarily unavailable"}), 500
    
    # System health and monitoring endpoints
    @app.route("/health")
    def health_check():
        """Memory-optimized health check"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "memory_optimized": True,
            "blueprints_loaded": blueprints_loaded,
            "modules": {
                "core_count": len(blueprints_loaded),
                "chatbot_type": "memory_optimized" if "Chatbot (Memory-Optimized)" in blueprints_loaded else "unavailable"
            },
            "storage": {
                "data_directory": os.path.exists("data"),
                "sds_directory": os.path.exists("data/sds"),
                "static_directory": os.path.exists("static"),
                "uploads_directory": os.path.exists("static/uploads")
            },
            "environment": {
                "sbert_enabled": os.getenv("ENABLE_SBERT", "false").lower() == "true",
                "python_version": sys.version.split()[0],
                "flask_env": os.environ.get("FLASK_ENV", "production")
            }
        }
        
        # Simple health determination
        critical_modules = ["SDS", "Incidents"]
        critical_modules_ok = all(module in blueprints_loaded for module in critical_modules)
        
        if not critical_modules_ok:
            health_status["status"] = "degraded"
            health_status["warning"] = "Some core modules not available"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code
    
    @app.route("/api/system/info")
    def system_info():
        """Memory-optimized system information"""
        info = {
            "version": "1.0.0-memory-optimized",
            "environment": os.environ.get("FLASK_ENV", "production"),
            "python_version": sys.version.split()[0],
            "memory_optimization": True,
            "features": {
                "ai_chatbot": "Chatbot (Memory-Optimized)" in blueprints_loaded,
                "rule_based_classification": True,
                "file_upload": True,
                "basic_analytics": True,
                "sbert_embeddings": os.getenv("ENABLE_SBERT", "false").lower() == "true",
                "advanced_ai": False  # Disabled for memory savings
            },
            "modules_loaded": blueprints_loaded
        }
        return jsonify(info)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "API endpoint not found"}), 404
        
        return render_template("error_404.html", 
                             blueprints_loaded=blueprints_loaded), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        print(f"Internal server error: {error}")
        traceback.print_exc()
        
        if request.path.startswith('/api/'):
            return jsonify({"error": "Internal server error"}), 500
        
        return render_template("error_500.html", 
                             blueprints_loaded=blueprints_loaded), 500
    
    @app.errorhandler(413)
    def too_large(error):
        return jsonify({"error": "File too large. Maximum size is 16MB."}

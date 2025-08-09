# app.py - FIXED VERSION with all routes properly registered and error handling
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
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
    
    blueprints_loaded = []
    
    # Register all blueprints with proper error handling
    try:
        from routes.sds import sds_bp
        app.register_blueprint(sds_bp, url_prefix="/sds")
        blueprints_loaded.append("SDS")
        print("✓ SDS module loaded")
    except ImportError as e:
        print(f"⚠ SDS module not available: {e}")
        # Create fallback SDS routes
        @app.route("/sds")
        def fallback_sds_list():
            return render_template("fallback_module.html", 
                                 module_name="SDS Library",
                                 description="Safety Data Sheets module is loading...")
        
        @app.route("/sds/upload")
        def fallback_sds_upload():
            return redirect(url_for('fallback_sds_list'))
    
    try:
        from routes.incidents import incidents_bp
        app.register_blueprint(incidents_bp, url_prefix="/incidents")
        blueprints_loaded.append("Incidents")
        print("✓ Incidents module loaded")
    except ImportError as e:
        print(f"⚠ Incidents module not available: {e}")
        # Create fallback incident routes
        @app.route("/incidents")
        def fallback_incidents_list():
            return render_template("fallback_module.html",
                                 module_name="Incident Management", 
                                 description="Incident reporting module is loading...")
        
        @app.route("/incidents/new")
        def fallback_incidents_new():
            return redirect(url_for('fallback_incidents_list'))
        
        @app.route("/incidents/<incident_id>/edit")
        def fallback_incidents_edit(incident_id):
            return redirect(url_for('fallback_incidents_list'))
    
    try:
        from routes.chatbot import chatbot_bp
        app.register_blueprint(chatbot_bp, url_prefix="/")
        blueprints_loaded.append("Enhanced Chatbot")
        print("✓ Enhanced Chatbot module loaded")
    except ImportError as e:
        print(f"⚠ Chatbot module not available: {e}")
        # Fallback chat route
        @app.route("/chat", methods=["GET", "POST"])
        def fallback_chat():
            if request.method == "GET":
                return render_template("enhanced_dashboard.html")
            return jsonify({
                "message": "Chat service temporarily unavailable. Please use the navigation menu to access other features.",
                "type": "error",
                "actions": [
                    {"text": "📝 Report Incident", "action": "navigate", "url": "/incidents/new"},
                    {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"}
                ]
            })
    
    # Register CAPA module
    try:
        from routes.capa import capa_bp
        app.register_blueprint(capa_bp, url_prefix="/capa")
        blueprints_loaded.append("CAPA")
        print("✓ CAPA module loaded")
    except ImportError as e:
        print(f"⚠ CAPA module not available: {e}")
        @app.route("/capa")
        def fallback_capa_list():
            return render_template("fallback_module.html", 
                                 module_name="CAPA Management",
                                 description="Corrective and Preventive Actions module is loading...")
        
        @app.route("/capa/new")
        def fallback_capa_new():
            return redirect(url_for('fallback_capa_list'))
        
        @app.route("/capa/<capa_id>")
        def fallback_capa_detail(capa_id):
            return redirect(url_for('fallback_capa_list'))
    
    # Register Risk module
    try:
        from routes.risk import risk_bp  
        app.register_blueprint(risk_bp, url_prefix="/risk")
        blueprints_loaded.append("Risk Management")
        print("✓ Risk module loaded")
    except ImportError as e:
        print(f"⚠ Risk module not available: {e}")
        @app.route("/risk/assess")
        def fallback_risk_assess():
            return render_template("fallback_module.html",
                                 module_name="Risk Assessment",
                                 description="Risk assessment module is loading...")
        
        @app.route("/risk/register")
        def fallback_risk_register():
            return redirect(url_for('fallback_risk_assess'))
    
    # Register Safety Concerns module
    try:
        from routes.safety_concerns import safety_concerns_bp
        app.register_blueprint(safety_concerns_bp, url_prefix="/safety-concerns")
        blueprints_loaded.append("Safety Concerns")
        print("✓ Safety concerns module loaded")
    except ImportError as e:
        print(f"⚠ Safety concerns module not available: {e}")
        @app.route("/safety-concerns")
        def fallback_safety_concerns_list():
            return render_template("fallback_module.html",
                                 module_name="Safety Concerns",
                                 description="Safety concerns module is loading...")
        
        @app.route("/safety-concerns/new")
        def fallback_safety_concerns_new():
            return redirect(url_for('fallback_safety_concerns_list'))
        
        @app.route("/safety-concerns/<concern_id>")
        def fallback_safety_concerns_detail(concern_id):
            return redirect(url_for('fallback_safety_concerns_list'))
    
    # Register Audits module
    try:
        from routes.audits import audits_bp
        app.register_blueprint(audits_bp, url_prefix="/audits")
        blueprints_loaded.append("Audits & Inspections")
        print("✓ Audits module loaded")
    except ImportError as e:
        print(f"⚠ Audits module not available: {e}")
        @app.route("/audits")
        def fallback_audits_list():
            return render_template("fallback_module.html",
                                 module_name="Audits & Inspections",
                                 description="Audits module is loading...")
        
        @app.route("/audits/new")
        def fallback_audits_new():
            return redirect(url_for('fallback_audits_list'))
        
        @app.route("/audits/<audit_id>")
        def fallback_audits_detail(audit_id):
            return redirect(url_for('fallback_audits_list'))
    
    # Register Contractors module
    try:
        from routes.contractors import contractors_bp
        app.register_blueprint(contractors_bp, url_prefix="/contractors")
        blueprints_loaded.append("Contractor Management")
        print("✓ Contractors module loaded")
    except ImportError as e:
        print(f"⚠ Contractors module not available: {e}")
        @app.route("/contractors")
        def fallback_contractors_list():
            return render_template("fallback_module.html",
                                 module_name="Contractor Management",
                                 description="Contractor management module is loading...")
        
        @app.route("/contractors/register")
        def fallback_contractors_register():
            return redirect(url_for('fallback_contractors_list'))

    @app.route("/")
    def index():
        """Main chat interface - enhanced dashboard"""
        try:
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
    
    @app.route("/api/stats")
    def api_stats():
        """API endpoint for dashboard statistics"""
        try:
            try:
                from services.dashboard_stats import get_dashboard_statistics
                stats = get_dashboard_statistics()
                return jsonify(stats)
            except ImportError:
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
    
    @app.route("/health")
    def health_check():
        """Enhanced health check with route verification"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "memory_optimized": True,
            "blueprints_loaded": blueprints_loaded,
            "modules": {
                "core_count": len(blueprints_loaded),
                "chatbot_type": "enhanced" if "Enhanced Chatbot" in blueprints_loaded else "fallback"
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
            },
            "routes": {
                "incidents": "Incidents" in blueprints_loaded,
                "safety_concerns": "Safety Concerns" in blueprints_loaded,
                "capa": "CAPA" in blueprints_loaded,
                "risk": "Risk Management" in blueprints_loaded,
                "audits": "Audits & Inspections" in blueprints_loaded,
                "contractors": "Contractor Management" in blueprints_loaded,
                "sds": "SDS" in blueprints_loaded,
                "chatbot": "Enhanced Chatbot" in blueprints_loaded
            }
        }
        
        critical_modules = ["SDS", "Incidents", "Enhanced Chatbot"]
        critical_modules_ok = any(module in blueprints_loaded for module in critical_modules)
        
        if not critical_modules_ok:
            health_status["status"] = "degraded"
            health_status["warning"] = "Some core modules not available"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code
    
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
        return jsonify({"error": "File too large. Maximum size is 16MB."}), 413
    
    # Template filters
    @app.template_filter('timeago')
    def timeago_filter(timestamp):
        """Convert timestamp to human-readable time ago"""
        try:
            if isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp)
            else:
                dt = timestamp
            
            now = datetime.now()
            diff = now - dt
            
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                return "Just now"
        except:
            return "Unknown"
    
    @app.template_filter('priority_badge')
    def priority_badge_filter(priority):
        """Convert priority to Bootstrap badge class"""
        badge_map = {
            "critical": "danger",
            "high": "warning", 
            "medium": "info",
            "low": "secondary"
        }
        return badge_map.get(str(priority).lower(), "secondary")
    
    # Jinja2 moment filter for date handling
    try:
        from datetime import datetime as dt
        
        @app.template_global()
        def moment(timestamp=None):
            """Create a moment-like object for date handling"""
            if timestamp is None:
                timestamp = dt.now()
            elif isinstance(timestamp, (int, float)):
                timestamp = dt.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                try:
                    timestamp = dt.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    timestamp = dt.now()
            
            class MomentHelper:
                def __init__(self, dt_obj):
                    self.dt = dt_obj
                
                def format(self, fmt):
                    return self.dt.strftime(fmt)
                
                def fromNow(self):
                    now = dt.now()
                    diff = now - self.dt
                    
                    if diff.days > 0:
                        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
                    elif diff.seconds > 3600:
                        hours = diff.seconds // 3600
                        return f"{hours} hour{'s' if hours != 1 else ''} ago"
                    elif diff.seconds > 60:
                        minutes = diff.seconds // 60
                        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                    else:
                        return "Just now"
            
            return MomentHelper(timestamp)
    except Exception as e:
        print(f"Warning: Could not set up moment filter: {e}")
    
    return app

def create_default_stats():
    """Create default statistics when services are unavailable"""
    return {
        "incidents": {"total": 0, "open": 0, "this_month": 0},
        "safety_concerns": {"total": 0, "open": 0, "this_month": 0},
        "capas": {"total": 0, "overdue": 0, "completed": 0},
        "sds": {"total": 0, "updated_this_month": 0},
        "audits": {"scheduled": 0, "completed": 0, "this_month": 0},
        "message": "Using default values - stats service unavailable"
    }

# Create app instance for Gunicorn/WSGI servers
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    print("=" * 60)
    print("🚀 Starting FIXED Smart EHS Management System")
    print("=" * 60)
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
    print(f"Python version: {sys.version.split()[0]}")
    print("🤖 Enhanced AI Chatbot with smart information extraction")
    print("🔧 All routes properly registered with fallback handlers")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=port, debug=debug)

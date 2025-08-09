# app.py - Fixed template path for enhanced dashboard
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request

def ensure_dirs():
    """Ensure all required directories exist"""
    directories = [
        "data/sds",
        "data/tmp", 
        "data/pdf",
        "static/qr",
        "static/uploads"  # Add uploads directory for chatbot file uploads
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def create_app():
    ensure_dirs()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
    
    # Register core blueprints with error handling
    try:
        from routes.sds import sds_bp
        app.register_blueprint(sds_bp, url_prefix="/sds")
        print("✓ SDS module loaded")
    except ImportError as e:
        print(f"⚠ SDS module not available: {e}")
    
    try:
        from routes.incidents import incidents_bp
        app.register_blueprint(incidents_bp, url_prefix="/incidents")
        print("✓ Incidents module loaded")
    except ImportError as e:
        print(f"⚠ Incidents module not available: {e}")
    
    # Register EHS module blueprints with graceful error handling
    try:
        from routes.chatbot import chatbot_bp
        app.register_blueprint(chatbot_bp, url_prefix="/")
        print("✓ Chatbot module loaded")
    except ImportError as e:
        print(f"⚠ Chatbot module not available: {e}")
    
    try:
        from routes.capa import capa_bp
        app.register_blueprint(capa_bp, url_prefix="/capa")
        print("✓ CAPA module loaded")
    except ImportError as e:
        print(f"⚠ CAPA module not available: {e}")
    
    try:
        from routes.risk import risk_bp  
        app.register_blueprint(risk_bp, url_prefix="/risk")
        print("✓ Risk module loaded")
    except ImportError as e:
        print(f"⚠ Risk module not available: {e}")
    
    try:
        from routes.safety_concerns import safety_concerns_bp
        app.register_blueprint(safety_concerns_bp, url_prefix="/safety-concerns") 
        print("✓ Safety concerns module loaded")
    except ImportError as e:
        print(f"⚠ Safety concerns module not available: {e}")
    
    try:
        from routes.audits import audits_bp
        app.register_blueprint(audits_bp, url_prefix="/audits")
        print("✓ Audits module loaded")
    except ImportError as e:
        print(f"⚠ Audits module not available: {e}")
    
    try:
        from routes.contractors import contractors_bp
        app.register_blueprint(contractors_bp, url_prefix="/contractors")
        print("✓ Contractors module loaded")
    except ImportError as e:
        print(f"⚠ Contractors module not available: {e}")

    @app.route("/")
    def index():
        """Main chat interface - enhanced dashboard"""
        try:
            from services.dashboard_stats import get_dashboard_statistics
            stats = get_dashboard_statistics()
        except:
            stats = {}
        # Use the enhanced dashboard template for the main route
        return render_template("enhanced_dashboard.html", stats=stats)

    @app.route("/dashboard")
    def dashboard():
        """Traditional dashboard view"""
        try:
            from services.dashboard_stats import get_dashboard_statistics
            stats = get_dashboard_statistics()
        except:
            stats = {}
        # Use the traditional dashboard for /dashboard route
        return render_template("dashboard.html", stats=stats)
    
    # API Endpoints with error handling
    @app.route("/api/stats")
    def api_stats():
        """API endpoint for dashboard statistics"""
        try:
            from services.dashboard_stats import get_dashboard_statistics
            stats = get_dashboard_statistics()
            return jsonify(stats)
        except ImportError:
            return jsonify({"error": "Stats service not available", "stats": {}})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/recent-activity")
    def api_recent_activity():
        """API endpoint for recent activity feed"""
        try:
            from services.dashboard_stats import get_recent_activity
            activity = get_recent_activity()
            return jsonify(activity)
        except ImportError:
            return jsonify({"activities": []})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/notifications")
    def api_notifications():
        """API endpoint for SLA notifications and alerts"""
        try:
            from services.notification_manager import NotificationManager
            notifier = NotificationManager()
            violations = notifier.check_sla_violations()
            return jsonify(violations)
        except ImportError:
            return jsonify([])
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/search")
    def api_search():
        """Global search API across all modules"""
        query = request.args.get("q", "").strip()
        if len(query) < 2:
            return jsonify({"results": [], "message": "Query too short"})
        
        try:
            results = perform_global_search(query)
            return jsonify({"results": results, "query": query})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # System health and monitoring endpoints
    @app.route("/health")
    def health_check():
        """Comprehensive health check endpoint"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "modules": {
                "incidents": check_module_available("routes.incidents"),
                "sds": check_module_available("routes.sds"),
                "chatbot": check_module_available("routes.chatbot"),
                "capa": check_module_available("routes.capa"),
                "risk": check_module_available("routes.risk"),
                "safety_concerns": check_module_available("routes.safety_concerns"),
                "audits": check_module_available("routes.audits"),
                "contractors": check_module_available("routes.contractors")
            },
            "services": {
                "embeddings": check_module_available("services.embeddings"),
                "dashboard_stats": check_module_available("services.dashboard_stats"),
                "notification_manager": check_module_available("services.notification_manager"),
                "ehs_chatbot": check_module_available("services.ehs_chatbot")
            },
            "storage": {
                "data_directory": os.path.exists("data"),
                "sds_directory": os.path.exists("data/sds"),
                "static_directory": os.path.exists("static"),
                "uploads_directory": os.path.exists("static/uploads")
            }
        }
        
        # Determine overall health
        critical_modules = ["incidents", "sds", "chatbot"]
        all_critical_modules_ok = all(health_status["modules"].get(module, False) for module in critical_modules)
        
        if not all_critical_modules_ok:
            health_status["status"] = "degraded"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code
    
    @app.route("/api/system/info")
    def system_info():
        """System information endpoint"""
        info = {
            "version": "1.0.0",
            "environment": os.environ.get("FLASK_ENV", "production"),
            "python_version": sys.version.split()[0],
            "features": {
                "ai_chatbot": check_module_available("services.ehs_chatbot"),
                "file_upload": True,
                "sds_chat": check_module_available("services.sds_chat"),
                "risk_matrix": check_module_available("services.risk_matrix"),
                "pdf_generation": check_module_available("services.pdf"),
                "qr_codes": check_module_available("services.sds_qr")
            }
        }
        return jsonify(info)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Page not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500
    
    @app.errorhandler(413)
    def too_large(error):
        return jsonify({"error": "File too large. Maximum size is 16MB."}), 413
    
    # Template filters for Jinja2
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
    
    return app

def check_module_available(module_name):
    """Check if a module is available and can be imported"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def perform_global_search(query: str) -> list:
    """Perform search across all EHS modules with error handling"""
    results = []
    query_lower = query.lower()
    
    try:
        # Search incidents
        incidents_file = Path("data/incidents.json")
        if incidents_file.exists():
            incidents = json.loads(incidents_file.read_text())
            for incident in incidents.values():
                if (query_lower in incident.get("type", "").lower() or 
                    any(query_lower in str(answer).lower() for answer in incident.get("answers", {}).values())):
                    results.append({
                        "type": "Incident",
                        "title": f"{incident.get('type', 'Unknown')} Incident",
                        "description": f"ID: {incident['id']}, Status: {incident.get('status', 'Unknown')}",
                        "url": f"/incidents/{incident['id']}/edit",
                        "module": "incidents"
                    })
        
        # Search safety concerns
        concerns_file = Path("data/safety_concerns.json")
        if concerns_file.exists():
            concerns = json.loads(concerns_file.read_text())
            for concern in concerns.values():
                if (query_lower in concern.get("title", "").lower() or
                    query_lower in concern.get("description", "").lower()):
                    results.append({
                        "type": "Safety Concern",
                        "title": concern.get("title", "Safety Concern"),
                        "description": concern.get("description", "")[:100] + "...",
                        "url": f"/safety-concerns/{concern['id']}",
                        "module": "safety_concerns"
                    })
        
        # Search SDS
        sds_file = Path("data/sds/index.json")
        if sds_file.exists():
            sds_index = json.loads(sds_file.read_text())
            for sds in sds_index.values():
                if (query_lower in sds.get("product_name", "").lower() or
                    query_lower in sds.get("file_name", "").lower()):
                    results.append({
                        "type": "SDS",
                        "title": sds.get("product_name", "Unknown Product"),
                        "description": f"File: {sds.get('file_name', 'Unknown')}",
                        "url": f"/sds/{sds['id']}",
                        "module": "sds"
                    })
        
    except Exception as e:
        print(f"Search error: {e}")
    
    return results[:20]  # Limit to 20 results

# Create app instance for Gunicorn/WSGI servers
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    print("=" * 50)
    print("🚀 Starting Smart EHS Management System")
    print("=" * 50)
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
    print(f"Python version: {sys.version.split()[0]}")
    print("🤖 AI Chatbot with file upload support enabled")
    
    app.run(host="0.0.0.0", port=port, debug=debug)

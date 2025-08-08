# Enhanced app.py - Complete EHS Management System
import os
from flask import Flask, render_template, jsonify, request
from datetime import datetime

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
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
    
    # Register existing blueprints
    from routes.sds import sds_bp
    from routes.incidents import incidents_bp
    app.register_blueprint(sds_bp, url_prefix="/sds")
    app.register_blueprint(incidents_bp, url_prefix="/incidents")
    
    # Register new EHS module blueprints with error handling
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
        app.register_blueprint(contractors_bp, url_prefix="/visitors")  # Share routes
        print("✓ Contractors module loaded")
    except ImportError as e:
        print(f"⚠ Contractors module not available: {e}")

    @app.route("/")
    def index():
        """Enhanced dashboard with AI chatbot integration"""
        try:
            from services.dashboard_stats import get_dashboard_statistics
            stats = get_dashboard_statistics()
        except ImportError:
            stats = {}
        return render_template("enhanced_dashboard.html", stats=stats)

    @app.route("/dashboard")
    def dashboard():
        """Dashboard with statistics - alias for index"""
        return index()
    
    # API Endpoints for dashboard and real-time data
    @app.route("/api/stats")
    def api_stats():
        """API endpoint for dashboard statistics"""
        try:
            from services.dashboard_stats import get_dashboard_statistics
            stats = get_dashboard_statistics()
            return jsonify(stats)
        except ImportError:
            return jsonify({"error": "Stats service not available"})
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
    
    @app.route("/api/notifications/history")
    def api_notification_history():
        """API endpoint for notification history"""
        try:
            from services.notification_manager import NotificationManager
            notifier = NotificationManager()
            days = request.args.get("days", 7, type=int)
            history = notifier.get_notification_history(days)
            return jsonify(history)
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
    
    @app.route("/api/quick-actions")
    def api_quick_actions():
        """API endpoint for context-aware quick actions"""
        try:
            actions = get_contextual_quick_actions()
            return jsonify(actions)
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
                "static_directory": os.path.exists("static")
            }
        }
        
        # Determine overall health
        all_critical_modules_ok = all([
            health_status["modules"]["incidents"],
            health_status["modules"]["sds"],
            health_status["storage"]["data_directory"]
        ])
        
        if not all_critical_modules_ok:
            health_status["status"] = "degraded"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code
    
    @app.route("/api/system/info")
    def system_info():
        """System information endpoint"""
        try:
            from services.dashboard_stats import get_dashboard_statistics
            stats = get_dashboard_statistics()
            
            info = {
                "version": "1.0.0",
                "environment": os.environ.get("FLASK_ENV", "production"),
                "python_version": os.sys.version,
                "total_records": {
                    "incidents": stats.get("incidents", {}).get("total", 0),
                    "safety_concerns": stats.get("safety_concerns", {}).get("total", 0),
                    "capas": stats.get("capas", {}).get("total", 0),
                    "audits": len(stats.get("audits", {})),
                    "sds": stats.get("sds", {}).get("total", 0),
                    "risk_assessments": stats.get("risk_assessments", {}).get("total", 0)
                },
                "features": {
                    "ai_chatbot": check_module_available("services.ehs_chatbot"),
                    "sds_chat": check_module_available("services.sds_chat"),
                    "risk_matrix": check_module_available("services.risk_matrix"),
                    "pdf_generation": check_module_available("services.pdf"),
                    "qr_codes": check_module_available("services.sds_qr")
                }
            }
            return jsonify(info)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html"), 500
    
    @app.errorhandler(413)
    def too_large(error):
        return jsonify({"error": "File too large. Maximum size is 16MB."}), 413
    
    # Template filters
    @app.template_filter('timeago')
    def timeago_filter(timestamp):
        """Convert timestamp to human-readable time ago"""
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
    
    @app.template_filter('priority_badge')
    def priority_badge_filter(priority):
        """Convert priority to Bootstrap badge class"""
        badge_map = {
            "critical": "danger",
            "high": "warning", 
            "medium": "info",
            "low": "secondary"
        }
        return badge_map.get(priority, "secondary")
    
    return app

def check_module_available(module_name):
    """Check if a

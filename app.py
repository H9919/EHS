# app.py - Memory-optimized version for Render free plan
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
    
    # Other EHS modules with memory-conscious loading
    try:
        from routes.capa import capa_bp
        app.register_blueprint(capa_bp, url_prefix="/capa")
        blueprints_loaded.append("CAPA")
        print("✓ CAPA module loaded")
    except ImportError as e:
        print(f"⚠ CAPA module not available: {e}")
    
    try:
        from routes.risk import risk_bp  
        app.register_blueprint(risk_bp, url_prefix="/risk")
        blueprints_loaded.append("Risk")
        print("✓ Risk module loaded")
    except ImportError as e:
        print(f"⚠ Risk module not available: {e}")
    
    try:
        from routes.safety_concerns import safety_concerns_bp
        app.register_blueprint(safety_concerns_bp, url_prefix="/safety-concerns")
        blueprints_loaded.append("Safety Concerns")
        print("✓ Safety concerns module loaded")
    except ImportError as e:
        print(f"⚠ Safety concerns module not available: {e}")
    
    try:
        from routes.audits import audits_bp
        app.register_blueprint(audits_bp, url_prefix="/audits")
        blueprints_loaded.append("Audits")
        print("✓ Audits module loaded")
    except ImportError as e:
        print(f"⚠ Audits module not available: {e}")
    
    try:
        from routes.contractors import contractors_bp
        app.register_blueprint(contractors_bp, url_prefix="/contractors")
        blueprints_loaded.append("Contractors")
        print("✓ Contractors module loaded")
    except ImportError as e:
        print(f"⚠ Contractors module not available: {e}")

    @app.route("/")
    def index():
        """Main chat interface - enhanced dashboard"""
        try:
            # Try to load stats, but don't fail if service unavailable
            from services.dashboard_stats import get_dashboard_statistics
            stats = get_dashboard_statistics()
        except ImportError:
            print("⚠ Dashboard stats service not available - using defaults")
            stats = {
                "incidents": {"total": 0, "open": 0},
                "safety_concerns": {"total": 0, "open": 0},
                "capas": {"total": 0, "overdue": 0}
            }
        except Exception as e:
            print(f"⚠ Error loading stats: {e}")
            stats = {}
        
        return render_template("enhanced_dashboard.html", stats=stats)

    @app.route("/dashboard")
    def dashboard():
        """Traditional dashboard view"""
        try:
            from services.dashboard_stats import get_dashboard_statistics
            stats = get_dashboard_statistics()
        except:
            stats = {}
        return render_template("dashboard.html", stats=stats)
    
    # Memory-efficient API endpoints
    @app.route("/api/stats")
    def api_stats():
        """API endpoint for dashboard statistics"""
        try:
            from services.dashboard_stats import get_dashboard_statistics
            stats = get_dashboard_statistics()
            return jsonify(stats)
        except ImportError:
            # Return basic stats if service not available
            return jsonify({
                "message": "Stats service not available in memory-optimized mode",
                "stats": {"incidents": {"total": 0}, "memory_optimized": True}
            })
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
            return jsonify({"activities": [], "message": "Activity service not available"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/notifications")
    def api_notifications():
        """API endpoint for SLA notifications and alerts"""
        try:
            # Only load if available to save memory
            from services.notification_manager import NotificationManager
            notifier = NotificationManager()
            violations = notifier.check_sla_violations()
            return jsonify(violations)
        except ImportError:
            return jsonify({"message": "Notification service not available in memory-optimized mode"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
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
            return jsonify({"error": str(e)}), 500
    
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
        return jsonify({"error": "Page not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500
    
    @app.errorhandler(413)
    def too_large(error):
        return jsonify({"error": "File too large. Maximum size is 16MB."}), 413
    
    # Memory-efficient template filters
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

def perform_lightweight_search(query: str) -> list:
    """Memory-efficient search across modules"""
    results = []
    query_lower = query.lower()
    
    try:
        # Search incidents (lightweight)
        incidents_file = Path("data/incidents.json")
        if incidents_file.exists():
            incidents = json.loads(incidents_file.read_text())
            for incident in list(incidents.values())[:20]:  # Limit to save memory
                if (query_lower in incident.get("type", "").lower() or 
                    query_lower in str(incident.get("answers", {}).get("people", "")).lower()[:100]):
                    results.append({
                        "type": "Incident",
                        "title": f"{incident.get('type', 'Unknown')} Incident",
                        "description": f"ID: {incident['id'][:8]}...",
                        "url": f"/incidents/{incident['id']}/edit",
                        "module": "incidents"
                    })
        
        # Search SDS (lightweight)
        sds_file = Path("data/sds/index.json")
        if sds_file.exists():
            sds_index = json.loads(sds_file.read_text())
            for sds in list(sds_index.values())[:10]:  # Limit to save memory
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
    
    return results[:10]  # Limit results to save memory

# Create app instance for Gunicorn/WSGI servers
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    print("=" * 60)
    print("🚀 Starting Memory-Optimized Smart EHS Management System")
    print("=" * 60)
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"SBERT enabled: {os.getenv('ENABLE_SBERT', 'false')}")
    print("🤖 Memory-optimized AI Chatbot enabled")
    print("💾 Optimized for Render free plan (512MB)")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=port, debug=debug)

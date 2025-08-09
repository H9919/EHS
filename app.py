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
    
    # Debug route for chatbot testing
    @app.route("/test-chatbot")
    def test_chatbot():
        try:
            from services.ehs_chatbot import create_chatbot
            chatbot = create_chatbot()
            if chatbot:
                # Test the exact failing conversation from your example
                response1 = chatbot.process_message("I need to report a workplace incident", "test_user")
                response2 = chatbot.process_message("a worker broke their arm in the garage while lifting a container breaking that container spilling oil all over the place and breaking a car causing 10000 dollars cost to fix the car", "test_user")
                
                return jsonify({
                    "status": "success",
                    "test_conversation": [
                        {"message": "I need to report a workplace incident", "response": response1},
                        {"message": "Complex incident description", "response": response2}
                    ],
                    "chatbot_state": {
                        "mode": chatbot.current_mode,
                        "context": chatbot.current_context,
                        "slot_state": chatbot.slot_filling_state
                    }
                })
            else:
                return jsonify({"status": "error", "message": "Chatbot creation failed"})
        except Exception as e:
            import traceback
            return jsonify({
                "status": "error", 
                "message": str(e), 
                "traceback": traceback.format_exc()
            })
    
    # Enhanced API endpoints with better error handling
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
        """Enhanced health check with route verification"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "memory_optimized": True,
            "blueprints_loaded": blueprints_loaded,
            "modules": {
                "core_count": len(blueprints_loaded),
                "chatbot_type": "enhanced" if "Enhanced Chatbot" in blueprints_loaded else "unavailable"
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
        
        # Simple health determination
        critical_modules = ["SDS", "Incidents", "Enhanced Chatbot"]
        critical_modules_ok = any(module in blueprints_loaded for module in critical_modules)
        
        if not critical_modules_ok:
            health_status["status"] = "degraded"
            health_status["warning"] = "Some core modules not available"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code
    
    @app.route("/api/system/info")
    def system_info():
        """Enhanced system information"""
        info = {
            "version": "2.0.0-enhanced",
            "environment": os.environ.get("FLASK_ENV", "production"),
            "python_version": sys.version.split()[0],
            "memory_optimization": True,
            "features": {
                "enhanced_ai_chatbot": "Enhanced Chatbot" in blueprints_loaded,
                "multi_incident_detection": True,
                "smart_information_extraction": True,
                "rule_based_classification": True,
                "file_upload": True,
                "basic_analytics": True,
                "sbert_embeddings": os.getenv("ENABLE_SBERT", "false").lower() == "true",
                "advanced_ai": False  # Disabled for memory savings
            },
            "modules_loaded": blueprints_loaded,
            "route_coverage": {
                "total_modules": 8,
                "loaded_modules": len(blueprints_loaded),
                "coverage_percentage": round((len(blueprints_loaded) / 8) * 100, 1)
            }
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

def perform_lightweight_search(query: str) -> list:
    """Memory-efficient search across modules"""
    results = []
    query_lower = query.lower()
    
    try:
        # Search incidents (lightweight)
        incidents_file = Path("data/incidents.json")
        if incidents_file.exists():
            try:
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
            except Exception as e:
                print(f"Error searching incidents: {e}")
        
        # Search SDS (lightweight)
        sds_file = Path("data/sds/index.json")
        if sds_file.exists():
            try:
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
                print(f"Error searching SDS: {e}")
        
    except Exception as e:
        print(f"Search error: {e}")
    
    return results[:10]  # Limit results to save memory

# Create app instance for Gunicorn/WSGI servers
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    print("=" * 60)
    print("🚀 Starting Enhanced Smart EHS Management System")
    print("=" * 60)
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"SBERT enabled: {os.getenv('ENABLE_SBERT', 'false')}")
    print("🤖 Enhanced AI Chatbot with multi-incident detection enabled")
    print("💾 Optimized for Render free plan (512MB)")
    print("🔧 All route handlers registered with fallbacks")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=port, debug=debug)("/chat", methods=["GET", "POST"])
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

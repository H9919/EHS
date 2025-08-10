# app.py - FIXED VERSION addressing Render deployment issues
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import traceback
import logging

# Configure logging for Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

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
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"✓ Directory created/verified: {directory}")
        except Exception as e:
            logger.warning(f"Could not create directory {directory}: {e}")

def create_app():
    """Create Flask app with comprehensive error handling"""
    logger.info("Starting Flask app creation...")
    
    try:
        ensure_dirs()
        app = Flask(__name__)
        
        # Configuration
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
        app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
        
        # Track loaded blueprints
        blueprints_loaded = []
        blueprint_errors = []
        
        # FIXED: Simplified blueprint registration with better error handling
        blueprint_configs = [
            ("routes.sds", "sds_bp", "/sds", "SDS"),
            ("routes.incidents", "incidents_bp", "/incidents", "Incidents"),
            ("routes.chatbot", "chatbot_bp", "/", "Enhanced Chatbot"),
            ("routes.capa", "capa_bp", "/capa", "CAPA"),
            ("routes.risk", "risk_bp", "/risk", "Risk Management"),
            ("routes.safety_concerns", "safety_concerns_bp", "/safety-concerns", "Safety Concerns"),
            ("routes.audits", "audits_bp", "/audits", "Audits & Inspections"),
            ("routes.contractors", "contractors_bp", "/contractors", "Contractor Management")
        ]
        
        for module_name, blueprint_name, url_prefix, display_name in blueprint_configs:
            try:
                logger.info(f"Loading {display_name} module...")
                module = __import__(module_name, fromlist=[blueprint_name])
                blueprint = getattr(module, blueprint_name)
                app.register_blueprint(blueprint, url_prefix=url_prefix)
                blueprints_loaded.append(display_name)
                logger.info(f"✓ {display_name} module loaded successfully")
            except ImportError as e:
                logger.warning(f"⚠ {display_name} module not available: {e}")
                blueprint_errors.append(f"{display_name}: Module not found - {str(e)}")
                create_fallback_routes(app, url_prefix, display_name)
            except AttributeError as e:
                logger.warning(f"⚠ {display_name} blueprint not found in module: {e}")
                blueprint_errors.append(f"{display_name}: Blueprint not found - {str(e)}")
                create_fallback_routes(app, url_prefix, display_name)
            except Exception as e:
                logger.error(f"✗ Error loading {display_name}: {e}")
                blueprint_errors.append(f"{display_name}: Load error - {str(e)}")
                create_fallback_routes(app, url_prefix, display_name)
        
        # FIXED: Core application routes with better error handling
        @app.route("/")
        def index():
            """Main dashboard route with error handling"""
            try:
                stats = get_dashboard_statistics_safe()
                return render_template("enhanced_dashboard.html", stats=stats)
            except Exception as e:
                logger.error(f"Error in index route: {e}")
                # FIXED: Try fallback template
                try:
                    return render_template("dashboard.html", stats=create_default_stats())
                except Exception as e2:
                    logger.error(f"Fallback template also failed: {e2}")
                    # Return basic HTML if templates fail
                    return """
                    <!DOCTYPE html>
                    <html>
                    <head><title>Smart EHS System</title></head>
                    <body>
                        <h1>Smart EHS Management System</h1>
                        <p>System is starting up. Some features may not be available yet.</p>
                        <ul>
                            <li><a href="/incidents">Incidents</a></li>
                            <li><a href="/safety-concerns">Safety Concerns</a></li>
                            <li><a href="/capa">CAPAs</a></li>
                            <li><a href="/sds">SDS Library</a></li>
                        </ul>
                    </body>
                    </html>
                    """

        @app.route("/dashboard")
        def dashboard():
            """Traditional dashboard view"""
            try:
                stats = get_dashboard_statistics_safe()
                return render_template("dashboard.html", stats=stats)
            except Exception as e:
                logger.error(f"Error in dashboard route: {e}")
                return jsonify({"error": "Dashboard temporarily unavailable", "stats": create_default_stats()})
        
        @app.route("/api/stats")
        def api_stats():
            """API endpoint for dashboard statistics"""
            try:
                stats = get_dashboard_statistics_safe()
                return jsonify(stats)
            except Exception as e:
                logger.error(f"Error in api_stats: {e}")
                return jsonify(create_default_stats())
        
        @app.route("/api/recent-activity")
        def api_recent_activity():
            """API endpoint for recent activity feed"""
            try:
                activity = get_recent_activity_safe()
                return jsonify(activity)
            except Exception as e:
                logger.error(f"Error in api_recent_activity: {e}")
                return jsonify({
                    "activities": [],
                    "error": "Unable to load recent activity"
                })
        
        @app.route("/health")
        def health_check():
            """Enhanced health check with detailed status"""
            try:
                health_status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "blueprints_loaded": blueprints_loaded,
                    "blueprint_errors": blueprint_errors,
                    "modules": {
                        "core_count": len(blueprints_loaded),
                        "error_count": len(blueprint_errors),
                        "chatbot_available": "Enhanced Chatbot" in blueprints_loaded
                    },
                    "storage": {
                        "data_directory": os.path.exists("data"),
                        "sds_directory": os.path.exists("data/sds"),
                        "static_directory": os.path.exists("static"),
                        "uploads_directory": os.path.exists("static/uploads")
                    },
                    "environment": {
                        "python_version": sys.version.split()[0],
                        "flask_env": os.environ.get("FLASK_ENV", "production"),
                        "port": os.environ.get("PORT", "5000"),
                        "render_service": os.environ.get("RENDER_SERVICE_NAME", "unknown")
                    }
                }
                
                # Determine overall health
                critical_modules = ["Enhanced Chatbot", "Incidents", "SDS"]
                critical_available = sum(1 for module in critical_modules if module in blueprints_loaded)
                
                if critical_available < 1:
                    health_status["status"] = "degraded"
                    health_status["warning"] = "Critical modules not available"
                elif blueprint_errors:
                    health_status["status"] = "partial"
                    health_status["warning"] = "Some modules have errors"
                
                status_code = 200 if health_status["status"] == "healthy" else 503
                return jsonify(health_status), status_code
            
            except Exception as e:
                logger.error(f"Health check error: {e}")
                return jsonify({
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        # FIXED: Enhanced error handlers
        @app.errorhandler(404)
        def not_found_error(error):
            logger.warning(f"404 error: {request.path}")
            if request.path.startswith('/api/'):
                return jsonify({"error": "API endpoint not found"}), 404
            
            try:
                return render_template("fallback_module.html", 
                                     module_name="Page",
                                     description="The page you're looking for was not found",
                                     blueprints_loaded=blueprints_loaded), 404
            except Exception:
                return "Page not found", 404
        
        @app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {error}")
            traceback.print_exc()
            
            if request.path.startswith('/api/'):
                return jsonify({"error": "Internal server error"}), 500
            
            try:
                return render_template("fallback_module.html", 
                                     module_name="System Error",
                                     description="A system error occurred",
                                     blueprints_loaded=blueprints_loaded), 500
            except Exception:
                return "Internal server error", 500
        
        @app.errorhandler(413)
        def too_large(error):
            return jsonify({"error": "File too large. Maximum size is 16MB."}), 413
        
        @app.errorhandler(502)
        def bad_gateway(error):
            logger.error(f"Bad Gateway error: {error}")
            if request.path.startswith('/api/'):
                return jsonify({"error": "Service temporarily unavailable"}), 502
            
            try:
                return render_template("fallback_module.html", 
                                     module_name="Service Unavailable",
                                     description="Service temporarily unavailable",
                                     blueprints_loaded=blueprints_loaded), 502
            except Exception:
                return "Service unavailable", 502
        
        # FIXED: Template filters with error handling
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
            except Exception:
                return "Unknown"
        
        @app.template_filter('priority_badge')
        def priority_badge_filter(priority):
            """Convert priority to Bootstrap badge class"""
            try:
                badge_map = {
                    "critical": "danger",
                    "high": "warning", 
                    "medium": "info",
                    "low": "secondary"
                }
                return badge_map.get(str(priority).lower(), "secondary")
            except Exception:
                return "secondary"
        
        # FIXED: Global template helper with error handling
        @app.template_global()
        def moment(timestamp=None):
            """Create a moment-like object for date handling"""
            try:
                if timestamp is None:
                    timestamp = datetime.now()
                elif isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp)
                elif isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        timestamp = datetime.now()
                
                class MomentHelper:
                    def __init__(self, dt_obj):
                        self.dt = dt_obj
                    
                    def format(self, fmt):
                        try:
                            return self.dt.strftime(fmt)
                        except:
                            return "Invalid date"
                    
                    def fromNow(self):
                        try:
                            now = datetime.now()
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
                        except:
                            return "Unknown time"
                
                return MomentHelper(timestamp)
            except Exception as e:
                logger.warning(f"Moment helper error: {e}")
                # Return dummy object that won't crash
                class DummyMoment:
                    def format(self, fmt): return "Date unavailable"
                    def fromNow(self): return "Time unknown"
                return DummyMoment()
        
        logger.info(f"Flask app created successfully. Loaded modules: {blueprints_loaded}")
        return app
    
    except Exception as e:
        logger.error(f"Critical error creating Flask app: {e}")
        traceback.print_exc()
        raise

def create_fallback_routes(app, url_prefix, module_name):
    """Create fallback routes for unavailable modules with unique function names"""
    try:
        # Create unique function names to avoid conflicts
        module_safe_name = module_name.replace(" ", "_").replace("&", "and").lower()
        
        # Create unique endpoint and function names
        list_endpoint = f"{module_safe_name}_fallback_list"
        new_endpoint = f"{module_safe_name}_fallback_new"
        
        def create_list_view():
            try:
                return render_template("fallback_module.html", 
                                     module_name=module_name,
                                     description=f"{module_name} module is loading...")
            except Exception:
                return f"{module_name} module is not available yet."
        
        def create_new_view():
            return redirect(url_for(list_endpoint))
        
        # Set unique function names for debugging
        create_list_view.__name__ = list_endpoint
        create_new_view.__name__ = new_endpoint
        
        # Register routes with unique endpoints
        app.add_url_rule(f"{url_prefix}", endpoint=list_endpoint, view_func=create_list_view)
        app.add_url_rule(f"{url_prefix}/", endpoint=f"{list_endpoint}_slash", view_func=create_list_view)
        app.add_url_rule(f"{url_prefix}/new", endpoint=new_endpoint, view_func=create_new_view)
        
        logger.info(f"Created fallback routes for {module_name}")
    except Exception as e:
        logger.error(f"Error creating fallback routes for {module_name}: {e}")

def get_dashboard_statistics_safe():
    """Get dashboard statistics with error handling"""
    try:
        from services.dashboard_stats import get_dashboard_statistics
        return get_dashboard_statistics()
    except ImportError:
        logger.warning("Dashboard stats service not available")
        return create_default_stats()
    except Exception as e:
        logger.warning(f"Error loading stats: {e}")
        return create_default_stats()

def get_recent_activity_safe():
    """Get recent activity with error handling"""
    try:
        from services.dashboard_stats import get_recent_activity
        return get_recent_activity()
    except ImportError:
        return {"activities": [], "message": "Activity service not available"}
    except Exception as e:
        logger.error(f"Error loading recent activity: {e}")
        return {"activities": [], "error": "Unable to load recent activity"}

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

# Create app instance for deployment
try:
    app = create_app()
    logger.info("App instance created successfully")
except Exception as e:
    logger.error(f"Failed to create app instance: {e}")
    # Create minimal Flask app as fallback
    app = Flask(__name__)
    
    @app.route("/")
    def minimal_index():
        return "EHS System is starting up. Please wait..."
    
    @app.route("/health")
    def minimal_health():
        return jsonify({"status": "starting", "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Smart EHS Management System")
    logger.info("=" * 60)
    logger.info(f"Port: {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
    logger.info(f"Python version: {sys.version.split()[0]}")
    logger.info("=" * 60)
    
    try:
        app.run(host="0.0.0.0", port=port, debug=debug)
    except Exception as e:
        logger.error(f"Failed to start app: {e}")
        sys.exit(1)

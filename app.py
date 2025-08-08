import os
from flask import Flask, render_template, jsonify
from routes.sds import sds_bp
from routes.incidents import incidents_bp

def ensure_dirs():
    """Ensure all required directories exist"""
    directories = [
        "data/sds",
        "data/tmp", 
        "data/pdf",
        "static/qr"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def create_app():
    ensure_dirs()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
    
    # Register existing blueprints
    app.register_blueprint(sds_bp, url_prefix="/sds")
    app.register_blueprint(incidents_bp, url_prefix="/incidents")
    
    # Register new EHS module blueprints
    try:
        from routes.chatbot import chatbot_bp
        app.register_blueprint(chatbot_bp, url_prefix="/")
    except ImportError:
        print("Chatbot module not available - install missing dependencies")
    
    try:
        from routes.capa import capa_bp
        app.register_blueprint(capa_bp, url_prefix="/capa")
    except ImportError:
        print("CAPA module not available")
    
    try:
        from routes.risk import risk_bp  
        app.register_blueprint(risk_bp, url_prefix="/risk")
    except ImportError:
        print("Risk module not available")
    
    try:
        from routes.safety_concerns import safety_concerns_bp
        app.register_blueprint(safety_concerns_bp, url_prefix="/safety-concerns") 
    except ImportError:
        print("Safety concerns module not available")
    
    try:
        from routes.audits import audits_bp
        app.register_blueprint(audits_bp, url_prefix="/audits")
    except ImportError:
        print("Audits module not available")

    @app.route("/")
    def index():
        """Enhanced dashboard with AI chatbot integration"""
        return render_template("enhanced_dashboard.html")

    @app.route("/dashboard")
    def dashboard():
        """Dashboard with statistics"""
        try:
            from services.dashboard_stats import get_dashboard_statistics
            stats = get_dashboard_statistics()
        except ImportError:
            stats = {}
        return render_template("enhanced_dashboard.html", stats=stats)
    
    @app.route("/api/stats")
    def api_stats():
        """API endpoint for dashboard statistics"""
        try:
            from services.dashboard_stats import get_dashboard_statistics
            stats = get_dashboard_statistics()
            return jsonify(stats)
        except ImportError:
            return jsonify({"error": "Stats service not available"})
    
    @app.route("/api/notifications")
    def api_notifications():
        """API endpoint for SLA notifications"""
        try:
            from services.notification_manager import NotificationManager
            notifier = NotificationManager()
            violations = notifier.check_sla_violations()
            return jsonify(violations)
        except ImportError:
            return jsonify([])
    
    @app.route("/health")
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "modules": {
                "incidents": True,
                "sds": True,
                "chatbot": check_module_available("routes.chatbot"),
                "capa": check_module_available("routes.capa"),
                "risk": check_module_available("routes.risk"),
                "safety_concerns": check_module_available("routes.safety_concerns"),
                "audits": check_module_available("routes.audits")
            }
        })

    return app

def check_module_available(module_name):
    """Check if a module is available"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

# Create app instance for Gunicorn/WSGI servers
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

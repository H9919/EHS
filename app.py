import os
from flask import Flask, redirect, url_for, render_template
from routes.sds import sds_bp
from routes.incidents import incidents_bp

def ensure_dirs():
    os.makedirs("data/sds", exist_ok=True)
    os.makedirs("data/tmp", exist_ok=True)
    os.makedirs("static/qr", exist_ok=True)

def create_app():
    ensure_dirs()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
    app.register_blueprint(sds_bp, url_prefix="/sds")
    app.register_blueprint(incidents_bp, url_prefix="/incidents")

    @app.route("/")
    def index():
        # Simple dashboard tiles
        return render_template("dashboard.html")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)


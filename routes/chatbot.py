# routes/chatbot.py - Updated with file upload support
import json
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, render_template
from services.ehs_chatbot import EHSChatbot

chatbot_bp = Blueprint("chatbot", __name__)
chatbot = EHSChatbot()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}
UPLOAD_FOLDER = Path("static/uploads")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_dir():
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

@chatbot_bp.route("/chat", methods=["GET", "POST"])
def chat_interface():
    if request.method == "GET":
        return render_template("enhanced_dashboard.html")
    
    # Handle both JSON and form data (for file uploads)
    if request.is_json:
        data = request.get_json()
        user_message = data.get("message", "")
        user_id = data.get("user_id")
        context = data.get("context", {})
        uploaded_file = None
    else:
        user_message = request.form.get("message", "")
        user_id = request.form.get("user_id")
        context_str = request.form.get("context", "{}")
        try:
            context = json.loads(context_str)
        except:
            context = {}
        
        # Handle file upload
        uploaded_file = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                ensure_upload_dir()
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                import time
                timestamp = str(int(time.time()))
                name, ext = os.path.splitext(filename)
                unique_filename = f"{name}_{timestamp}{ext}"
                file_path = UPLOAD_FOLDER / unique_filename
                file.save(file_path)
                
                uploaded_file = {
                    "filename": filename,
                    "path": str(file_path),
                    "type": file.content_type,
                    "size": os.path.getsize(file_path)
                }
    
    # Update context with file info if present
    if uploaded_file:
        context["uploaded_file"] = uploaded_file
        # If no message but file uploaded, create a contextual message
        if not user_message.strip():
            file_type = uploaded_file["type"]
            if file_type.startswith('image/'):
                user_message = f"I've uploaded an image ({uploaded_file['filename']}) for my report or incident"
            elif file_type == 'application/pdf':
                user_message = f"I've uploaded a PDF document ({uploaded_file['filename']})"
            else:
                user_message = f"I've uploaded a file ({uploaded_file['filename']})"
    
    response = chatbot.process_message(user_message, user_id, context)
    return jsonify(response)

@chatbot_bp.route("/chat/history")
def chat_history():
    return jsonify(chatbot.conversation_history[-20:])

@chatbot_bp.route("/chat/summary")
def chat_summary():
    return jsonify(chatbot.get_conversation_summary())

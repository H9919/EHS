from flask import Blueprint, request, jsonify, render_template
from services.ehs_chatbot import EHSChatbot

chatbot_bp = Blueprint("chatbot", __name__)
chatbot = EHSChatbot()

@chatbot_bp.route("/chat", methods=["GET", "POST"])
def chat_interface():
    if request.method == "GET":
        return render_template("chatbot.html")
    
    data = request.get_json()
    user_message = data.get("message", "")
    user_id = data.get("user_id")
    
    response = chatbot.process_message(user_message, user_id)
    return jsonify(response)

@chatbot_bp.route("/chat/history")
def chat_history():
    return jsonify(chatbot.conversation_history[-20:])

@chatbot_bp.route("/chat/summary")
def chat_summary():
    return jsonify(chatbot.get_conversation_summary())

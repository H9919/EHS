# 1. Fix routes/chatbot.py - Enhanced error handling and state management
# =============================================================================

def parse_request_data():
    """Efficiently parse request data with detailed debugging"""
    try:
        print(f"DEBUG: Parsing request - Content-Type: {request.content_type}")
        print(f"DEBUG: Is JSON: {request.is_json}")
        print(f"DEBUG: Form data: {dict(request.form)}")
        print(f"DEBUG: Files: {list(request.files.keys())}")
        
        if request.is_json:
            data = request.get_json()
            user_message = data.get("message", "")
            user_id = data.get("user_id", "default_user")
            context = data.get("context", {})
            uploaded_file = None
            print(f"DEBUG: JSON data parsed - message: '{user_message}', context: {context}")
        else:
            user_message = request.form.get("message", "")
            user_id = request.form.get("user_id", "default_user")
            context = {}
            
            print(f"DEBUG: Form data parsed - message: '{user_message}'")
            
            # Handle file upload
            uploaded_file = None
            if 'file' in request.files:
                file = request.files['file']
                print(f"DEBUG: File upload detected - filename: {file.filename}, type: {file.content_type}")
                if file and file.filename and allowed_file(file.filename):
                    uploaded_file = handle_file_upload_efficient(file)
                    print(f"DEBUG: File processed successfully: {uploaded_file}")
                else:
                    print("DEBUG: File rejected - invalid filename or type")
        
        # Update context with file info if present
        if uploaded_file:
            context["uploaded_file"] = uploaded_file
            if not user_message.strip():
                user_message = f"I've uploaded a file ({uploaded_file['filename']})"
                print(f"DEBUG: Generated message for file upload: '{user_message}'")
        
        return user_message, user_id, context, uploaded_file
        
    except Exception as e:
        print(f"ERROR: Failed to parse request data: {e}")
        import traceback
        traceback.print_exc()
        return "", "default_user", {}, None

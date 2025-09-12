import os
import google.generativeai as genai
from flask import current_app

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

def load_knowledge_base():
    """Load and return content from uploaded knowledge base files."""
    try:
        knowledge_content = []
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads/knowledge/')
        
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                if filename.endswith('.txt'):
                    filepath = os.path.join(upload_folder, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                knowledge_content.append(content)
                    except Exception:
                        continue  # Skip problematic files
        
        return "\n\n".join(knowledge_content) if knowledge_content else ""
    except Exception:
        return ""

def get_ai_response(prompt, context=""):
    try:
        # Load knowledge base content
        knowledge_base = load_knowledge_base()
        
        # Build the full prompt with knowledge base context
        full_prompt_parts = []
        
        if knowledge_base:
            full_prompt_parts.append("Ma'lumotlar bazasi:")
            full_prompt_parts.append(knowledge_base)
            full_prompt_parts.append("\n---\n")
        
        if context:
            full_prompt_parts.append("Suhbat tarixi:")
            full_prompt_parts.append(context)
            full_prompt_parts.append("\n---\n")
        
        full_prompt_parts.append("Iltimos, yuqoridagi ma'lumotlar asosida javob bering.")
        full_prompt_parts.append(f"Foydalanuvchi: {prompt}")
        
        full_prompt = "\n".join(full_prompt_parts)
        
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        return "Kechirasiz, AI hozir ishlamayapti. Keyinroq qaytadan urinib ko'ring."
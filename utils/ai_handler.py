import google.generativeai as genai
import openai
from flask import current_app
import json
import time
from typing import Optional, Dict, Any

class AIHandler:
    """Dual AI handler - Gemini va OpenAI"""
    
    def __init__(self):
        self.setup_gemini()
    
    def setup_gemini(self):
        """Gemini AI ni sozlash"""
        if current_app.config.get('GEMINI_API_KEY'):
            genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
        
    def setup_openai(self, api_key: str):
        """OpenAI ni sozlash"""
        openai.api_key = api_key
    
    def generate_response(self, message: str, knowledge_base_content: str = "", 
                         ai_provider: str = "gemini", model: str = None,
                         openai_api_key: str = None, language: str = "uz") -> Dict[str, Any]:
        """
        AI javob yaratish
        
        Args:
            message: Foydalanuvchi xabari
            knowledge_base_content: Bilimlar bazasi tarkibi
            ai_provider: gemini yoki openai
            model: AI model nomi
            openai_api_key: OpenAI API kalit (agar OpenAI ishlatilsa)
            language: Javob tili (uz, ru, en)
            
        Returns:
            Dict: {'response': str, 'success': bool, 'error': str, 'provider': str, 'response_time': float}
        """
        start_time = time.time()
        
        try:
            if ai_provider == "openai" and openai_api_key:
                return self._generate_openai_response(
                    message, knowledge_base_content, model or "gpt-3.5-turbo", 
                    openai_api_key, language, start_time
                )
            else:
                return self._generate_gemini_response(
                    message, knowledge_base_content, model or "gemini-1.5-flash", 
                    language, start_time
                )
                
        except Exception as e:
            return {
                'response': self._get_error_message(language),
                'success': False,
                'error': str(e),
                'provider': ai_provider,
                'response_time': time.time() - start_time
            }
    
    def _generate_gemini_response(self, message: str, knowledge_base: str, 
                                 model: str, language: str, start_time: float) -> Dict[str, Any]:
        """Gemini AI bilan javob yaratish"""
        try:
            genai_model = genai.GenerativeModel(model)
            
            # Prompt yaratish
            prompt = self._build_prompt(message, knowledge_base, language)
            
            # AI dan javob olish
            response = genai_model.generate_content(prompt)
            
            return {
                'response': response.text,
                'success': True,
                'error': None,
                'provider': 'gemini',
                'response_time': time.time() - start_time
            }
            
        except Exception as e:
            raise Exception(f"Gemini API xato: {str(e)}")
    
    def _generate_openai_response(self, message: str, knowledge_base: str, 
                                 model: str, api_key: str, language: str, start_time: float) -> Dict[str, Any]:
        """OpenAI bilan javob yaratish (v1.0.0+ API)"""
        try:
            from openai import OpenAI
            
            # OpenAI client yaratish
            client = OpenAI(api_key=api_key)
            
            # Prompt yaratish
            system_prompt = self._build_system_prompt(knowledge_base, language)
            
            # OpenAI dan javob olish
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return {
                'response': response.choices[0].message.content,
                'success': True,
                'error': None,
                'provider': 'openai',
                'response_time': time.time() - start_time
            }
            
        except Exception as e:
            raise Exception(f"OpenAI API xato: {str(e)}")
    
    def _build_system_prompt(self, knowledge_base: str, language: str) -> str:
        """AI uchun system prompt yaratish"""
        
        # Til bo'yicha yo'riqnomalar
        language_instructions = {
            'uz': """
Sen professional AI yordamchisan. O'zbek tilida javob ber.
Quyidagi bilimlar bazasidan foydalanib, aniq va foydali javob ber.
Agar bilimlar bazasida javob yo'q bo'lsa, umumiy bilimlaringdan foydalanib yordam ber.
            """,
            'ru': """
Ты профессиональный AI помощник. Отвечай на русском языке.
Используя приведенную базу знаний, дай точный и полезный ответ.
Если в базе знаний нет ответа, помоги используя свои общие знания.
            """,
            'en': """
You are a professional AI assistant. Respond in English.
Using the provided knowledge base, give an accurate and helpful answer.
If the knowledge base doesn't contain the answer, help using your general knowledge.
            """
        }
        
        instruction = language_instructions.get(language, language_instructions['uz'])
        
        if knowledge_base:
            system_prompt = f"""
{instruction}

BILIMLAR BAZASI:
{knowledge_base}

QOIDALAR:
1. Avval bilimlar bazasini tekshir
2. Agar javob bor bo'lsa, uni ishlatib javob ber
3. Agar yo'q bo'lsa, umumiy bilimlaringdan yordam ber
4. Har doim foydali va aniq javob ber
5. Javobni {language} tilida ber
"""
        else:
            system_prompt = f"""
{instruction}

Foydalanuvchiga yordam ber va javobni {language} tilida ber.
"""
        
        return system_prompt
    
    def _build_prompt(self, message: str, knowledge_base: str, language: str) -> str:
        """Gemini uchun prompt yaratish (backward compatibility)"""
        system_prompt = self._build_system_prompt(knowledge_base, language)
        return f"{system_prompt}\n\nFOYDALANUVCHI SAVOLI: {message}"
    
    def _get_error_message(self, language: str) -> str:
        """Xato xabarlari"""
        error_messages = {
            'uz': "Kechirasiz, hozir javob bera olmayapman. Iltimos, keyinroq urinib ko'ring.",
            'ru': "Извините, сейчас не могу ответить. Пожалуйста, попробуйте позже.",
            'en': "Sorry, I can't respond right now. Please try again later."
        }
        return error_messages.get(language, error_messages['uz'])
    
    @staticmethod
    def validate_openai_api_key(api_key: str) -> bool:
        """OpenAI API kalitini tekshirish (v1.0.0+ API)"""
        try:
            from openai import OpenAI
            
            # Client yaratish va test qilish
            client = OpenAI(api_key=api_key)
            
            # Test so'rov yuborish - models ro'yxatini olish
            models = client.models.list()
            return True
        except:
            return False
    
    @staticmethod
    def get_available_models(provider: str) -> list:
        """Mavjud modellar ro'yxati"""
        if provider == "gemini":
            return ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
        elif provider == "openai":
            return ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]
        return []

# Backward compatibility uchun eski funksiyalarni saqlash
def get_ai_response(prompt, context=""):
    """Eski AI funksiya - backward compatibility uchun"""
    handler = AIHandler()
    result = handler.generate_response(prompt, context)
    return result.get('response', 'Kechirasiz, AI hozir ishlamayapti.')

def load_knowledge_base():
    """Eski knowledge base funksiya - backward compatibility uchun"""
    return ""  # Yangi tizimda database orqali amalga oshiriladi
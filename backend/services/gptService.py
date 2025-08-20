import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from backend.models.complaintModel import ComplaintData
from utils.textCleaner import TextCleaner
from utils.timeUtils import TimeUtils
from backend.services.ai.ai_manager import AIManager

logger = logging.getLogger(__name__)

class GPTService:
    """Service for OpenAI GPT API interactions"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        
        # AI manager/provider
        self.ai_manager = AIManager()
        # Keep OpenAI client for health-check legacy path
        if self.api_key:
            try:
                self.client = AsyncOpenAI(api_key=self.api_key)
            except Exception:
                self.client = None
        else:
            self.client = None
        
        self.text_cleaner = TextCleaner()
        self.time_utils = TimeUtils()
        
        # Fallback responses for when GPT is unavailable
        self.fallback_responses = {
            "greeting": [
                "Hello! I'm SafeChild, your safety companion. How can I help you today?",
                "Hi there! I'm here to help you stay safe. What would you like to know?",
                "Welcome! I'm SafeChild, ready to help with safety questions and concerns."
            ],
            "safety_tip": [
                "Remember: Your body belongs to you. No one should touch you in ways that make you uncomfortable.",
                "Always tell a trusted adult if something doesn't feel right.",
                "It's okay to say 'NO' if someone makes you feel unsafe or uncomfortable."
            ],
            "emergency": [
                "If you're in immediate danger, call emergency services right away.",
                "Tell a trusted adult immediately if you feel unsafe.",
                "Your safety is the most important thing. Don't hesitate to ask for help."
            ],
            "general": [
                "I'm here to help you learn about safety. What specific question do you have?",
                "That's a great question about safety. Let me help you understand this better.",
                "Safety is important for everyone. I'm happy to help you learn more."
            ]
        }
    
    async def get_chatbot_response(
        self, 
        message: str, 
        chat_history: List[Dict[str, str]], 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get chatbot response from GPT API"""
        try:
            provider = self.ai_manager.get_provider()
            
            # Clean and validate input
            cleaned_message = self.text_cleaner.clean_text(message)
            if not cleaned_message:
                return {
                    "success": False,
                    "error": "Invalid message content",
                    "response": "I couldn't understand your message. Could you please rephrase it?"
                }
            
            # Prepare conversation context
            messages = self._prepare_conversation_context(cleaned_message, chat_history, user_context)
            
            # Call OpenAI API
            ai = await provider.chat(messages, {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "timeout": 30.0
            })
            ai_response = ai.get("content")
            if not ai_response:
                return await self._get_fallback_response(message, "general")
            
            # Clean and validate response
            cleaned_response = self.text_cleaner.clean_text(ai_response)
            
            return {
                "success": True,
                "response": cleaned_response,
                "model": ai.get("model"),
                "tokens_used": ai.get("usage", {}).get("total_tokens") if ai.get("usage") else None,
                "timestamp": self.time_utils.get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error getting chatbot response: {e}")
            return await self._get_fallback_response(message, "general")
    
    async def generate_complaint_draft(
        self, 
        incident_data: Dict[str, Any], 
        template_type: str = "formal"
    ) -> Dict[str, Any]:
        """Generate complaint draft using GPT API"""
        try:
            provider = self.ai_manager.get_provider()
            
            # Clean incident data
            cleaned_data = self._clean_incident_data(incident_data)
            
            # Prepare prompt for complaint generation
            prompt = self._prepare_complaint_prompt(cleaned_data, template_type)
            
            # Call OpenAI API
            ai = await provider.chat([
                {"role": "system", "content": "You are a legal document generator specializing in child safety incident reports. Generate professional, clear, and legally appropriate complaint drafts."},
                {"role": "user", "content": prompt}
            ], {
                "model": self.model,
                "max_tokens": self.max_tokens * 2,
                "temperature": 0.3,
                "timeout": 60.0
            })
            complaint_draft = ai.get("content")
            if not complaint_draft:
                return await self._generate_fallback_complaint(incident_data, template_type)
            
            # Clean and validate response
            cleaned_draft = self.text_cleaner.clean_text(complaint_draft)
            
            return {
                "success": True,
                "complaint_draft": cleaned_draft,
                "template_type": template_type,
                "model": ai.get("model"),
                "tokens_used": ai.get("usage", {}).get("total_tokens") if ai.get("usage") else None,
                "timestamp": self.time_utils.get_current_timestamp(),
                "metadata": {
                    "incident_type": cleaned_data.get("incident_type"),
                    "priority": cleaned_data.get("priority"),
                    "generated_by": "gpt"
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating complaint draft: {e}")
            return await self._generate_fallback_complaint(incident_data, template_type)
    
    async def analyze_safety_concern(
        self, 
        concern_text: str, 
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """Analyze safety concern using GPT API"""
        try:
            provider = self.ai_manager.get_provider()
            
            # Clean input text
            cleaned_text = self.text_cleaner.clean_text(concern_text)
            if not cleaned_text:
                return {
                    "success": False,
                    "error": "Invalid concern text",
                    "analysis": "I couldn't analyze the provided text. Please provide more details."
                }
            
            # Prepare analysis prompt
            prompt = self._prepare_analysis_prompt(cleaned_text, analysis_type)
            
            # Call OpenAI API
            ai = await provider.chat([
                {"role": "system", "content": "You are a child safety expert. Analyze safety concerns and provide appropriate guidance and recommendations."},
                {"role": "user", "content": prompt}
            ], {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": 0.5,
                "timeout": 45.0
            })
            analysis = ai.get("content")
            if not analysis:
                return await self._get_fallback_safety_analysis(concern_text, analysis_type)
            
            # Clean and validate response
            cleaned_analysis = self.text_cleaner.clean_text(analysis)
            
            return {
                "success": True,
                "analysis": cleaned_analysis,
                "analysis_type": analysis_type,
                "model": ai.get("model"),
                "tokens_used": ai.get("usage", {}).get("total_tokens") if ai.get("usage") else None,
                "timestamp": self.time_utils.get_current_timestamp(),
                "risk_level": self._assess_risk_level(cleaned_text),
                "recommendations": self._extract_recommendations(cleaned_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing safety concern: {e}")
            return await self._get_fallback_safety_analysis(concern_text, analysis_type)
    
    def _prepare_conversation_context(
        self, 
        message: str, 
        chat_history: List[Dict[str, str]], 
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Prepare conversation context for GPT API"""
        messages = []
        
        # Add system message
        system_message = self._get_system_prompt(user_context)
        messages.append({"role": "system", "content": system_message})
        
        # Add chat history (limit to last 10 messages to avoid token limits)
        for msg in chat_history[-10:]:
            if msg.get("role") == "user":
                messages.append({"role": "user", "content": msg.get("content", "")})
            elif msg.get("role") == "assistant":
                messages.append({"role": "assistant", "content": msg.get("content", "")})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        return messages
    
    def _get_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Get system prompt for GPT API"""
        base_prompt = """You are SafeChild, a friendly and supportive AI companion designed to help children learn about safety and provide guidance in difficult situations.

Your core responsibilities:
1. Provide age-appropriate safety education
2. Offer emotional support and guidance
3. Direct children to trusted adults when needed
4. Maintain a calm, reassuring tone
5. Never provide medical or legal advice

Safety guidelines:
- Always prioritize child safety
- Encourage communication with trusted adults
- Provide clear, simple explanations
- Use positive reinforcement
- Maintain appropriate boundaries

Emergency response:
- If a child mentions immediate danger, guide them to call emergency services
- Encourage them to tell a trusted adult immediately
- Provide clear next steps for safety

Remember: You are a supportive companion, not a replacement for professional help or trusted adults."""

        if user_context:
            if user_context.get("age_group"):
                base_prompt += f"\n\nUser age group: {user_context['age_group']}"
            if user_context.get("safety_topics"):
                base_prompt += f"\n\nFocus areas: {', '.join(user_context['safety_topics'])}"
        
        return base_prompt
    
    def _prepare_complaint_prompt(
        self, 
        incident_data: Dict[str, Any], 
        template_type: str
    ) -> str:
        """Prepare prompt for complaint generation"""
        prompt = f"""Generate a {template_type} complaint draft based on the following incident data:

Incident Type: {incident_data.get('incident_type', 'Unknown')}
Priority Level: {incident_data.get('priority', 'Medium')}
Date: {incident_data.get('date', 'Unknown')}

Child Information:
- Age: {incident_data.get('child_age', 'Unknown')}
- Gender: {incident_data.get('child_gender', 'Unknown')}

Incident Details:
{incident_data.get('description', 'No description provided')}

Guardian Information:
- Name: {incident_data.get('guardian_name', 'Unknown')}
- Contact: {incident_data.get('guardian_contact', 'Unknown')}

Please generate a professional, clear, and legally appropriate complaint draft that includes:
1. Clear incident description
2. Relevant details and context
3. Requested actions or outcomes
4. Professional tone and language

Template Style: {template_type}"""

        return prompt
    
    def _prepare_analysis_prompt(self, concern_text: str, analysis_type: str) -> str:
        """Prepare prompt for safety concern analysis"""
        prompt = f"""Analyze the following safety concern and provide guidance:

Concern Text: {concern_text}
Analysis Type: {analysis_type}

Please provide:
1. Risk assessment and level
2. Immediate safety recommendations
3. Long-term safety measures
4. When to seek professional help
5. Resources and support options

Focus on practical, actionable advice that prioritizes child safety."""

        return prompt
    
    def _extract_response_content(self, response: ChatCompletion) -> Optional[str]:
        """Extract content from OpenAI API response"""
        try:
            if not response.choices:
                return None
            
            choice: Choice = response.choices[0]
            if not choice.message:
                return None
            
            message: ChatCompletionMessage = choice.message
            return message.content
            
        except Exception as e:
            logger.error(f"Error extracting response content: {e}")
            return None
    
    def _clean_incident_data(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate incident data"""
        cleaned_data = {}
        
        for key, value in incident_data.items():
            if isinstance(value, str):
                cleaned_data[key] = self.text_cleaner.clean_text(value)
            else:
                cleaned_data[key] = value
        
        return cleaned_data
    
    def _assess_risk_level(self, text: str) -> str:
        """Assess risk level based on text content"""
        text_lower = text.lower()
        
        # High-risk keywords
        high_risk_keywords = [
            "immediate danger", "emergency", "hurt", "pain", "bleeding",
            "unconscious", "choking", "poison", "fire", "weapon"
        ]
        
        # Medium-risk keywords
        medium_risk_keywords = [
            "uncomfortable", "scared", "worried", "strange", "suspicious",
            "bullying", "harassment", "inappropriate", "touch"
        ]
        
        for keyword in high_risk_keywords:
            if keyword in text_lower:
                return "high"
        
        for keyword in medium_risk_keywords:
            if keyword in text_lower:
                return "medium"
        
        return "low"
    
    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract recommendations from analysis text"""
        recommendations = []
        
        # Simple extraction based on common patterns
        lines = analysis.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                recommendations.append(line.lstrip('-•*1234567890. '))
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    async def _get_fallback_response(self, message: str, response_type: str) -> Dict[str, Any]:
        """Get fallback response when GPT is unavailable"""
        import random
        
        responses = self.fallback_responses.get(response_type, self.fallback_responses["general"])
        fallback_response = random.choice(responses)
        
        return {
            "success": False,
            "response": fallback_response,
            "fallback": True,
            "error": "GPT service unavailable, using fallback response",
            "timestamp": self.time_utils.get_current_timestamp()
        }
    
    async def _generate_fallback_complaint(
        self, 
        incident_data: Dict[str, Any], 
        template_type: str
    ) -> Dict[str, Any]:
        """Generate fallback complaint when GPT is unavailable"""
        fallback_draft = f"""COMPLAINT DRAFT - {template_type.upper()}

Date: {self.time_utils.get_current_timestamp()}
Incident Type: {incident_data.get('incident_type', 'Child Safety Incident')}
Priority: {incident_data.get('priority', 'Medium')}

DESCRIPTION:
{incident_data.get('description', 'Incident description not provided')}

CHILD INFORMATION:
Age: {incident_data.get('child_age', 'Unknown')}
Gender: {incident_data.get('child_gender', 'Unknown')}

GUARDIAN INFORMATION:
Name: {incident_data.get('guardian_name', 'Unknown')}
Contact: {incident_data.get('guardian_contact', 'Unknown')}

REQUESTED ACTION:
Please investigate this incident and take appropriate action to ensure child safety.

Note: This is a fallback draft. For more detailed legal assistance, please consult with a legal professional."""

        return {
            "success": False,
            "complaint_draft": fallback_draft,
            "template_type": template_type,
            "fallback": True,
            "error": "GPT service unavailable, using fallback complaint",
            "timestamp": self.time_utils.get_current_timestamp(),
            "metadata": {
                "incident_type": incident_data.get("incident_type"),
                "priority": incident_data.get("priority"),
                "generated_by": "fallback"
            }
        }
    
    async def _get_fallback_safety_analysis(
        self, 
        concern_text: str, 
        analysis_type: str
    ) -> Dict[str, Any]:
        """Get fallback safety analysis when GPT is unavailable"""
        fallback_analysis = f"""SAFETY ANALYSIS - {analysis_type.upper()}

Concern: {concern_text[:100]}...

General Safety Recommendations:
1. Always prioritize immediate safety
2. Contact trusted adults or authorities if needed
3. Document any incidents or concerns
4. Follow established safety protocols
5. Seek professional guidance when appropriate

Risk Assessment: Medium (requires professional evaluation)

Note: This is a fallback analysis. For specific safety concerns, please consult with safety professionals or authorities."""

        return {
            "success": False,
            "analysis": fallback_analysis,
            "analysis_type": analysis_type,
            "fallback": True,
            "error": "GPT service unavailable, using fallback analysis",
            "timestamp": self.time_utils.get_current_timestamp(),
            "risk_level": "medium",
            "recommendations": [
                "Prioritize immediate safety",
                "Contact trusted adults",
                "Document incidents",
                "Follow safety protocols",
                "Seek professional guidance"
            ]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check GPT service health"""
        try:
            if not self.client:
                return {
                    "status": "unavailable",
                    "error": "OpenAI client not initialized",
                    "timestamp": self.time_utils.get_current_timestamp()
                }
            
            # Test API connection with a simple request
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for health check
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                timeout=10.0
            )
            
            return {
                "status": "healthy",
                "model": self.model,
                "api_working": True,
                "timestamp": self.time_utils.get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"GPT service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": self.time_utils.get_current_timestamp()
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get GPT service usage statistics"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "api_key_configured": bool(self.api_key),
            "client_available": bool(self.client),
            "fallback_responses_available": bool(self.fallback_responses)
        }

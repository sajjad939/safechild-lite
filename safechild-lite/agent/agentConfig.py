import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentConfig:
    """Configuration class for AI agents and prompts"""
    
    def __init__(self, config_path: str = "agent/config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.prompts = self.load_prompts()
        self.schemas = self.load_schemas()
        
        # Default configuration
        self.default_config = {
            "openai": {
                "model": "gpt-4",
                "max_tokens": 1000,
                "temperature": 0.7,
                "timeout": 30,
                "retry_attempts": 3
            },
            "safety": {
                "content_filter": True,
                "sensitive_info_removal": True,
                "age_appropriate_content": True,
                "emergency_keywords": [
                    "hurt", "pain", "bleeding", "unconscious", "not breathing",
                    "choking", "fire", "explosion", "weapon", "gun", "knife",
                    "attack", "assault", "kidnapping", "missing", "lost"
                ]
            },
            "chatbot": {
                "max_conversation_length": 50,
                "context_window": 10,
                "response_timeout": 15,
                "fallback_responses": True,
                "safety_checks": True
            },
            "complaint_generation": {
                "template_based": True,
                "ai_enhanced": True,
                "legal_terminology": True,
                "professional_tone": True,
                "max_length": 2000
            },
            "emergency_detection": {
                "keyword_monitoring": True,
                "sentiment_analysis": True,
                "urgency_scoring": True,
                "auto_escalation": False,
                "threshold_high": 0.7,
                "threshold_critical": 0.9
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info(f"Configuration loaded from {self.config_path}")
                    return config
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                return self.default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return self.default_config
    
    def load_prompts(self) -> Dict[str, str]:
        """Load prompt templates from files"""
        prompts = {}
        prompts_dir = Path("agent/prompts")
        
        try:
            if prompts_dir.exists():
                for prompt_file in prompts_dir.glob("*.md"):
                    try:
                        with open(prompt_file, 'r', encoding='utf-8') as f:
                            prompt_name = prompt_file.stem
                            prompts[prompt_name] = f.read().strip()
                            logger.info(f"Loaded prompt: {prompt_name}")
                    except Exception as e:
                        logger.error(f"Error loading prompt {prompt_file}: {str(e)}")
            
            # Load default prompts if files don't exist
            if not prompts:
                prompts = self.get_default_prompts()
                logger.info("Loaded default prompts")
                
        except Exception as e:
            logger.error(f"Error loading prompts: {str(e)}")
            prompts = self.get_default_prompts()
        
        return prompts
    
    def load_schemas(self) -> Dict[str, Any]:
        """Load JSON schemas from files"""
        schemas = {}
        schemas_dir = Path("agent/schemas")
        
        try:
            if schemas_dir.exists():
                for schema_file in schemas_dir.glob("*.json"):
                    try:
                        with open(schema_file, 'r', encoding='utf-8') as f:
                            schema_name = schema_file.stem
                            schemas[schema_name] = json.load(f)
                            logger.info(f"Loaded schema: {schema_name}")
                    except Exception as e:
                        logger.error(f"Error loading schema {schema_file}: {str(e)}")
            
            # Load default schemas if files don't exist
            if not schemas:
                schemas = self.get_default_schemas()
                logger.info("Loaded default schemas")
                
        except Exception as e:
            logger.error(f"Error loading schemas: {str(e)}")
            schemas = self.get_default_schemas()
        
        return schemas
    
    def get_default_prompts(self) -> Dict[str, str]:
        """Get default prompt templates"""
        return {
            "chatbot": """You are SafeChild, a friendly and supportive AI companion designed to help children learn about safety and provide guidance in difficult situations.

Your role is to:
1. Help children understand safety concepts in an age-appropriate way
2. Provide emotional support and reassurance
3. Guide children to trusted adults when needed
4. Teach safety rules and best practices
5. Help children recognize and respond to unsafe situations

IMPORTANT SAFETY GUIDELINES:
- Always use age-appropriate language
- Be supportive and non-judgmental
- Encourage children to talk to trusted adults
- Never give medical or legal advice
- If a child mentions serious harm or danger, immediately encourage them to tell a trusted adult or call emergency services
- Use positive reinforcement and gentle guidance
- Keep responses encouraging and helpful

Remember: You are here to support and educate, but serious safety concerns should always be referred to trusted adults or authorities.

Respond in a warm, friendly, and supportive manner while maintaining appropriate boundaries.""",
            
            "complaint_generation": """You are a legal document assistant specializing in child safety incident reports. Your task is to generate professional, legally-sound complaint drafts based on provided information.

Requirements:
1. Use formal, professional language appropriate for legal documents
2. Include all relevant details from the provided information
3. Structure the complaint in standard legal format
4. Use appropriate legal terminology
5. Be specific about requested actions
6. Maintain the child's privacy and dignity
7. Follow standard complaint format with clear sections

The complaint should be:
- Professional and formal
- Comprehensive and detailed
- Legally appropriate
- Clear and actionable
- Respectful of all parties involved

Generate a complaint draft that can be submitted to authorities or legal professionals.""",
            
            "emergency_assessment": """You are an emergency response specialist. Your task is to assess the urgency and severity of reported situations and provide appropriate guidance.

Assessment Criteria:
1. Immediate danger to life or safety
2. Risk of serious harm
3. Need for immediate intervention
4. Appropriate response level
5. Recommended actions

Emergency Levels:
- CRITICAL: Immediate danger, call 911
- HIGH: Significant risk, immediate attention needed
- MEDIUM: Moderate concern, monitor closely
- LOW: Minor concern, routine follow-up

Provide clear, actionable guidance based on the situation described.""",
            
            "safety_education": """You are a child safety educator. Your task is to teach safety concepts in an engaging, age-appropriate way.

Teaching Principles:
1. Use simple, clear language
2. Make learning interactive and fun
3. Reinforce positive behaviors
4. Use examples and scenarios
5. Encourage questions and discussion
6. Build confidence and awareness

Topics to cover:
- Body safety and boundaries
- Stranger danger awareness
- Online safety
- Emergency procedures
- Trusted adults and resources
- Reporting unsafe situations

Make safety education engaging and memorable for children."""
        }
    
    def get_default_schemas(self) -> Dict[str, Any]:
        """Get default JSON schemas"""
        return {
            "complaint": {
                "type": "object",
                "properties": {
                    "incident_details": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "format": "date"},
                            "time": {"type": "string", "format": "time"},
                            "location": {"type": "string"},
                            "description": {"type": "string"},
                            "type": {"type": "string", "enum": ["physical_abuse", "verbal_abuse", "bullying", "inappropriate_touching", "harassment", "neglect", "other"]}
                        },
                        "required": ["date", "time", "location", "description", "type"]
                    },
                    "child_information": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer", "minimum": 0, "maximum": 18},
                            "gender": {"type": "string"},
                            "school": {"type": "string"}
                        },
                        "required": ["name", "age"]
                    },
                    "guardian_information": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "phone": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                            "address": {"type": "string"}
                        },
                        "required": ["name", "phone"]
                    }
                },
                "required": ["incident_details", "child_information", "guardian_information"]
            },
            
            "emergency_alert": {
                "type": "object",
                "properties": {
                    "urgency_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"]
                    },
                    "location": {"type": "string"},
                    "description": {"type": "string"},
                    "contacts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "phone": {"type": "string"},
                                "relationship": {"type": "string"}
                            },
                            "required": ["name", "phone", "relationship"]
                        }
                    }
                },
                "required": ["urgency_level", "location", "description", "contacts"]
            }
        }
    
    def get_config(self, section: str = None, key: str = None) -> Any:
        """Get configuration value"""
        try:
            if section is None:
                return self.config
            
            if key is None:
                return self.config.get(section, {})
            
            return self.config.get(section, {}).get(key)
            
        except Exception as e:
            logger.error(f"Error getting config: {str(e)}")
            return None
    
    def get_prompt(self, prompt_name: str) -> str:
        """Get prompt template by name"""
        return self.prompts.get(prompt_name, "")
    
    def get_schema(self, schema_name: str) -> Dict[str, Any]:
        """Get JSON schema by name"""
        return self.schemas.get(schema_name, {})
    
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """Update configuration value"""
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section][key] = value
            
            # Save to file
            self.save_config()
            logger.info(f"Configuration updated: {section}.{key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating config: {str(e)}")
            return False
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return issues"""
        issues = []
        warnings = []
        
        try:
            # Check required sections
            required_sections = ["openai", "safety", "chatbot"]
            for section in required_sections:
                if section not in self.config:
                    issues.append(f"Missing required configuration section: {section}")
            
            # Check OpenAI configuration
            openai_config = self.config.get("openai", {})
            if not openai_config.get("model"):
                issues.append("OpenAI model not configured")
            
            # Check safety configuration
            safety_config = self.config.get("safety", {})
            if not safety_config.get("emergency_keywords"):
                warnings.append("No emergency keywords configured")
            
            # Check chatbot configuration
            chatbot_config = self.config.get("chatbot", {})
            if chatbot_config.get("max_conversation_length", 0) <= 0:
                warnings.append("Invalid conversation length configuration")
            
        except Exception as e:
            issues.append(f"Configuration validation error: {str(e)}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "timestamp": self.get_current_timestamp()
        }
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and configuration summary"""
        validation = self.validate_config()
        
        return {
            "service": "agent_config",
            "status": "active" if validation["valid"] else "configuration_issues",
            "config_sections": list(self.config.keys()),
            "prompts_loaded": len(self.prompts),
            "schemas_loaded": len(self.schemas),
            "validation": validation,
            "timestamp": self.get_current_timestamp()
        }

# Global instance
agent_config = AgentConfig()

def get_agent_config() -> AgentConfig:
    """Get global agent configuration instance"""
    return agent_config

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import logging
from datetime import datetime
import uuid

# Import services
from utils.textCleaner import TextCleaner
from utils.timeUtils import TimeUtils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/awareness", tags=["awareness"])

class SafetyStory(BaseModel):
    id: str
    title: str
    description: str
    age_group: str
    difficulty_level: str
    content: List[Dict[str, Any]]
    tags: List[str]
    estimated_duration: int  # in minutes

class SafetyQuiz(BaseModel):
    id: str
    title: str
    description: str
    age_group: str
    questions: List[Dict[str, Any]]
    passing_score: int
    estimated_duration: int

class AwarenessContent(BaseModel):
    stories: List[SafetyStory]
    quizzes: List[SafetyQuiz]
    resources: List[Dict[str, Any]]
    last_updated: str

class AwarenessAPI:
    def __init__(self):
        self.text_cleaner = TextCleaner()
        self.time_utils = TimeUtils()
        
        # Initialize awareness content
        self.awareness_content = self.initialize_content()
    
    def initialize_content(self) -> AwarenessContent:
        """Initialize default awareness content"""
        stories = [
            SafetyStory(
                id="good_touch_bad_touch",
                title="Good Touch vs Bad Touch",
                description="Learn to identify safe and unsafe touches",
                age_group="5-12",
                difficulty_level="beginner",
                content=[
                    {
                        "type": "lesson",
                        "title": "What is Good Touch?",
                        "text": "Good touches make you feel safe, loved, and comfortable. They include:",
                        "examples": [
                            "Hugs from family members",
                            "High-fives from friends",
                            "Doctor check-ups (with parent present)",
                            "Gentle pats on the back"
                        ],
                        "icon": "✅",
                        "interactive_elements": ["examples", "practice_scenarios"]
                    },
                    {
                        "type": "lesson",
                        "title": "What is Bad Touch?",
                        "text": "Bad touches make you feel uncomfortable, scared, or confused. They include:",
                        "examples": [
                            "Touching private parts",
                            "Touches that hurt",
                            "Touches that make you feel scared",
                            "Touches that are kept secret"
                        ],
                        "icon": "❌",
                        "interactive_elements": ["examples", "practice_scenarios"]
                    },
                    {
                        "type": "interactive",
                        "title": "Practice Time!",
                        "text": "Let's practice identifying good and bad touches",
                        "scenarios": [
                            {
                                "text": "A hug from your mom",
                                "type": "good",
                                "explanation": "This is a good touch - it's safe and loving",
                                "image_url": "/assets/images/good_hug.png"
                            },
                            {
                                "text": "Someone touching your private parts",
                                "type": "bad",
                                "explanation": "This is a bad touch - tell a trusted adult immediately",
                                "image_url": "/assets/images/bad_touch.png"
                            },
                            {
                                "text": "A high-five from your friend",
                                "type": "good",
                                "explanation": "This is a good touch - it's friendly and fun",
                                "image_url": "/assets/images/good_highfive.png"
                            },
                            {
                                "text": "A touch that hurts",
                                "type": "bad",
                                "explanation": "This is a bad touch - no one should hurt you",
                                "image_url": "/assets/images/bad_hurt.png"
                            },
                            {
                                "text": "A doctor's check-up with your parent",
                                "type": "good",
                                "explanation": "This is a good touch - it's for your health and safety",
                                "image_url": "/assets/images/good_doctor.png"
                            }
                        ],
                        "interactive_elements": ["scenarios", "feedback", "progress_tracking"]
                    }
                ],
                tags=["body_safety", "good_touch", "bad_touch", "interactive"],
                estimated_duration=15
            ),
            SafetyStory(
                id="body_safety_rules",
                title="Body Safety Rules",
                description="Important rules to keep your body safe",
                age_group="5-12",
                difficulty_level="beginner",
                content=[
                    {
                        "type": "rules",
                        "title": "The 5 Body Safety Rules",
                        "rules": [
                            "My body belongs to me",
                            "I can say NO to any touch I don't want",
                            "I can tell a trusted adult if something feels wrong",
                            "I don't keep secrets about touches",
                            "I trust my feelings - if it feels wrong, it probably is"
                        ],
                        "interactive_elements": ["rule_practice", "memory_game", "quiz"]
                    },
                    {
                        "type": "activity",
                        "title": "Safe Adults",
                        "text": "Who are the safe adults in your life?",
                        "examples": [
                            "Parents and guardians",
                            "Teachers and school staff",
                            "Doctors and nurses",
                            "Police officers",
                            "Trusted family members"
                        ],
                        "interactive_elements": ["list_building", "role_play", "discussion"]
                    }
                ],
                tags=["body_safety", "rules", "safe_adults", "interactive"],
                estimated_duration=20
            },
            SafetyStory(
                id="online_safety",
                title="Online Safety",
                description="Stay safe on the internet and social media",
                age_group="8-16",
                difficulty_level="intermediate",
                content=[
                    {
                        "type": "lesson",
                        "title": "Internet Safety Rules",
                        "text": "When you're online, remember:",
                        "rules": [
                            "Never share personal information",
                            "Don't talk to strangers online",
                            "Tell a parent if someone makes you uncomfortable",
                            "Don't share photos without permission",
                            "If something feels wrong, tell a trusted adult"
                        ],
                        "interactive_elements": ["rule_practice", "scenarios", "quiz"]
                    },
                    {
                        "type": "interactive",
                        "title": "Online Safety Scenarios",
                        "text": "Practice making safe choices online",
                        "scenarios": [
                            {
                                "text": "Someone asks for your address online",
                                "correct_action": "Don't share it and tell a parent",
                                "explanation": "Never share personal information with strangers online"
                            },
                            {
                                "text": "A friend wants to share your photo",
                                "correct_action": "Ask permission first",
                                "explanation": "Always get permission before sharing photos"
                            }
                        ],
                        "interactive_elements": ["scenarios", "feedback", "discussion"]
                    }
                ],
                tags=["online_safety", "internet", "social_media", "interactive"],
                estimated_duration=25
            },
            SafetyStory(
                id="stranger_danger",
                title="Stranger Danger Awareness",
                description="Learn about staying safe around strangers",
                age_group="5-12",
                difficulty_level="beginner",
                content=[
                    {
                        "type": "lesson",
                        "title": "What is a Stranger?",
                        "text": "A stranger is someone you don't know well. Not all strangers are bad, but it's important to be careful.",
                        "examples": [
                            "Someone you've never met before",
                            "Someone who asks for help with something",
                            "Someone who offers you gifts or treats",
                            "Someone who asks you to keep secrets"
                        ],
                        "interactive_elements": ["examples", "discussion", "practice"]
                    },
                    {
                        "type": "rules",
                        "title": "Stranger Safety Rules",
                        "rules": [
                            "Never go anywhere with a stranger",
                            "Don't accept gifts from strangers",
                            "Don't give personal information to strangers",
                            "If a stranger makes you uncomfortable, run away and tell a trusted adult",
                            "Stay with your group when in public places"
                        ],
                        "interactive_elements": ["rule_practice", "scenarios", "role_play"]
                    }
                ],
                tags=["stranger_danger", "safety_rules", "interactive"],
                estimated_duration=20
            }
        ]
        
        quizzes = [
            SafetyQuiz(
                id="touch_identification",
                title="Touch Identification Quiz",
                description="Test your knowledge about good and bad touches",
                age_group="5-12",
                questions=[
                    {
                        "question": "Is a hug from your parent a good touch or bad touch?",
                        "options": ["Good touch", "Bad touch"],
                        "correct": 0,
                        "explanation": "A hug from your parent is a good touch because it's safe and loving.",
                        "image_url": "/assets/images/parent_hug.png"
                    },
                    {
                        "question": "What should you do if someone touches you in a way that makes you uncomfortable?",
                        "options": ["Keep it a secret", "Tell a trusted adult", "Ignore it", "Touch them back"],
                        "correct": 1,
                        "explanation": "Always tell a trusted adult if someone makes you uncomfortable.",
                        "image_url": "/assets/images/tell_adult.png"
                    },
                    {
                        "question": "Which of these is a good touch?",
                        "options": ["A high-five from a friend", "Someone touching your private parts", "A touch that hurts", "A touch that's kept secret"],
                        "correct": 0,
                        "explanation": "A high-five from a friend is a good touch - it's friendly and fun!",
                        "image_url": "/assets/images/friend_highfive.png"
                    }
                ],
                passing_score=2,
                estimated_duration=10
            ),
            SafetyQuiz(
                id="body_safety_rules",
                title="Body Safety Rules Quiz",
                description="Test your knowledge of body safety rules",
                age_group="5-12",
                questions=[
                    {
                        "question": "Who does your body belong to?",
                        "options": ["Your parents", "Your teachers", "You", "Your friends"],
                        "correct": 2,
                        "explanation": "Your body belongs to YOU! No one else has the right to touch it without your permission.",
                        "image_url": "/assets/images/body_ownership.png"
                    },
                    {
                        "question": "What should you do if someone asks you to keep a touch secret?",
                        "options": ["Keep the secret", "Tell a trusted adult", "Ignore them", "Tell your friends"],
                        "correct": 1,
                        "explanation": "Never keep secrets about touches. Always tell a trusted adult.",
                        "image_url": "/assets/images/no_secrets.png"
                    }
                ],
                passing_score=1,
                estimated_duration=8
            )
        ]
        
        resources = [
            {
                "id": "emergency_contacts",
                "title": "Emergency Contacts",
                "type": "reference",
                "content": {
                    "911": "Emergency Services",
                    "1-800-4-A-CHILD": "Childhelp National Child Abuse Hotline",
                    "1-800-422-4453": "Child Abuse Hotline",
                    "1-800-656-4673": "RAINN (Rape, Abuse & Incest National Network)"
                }
            },
            {
                "id": "safety_tips",
                "title": "Daily Safety Tips",
                "type": "tips",
                "content": [
                    "Always tell a trusted adult if something feels wrong",
                    "Trust your instincts - if it feels wrong, it probably is",
                    "Never keep secrets about touches or uncomfortable situations",
                    "Stay with your group when in public places",
                    "Know your emergency contacts by heart"
                ]
            },
            {
                "id": "parent_resources",
                "title": "Parent Resources",
                "type": "guide",
                "content": [
                    "How to talk to your child about safety",
                    "Signs of abuse to watch for",
                    "Building trust with your child",
                    "Creating a family safety plan",
                    "When to seek professional help"
                ]
            }
        ]
        
        return AwarenessContent(
            stories=stories,
            quizzes=quizzes,
            resources=resources,
            last_updated=self.time_utils.get_current_timestamp()
        )
    
    def get_content_by_age_group(self, age_group: str) -> Dict[str, Any]:
        """Get content filtered by age group"""
        try:
            age = int(age_group)
            
            # Filter stories by age group
            if age <= 5:
                target_age = "5-12"
            elif age <= 12:
                target_age = "5-12"
            elif age <= 16:
                target_age = "8-16"
            else:
                target_age = "8-16"
            
            filtered_stories = [
                story for story in self.awareness_content.stories
                if story.age_group == target_age
            ]
            
            filtered_quizzes = [
                quiz for quiz in self.awareness_content.quizzes
                if quiz.age_group == target_age
            ]
            
            return {
                "stories": filtered_stories,
                "quizzes": filtered_quizzes,
                "resources": self.awareness_content.resources,
                "age_group": target_age,
                "last_updated": self.awareness_content.last_updated
            }
            
        except ValueError:
            # Return all content if age group is invalid
            return {
                "stories": self.awareness_content.stories,
                "quizzes": self.awareness_content.quizzes,
                "resources": self.awareness_content.resources,
                "age_group": "all",
                "last_updated": self.awareness_content.last_updated
            }
    
    def get_content_by_tags(self, tags: List[str]) -> Dict[str, Any]:
        """Get content filtered by tags"""
        filtered_stories = [
            story for story in self.awareness_content.stories
            if any(tag in story.tags for tag in tags)
        ]
        
        filtered_quizzes = [
            quiz for quiz in self.awareness_content.quizzes
            if any(tag in quiz.tags for tag in tags)
        ]
        
        return {
            "stories": filtered_stories,
            "quizzes": filtered_quizzes,
            "resources": self.awareness_content.resources,
            "tags": tags,
            "last_updated": self.awareness_content.last_updated
        }
    
    def get_story_by_id(self, story_id: str) -> Optional[SafetyStory]:
        """Get safety story by ID"""
        for story in self.awareness_content.stories:
            if story.id == story_id:
                return story
        return None
    
    def get_quiz_by_id(self, quiz_id: str) -> Optional[SafetyQuiz]:
        """Get safety quiz by ID"""
        for quiz in self.awareness_content.quizzes:
            if quiz.id == quiz_id:
                return quiz
        return None
    
    def get_progress_tracking(self, user_id: str, content_id: str) -> Dict[str, Any]:
        """Get user progress for specific content"""
        # In production, this would query a database
        # For now, return mock data
        return {
            "user_id": user_id,
            "content_id": content_id,
            "progress": 0,
            "completed": False,
            "score": None,
            "last_accessed": None
        }
    
    def update_progress(self, user_id: str, content_id: str, progress: int, score: Optional[int] = None) -> Dict[str, Any]:
        """Update user progress for specific content"""
        # In production, this would update a database
        # For now, return mock data
        return {
            "user_id": user_id,
            "content_id": content_id,
            "progress": progress,
            "completed": progress >= 100,
            "score": score,
            "last_updated": self.time_utils.get_current_timestamp()
        }
    
    def get_recommended_content(self, user_id: str, age_group: str, completed_content: List[str]) -> Dict[str, Any]:
        """Get recommended content based on user profile and progress"""
        # Filter out completed content
        available_stories = [
            story for story in self.awareness_content.stories
            if story.id not in completed_content and story.age_group == age_group
        ]
        
        available_quizzes = [
            quiz for quiz in self.awareness_content.quizzes
            if quiz.id not in completed_content and quiz.age_group == age_group
        ]
        
        # Sort by difficulty level and estimated duration
        recommended_stories = sorted(available_stories, key=lambda x: (x.difficulty_level, x.estimated_duration))[:3]
        recommended_quizzes = sorted(available_quizzes, key=lambda x: (x.difficulty_level, x.estimated_duration))[:2]
        
        return {
            "recommended_stories": recommended_stories,
            "recommended_quizzes": recommended_quizzes,
            "reasoning": "Based on your age group and learning progress"
        }

# Initialize API
awareness_api = AwarenessAPI()

@router.get("/", response_model=AwarenessContent)
async def get_awareness_content():
    """Get all awareness content"""
    return awareness_api.awareness_content

@router.get("/age-group/{age_group}")
async def get_content_by_age_group(age_group: str):
    """Get content filtered by age group"""
    return awareness_api.get_content_by_age_group(age_group)

@router.get("/tags")
async def get_content_by_tags(tags: str):
    """Get content filtered by tags (comma-separated)"""
    tag_list = [tag.strip() for tag in tags.split(",")]
    return awareness_api.get_content_by_tags(tag_list)

@router.get("/stories/{story_id}")
async def get_safety_story(story_id: str):
    """Get specific safety story by ID"""
    story = awareness_api.get_story_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Safety story not found")
    return story

@router.get("/quizzes/{quiz_id}")
async def get_safety_quiz(quiz_id: str):
    """Get specific safety quiz by ID"""
    quiz = awareness_api.get_quiz_by_id(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Safety quiz not found")
    return quiz

@router.get("/progress/{user_id}/{content_id}")
async def get_user_progress(user_id: str, content_id: str):
    """Get user progress for specific content"""
    return awareness_api.get_progress_tracking(user_id, content_id)

@router.post("/progress/{user_id}/{content_id}")
async def update_user_progress(user_id: str, content_id: str, progress: int, score: Optional[int] = None):
    """Update user progress for specific content"""
    return awareness_api.update_progress(user_id, content_id, progress, score)

@router.get("/recommendations/{user_id}")
async def get_recommended_content(user_id: str, age_group: str, completed_content: str = ""):
    """Get recommended content for user"""
    completed_list = [item.strip() for item in completed_content.split(",") if item.strip()]
    return awareness_api.get_recommended_content(user_id, age_group, completed_list)

@router.get("/search")
async def search_content(query: str):
    """Search content by title, description, or tags"""
    query_lower = query.lower()
    
    matching_stories = [
        story for story in awareness_api.awareness_content.stories
        if (query_lower in story.title.lower() or 
            query_lower in story.description.lower() or
            any(query_lower in tag.lower() for tag in story.tags))
    ]
    
    matching_quizzes = [
        quiz for quiz in awareness_api.awareness_content.quizzes
        if (query_lower in quiz.title.lower() or 
            query_lower in quiz.description.lower())
    ]
    
    return {
        "query": query,
        "stories": matching_stories,
        "quizzes": matching_quizzes,
        "total_results": len(matching_stories) + len(matching_quizzes)
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "awareness",
        "timestamp": TimeUtils().get_current_timestamp(),
        "total_stories": len(awareness_api.awareness_content.stories),
        "total_quizzes": len(awareness_api.awareness_content.quizzes),
        "total_resources": len(awareness_api.awareness_content.resources)
    }

@router.get("/content")
async def get_content(age_group: Optional[str] = None, type: Optional[str] = None, difficulty: Optional[str] = None, q: Optional[str] = None):
    """Get awareness content with optional filters used by the frontend"""
    content = awareness_api.awareness_content
    data = {
        "stories": content.stories,
        "quizzes": content.quizzes,
        "resources": content.resources,
        "last_updated": content.last_updated
    }
    if age_group and age_group != "All Ages":
        filtered = awareness_api.get_content_by_age_group(age_group)
        data.update({
            "stories": filtered["stories"],
            "quizzes": filtered["quizzes"]
        })
    if q:
        search = (await search_content(q))
        data.update({
            "stories": search["stories"],
            "quizzes": search["quizzes"]
        })
    return data

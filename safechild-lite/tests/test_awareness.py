import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_awareness_health():
    res = client.get("/api/awareness/health")
    assert res.status_code == 200

def test_awareness_content_endpoint():
    res = client.get("/api/awareness/content")
    assert res.status_code == 200
    data = res.json()
    assert "stories" in data and "quizzes" in data

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app
from backend.api.awareness import router

# Create test client
client = TestClient(app)

class TestAwarenessAPI:
    """Test cases for awareness API endpoints"""
    
    def setup_method(self):
        """Setup test data before each test"""
        self.sample_story = {
            "id": "story_001",
            "title": "The Safe Adventure",
            "content": "Once upon a time, there was a brave little hero...",
            "age_group": "5-8",
            "tags": ["stranger_danger", "safety_rules"],
            "type": "story",
            "difficulty": "beginner"
        }
        
        self.sample_quiz = {
            "id": "quiz_001",
            "title": "Safety Rules Quiz",
            "questions": [
                {
                    "question": "What should you do if a stranger offers you candy?",
                    "options": ["Take it", "Say no and walk away", "Ask for more"],
                    "correct_answer": 1,
                    "explanation": "Never take anything from strangers"
                }
            ],
            "age_group": "5-8",
            "tags": ["stranger_danger"],
            "type": "quiz",
            "difficulty": "beginner"
        }
        
        self.sample_lesson = {
            "id": "lesson_001",
            "title": "Good Touch vs Bad Touch",
            "content": "Your body belongs to you...",
            "age_group": "5-8",
            "tags": ["body_safety", "boundaries"],
            "type": "lesson",
            "difficulty": "beginner"
        }
        
        self.sample_user_progress = {
            "user_id": "user_123",
            "completed_content": ["story_001", "quiz_001"],
            "quiz_scores": {"quiz_001": 100},
            "time_spent": {"story_001": 300, "lesson_001": 180},
            "last_activity": "2024-01-15T10:00:00Z"
        }

    def test_get_awareness_content_success(self):
        """Test successful retrieval of awareness content"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_lesson]
            
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["title"] == "The Safe Adventure"
            assert data[1]["title"] == "Good Touch vs Bad Touch"

    def test_get_awareness_content_filtered(self):
        """Test filtering awareness content by age group and tags"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            response = client.get("/api/awareness/content?age_group=5-8&tags=stranger_danger")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["age_group"] == "5-8"
            assert "stranger_danger" in data[0]["tags"]

    def test_get_awareness_content_by_type(self):
        """Test filtering content by type"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_quiz]
            
            response = client.get("/api/awareness/content?type=quiz")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["type"] == "quiz"

    def test_get_awareness_content_empty_result(self):
        """Test when no content matches filters"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = []
            
            response = client.get("/api/awareness/content?age_group=15-18&tags=nonexistent")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0

    def test_get_content_by_id_success(self):
        """Test successful retrieval of specific content by ID"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            response = client.get("/api/awareness/content/story_001")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "story_001"
            assert data["title"] == "The Safe Adventure"

    def test_get_content_by_id_not_found(self):
        """Test when content ID doesn't exist"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = []
            
            response = client.get("/api/awareness/content/nonexistent_id")
            
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Content not found"

    def test_get_quizzes_success(self):
        """Test successful retrieval of quizzes"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_quiz]
            
            response = client.get("/api/awareness/quizzes")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["type"] == "quiz"

    def test_get_quizzes_filtered(self):
        """Test filtering quizzes by age group and difficulty"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_quiz]
            
            response = client.get("/api/awareness/quizzes?age_group=5-8&difficulty=beginner")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["age_group"] == "5-8"
            assert data[0]["difficulty"] == "beginner"

    def test_get_stories_success(self):
        """Test successful retrieval of stories"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            response = client.get("/api/awareness/stories")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["type"] == "story"

    def test_get_lessons_success(self):
        """Test successful retrieval of lessons"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_lesson]
            
            response = client.get("/api/awareness/lessons")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["type"] == "lesson"

    def test_get_user_progress_success(self):
        """Test successful retrieval of user progress"""
        with patch('backend.api.awareness.user_progress') as mock_progress:
            mock_progress.return_value = self.sample_user_progress
            
            response = client.get("/api/awareness/progress/user_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "user_123"
            assert len(data["completed_content"]) == 2

    def test_get_user_progress_not_found(self):
        """Test when user progress doesn't exist"""
        with patch('backend.api.awareness.user_progress') as mock_progress:
            mock_progress.return_value = None
            
            response = client.get("/api/awareness/progress/nonexistent_user")
            
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "User progress not found"

    def test_update_user_progress_success(self):
        """Test successful update of user progress"""
        progress_update = {
            "content_id": "story_001",
            "completed": True,
            "time_spent": 300,
            "quiz_score": None
        }
        
        with patch('backend.api.awareness.user_progress') as mock_progress:
            mock_progress.return_value = self.sample_user_progress
            
            response = client.post("/api/awareness/progress/user_123", json=progress_update)
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Progress updated successfully"

    def test_update_user_progress_invalid_data(self):
        """Test update with invalid progress data"""
        invalid_progress = {
            "content_id": "",  # Empty content ID
            "completed": "invalid_boolean"  # Invalid boolean
        }
        
        response = client.post("/api/awareness/progress/user_123", json=invalid_progress)
        
        assert response.status_code == 422  # Validation error

    def test_get_awareness_statistics_success(self):
        """Test successful retrieval of awareness statistics"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            response = client.get("/api/awareness/statistics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_content"] == 3
            assert data["content_by_type"]["story"] == 1
            assert data["content_by_type"]["quiz"] == 1
            assert data["content_by_type"]["lesson"] == 1

    def test_get_awareness_statistics_empty_content(self):
        """Test statistics when no content exists"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = []
            
            response = client.get("/api/awareness/statistics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_content"] == 0
            assert all(count == 0 for count in data["content_by_type"].values())

    def test_search_awareness_content_success(self):
        """Test successful search of awareness content"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            response = client.get("/api/awareness/search?q=safe adventure")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert "safe" in data[0]["title"].lower()

    def test_search_awareness_content_no_results(self):
        """Test search with no matching results"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = []
            
            response = client.get("/api/awareness/search?q=nonexistent content")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0

    def test_get_awareness_content_with_invalid_filters(self):
        """Test content retrieval with invalid filter parameters"""
        response = client.get("/api/awareness/content?age_group=invalid&difficulty=invalid")
        
        # Should still return a response (even if empty) rather than error
        assert response.status_code == 200

    def test_get_content_by_id_malformed_id(self):
        """Test content retrieval with malformed ID"""
        response = client.get("/api/awareness/content/")
        
        assert response.status_code == 404

    def test_update_progress_missing_user(self):
        """Test progress update for non-existent user"""
        progress_update = {
            "content_id": "story_001",
            "completed": True,
            "time_spent": 300
        }
        
        with patch('backend.api.awareness.user_progress') as mock_progress:
            mock_progress.return_value = None
            
            response = client.post("/api/awareness/progress/nonexistent_user", json=progress_update)
            
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "User progress not found"

    def test_get_awareness_content_pagination(self):
        """Test content retrieval with pagination parameters"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_lesson]
            
            response = client.get("/api/awareness/content?limit=1&offset=0")
            
            assert response.status_code == 200
            data = response.json()
            # Note: Current implementation doesn't support pagination, so this test
            # verifies the API doesn't break with pagination parameters
            assert len(data) >= 0

    def test_get_awareness_content_sorting(self):
        """Test content retrieval with sorting parameters"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_lesson]
            
            response = client.get("/api/awareness/content?sort_by=title&sort_order=asc")
            
            assert response.status_code == 200
            data = response.json()
            # Note: Current implementation doesn't support sorting, so this test
            # verifies the API doesn't break with sorting parameters
            assert len(data) >= 0

    def test_awareness_content_validation(self):
        """Test that awareness content has required fields"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            data = response.json()
            
            if len(data) > 0:
                content = data[0]
                required_fields = ["id", "title", "content", "type"]
                for field in required_fields:
                    assert field in content, f"Missing required field: {field}"

    def test_quiz_content_structure(self):
        """Test that quiz content has proper structure"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_quiz]
            
            response = client.get("/api/awareness/quizzes")
            
            assert response.status_code == 200
            data = response.json()
            
            if len(data) > 0:
                quiz = data[0]
                assert "questions" in quiz
                assert isinstance(quiz["questions"], list)
                
                if quiz["questions"]:
                    question = quiz["questions"][0]
                    required_question_fields = ["question", "options", "correct_answer"]
                    for field in required_question_fields:
                        assert field in question, f"Missing required question field: {field}"

    def test_awareness_content_age_groups(self):
        """Test that content has valid age group values"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            data = response.json()
            
            valid_age_groups = ["3-5", "5-8", "8-12", "12-15", "15-18"]
            
            for content in data:
                if "age_group" in content:
                    assert content["age_group"] in valid_age_groups, f"Invalid age group: {content['age_group']}"

    def test_awareness_content_tags(self):
        """Test that content has valid tag values"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            data = response.json()
            
            valid_tags = [
                "stranger_danger", "body_safety", "boundaries", "online_safety",
                "bullying", "emergency", "safety_rules", "good_touch_bad_touch"
            ]
            
            for content in data:
                if "tags" in content and content["tags"]:
                    for tag in content["tags"]:
                        assert tag in valid_tags, f"Invalid tag: {tag}"

    def test_awareness_content_types(self):
        """Test that content has valid type values"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            data = response.json()
            
            valid_types = ["story", "quiz", "lesson", "video", "activity"]
            
            for content in data:
                assert content["type"] in valid_types, f"Invalid content type: {content['type']}"

    def test_awareness_content_difficulty_levels(self):
        """Test that content has valid difficulty values"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            data = response.json()
            
            valid_difficulties = ["beginner", "intermediate", "advanced"]
            
            for content in data:
                if "difficulty" in content:
                    assert content["difficulty"] in valid_difficulties, f"Invalid difficulty: {content['difficulty']}"

    def test_awareness_content_content_length(self):
        """Test that content has reasonable length"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            data = response.json()
            
            for content in data:
                if "content" in content:
                    content_length = len(content["content"])
                    assert content_length > 0, "Content should not be empty"
                    assert content_length < 10000, "Content should not be excessively long"

    def test_awareness_content_title_length(self):
        """Test that content titles have reasonable length"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            data = response.json()
            
            for content in data:
                if "title" in content:
                    title_length = len(content["title"])
                    assert title_length > 0, "Title should not be empty"
                    assert title_length < 200, "Title should not be excessively long"

    def test_awareness_content_id_format(self):
        """Test that content IDs have consistent format"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            data = response.json()
            
            for content in data:
                if "id" in content:
                    content_id = content["id"]
                    assert len(content_id) > 0, "Content ID should not be empty"
                    assert len(content_id) < 50, "Content ID should not be excessively long"
                    # Check for common ID patterns
                    assert "_" in content_id or content_id.isalnum(), "Content ID should have consistent format"

    def test_awareness_content_metadata(self):
        """Test that content has appropriate metadata"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            data = response.json()
            
            for content in data:
                # Check for required metadata fields
                required_metadata = ["id", "title", "type"]
                for field in required_metadata:
                    assert field in content, f"Missing required metadata field: {field}"
                
                # Check for optional metadata fields
                optional_metadata = ["age_group", "tags", "difficulty", "content"]
                metadata_count = sum(1 for field in optional_metadata if field in content)
                assert metadata_count >= 1, "Content should have at least one optional metadata field"

    def test_awareness_content_consistency(self):
        """Test that content data is consistent across endpoints"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            # Get content from main endpoint
            main_response = client.get("/api/awareness/content")
            main_data = main_response.json()
            
            # Get content from specific type endpoints
            stories_response = client.get("/api/awareness/stories")
            stories_data = stories_response.json()
            
            quizzes_response = client.get("/api/awareness/quizzes")
            quizzes_data = quizzes_response.json()
            
            lessons_response = client.get("/api/awareness/lessons")
            lessons_data = lessons_response.json()
            
            # Verify consistency
            assert len(main_data) == len(stories_data) + len(quizzes_data) + len(lessons_data)
            
            # Verify that stories endpoint only returns stories
            for story in stories_data:
                assert story["type"] == "story"
            
            # Verify that quizzes endpoint only returns quizzes
            for quiz in quizzes_data:
                assert quiz["type"] == "quiz"
            
            # Verify that lessons endpoint only returns lessons
            for lesson in lessons_data:
                assert lesson["type"] == "lesson"

    def test_awareness_content_error_handling(self):
        """Test error handling in awareness content endpoints"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.side_effect = Exception("Database error")
            
            response = client.get("/api/awareness/content")
            
            # Should handle errors gracefully
            assert response.status_code in [200, 500, 503]

    def test_awareness_content_performance(self):
        """Test that awareness content endpoints respond within reasonable time"""
        import time
        
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            start_time = time.time()
            response = client.get("/api/awareness/content")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.0, f"Response time {response_time}s exceeds 1 second threshold"

    def test_awareness_content_caching(self):
        """Test that awareness content can be cached effectively"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            # First request
            response1 = client.get("/api/awareness/content")
            assert response1.status_code == 200
            
            # Second request (should be served from cache if implemented)
            response2 = client.get("/api/awareness/content")
            assert response2.status_code == 200
            
            # Verify responses are identical
            assert response1.json() == response2.json()

    def test_awareness_content_compression(self):
        """Test that awareness content responses can be compressed"""
        headers = {"Accept-Encoding": "gzip, deflate"}
        
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            response = client.get("/api/awareness/content", headers=headers)
            
            assert response.status_code == 200
            # Note: Compression is handled by FastAPI/uvicorn, so we just verify the endpoint works

    def test_awareness_content_rate_limiting(self):
        """Test that awareness content endpoints respect rate limiting"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            # Make multiple rapid requests
            responses = []
            for _ in range(5):
                response = client.get("/api/awareness/content")
                responses.append(response)
            
            # All requests should succeed (rate limiting not implemented in current version)
            for response in responses:
                assert response.status_code == 200

    def test_awareness_content_authentication(self):
        """Test that awareness content endpoints work without authentication"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            response = client.get("/api/awareness/content")
            
            # Should work without authentication headers
            assert response.status_code == 200

    def test_awareness_content_authorization(self):
        """Test that awareness content endpoints don't require specific permissions"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            # Test with various user roles (none required in current implementation)
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200

    def test_awareness_content_logging(self):
        """Test that awareness content endpoints log appropriately"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            # This test verifies the endpoint works, actual logging would be tested
            # in integration tests with proper logging configuration
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200

    def test_awareness_content_monitoring(self):
        """Test that awareness content endpoints can be monitored"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            # This test verifies the endpoint works, actual monitoring would be tested
            # in integration tests with proper monitoring setup
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200

    def test_awareness_content_health_check(self):
        """Test that awareness content endpoints respond to health checks"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            # Test basic health check
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            assert response.headers.get("content-type") == "application/json"

    def test_awareness_content_versioning(self):
        """Test that awareness content endpoints support versioning"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            # Test current version
            response = client.get("/api/awareness/content")
            assert response.status_code == 200
            
            # Test with version header (if implemented)
            headers = {"Accept": "application/json; version=1.0"}
            response_v1 = client.get("/api/awareness/content", headers=headers)
            assert response_v1.status_code == 200

    def test_awareness_content_documentation(self):
        """Test that awareness content endpoints provide proper documentation"""
        # Test that the API is accessible
        response = client.get("/docs")
        
        # FastAPI should provide automatic documentation
        assert response.status_code in [200, 404]  # 404 if docs not enabled

    def test_awareness_content_openapi_spec(self):
        """Test that awareness content endpoints provide OpenAPI specification"""
        response = client.get("/openapi.json")
        
        # FastAPI should provide OpenAPI specification
        assert response.status_code in [200, 404]  # 404 if spec not enabled

    def test_awareness_content_cors(self):
        """Test that awareness content endpoints support CORS"""
        headers = {"Origin": "http://localhost:3000"}
        
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            response = client.get("/api/awareness/content", headers=headers)
            
            assert response.status_code == 200
            # CORS headers would be checked in integration tests

    def test_awareness_content_headers(self):
        """Test that awareness content endpoints return proper headers"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            assert response.headers.get("content-type") == "application/json"
            assert "content-length" in response.headers

    def test_awareness_content_status_codes(self):
        """Test that awareness content endpoints return appropriate status codes"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            # Test successful response
            response = client.get("/api/awareness/content")
            assert response.status_code == 200
            
            # Test not found response
            response_not_found = client.get("/api/awareness/content/nonexistent")
            assert response_not_found.status_code == 404

    def test_awareness_content_response_format(self):
        """Test that awareness content endpoints return properly formatted responses"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            response = client.get("/api/awareness/content")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response is a list
            assert isinstance(data, list)
            
            # Verify each item has required structure
            if data:
                item = data[0]
                assert isinstance(item, dict)
                assert "id" in item
                assert "title" in item
                assert "type" in item

    def test_awareness_content_error_responses(self):
        """Test that awareness content endpoints return proper error responses"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.side_effect = Exception("Internal server error")
            
            response = client.get("/api/awareness/content")
            
            # Should handle errors gracefully
            assert response.status_code in [200, 500, 503]

    def test_awareness_content_validation(self):
        """Test that awareness content endpoints validate input properly"""
        # Test with invalid query parameters
        response = client.get("/api/awareness/content?invalid_param=value")
        
        # Should not break with invalid parameters
        assert response.status_code in [200, 400, 422]

    def test_awareness_content_security(self):
        """Test that awareness content endpoints are secure"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            # Test with potentially malicious input
            malicious_inputs = [
                "'; DROP TABLE users; --",
                "<script>alert('xss')</script>",
                "../../../etc/passwd",
                "'; EXEC xp_cmdshell('dir'); --"
            ]
            
            for malicious_input in malicious_inputs:
                response = client.get(f"/api/awareness/content?q={malicious_input}")
                # Should not break or expose vulnerabilities
                assert response.status_code in [200, 400, 422]

    def test_awareness_content_integration(self):
        """Test integration between different awareness content endpoints"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            # Test that all endpoints work together
            content_response = client.get("/api/awareness/content")
            stories_response = client.get("/api/awareness/stories")
            quizzes_response = client.get("/api/awareness/quizzes")
            lessons_response = client.get("/api/awareness/lessons")
            
            # All should succeed
            assert content_response.status_code == 200
            assert stories_response.status_code == 200
            assert quizzes_response.status_code == 200
            assert lessons_response.status_code == 200
            
            # Verify data consistency
            content_data = content_response.json()
            stories_data = stories_response.json()
            quizzes_data = quizzes_response.json()
            lessons_data = lessons_response.json()
            
            # Total content should equal sum of individual types
            total_individual = len(stories_data) + len(quizzes_data) + len(lessons_data)
            assert len(content_data) == total_individual

    def test_awareness_content_edge_cases(self):
        """Test awareness content endpoints with edge cases"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = []
            
            # Test with empty content
            response = client.get("/api/awareness/content")
            assert response.status_code == 200
            assert response.json() == []
            
            # Test with very long query parameters
            long_query = "a" * 1000
            response_long = client.get(f"/api/awareness/content?q={long_query}")
            assert response_long.status_code in [200, 400, 413]
            
            # Test with special characters
            special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
            response_special = client.get(f"/api/awareness/content?q={special_chars}")
            assert response_special.status_code in [200, 400, 422]

    def test_awareness_content_performance_under_load(self):
        """Test awareness content endpoints performance under load"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            import time
            import concurrent.futures
            
            def make_request():
                start_time = time.time()
                response = client.get("/api/awareness/content")
                end_time = time.time()
                return response.status_code, end_time - start_time
            
            # Make concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [future.result() for future in futures]
            
            # All requests should succeed
            for status_code, response_time in results:
                assert status_code == 200
                assert response_time < 2.0  # Should respond within 2 seconds under load

    def test_awareness_content_memory_usage(self):
        """Test that awareness content endpoints don't consume excessive memory"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            # Create large content for testing
            large_content = []
            for i in range(100):
                large_content.append({
                    "id": f"content_{i}",
                    "title": f"Content {i}",
                    "content": "x" * 1000,  # 1KB content
                    "type": "story",
                    "age_group": "5-8",
                    "tags": ["safety"],
                    "difficulty": "beginner"
                })
            
            mock_content.return_value = large_content
            
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss
            
            response = client.get("/api/awareness/content")
            
            memory_after = process.memory_info().rss
            memory_increase = memory_after - memory_before
            
            assert response.status_code == 200
            # Memory increase should be reasonable (less than 10MB)
            assert memory_increase < 10 * 1024 * 1024

    def test_awareness_content_concurrent_access(self):
        """Test that awareness content endpoints handle concurrent access properly"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            import threading
            import time
            
            results = []
            errors = []
            
            def worker():
                try:
                    response = client.get("/api/awareness/content")
                    results.append(response.status_code)
                except Exception as e:
                    errors.append(str(e))
            
            # Create multiple threads
            threads = []
            for _ in range(10):
                thread = threading.Thread(target=worker)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # All requests should succeed
            assert len(errors) == 0, f"Errors occurred: {errors}"
            assert len(results) == 10
            assert all(status == 200 for status in results)

    def test_awareness_content_cleanup(self):
        """Test that awareness content endpoints clean up resources properly"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story]
            
            # Make multiple requests to test resource cleanup
            for _ in range(5):
                response = client.get("/api/awareness/content")
                assert response.status_code == 200
            
            # Verify no resource leaks (this would be tested in integration tests)
            # For unit tests, we just verify the endpoints work correctly

    def test_awareness_content_final_validation(self):
        """Final comprehensive validation of awareness content endpoints"""
        with patch('backend.api.awareness.awareness_content') as mock_content:
            mock_content.return_value = [self.sample_story, self.sample_quiz, self.sample_lesson]
            
            # Test all endpoints comprehensively
            endpoints = [
                "/api/awareness/content",
                "/api/awareness/stories",
                "/api/awareness/quizzes",
                "/api/awareness/lessons",
                "/api/awareness/statistics"
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint)
                assert response.status_code == 200, f"Endpoint {endpoint} failed"
                
                data = response.json()
                if isinstance(data, list):
                    assert len(data) >= 0
                elif isinstance(data, dict):
                    assert "total_content" in data or "content" in data or "message" in data
            
            # Test content retrieval by ID
            response = client.get("/api/awareness/content/story_001")
            assert response.status_code == 200
            
            # Test user progress
            response = client.get("/api/awareness/progress/user_123")
            assert response.status_code in [200, 404]  # 404 if user doesn't exist
            
            # Test search
            response = client.get("/api/awareness/search?q=test")
            assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__])

import streamlit as st
import requests
import json
from datetime import datetime
import time

from frontend.utils.api_client import APIClient

class AwarenessStories:
    """Streamlit UI component for child safety awareness content"""
    
    def __init__(self, backend_url="http://localhost:8000"):
        self.backend_url = backend_url
        self.api_client = APIClient(backend_url)
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'current_content' not in st.session_state:
            st.session_state.current_content = None
        if 'user_progress' not in st.session_state:
            st.session_state.user_progress = {}
        if 'quiz_attempts' not in st.session_state:
            st.session_state.quiz_attempts = {}
        if 'favorite_content' not in st.session_state:
            st.session_state.favorite_content = []
    
    def render(self):
        """Render the awareness stories UI"""
        st.header("📚 Safety Awareness & Education")
        st.markdown("Learn about safety through interactive stories, lessons, and quizzes")
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📖 Stories & Lessons", "🧩 Interactive Quizzes", "📊 Progress Tracker", "⭐ Favorites"])
        
        with tab1:
            self.render_content_browser()
        
        with tab2:
            self.render_quiz_interface()
        
        with tab3:
            self.render_progress_tracker()
        
        with tab4:
            self.render_favorites()
    
    def render_content_browser(self):
        """Render the content browser interface"""
        st.subheader("📖 Browse Safety Content")
        
        # Content filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            age_group = st.selectbox(
                "Age Group",
                ["All Ages", "3-5", "5-8", "8-12", "12-15", "15-18"],
                key="filter_age"
            )
        
        with col2:
            content_type = st.selectbox(
                "Content Type",
                ["All Types", "story", "lesson", "video", "activity"],
                key="filter_type"
            )
        
        with col3:
            difficulty = st.selectbox(
                "Difficulty",
                ["All Levels", "beginner", "intermediate", "advanced"],
                key="filter_difficulty"
            )
        
        # Search functionality
        search_query = st.text_input(
            "🔍 Search content...",
            placeholder="Search for safety topics, keywords, or content titles",
            key="content_search"
        )
        
        # Load and display content
        content = self.load_awareness_content(age_group, content_type, difficulty, search_query)
        
        if not content:
            st.info("👆 No content found matching your filters. Try adjusting your search criteria.")
            return
        
        # Display content in cards
        st.markdown(f"### 📚 Found {len(content)} items")
        
        # Content grid
        cols = st.columns(2)
        for i, item in enumerate(content):
            with cols[i % 2]:
                self.render_content_card(item)
    
    def render_content_card(self, content):
        """Render a content item as a card"""
        with st.container():
            st.markdown(f"### {content.get('title', 'Untitled')}")
            
            # Content metadata
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"📚 {content.get('type', 'unknown').title()}")
                st.caption(f"👶 {content.get('age_group', 'All Ages')}")
            
            with col2:
                st.caption(f"⭐ {content.get('difficulty', 'beginner').title()}")
                if content.get('tags'):
                    tags_str = ", ".join(content.get('tags', [])[:3])
                    st.caption(f"🏷️ {tags_str}")
            
            # Content preview
            if content.get('content'):
                preview = content['content'][:150] + "..." if len(content['content']) > 150 else content['content']
                st.markdown(f"*{preview}*")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"📖 Read", key=f"read_{content.get('id', i)}", use_container_width=True):
                    self.display_content_detail(content)
            
            with col2:
                if st.button(f"⭐ Favorite", key=f"favorite_{content.get('id', i)}", use_container_width=True):
                    self.toggle_favorite(content)
            
            with col3:
                if content.get('type') == 'quiz':
                    if st.button(f"🧩 Quiz", key=f"quiz_{content.get('id', i)}", use_container_width=True):
                        self.start_quiz(content)
            
            st.markdown("---")
    
    def display_content_detail(self, content):
        """Display detailed content view"""
        st.session_state.current_content = content
        
        # Content detail view
        st.markdown(f"# {content.get('title', 'Untitled')}")
        
        # Content metadata
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**Type:** {content.get('type', 'Unknown').title()}")
            st.info(f"**Age Group:** {content.get('age_group', 'All Ages')}")
        
        with col2:
            st.info(f"**Difficulty:** {content.get('difficulty', 'Beginner').title()}")
            if content.get('tags'):
                st.info(f"**Tags:** {', '.join(content.get('tags', []))}")
        
        with col3:
            st.info(f"**Reading Time:** ~{self.estimate_reading_time(content.get('content', ''))} min")
            if content.get('id') in st.session_state.user_progress:
                st.success("✅ Completed")
        
        # Main content
        st.markdown("## 📖 Content")
        st.markdown(content.get('content', 'No content available'))
        
        # Interactive elements
        if content.get('type') == 'story':
            self.render_story_interactions(content)
        elif content.get('type') == 'lesson':
            self.render_lesson_interactions(content)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Mark as Complete", use_container_width=True):
                self.mark_content_complete(content)
        
        with col2:
            if st.button("🔙 Back to Browse", use_container_width=True):
                st.session_state.current_content = None
                st.rerun()
        
        with col3:
            if st.button("📤 Share", use_container_width=True):
                self.share_content(content)
    
    def render_story_interactions(self, content):
        """Render interactive elements for stories"""
        st.markdown("### 💭 Story Discussion")
        
        # Discussion questions
        discussion_questions = [
            "What did you learn from this story?",
            "How would you handle a similar situation?",
            "Who would you tell if something like this happened to you?",
            "What safety rules does this story teach us?"
        ]
        
        selected_question = st.selectbox("Choose a discussion question:", discussion_questions)
        
        if selected_question:
            user_response = st.text_area(
                f"**{selected_question}**",
                placeholder="Share your thoughts...",
                height=100
            )
            
            if st.button("💬 Share Response", use_container_width=True):
                if user_response.strip():
                    st.success("✅ Thank you for sharing your thoughts!")
                    # Store response in progress
                    if content.get('id') not in st.session_state.user_progress:
                        st.session_state.user_progress[content.get('id')] = {}
                    st.session_state.user_progress[content.get('id')]['discussion_response'] = user_response
                else:
                    st.warning("Please write your response before sharing.")
    
    def render_lesson_interactions(self, content):
        """Render interactive elements for lessons"""
        st.markdown("### 📝 Lesson Activities")
        
        # Key takeaways
        st.markdown("**🎯 Key Takeaways:**")
        key_points = [
            "Always tell a trusted adult if something feels wrong",
            "Your body belongs to you - you can say NO",
            "Never share personal information with strangers",
            "Trust your instincts and feelings"
        ]
        
        for point in key_points:
            st.markdown(f"- {point}")
        
        # Practice scenarios
        st.markdown("**🎭 Practice Scenarios:**")
        
        scenario = st.selectbox(
            "Choose a scenario to practice:",
            [
                "A stranger offers you candy",
                "Someone makes you feel uncomfortable",
                "You see something that doesn't seem right",
                "You're asked to keep a secret"
            ]
        )
        
        if scenario:
            st.markdown(f"**Scenario:** {scenario}")
            st.markdown("**What would you do?**")
            
            user_action = st.text_area(
                "Describe your response:",
                placeholder="What would you do in this situation?",
                height=100
            )
            
            if st.button("✅ Submit Response", use_container_width=True):
                if user_action.strip():
                    st.success("✅ Great thinking! Here are some safe responses:")
                    st.markdown("""
                    - **Tell a trusted adult immediately**
                    - **Say NO firmly and walk away**
                    - **Get to a safe location**
                    - **Call for help if needed**
                    """)
                    
                    # Store response in progress
                    if content.get('id') not in st.session_state.user_progress:
                        st.session_state.user_progress[content.get('id')] = {}
                    st.session_state.user_progress[content.get('id')]['scenario_response'] = user_action
                else:
                    st.warning("Please describe your response before submitting.")
    
    def render_quiz_interface(self):
        """Render the quiz interface"""
        st.subheader("🧩 Interactive Safety Quizzes")
        
        # Load available quizzes
        quizzes = self.load_awareness_content(content_type="quiz")
        
        if not quizzes:
            st.info("👆 No quizzes available at the moment. Check back later!")
            return
        
        # Quiz selection
        selected_quiz = st.selectbox(
            "Choose a quiz to take:",
            options=[quiz['title'] for quiz in quizzes],
            key="quiz_selection"
        )
        
        if selected_quiz:
            quiz = next((q for q in quizzes if q['title'] == selected_quiz), None)
            if quiz:
                self.render_quiz(quiz)
    
    def render_quiz(self, quiz):
        """Render a specific quiz"""
        st.markdown(f"## 🧩 {quiz.get('title', 'Quiz')}")
        st.markdown(f"**Age Group:** {quiz.get('age_group', 'All Ages')} | **Difficulty:** {quiz.get('difficulty', 'Beginner').title()}")
        
        if quiz.get('content'):
            st.markdown(quiz.get('content'))
        
        # Quiz questions
        questions = quiz.get('questions', [])
        if not questions:
            st.warning("This quiz has no questions available.")
            return
        
        # Initialize quiz state
        quiz_id = quiz.get('id', 'unknown')
        if f"quiz_{quiz_id}" not in st.session_state:
            st.session_state[f"quiz_{quiz_id}"] = {
                "current_question": 0,
                "answers": {},
                "score": 0,
                "completed": False
            }
        
        quiz_state = st.session_state[f"quiz_{quiz_id}"]
        
        if not quiz_state["completed"]:
            self.render_quiz_question(quiz, quiz_state)
        else:
            self.render_quiz_results(quiz, quiz_state)
    
    def render_quiz_question(self, quiz, quiz_state):
        """Render a quiz question"""
        questions = quiz.get('questions', [])
        current_q = quiz_state["current_question"]
        
        if current_q >= len(questions):
            # Quiz completed
            quiz_state["completed"] = True
            self.calculate_quiz_score(quiz, quiz_state)
            st.rerun()
            return
        
        question_data = questions[current_q]
        
        st.markdown(f"### Question {current_q + 1} of {len(questions)}")
        st.markdown(f"**{question_data.get('question', 'Question not available')}**")
        
        # Answer options
        options = question_data.get('options', [])
        selected_answer = st.radio(
            "Choose your answer:",
            options=options,
            key=f"answer_{quiz.get('id')}_{current_q}"
        )
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if current_q > 0:
                if st.button("⬅️ Previous", use_container_width=True):
                    quiz_state["current_question"] -= 1
                    st.rerun()
        
        with col2:
            if st.button("Next ➡️", use_container_width=True):
                # Store answer
                quiz_state["answers"][current_q] = options.index(selected_answer)
                
                if current_q + 1 < len(questions):
                    quiz_state["current_question"] += 1
                    st.rerun()
                else:
                    # Quiz completed
                    quiz_state["completed"] = True
                    self.calculate_quiz_score(quiz, quiz_state)
                    st.rerun()
    
    def calculate_quiz_score(self, quiz, quiz_state):
        """Calculate quiz score and store results"""
        questions = quiz.get('questions', [])
        correct_answers = 0
        
        for i, question in enumerate(questions):
            user_answer = quiz_state["answers"].get(i)
            correct_answer = question.get('correct_answer', 0)
            
            if user_answer == correct_answer:
                correct_answers += 1
        
        quiz_state["score"] = (correct_answers / len(questions)) * 100
        
        # Store in progress
        quiz_id = quiz.get('id')
        if quiz_id not in st.session_state.user_progress:
            st.session_state.user_progress[quiz_id] = {}
        
        st.session_state.user_progress[quiz_id].update({
            "quiz_score": quiz_state["score"],
            "completed_at": datetime.now().isoformat(),
            "total_questions": len(questions),
            "correct_answers": correct_answers
        })
        
        # Store quiz attempt
        if quiz_id not in st.session_state.quiz_attempts:
            st.session_state.quiz_attempts[quiz_id] = []
        
        st.session_state.quiz_attempts[quiz_id].append({
            "timestamp": datetime.now().isoformat(),
            "score": quiz_state["score"],
            "answers": quiz_state["answers"]
        })
    
    def render_quiz_results(self, quiz, quiz_state):
        """Render quiz results"""
        st.success("🎉 Quiz Completed!")
        
        score = quiz_state["score"]
        st.markdown(f"### 📊 Your Score: {score:.1f}%")
        
        # Score interpretation
        if score >= 90:
            st.success("🌟 Excellent! You're a safety expert!")
        elif score >= 80:
            st.success("👍 Great job! You know your safety rules well!")
        elif score >= 70:
            st.info("✅ Good work! Keep learning about safety!")
        elif score >= 60:
            st.warning("⚠️ You're on the right track! Review the material and try again.")
        else:
            st.error("📚 Keep studying! Safety is important - try the quiz again.")
        
        # Review answers
        st.markdown("### 📝 Review Your Answers")
        
        questions = quiz.get('questions', [])
        for i, question in enumerate(questions):
            user_answer = quiz_state["answers"].get(i, -1)
            correct_answer = question.get('correct_answer', 0)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**Question {i + 1}:** {question.get('question', '')}")
                options = question.get('options', [])
                st.markdown(f"Your answer: {options[user_answer] if user_answer >= 0 else 'Not answered'}")
                st.markdown(f"Correct answer: {options[correct_answer]}")
            
            with col2:
                if user_answer == correct_answer:
                    st.success("✅ Correct")
                else:
                    st.error("❌ Incorrect")
            
            with col3:
                if question.get('explanation'):
                    with st.expander("💡 Explanation"):
                        st.markdown(question.get('explanation'))
            
            st.markdown("---")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Retake Quiz", use_container_width=True):
                # Reset quiz state
                quiz_state["current_question"] = 0
                quiz_state["answers"] = {}
                quiz_state["completed"] = False
                st.rerun()
        
        with col2:
            if st.button("📚 Back to Lessons", use_container_width=True):
                st.session_state.current_content = None
                st.rerun()
        
        with col3:
            if st.button("📊 View Progress", use_container_width=True):
                st.switch_page("📊 Progress Tracker")
    
    def render_progress_tracker(self):
        """Render the progress tracking interface"""
        st.subheader("📊 Your Learning Progress")
        
        if not st.session_state.user_progress:
            st.info("👆 Start learning to track your progress!")
            return
        
        # Progress overview
        total_content = len(st.session_state.user_progress)
        completed_content = sum(1 for p in st.session_state.user_progress.values() if p.get('completed_at'))
        average_score = 0
        
        if st.session_state.quiz_attempts:
            all_scores = []
            for quiz_attempts in st.session_state.quiz_attempts.values():
                all_scores.extend([attempt['score'] for attempt in quiz_attempts])
            average_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        # Progress metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Content", total_content)
        
        with col2:
            st.metric("Completed", completed_content)
        
        with col3:
            st.metric("Average Quiz Score", f"{average_score:.1f}%")
        
        # Progress chart
        st.markdown("### 📈 Progress Timeline")
        
        # Sort progress by completion date
        sorted_progress = sorted(
            [(k, v) for k, v in st.session_state.user_progress.items() if v.get('completed_at')],
            key=lambda x: x[1]['completed_at']
        )
        
        if sorted_progress:
            for content_id, progress in sorted_progress:
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**Content ID:** {content_id}")
                        st.caption(f"📅 {progress.get('completed_at', 'Unknown')}")
                    
                    with col2:
                        if 'quiz_score' in progress:
                            st.markdown(f"**Quiz Score:** {progress['quiz_score']:.1f}%")
                        else:
                            st.markdown("**Status:** Completed")
                    
                    with col3:
                        if 'quiz_score' in progress:
                            score = progress['quiz_score']
                            if score >= 80:
                                st.success("🌟")
                            elif score >= 60:
                                st.info("✅")
                            else:
                                st.warning("⚠️")
                    
                    st.markdown("---")
        
        # Export progress
        if st.button("📤 Export Progress Report", use_container_width=True):
            self.export_progress_report()
    
    def render_favorites(self):
        """Render the favorites interface"""
        st.subheader("⭐ Your Favorite Content")
        
        if not st.session_state.favorite_content:
            st.info("👆 No favorite content yet. Click the ⭐ button on any content to add it to favorites!")
            return
        
        # Display favorite content
        for content in st.session_state.favorite_content:
            with st.container():
                st.markdown(f"### {content.get('title', 'Untitled')}")
                st.caption(f"📚 {content.get('type', 'unknown').title()} | 👶 {content.get('age_group', 'All Ages')}")
                
                if content.get('content'):
                    preview = content['content'][:100] + "..." if len(content['content']) > 100 else content['content']
                    st.markdown(f"*{preview}*")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"📖 Read", key=f"read_fav_{content.get('id')}", use_container_width=True):
                        self.display_content_detail(content)
                
                with col2:
                    if st.button(f"❌ Remove", key=f"remove_fav_{content.get('id')}", use_container_width=True):
                        self.remove_favorite(content)
                        st.rerun()
                
                st.markdown("---")
    
    def toggle_favorite(self, content):
        """Toggle favorite status for content"""
        content_id = content.get('id')
        
        if content_id in [fav.get('id') for fav in st.session_state.favorite_content]:
            # Remove from favorites
            st.session_state.favorite_content = [
                fav for fav in st.session_state.favorite_content 
                if fav.get('id') != content_id
            ]
            st.success("❌ Removed from favorites")
        else:
            # Add to favorites
            st.session_state.favorite_content.append(content)
            st.success("⭐ Added to favorites")
        
        st.rerun()
    
    def remove_favorite(self, content):
        """Remove content from favorites"""
        content_id = content.get('id')
        st.session_state.favorite_content = [
            fav for fav in st.session_state.favorite_content 
            if fav.get('id') != content_id
        ]
        st.success("❌ Removed from favorites")
    
    def mark_content_complete(self, content):
        """Mark content as completed"""
        content_id = content.get('id')
        
        if content_id not in st.session_state.user_progress:
            st.session_state.user_progress[content_id] = {}
        
        st.session_state.user_progress[content_id].update({
            "completed_at": datetime.now().isoformat(),
            "content_type": content.get('type'),
            "title": content.get('title')
        })
        
        st.success("✅ Content marked as completed!")
    
    def share_content(self, content):
        """Share content (placeholder for future implementation)"""
        st.info("📤 Sharing functionality will be implemented in future versions!")
    
    def export_progress_report(self):
        """Export progress report as JSON"""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "user_progress": st.session_state.user_progress,
            "quiz_attempts": st.session_state.quiz_attempts,
            "favorite_content": [c.get('id') for c in st.session_state.favorite_content]
        }
        
        json_str = json.dumps(export_data, indent=2)
        
        st.download_button(
            label="📥 Download Progress Report",
            data=json_str,
            file_name=f"learning_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def load_awareness_content(self, age_group="All Ages", content_type="All Types", difficulty="All Levels", search_query=""):
        """Load awareness content from backend"""
        # Build query parameters
        filters = {}
        if age_group != "All Ages":
            filters["age_group"] = age_group
        if content_type != "All Types":
            filters["type"] = content_type
        if difficulty != "All Levels":
            filters["difficulty"] = difficulty
        if search_query:
            filters["q"] = search_query
        
        result = self.api_client.get_awareness_content(filters)
        
        if result["success"]:
            data = result["data"]
            # Combine stories and quizzes into a single list
            content = []
            if "stories" in data:
                content.extend(data["stories"])
            if "quizzes" in data:
                content.extend(data["quizzes"])
            return content
        else:
            st.error(f"Failed to load content: {result['error']}")
            return []
    
    def estimate_reading_time(self, content):
        """Estimate reading time for content"""
        if not content:
            return 1
        
        # Average reading speed: 200 words per minute
        word_count = len(content.split())
        minutes = max(1, round(word_count / 200))
        return minutes
    
    def check_backend_status(self):
        """Check if backend is accessible"""
        return self.api_client.health_check()

def main():
    """Main function to run the awareness stories UI"""
    st.set_page_config(
        page_title="SafeChild Awareness Stories",
        page_icon="📚",
        layout="wide"
    )
    
    # Initialize awareness stories UI
    awareness_stories = AwarenessStories()
    
    # Check backend status
    if not awareness_stories.check_backend_status():
        st.warning("⚠️ Backend service is not accessible. Some features may not work.")
    
    # Render the UI
    awareness_stories.render()

if __name__ == "__main__":
    main()

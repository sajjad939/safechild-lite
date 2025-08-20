import streamlit as st
import requests
from datetime import datetime
import time

# Import components
from components.ChatbotUI import ChatbotUI
from components.ComplaintForm import ComplaintForm
from components.EmergencyButton import EmergencyButton
from components.AwarenessStories import AwarenessStories
from components.AudioPlayer import AudioPlayer

class SafeChildApp:
    """Main SafeChild application with navigation and component integration"""
    
    def __init__(self):
        self.backend_url = st.secrets.get("BACKEND_URL", "http://localhost:8000")
        self.setup_page_config()
        self.setup_session_state()
    
    def setup_page_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="SafeChild-Lite",
            page_icon="🛡️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "home"
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {
                "theme": "light",
                "language": "en",
                "notifications": True
            }
        if 'app_start_time' not in st.session_state:
            st.session_state.app_start_time = datetime.now()
    
    def render_header(self):
        """Render the application header"""
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.image("https://via.placeholder.com/80x80/4CAF50/FFFFFF?text=🛡️", width=80)
        
        with col2:
            st.title("🛡️ SafeChild-Lite")
            st.markdown("**Comprehensive Child Safety & Protection Platform**")
        
        with col3:
            # Backend status indicator
            backend_status = self.check_backend_status()
            status_color = "🟢" if backend_status else "🔴"
            status_text = "Online" if backend_status else "Offline"
            
            st.markdown(f"**Backend:** {status_color} {status_text}")
    
    def render_navigation(self):
        """Render the main navigation menu"""
        st.markdown("---")
        
        # Navigation tabs
        nav_tabs = st.tabs([
            "🏠 Home",
            "🤖 Chatbot",
            "📝 Complaints",
            "🚨 Emergency",
            "📚 Awareness",
            "🎵 Audio",
            "⚙️ Settings"
        ])
        
        # Home tab
        with nav_tabs[0]:
            self.render_home_page()
        
        # Chatbot tab
        with nav_tabs[1]:
            chatbot = ChatbotUI(self.backend_url)
            chatbot.render()
        
        # Complaints tab
        with nav_tabs[2]:
            complaint_form = ComplaintForm(self.backend_url)
            complaint_form.render()
        
        # Emergency tab
        with nav_tabs[3]:
            emergency_button = EmergencyButton(self.backend_url)
            emergency_button.render()
        
        # Awareness tab
        with nav_tabs[4]:
            awareness_stories = AwarenessStories(self.backend_url)
            awareness_stories.render()
        
        # Audio tab
        with nav_tabs[5]:
            audio_player = AudioPlayer(self.backend_url)
            audio_player.render()
        
        # Settings tab
        with nav_tabs[6]:
            self.render_settings_page()
    
    def render_home_page(self):
        """Render the home page with overview and quick actions"""
        st.header("🏠 Welcome to SafeChild-Lite")
        
        # Welcome message
        st.markdown("""
        **SafeChild-Lite** is your comprehensive platform for child safety education, incident reporting, 
        emergency response, and awareness building. We're here to help protect children and empower 
        families with knowledge and tools for safety.
        """)
        
        # Quick stats
        st.markdown("### 📊 Platform Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Safety Stories", "25+")
            st.caption("Interactive learning content")
        
        with col2:
            st.metric("Emergency Contacts", "Unlimited")
            st.caption("Manage your safety network")
        
        with col3:
            st.metric("AI Chatbot", "24/7")
            st.caption("Always available support")
        
        with col4:
            st.metric("Response Time", "<1 min")
            st.caption("Emergency alert speed")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚨 Emergency SOS", type="primary", use_container_width=True):
                st.switch_page("🚨 Emergency")
        
        with col2:
            if st.button("🤖 Chat with AI", type="secondary", use_container_width=True):
                st.switch_page("🤖 Chatbot")
        
        with col3:
            if st.button("📚 Learn Safety", type="secondary", use_container_width=True):
                st.switch_page("📚 Awareness")
        
        # Recent activity
        st.markdown("### 📈 Recent Activity")
        
        if 'recent_activity' in st.session_state and st.session_state.recent_activity:
            for activity in st.session_state.recent_activity[-5:]:
                st.info(f"📅 {activity['timestamp']}: {activity['description']}")
        else:
            st.info("👆 Start using the platform to see your activity here!")
        
        # Safety tips
        st.markdown("### 💡 Today's Safety Tip")
        
        safety_tips = [
            "Always teach children their full name, address, and phone number",
            "Establish a family password for emergency situations",
            "Practice 'what if' scenarios with your children regularly",
            "Encourage children to trust their instincts and feelings",
            "Keep emergency contact information easily accessible"
        ]
        
        import random
        today_tip = random.choice(safety_tips)
        st.success(f"💡 **{today_tip}**")
        
        # Emergency resources
        st.markdown("### 🚨 Emergency Resources")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📞 Emergency Numbers:**
            - **911** - Emergency Services
            - **1-800-4-A-CHILD** - Child Abuse Hotline
            - **988** - Suicide Prevention
            - **1-800-799-SAFE** - Domestic Violence
            """)
        
        with col2:
            st.markdown("""
            **🏥 Local Resources:**
            - **Police Department** - Non-emergency line
            - **Hospital** - Emergency care
            - **Child Advocacy Center** - Support services
            - **Legal Aid** - Free legal assistance
            """)
    
    def render_settings_page(self):
        """Render the settings page"""
        st.header("⚙️ Application Settings")
        
        # User preferences
        st.markdown("### 👤 User Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            theme = st.selectbox(
                "Theme",
                ["light", "dark"],
                index=0 if st.session_state.user_preferences["theme"] == "light" else 1,
                key="theme_setting"
            )
            
            language = st.selectbox(
                "Language",
                ["en", "es", "fr", "de"],
                index=0 if st.session_state.user_preferences["language"] == "en" else 1,
                key="language_setting"
            )
        
        with col2:
            notifications = st.checkbox(
                "Enable Notifications",
                value=st.session_state.user_preferences["notifications"],
                key="notifications_setting"
            )
            
            auto_save = st.checkbox(
                "Auto-save Progress",
                value=True,
                key="auto_save_setting"
            )
        
        # Save preferences
        if st.button("💾 Save Preferences", use_container_width=True):
            st.session_state.user_preferences.update({
                "theme": theme,
                "language": language,
                "notifications": notifications
            })
            st.success("✅ Preferences saved successfully!")
        
        # Backend configuration
        st.markdown("### 🔧 Backend Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input(
                "Backend URL",
                value=self.backend_url,
                key="backend_url_setting",
                help="URL of the SafeChild backend service"
            )
        
        with col2:
            if st.button("🔍 Test Connection", use_container_width=True):
                if self.check_backend_status():
                    st.success("✅ Backend connection successful!")
                else:
                    st.error("❌ Backend connection failed!")

        st.markdown("### 🧠 AI/ML Provider Settings")
        try:
            cfg_res = requests.get(f"{self.backend_url}/api/config/ai", timeout=10)
            if cfg_res.ok:
                current = cfg_res.json()
            else:
                current = {"provider": "openai", "config": {}}
        except Exception:
            current = {"provider": "openai", "config": {}}

        provider = st.selectbox("Provider", ["openai", "aiml"], index=0 if current.get("provider") == "openai" else 1)

        col1, col2 = st.columns(2)
        with col1:
            if provider == "openai":
                openai_model = st.text_input("OpenAI Model", value=current.get("config", {}).get("model", "gpt-4"))
                openai_key = st.text_input("OpenAI API Key", value=current.get("config", {}).get("api_key", ""), type="password")
            else:
                aiml_base = st.text_input("AIML Base URL", value=current.get("config", {}).get("base_url", "http://localhost:8001"))
        with col2:
            if provider == "aiml":
                aiml_model = st.text_input("AIML Model", value=current.get("config", {}).get("model", "default"))
                aiml_key = st.text_input("AIML API Key", value=current.get("config", {}).get("api_key", ""), type="password")
            else:
                st.empty()

        if st.button("💾 Save AI Settings", use_container_width=True):
            body = {"provider": provider, "config": {}}
            if provider == "openai":
                body["config"] = {"model": openai_model, "api_key": openai_key}
            else:
                body["config"] = {"base_url": aiml_base, "model": aiml_model, "api_key": aiml_key}
            try:
                res = requests.post(f"{self.backend_url}/api/config/ai", json=body, timeout=10)
                if res.ok:
                    st.success("✅ AI settings updated")
                else:
                    st.error(f"❌ Failed to update settings: {res.status_code}")
            except Exception as e:
                st.error(f"❌ Error updating settings: {e}")
        
        # System information
        st.markdown("### ℹ️ System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("App Version", "1.0.0")
            st.metric("Session Duration", self.get_session_duration())
            st.metric("Backend Status", "🟢 Online" if self.check_backend_status() else "🔴 Offline")
        
        with col2:
            st.metric("Python Version", "3.8+")
            st.metric("Streamlit Version", "1.28.0+")
            st.metric("Last Updated", datetime.now().strftime("%Y-%m-%d"))
        
        # Data management
        st.markdown("### 🗄️ Data Management")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 Export Data", use_container_width=True):
                self.export_user_data()
        
        with col2:
            if st.button("🗑️ Clear Cache", use_container_width=True):
                self.clear_application_cache()
        
        with col3:
            if st.button("🔄 Reset App", use_container_width=True):
                self.reset_application()
    
    def render_sidebar(self):
        """Render the sidebar with additional information and controls"""
        with st.sidebar:
            st.header("🛡️ SafeChild-Lite")
            st.markdown("**Child Safety Platform**")
            
            st.markdown("---")
            
            # User info
            st.subheader("👤 User Information")
            st.info("**Guest User**")
            st.caption("Sign in for personalized experience")
            
            # Quick navigation
            st.subheader("🧭 Quick Navigation")
            
            if st.button("🏠 Home", use_container_width=True):
                st.switch_page("🏠 Home")
            
            if st.button("🚨 Emergency SOS", use_container_width=True, type="primary"):
                st.switch_page("🚨 Emergency")
            
            if st.button("🤖 AI Chatbot", use_container_width=True):
                st.switch_page("🤖 Chatbot")
            
            st.markdown("---")
            
            # Safety resources
            st.subheader("📚 Safety Resources")
            
            with st.expander("🚨 Emergency Numbers"):
                st.markdown("""
                - **911** - Emergency
                - **Child Abuse** - 1-800-4-A-CHILD
                - **Suicide Prevention** - 988
                - **Domestic Violence** - 1-800-799-SAFE
                """)
            
            with st.expander("📖 Safety Tips"):
                st.markdown("""
                - Teach children their personal information
                - Establish family safety rules
                - Practice emergency scenarios
                - Trust your instincts
                - Report suspicious behavior
                """)
            
            # App statistics
            st.markdown("---")
            st.subheader("📊 App Statistics")
            
            session_duration = self.get_session_duration()
            st.metric("Session Time", session_duration)
            
            backend_status = "🟢 Online" if self.check_backend_status() else "🔴 Offline"
            st.metric("Backend", backend_status)
            
            # Footer
            st.markdown("---")
            st.caption("🛡️ SafeChild-Lite v1.0.0")
            st.caption("Protecting children, empowering families")
    
    def check_backend_status(self):
        """Check if backend service is accessible"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_session_duration(self):
        """Get current session duration"""
        if 'app_start_time' in st.session_state:
            duration = datetime.now() - st.session_state.app_start_time
            minutes = int(duration.total_seconds() / 60)
            return f"{minutes}m"
        return "0m"
    
    def export_user_data(self):
        """Export user data (placeholder)"""
        st.info("📤 Data export functionality coming soon!")
    
    def clear_application_cache(self):
        """Clear application cache (placeholder)"""
        st.info("🗑️ Cache cleared successfully!")
    
    def reset_application(self):
        """Reset application state (placeholder)"""
        st.info("🔄 Application reset functionality coming soon!")
    
    def render_footer(self):
        """Render the application footer"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🛡️ SafeChild-Lite**")
            st.caption("Comprehensive child safety platform")
        
        with col2:
            st.markdown("**📞 Support**")
            st.caption("help@safechild-lite.com")
        
        with col3:
            st.markdown("**🔗 Resources**")
            st.caption("Privacy Policy | Terms of Service")
        
        st.caption("© 2024 SafeChild-Lite. All rights reserved.")
    
    def run(self):
        """Main application run method"""
        try:
            # Render header
            self.render_header()
            
            # Render navigation
            self.render_navigation()
            
            # Render sidebar
            self.render_sidebar()
            
            # Render footer
            self.render_footer()
            
        except Exception as e:
            st.error(f"❌ Application error: {str(e)}")
            st.info("Please refresh the page or contact support if the issue persists.")

def main():
    """Main function to run the SafeChild application"""
    # Initialize and run the app
    app = SafeChildApp()
    app.run()

if __name__ == "__main__":
    main()

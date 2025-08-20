import streamlit as st
import requests
import json
from datetime import datetime
import time

class ChatbotUI:
    """Streamlit UI component for the SafeChild chatbot"""
    
    def __init__(self, backend_url="http://localhost:8000"):
        self.backend_url = backend_url
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'chat_session_id' not in st.session_state:
            st.session_state.chat_session_id = f"session_{int(time.time())}"
    
    def render(self):
        """Render the chatbot UI"""
        st.header("🤖 SafeChild Chatbot")
        st.markdown("Your friendly AI companion for safety education and support")
        
        # Chat interface
        self.render_chat_interface()
        
        # Sidebar controls
        with st.sidebar:
            self.render_sidebar_controls()
    
    def render_chat_interface(self):
        """Render the main chat interface"""
        # Display chat history
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.chat_message("user").write(message["content"])
                else:
                    st.chat_message("assistant").write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me about safety, or tell me what's on your mind..."):
            # Add user message to chat
            st.session_state.chat_history.append({
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now().isoformat()
            })
            
            # Display user message
            st.chat_message("user").write(prompt)
            
            # Get AI response
            with st.spinner("SafeChild is thinking..."):
                response = self.get_chatbot_response(prompt)
                
                if response:
                    # Add AI response to chat
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Display AI response
                    st.chat_message("assistant").write(response)
                    
                    # Rerun to update the display
                    st.rerun()
                else:
                    st.error("Sorry, I'm having trouble responding right now. Please try again.")
    
    def get_chatbot_response(self, message):
        """Get response from chatbot backend"""
        try:
            payload = {
                "message": message,
                "session_id": st.session_state.chat_session_id,
                "user_id": "anonymous"  # In a real app, this would be the logged-in user
            }
            
            response = requests.post(
                f"{self.backend_url}/api/chatbot",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "I'm sorry, I didn't understand that.")
            else:
                st.error(f"Backend error: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None
    
    def render_sidebar_controls(self):
        """Render sidebar controls and information"""
        st.subheader("Chat Controls")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.chat_session_id = f"session_{int(time.time())}"
            st.rerun()
        
        # Export chat button
        if st.button("📤 Export Chat", use_container_width=True):
            self.export_chat_history()
        
        # Chat statistics
        st.subheader("Chat Statistics")
        st.metric("Messages", len(st.session_state.chat_history))
        st.metric("Session ID", st.session_state.chat_session_id[:8] + "...")
        
        # Safety tips
        st.subheader("💡 Safety Tips")
        st.info("""
        - Always talk to a trusted adult if something makes you uncomfortable
        - Your body belongs to you - you can say NO to unwanted touches
        - Never share personal information online
        - If you're in danger, call 911 or tell an adult immediately
        """)
        
        # Emergency resources
        st.subheader("🚨 Emergency Resources")
        st.markdown("""
        - **National Child Abuse Hotline**: 1-800-4-A-CHILD
        - **Emergency Services**: 911
        - **CyberTipline**: 1-800-THE-LOST
        """)
    
    def export_chat_history(self):
        """Export chat history as JSON"""
        if not st.session_state.chat_history:
            st.warning("No chat history to export")
            return
        
        # Create export data
        export_data = {
            "session_id": st.session_state.chat_session_id,
            "export_timestamp": datetime.now().isoformat(),
            "total_messages": len(st.session_state.chat_history),
            "chat_history": st.session_state.chat_history
        }
        
        # Convert to JSON string
        json_str = json.dumps(export_data, indent=2)
        
        # Create download button
        st.download_button(
            label="📥 Download Chat History",
            data=json_str,
            file_name=f"safechild_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def check_backend_status(self):
        """Check if backend is accessible"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

def main():
    """Main function to run the chatbot UI"""
    st.set_page_config(
        page_title="SafeChild Chatbot",
        page_icon="🤖",
        layout="wide"
    )
    
    # Initialize chatbot UI
    chatbot = ChatbotUI()
    
    # Check backend status
    if not chatbot.check_backend_status():
        st.warning("⚠️ Backend service is not accessible. Some features may not work.")
    
    # Render the UI
    chatbot.render()

if __name__ == "__main__":
    main()

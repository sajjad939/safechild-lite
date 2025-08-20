import streamlit as st
import requests
import json
from datetime import datetime
import time
import base64

class AudioPlayer:
    """Streamlit UI component for text-to-speech and audio playback"""
    
    def __init__(self, backend_url="http://localhost:8000"):
        self.backend_url = backend_url
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'audio_history' not in st.session_state:
            st.session_state.audio_history = []
        if 'current_audio' not in st.session_state:
            st.session_state.current_audio = None
        if 'tts_settings' not in st.session_state:
            st.session_state.tts_settings = {
                "language": "en",
                "speed": 1.0,
                "voice": "default"
            }
    
    def render(self):
        """Render the audio player UI"""
        st.header("🎵 Text-to-Speech & Audio Player")
        st.markdown("Convert text to speech and manage your audio content")
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🎤 Text to Speech", "🎵 Audio Player", "📚 Audio History", "⚙️ Settings"])
        
        with tab1:
            self.render_tts_interface()
        
        with tab2:
            self.render_audio_player()
        
        with tab3:
            self.render_audio_history()
        
        with tab4:
            self.render_tts_settings()
    
    def render_tts_interface(self):
        """Render the text-to-speech interface"""
        st.subheader("🎤 Convert Text to Speech")
        
        # Text input
        text_input = st.text_area(
            "Enter text to convert to speech:",
            placeholder="Type or paste the text you want to convert to speech...",
            height=150,
            key="tts_text_input"
        )
        
        # TTS options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            language = st.selectbox(
                "Language",
                ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                index=0,
                key="tts_language"
            )
        
        with col2:
            speed = st.slider(
                "Speed",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                key="tts_speed"
            )
        
        with col3:
            voice = st.selectbox(
                "Voice",
                ["default", "male", "female", "child", "elderly"],
                key="tts_voice"
            )
        
        # Generate audio button
        if st.button("🎵 Generate Audio", type="primary", use_container_width=True):
            if text_input.strip():
                self.generate_audio(text_input, language, speed, voice)
            else:
                st.warning("⚠️ Please enter some text to convert to speech.")
        
        # Quick text examples
        st.markdown("### 💡 Quick Examples")
        
        examples = [
            "Hello! Welcome to SafeChild. Let's learn about safety together!",
            "Remember: your body belongs to you. You can say NO to unwanted touches.",
            "If something makes you feel uncomfortable, tell a trusted adult immediately.",
            "Safety first! Always look both ways before crossing the street."
        ]
        
        cols = st.columns(2)
        for i, example in enumerate(examples):
            with cols[i % 2]:
                if st.button(f"🎤 {example[:30]}...", key=f"example_{i}", use_container_width=True):
                    st.session_state.tts_text_input = example
                    st.rerun()
    
    def generate_audio(self, text, language, speed, voice):
        """Generate audio from text using backend TTS service"""
        try:
            with st.spinner("🎵 Generating audio..."):
                payload = {
                    "text": text,
                    "language": language,
                    "speed": speed,
                    "voice": voice
                }
                
                response = requests.post(
                    f"{self.backend_url}/api/tts",
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Store in audio history
                    audio_item = {
                        "id": data.get("audio_id", f"audio_{int(time.time())}"),
                        "text": text,
                        "language": language,
                        "speed": speed,
                        "voice": voice,
                        "audio_url": data.get("audio_url"),
                        "audio_data": data.get("audio_data"),
                        "duration": data.get("duration", 0),
                        "created_at": datetime.now().isoformat(),
                        "file_size": data.get("file_size", 0)
                    }
                    
                    st.session_state.audio_history.append(audio_item)
                    st.session_state.current_audio = audio_item
                    
                    st.success("✅ Audio generated successfully!")
                    st.balloons()
                    
                    # Auto-play the generated audio
                    st.rerun()
                    
                else:
                    st.error(f"❌ Failed to generate audio: {response.status_code}")
                    
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Connection error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
    
    def render_audio_player(self):
        """Render the audio player interface"""
        st.subheader("🎵 Audio Player")
        
        if not st.session_state.current_audio:
            st.info("👆 Generate some audio first to use the player!")
            return
        
        current_audio = st.session_state.current_audio
        
        # Audio information
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Audio ID:** {current_audio.get('id', 'Unknown')}")
            st.info(f"**Language:** {current_audio.get('language', 'Unknown').upper()}")
        
        with col2:
            st.info(f"**Speed:** {current_audio.get('speed', 1.0)}x")
            st.info(f"**Voice:** {current_audio.get('voice', 'Unknown').title()}")
        
        # Audio playback
        st.markdown("### 🎵 Play Audio")
        
        if current_audio.get('audio_data'):
            # Convert base64 audio data to bytes
            try:
                audio_bytes = base64.b64decode(current_audio['audio_data'])
                
                # Display audio player
                st.audio(audio_bytes, format="audio/mp3")
                
                # Audio controls
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🔄 Regenerate", use_container_width=True):
                        self.regenerate_audio(current_audio)
                
                with col2:
                    if st.button("📥 Download", use_container_width=True):
                        self.download_audio(current_audio, audio_bytes)
                
                with col3:
                    if st.button("⭐ Add to Favorites", use_container_width=True):
                        self.add_to_favorites(current_audio)
                
            except Exception as e:
                st.error(f"❌ Error playing audio: {str(e)}")
        
        elif current_audio.get('audio_url'):
            # External audio URL
            st.audio(current_audio['audio_url'], format="audio/mp3")
            
            # Audio controls
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Regenerate", use_container_width=True):
                    self.regenerate_audio(current_audio)
            
            with col2:
                if st.button("📥 Download", use_container_width=True):
                    self.download_audio_url(current_audio)
        
        # Text display
        st.markdown("### 📝 Original Text")
        st.text_area(
            "Text used to generate this audio:",
            value=current_audio.get('text', ''),
            height=100,
            disabled=True
        )
        
        # Audio statistics
        st.markdown("### 📊 Audio Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            duration = current_audio.get('duration', 0)
            st.metric("Duration", f"{duration:.1f}s")
        
        with col2:
            file_size = current_audio.get('file_size', 0)
            if file_size > 0:
                size_kb = file_size / 1024
                st.metric("File Size", f"{size_kb:.1f} KB")
            else:
                st.metric("File Size", "Unknown")
        
        with col3:
            st.metric("Created", datetime.fromisoformat(current_audio['created_at']).strftime("%H:%M"))
    
    def render_audio_history(self):
        """Render the audio history interface"""
        st.subheader("📚 Audio History")
        
        if not st.session_state.audio_history:
            st.info("👆 No audio generated yet. Start by converting some text to speech!")
            return
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            filter_language = st.selectbox(
                "Filter by Language",
                ["All Languages"] + list(set(item.get('language', 'en') for item in st.session_state.audio_history)),
                key="history_language_filter"
            )
        
        with col2:
            filter_voice = st.selectbox(
                "Filter by Voice",
                ["All Voices"] + list(set(item.get('voice', 'default') for item in st.session_state.audio_history)),
                key="history_voice_filter"
            )
        
        # Apply filters
        filtered_history = st.session_state.audio_history
        
        if filter_language != "All Languages":
            filtered_history = [item for item in filtered_history if item.get('language') == filter_language]
        
        if filter_voice != "All Voices":
            filtered_history = [item for item in filtered_history if item.get('voice') == filter_voice]
        
        # Display history
        st.markdown(f"### 📚 Found {len(filtered_history)} audio items")
        
        for i, audio_item in enumerate(reversed(filtered_history)):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**Audio ID:** {audio_item.get('id', 'Unknown')}")
                    st.caption(f"📅 {audio_item['created_at']}")
                    st.caption(f"🌍 {audio_item.get('language', 'en').upper()} | 🎤 {audio_item.get('voice', 'default').title()}")
                    
                    # Text preview
                    text = audio_item.get('text', '')
                    preview = text[:100] + "..." if len(text) > 100 else text
                    st.markdown(f"*{preview}*")
                
                with col2:
                    if st.button(f"🎵 Play", key=f"play_{i}", use_container_width=True):
                        st.session_state.current_audio = audio_item
                        st.switch_page("🎵 Audio Player")
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"delete_{i}", use_container_width=True):
                        self.delete_audio_item(i)
                        st.rerun()
                
                st.markdown("---")
        
        # Export history
        if st.button("📤 Export Audio History", use_container_width=True):
            self.export_audio_history()
    
    def render_tts_settings(self):
        """Render TTS settings interface"""
        st.subheader("⚙️ Text-to-Speech Settings")
        
        # Language settings
        st.markdown("### 🌍 Language Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_language = st.selectbox(
                "Default Language",
                ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                index=0,
                key="default_language"
            )
        
        with col2:
            auto_detect = st.checkbox(
                "Auto-detect language from text",
                value=True,
                help="Automatically detect the language of input text"
            )
        
        # Voice settings
        st.markdown("### 🎤 Voice Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_voice = st.selectbox(
                "Default Voice",
                ["default", "male", "female", "child", "elderly"],
                key="default_voice"
            )
        
        with col2:
            voice_preview = st.checkbox(
                "Enable voice preview",
                value=True,
                help="Play a short preview when selecting different voices"
            )
        
        # Quality settings
        st.markdown("### 🎵 Quality Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_speed = st.slider(
                "Default Speed",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                key="default_speed"
            )
        
        with col2:
            audio_format = st.selectbox(
                "Audio Format",
                ["mp3", "wav", "ogg"],
                key="audio_format"
            )
        
        # Advanced settings
        st.markdown("### 🔧 Advanced Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cache_audio = st.checkbox(
                "Cache generated audio",
                value=True,
                help="Store generated audio for faster playback"
            )
        
        with col2:
            auto_play = st.checkbox(
                "Auto-play generated audio",
                value=True,
                help="Automatically play audio after generation"
            )
        
        # Save settings
        if st.button("💾 Save Settings", use_container_width=True):
            self.save_tts_settings(
                default_language, default_voice, default_speed, audio_format,
                auto_detect, voice_preview, cache_audio, auto_play
            )
        
        # System information
        st.markdown("### ℹ️ System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            backend_status = "🟢 Online" if self.check_backend_status() else "🔴 Offline"
            st.metric("Backend Status", backend_status)
            
            st.metric("Audio History", len(st.session_state.audio_history))
        
        with col2:
            st.metric("Current Audio", "Yes" if st.session_state.current_audio else "No")
            
            if st.session_state.audio_history:
                total_duration = sum(item.get('duration', 0) for item in st.session_state.audio_history)
                st.metric("Total Duration", f"{total_duration:.1f}s")
    
    def regenerate_audio(self, audio_item):
        """Regenerate audio with current settings"""
        st.info("🔄 Regenerating audio...")
        
        # Use current TTS settings
        language = st.session_state.tts_language
        speed = st.session_state.tts_speed
        voice = st.session_state.tts_voice
        
        self.generate_audio(audio_item['text'], language, speed, voice)
    
    def download_audio(self, audio_item, audio_bytes):
        """Download audio file"""
        if not audio_bytes:
            st.error("❌ No audio data available for download")
            return
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio_{audio_item.get('id', 'unknown')}_{timestamp}.mp3"
        
        st.download_button(
            label="📥 Download Audio",
            data=audio_bytes,
            file_name=filename,
            mime="audio/mp3"
        )
    
    def download_audio_url(self, audio_item):
        """Download audio from URL"""
        if not audio_item.get('audio_url'):
            st.error("❌ No audio URL available for download")
            return
        
        try:
            response = requests.get(audio_item['audio_url'], timeout=30)
            
            if response.status_code == 200:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"audio_{audio_item.get('id', 'unknown')}_{timestamp}.mp3"
                
                st.download_button(
                    label="📥 Download Audio",
                    data=response.content,
                    file_name=filename,
                    mime="audio/mp3"
                )
            else:
                st.error(f"❌ Failed to download audio: {response.status_code}")
                
        except Exception as e:
            st.error(f"❌ Download error: {str(e)}")
    
    def add_to_favorites(self, audio_item):
        """Add audio to favorites (placeholder)"""
        st.success("⭐ Added to favorites! (Feature coming soon)")
    
    def delete_audio_item(self, index):
        """Delete audio item from history"""
        if 0 <= index < len(st.session_state.audio_history):
            deleted_item = st.session_state.audio_history.pop(index)
            st.success(f"✅ Audio item '{deleted_item.get('id', 'Unknown')}' deleted successfully!")
        else:
            st.error("❌ Invalid audio item index.")
    
    def export_audio_history(self):
        """Export audio history as JSON"""
        if not st.session_state.audio_history:
            st.warning("No audio history to export")
            return
        
        # Prepare export data (exclude large audio data)
        export_data = []
        for item in st.session_state.audio_history:
            export_item = item.copy()
            # Remove large audio data for export
            export_item.pop('audio_data', None)
            export_data.append(export_item)
        
        export_payload = {
            "export_timestamp": datetime.now().isoformat(),
            "total_audio_items": len(export_data),
            "audio_history": export_data
        }
        
        json_str = json.dumps(export_payload, indent=2)
        
        st.download_button(
            label="📥 Download Audio History",
            data=json_str,
            file_name=f"audio_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def save_tts_settings(self, *args):
        """Save TTS settings"""
        (default_language, default_voice, default_speed, audio_format,
         auto_detect, voice_preview, cache_audio, auto_play) = args
        
        # Update session state
        st.session_state.tts_settings.update({
            "language": default_language,
            "voice": default_voice,
            "speed": default_speed,
            "format": audio_format,
            "auto_detect": auto_detect,
            "voice_preview": voice_preview,
            "cache_audio": cache_audio,
            "auto_play": auto_play
        })
        
        st.success("✅ TTS settings saved successfully!")
    
    def check_backend_status(self):
        """Check if backend is accessible"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

def main():
    """Main function to run the audio player UI"""
    st.set_page_config(
        page_title="SafeChild Audio Player",
        page_icon="🎵",
        layout="wide"
    )
    
    # Initialize audio player UI
    audio_player = AudioPlayer()
    
    # Check backend status
    if not audio_player.check_backend_status():
        st.warning("⚠️ Backend service is not accessible. Some features may not work.")
    
    # Render the UI
    audio_player.render()

if __name__ == "__main__":
    main()

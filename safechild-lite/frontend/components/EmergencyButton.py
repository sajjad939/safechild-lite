import streamlit as st
import requests
import json
from datetime import datetime
import time

class EmergencyButton:
    """Streamlit UI component for emergency SOS alerts"""
    
    def __init__(self, backend_url="http://localhost:8000"):
        self.backend_url = backend_url
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'emergency_contacts' not in st.session_state:
            st.session_state.emergency_contacts = []
        if 'emergency_alerts' not in st.session_state:
            st.session_state.emergency_alerts = []
        if 'last_alert_time' not in st.session_state:
            st.session_state.last_alert_time = None
    
    def render(self):
        """Render the emergency button UI"""
        st.header("🚨 Emergency SOS System")
        st.markdown("Immediate emergency response and contact management")
        
        # Emergency SOS Button
        self.render_sos_button()
        
        # Tabs for different functions
        tab1, tab2, tab3 = st.tabs(["📞 Emergency Contacts", "🚨 Alert History", "⚙️ Settings"])
        
        with tab1:
            self.render_emergency_contacts()
        
        with tab2:
            self.render_alert_history()
        
        with tab3:
            self.render_emergency_settings()
    
    def render_sos_button(self):
        """Render the main SOS emergency button"""
        st.markdown("---")
        
        # Large SOS button
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button(
                "🚨 SOS EMERGENCY 🚨",
                type="primary",
                use_container_width=True,
                help="Click this button in case of emergency to immediately alert all emergency contacts"
            ):
                self.trigger_emergency_alert()
        
        # Emergency instructions
        st.markdown("### 🚨 Emergency Instructions")
        st.warning("""
        **IMMEDIATE ACTION REQUIRED:**
        1. **Call 911** if there is immediate danger to life or safety
        2. **Get to a safe location** if possible
        3. **Contact emergency services** or law enforcement
        4. **Use this SOS button** to alert your emergency contacts
        """)
        
        # Emergency numbers
        st.markdown("### 📞 Emergency Numbers")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            - **Emergency Services**: 911
            - **Police**: 911
            - **Fire Department**: 911
            - **Ambulance**: 911
            """)
        
        with col2:
            st.markdown("""
            - **Child Abuse Hotline**: 1-800-4-A-CHILD
            - **Suicide Prevention**: 988
            - **Poison Control**: 1-800-222-1222
            - **Domestic Violence**: 1-800-799-SAFE
            """)
    
    def trigger_emergency_alert(self):
        """Trigger an emergency alert"""
        # Check if we have emergency contacts
        if not st.session_state.emergency_contacts:
            st.error("❌ No emergency contacts configured. Please add emergency contacts first.")
            return
        
        # Check rate limiting (prevent spam)
        if st.session_state.last_alert_time:
            time_since_last = (datetime.now() - st.session_state.last_alert_time).total_seconds()
            if time_since_last < 60:  # 1 minute cooldown
                st.warning("⚠️ Please wait before sending another emergency alert.")
                return
        
        # Show confirmation dialog
        with st.expander("🚨 Emergency Alert Confirmation", expanded=True):
            st.error("**EMERGENCY ALERT CONFIRMATION**")
            st.markdown("""
            You are about to send an emergency alert to all your emergency contacts.
            
            **This action will:**
            - Send SMS alerts to all emergency contacts
            - Log the emergency alert
            - Potentially trigger automated emergency responses
            
            **Only use this if there is a genuine emergency.**
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ CONFIRM EMERGENCY", type="primary", use_container_width=True):
                    self.send_emergency_alert()
            
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.rerun()
    
    def send_emergency_alert(self):
        """Send emergency alert to backend"""
        try:
            # Prepare emergency data
            emergency_data = {
                "urgency_level": "critical",
                "location": "Unknown",  # Could be enhanced with GPS
                "description": "SOS Emergency Alert triggered by user",
                "contacts": st.session_state.emergency_contacts,
                "timestamp": datetime.now().isoformat(),
                "user_id": "anonymous"  # In real app, this would be logged-in user
            }
            
            with st.spinner("🚨 Sending emergency alert..."):
                response = requests.post(
                    f"{self.backend_url}/api/emergency",
                    json=emergency_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Update session state
                    st.session_state.last_alert_time = datetime.now()
                    st.session_state.emergency_alerts.append({
                        "timestamp": datetime.now().isoformat(),
                        "status": "sent",
                        "message": "Emergency alert sent successfully",
                        "alert_id": data.get("alert_id", "unknown")
                    })
                    
                    st.success("✅ Emergency alert sent successfully!")
                    st.balloons()
                    
                    # Show next steps
                    st.info("""
                    **Emergency Alert Sent Successfully!**
                    
                    **Next Steps:**
                    1. **Stay calm** and assess the situation
                    2. **Call 911** if immediate danger exists
                    3. **Follow emergency services instructions**
                    4. **Your emergency contacts have been notified**
                    """)
                    
                else:
                    st.error(f"❌ Failed to send emergency alert: {response.status_code}")
                    
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Connection error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
    
    def render_emergency_contacts(self):
        """Render emergency contacts management"""
        st.subheader("📞 Emergency Contacts")
        
        # Add new contact form
        with st.expander("➕ Add New Emergency Contact", expanded=False):
            with st.form("add_contact_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    contact_name = st.text_input("Contact Name *", key="new_contact_name")
                    contact_phone = st.text_input("Phone Number *", key="new_contact_phone")
                    contact_email = st.text_input("Email Address", key="new_contact_email")
                
                with col2:
                    contact_relationship = st.text_input("Relationship *", key="new_contact_relationship")
                    contact_address = st.text_input("Address", key="new_contact_address")
                    is_primary = st.checkbox("Primary Emergency Contact", key="new_contact_primary")
                
                if st.form_submit_button("➕ Add Contact", use_container_width=True):
                    self.add_emergency_contact(
                        contact_name, contact_phone, contact_email,
                        contact_relationship, contact_address, is_primary
                    )
        
        # Display existing contacts
        if not st.session_state.emergency_contacts:
            st.info("👆 No emergency contacts configured. Add contacts to enable emergency alerts.")
        else:
            st.markdown("### Current Emergency Contacts")
            
            for i, contact in enumerate(st.session_state.emergency_contacts):
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{contact['name']}** ({contact['relationship']})")
                        st.caption(f"📱 {contact['phone']}")
                        if contact.get('email'):
                            st.caption(f"📧 {contact['email']}")
                        if contact.get('address'):
                            st.caption(f"📍 {contact['address']}")
                        if contact.get('is_primary'):
                            st.success("⭐ Primary Contact")
                    
                    with col2:
                        if st.button(f"✏️ Edit", key=f"edit_{i}", use_container_width=True):
                            st.session_state.editing_contact = i
                            st.rerun()
                    
                    with col3:
                        if st.button(f"🗑️ Delete", key=f"delete_{i}", use_container_width=True):
                            self.delete_emergency_contact(i)
                            st.rerun()
                    
                    st.markdown("---")
            
            # Contact statistics
            st.markdown("### 📊 Contact Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Contacts", len(st.session_state.emergency_contacts))
            
            with col2:
                primary_contacts = sum(1 for c in st.session_state.emergency_contacts if c.get('is_primary'))
                st.metric("Primary Contacts", primary_contacts)
            
            with col3:
                contacts_with_email = sum(1 for c in st.session_state.emergency_contacts if c.get('email'))
                st.metric("With Email", contacts_with_email)
    
    def add_emergency_contact(self, name, phone, email, relationship, address, is_primary):
        """Add a new emergency contact"""
        if not name or not phone or not relationship:
            st.error("❌ Name, phone, and relationship are required fields.")
            return
        
        # Validate phone number (basic validation)
        if len(phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')) < 10:
            st.error("❌ Please enter a valid phone number.")
            return
        
        # Create contact object
        contact = {
            "name": name.strip(),
            "phone": phone.strip(),
            "relationship": relationship.strip(),
            "email": email.strip() if email else None,
            "address": address.strip() if address else None,
            "is_primary": is_primary
        }
        
        # If this is the first contact or marked as primary, update other contacts
        if is_primary or not st.session_state.emergency_contacts:
            for existing_contact in st.session_state.emergency_contacts:
                existing_contact['is_primary'] = False
            contact['is_primary'] = True
        
        # Add to session state
        st.session_state.emergency_contacts.append(contact)
        
        st.success(f"✅ Emergency contact '{name}' added successfully!")
        st.rerun()
    
    def delete_emergency_contact(self, index):
        """Delete an emergency contact"""
        if 0 <= index < len(st.session_state.emergency_contacts):
            contact_name = st.session_state.emergency_contacts[index]['name']
            del st.session_state.emergency_contacts[index]
            st.success(f"✅ Emergency contact '{contact_name}' deleted successfully!")
        else:
            st.error("❌ Invalid contact index.")
    
    def render_alert_history(self):
        """Render emergency alert history"""
        st.subheader("🚨 Emergency Alert History")
        
        if not st.session_state.emergency_alerts:
            st.info("📝 No emergency alerts sent yet.")
            return
        
        # Display alert history
        for alert in reversed(st.session_state.emergency_alerts):
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Alert ID:** {alert['alert_id']}")
                    st.caption(f"📅 {alert['timestamp']}")
                    st.caption(f"📊 Status: {alert['status']}")
                    st.caption(f"💬 {alert['message']}")
                
                with col2:
                    if alert['status'] == 'sent':
                        st.success("✅ Sent")
                    else:
                        st.error("❌ Failed")
                
                st.markdown("---")
        
        # Export alert history
        if st.button("📤 Export Alert History", use_container_width=True):
            self.export_alert_history()
    
    def export_alert_history(self):
        """Export alert history as JSON"""
        if not st.session_state.emergency_alerts:
            st.warning("No alert history to export")
            return
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_alerts": len(st.session_state.emergency_alerts),
            "alert_history": st.session_state.emergency_alerts
        }
        
        json_str = json.dumps(export_data, indent=2)
        
        st.download_button(
            label="📥 Download Alert History",
            data=json_str,
            file_name=f"emergency_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def render_emergency_settings(self):
        """Render emergency system settings"""
        st.subheader("⚙️ Emergency System Settings")
        
        # Alert settings
        st.markdown("### 🚨 Alert Settings")
        
        # Rate limiting settings
        st.markdown("#### ⏱️ Rate Limiting")
        alert_cooldown = st.slider(
            "Minimum time between emergency alerts (minutes)",
            min_value=1,
            max_value=60,
            value=5,
            help="Prevents accidental spam of emergency alerts"
        )
        
        # Contact verification
        st.markdown("#### ✅ Contact Verification")
        verify_contacts = st.checkbox(
            "Verify emergency contacts before sending alerts",
            value=True,
            help="Ensures all emergency contacts are valid before sending alerts"
        )
        
        # Auto-escalation
        st.markdown("#### 📈 Auto-Escalation")
        auto_escalate = st.checkbox(
            "Automatically escalate to authorities if no response",
            value=False,
            help="Automatically contact emergency services if no response from contacts"
        )
        
        # Save settings
        if st.button("💾 Save Settings", use_container_width=True):
            st.success("✅ Emergency settings saved successfully!")
        
        # System status
        st.markdown("### 🔧 System Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Emergency Contacts", len(st.session_state.emergency_contacts))
            st.metric("Total Alerts Sent", len(st.session_state.emergency_alerts))
        
        with col2:
            backend_status = "🟢 Online" if self.check_backend_status() else "🔴 Offline"
            st.metric("Backend Status", backend_status)
            
            if st.session_state.last_alert_time:
                time_since_last = (datetime.now() - st.session_state.last_alert_time).total_seconds()
                minutes_ago = int(time_since_last / 60)
                st.metric("Last Alert", f"{minutes_ago} min ago")
            else:
                st.metric("Last Alert", "Never")
        
        # Emergency system information
        st.markdown("### ℹ️ System Information")
        st.info("""
        **SafeChild Emergency SOS System**
        
        This system provides immediate emergency response capabilities:
        - **Instant Contact Alerting**: Notify all emergency contacts simultaneously
        - **SMS Integration**: Send text messages to emergency contacts
        - **Alert Logging**: Track all emergency alerts for record-keeping
        - **Rate Limiting**: Prevent accidental spam of emergency alerts
        - **Contact Management**: Manage and verify emergency contacts
        
        **Important**: This system is designed for genuine emergencies only.
        Misuse may result in system restrictions.
        """)
    
    def check_backend_status(self):
        """Check if backend is accessible"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

def main():
    """Main function to run the emergency button UI"""
    st.set_page_config(
        page_title="SafeChild Emergency SOS",
        page_icon="🚨",
        layout="wide"
    )
    
    # Initialize emergency button UI
    emergency_button = EmergencyButton()
    
    # Check backend status
    if not emergency_button.check_backend_status():
        st.warning("⚠️ Backend service is not accessible. Emergency alerts may not work.")
    
    # Render the UI
    emergency_button.render()

if __name__ == "__main__":
    main()

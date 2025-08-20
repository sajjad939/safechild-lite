import streamlit as st
import requests
import json
from datetime import datetime, date
import time

from frontend.utils.api_client import APIClient

class ComplaintForm:
    """Streamlit UI component for incident complaint reporting"""
    
    def __init__(self, backend_url="http://localhost:8000"):
        self.backend_url = backend_url
        self.api_client = APIClient(backend_url)
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'complaint_data' not in st.session_state:
            st.session_state.complaint_data = {}
        if 'generated_complaint' not in st.session_state:
            st.session_state.generated_complaint = None
        if 'complaint_id' not in st.session_state:
            st.session_state.complaint_id = None
    
    def render(self):
        """Render the complaint form UI"""
        st.header("📝 Incident Report Form")
        st.markdown("Report incidents and generate professional complaint drafts")
        
        # Form tabs
        tab1, tab2, tab3 = st.tabs(["📋 Report Incident", "📄 Generated Draft", "📊 Status"])
        
        with tab1:
            self.render_incident_form()
        
        with tab2:
            self.render_generated_draft()
        
        with tab3:
            self.render_complaint_status()
    
    def render_incident_form(self):
        """Render the incident reporting form"""
        st.subheader("Incident Details")
        
        with st.form("incident_form", clear_on_submit=False):
            # Child Information
            st.markdown("### 👶 Child Information")
            col1, col2 = st.columns(2)
            
            with col1:
                child_name = st.text_input("Child's Full Name *", key="child_name")
                child_age = st.number_input("Child's Age *", min_value=0, max_value=18, value=8, key="child_age")
                child_gender = st.selectbox("Child's Gender", 
                    ["", "Male", "Female", "Non-binary", "Other", "Prefer not to say"], key="child_gender")
            
            with col2:
                child_school = st.text_input("School/Institution", key="child_school")
                child_grade = st.text_input("Grade Level", key="child_grade")
                child_contact = st.text_input("Child's Contact Info", key="child_contact")
            
            # Incident Information
            st.markdown("### 🚨 Incident Information")
            col1, col2 = st.columns(2)
            
            with col1:
                incident_date = st.date_input("Incident Date *", key="incident_date")
                incident_time = st.time_input("Incident Time *", key="incident_time")
                incident_type = st.selectbox("Type of Incident *", [
                    "", "Physical Abuse", "Verbal Abuse", "Bullying", 
                    "Inappropriate Touching", "Harassment", "Neglect", 
                    "Cyber Bullying", "Sexual Harassment", "Emotional Abuse", "Other"
                ], key="incident_type")
            
            with col2:
                location = st.text_input("Location *", key="location")
                priority = st.selectbox("Priority Level", [
                    "Low", "Medium", "High", "Urgent", "Critical"
                ], key="priority")
            
            incident_description = st.text_area(
                "Detailed Description of Incident *", 
                height=150,
                placeholder="Please provide a detailed description of what happened, including any relevant details, witnesses, and evidence...",
                key="incident_description"
            )
            
            # Guardian Information
            st.markdown("### 👨‍👩‍👧‍👦 Guardian Information")
            col1, col2 = st.columns(2)
            
            with col1:
                guardian_name = st.text_input("Guardian's Full Name *", key="guardian_name")
                guardian_phone = st.text_input("Guardian's Phone *", key="guardian_phone")
                guardian_email = st.text_input("Guardian's Email", key="guardian_email")
            
            with col2:
                guardian_address = st.text_input("Guardian's Address", key="guardian_address")
                guardian_relationship = st.text_input("Relationship to Child", key="guardian_relationship")
            
            # Additional Details
            st.markdown("### 📋 Additional Details")
            witnesses = st.text_area("Witnesses (if any)", key="witnesses")
            evidence = st.text_area("Available Evidence/Documentation", key="evidence")
            previous_incidents = st.text_area("Previous Similar Incidents", key="previous_incidents")
            
            # Legal Preferences
            st.markdown("### ⚖️ Legal Preferences")
            col1, col2 = st.columns(2)
            
            with col1:
                wants_legal_action = st.checkbox("Seek Legal Action", key="wants_legal_action")
                wants_mediation = st.checkbox("Request Mediation", key="wants_mediation")
            
            with col2:
                wants_restraining_order = st.checkbox("Request Restraining Order", key="wants_restraining_order")
                wants_compensation = st.checkbox("Seek Compensation", key="wants_compensation")
            
            additional_requests = st.text_area("Additional Requests or Concerns", key="additional_requests")
            
            # Submit button
            submitted = st.form_submit_button("🚀 Generate Complaint Draft", type="primary", use_container_width=True)
            
            if submitted:
                self.process_complaint_form(
                    child_name, child_age, child_gender, child_school, child_grade, child_contact,
                    incident_date, incident_time, incident_type, location, priority, incident_description,
                    guardian_name, guardian_phone, guardian_email, guardian_address, guardian_relationship,
                    witnesses, evidence, previous_incidents,
                    wants_legal_action, wants_mediation, wants_restraining_order, wants_compensation,
                    additional_requests
                )
    
    def process_complaint_form(self, *args):
        """Process the complaint form and generate draft"""
        # Extract arguments
        (child_name, child_age, child_gender, child_school, child_grade, child_contact,
         incident_date, incident_time, incident_type, location, priority, incident_description,
         guardian_name, guardian_phone, guardian_email, guardian_address, guardian_relationship,
         witnesses, evidence, previous_incidents,
         wants_legal_action, wants_mediation, wants_restraining_order, wants_compensation,
         additional_requests) = args
        
        # Validate required fields
        required_fields = {
            "Child's Name": child_name,
            "Child's Age": child_age,
            "Incident Date": incident_date,
            "Incident Time": incident_time,
            "Incident Type": incident_type,
            "Location": location,
            "Incident Description": incident_description,
            "Guardian's Name": guardian_name,
            "Guardian's Phone": guardian_phone
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        
        if missing_fields:
            st.error(f"Please fill in all required fields: {', '.join(missing_fields)}")
            return
        
        # Prepare complaint data
        complaint_data = {
            "child_name": child_name,
            "child_age": child_age,
            "child_gender": child_gender if child_gender else None,
            "child_school": child_school if child_school else None,
            "child_grade": child_grade if child_grade else None,
            "child_contact": child_contact if child_contact else None,
            "incident_date": incident_date.strftime("%Y-%m-%d"),
            "incident_time": incident_time.strftime("%H:%M"),
            "incident_type": incident_type.lower().replace(" ", "_"),
            "location": location,
            "incident_description": incident_description,
            "guardian_name": guardian_name,
            "guardian_phone": guardian_phone,
            "guardian_email": guardian_email if guardian_email else None,
            "guardian_address": guardian_address if guardian_address else None,
            "witnesses": witnesses if witnesses else None,
            "evidence": evidence if evidence else None,
            "previous_incidents": previous_incidents if previous_incidents else None,
            "wants_legal_action": wants_legal_action,
            "wants_mediation": wants_mediation,
            "wants_restraining_order": wants_restraining_order,
            "wants_compensation": wants_compensation,
            "additional_requests": additional_requests if additional_requests else None
        }
        
        # Store in session state
        st.session_state.complaint_data = complaint_data
        
        # Generate complaint draft
        with st.spinner("Generating professional complaint draft..."):
            success = self.generate_complaint_draft(complaint_data)
            
            if success:
                st.success("✅ Complaint draft generated successfully!")
                st.balloons()
                # Switch to the generated draft tab
                st.switch_page("📄 Generated Draft")
            else:
                st.error("❌ Failed to generate complaint draft. Please try again.")
    
    def generate_complaint_draft(self, complaint_data):
        """Send complaint data to backend for draft generation"""
        result = self.api_client.submit_complaint(complaint_data)
        
        if result["success"]:
            data = result["data"]
            st.session_state.generated_complaint = data.get("complaint_text")
            st.session_state.complaint_id = data.get("complaint_id")
            return True
        else:
            st.error(f"Complaint generation failed: {result['error']}")
            return False
    
    def render_generated_draft(self):
        """Render the generated complaint draft"""
        if not st.session_state.generated_complaint:
            st.info("👆 Please fill out the incident form to generate a complaint draft.")
            return
        
        st.subheader("Generated Complaint Draft")
        
        # Display the draft
        st.markdown("### 📄 Professional Complaint Draft")
        st.text_area(
            "Generated Complaint",
            value=st.session_state.generated_complaint,
            height=400,
            disabled=True,
            key="display_draft"
        )
        
        # Download options
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Download as PDF", use_container_width=True):
                self.download_complaint("pdf")
        
        with col2:
            if st.button("📄 Download as Word", use_container_width=True):
                self.download_complaint("docx")
        
        # Edit and regenerate options
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✏️ Edit and Regenerate", use_container_width=True):
                st.switch_page("📋 Report Incident")
        
        with col2:
            if st.button("🔄 Generate New Draft", use_container_width=True):
                self.regenerate_complaint()
        
        # Complaint metadata
        if st.session_state.complaint_id:
            st.info(f"**Complaint ID:** {st.session_state.complaint_id}")
    
    def download_complaint(self, format_type):
        """Download complaint in specified format"""
        if not st.session_state.complaint_id:
            st.error("No complaint available for download")
            return
        
        try:
            response = requests.get(
                f"{self.backend_url}/api/complaint/{st.session_state.complaint_id}/download/{format_type}",
                timeout=30
            )
            
            if response.status_code == 200:
                # Create download button
                file_extension = "pdf" if format_type == "pdf" else "docx"
                mime_type = "application/pdf" if format_type == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                
                st.download_button(
                    label=f"📥 Download {format_type.upper()}",
                    data=response.content,
                    file_name=f"complaint_{st.session_state.complaint_id}.{file_extension}",
                    mime=mime_type
                )
            else:
                st.error(f"Download failed: {response.status_code}")
                
        except Exception as e:
            st.error(f"Download error: {str(e)}")
    
    def regenerate_complaint(self):
        """Regenerate the complaint draft"""
        if not st.session_state.complaint_data:
            st.error("No complaint data available for regeneration")
            return
        
        with st.spinner("Regenerating complaint draft..."):
            success = self.generate_complaint_draft(st.session_state.complaint_data)
            
            if success:
                st.success("✅ Complaint draft regenerated successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to regenerate complaint draft")
    
    def render_complaint_status(self):
        """Render complaint status and tracking"""
        st.subheader("📊 Complaint Status")
        
        if not st.session_state.complaint_id:
            st.info("No complaint submitted yet. Submit a complaint to track its status.")
            return
        
        # Display complaint status
        st.info(f"**Complaint ID:** {st.session_state.complaint_id}")
        
        # Status timeline
        st.markdown("### 📈 Status Timeline")
        
        timeline_data = [
            {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "Draft Generated", "description": "Professional complaint draft created"},
            {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "Submitted", "description": "Ready for review and submission"}
        ]
        
        for item in timeline_data:
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f"**{item['date']}**")
                with col2:
                    st.markdown(f"**{item['status']}** - {item['description']}")
                st.markdown("---")
        
        # Next steps
        st.markdown("### 🎯 Next Steps")
        st.markdown("""
        1. **Review the generated draft** for accuracy and completeness
        2. **Make any necessary edits** to the incident details
        3. **Download the final version** in your preferred format
        4. **Submit to appropriate authorities** or legal professionals
        5. **Keep a copy** for your records
        """)
        
        # Contact information
        st.markdown("### 📞 Need Help?")
        st.markdown("""
        - **Legal Aid Services**: Contact your local legal aid office
        - **Child Advocacy Centers**: Find resources in your area
        - **Emergency**: Call 911 for immediate danger
        - **National Hotline**: 1-800-4-A-CHILD for child abuse concerns
        """)
    
    def check_backend_status(self):
        """Check if backend is accessible"""
        return self.api_client.health_check()

def main():
    """Main function to run the complaint form UI"""
    st.set_page_config(
        page_title="SafeChild Complaint Form",
        page_icon="📝",
        layout="wide"
    )
    
    # Initialize complaint form UI
    complaint_form = ComplaintForm()
    
    # Check backend status
    if not complaint_form.check_backend_status():
        st.warning("⚠️ Backend service is not accessible. Some features may not work.")
    
    # Render the UI
    complaint_form.render()

if __name__ == "__main__":
    main()

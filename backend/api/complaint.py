from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import logging
from datetime import datetime
import uuid
import os
import io

# Import services
from backend.services.gptService import GPTService
from backend.services.pdfService import PDFService
from utils.textCleaner import TextCleaner
from utils.timeUtils import TimeUtils
from backend.models.complaintModel import ComplaintData, PriorityLevel, IncidentType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/complaint", tags=["complaint"])

class ComplaintRequest(BaseModel):
    child_name: str
    child_age: int
    child_gender: Optional[str] = None
    child_school: Optional[str] = None
    child_grade: Optional[str] = None
    child_contact: Optional[str] = None
    incident_date: str
    incident_time: str
    location: str
    incident_type: str
    incident_description: str
    guardian_name: str
    guardian_phone: str
    guardian_email: Optional[str] = None
    guardian_address: Optional[str] = None
    witnesses: Optional[str] = None
    evidence: Optional[str] = None
    previous_incidents: Optional[str] = None
    wants_legal_action: bool = False
    wants_mediation: bool = False
    wants_restraining_order: bool = False
    wants_compensation: bool = False
    additional_requests: Optional[str] = None
    submission_timestamp: Optional[str] = None

class ComplaintResponse(BaseModel):
    complaint_id: str
    status: str
    complaint_text: str
    submission_timestamp: str
    generated_at: str
    download_urls: Dict[str, str]

class ComplaintAPI:
    def __init__(self):
        self.gpt_service = GPTService()
        self.pdf_service = PDFService()
        self.text_cleaner = TextCleaner()
        self.time_utils = TimeUtils()
        
        # In-memory complaint storage (in production, use a database)
        self.complaints: Dict[str, Dict[str, Any]] = {}
        
        # Complaint templates
        self.complaint_templates = {
            "physical_abuse": "physical_abuse_template.txt",
            "verbal_abuse": "verbal_abuse_template.txt",
            "bullying": "bullying_template.txt",
            "inappropriate_touching": "inappropriate_touching_template.txt",
            "harassment": "harassment_template.txt",
            "neglect": "neglect_template.txt",
            "other": "general_template.txt"
        }
    
    def create_complaint_id(self) -> str:
        """Generate unique complaint ID"""
        return f"COMP_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
    
    def validate_complaint_data(self, data: ComplaintRequest) -> List[str]:
        """Validate complaint data"""
        errors = []
        
        if not data.child_name.strip():
            errors.append("Child's name is required")
        
        if data.child_age < 1 or data.child_age > 18:
            errors.append("Child's age must be between 1 and 18")
        
        if not data.incident_description.strip():
            errors.append("Incident description is required")
        
        if not data.location.strip():
            errors.append("Location is required")
        
        if not data.guardian_name.strip():
            errors.append("Guardian's name is required")
        
        if not data.guardian_phone.strip():
            errors.append("Guardian's phone number is required")
        
        return errors
    
    def _to_incident_dict(self, data: ComplaintRequest) -> Dict[str, Any]:
        return {
            "incident_type": data.incident_type,
            "priority": "medium",
            "date": data.incident_date,
            "child_age": data.child_age,
            "child_gender": data.child_gender or "",
            "description": data.incident_description,
            "guardian_name": data.guardian_name,
            "guardian_contact": data.guardian_phone,
        }

    async def generate_complaint_draft(self, data: ComplaintRequest) -> str:
        """Generate complaint draft using GPT-5"""
        try:
            incident = self._to_incident_dict(data)
            result = await self.gpt_service.generate_complaint_draft(incident, template_type="formal")
            if result.get("success") and result.get("complaint_draft"):
                return result["complaint_draft"]
            return self.generate_from_template(data)
        except Exception as e:
            logger.error(f"Error generating complaint draft: {str(e)}")
            return self.generate_from_template(data)
    
    def create_complaint_prompt(self, data: ComplaintRequest) -> str:
        """Create detailed prompt for complaint generation"""
        prompt = f"""
        Generate a professional, legally-sound complaint draft for a child safety incident.
        
        Incident Details:
        - Child: {data.child_name} (Age: {data.child_age}, Gender: {data.child_gender or 'Not specified'})
        - School/Institution: {data.child_school or 'Not specified'}
        - Incident Type: {data.incident_type}
        - Date: {data.incident_date}
        - Time: {data.incident_time}
        - Location: {data.location}
        - Description: {data.incident_description}
        
        Guardian Information:
        - Name: {data.guardian_name}
        - Phone: {data.guardian_phone}
        - Email: {data.guardian_email or 'Not provided'}
        - Address: {data.guardian_address or 'Not provided'}
        
        Additional Information:
        - Witnesses: {data.witnesses or 'None reported'}
        - Evidence: {data.evidence or 'None provided'}
        - Previous Incidents: {data.previous_incidents or 'None reported'}
        
        Legal Preferences:
        - Legal Action: {'Yes' if data.wants_legal_action else 'No'}
        - Mediation: {'Yes' if data.wants_mediation else 'No'}
        - Restraining Order: {'Yes' if data.wants_restraining_order else 'No'}
        - Compensation: {'Yes' if data.wants_compensation else 'No'}
        
        Additional Requests: {data.additional_requests or 'None'}
        
        Requirements:
        1. Use formal, professional language
        2. Include all relevant details
        3. Structure as an official complaint
        4. Include appropriate legal terminology
        5. Be specific about requested actions
        6. Maintain child's privacy and dignity
        7. Follow standard complaint format
        
        Generate a comprehensive complaint draft that can be submitted to authorities.
        """
        
        return prompt
    
    def generate_from_template(self, data: ComplaintRequest) -> str:
        """Generate complaint from template if GPT fails"""
        template = self.get_complaint_template(data.incident_type)
        
        # Replace placeholders in template
        complaint_text = template.replace("{CHILD_NAME}", data.child_name)
        complaint_text = complaint_text.replace("{CHILD_AGE}", str(data.child_age))
        complaint_text = complaint_text.replace("{INCIDENT_TYPE}", data.incident_type)
        complaint_text = complaint_text.replace("{INCIDENT_DATE}", data.incident_date)
        complaint_text = complaint_text.replace("{INCIDENT_TIME}", data.incident_time)
        complaint_text = complaint_text.replace("{LOCATION}", data.location)
        complaint_text = complaint_text.replace("{INCIDENT_DESCRIPTION}", data.incident_description)
        complaint_text = complaint_text.replace("{GUARDIAN_NAME}", data.guardian_name)
        complaint_text = complaint_text.replace("{GUARDIAN_PHONE}", data.guardian_phone)
        complaint_text = complaint_text.replace("{GUARDIAN_EMAIL}", data.guardian_email or "Not provided")
        complaint_text = complaint_text.replace("{GUARDIAN_ADDRESS}", data.guardian_address or "Not provided")
        complaint_text = complaint_text.replace("{WITNESSES}", data.witnesses or "None reported")
        complaint_text = complaint_text.replace("{EVIDENCE}", data.evidence or "None provided")
        complaint_text = complaint_text.replace("{PREVIOUS_INCIDENTS}", data.previous_incidents or "None reported")
        
        # Add legal preferences
        legal_actions = []
        if data.wants_legal_action:
            legal_actions.append("pursue legal action")
        if data.wants_mediation:
            legal_actions.append("mediate this matter")
        if data.wants_restraining_order:
            legal_actions.append("obtain a restraining order")
        if data.wants_compensation:
            legal_actions.append("seek appropriate compensation")
        
        if legal_actions:
            complaint_text += f"\n\nRequested Actions: We request to {', '.join(legal_actions)}."
        
        if data.additional_requests:
            complaint_text += f"\n\nAdditional Requests: {data.additional_requests}"
        
        return complaint_text
    
    def get_complaint_template(self, incident_type: str) -> str:
        """Get complaint template based on incident type"""
        # Default template
        default_template = """
        OFFICIAL COMPLAINT

        Date: {INCIDENT_DATE}
        Time: {INCIDENT_TIME}
        Location: {LOCATION}

        COMPLAINANT INFORMATION:
        Name: {GUARDIAN_NAME}
        Phone: {GUARDIAN_PHONE}
        Email: {GUARDIAN_EMAIL}
        Address: {GUARDIAN_ADDRESS}

        VICTIM INFORMATION:
        Name: {CHILD_NAME}
        Age: {CHILD_AGE}
        Relationship to Complainant: Child

        INCIDENT DETAILS:
        Type of Incident: {INCIDENT_TYPE}
        Date of Incident: {INCIDENT_DATE}
        Time of Incident: {INCIDENT_TIME}
        Location of Incident: {LOCATION}

        DESCRIPTION OF INCIDENT:
        {INCIDENT_DESCRIPTION}

        WITNESSES:
        {WITNESSES}

        EVIDENCE:
        {EVIDENCE}

        PREVIOUS INCIDENTS:
        {PREVIOUS_INCIDENTS}

        REQUESTED ACTIONS:
        We request a thorough investigation of this matter and appropriate action to ensure the safety and well-being of our child.

        We are available for any additional information or interviews that may be required.

        Sincerely,
        {GUARDIAN_NAME}
        Date: {INCIDENT_DATE}
        """
        
        return default_template
    
    async def process_complaint(self, request: ComplaintRequest) -> ComplaintResponse:
        """Process complaint and generate draft"""
        try:
            # Validate data
            errors = self.validate_complaint_data(request)
            if errors:
                raise HTTPException(status_code=400, detail=f"Validation errors: {', '.join(errors)}")
            
            # Generate complaint ID
            complaint_id = self.create_complaint_id()
            
            # Generate complaint draft
            complaint_text = await self.generate_complaint_draft(request)
            
            # Store complaint
            complaint_data = {
                "complaint_id": complaint_id,
                "status": "Draft Generated",
                "complaint_text": complaint_text,
                "submission_timestamp": request.submission_timestamp or self.time_utils.get_current_timestamp(),
                "generated_at": self.time_utils.get_current_timestamp(),
                "request_data": request.dict(),
                "download_urls": {
                    "pdf": f"/api/complaint/{complaint_id}/download/pdf",
                    "docx": f"/api/complaint/{complaint_id}/download/docx"
                }
            }
            
            self.complaints[complaint_id] = complaint_data
            
            logger.info(f"Generated complaint draft: {complaint_id}")
            
            # Create response
            response = ComplaintResponse(
                complaint_id=complaint_id,
                status=complaint_data["status"],
                complaint_text=complaint_text,
                submission_timestamp=complaint_data["submission_timestamp"],
                generated_at=complaint_data["generated_at"],
                download_urls=complaint_data["download_urls"]
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing complaint: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def _build_complaint_model(self, stored: Dict[str, Any]) -> ComplaintData:
        req = stored["request_data"]
        try:
            incident_type = IncidentType(req.get("incident_type", "other"))
        except Exception:
            incident_type = IncidentType.OTHER
        return ComplaintData(
            complaint_id=stored["complaint_id"],
            status="draft",
            priority=PriorityLevel.MEDIUM,
            child_name=req.get("child_name"),
            child_age=req.get("child_age"),
            child_gender=req.get("child_gender"),
            child_school=req.get("child_school"),
            child_grade=req.get("child_grade"),
            child_contact=req.get("child_contact"),
            incident_type=incident_type,
            incident_date=req.get("incident_date"),
            incident_time=req.get("incident_time"),
            location=req.get("location"),
            incident_description=req.get("incident_description"),
            guardian_name=req.get("guardian_name"),
            guardian_phone=req.get("guardian_phone"),
            guardian_email=req.get("guardian_email"),
            guardian_address=req.get("guardian_address"),
            witnesses=req.get("witnesses"),
            evidence=req.get("evidence"),
            previous_incidents=req.get("previous_incidents"),
            wants_legal_action=req.get("wants_legal_action", False),
            wants_mediation=req.get("wants_mediation", False),
            wants_restraining_order=req.get("wants_restraining_order", False),
            wants_compensation=req.get("wants_compensation", False),
            additional_requests=req.get("additional_requests"),
            complaint_text=stored.get("complaint_text")
        )

    async def generate_document(self, complaint_id: str, fmt: str) -> bytes:
        stored = self.complaints.get(complaint_id)
        if not stored:
            raise HTTPException(status_code=404, detail="Complaint not found")
        model = self._build_complaint_model(stored)
        result = await self.pdf_service.generate_complaint_document(model, document_type=fmt)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Document generation failed"))
        return result.get("document_data", b"")

    def get_complaint(self, complaint_id: str) -> Dict[str, Any]:
        """Get complaint by ID"""
        if complaint_id not in self.complaints:
            raise HTTPException(status_code=404, detail="Complaint not found")
        return self.complaints[complaint_id]
    
    def get_all_complaints(self) -> List[Dict[str, Any]]:
        """Get all complaints"""
        return list(self.complaints.values())
    
    def update_complaint_status(self, complaint_id: str, status: str) -> Dict[str, Any]:
        """Update complaint status"""
        if complaint_id not in self.complaints:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        self.complaints[complaint_id]["status"] = status
        self.complaints[complaint_id]["updated_at"] = self.time_utils.get_current_timestamp()
        
        return self.complaints[complaint_id]

# Initialize API
complaint_api = ComplaintAPI()

@router.post("/", response_model=ComplaintResponse)
async def submit_complaint(request: ComplaintRequest):
    """Submit complaint and generate draft"""
    return await complaint_api.process_complaint(request)

@router.post("", response_model=ComplaintResponse)
async def submit_complaint_root(request: ComplaintRequest):
    """Submit complaint and generate draft (root alias)"""
    return await complaint_api.process_complaint(request)

@router.get("/{complaint_id}")
async def get_complaint(complaint_id: str):
    """Get complaint by ID"""
    return complaint_api.get_complaint(complaint_id)

@router.get("/")
async def get_all_complaints():
    """Get all complaints"""
    return {"complaints": complaint_api.get_all_complaints()}

@router.get("/{complaint_id}/download/{format_type}")
async def download_document(complaint_id: str, format_type: str):
    """Download complaint as PDF or Word document"""
    try:
        if format_type not in ("pdf", "docx"):
            raise HTTPException(status_code=400, detail="Unsupported format")
        data = await complaint_api.generate_document(complaint_id, format_type)
        filename = f"complaint_{complaint_id}.{format_type}"
        media_type = "application/pdf" if format_type == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return Response(content=data, media_type=media_type, headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving document: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving document")

@router.get("/{complaint_id}/pdf")
async def download_pdf(complaint_id: str):
    """Download complaint as PDF (legacy endpoint)"""
    try:
        data = await complaint_api.generate_document(complaint_id, "pdf")
        filename = f"complaint_{complaint_id}.pdf"
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return Response(content=data, media_type="application/pdf", headers=headers)
    except Exception as e:
        logger.error(f"Error serving PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving PDF")

@router.get("/{complaint_id}/word")
async def download_word(complaint_id: str):
    """Download complaint as Word document (legacy endpoint)"""
    try:
        data = await complaint_api.generate_document(complaint_id, "docx")
        filename = f"complaint_{complaint_id}.docx"
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers
        )
    except Exception as e:
        logger.error(f"Error serving Word document: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving Word document")

@router.put("/{complaint_id}/status")
async def update_status(complaint_id: str, status: str):
    """Update complaint status"""
    return complaint_api.update_complaint_status(complaint_id, status)

@router.delete("/{complaint_id}")
async def delete_complaint(complaint_id: str):
    """Delete complaint"""
    if complaint_id in complaint_api.complaints:
        del complaint_api.complaints[complaint_id]
        return {"message": "Complaint deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Complaint not found")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "complaint",
        "timestamp": TimeUtils().get_current_timestamp(),
        "total_complaints": len(complaint_api.complaints)
    }

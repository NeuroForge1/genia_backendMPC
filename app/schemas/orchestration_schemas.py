# En /home/ubuntu/genia_backendMPC/app/schemas/orchestration_schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional

class GenerateAndScheduleEmailRequest(BaseModel):
    prompt: str
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    email_subject: str
    email_from_address: Optional[EmailStr] = "noreply_orchestrated@genia.systems"
    # Puedes añadir más campos si necesitas, como un schedule_offset_minutes

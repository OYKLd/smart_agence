from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class AgentCategory(str, Enum):
    transaction = "transaction"
    conseil = "conseil"

class TicketStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"
    canceled = "canceled"

class AgentBase(BaseModel):
    nom: str
    prenoms: str
    annee_naissance: Optional[int]
    categorie: AgentCategory
    email: Optional[EmailStr]
    telephone: Optional[str]

class AgentCreate(AgentBase):
    pass

class Agent(AgentBase):
    id: int
    date_enregistrement: datetime

    class Config:
        orm_mode = True

class TicketBase(BaseModel):
    categorie_service: str
    description: Optional[str]

class TicketCreate(TicketBase):
    agent_id: int

class Ticket(TicketBase):
    id: int
    date_creation: datetime
    agent_id: int

    class Config:
        orm_mode = True

class EvenementBase(BaseModel):
    statut: TicketStatus

class EvenementCreate(EvenementBase):
    agent_id: int

class Evenement(EvenementBase):
    id: int
    ticket_id: int
    date: datetime
    agent_id: int

    class Config:
        orm_mode = True
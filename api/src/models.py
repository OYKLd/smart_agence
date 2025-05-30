from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from .database import Base

class AgentCategory(PyEnum):
    transaction = "transaction"
    conseil = "conseil"

class TicketStatus(PyEnum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"
    canceled = "canceled"

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    prenoms = Column(String, nullable=False)
    annee_naissance = Column(Integer)
    categorie = Column(Enum(AgentCategory), nullable=False)
    email = Column(String, unique=True)
    telephone = Column(String)
    date_enregistrement = Column(DateTime, default=datetime.utcnow)
    tickets = relationship("Ticket", back_populates="agent")

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    date_creation = Column(DateTime, default=datetime.utcnow)
    categorie_service = Column(String, nullable=False)
    description = Column(String)
    agent = relationship("Agent", back_populates="tickets")
    evenements = relationship("Evenement", back_populates="ticket")

class Evenement(Base):
    __tablename__ = "evenements"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    agent_id = Column(Integer, ForeignKey("agents.id"))
    date = Column(DateTime, default=datetime.utcnow)
    statut = Column(Enum(TicketStatus), nullable=False)
    ticket = relationship("Ticket", back_populates="evenements")
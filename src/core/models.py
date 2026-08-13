from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    company = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    service_needed = Column(String, nullable=True)
    status = Column(String, default="Pending")
    deal_stage = Column(String, default="Cold")
    thread_id = Column(String, nullable=True)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    reply_text = Column(Text, nullable=True)
    reply_status = Column(String, nullable=True)
    reply_timestamp = Column(DateTime, nullable=True)
    last_message_id = Column(String, nullable=True)
    email_sent_timestamp = Column(DateTime, nullable=True)
    followup_count = Column(Integer, default=0)
    last_followup_timestamp = Column(DateTime, nullable=True)
    send_attempts = Column(Integer, default=0)
    last_send_attempt_timestamp = Column(DateTime, nullable=True)
    last_send_error = Column(Text, nullable=True)

    email_logs = relationship("EmailLog", back_populates="lead")
    processed_messages = relationship("InboxProcessedMessage", back_populates="lead")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    message_id = Column(String, nullable=True)

    lead = relationship("Lead", back_populates="email_logs")


class InboxProcessedMessage(Base):
    __tablename__ = "inbox_processed_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True)
    sender_email = Column(String, nullable=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    status = Column(String, nullable=False)
    error = Column(Text, nullable=True)
    processed_at = Column(DateTime, default=func.now())

    lead = relationship("Lead", back_populates="processed_messages")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

import os
from sqlalchemy import create_client, Column, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# O SQLAlchemy exige que a URL comece com postgresql:// (o Render às vezes dá postgres://)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Tabela de Leads (Substitui o leads.json)
class Lead(Base):
    __tablename__ = "leads"
    jid = Column(String, primary_key=True)
    nome = Column(String)
    whatsapp = Column(String)
    ultima_mensagem = Column(Text)
    status = Column(String, default="Atendimento IA")
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# Cria as tabelas no banco automaticamente
def init_db():
    Base.metadata.create_all(bind=engine)

def salvar_lead_db(jid, nome, msg, status="Atendimento IA"):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.jid == jid).first()
        if not lead:
            lead = Lead(jid=jid, whatsapp=jid.split('@')[0])
        
        lead.nome = nome
        lead.ultima_mensagem = msg[:200]
        lead.status = status
        db.add(lead)
        db.commit()
    finally:
        db.close()

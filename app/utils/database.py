import os
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"
    jid = Column(String, primary_key=True)
    nome = Column(String)
    whatsapp = Column(String)
    ultima_mensagem = Column(Text)
    status = Column(String, default="Atendimento IA")
    pausar_ia = Column(Boolean, default=False) # MELHORIA 3: Trava para humano assumir
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ConfigLoja(Base):
    __tablename__ = "configs"
    id = Column(Integer, primary_key=True, default=1)
    nome_loja = Column(String)
    conhecimento = Column(Text)

class Mensagem(Base):
    __tablename__ = "historico"
    id = Column(Integer, primary_key=True, autoincrement=True)
    jid = Column(String)
    role = Column(String) # 'user' ou 'assistant'
    content = Column(Text)
    data_criacao = Column(DateTime, default=datetime.now)

def init_db():
    Base.metadata.create_all(bind=engine)
    # Garante que existe ao menos uma config padrão
    db = SessionLocal()
    if not db.query(ConfigLoja).first():
        db.add(ConfigLoja(id=1, nome_loja="Minha Loja", conhecimento="Atendimento inicial."))
        db.commit()
    db.close()

def salvar_lead_db(jid, nome, msg, status="Atendimento IA"):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.jid == jid).first()
        if not lead:
            lead = Lead(jid=jid, whatsapp=jid.split('@')[0])
        lead.nome = nome
        lead.ultima_mensagem = msg[:200]
        # Só atualiza o status se a IA não estiver pausada
        if not lead.pausar_ia:
            lead.status = status
        db.add(lead)
        db.commit()
    finally:
        db.close()

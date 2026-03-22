import json
import os
from loguru import logger
from app.utils.database import SessionLocal, Mensagem
from datetime import datetime

# Centraliza o diretório de banco de dados
DB_DIR = "app/db/messages"

def obter_caminho_historico(jid):
    """Garante que a pasta exista e retorna o caminho do arquivo do cliente."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)
        
    # Limpa o JID para evitar caracteres especiais no nome do arquivo
    id_limpo = jid.split('@')[0]
    return os.path.join(DB_DIR, f"historico_{id_limpo}.json")

def carregar_contexto(jid):
    """Busca as últimas 6 mensagens do banco de dados."""
    db = SessionLocal()
    try:
        mensagens = db.query(Mensagem).filter(Mensagem.jid == jid)\
                      .order_by(Mensagem.data_criacao.desc()).limit(6).all()
        # Inverte para ordem cronológica (mais antiga para mais recente)
        return [{"role": m.role, "content": m.content} for m in reversed(mensagens)]
    finally:
        db.close()

def salvar_contexto(jid, role, content):
    """Salva a interação no banco de dados."""
    db = SessionLocal()
    try:
        nova_msg = Mensagem(jid=jid, role=role, content=content)
        db.add(nova_msg)
        db.commit()
    finally:
        db.close()

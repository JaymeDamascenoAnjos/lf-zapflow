import httpx
import os
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# Configurações vindas do Render/Environment
EVOLUTION_URL = os.getenv("EVOLUTION_URL")
EVOLUTION_KEY = os.getenv("EVOLUTION_KEY")
INSTANCE_NAME = os.getenv("INSTANCE_NAME")

async def enviar_status_presenca(numero_jid: str, estado: str = "composing"):
    """Informa ao WhatsApp que o bot está 'digitando...'"""
    # Algumas versões usam /chat/sendPresence, outras /presence/sendPresence
    url = f"{EVOLUTION_URL}/presence/sendPresence/{INSTANCE_NAME}"
    
    headers = {"apikey": EVOLUTION_KEY, "Content-Type": "application/json"}
    payload = {
        "number": numero_jid.split('@')[0], # Envia apenas os números
        "presence": estado,
        "delay": 1200
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(url, json=payload, headers=headers)
            return True
        except Exception as e:
            logger.error(f"Erro status presença: {e}")
            return False

async def enviar_mensagem_zap(numero_jid: str, texto_resposta: str):
    """Envia o texto corrigido para a Evolution API (Cloudfy)."""
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"
    
    headers = {"apikey": EVOLUTION_KEY, "Content-Type": "application/json"}
    
    # AJUSTE CRÍTICO: O campo deve ser 'text' na raiz do JSON
    payload = {
        "number": numero_jid.split('@')[0], # Remove o @s.whatsapp.net se houver
        "text": texto_resposta,             # CAMPO OBRIGATÓRIO NA RAIZ
        "linkPreview": True,
        "delay": 1200
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                logger.success(f"Zap enviado para {numero_jid}")
                return True
            else:
                # Se der erro, o log mostrará exatamente o que a API recusou
                logger.error(f"Erro Evolution ({response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Falha conexão Evolution: {e}")
            return False

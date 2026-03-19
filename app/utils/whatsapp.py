import httpx
import os
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# Configurações vindas do seu arquivo .env
EVOLUTION_URL = os.getenv("EVOLUTION_URL")
EVOLUTION_KEY = os.getenv("EVOLUTION_KEY")
INSTANCE_NAME = os.getenv("INSTANCE_NAME")

async def enviar_status_presenca(numero_jid: str, estado: str = "composing"):
    """
    Informa ao WhatsApp que o bot está 'digitando...' ou 'gravando áudio...'
    Estados: 'composing' (digitando), 'recording' (gravando), 'paused' (parado)
    """
    # A Evolution usa o endpoint /chat/sendPresence/
    url = f"{EVOLUTION_URL}/chat/sendPresence/{INSTANCE_NAME}"
    
    headers = {
        "apikey": EVOLUTION_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "number": numero_jid,
        "presence": estado,
        "delay": 0
    }

    # Timeout curto de 10s pois é uma função de UX (não deve travar o fluxo)
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Erro ao enviar status de presença para {numero_jid}: {e}")
            return False

async def enviar_mensagem_zap(numero_jid: str, texto_resposta: str):
    """
    Faz a requisição para a Evolution API para enviar o texto ao cliente.
    """
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"
    
    headers = {
        "apikey": EVOLUTION_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "number": numero_jid,
        "options": {
            "delay": 500,           # Delay menor aqui pois o status inicial já foi enviado
            "presence": "composing" 
        },
        "textMessage": {
            "text": texto_resposta
        }
    }

    # Timeout de 30s é ideal para chamadas que dependem do processamento da IA
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                logger.success(f"Zap enviado com sucesso para {numero_jid}")
                return True
            else:
                logger.error(f"Erro Evolution API ({response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Falha na conexão com Evolution API: {e}")
            return False

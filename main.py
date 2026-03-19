import os
import json
import base64
import openai
from datetime import datetime
from fastapi import FastAPI, Request, BackgroundTasks
from loguru import logger
from dotenv import load_dotenv

from brain import processar_conversa
from app.utils.whatsapp import enviar_mensagem_zap, enviar_status_presenca

load_dotenv()

app = FastAPI(title="ZapFlow - Consultor de Vendas Digital")
app = FastAPI(redirect_slashes=False) # Adicione isso para evitar o "ignorado"

# Configurações e Logs
os.makedirs("app/logs", exist_ok=True)
os.makedirs("app/db", exist_ok=True)
logger.add("app/logs/zapflow.log", rotation="500 MB", level="INFO")

PROCESSADOS = set()

def registrar_lead(jid, nome, ultima_msg, status="Atendimento IA"):
    """Salva o contato na lista de leads para o lojista ver no Streamlit."""
    caminho_leads = "app/db/leads.json"
    leads = {}
    if os.path.exists(caminho_leads):
        try:
            with open(caminho_leads, 'r', encoding='utf-8') as f:
                leads = json.load(f)
        except: leads = {}

    leads[jid] = {
        "nome": nome,
        "whatsapp": jid.split('@')[0],
        "ultima_interacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "ultima_mensagem": ultima_msg[:50] + "..." if len(ultima_msg) > 50 else ultima_msg,
        "status": status
    }

    with open(caminho_leads, 'w', encoding='utf-8') as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)

@app.post("/webhook")
async def webhook_whatsapp(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        
        if data.get("event") != "messages.upsert":
            return {"status": "ignorado"}

        if data.get("data", {}).get("key", {}).get("fromMe"):
            return {"status": "ignorado"}

        msg_id = data.get("data", {}).get("key", {}).get("id")
        if msg_id in PROCESSADOS:
            return {"status": "duplicado"}
        
        PROCESSADOS.add(msg_id)
        if len(PROCESSADOS) > 200: PROCESSADOS.pop()

        message_obj = data.get("data", {}).get("message", {})
        texto_usuario = ""

        # --- EXTRAÇÃO DE TEXTO ---
        if "conversation" in message_obj:
            texto_usuario = message_obj["conversation"]
        elif "extendedTextMessage" in message_obj:
            texto_usuario = message_obj["extendedTextMessage"].get("text", "")
        
        # --- EXTRAÇÃO DE ÁUDIO (WHISPER) ---
        elif "audioMessage" in message_obj:
            logger.info("🎙️ Áudio recebido! Transcrevendo...")
            try:
                # O base64 vem direto da Evolution API no evento upsert
                audio_base64 = data["data"].get("base64")
                if audio_base64:
                    audio_data = base64.b64decode(audio_base64)
                    caminho_audio = f"app/db/temp_{msg_id}.mp3"
                    
                    with open(caminho_audio, "wb") as f:
                        f.write(audio_data)
                    
                    with open(caminho_audio, "rb") as audio_file:
                        transcricao = openai.audio.transcriptions.create(
                            model="whisper-1", 
                            file=audio_file
                        )
                    texto_usuario = f"[Áudio]: {transcricao.text}"
                    os.remove(caminho_audio)
            except Exception as e:
                logger.error(f"Erro Whisper: {e}")

        if not texto_usuario:
            return {"status": "sem_conteudo_util"}

        jid = data["data"]["key"]["remoteJid"]
        nome_contato = data["data"].get("pushName", "Cliente")

        registrar_lead(jid, nome_contato, texto_usuario)

        background_tasks.add_task(enviar_status_presenca, jid, "composing")
        background_tasks.add_task(fluxo_de_atendimento, jid, texto_usuario, nome_contato)

        return {"status": "sucesso"}

    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return {"status": "erro"}

async def fluxo_de_atendimento(jid: str, texto: str, nome: str):
    resposta_ia = processar_conversa(jid, texto, nome)
    
    # Valida Escalação Humana
    status_atual = "Atendimento IA"
    if "consultor humano" in resposta_ia.lower() or "momento" in resposta_ia.lower():
        logger.warning(f"🚨 Escalação: {nome}")
        status_atual = "🚨 PRECISA DE HUMANO"
    
    # Atualiza o lead com a resposta e status final
    registrar_lead(jid, nome, texto, status_atual)
    
    await enviar_mensagem_zap(jid, resposta_ia)
import openai
import json
import os
import time
from loguru import logger
from dotenv import load_dotenv

# Importamos as funções de memória
from app.utils.memory import carregar_contexto, salvar_contexto

load_dotenv()

# Ajuste importante: Garantir que a chave seja lida do ambiente do Render
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def carregar_dados_loja():
    """Lê as configurações com Retry para evitar conflito com o Streamlit."""
    caminho = "app/db/config_loja.json"
    
    for _ in range(3):
        if os.path.exists(caminho):
            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    if not dados.get("nome") or not dados.get("conhecimento"):
                        break
                    return dados
            except (json.JSONDecodeError, IOError):
                time.sleep(0.1)
                continue
    
    return {
        "nome": "Assistente de Vendas", 
        "conhecimento": "Atendimento cordial ao cliente. Informe que estamos configurando nosso catálogo."
    }

def processar_conversa(jid, texto_cliente, nome_cliente):
    """Coordena a inteligência de vendas."""
    try:
        loja = carregar_dados_loja()
        historico_antigo = carregar_contexto(jid)
        
        prompt_sistema = {
            "role": "system",
            "content": f"""Você é o Consultor Comercial da {loja['nome']}. Seu objetivo único é transformar curiosos em clientes.
            BASE DE CONHECIMENTO: {loja['conhecimento']}
            ESTRATÉGIA DE VENDA: Responda de forma empática e direta. Encerre com uma pergunta de engajamento."""
        }

        mensagens_para_ia = [prompt_sistema]
        for msg in (historico_antigo or []):
            mensagens_para_ia.append(msg)
        
        mensagens_para_ia.append({"role": "user", "content": texto_cliente})

        # Chamada OpenAI com a nova sintaxe da biblioteca
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensagens_para_ia,
            temperature=0.3,
            max_tokens=300
        )
        
        resposta_ia = response.choices[0].message.content

        if not resposta_ia:
            raise ValueError("Resposta da IA veio vazia")

        salvar_contexto(jid, "user", texto_cliente)
        salvar_contexto(jid, "assistant", resposta_ia)
        
        logger.info(f"IA gerou resposta para {nome_cliente}")
        return resposta_ia

    except Exception as e:
        logger.error(f"Erro no processamento da conversa: {e}")
        # Retorno padrão de segurança para evitar erro 400 na Evolution API
        return "Olá! Tive um breve problema técnico para processar sua mensagem agora. Pode repetir, por favor?"

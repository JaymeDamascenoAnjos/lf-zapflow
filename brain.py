import openai
import os
from loguru import logger
from dotenv import load_dotenv
from app.utils.database import SessionLocal, ConfigLoja
from datetime import datetime

# Importamos as funções de memória centralizadas
from app.utils.memory import carregar_contexto, salvar_contexto

load_dotenv()

# Cliente OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def carregar_dados_loja():
    """Busca as configurações da loja no PostgreSQL."""
    db = SessionLocal()
    try:
        config = db.query(ConfigLoja).filter(ConfigLoja.id == 1).first()
        if config:
            return {"nome": config.nome_loja, "conhecimento": config.conhecimento}
        return {"nome": "Consultor Comercial", "conhecimento": "Atendimento padrão de vendas."}
    finally:
        db.close()

def processar_conversa(jid, texto_cliente, nome_cliente):
    """Coordena a inteligência de vendas com foco em conversão."""
    try:
        loja = carregar_dados_loja()
        # Busca o histórico do banco (Persistência Total)
        historico_antigo = carregar_contexto(jid)
        
        prompt_sistema = {
            "role": "system",
            "content": f"""Você é o Consultor Comercial de elite da {loja['nome']}. 
            Seu objetivo único é transformar curiosos em compradores.

            BASE DE CONHECIMENTO: {loja['conhecimento']}

            ESTRATÉGIA DE VENDA (FECHAMENTO):
            1. Responda de forma extremamente empática, direta e sem enrolação.
            2. Se o cliente demonstrar interesse ou tirar dúvida sobre preço/serviço, induza o fechamento imediatamente.
            3. Use gatilhos de fechamento: 'Posso separar o seu?', 'Prefere retirar hoje ou que eu envie?', 'Vamos garantir sua vaga?'.
            4. NUNCA termine uma mensagem sem uma pergunta que direcione o cliente para o próximo passo da compra."""
        }

        # Montagem do histórico para a IA
        mensagens_para_ia = [prompt_sistema]
        for msg in (historico_antigo or []):
            mensagens_para_ia.append(msg)
        
        mensagens_para_ia.append({"role": "user", "content": texto_cliente})

        # Chamada OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensagens_para_ia,
            temperature=0.3, # Baixa temperatura para manter o foco comercial
            max_tokens=400
        )
        
        resposta_ia = response.choices[0].message.content

        if not resposta_ia:
            raise ValueError("Resposta da IA veio vazia")

        # PERSISTÊNCIA: Salva as duas pontas da conversa no banco
        salvar_contexto(jid, "user", texto_cliente)
        salvar_contexto(jid, "assistant", resposta_ia)
        
        logger.info(f"✅ Resposta enviada para {nome_cliente} ({jid})")
        return resposta_ia

    except Exception as e:
        logger.error(f"❌ Erro no processamento da conversa: {e}")
        return "Olá! Tive um pequeno problema técnico aqui, mas já estou de volta. Pode repetir sua última dúvida?"

# Nota: As funções carregar_contexto e salvar_contexto duplicadas foram removidas 
# pois agora são importadas corretamente do arquivo memory.py.

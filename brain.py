import openai
import json
import os
import time
from loguru import logger
from dotenv import load_dotenv

# Importamos as funções de memória
from app.utils.memory import carregar_contexto, salvar_contexto

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def carregar_dados_loja():
    """Lê as configurações com Retry para evitar conflito com o Streamlit."""
    caminho = "app/db/config_loja.json"
    
    # Tenta ler 3 vezes caso o arquivo esteja sendo escrito no exato momento
    for _ in range(3):
        if os.path.exists(caminho):
            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    # Validação mínima dos campos
                    if not dados.get("nome") or not dados.get("conhecimento"):
                        break
                    return dados
            except (json.JSONDecodeError, IOError):
                time.sleep(0.1) # Aguarda o arquivo liberar
                continue
    
    # Padrão de segurança caso o lojista ainda não tenha configurado nada
    return {
        "nome": "Assistente de Vendas", 
        "conhecimento": "Atendimento cordial ao cliente. Informe que estamos configurando nosso catálogo."
    }

def processar_conversa(jid, texto_cliente, nome_cliente):
    """Coordena a inteligência de vendas."""
    loja = carregar_dados_loja()
    
    # 1. Recupera apenas o contexto necessário (Histórico Curto)
    historico_antigo = carregar_contexto(jid)
    
    # 2. System Prompt Otimizado para Conversão de Vendas
    prompt_sistema = {
        "role": "system",
        "content": f"""Você é o Consultor Comercial da {loja['nome']}. Seu objetivo único é transformar curiosos em clientes.

        BASE DE CONHECIMENTO:
        {loja['conhecimento']}

        ESTRATÉGIA DE VENDA:
        1. Responda de forma empática e direta (máximo 3 frases).
        2. SEMPRE encerre com uma pergunta de fechamento ou engajamento. 
           Ex: 'Podemos agendar sua visita?' ou 'Qual cor você prefere?'
        3. Se o cliente demonstrar dúvida sobre preço, ressalte o valor/benefício antes de dar o valor.
        4. Nunca diga 'Eu não sei'. Diga: 'Vou confirmar esse detalhe específico com o estoque, qual seu melhor e-mail para eu te enviar a resposta agora?'

        REGRAS:
        - Nome do cliente: {nome_cliente} (use ocasionalmente).
        - Use emojis que transmitam confiança (✅, 🚀, 📦), sem exageros.
        - Se pedirem algo fora do CONHECIMENTO, peça o telefone para um especialista humano ligar.
        - Se o cliente pedir para falar com uma pessoa, usar a palavra 'gerente', 'atendente' ou se a conversa ficar tensa, responda EXATAMENTE: 'Entendido. Estou chamando um consultor humano para te dar uma atenção especial agora. Só um momento! ⏳'. Adicione a tag [ESCALAR] ao final da sua resposta interna."""
    }

    # 3. Construção do contexto de mensagens
    mensagens_para_ia = [prompt_sistema]
    for msg in historico_antigo:
        mensagens_para_ia.append(msg)
    
    mensagens_para_ia.append({"role": "user", "content": texto_cliente})

    try:
        # 4. Chamada OpenAI (GPT-4o-mini é excelente para agilidade)
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensagens_para_ia,
            temperature=0.3, # Mantém a IA fiel ao conhecimento da loja
            max_tokens=300
        )
        
        resposta_ia = response.choices[0].message.content

        # 5. Persistência da Memória
        salvar_contexto(jid, "user", texto_cliente)
        salvar_contexto(jid, "assistant", resposta_ia)
        
        logger.info(f"IA gerou resposta para {nome_cliente}")
        return resposta_ia

    except Exception as e:
        logger.error(f"Erro na OpenAI: {e}")
        return "Desculpe, tive um breve problema técnico. Pode repetir sua última pergunta?"

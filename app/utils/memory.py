import json
import os
from loguru import logger

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
    """Recupera as últimas mensagens do cliente com tratamento de erro."""
    caminho = obter_caminho_historico(jid)
    
    if os.path.exists(caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                historico = json.load(f)
                # Retorna apenas as últimas 6 mensagens para manter o foco da IA
                return historico[-6:]
        except Exception as e:
            logger.error(f"Erro ao ler histórico de {jid}: {e}")
            
    return []

def salvar_contexto(jid, role, content):
    """Adiciona uma nova interação e mantém o arquivo saudável."""
    caminho = obter_caminho_historico(jid)
    
    # Carregamos o histórico completo para adicionar a nova mensagem
    # (Usamos uma leitura simples aqui para performance)
    historico = []
    if os.path.exists(caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                historico = json.load(f)
        except:
            historico = []

    # Adiciona a nova interação
    historico.append({"role": role, "content": content})
    
    # Mantém apenas as últimas 12 mensagens no arquivo físico 
    # (6 interações completas: User + Assistant) para não crescer infinito
    historico_final = historico[-12:]
    
    try:
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(historico_final, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar histórico de {jid}: {e}")
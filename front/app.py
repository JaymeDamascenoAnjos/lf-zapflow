import streamlit as st
import pandas as pd
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Carrega as chaves
load_dotenv()

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# --- FUNÇÕES DE BANCO ---
def carregar_configuracoes_db():
    """Lê as configurações da loja da tabela (ou cria padrão)."""
    with engine.connect() as conn:
        # Tentamos ler de uma tabela de configs (opcional) ou mantemos o JSON apenas para a config
        # Para simplificar agora, vamos focar em carregar os LEADS do banco.
        pass

def carregar_leads_db():
    """Busca os leads diretamente do PostgreSQL."""
    try:
        query = "SELECT nome, data_atualizacao as ultima_interacao, status, ultima_mensagem FROM leads ORDER BY data_atualizacao DESC"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Erro ao conectar no banco: {e}")
        return pd.DataFrame()

# --- CONFIGURAÇÃO DE SEGURANÇA ---
SENHA_MESTRE = os.getenv("ZAPFLOW_ADMIN_PASSWORD", "admin123") 

# --- INTERFACE ---
st.set_page_config(page_title="ZapFlow - Painel do Lojista", page_icon="🤖", layout="wide")

st.title("🤖 ZapFlow - Gestão da IA")
st.markdown("---")

# 1. BLOCO DE LOGIN
senha_digitada = st.sidebar.text_input("Chave de Acesso", type="password")

if senha_digitada != SENHA_MESTRE:
    st.warning("⚠️ Por favor, insira a Chave de Acesso correta na barra lateral.")
    st.stop()

st.sidebar.success("Acesso Autorizado!")

# 2. ABAS
tab1, tab2 = st.tabs(["⚙️ Configuração da IA", "👥 Leads Captados"])

with tab1:
    st.info("As configurações de treinamento ainda estão lendo do arquivo local. Em breve no Banco!")
    # Nota: Mantenha a lógica do JSON aqui por enquanto se quiser, 
    # mas o importante são os LEADS abaixo que agora vêm do banco.

with tab2:
    st.subheader("Últimos contatos captados no PostgreSQL")
    
    df_leads = carregar_leads_db()
    
    if not df_leads.empty:
        # Formata a data para ficar mais amigável
        df_leads['ultima_interacao'] = pd.to_datetime(df_leads['ultima_interacao']).dt.strftime('%d/%m/%Y %H:%M')
        st.dataframe(df_leads, use_container_width=True)
        
        if st.button("🔄 Atualizar Lista"):
            st.rerun()
    else:
        st.info("Nenhum lead encontrado no banco de dados ainda.")

st.caption("ZapFlow v1.1 - Conectado ao PostgreSQL")

import streamlit as st
import pandas as pd
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ajuste de path para encontrar o database.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# --- FUNÇÕES DE BANCO ---
def carregar_configuracoes_db():
    """Busca as configurações da IA da tabela 'configs'."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT nome_loja, conhecimento FROM configs WHERE id = 1")).fetchone()
        if result:
            return {"nome": result[0], "conhecimento": result[1]}
        return {"nome": "ZapFlow", "conhecimento": "Atendimento padrão."}

def salvar_configuracoes_db(nome, conhecimento):
    """Atualiza as configurações da IA no Banco."""
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE configs SET nome_loja = :n, conhecimento = :c WHERE id = 1"),
            {"n": nome, "c": conhecimento}
        )

def carregar_leads_db():
    """Busca os leads diretamente do PostgreSQL."""
    try:
        # Importante: selecionei o JID para o botão 'Assumir' funcionar
        query = "SELECT jid, nome, data_atualizacao as ultima_interacao, status, ultima_mensagem FROM leads ORDER BY data_atualizacao DESC"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Erro ao conectar no banco: {e}")
        return pd.DataFrame()

# --- INTERFACE ---
st.set_page_config(page_title="ZapFlow - Gestão IA", page_icon="🤖", layout="wide")

# --- SEGURANÇA ---
SENHA_MESTRE = os.getenv("ZAPFLOW_ADMIN_PASSWORD", "admin123") 
senha_digitada = st.sidebar.text_input("Chave de Acesso", type="password")

if senha_digitada != SENHA_MESTRE:
    st.warning("⚠️ Aguardando Chave de Acesso...")
    st.stop()

st.title("🤖 ZapFlow - Painel do Lojista")
st.markdown("---")

tab1, tab2 = st.tabs(["⚙️ Configuração da IA", "👥 Leads Captados"])

with tab1:
    st.subheader("Treinamento e Identidade do Agente")
    config = carregar_configuracoes_db()
    
    with st.form("form_config"):
        nome_loja = st.text_input("Nome da Loja/Agente", value=config['nome'])
        conhecimento = st.text_area("Base de Conhecimento (Instruções)", value=config['conhecimento'], height=200)
        
        if st.form_submit_button("Salvar Configurações"):
            salvar_configuracoes_db(nome_loja, conhecimento)
            st.success("Configurações salvas no PostgreSQL!")

with tab2:
    st.subheader("Leads em tempo real")
    df_leads = carregar_leads_db()
    
    if not df_leads.empty:
        # Criamos o cabeçalho da tabela
        col_h1, col_h2, col_h3, col_h4 = st.columns([2, 3, 2, 1])
        col_h1.write("**Nome**")
        col_h2.write("**Última Mensagem**")
        col_h3.write("**Status**")
        col_h4.write("**Ação**")
        st.divider()

        for index, row in df_leads.iterrows():
            col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
            
            with col1: st.write(row['nome'])
            with col2: st.write(f"_{row['ultima_mensagem']}_")
            with col3: st.info(row['status'])
            with col4:
                # O key precisa ser único, usamos o jid
                if st.button("🙋‍♂️ Assumir", key=f"btn_{row['jid']}"):
                    with engine.begin() as conn:
                        conn.execute(
                            text("UPDATE leads SET pausar_ia = True, status = '👨‍💼 Humano Assumiu' WHERE jid = :j"), 
                            {"j": row['jid']}
                        )
                    st.rerun()
    else:
        st.info("Nenhum lead encontrado no banco de dados ainda.")

st.caption("ZapFlow v1.2 - 100% PostgreSQL Native")

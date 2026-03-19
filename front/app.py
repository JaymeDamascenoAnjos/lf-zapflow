import streamlit as st
import json
import os
import pandas as pd # Precisamos para exibir a tabela de leads
from dotenv import load_dotenv

# Carrega as chaves
load_dotenv()

# --- CONFIGURAÇÃO DE SEGURANÇA ---
SENHA_MESTRE = os.getenv("ZAPFLOW_ADMIN_PASSWORD", "admin123") 

def obter_caminho_base():
    # Pega a raiz do projeto (ZAPFLOW)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def obter_caminho_arquivo(nome_arquivo):
    caminho_db = os.path.join(obter_caminho_base(), "app", "db")
    os.makedirs(caminho_db, exist_ok=True)
    return os.path.join(caminho_db, nome_arquivo)

def salvar_configuracoes(dados):
    with open(obter_caminho_arquivo("config_loja.json"), 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def carregar_configuracoes():
    caminho = obter_caminho_arquivo("config_loja.json")
    if os.path.exists(caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {"nome": "", "conhecimento": ""}
    return {"nome": "", "conhecimento": ""}

def carregar_leads():
    caminho = obter_caminho_arquivo("leads.json")
    if os.path.exists(caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

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

# 2. ABAS (Organização Profissional)
tab1, tab2 = st.tabs(["⚙️ Configuração da IA", "👥 Leads Captados"])

with tab1:
    config_atual = carregar_configuracoes()
    
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.subheader("Configurações")
        nome_loja = st.text_input("Nome da Empresa", value=config_atual.get("nome", ""))
    
    with col_b:
        st.subheader("Treinamento")
        conhecimento = st.text_area(
            "O que a IA deve saber?", 
            value=config_atual.get("conhecimento", ""),
            height=250
        )
        if st.button("🚀 Atualizar Inteligência"):
            salvar_configuracoes({"nome": nome_loja, "conhecimento": conhecimento})
            st.success("IA Atualizada!")
            st.balloons()

    st.markdown("---")
    st.subheader("📊 Status")
    c1, c2 = st.columns(2)
    c1.metric("Status", "Online", delta="Ativo")
    c2.metric("Plataforma", "WhatsApp", delta="Cloudfy")

with tab2:
    st.subheader("Últimos contatos realizados pelo ZapFlow")
    leads_data = carregar_leads()
    
    if leads_data:
        # Transforma o JSON em uma tabela bonita
        df = pd.DataFrame.from_dict(leads_data, orient='index')
        # Reorganiza as colunas para o lojista
        df = df[['nome', 'ultima_interacao', 'status', 'ultima_mensagem']]
        st.dataframe(df, use_container_width=True)
        
        if st.button("🔄 Atualizar Lista"):
            st.rerun()
    else:
        st.info("Nenhum lead captado ainda. O robô está aguardando mensagens no WhatsApp.")

st.caption("ZapFlow v1.0 - Transformando conversas em faturamento.")

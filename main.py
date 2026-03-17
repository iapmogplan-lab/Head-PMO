import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# Configuração de Elite
st.set_page_config(
    page_title="GPlan IA — Gemini Edition",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS (Premium Dark)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; border: 1px solid #30363d; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #4285F4; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

# Inicialização do Gemini
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Usando o 1.5 Pro para máxima inteligência analítica
    model = genai.GenerativeModel('gemini-1.5-pro')
except Exception as e:
    st.error("Erro: GOOGLE_API_KEY não configurada corretamente nos Secrets.")
    st.stop()

# --- ESTADO DA SESSÃO ---
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Sou o **GPlan IA (Gemini Edition)**. Pronto para transformar seus dados em estratégia?"}
    ]
if "df" not in st.session_state:
    st.session_state.df = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("GPlan Control")
    st.divider()
    st.subheader("📁 Ingestão de Dados")
    uploaded_file = st.file_uploader("Upload de Cronograma (Excel/CSV)", type=["xlsx", "csv"])
    
    if uploaded_file:
        try:
            st.session_state.df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            st.success("Base integrada ao Gemini!")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

    st.divider()
    st.subheader("⚡ Comandos Rápidos")
    for cmd in ["🚨 Análise de Riscos", "📋 Plano de Ação 5W2H", "📊 Resumo Executivo"]:
        if st.button(cmd):
            st.session_state.temp_prompt = cmd

# --- DASHBOARD DE BI ---
st.title("🧠 GPlan IA — Copiloto Master")

if st.session_state.df is not None:
    df = st.session_state.df
    st.subheader("📊 Dashboard de Performance")
    
    total = len(df)
    status_col = next((c for c in df.columns if 'status' in c.lower()), None)
    atrasadas = len(df[df[status_col].str.contains("Atrasado|Atraso|Late", case=False)]) if status_col else 0
    saude = ((total - atrasadas) / total) * 100 if total > 0 else 0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Tarefas", total)
    m2.metric("Tarefas Atrasadas", atrasadas, delta_color="inverse")
    m3.metric("Saúde do Projeto", f"{saude:.1f}%")
    m4.metric("Motor IA", "Gemini 1.5 Pro")

    c1, c2 = st.columns(2)
    with c1:
        if status_col:
            st.plotly_chart(px.pie(df, names=status_col, hole=.4, template="plotly_dark"), use_container_width=True)
    with c2:
        resp_col = next((c for c in df.columns if 'respons' in c.lower() or 'dono' in c.lower()), None)
        if resp_col:
            st.plotly_chart(px.bar(df[resp_col].value_counts(), template="plotly_dark"), use_container_width=True)

st.divider()

# --- ÁREA DE CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Lógica de Input (Manual ou Botão)
prompt = st.chat_input("Pergunte ao Gemini sobre seu projeto...")
if "temp_prompt" in st.session_state:
    prompt = st.session_state.temp_prompt
    del st.session_state.temp_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Preparar Contexto Master para o Gemini
    contexto_dados = ""
    if st.session_state.df is not None:
        # Gemini ama JSON ou CSV para análise
        contexto_dados = f"\n[DADOS DO PROJETO]:\n{st.session_state.df.to_csv(index=False)}"

    SYSTEM_INSTRUCTIONS = (
        "Você é o GPlan IA, um especialista em Gerenciamento de Projetos (PMBOK/Scrum). "
        "Analise os dados fornecidos e responda de forma executiva, técnica e direta. "
        "Se houver atrasos, foque em planos de contenção."
    )

    with st.chat_message("assistant"):
        with st.spinner("Gemini analisando cenário..."):
            try:
                full_input = f"{SYSTEM_INSTRUCTIONS}\n\n{contexto_dados}\n\nPergunta do Gerente: {prompt}"
                response = st.session_state.chat.send_message(full_input)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro no Gemini: {e}")

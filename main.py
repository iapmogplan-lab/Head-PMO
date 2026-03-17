import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI

# Configuração de Elite
st.set_page_config(
    page_title="GPlan IA — Master Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS para visual "Premium Dark Mode"
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; border: 1px solid #30363d; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #238636; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

# Inicialização do Cliente OpenAI (Puxando dos Secrets do Streamlit)
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    st.error("Erro: OpenAI API Key não configurada nos Secrets.")
    st.stop()

# --- ESTADO DA SESSÃO ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá, sou o **GPlan IA**. Estou pronto para otimizar seus projetos. Como posso ajudar hoje?"}
    ]
if "df" not in st.session_state:
    st.session_state.df = None

# --- SIDEBAR (CONTROLES) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1087/1087815.png", width=80)
    st.title("GPlan Control")
    st.divider()
    
    st.subheader("📁 Ingestão de Dados")
    uploaded_file = st.file_uploader("Upload de Cronograma (Excel/CSV)", type=["xlsx", "csv"])
    
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        st.success("Base de dados integrada!")

    st.divider()
    st.subheader("⚡ Comandos Rápidos")
    if st.button("🚨 Análise de Riscos"):
        st.session_state.messages.append({"role": "user", "content": "Faça uma análise rigorosa de riscos baseada nos dados atuais."})
    if st.button("📋 Plano de Ação 5W2H"):
        st.session_state.messages.append({"role": "user", "content": "Gere um plano de ação 5W2H para as tarefas atrasadas."})
    if st.button("📊 Resumo Executivo"):
        st.session_state.messages.append({"role": "user", "content": "Crie um resumo executivo para diretoria."})

# --- LAYOUT PRINCIPAL ---
st.title("🧠 GPlan IA — Copiloto Master")

# Se houver dados, mostra o Dashboard de BI antes do Chat
if st.session_state.df is not None:
    df = st.session_state.df
    st.subheader("📊 Dashboard de Performance")
    
    # Cálculos PMBOK/Scrum
    total = len(df)
    # Tenta encontrar colunas comuns de status
    status_col = next((c for c in df.columns if 'status' in c.lower()), None)
    
    atrasadas = len(df[df[status_col].str.contains("Atrasado|Atraso|Late", case=False)]) if status_col else 0
    saude = ((total - atrasadas) / total) * 100 if total > 0 else 0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Tarefas", total)
    m2.metric("Tarefas Atrasadas", atrasadas, delta=f"{atrasadas/total*100:.1f}%" if total > 0 else 0, delta_color="inverse")
    m3.metric("Saúde do Projeto", f"{saude:.1f}%")
    m4.metric("Metodologia", "Híbrida (Scrum/PMI)")

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        if status_col:
            fig_pie = px.pie(df, names=status_col, title="Distribuição de Status", hole=.4, template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)
    with col_chart2:
        # Gráfico de barras simples por responsável ou categoria se existir
        resp_col = next((c for c in df.columns if 'respons' in c.lower() or 'dono' in c.lower()), None)
        if resp_col:
            fig_bar = px.bar(df[resp_col].value_counts(), title="Carga por Responsável", template="plotly_dark")
            st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# --- ÁREA DE CHAT (INTERATIVA) ---
# Container para o histórico de chat para não perder o scroll
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Input de Chat
if prompt := st.chat_input("Como posso ajudar no seu planejamento agora?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Contexto Inteligente
    contexto_dados = ""
    if st.session_state.df is not None:
        contexto_dados = f"DADOS ATUAIS DO PROJETO (Primeiras 50 linhas):\n{st.session_state.df.head(50).to_string()}"
    else:
        contexto_dados = "Nenhuma planilha subida ainda. Responda com base em teoria geral de PMBOK/Scrum."

    SYSTEM_PROMPT = f"""
    Você é o GPlan IA, o mais avançado copiloto de gestão de projetos.
    Personalidade: Consultor Sênior, assertivo, analítico e focado em resultados.
    Base de Conhecimento: PMBOK 7, Scrum Guide 2020, Kanban e Lean.
    Instrução: Se houver dados abaixo, use-os para dar respostas quantitativas. Se não, dê orientações estratégicas.
    
    {contexto_dados}
    """

    with st.chat_message("assistant"):
        with st.spinner("GPlan processando estratégia..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o", # Mudado para GPT-4o original para máxima inteligência
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        *st.session_state.messages
                    ],
                    temperature=0.7
                )
                texto_resposta = response.choices[0].message.content
                st.markdown(texto_resposta)
                st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
            except Exception as e:
                st.error(f"Erro na IA: {str(e)}")

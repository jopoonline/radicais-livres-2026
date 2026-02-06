import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import calendar
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Radicais Livres 2026", layout="wide", page_icon="⛪")

conn = st.connection("gsheets", type=GSheetsConnection)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1ptEbNIYh9_vVHJhnYLVoicAZ9REHTuIsBO4c1h7PsIs/edit#gid=0"

# --- ESTILO CSS (O DESIGN ORIGINAL) ---
st.markdown("""
<style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    .metric-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 15px; border-radius: 12px; border: 1px solid #334155;
        text-align: center; margin-bottom: 10px;
    }
    .metric-value { color: #00D4FF; font-size: 28px; font-weight: 800; margin: 0; }
    .metric-label { color: #94A3B8; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
    .type-label { 
        background-color: #00D4FF; color: #0F172A; padding: 2px 8px; 
        border-radius: 5px; font-size: 11px; font-weight: bold; margin-bottom: 8px; display: inline-block;
    }
    .main-title {
        background: linear-gradient(90deg, #00D4FF 0%, #0072FF 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 900; font-size: 40px; text-align: center; margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÕES E LISTAS ---
DISCIPULADORES_FIXOS = {
    "Jovens": ["André e Larissa", "Lucas e Rosana", "Deric e Nayara"],
    "Adolescentes": ["Giovana", "Guilherme", "Larissa", "Bella", "Pedro"]
}
MESES_ORDEM = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
TIPOS = ["Célula", "Culto de Jovens"]

def obter_sabados_2026(mes_nome):
    mes_idx = MESES_ORDEM.index(mes_nome) + 1
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    sabados = [d for d in cal.itermonthdates(2026, mes_idx) if d.weekday() == calendar.SATURDAY and d.month == mes_idx]
    return [d.strftime("%d/%m") for d in sabados]

def carregar_dados():
    try:
        df_d = conn.read(spreadsheet=URL_PLANILHA, worksheet="Dizimos", ttl=0)
        df_f = conn.read(spreadsheet=URL_PLANILHA, worksheet="Frequencia", ttl=0)
        if df_f.empty or "Discipulador" not in df_f.columns:
            f_data = []
            for m in MESES_ORDEM:
                for cat, nomes in DISCIPULADORES_FIXOS.items():
                    for n in nomes:
                        for t in TIPOS:
                            row = {"Mês": m, "Discipulador": n, "Categoria": cat, "Tipo": t}
                            for i in range(1, 6): row[f"S{i}_ME"] = row[f"S{i}_FA"] = row[f"S{i}_VI"] = 0
                            f_data.append(row)
            df_f = pd.DataFrame(f_data)
        return df_d, df_f
    except:
        return pd.DataFrame(columns=["Mês", "Líder", "Categoria", "Valor", "Pago"]), pd.DataFrame()

if 'df' not in st.session_state:
    st.session_state.df, st.session_state.df_freq = carregar_dados()

def salvar():
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Dizimos", data=st.session_state.df)
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Frequencia", data=st.session_state.df_freq)
    st.cache_data.clear()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🔐 Acesso")
    senha = st.text_input("Senha Admin:", type="password")
    is_admin = (senha == "1234")
    if st.button("🔄 Sincronizar"):
        st.session_state.df, st.session_state.df_freq = carregar_dados()
        st.rerun()

st.markdown('<p class="main-title">⛪ RADICAIS LIVRES 2026</p>', unsafe_allow_html=True)

# --- TABS ---
if is_admin:
    tab1, tab2, tab3 = st.tabs(["📊 Frequência", "💰 Finanças", "⚙️ Admin"])
else:
    tab1, tab2 = st.tabs(["📊 Frequência", "💰 Finanças"])

# --- ABA 1: FREQUÊNCIA ---
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1: mes_sel = st.selectbox("📅 Mês:", MESES_ORDEM, index=datetime.now().month-1)
    with c2: cat_filt = st.radio("📂 Grupo:", ["Todos", "Jovens", "Adolescentes"], horizontal=True)

    sabados = obter_sabados_2026(mes_sel)
    df_f_mes = st.session_state.df_freq[st.session_state.df_freq["Mês"] == mes_sel].copy()
    if cat_filt != "Todos": df_f_mes = df_f_mes[df_f_mes["Categoria"] == cat_filt]

    # CARTÕES DE MÉTRICAS (ESTILO DASHBOARD)
    st.write("### 💎 Resumo do Mês")
    cols_s = [f"S{i+1}_{t}" for i in range(len(sabados)) for t in ["ME", "FA", "VI"]]
    
    def criar_card(titulo, df_origem, label_tipo):
        me = int(df_origem[[f"S{i+1}_ME" for i in range(len(sabados))]].sum().sum())
        fa = int(df_origem[[f"S{i+1}_FA" for i in range(len(sabados))]].sum().sum())
        vi = int(df_origem[[f"S{i+1}_VI" for i in range(len(sabados))]].sum().sum())
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(f'<div class="metric-card"><span class="type-label">{label_tipo}</span><p class="metric-label">Membros</p><p class="metric-value">{me}</p></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card"><span class="type-label">{label_tipo}</span><p class="metric-label">Ativos</p><p class="metric-value">{fa}</p></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-card"><span class="type-label">{label_tipo}</span><p class="metric-label">Visitantes</p><p class="metric-value">{vi}</p></div>', unsafe_allow_html=True)
        col4.markdown(f'<div class="metric-card" style="border-color:#00D4FF"><span class="type-label">{label_tipo}</span><p class="metric-label">Total</p><p class="metric-value">{me+fa+vi}</p></div>', unsafe_allow_html=True)

    st.write("🏠 **Células**")
    criar_card("Células", df_f_mes[df_f_mes["Tipo"]=="Célula"], "CÉLULA")
    st.write("🎸 **Culto**")
    criar_card("Culto", df_f_mes[df_f_mes["Tipo"]=="Culto de Jovens"], "CULTO")

    # GRÁFICO
    st.divider()
    chart_data = []
    for i, data in enumerate(sabados):
        chart_data.append({"Dia": data, "Qtd": df_f_mes[f"S{i+1}_ME"].sum(), "Tipo": "Membros"})
        chart_data.append({"Dia": data, "Qtd": df_f_mes[f"S{i+1}_FA"].sum(), "Tipo": "Ativos"})
        chart_data.append({"Dia": data, "Qtd": df_f_mes[f"S{i+1}_VI"].sum(), "Tipo": "Visitantes"})
    
    st.plotly_chart(px.line(pd.DataFrame(chart_data), x="Dia", y="Qtd", color="Tipo", markers=True, title="Evolução Semanal", template="plotly_dark"), use_container_width=True)

    # TABELA DE EDIÇÃO (LÁ NO FUNDO)
    with st.expander("📝 Editar Lançamentos"):
        col_visiveis = ["Discipulador", "Tipo"] + [f"S{i+1}_{t}" for i in range(len(sabados)) for t in ["ME", "FA", "VI"]]
        df_ed = st.data_editor(df_f_mes[col_visiveis], use_container_width=True, hide_index=True)
        if st.button("💾 Salvar Frequência"):
            for _, row in df_ed.iterrows():
                idx = st.session_state.df_freq[(st.session_state.df_freq["Mês"]==mes_sel) & (st.session_state.df_freq["Discipulador"]==row["Discipulador"]) & (st.session_state.df_freq["Tipo"]==row["Tipo"])].index
                st.session_state.df_freq.loc[idx, col_visiveis] = row[col_visiveis]
            salvar(); st.success("Salvo!"); st.rerun()

# --- ABA 2: FINANÇAS ---
with tab2:
    total = st.session_state.df[st.session_state.df["Pago"]=="Sim"]["Valor"].astype(float).sum()
    st.markdown(f'<div class="metric-card"><p class="metric-label">Total Acumulado (Dízimos Líderes)</p><p class="metric-value" style="font-size:45px">R$ {total:,.2f}</p></div>', unsafe_allow_html=True)
    st.dataframe(st.session_state.df[st.session_state.df["Mês"]==mes_sel], use_container_width=True, hide_index=True)

# --- ABA 3: ADMIN ---
if is_admin:
    with tab3:
        st.write("### ⚙️ Gestão de Líderes")
        n_l = st.text_input("Novo Líder (Finanças):")
        c_l = st.selectbox("Categoria:", ["Jovens", "Adolescentes"])
        if st.button("➕ Adicionar"):
            novas = pd.DataFrame([{"Mês": m, "Líder": n_l, "Categoria": c_l, "Valor": 0.0, "Pago": "Não"} for m in MESES_ORDEM])
            st.session_state.df = pd.concat([st.session_state.df, novas], ignore_index=True)
            salvar(); st.rerun()

import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import calendar
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Radicais Livres 2026", layout="wide", page_icon="⛪")

# --- CONEXÃO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1ptEbNIYh9_vVHJhnYLVoicAZ9REHTuIsBO4c1h7PsIs/edit#gid=0"

# --- ESTILO CSS ---
st.markdown("""
<style>
.stApp { background-color: #0F172A; color: #F8FAFC; }
.metric-card {
background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
padding: 15px; border-radius: 12px; border: 1px solid #334155;
text-align: center; margin-bottom: 10px;
}
.metric-value { color: #00D4FF; font-size: 24px; font-weight: 800; margin: 0; }
.metric-label { color: #94A3B8; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
.type-label {
background-color: #00D4FF; color: #0F172A; padding: 2px 8px;
border-radius: 5px; font-size: 12px; font-weight: bold; margin-bottom: 8px; display: inline-block;
}
.main-title {
background: linear-gradient(90deg, #00D4FF 0%, #0072FF 100%);
-webkit-background-clip: text; -webkit-text-fill-color: transparent;
font-weight: 900; font-size: 38px; text-align: center; margin-bottom: 20px;
}
.edit-section {
background-color: #1E293B; padding: 20px; border-radius: 15px;
border-top: 3px solid #00D4FF; margin-top: 30px;
}
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÕES ---
MESES_ORDEM = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

GRUPOS_DISCIPULADORES = {
"Jovens": ["André e Larissa","Lucas e Rosana","Deric e Nayara"],
"Adolescentes": ["Giovana","Gui&La","Bella","Pedro"]
}

TODOS_DISCIPULADORES_CODIGO = GRUPOS_DISCIPULADORES["Jovens"] + GRUPOS_DISCIPULADORES["Adolescentes"]

TIPOS = ["Célula","Culto de Jovens"]

CORES_AZYK = {"ME":"#00D4FF","FA":"#0072FF","VI":"#00E6CC"}

meses_map = {m:list(calendar.month_name)[i+1] for i,m in enumerate(MESES_ORDEM)}

mes_atual_numero = datetime.now().month

# --- FUNÇÕES ---
def carregar_dados():
    try:
        df_d = conn.read(spreadsheet=URL_PLANILHA, worksheet="Dizimos", ttl=0)
        df_f = conn.read(spreadsheet=URL_PLANILHA, worksheet="Frequencia", ttl=0)
        return df_d, df_f
    except:
        return pd.DataFrame(), pd.DataFrame()

if 'df' not in st.session_state or 'df_freq' not in st.session_state:
    st.session_state.df, st.session_state.df_freq = carregar_dados()

def salvar_dados():
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Dizimos", data=st.session_state.df)
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Frequencia", data=st.session_state.df_freq)
    st.cache_data.clear()

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def obter_sabados_do_mes(mes_nome, ano=2026):
    mes_num = list(calendar.month_name).index(meses_map[mes_nome])
    cal = calendar.monthcalendar(ano, mes_num)
    return [f"{semana[calendar.SATURDAY]:02d}/{mes_num:02d}" for semana in cal if semana[calendar.SATURDAY] != 0]

# --- SIDEBAR ---
with st.sidebar:
    st.title("🔐 Acesso")
    senha = st.text_input("Senha Administrativa:", type="password")
    is_admin = (senha == "Videira@1020")

    if st.button("🔄 Sincronizar"):
        st.session_state.df, st.session_state.df_freq = carregar_dados()
        st.rerun()

st.markdown('<p class="main-title">⛪ RADICAIS LIVRES 2026</p>', unsafe_allow_html=True)

if is_admin:
    tabs = st.tabs(["📊 Frequência","💰 Finanças","⚙️ Admin"])
    tab1, tab2, tab3 = tabs
else:
    tabs = st.tabs(["📊 Frequência","💰 Finanças"])
    tab1, tab2 = tabs

# ================================
# ABA 1 FREQUENCIA (NÃO MODIFICADA)
# ================================
with tab1:

    col_sel1, col_sel2, col_sel3 = st.columns([1,1,2])

    with col_sel1:
        mes_sel = st.selectbox("📅 Mês:", MESES_ORDEM, index=mes_atual_numero-1)

    with col_sel2:
        cat_freq_filt = st.radio("📂 Categoria:", ["Jovens","Adolescentes","Todos"], horizontal=True)

    sabados = obter_sabados_do_mes(mes_sel)

    df_f_base = st.session_state.df_freq[
        (st.session_state.df_freq["Mês"] == mes_sel) &
        (st.session_state.df_freq["Discipulador"].isin(TODOS_DISCIPULADORES_CODIGO))
    ].copy()

    if cat_freq_filt != "Todos":
        df_f_base = df_f_base[df_f_base["Categoria"] == cat_freq_filt]

    with col_sel3:
        lista_nomes = sorted(df_f_base["Discipulador"].unique())
        selecao_nomes = st.multiselect("👥 Filtrar Discipuladores:", lista_nomes, default=lista_nomes)

    df_f_view = df_f_base[df_f_base["Discipulador"].isin(selecao_nomes)]

    st.dataframe(df_f_view, use_container_width=True)

# ================================
# ABA 2 FINANÇAS (CORRIGIDA)
# ================================
with tab2:

    cat_fin_view = st.selectbox("🔍 Ver Finanças de:", ["Todos","Jovens","Adolescentes"])

    mes_status = st.selectbox(
        "Status no Mês:",
        MESES_ORDEM,
        index=mes_atual_numero-1
    )

    df_fin_filtrado = st.session_state.df.copy()

    if cat_fin_view != "Todos":
        df_fin_filtrado = df_fin_filtrado[df_fin_filtrado["Categoria"] == cat_fin_view]

    df_mes = df_fin_filtrado[df_fin_filtrado["Mês"] == mes_status]

    df_pago_mes = df_mes[df_mes["Pago"] == "Sim"]

    st.markdown(f"""
    <div style="background:linear-gradient(90deg,#1E293B,#0072FF);
    padding:25px;border-radius:15px;border-left:5px solid #00D4FF;margin-bottom:20px;">
    <p class="metric-label">Total no Mês ({mes_status})</p>
    <p style="font-size:36px;font-weight:900;margin:0;">
    {formatar_brl(df_pago_mes["Valor"].sum())}
    </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])

    with col1:

        st.write("### 📈 Evolução de Arrecadação")

        df_pago = df_fin_filtrado[df_fin_filtrado["Pago"] == "Sim"]

        df_evol = df_pago.groupby("Mês")["Valor"].sum().reindex(MESES_ORDEM).fillna(0).reset_index()

        fig = px.line(df_evol, x="Mês", y="Valor", markers=True)

        fig.update_traces(
            texttemplate='R$ %{y:,.2f}',
            textposition="top center",
            line_color="#00D4FF"
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:

        st.write(f"### 🍩 Status: {mes_status}")

        fig_pizza = px.pie(
            df_mes,
            names="Pago",
            hole=0.6,
            color="Pago",
            color_discrete_map={
                "Sim":"#00D4FF",
                "Não":"#EF4444"
            }
        )

        fig_pizza.update_traces(textinfo="percent+label")

        fig_pizza.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )

        st.plotly_chart(fig_pizza, use_container_width=True)

# ================================
# ABA ADMIN (NÃO MODIFICADA)
# ================================
if is_admin:
    with tab3:
        st.write("### 👥 Gestão de Líderes")

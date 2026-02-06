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

# --- LISTA FIXA DE DISCIPULADORES (FREQUÊNCIA) ---
DISCIPULADORES_FIXOS = {
    "Jovens": ["André e Larissa", "Lucas e Rosana", "Deric e Nayara"],
    "Adolescentes": ["Giovana", "Guilherme", "Larissa", "Bella", "Pedro"]
}

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
</style>
""", unsafe_allow_html=True)

MESES_ORDEM = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
TIPOS = ["Célula", "Culto de Jovens"]
meses_map = {m: list(calendar.month_name)[i+1] for i, m in enumerate(MESES_ORDEM)}
mes_atual_numero = datetime.now().month

# --- FUNÇÕES DE DADOS ---
def carregar_dados_nuvem():
    try:
        df_d = conn.read(spreadsheet=URL_PLANILHA, worksheet="Dizimos", ttl=0)
        df_f = conn.read(spreadsheet=URL_PLANILHA, worksheet="Frequencia", ttl=0)
        
        # Se a planilha de frequência estiver vazia, cria com os nomes fixos
        if df_f.empty or len(df_f) < 5:
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

if 'df' not in st.session_state or 'df_freq' not in st.session_state:
    st.session_state.df, st.session_state.df_freq = carregar_dados_nuvem()

def salvar_nuvem():
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Dizimos", data=st.session_state.df)
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Frequencia", data=st.session_state.df_freq)
    st.cache_data.clear()

def obter_sabados_do_mes(mes_nome, ano=2026):
    mes_num = list(calendar.month_name).index(meses_map[mes_nome])
    cal = calendar.monthcalendar(ano, mes_num)
    return [f"{semana[calendar.SATURDAY]:02d}/{mes_num:02d}" for semana in cal if semana[calendar.SATURDAY] != 0]

# --- SIDEBAR ---
with st.sidebar:
    st.title("🔐 Acesso")
    senha = st.text_input("Senha Administrativa:", type="password")
    is_admin = (senha == "1234")
    if st.button("🔄 Sincronizar Dados"):
        st.session_state.df, st.session_state.df_freq = carregar_dados_nuvem()
        st.rerun()

st.markdown('<p class="main-title">⛪ RADICAIS LIVRES 2026</p>', unsafe_allow_html=True)

if is_admin:
    tab1, tab2, tab3 = st.tabs(["📊 Frequência", "💰 Finanças", "⚙️ Admin"])
else:
    tab1, tab2 = st.tabs(["📊 Frequência", "💰 Finanças"])

# --- ABA 1: FREQUÊNCIA ---
with tab1:
    c_f1, c_f2 = st.columns([1, 2])
    with c_f1: mes_sel = st.selectbox("📅 Mês:", MESES_ORDEM, index=mes_atual_numero-1, key="f_mes")
    with c_f2: cat_freq_filt = st.radio("📂 Categoria:", ["Jovens", "Adolescentes", "Todos"], horizontal=True, key="f_cat")
    
    sabados = obter_sabados_do_mes(mes_sel)
    n_sab = len(sabados)
    
    df_f_view = st.session_state.df_freq[st.session_state.df_freq["Mês"] == mes_sel].copy()
    if cat_freq_filt != "Todos": 
        df_f_view = df_f_view[df_f_view["Categoria"] == cat_freq_filt]

    # Métricas
    def show_metrics(df_filter, label):
        cols = [f"S{i}_{ind}" for i in range(1, n_sab+1) for ind in ["ME", "FA", "VI"]]
        total = int(df_filter[cols].sum().sum()) if not df_filter.empty else 0
        st.markdown(f'<div class="metric-card"><span class="type-label">{label}</span><p class="metric-label">Total Geral</p><p class="metric-value">{total}</p></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: show_metrics(df_f_view[df_f_view["Tipo"] == "Célula"], "CÉLULA")
    with c2: show_metrics(df_f_view[df_f_view["Tipo"] == "Culto de Jovens"], "CULTO")

    st.write("### 📝 Registrar Frequência")
    # Mostrar apenas colunas das semanas existentes no mês
    col_visiveis = ["Discipulador", "Tipo"] + [f"S{i}_{j}" for i in range(1, n_sab+1) for j in ["ME", "FA", "VI"]]
    df_ed = st.data_editor(df_f_view[col_visiveis], use_container_width=True, hide_index=True)
    
    if st.button("💾 Salvar Frequência"):
        for _, row in df_ed.iterrows():
            idx = st.session_state.df_freq[(st.session_state.df_freq["Mês"] == mes_sel) & 
                                          (st.session_state.df_freq["Discipulador"] == row["Discipulador"]) & 
                                          (st.session_state.df_freq["Tipo"] == row["Tipo"])].index
            for col in col_visiveis:
                if col not in ["Discipulador", "Tipo"]:
                    st.session_state.df_freq.loc[idx, col] = row[col]
        salvar_nuvem()
        st.success("Frequência Sincronizada!"); st.rerun()

# --- ABA 2: FINANÇAS ---
with tab2:
    if st.session_state.df.empty:
        st.info("Nenhum registro financeiro. Use o Admin para cadastrar líderes.")
    else:
        f_cat_fin = st.selectbox("Filtrar Categoria:", ["Todos", "Jovens", "Adolescentes"], key="fin_cat")
        df_fin = st.session_state.df.copy()
        if f_cat_fin != "Todos": df_fin = df_fin[df_fin["Categoria"] == f_cat_fin]
        
        total_pago = df_fin[df_fin["Pago"]=="Sim"]["Valor"].astype(float).sum()
        st.markdown(f'<div class="metric-card"><p class="metric-label">Arrecadação Total ({f_cat_fin})</p><p class="metric-value" style="font-size:40px">R$ {total_pago:,.2f}</p></div>', unsafe_allow_html=True)
        st.dataframe(df_fin[df_fin["Mês"] == MESES_ORDEM[mes_atual_numero-1]], use_container_width=True, hide_index=True)

# --- ABA 3: ADMIN ---
if is_admin:
    with tab3:
        st.write("### ⚙️ Gestão de Dízimos (Líderes)")
        c_a, c_b = st.columns(2)
        with c_a:
            novo_l = st.text_input("Nome do Líder para Dízimo:")
            cat_l = st.selectbox("Grupo:", ["Jovens", "Adolescentes"])
            if st.button("➕ Adicionar Líder"):
                if novo_l:
                    novas_linhas = pd.DataFrame([{"Mês": m, "Líder": novo_l, "Categoria": cat_l, "Valor": 0.0, "Pago": "Não"} for m in MESES_ORDEM])
                    st.session_state.df = pd.concat([st.session_state.df, novas_linhas], ignore_index=True)
                    salvar_nuvem(); st.success("Líder Adicionado!"); st.rerun()
        with c_b:
            l_ex = st.selectbox("Remover Líder:", sorted(st.session_state.df["Líder"].unique()) if not st.session_state.df.empty else [])
            if st.button("🗑️ Excluir"):
                st.session_state.df = st.session_state.df[st.session_state.df["Líder"]!=l_ex]
                salvar_nuvem(); st.warning("Removido!"); st.rerun()
        
        st.divider()
        m_adm = st.selectbox("Lançar dízimos de:", MESES_ORDEM, index=mes_atual_numero-1)
        df_adm = st.data_editor(st.session_state.df[st.session_state.df["Mês"] == m_adm], use_container_width=True, hide_index=True)
        if st.button("💾 Salvar Financeiro"):
            for _, r in df_adm.iterrows():
                pago = "Sim" if float(r["Valor"]) > 0 else "Não"
                st.session_state.df.loc[(st.session_state.df["Mês"]==m_adm)&(st.session_state.df["Líder"]==r["Líder"]), ["Valor", "Pago"]] = [r["Valor"], pago]
            salvar_nuvem(); st.success("Dados Financeiros Salvos!"); st.rerun()

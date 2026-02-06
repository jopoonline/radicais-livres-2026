import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import calendar
from datetime import datetime

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="Radicais Livres 2026", layout="wide", page_icon="⛪")

conn = st.connection("gsheets", type=GSheetsConnection)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1ptEbNIYh9_vVHJhnYLVoicAZ9REHTuIsBO4c1h7PsIs/edit#gid=0"

# --- LISTA FIXA DE DISCIPULADORES ---
DISCIPULADORES_FIXOS = {
    "Jovens": ["André e Larissa", "Lucas e Rosana", "Deric e Nayara"],
    "Adolescentes": ["Giovana", "Guilherme", "Larissa", "Bella", "Pedro"]
}

MESES_ORDEM = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
TIPOS = ["Célula", "Culto de Jovens"]

# --- FUNÇÃO PARA PEGAR SÁBADOS COM DATAS ---
def obter_sabados_2026(mes_nome):
    mes_idx = MESES_ORDEM.index(mes_nome) + 1
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    # Pega todos os sábados de 2026 para o mês selecionado
    sabados = [d for d in cal.itermonthdates(2026, mes_idx) if d.weekday() == calendar.SATURDAY and d.month == mes_idx]
    return [d.strftime("%d/%m") for d in sabados]

# --- CARREGAR DADOS ---
def carregar_dados_nuvem():
    try:
        df_d = conn.read(spreadsheet=URL_PLANILHA, worksheet="Dizimos", ttl=0)
        df_f = conn.read(spreadsheet=URL_PLANILHA, worksheet="Frequencia", ttl=0)
        
        # FORÇAR LISTA FIXA SE ESTIVER ERRADO OU VAZIO
        lista_atual = df_f["Discipulador"].unique().tolist() if not df_f.empty else []
        if not any(nome in lista_atual for nome in DISCIPULADORES_FIXOS["Jovens"]):
            f_data = []
            for m in MESES_ORDEM:
                for cat, nomes in DISCIPULADORES_FIXOS.items():
                    for n in nomes:
                        for t in TIPOS:
                            row = {"Mês": m, "Discipulador": n, "Categoria": cat, "Tipo": t}
                            for i in range(1, 6): 
                                row[f"S{i}_ME"] = row[f"S{i}_FA"] = row[f"S{i}_VI"] = 0
                            f_data.append(row)
            df_f = pd.DataFrame(f_data)
        return df_d, df_f
    except:
        return pd.DataFrame(), pd.DataFrame()

if 'df' not in st.session_state or 'df_freq' not in st.session_state:
    st.session_state.df, st.session_state.df_freq = carregar_dados_nuvem()

def salvar_nuvem():
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Dizimos", data=st.session_state.df)
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Frequencia", data=st.session_state.df_freq)
    st.cache_data.clear()

# --- INTERFACE ---
with st.sidebar:
    senha = st.text_input("Senha Admin:", type="password")
    is_admin = (senha == "1234")
    if st.button("🔄 Forçar Reset/Sincronização"):
        st.session_state.df, st.session_state.df_freq = carregar_dados_nuvem()
        st.rerun()

st.markdown('<h1 style="text-align:center; color:#00D4FF;">⛪ RADICAIS LIVRES 2026</h1>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Frequência", "💰 Finanças", "⚙️ Admin"]) if is_admin else st.tabs(["📊 Frequência", "💰 Finanças"])

# --- ABA 1: FREQUÊNCIA ---
with tab1:
    col_a, col_b = st.columns(2)
    with col_a: mes_sel = st.selectbox("📅 Selecione o Mês:", MESES_ORDEM, index=datetime.now().month-1)
    with col_b: cat_filt = st.radio("📂 Grupo:", ["Todos", "Jovens", "Adolescentes"], horizontal=True)

    sabados_mes = obter_sabados_2026(mes_sel)
    num_sabados = len(sabados_mes)

    df_f_view = st.session_state.df_freq[st.session_state.df_freq["Mês"] == mes_sel].copy()
    if cat_filt != "Todos":
        df_f_view = df_f_view[df_f_view["Categoria"] == cat_filt]

    st.write(f"### 📝 Registrar Frequência - {mes_sel}")
    
    # Criar mapeamento de nomes de colunas para as datas reais
    col_config = {
        "Mês": None, "Categoria": None,
        "Discipulador": st.column_config.Column(width="medium", disabled=True),
        "Tipo": st.column_config.Column(width="small", disabled=True)
    }
    
    # Configura apenas as colunas das semanas que existem no mês
    col_originais = ["Discipulador", "Tipo"]
    for i, data_sab in enumerate(sabados_mes):
        s = i + 1
        col_originais.extend([f"S{s}_ME", f"S{s}_FA", f"S{s}_VI"])
        col_config[f"S{s}_ME"] = st.column_config.NumberColumn(f"📅 {data_sab} (Memb)", min_value=0, format="%d")
        col_config[f"S{s}_FA"] = st.column_config.NumberColumn(f"📅 {data_sab} (Ativ)", min_value=0, format="%d")
        col_config[f"S{s}_VI"] = st.column_config.NumberColumn(f"📅 {data_sab} (Visit)", min_value=0, format="%d")

    # Esconde as colunas S4 ou S5 se o mês não tiver
    for s in range(num_sabados + 1, 6):
        col_config[f"S{s}_ME"] = None
        col_config[f"S{s}_FA"] = None
        col_config[f"S{s}_VI"] = None

    df_ed = st.data_editor(df_f_view[col_originais], column_config=col_config, use_container_width=True, hide_index=True)

    if st.button("💾 Salvar Frequência"):
        for _, row in df_ed.iterrows():
            idx = st.session_state.df_freq[(st.session_state.df_freq["Mês"] == mes_sel) & 
                                          (st.session_state.df_freq["Discipulador"] == row["Discipulador"]) & 
                                          (st.session_state.df_freq["Tipo"] == row["Tipo"])].index
            for col in col_originais:
                if col not in ["Discipulador", "Tipo"]:
                    st.session_state.df_freq.loc[idx, col] = row[col]
        salvar_nuvem()
        st.success("Dados salvos com sucesso!"); st.rerun()

# --- ABA 2: FINANÇAS ---
with tab2:
    if not st.session_state.df.empty:
        total = st.session_state.df[st.session_state.df["Pago"]=="Sim"]["Valor"].sum()
        st.metric("Arrecadação Total Líderes", f"R$ {total:,.2f}")
        st.dataframe(st.session_state.df[st.session_state.df["Mês"]==mes_sel], use_container_width=True, hide_index=True)

# --- ABA 3: ADMIN ---
if is_admin:
    with tab3:
        st.write("### ⚙️ Gestão de Dízimos (Líderes)")
        n_l = st.text_input("Novo Líder:")
        c_l = st.selectbox("Grupo:", ["Jovens", "Adolescentes"])
        if st.button("➕ Adicionar Líder"):
            novas = pd.DataFrame([{"Mês": m, "Líder": n_l, "Categoria": c_l, "Valor": 0.0, "Pago": "Não"} for m in MESES_ORDEM])
            st.session_state.df = pd.concat([st.session_state.df, novas], ignore_index=True)
            salvar_nuvem(); st.rerun()

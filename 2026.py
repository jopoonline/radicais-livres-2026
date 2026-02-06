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

# --- FUNÇÃO PARA PEGAR SÁBADOS COM DATAS (2026) ---
def obter_sabados_2026(mes_nome):
    mes_idx = MESES_ORDEM.index(mes_nome) + 1
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    # Filtra apenas os sábados do mês específico no ano de 2026
    sabados = [d for d in cal.itermonthdates(2026, mes_idx) if d.weekday() == calendar.SATURDAY and d.month == mes_idx]
    return [d.strftime("%d/%m") for d in sabados]

# --- CARREGAR DADOS ---
def carregar_dados_nuvem():
    try:
        df_d = conn.read(spreadsheet=URL_PLANILHA, worksheet="Dizimos", ttl=0)
        df_f = conn.read(spreadsheet=URL_PLANILHA, worksheet="Frequencia", ttl=0)
        
        # Se a planilha estiver vazia ou com nomes errados, recria a base fixa
        if df_f.empty or "Discipulador" not in df_f.columns:
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
        return pd.DataFrame(columns=["Mês", "Líder", "Categoria", "Valor", "Pago"]), pd.DataFrame()

if 'df' not in st.session_state or 'df_freq' not in st.session_state:
    st.session_state.df, st.session_state.df_freq = carregar_dados_nuvem()

def salvar_nuvem():
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Dizimos", data=st.session_state.df)
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Frequencia", data=st.session_state.df_freq)
    st.cache_data.clear()

# --- INTERFACE ---
with st.sidebar:
    st.title("🔐 Acesso")
    senha = st.text_input("Senha Admin:", type="password")
    is_admin = (senha == "1234")
    if st.button("🔄 Forçar Reset/Sincronização"):
        st.session_state.df, st.session_state.df_freq = carregar_dados_nuvem()
        st.rerun()

st.markdown('<h1 style="text-align:center; color:#00D4FF;">⛪ RADICAIS LIVRES 2026</h1>', unsafe_allow_html=True)

# --- DEFINIÇÃO DAS ABAS (CORRIGIDO PARA EVITAR VALUEERROR) ---
if is_admin:
    tabs = st.tabs(["📊 Frequência", "💰 Finanças", "⚙️ Admin"])
    tab1, tab2, tab3 = tabs
else:
    tabs = st.tabs(["📊 Frequência", "💰 Finanças"])
    tab1, tab2 = tabs

# --- ABA 1: FREQUÊNCIA ---
with tab1:
    col_a, col_b = st.columns(2)
    with col_a: 
        mes_sel = st.selectbox("📅 Selecione o Mês:", MESES_ORDEM, index=datetime.now().month-1)
    with col_b: 
        cat_filt = st.radio("📂 Grupo:", ["Todos", "Jovens", "Adolescentes"], horizontal=True)

    sabados_mes = obter_sabados_2026(mes_sel)
    num_sabados = len(sabados_mes)

    # Filtragem dos dados da memória
    df_f_view = st.session_state.df_freq[st.session_state.df_freq["Mês"] == mes_sel].copy()
    if cat_filt != "Todos":
        df_f_view = df_f_view[df_f_view["Categoria"] == cat_filt]

    st.write(f"### 📝 Registrar Frequência - {mes_sel}")
    
    # Configuração das Colunas com Datas de 2026
    col_config = {
        "Discipulador": st.column_config.Column(disabled=True),
        "Tipo": st.column_config.Column(disabled=True)
    }
    
    col_exibir = ["Discipulador", "Tipo"]
    for i, data_sab in enumerate(sabados_mes):
        s = i + 1
        col_exibir.extend([f"S{s}_ME", f"S{s}_FA", f"S{s}_VI"])
        col_config[f"S{s}_ME"] = st.column_config.NumberColumn(f"{data_sab} Memb", min_value=0)
        col_config[f"S{s}_FA"] = st.column_config.NumberColumn(f"{data_sab} Ativ", min_value=0)
        col_config[f"S{s}_VI"] = st.column_config.NumberColumn(f"{data_sab} Visit", min_value=0)

    # Ocultar colunas de semanas que não existem no mês (ex: S5 em meses de 4 semanas)
    todas_cols_semana = [f"S{s}_{t}" for s in range(1, 6) for t in ["ME", "FA", "VI"]]
    cols_para_esconder = [c for c in todas_cols_semana if c not in col_exibir]
    for c in cols_para_esconder:
        col_config[c] = None

    # Editor de Dados
    df_ed = st.data_editor(
        df_f_view[col_exibir], 
        column_config=col_config, 
        use_container_width=True, 
        hide_index=True
    )

    if st.button("💾 Salvar Dados de Frequência"):
        for _, row in df_ed.iterrows():
            idx = st.session_state.df_freq[
                (st.session_state.df_freq["Mês"] == mes_sel) & 
                (st.session_state.df_freq["Discipulador"] == row["Discipulador"]) & 
                (st.session_state.df_freq["Tipo"] == row["Tipo"])
            ].index
            for col in col_exibir:
                if col not in ["Discipulador", "Tipo"]:
                    st.session_state.df_freq.loc[idx, col] = row[col]
        salvar_nuvem()
        st.success("Frequência salva no Google Sheets!"); st.rerun()

# --- ABA 2: FINANÇAS ---
with tab2:
    if st.session_state.df.empty:
        st.info("Nenhum registro de dízimo encontrado.")
    else:
        total = st.session_state.df[st.session_state.df["Pago"]=="Sim"]["Valor"].astype(float).sum()
        st.metric("Total Arrecadado (Dízimo Líderes)", f"R$ {total:,.2f}")
        st.dataframe(st.session_state.df[st.session_state.df["Mês"]==mes_sel], use_container_width=True, hide_index=True)

# --- ABA 3: ADMIN ---
if is_admin:
    with tab3:
        st.write("### ⚙️ Gestão de Líderes (Finanças)")
        c1, c2 = st.columns(2)
        with c1:
            n_l = st.text_input("Nome do Líder:")
            c_l = st.selectbox("Categoria:", ["Jovens", "Adolescentes"])
            if st.button("➕ Adicionar Líder"):
                novas = pd.DataFrame([{"Mês": m, "Líder": n_l, "Categoria": c_l, "Valor": 0.0, "Pago": "Não"} for m in MESES_ORDEM])
                st.session_state.df = pd.concat([st.session_state.df, novas], ignore_index=True)
                salvar_nuvem(); st.rerun()
        with c2:
            l_list = sorted(st.session_state.df["Líder"].unique()) if not st.session_state.df.empty else []
            l_ex = st.selectbox("Excluir Líder:", l_list)
            if st.button("🗑️ Remover"):
                st.session_state.df = st.session_state.df[st.session_state.df["Líder"]!=l_ex]
                salvar_nuvem(); st.rerun()

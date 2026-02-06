import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import calendar
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Radicais Livres 2026", layout="wide", page_icon="⛪")

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# URL DA SUA PLANILHA
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
MESES_ORDEM = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
TIPOS = ["Célula", "Culto de Jovens"]
CORES_AZYK = {"ME": "#00D4FF", "FA": "#0072FF", "VI": "#00E6CC"}
meses_map = {m: list(calendar.month_name)[i+1] for i, m in enumerate(MESES_ORDEM)}
mes_atual_numero = datetime.now().month

# --- FUNÇÕES DE DADOS ---
def carregar_dados_nuvem():
    try:
        df_d = conn.read(spreadsheet=URL_PLANILHA, worksheet="Dizimos", ttl=0)
        df_f = conn.read(spreadsheet=URL_PLANILHA, worksheet="Frequencia", ttl=0)
        return df_d, df_f
    except Exception:
        # Retorna estruturas vazias se a planilha não tiver as abas
        return pd.DataFrame(columns=["Mês", "Líder", "Categoria", "Valor", "Pago"]), \
               pd.DataFrame(columns=["Mês", "Discipulador", "Categoria", "Tipo"] + [f"S{i}_{j}" for i in range(1,6) for j in ["ME","FA","VI"]])

if 'df' not in st.session_state or 'df_freq' not in st.session_state:
    st.session_state.df, st.session_state.df_freq = carregar_dados_nuvem()

def salvar_nuvem():
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Dizimos", data=st.session_state.df)
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Frequencia", data=st.session_state.df_freq)
    st.cache_data.clear()

def formatar_brl(valor): 
    try: return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

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

# --- DEFINIÇÃO DAS ABAS (CORRIGIDO) ---
if is_admin:
    tab1, tab2, tab3 = st.tabs(["📊 Frequência", "💰 Finanças", "⚙️ Admin"])
else:
    tab1, tab2 = st.tabs(["📊 Frequência", "💰 Finanças"])

# --- ABA 1: FREQUÊNCIA ---
with tab1:
    if st.session_state.df_freq.empty:
        st.info("Nenhum líder cadastrado. Vá em Admin para começar.")
    else:
        c_f1, c_f2, c_f3 = st.columns([1, 1, 2])
        with c_f1: mes_sel = st.selectbox("📅 Mês:", MESES_ORDEM, index=mes_atual_numero-1)
        with c_f2: cat_freq_filt = st.radio("📂 Categoria:", ["Jovens", "Adolescentes", "Todos"], horizontal=True)
        
        sabados = obter_sabados_do_mes(mes_sel)
        n_sab = len(sabados)
        df_f_base = st.session_state.df_freq[st.session_state.df_freq["Mês"] == mes_sel].copy()
        if cat_freq_filt != "Todos": df_f_base = df_f_base[df_f_base["Categoria"] == cat_freq_filt]
        with c_f3:
            lista_nomes = sorted(df_f_base["Discipulador"].unique())
            selecao_nomes = st.multiselect("👥 Filtrar Discipuladores:", lista_nomes, default=lista_nomes)
        
        df_f_view = df_f_base[df_f_base["Discipulador"].isin(selecao_nomes)]

        if not df_f_view.empty:
            def show_metrics(df_filter, label):
                cols_me = [f"S{i}_ME" for i in range(1, n_sab+1)]
                cols_fa = [f"S{i}_FA" for i in range(1, n_sab+1)]
                cols_vi = [f"S{i}_VI" for i in range(1, n_sab+1)]
                me = int(df_filter[cols_me].sum().sum())
                fa = int(df_filter[cols_fa].sum().sum())
                vi = int(df_filter[cols_vi].sum().sum())
                m1, m2, m3, m4 = st.columns(4)
                m1.markdown(f'<div class="metric-card"><span class="type-label">{label}</span><p class="metric-label">Membros</p><p class="metric-value">{me}</p></div>', unsafe_allow_html=True)
                m2.markdown(f'<div class="metric-card"><span class="type-label">{label}</span><p class="metric-label">Ativos</p><p class="metric-value">{fa}</p></div>', unsafe_allow_html=True)
                m3.markdown(f'<div class="metric-card"><span class="type-label">{label}</span><p class="metric-label">Visitantes</p><p class="metric-value">{vi}</p></div>', unsafe_allow_html=True)
                m4.markdown(f'<div class="metric-card" style="border-color:#00D4FF"><span class="type-label">{label}</span><p class="metric-label">Total</p><p class="metric-value">{me+fa+vi}</p></div>', unsafe_allow_html=True)

            st.write("### 🏠 Resumo Semanal")
            show_metrics(df_f_view[df_f_view["Tipo"] == "Célula"], "CÉLULA")
            show_metrics(df_f_view[df_f_view["Tipo"] == "Culto de Jovens"], "CULTO")

            st.markdown('<div class="edit-section">', unsafe_allow_html=True)
            if st.toggle("📝 Habilitar Edição"):
                df_ed = st.data_editor(df_f_view, use_container_width=True, hide_index=True)
                if st.button("💾 Salvar Alterações"):
                    for _, row in df_ed.iterrows():
                        idx = st.session_state.df_freq[(st.session_state.df_freq["Mês"] == row["Mês"]) & (st.session_state.df_freq["Discipulador"] == row["Discipulador"]) & (st.session_state.df_freq["Tipo"] == row["Tipo"])].index
                        st.session_state.df_freq.loc[idx, :] = row.values
                    salvar_nuvem(); st.success("Salvo com sucesso!"); st.rerun()
            else:
                st.dataframe(df_f_view, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 2: FINANÇAS ---
with tab2:
    if st.session_state.df.empty:
        st.info("Nenhum registro financeiro.")
    else:
        f_cat = st.selectbox("Categoria:", ["Todos", "Jovens", "Adolescentes"], key="fin_cat")
        df_fin = st.session_state.df.copy()
        if f_cat != "Todos": df_fin = df_fin[df_fin["Categoria"] == f_cat]
        total = df_fin[df_fin["Pago"]=="Sim"]["Valor"].astype(float).sum()
        st.markdown(f'<div class="metric-card"><p class="metric-label">Arrecadação Total ({f_cat})</p><p class="metric-value" style="font-size:40px">{formatar_brl(total)}</p></div>', unsafe_allow_html=True)
        st.dataframe(df_fin, use_container_width=True, hide_index=True)

# --- ABA 3: ADMIN (APENAS COM SENHA) ---
if is_admin:
    with tab3:
        st.write("### ⚙️ Gestão de Líderes")
        col_a, col_b = st.columns(2)
        with col_a:
            novo_nome = st.text_input("Nome do Líder:")
            nova_cat = st.selectbox("Grupo:", ["Jovens", "Adolescentes"], key="new_cat")
            if st.button("➕ Adicionar ao Sistema"):
                if novo_nome:
                    # Adiciona no Financeiro
                    for m in MESES_ORDEM:
                        new_d = pd.DataFrame([{"Mês":m,"Líder":novo_nome,"Categoria":nova_cat,"Valor":0.0,"Pago":"Não"}])
                        st.session_state.df = pd.concat([st.session_state.df, new_d], ignore_index=True)
                        # Adiciona na Frequência
                        for t in TIPOS:
                            new_f = {"Mês":m,"Discipulador":novo_nome,"Categoria":nova_cat,"Tipo":t}
                            for i in range(1,6): new_f[f"S{i}_ME"]=new_f[f"S{i}_FA"]=new_f[f"S{i}_VI"]=0
                            st.session_state.df_freq = pd.concat([st.session_state.df_freq, pd.DataFrame([new_f])], ignore_index=True)
                    salvar_nuvem(); st.success(f"{novo_nome} cadastrado!"); st.rerun()
        
        with col_b:
            l_remover = st.selectbox("Remover Líder:", sorted(st.session_state.df["Líder"].unique()) if not st.session_state.df.empty else [])
            if st.button("🗑️ Excluir permanentemente"):
                st.session_state.df = st.session_state.df[st.session_state.df["Líder"]!=l_remover]
                st.session_state.df_freq = st.session_state.df_freq[st.session_state.df_freq["Discipulador"]!=l_remover]
                salvar_nuvem(); st.warning(f"{l_remover} removido!"); st.rerun()
        
        st.divider()
        st.write("### 💰 Lançamento de Valores")
        mes_adm = st.selectbox("Mês de Referência:", MESES_ORDEM, index=mes_atual_numero-1, key="mes_adm")
        df_ed_adm = st.data_editor(st.session_state.df[st.session_state.df["Mês"]==mes_adm], use_container_width=True, hide_index=True)
        if st.button("💾 Sincronizar Financeiro"):
            for _, r in df_ed_adm.iterrows():
                val_pago = "Sim" if float(r["Valor"]) > 0 else "Não"
                st.session_state.df.loc[(st.session_state.df["Mês"]==mes_adm)&(st.session_state.df["Líder"]==r["Líder"]), ["Valor", "Pago"]] = [r["Valor"], val_pago]
            salvar_nuvem(); st.success("Planilha atualizada!"); st.rerun()

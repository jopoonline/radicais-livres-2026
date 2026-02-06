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
GRUPOS_DISCIPULADORES = {
    "Jovens": ["André e Larissa", "Lucas e Rosana", "Deric e Nayara"],
    "Adolescentes": ["Giovana", "Guilherme", "Larissa", "Bella", "Pedro"]
}
TODOS_DISCIPULADORES = GRUPOS_DISCIPULADORES["Jovens"] + GRUPOS_DISCIPULADORES["Adolescentes"]
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
        d_data = []
        for m in MESES_ORDEM:
            for l in TODOS_DISCIPULADORES:
                cat = "Jovens" if l in GRUPOS_DISCIPULADORES["Jovens"] else "Adolescentes"
                d_data.append({"Mês": m, "Líder": l, "Categoria": cat, "Valor": 0.0, "Pago": "Não"})
        f_data = []
        for mes in MESES_ORDEM:
            for disc in TODOS_DISCIPULADORES:
                cat = "Jovens" if disc in GRUPOS_DISCIPULADORES["Jovens"] else "Adolescentes"
                for tipo in TIPOS:
                    row = {"Mês": mes, "Discipulador": disc, "Categoria": cat, "Tipo": tipo}
                    for i in range(1, 6): row[f"S{i}_ME"] = row[f"S{i}_FA"] = row[f"S{i}_VI"] = 0
                    f_data.append(row)
        return pd.DataFrame(d_data), pd.DataFrame(f_data)

if 'df' not in st.session_state or 'df_freq' not in st.session_state:
    st.session_state.df, st.session_state.df_freq = carregar_dados_nuvem()

def salvar_nuvem():
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Dizimos", data=st.session_state.df)
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Frequencia", data=st.session_state.df_freq)
    st.cache_data.clear()

def formatar_brl(valor): return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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

tab1, tab2, tab3 = st.tabs(["📊 Frequência", "💰 Finanças", "⚙️ Admin"]) if is_admin else st.tabs(["📊 Frequência", "💰 Finanças"])

# --- ABA 1: FREQUÊNCIA ---
with tab1:
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

    def show_metrics(df_filter, label):
        cols_me = [f"S{i}_ME" for i in range(1, n_sab+1)]
        cols_fa = [f"S{i}_FA" for i in range(1, n_sab+1)]
        cols_vi = [f"S{i}_VI" for i in range(1, n_sab+1)]
        me, fa, vi = int(df_filter[cols_me].sum().sum()), int(df_filter[cols_fa].sum().sum()), int(df_filter[cols_vi].sum().sum())
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="metric-card"><span class="type-label">{label}</span><p class="metric-label">Membros</p><p class="metric-value">{me}</p></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><span class="type-label">{label}</span><p class="metric-label">Ativos</p><p class="metric-value">{fa}</p></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><span class="type-label">{label}</span><p class="metric-label">Visitantes</p><p class="metric-value">{vi}</p></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-card" style="border-color:#00D4FF"><span class="type-label">{label}</span><p class="metric-label">Total</p><p class="metric-value">{me+fa+vi}</p></div>', unsafe_allow_html=True)

    st.write("### 🏠 Células")
    show_metrics(df_f_view[df_f_view["Tipo"] == "Célula"], "CÉLULA")
    st.write("### 🎸 Culto")
    show_metrics(df_f_view[df_f_view["Tipo"] == "Culto de Jovens"], "CULTO")

    # Gráficos
    st.divider()
    g1, g2 = st.columns(2)
    with g1:
        idx = MESES_ORDEM.index(mes_sel)
        df_hist = st.session_state.df_freq[(st.session_state.df_freq["Mês"].isin(MESES_ORDEM[max(0,idx-2):idx+1])) & (st.session_state.df_freq["Discipulador"].isin(selecao_nomes))]
        cols = [f"S{i}_{ind}" for i in range(1,6) for ind in ["ME","FA","VI"]]
        df_g = df_hist.groupby(["Mês", "Tipo"], sort=False)[cols].sum().sum(axis=1).reset_index(name="Total")
        st.plotly_chart(px.bar(df_g, x="Mês", y="Total", color="Tipo", barmode="group", title="Histórico"), use_container_width=True)
    with g2:
        list_s = []
        for i, d_s in enumerate(sabados):
            for ind in CORES_AZYK:
                val = df_f_view[f"S{i+1}_{ind}"].sum()
                list_s.append({"Dia": d_s, "Tipo": ind, "Qtd": val})
        if list_s:
            st.plotly_chart(px.line(pd.DataFrame(list_s), x="Dia", y="Qtd", color="Tipo", markers=True, title="Evolução Semanal"), use_container_width=True)

    st.markdown('<div class="edit-section">', unsafe_allow_html=True)
    if st.toggle("📝 Modo Edição"):
        df_ed = st.data_editor(df_f_view, use_container_width=True, hide_index=True)
        if st.button("💾 Salvar Alterações"):
            for _, row in df_ed.iterrows():
                idx = st.session_state.df_freq[(st.session_state.df_freq["Mês"] == row["Mês"]) & (st.session_state.df_freq["Discipulador"] == row["Discipulador"]) & (st.session_state.df_freq["Tipo"] == row["Tipo"])].index
                st.session_state.df_freq.loc[idx, :] = row.values
            salvar_nuvem(); st.success("Salvo!"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 2: FINANÇAS ---
with tab2:
    f_cat = st.selectbox("Filtrar Categoria:", ["Todos", "Jovens", "Adolescentes"], key="f_cat")
    df_fin = st.session_state.df.copy()
    if f_cat != "Todos": df_fin = df_fin[df_fin["Categoria"] == f_cat]
    total = df_fin[df_fin["Pago"]=="Sim"]["Valor"].sum()
    st.markdown(f'<div class="metric-card"><p class="metric-label">Total Acumulado ({f_cat})</p><p class="metric-value" style="font-size:40px">{formatar_brl(total)}</p></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        df_m = df_fin[df_fin["Pago"]=="Sim"].groupby("Mês", sort=False)["Valor"].sum().reindex(MESES_ORDEM).fillna(0).reset_index()
        st.plotly_chart(px.line(df_m, x="Mês", y="Valor", markers=True, title="Entradas por Mês"), use_container_width=True)
    with c2:
        m_v = st.selectbox("Mês:", MESES_ORDEM, index=mes_atual_numero-1, key="m_v_fin")
        st.plotly_chart(px.pie(df_fin[df_fin["Mês"]==m_v], names="Pago", hole=0.5, title="Status"), use_container_width=True)

# --- ABA 3: ADMIN ---
if is_admin:
    with tab3:
        st.write("### ⚙️ Gestão")
        a1, a2 = st.columns(2)
        with a1:
            n_n = st.text_input("Novo Líder:")
            c_n = st.selectbox("Grupo:", ["Jovens", "Adolescentes"])
            if st.button("➕ Adicionar") and n_n:
                for m in MESES_ORDEM:
                    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"Mês":m,"Líder":n_n,"Categoria":c_n,"Valor":0.0,"Pago":"Não"}])], ignore_index=True)
                    for t in TIPOS:
                        row = {"Mês":m,"Discipulador":n_n,"Categoria":c_n,"Tipo":t}
                        for i in range(1,6): row[f"S{i}_ME"]=row[f"S{i}_FA"]=row[f"S{i}_VI"]=0
                        st.session_state.df_freq = pd.concat([st.session_state.df_freq, pd.DataFrame([row])], ignore_index=True)
                salvar_nuvem(); st.success("Adicionado!"); st.rerun()
        with a2:
            l_ex = st.selectbox("Remover:", sorted(st.session_state.df["Líder"].unique()))
            if st.button("🗑️ Excluir"):
                st.session_state.df = st.session_state.df[st.session_state.df["Líder"]!=l_ex]
                st.session_state.df_freq = st.session_state.df_freq[st.session_state.df_freq["Discipulador"]!=l_ex]
                salvar_nuvem(); st.warning("Removido!"); st.rerun()
        
        st.divider()
        m_adm = st.selectbox("Mês de Lançamento:", MESES_ORDEM, index=mes_atual_numero-1)
        df_ed_d = st.data_editor(st.session_state.df[st.session_state.df["Mês"]==m_adm], use_container_width=True, hide_index=True)
        if st.button("💾 Salvar Financeiro"):
            for _, r in df_ed_d.iterrows():
                pago = "Sim" if r["Valor"] > 0 else "Não"
                st.session_state.df.loc[(st.session_state.df["Mês"]==m_adm)&(st.session_state.df["Líder"]==r["Líder"]), ["Valor", "Pago"]] = [r["Valor"], pago]
            salvar_nuvem(); st.success("Sincronizado!"); st.rerun()

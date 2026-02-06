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
def carregar_dados():
    try:
        df_d = conn.read(spreadsheet=URL_PLANILHA, worksheet="Dizimos", ttl=0)
        df_f = conn.read(spreadsheet=URL_PLANILHA, worksheet="Frequencia", ttl=0)
        
        if df_f.empty or "Discipulador" not in df_f.columns:
            data_f = []
            for mes in MESES_ORDEM:
                for disc in TODOS_DISCIPULADORES:
                    cat = "Jovens" if disc in GRUPOS_DISCIPULADORES["Jovens"] else "Adolescentes"
                    for tipo in TIPOS:
                        row = {"Mês": mes, "Discipulador": disc, "Categoria": cat, "Tipo": tipo}
                        for i in range(1, 6): row[f"S{i}_ME"] = row[f"S{i}_FA"] = row[f"S{i}_VI"] = 0
                        data_f.append(row)
            df_f = pd.DataFrame(data_f)
            
        if df_d.empty or "Líder" not in df_d.columns:
            data_d = []
            for m in MESES_ORDEM:
                for l in TODOS_DISCIPULADORES:
                    cat = "Jovens" if l in GRUPOS_DISCIPULADORES["Jovens"] else "Adolescentes"
                    data_d.append({"Mês": m, "Líder": l, "Categoria": cat, "Valor": 0.0, "Pago": "Não"})
            df_d = pd.DataFrame(data_d)
            
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
    is_admin = (senha == "1234")
    if st.button("🔄 Sincronizar"):
        st.session_state.df, st.session_state.df_freq = carregar_dados()
        st.rerun()

st.markdown('<p class="main-title">⛪ RADICAIS LIVRES 2026</p>', unsafe_allow_html=True)

if is_admin:
    tabs = st.tabs(["📊 Frequência", "💰 Finanças", "⚙️ Admin"])
    tab1, tab2, tab3 = tabs
else:
    tabs = st.tabs(["📊 Frequência", "💰 Finanças"])
    tab1, tab2 = tabs

# --- ABA 1: FREQUÊNCIA ---
with tab1:
    col_sel1, col_sel2, col_sel3 = st.columns([1, 1, 2])
    with col_sel1: mes_sel = st.selectbox("📅 Mês:", MESES_ORDEM, key="f_mes", index=mes_atual_numero-1)
    with col_sel2: cat_freq_filt = st.radio("📂 Categoria:", ["Jovens", "Adolescentes", "Todos"], horizontal=True, key="cat_freq")
    
    sabados = obter_sabados_do_mes(mes_sel)
    n_sab = len(sabados)
    
    df_f_base = st.session_state.df_freq[st.session_state.df_freq["Mês"] == mes_sel].copy()
    if cat_freq_filt != "Todos":
        df_f_base = df_f_base[df_f_base["Categoria"] == cat_freq_filt]

    with col_sel3:
        lista_nomes = sorted(df_f_base["Discipulador"].unique())
        selecao_nomes = st.multiselect("👥 Filtrar Discipuladores:", lista_nomes, default=lista_nomes)

    df_f_view = df_f_base[df_f_base["Discipulador"].isin(selecao_nomes)]

    def render_metrics(df_filter, titulo_tipo):
        cols_me = [f"S{i}_ME" for i in range(1, n_sab+1)]
        cols_fa = [f"S{i}_FA" for i in range(1, n_sab+1)]
        cols_vi = [f"S{i}_VI" for i in range(1, n_sab+1)]
        me = int(df_filter[cols_me].sum().sum()); fa = int(df_filter[cols_fa].sum().sum()); vi = int(df_filter[cols_vi].sum().sum())
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="metric-card"><span class="type-label">{titulo_tipo}</span><p class="metric-label">Membros</p><p class="metric-value">{me}</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card"><span class="type-label">{titulo_tipo}</span><p class="metric-label">Freq. Ativa</p><p class="metric-value">{fa}</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card"><span class="type-label">{titulo_tipo}</span><p class="metric-label">Visitantes</p><p class="metric-value">{vi}</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card" style="border-color:#00D4FF"><span class="type-label">{titulo_tipo}</span><p class="metric-label">Total</p><p class="metric-value">{me+fa+vi}</p></div>', unsafe_allow_html=True)

    st.write("### 🏠 Resumo de Células")
    render_metrics(df_f_view[df_f_view["Tipo"] == "Célula"], "CÉLULA")
    st.write("### 🎸 Resumo de Culto")
    render_metrics(df_f_view[df_f_view["Tipo"] == "Culto de Jovens"], "CULTO")

    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.write("### 📅 Comparativo Mensal")
        idx_atual = MESES_ORDEM.index(mes_sel)
        meses_para_grafico = MESES_ORDEM[max(0, idx_atual-2) : idx_atual+1]
        df_mensal = st.session_state.df_freq[(st.session_state.df_freq["Mês"].isin(meses_para_grafico)) & (st.session_state.df_freq["Discipulador"].isin(selecao_nomes))].copy()
        cols_total = [f"S{i}_{ind}" for i in range(1, 6) for ind in ["ME", "FA", "VI"]]
        df_mensal_soma = df_mensal.groupby(["Mês", "Tipo"], sort=False)[cols_total].sum().sum(axis=1).reset_index(name="Total")
        fig_mensal = px.bar(df_mensal_soma, x="Mês", y="Total", color="Tipo", barmode="group", text_auto=True, color_discrete_sequence=["#00D4FF", "#0072FF"])
        fig_mensal.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig_mensal, use_container_width=True)

    with col_g2:
        st.write(f"### 📊 Frequência Semanal - {mes_sel}")
        list_semanal = []
        for i, data_sab in enumerate(sabados):
            for ind, cor in CORES_AZYK.items():
                valor = df_f_view[[f"S{i+1}_{ind}"]].sum().sum()
                list_semanal.append({"Sábado": data_sab, "Indicador": ind, "Quantidade": valor})
        if list_semanal:
            fig_sem = px.line(pd.DataFrame(list_semanal), x="Sábado", y="Quantidade", color="Indicador", markers=True, color_discrete_map=CORES_AZYK)
            fig_sem.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_sem, use_container_width=True)

    st.markdown('<div class="edit-section">', unsafe_allow_html=True)
    st.markdown("### 📝 Lançamento de Frequência")
    modo_edicao = st.toggle("Habilitar Edição", value=False)
    conf_f = {"Mês": None, "Categoria": None, "Discipulador": st.column_config.Column(disabled=True), "Tipo": st.column_config.Column(disabled=True)}
    for i in range(1, 6):
        if i <= n_sab:
            conf_f[f"S{i}_ME"] = st.column_config.NumberColumn(f"{sabados[i-1]}|ME")
            conf_f[f"S{i}_FA"] = st.column_config.NumberColumn(f"{sabados[i-1]}|FA")
            conf_f[f"S{i}_VI"] = st.column_config.NumberColumn(f"{sabados[i-1]}|VI")
        else:
            conf_f[f"S{i}_ME"] = conf_f[f"S{i}_FA"] = conf_f[f"S{i}_VI"] = None
    
    if modo_edicao:
        df_ed_f = st.data_editor(df_f_view, column_config=conf_f, use_container_width=True, hide_index=True)
        if st.button("💾 Salvar Frequência"):
            for _, row in df_ed_f.iterrows():
                idx = st.session_state.df_freq[(st.session_state.df_freq["Mês"] == row["Mês"]) & (st.session_state.df_freq["Discipulador"] == row["Discipulador"]) & (st.session_state.df_freq["Tipo"] == row["Tipo"])].index
                st.session_state.df_freq.loc[idx, :] = row.values
            salvar_dados()
            st.success("Salvo!"); st.rerun()
    else:
        st.dataframe(df_f_view, column_config=conf_f, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 2: FINANÇAS ---
with tab2:
    cat_fin_view = st.selectbox("🔍 Ver Finanças de:", ["Todos", "Jovens", "Adolescentes"], key="cat_fin")
    df_fin_filtrado = st.session_state.df.copy()
    if cat_fin_view != "Todos":
        df_fin_filtrado = df_fin_filtrado[df_fin_filtrado["Categoria"] == cat_fin_view]
    
    df_pago = df_fin_filtrado[df_fin_filtrado["Pago"] == "Sim"]
    
    st.markdown(f'''<div style="background:linear-gradient(90deg, #1E293B, #0072FF); padding:25px; border-radius:15px; border-left:5px solid #00D4FF; margin-bottom:20px;">
        <p class="metric-label">Total Acumulado ({cat_fin_view})</p>
        <p style="font-size:36px; font-weight:900; margin:0;">{formatar_brl(df_pago["Valor"].sum())}</p>
    </div>''', unsafe_allow_html=True)
    
    c1, c2 = st.columns([2, 1.2]) # Ajuste leve na proporção
    
    with c1:
        st.write("### 📈 Evolução de Arrecadação")
        df_evol = df_pago.groupby("Mês", sort=False)["Valor"].sum().reindex(MESES_ORDEM).fillna(0).reset_index()
        fig_l = px.line(df_evol, x="Mês", y="Valor", text="Valor", markers=True)
        fig_l.update_traces(texttemplate='R$ %{y:,.2f}', textposition="top center", line_color="#00D4FF")
        fig_l.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", margin=dict(t=20, b=20))
        st.plotly_chart(fig_l, use_container_width=True)
    
    with c2:
        m_v = st.selectbox("Status no Mês:", MESES_ORDEM, index=mes_atual_numero-1)
        st.write(f"### 🍩 Status: {m_v}")
        
        # Filtro para o gráfico de pizza
        df_pizza = df_fin_filtrado[df_fin_filtrado["Mês"] == m_v]
        
        # Criação do Gráfico de Pizza (Donut) melhorado
        fig_p = px.pie(
            df_pizza, 
            names='Pago', 
            hole=0.6, 
            color='Pago',
            color_discrete_map={'Sim': '#00D4FF', 'Não': '#EF4444'}
        )
        
        # Melhorando o layout para tirar o fundo preto e alinhar
        fig_p.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)", 
            font_color="white",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            margin=dict(t=0, b=0, l=0, r=0)
        )
        
        # Ajuste de informações no hover e no gráfico
        fig_p.update_traces(textposition='inside', textinfo='percent+label')
        
        st.plotly_chart(fig_p, use_container_width=True)

# --- ABA 3: ADMIN ---
if is_admin:
    with tab3:
        st.write("### 👥 Gestão de Líderes")
        col_adm1, col_adm2 = st.columns(2)
        with col_adm1:
            nome_n = st.text_input("Nome:")
            cat_n = st.selectbox("Categoria:", ["Jovens", "Adolescentes"])
            if st.button("Confirmar Adição"):
                if nome_n:
                    novas_d = pd.DataFrame([{"Mês": m, "Líder": nome_n, "Categoria": cat_n, "Valor": 0.0, "Pago": "Não"} for m in MESES_ORDEM])
                    st.session_state.df = pd.concat([st.session_state.df, novas_d], ignore_index=True)
                    novas_f = pd.DataFrame([{"Mês": m, "Discipulador": nome_n, "Categoria": cat_n, "Tipo": t, **{f"S{i}_{ind}": 0 for i in range(1, 6) for ind in ["ME", "FA", "VI"]}} for m in MESES_ORDEM for t in TIPOS])
                    st.session_state.df_freq = pd.concat([st.session_state.df_freq, novas_f], ignore_index=True)
                    salvar_dados(); st.success("Adicionado!"); st.rerun()
        
        with col_adm2:
            lider_ex = st.selectbox("Escolher para remover:", sorted(st.session_state.df["Líder"].unique()))
            if st.button("Excluir Permanentemente"):
                st.session_state.df = st.session_state.df[st.session_state.df["Líder"] != lider_ex]
                st.session_state.df_freq = st.session_state.df_freq[st.session_state.df_freq["Discipulador"] != lider_ex]
                salvar_dados(); st.warning("Removido!"); st.rerun()

        st.divider()
        st.markdown("### 💰 Lançamento de Dízimos")
        df_ed_diz = st.data_editor(st.session_state.df[st.session_state.df["Mês"] == st.selectbox("Mês de Lançamento:", MESES_ORDEM, index=mes_atual_numero-1, key="adm_m")],
            use_container_width=True, hide_index=True, column_config={"Mês": None, "Líder": st.column_config.Column(disabled=True), "Categoria": st.column_config.Column(disabled=True)})
        if st.button("💾 Salvar Dízimos"):
            for _, row in df_ed_diz.iterrows():
                row["Pago"] = "Sim" if row["Valor"] > 0 else "Não"
                idx = st.session_state.df[(st.session_state.df["Mês"] == row["Mês"]) & (st.session_state.df["Líder"] == row["Líder"])].index
                st.session_state.df.loc[idx, ["Valor", "Pago"]] = [row["Valor"], row["Pago"]]
            salvar_dados(); st.success("Salvo!"); st.rerun()

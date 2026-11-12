import calendar
import hmac
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Radicais Livres 2026", layout="wide", page_icon="⛪")

# --- CONEXÃO GOOGLE SHEETS (igual à versão anterior) ---
conn = st.connection("gsheets", type=GSheetsConnection)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1ptEbNIYh9_vVHJhnYLVoicAZ9REHTuIsBO4c1h7PsIs/edit#gid=0"
ABA_DIZIMOS = "Dizimos"
ABA_FREQ = "Frequencia"
SENHA_ADMIN = "Videira@1020"

# --- CONFIGURAÇÕES ---
ANO = 2026
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
GRUPOS_DISCIPULADORES = {
    "Jovens": ["André e Larissa", "Lucas e Rosana", "Deric e Nayara"],
    "Adolescentes": ["Giovana", "Gui&La", "Bella", "Pedro"],
}
TODOS_DISCIPULADORES = GRUPOS_DISCIPULADORES["Jovens"] + GRUPOS_DISCIPULADORES["Adolescentes"]
CATEGORIAS = ["Jovens", "Adolescentes"]
TIPOS = ["Célula", "Culto de Jovens"]
INDICADORES = {"ME": "Membros", "FA": "FA", "VI": "Visitantes"}
CORES_IND = {"Membros": "#22D3EE", "FA": "#818CF8", "Visitantes": "#FBBF24"}
CORES_TIPO = {"Célula": "#22D3EE", "Culto de Jovens": "#818CF8"}
COLS_S = [f"S{i}_{ind}" for i in range(1, 6) for ind in INDICADORES]
COLS_DIZIMOS = ["Mês", "Líder", "Categoria", "Valor", "Pago"]
COLS_FREQ = ["Mês", "Discipulador", "Categoria", "Tipo"] + COLS_S

FUSO = ZoneInfo("America/Sao_Paulo")
AGORA = datetime.now(FUSO)
IDX_MES_ATUAL = AGORA.month - 1


def sabados_do_mes(idx_mes):
    return [f"{sem[calendar.SATURDAY]:02d}/{idx_mes + 1:02d}"
            for sem in calendar.monthcalendar(ANO, idx_mes + 1) if sem[calendar.SATURDAY]]


SABADOS = {m: sabados_do_mes(i) for i, m in enumerate(MESES)}


def _versao_streamlit():
    try:
        return tuple(int(p) for p in st.__version__.split(".")[:2])
    except Exception:
        return (0, 0)


# Versões novas do Streamlit trocaram use_container_width por width="stretch".
LARGURA = {"width": "stretch"} if _versao_streamlit() >= (1, 52) else {"use_container_width": True}
SEM_BARRA = {"displayModeBar": False}

# --- ESTILO ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, .stApp, .stApp p, .stApp label, .stApp input, .stApp button, .stApp div { font-family: 'Plus Jakarta Sans', system-ui, -apple-system, 'Segoe UI', sans-serif; }
.stApp { background: radial-gradient(900px 500px at 100% -10%, rgba(129,140,248,.16) 0%, rgba(8,12,24,0) 60%), radial-gradient(900px 500px at 0% 0%, rgba(34,211,238,.12) 0%, rgba(8,12,24,0) 55%), #080C18; color: #E5E9F5; }
.stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #E5E9F5; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1320px; }
[data-testid="stHeader"] { background: transparent; }

.hero { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap; padding: 26px 28px; border-radius: 24px; margin-bottom: 18px; border: 1px solid rgba(255,255,255,.08); background: linear-gradient(120deg, rgba(34,211,238,.16) 0%, rgba(129,140,248,.14) 55%, rgba(255,255,255,.03) 100%); }
.hero-kicker { color: #22D3EE; font-size: 12px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; }
.hero-titulo { color: #FFFFFF; font-size: clamp(28px, 5.5vw, 46px); font-weight: 800; letter-spacing: -1.2px; line-height: 1.05; margin-top: 4px; }
.hero-sub { color: #A5AEC6; font-size: 14px; margin-top: 6px; }
.hero-chip { display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 999px; background: rgba(8,12,24,.55); border: 1px solid rgba(255,255,255,.1); color: #CBD3E6; font-size: 12px; font-weight: 600; }
.ponto { width: 8px; height: 8px; border-radius: 50%; background: #34D399; box-shadow: 0 0 0 4px rgba(52,211,153,.18); display: inline-block; }

.secao { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 1.5rem 0 .8rem 0; }
.secao-titulo { font-size: 17px; font-weight: 700; color: #FFFFFF; }
.secao-detalhe { font-size: 12px; font-weight: 500; color: #8E99B5; }
.secao::before { content: ""; width: 4px; height: 18px; border-radius: 4px; background: linear-gradient(180deg, #22D3EE, #818CF8); }

.painel-titulo { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; font-size: 15px; font-weight: 700; color: #FFFFFF; margin: .4rem 0 .6rem 0; }
.painel-titulo small { font-size: 11px; font-weight: 600; color: #8E99B5; background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.08); padding: 3px 10px; border-radius: 999px; }
.kpi-grade { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 8px; }
.kpi { position: relative; overflow: hidden; background: rgba(255,255,255,.035); border: 1px solid rgba(255,255,255,.08); border-radius: 18px; padding: 14px 16px 14px 20px; }
.kpi::before { content: ""; position: absolute; left: 0; top: 14px; bottom: 14px; width: 4px; border-radius: 0 4px 4px 0; background: var(--cor, #22D3EE); }
.kpi.cheio { background: linear-gradient(135deg, rgba(34,211,238,.20), rgba(129,140,248,.18)); border-color: rgba(34,211,238,.35); }
.kpi-rotulo { color: #8E99B5; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
.kpi-valor { color: #FFFFFF; white-space: nowrap; font-size: clamp(20px, 2.1vw, 26px); font-weight: 800; line-height: 1.25; letter-spacing: -.5px; font-variant-numeric: tabular-nums; }
.kpi-detalhe { color: #8E99B5; font-size: 12px; min-height: 18px; }
.delta { display: block; font-weight: 700; margin-top: 2px; }
.delta.sobe { color: #34D399; } .delta.desce { color: #FB7185; } .delta.neutro { color: #8E99B5; }

.destaque { display: flex; justify-content: space-between; align-items: center; gap: 18px; flex-wrap: wrap; padding: 24px 26px; border-radius: 22px; margin: 6px 0 12px 0; border: 1px solid rgba(34,211,238,.3); background: linear-gradient(120deg, rgba(34,211,238,.22) 0%, rgba(129,140,248,.22) 100%); }
.destaque-rotulo { color: #CBD3E6; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.4px; }
.destaque-valor { color: #FFFFFF; font-size: clamp(30px, 6.5vw, 46px); font-weight: 800; letter-spacing: -1px; line-height: 1.15; font-variant-numeric: tabular-nums; }
.destaque-lado { text-align: right; color: #CBD3E6; font-size: 13px; }
.barra { width: 220px; max-width: 60vw; height: 8px; border-radius: 999px; background: rgba(8,12,24,.5); overflow: hidden; margin-top: 8px; margin-left: auto; }
.barra > span { display: block; height: 100%; border-radius: 999px; background: linear-gradient(90deg, #22D3EE, #34D399); }

.stTabs [role="tablist"] { gap: 4px; background: rgba(255,255,255,.04); padding: 5px; border-radius: 999px; border: 1px solid rgba(255,255,255,.08); width: fit-content; max-width: 100%; border-bottom: 1px solid rgba(255,255,255,.08) !important; box-shadow: none !important; }
.stTabs [role="tab"] { border-radius: 999px !important; padding: 8px 20px; height: auto; background: transparent; border: 0 !important; box-shadow: none !important; }
.stTabs [role="tab"] p { color: #A5AEC6; font-weight: 700; font-size: 14px; }
.stTabs [role="tab"][aria-selected="true"] { background: #FFFFFF !important; }
.stTabs [role="tab"][aria-selected="true"] p { color: #080C18; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [role="tablist"]::before, .stTabs [role="tablist"]::after, .stTabs [role="tab"]::before, .stTabs [role="tab"]::after { display: none !important; }

[data-testid="stPlotlyChart"] { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.08); border-radius: 20px; padding: 10px 8px 4px 8px; }
[data-testid="stForm"] { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.08); border-radius: 20px; }
[data-testid="stExpander"] details { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.08); border-radius: 16px; }
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button { background: linear-gradient(90deg, #22D3EE 0%, #818CF8 100%); color: #080C18; border: 0; border-radius: 999px; font-weight: 800; padding: .5rem 1.3rem; }
.stButton > button p, .stDownloadButton > button p, [data-testid="stFormSubmitButton"] > button p { color: #080C18; font-weight: 800; }
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover { filter: brightness(1.1); color: #080C18; }
.stButton > button:disabled { opacity: .4; }
[data-testid="stSidebar"] { background: #0B1020; border-right: 1px solid rgba(255,255,255,.08); }
</style>
""", unsafe_allow_html=True)


# --- FORMATAÇÃO ---
def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def num(valor, casas=1):
    return f"{valor:.{casas}f}".replace(".", ",")


def cartao(rotulo, valor, detalhe="", cor="#22D3EE", cheio=False):
    classe = "kpi cheio" if cheio else "kpi"
    return (f'<div class="{classe}" style="--cor:{cor}"><div class="kpi-rotulo">{rotulo}</div>'
            f'<div class="kpi-valor">{valor}</div>'
            f'<div class="kpi-detalhe">{detalhe or "&nbsp;"}</div></div>')


def grade(cartoes):
    st.markdown('<div class="kpi-grade">' + "".join(cartoes) + '</div>', unsafe_allow_html=True)


def secao(titulo, detalhe=""):
    extra = f'<span class="secao-detalhe">{detalhe}</span>' if detalhe else ""
    st.markdown(f'<div class="secao"><span class="secao-titulo">{titulo}</span>{extra}</div>', unsafe_allow_html=True)


def delta_html(atual, anterior, referencia):
    if not anterior:
        return ""
    pct = (atual - anterior) / anterior * 100
    if abs(pct) < 0.5:
        return f'<span class="delta neutro">● igual a {referencia}</span>'
    seta, classe = ("▲", "sobe") if pct > 0 else ("▼", "desce")
    return f'<span class="delta {classe}">{seta} {abs(pct):.0f}% vs {referencia}</span>'


def estilo(fig, altura=360):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD3E6", family="Plus Jakarta Sans, sans-serif", size=13),
        height=altura, margin=dict(l=12, r=12, t=34, b=8),
        legend=dict(orientation="h", yanchor="top", y=-0.14, xanchor="center", x=0.5, title_text=""),
        hoverlabel=dict(bgcolor="#0B1020", font_color="#FFFFFF", bordercolor="rgba(255,255,255,.15)"),
        bargap=0.28,
    )
    fig.update_xaxes(showgrid=False, linecolor="rgba(255,255,255,.12)", title_text="")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.06)", zeroline=False, title_text="")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=13, color="#FFFFFF")))
    return fig


# --- DADOS ---
class ErroDados(Exception):
    pass


def _numerico(serie):
    numero = pd.to_numeric(serie, errors="coerce")
    if numero.isna().any():
        texto = (serie.astype(str).str.replace("R$", "", regex=False).str.replace(".", "", regex=False)
                 .str.replace(",", ".", regex=False).str.strip())
        numero = numero.fillna(pd.to_numeric(texto, errors="coerce"))
    return numero.fillna(0)


def _ler_aba(aba, obrigatorias):
    """Lê uma aba como ela está. Se algo estiver errado, levanta erro em vez de devolver tabela vazia."""
    try:
        df = pd.DataFrame(conn.read(spreadsheet=URL_PLANILHA, worksheet=aba, ttl=0))
    except Exception as erro:
        raise ErroDados(f"não consegui ler a aba {aba}: {erro}") from erro
    df = df.dropna(how="all")
    df = df[[c for c in df.columns if not (str(c).startswith("Unnamed") and df[c].isna().all())]]
    faltando = [c for c in obrigatorias if c not in df.columns]
    if faltando:
        raise ErroDados(f"a aba {aba} veio sem as colunas: " + ", ".join(faltando))
    if df.empty:
        raise ErroDados(f"a aba {aba} veio vazia")
    return df.reset_index(drop=True)


def ler_dizimos():
    return _ler_aba(ABA_DIZIMOS, COLS_DIZIMOS)


def ler_freq():
    return _ler_aba(ABA_FREQ, COLS_FREQ)


@st.cache_data(ttl=60, show_spinner="Carregando dados da planilha…")
def carregar_dados():
    return ler_dizimos(), ler_freq(), datetime.now(FUSO).strftime("%H:%M")


def gravar(aba, df):
    conn.update(spreadsheet=URL_PLANILHA, worksheet=aba, data=df)
    st.cache_data.clear()


def salvar_frequencia(base, editado, colunas):
    """Relê a planilha e grava só as células que mudaram na tela."""
    atual = ler_freq()
    linhas_antes = len(atual)
    mudancas = 0
    for i in range(len(base)):
        antes, depois = base.iloc[i], editado.iloc[i]
        filtro = ((atual["Mês"] == antes["Mês"]) & (atual["Discipulador"] == antes["Discipulador"])
                  & (atual["Tipo"] == antes["Tipo"]))
        for c in colunas:
            novo = pd.to_numeric(depois[c], errors="coerce")
            novo = 0 if pd.isna(novo) else max(0, int(round(novo)))
            if novo != int(antes[c]):
                if not filtro.any():
                    raise ErroDados("a planilha mudou desde que a página abriu; clique em Sincronizar e tente de novo")
                atual.loc[filtro, c] = novo
                mudancas += 1
    if mudancas:
        if len(atual) != linhas_antes:
            raise ErroDados("contagem de linhas inesperada; nada foi gravado")
        gravar(ABA_FREQ, atual)
    return mudancas


def salvar_dizimos(base, editado):
    atual = ler_dizimos()
    mudancas = 0
    for i in range(len(base)):
        antes, depois = base.iloc[i], editado.iloc[i]
        novo = pd.to_numeric(depois["Valor"], errors="coerce")
        novo = 0.0 if pd.isna(novo) else max(0.0, float(novo))
        if abs(novo - float(antes["Valor"])) > 0.004:
            filtro = (atual["Mês"] == antes["Mês"]) & (atual["Líder"] == antes["Líder"])
            if not filtro.any():
                raise ErroDados("a planilha mudou desde que a página abriu; clique em Sincronizar e tente de novo")
            atual.loc[filtro, "Valor"] = novo
            atual.loc[filtro, "Pago"] = "Sim" if novo > 0 else "Não"
            mudancas += 1
    if mudancas:
        gravar(ABA_DIZIMOS, atual)
    return mudancas


def adicionar_lider(nome, categoria):
    diz, freq = ler_dizimos(), ler_freq()
    if nome.lower() in diz["Líder"].astype(str).str.strip().str.lower().values:
        raise ErroDados(f"já existe um líder chamado {nome}")
    novas_d = pd.DataFrame([{"Mês": m, "Líder": nome, "Categoria": categoria, "Valor": 0.0, "Pago": "Não"}
                            for m in MESES])
    novas_f = pd.DataFrame([{"Mês": m, "Discipulador": nome, "Categoria": categoria, "Tipo": t,
                             **{c: 0 for c in COLS_S}} for m in MESES for t in TIPOS])
    gravar(ABA_DIZIMOS, pd.concat([diz, novas_d], ignore_index=True))
    gravar(ABA_FREQ, pd.concat([freq, novas_f], ignore_index=True))


def remover_lider(nome):
    diz, freq = ler_dizimos(), ler_freq()
    novo_d = diz[diz["Líder"] != nome]
    novo_f = freq[freq["Discipulador"] != nome]
    if novo_d.empty or novo_f.empty:
        raise ErroDados("essa remoção deixaria a planilha vazia; nada foi gravado")
    gravar(ABA_DIZIMOS, novo_d)
    if len(novo_f) != len(freq):
        gravar(ABA_FREQ, novo_f)


def formato_longo(df):
    longo = df.melt(id_vars=["Mês", "Discipulador", "Categoria", "Tipo"], value_vars=COLS_S,
                    var_name="col", value_name="Valor")
    longo["Semana"] = longo["col"].str[1].astype(int)
    longo["Indicador"] = longo["col"].str[3:]
    n_sab = longo["Mês"].map({m: len(s) for m, s in SABADOS.items()}).fillna(0)
    return longo[longo["Semana"] <= n_sab].drop(columns="col")


def resumo(base, mes, tipo):
    """Totais por indicador e quantidade de sábados com lançamento."""
    f = base[(base["Mês"] == mes) & (base["Tipo"] == tipo)]
    por_sabado = f.groupby("Semana")["Valor"].sum()
    totais = f.groupby("Indicador")["Valor"].sum().reindex(list(INDICADORES)).fillna(0)
    return totais, int((por_sabado > 0).sum())


# --- CARGA ---
try:
    bruto_diz, bruto_freq, hora_carga = carregar_dados()
except Exception as erro:
    st.error(f"⚠️ Não foi possível carregar os dados: {erro}")
    st.info("Nada foi alterado na planilha. O app fica bloqueado para não gravar por cima dos seus dados.")
    if st.button("🔄 Tentar de novo"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

# Cópias de trabalho com números tratados; a planilha só recebe o que for editado.
df_diz = bruto_diz.copy()
df_diz["Valor"] = _numerico(df_diz["Valor"]).astype(float)
df_freq = bruto_freq.copy()
for _c in COLS_S:
    df_freq[_c] = _numerico(df_freq[_c]).round().astype(int)

if "rev" not in st.session_state:
    st.session_state.rev = 0


def concluir(mensagem):
    st.session_state.rev += 1
    st.session_state.aviso = mensagem
    st.rerun()


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🔐 Acesso")
    senha = st.text_input("Senha administrativa", type="password")
    is_admin = bool(senha) and hmac.compare_digest(senha.encode(), SENHA_ADMIN.encode())
    if is_admin:
        st.caption("✅ Modo administrador")
    elif senha:
        st.caption("Senha incorreta.")
    if st.button("🔄 Sincronizar"):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Dados lidos às {hora_carga}")

# --- CABEÇALHO ---
st.markdown(
    '<div class="hero"><div><div class="hero-kicker">Painel 2026</div>'
    '<div class="hero-titulo">⛪ Radicais Livres</div>'
    '<div class="hero-sub">Frequência de células e cultos · Dízimos</div></div>'
    f'<div class="hero-chip"><span class="ponto"></span>Planilha lida às {hora_carga}</div></div>',
    unsafe_allow_html=True)

if "aviso" in st.session_state:
    st.success(st.session_state.pop("aviso"))

if is_admin:
    tab1, tab2, tab3 = st.tabs(["📊 Frequência", "💰 Finanças", "⚙️ Admin"])
else:
    tab1, tab2 = st.tabs(["📊 Frequência", "💰 Finanças"])
    tab3 = None

# --- ABA 1: FREQUÊNCIA ---
with tab1:
    f1, f2, f3 = st.columns([1, 1.7, 2])
    mes_sel = f1.selectbox("📅 Mês", MESES, index=IDX_MES_ATUAL, key="f_mes")
    cat_freq = f2.radio("📂 Categoria", ["Jovens", "Adolescentes", "Todos"], horizontal=True, key="cat_freq")

    idx_mes = MESES.index(mes_sel)
    sabados = SABADOS[mes_sel]
    n_sab = len(sabados)
    mes_ant = MESES[idx_mes - 1] if idx_mes > 0 else None

    df_base = df_freq[(df_freq["Mês"] == mes_sel) & (df_freq["Discipulador"].isin(TODOS_DISCIPULADORES))]
    if cat_freq != "Todos":
        df_base = df_base[df_base["Categoria"] == cat_freq]
    nomes = sorted(df_base["Discipulador"].unique())
    selecao = f3.multiselect("👥 Discipuladores", nomes, default=nomes, key=f"f_disc_{cat_freq}")

    if not selecao:
        st.info("Selecione pelo menos um discipulador para ver os dados.")
    else:
        longo = formato_longo(df_freq[df_freq["Discipulador"].isin(selecao)])
        if cat_freq != "Todos":
            longo = longo[longo["Categoria"] == cat_freq]

        # Resumo: dois painéis lado a lado
        paineis = st.columns(2)
        for coluna, (tipo, titulo) in zip(paineis, (("Célula", "🏠 Células"), ("Culto de Jovens", "🎸 Culto"))):
            with coluna:
                totais, n = resumo(longo, mes_sel, tipo)
                totais_ant, n_ant = resumo(longo, mes_ant, tipo) if mes_ant else (None, 0)
                st.markdown(f'<div class="painel-titulo">{titulo}<small>{n} de {n_sab} sábados lançados</small></div>',
                            unsafe_allow_html=True)
                itens = []
                for ind, nome, cor in (("ME", "Membros", "#22D3EE"), ("FA", "FA", "#818CF8"),
                                       ("VI", "Visitantes", "#FBBF24"), ("TOTAL", "Total", "#34D399")):
                    valor = int(totais.sum()) if ind == "TOTAL" else int(totais[ind])
                    detalhe = ""
                    if n:
                        media = valor / n
                        detalhe = f"média {num(media)} por sábado"
                        if n_ant:
                            valor_ant = totais_ant.sum() if ind == "TOTAL" else totais_ant[ind]
                            detalhe += delta_html(media, valor_ant / n_ant, mes_ant)
                    itens.append(cartao(nome, valor, detalhe, cor=cor, cheio=(ind == "TOTAL")))
                grade(itens)

        do_mes = longo[longo["Mês"] == mes_sel]
        if do_mes["Valor"].sum() == 0:
            st.info(f"Ainda não há lançamentos em {mes_sel}. Use a tabela no fim da página para lançar.")
        else:
            secao(f"Frequência semanal · {mes_sel}", "por sábado e indicador")
            por_sab = do_mes.groupby(["Semana", "Tipo", "Indicador"], as_index=False)["Valor"].sum()
            por_sab["Sábado"] = por_sab["Semana"].map(lambda i: sabados[i - 1])
            por_sab["Indicador"] = por_sab["Indicador"].map(INDICADORES)
            fig = px.bar(por_sab, x="Sábado", y="Valor", color="Indicador", barmode="group", facet_col="Tipo",
                         text="Valor", color_discrete_map=CORES_IND,
                         category_orders={"Sábado": sabados, "Tipo": TIPOS, "Indicador": list(INDICADORES.values())})
            fig.update_xaxes(type="category")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            st.plotly_chart(estilo(fig, 380), config=SEM_BARRA, **LARGURA)

            g1, g2 = st.columns(2)
            with g1:
                janela = MESES[max(0, idx_mes - 2): idx_mes + 1]
                secao("Comparativo mensal", "total de presenças, últimos 3 meses")
                mensal = (longo[longo["Mês"].isin(janela)].groupby(["Mês", "Tipo"], as_index=False)["Valor"].sum()
                          .rename(columns={"Valor": "Total"}))
                fig = px.bar(mensal, x="Mês", y="Total", color="Tipo", barmode="group", text="Total",
                             color_discrete_map=CORES_TIPO, category_orders={"Mês": janela, "Tipo": TIPOS})
                fig.update_xaxes(type="category")
                fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
                st.plotly_chart(estilo(fig, 360), config=SEM_BARRA, **LARGURA)
            with g2:
                secao("Por discipulador", f"total em {mes_sel}")
                por_disc = do_mes.groupby(["Discipulador", "Indicador"], as_index=False)["Valor"].sum()
                por_disc["Indicador"] = por_disc["Indicador"].map(INDICADORES)
                ordem_disc = (por_disc.groupby("Discipulador")["Valor"].sum().sort_values(ascending=False).index.tolist())
                fig = px.bar(por_disc, y="Discipulador", x="Valor", color="Indicador", orientation="h",
                             barmode="stack", text="Valor", color_discrete_map=CORES_IND,
                             category_orders={"Discipulador": ordem_disc, "Indicador": list(INDICADORES.values())})
                fig.update_traces(marker_line_width=0, insidetextanchor="middle")
                st.plotly_chart(estilo(fig, 360), config=SEM_BARRA, **LARGURA)

        # Lançamento
        secao("📝 Lançamento de frequência", "ME = membros · FA · VI = visitantes")
        modo_edicao = st.toggle("Habilitar edição", value=False)

        df_view = df_base[df_base["Discipulador"].isin(selecao)].reset_index(drop=True)
        visiveis = [f"S{i}_{ind}" for i in range(1, n_sab + 1) for ind in INDICADORES]
        conf = {"Discipulador": st.column_config.Column(disabled=True),
                "Tipo": st.column_config.Column(disabled=True)}
        for i in range(1, n_sab + 1):
            for ind in INDICADORES:
                conf[f"S{i}_{ind}"] = st.column_config.NumberColumn(f"{sabados[i - 1]} · {ind}", min_value=0, step=1)
        ordem = ["Discipulador", "Tipo"] + visiveis

        if modo_edicao:
            with st.form("form_freq"):
                chave = f"ed_freq_{mes_sel}_{cat_freq}_{'|'.join(selecao)}_{st.session_state.rev}"
                editado = st.data_editor(df_view, column_config=conf, column_order=ordem, hide_index=True,
                                         key=chave, **LARGURA)
                if st.form_submit_button("💾 Salvar frequência"):
                    try:
                        mudancas = salvar_frequencia(df_view, editado, visiveis)
                    except Exception as erro:
                        st.error(f"Não foi possível salvar, nada foi alterado: {erro}")
                    else:
                        if mudancas:
                            concluir(f"Frequência de {mes_sel} salva ({mudancas} valor(es) alterado(s)).")
                        else:
                            st.info("Nenhum valor foi alterado.")
        else:
            st.dataframe(df_view, column_config=conf, column_order=ordem, hide_index=True, **LARGURA)

# --- ABA 2: FINANÇAS ---
with tab2:
    c1, c2 = st.columns([1.3, 1])
    cat_fin = c1.radio("🔍 Ver finanças de", ["Todos", "Jovens", "Adolescentes"], horizontal=True, key="cat_fin")
    mes_fin = c2.selectbox("📅 Mês", MESES, index=IDX_MES_ATUAL, key="mes_fin_stat")
    idx_fin = MESES.index(mes_fin)

    df_fin = df_diz if cat_fin == "Todos" else df_diz[df_diz["Categoria"] == cat_fin]
    df_mes = df_fin[df_fin["Mês"] == mes_fin]
    pagos = df_fin[df_fin["Pago"] == "Sim"]
    pagos_mes = pagos[pagos["Mês"] == mes_fin]

    total_mes = pagos_mes["Valor"].sum()
    n_lideres = len(df_mes)
    em_dia = len(pagos_mes)
    pct = (em_dia / n_lideres * 100) if n_lideres else 0
    st.markdown(
        f'<div class="destaque"><div><div class="destaque-rotulo">Total no mês · {mes_fin}</div>'
        f'<div class="destaque-valor">{formatar_brl(total_mes)}</div></div>'
        f'<div class="destaque-lado"><b>{em_dia} de {n_lideres}</b> líderes com dízimo lançado'
        f'<div class="barra"><span style="width:{pct:.0f}%"></span></div></div></div>',
        unsafe_allow_html=True)

    rotulo_ant, valor_ant_txt, detalhe_mes = "Mês anterior", "—", ""
    if idx_fin > 0:
        anterior = pagos[pagos["Mês"] == MESES[idx_fin - 1]]["Valor"].sum()
        rotulo_ant, valor_ant_txt = MESES[idx_fin - 1], formatar_brl(anterior)
        detalhe_mes = delta_html(total_mes, anterior, MESES[idx_fin - 1]).replace(
            f"vs {MESES[idx_fin - 1]}", f"em {mes_fin}")
    grade([
        cartao(f"Acumulado em {ANO}", formatar_brl(pagos["Valor"].sum()), cor="#34D399"),
        cartao(rotulo_ant, valor_ant_txt, detalhe_mes, cor="#22D3EE"),
        cartao("Adesão no mês", f"{pct:.0f}%", f"{n_lideres - em_dia} sem lançamento", cor="#818CF8"),
        cartao("Média por dízimo", formatar_brl(total_mes / em_dia) if em_dia else "—", cor="#FBBF24"),
    ])

    g1, g2 = st.columns([2, 1.1])
    with g1:
        secao("Evolução de arrecadação")
        evol = pagos.groupby("Mês")["Valor"].sum().reindex(MESES).fillna(0).reset_index()
        evol["Rótulo"] = evol["Valor"].map(lambda v: formatar_brl(v)[:-3] if v else "")
        evol["Mês curto"] = evol["Mês"].str[:3]
        fig = px.line(evol, x="Mês curto", y="Valor", text="Rótulo", markers=True)
        fig.update_traces(line_color="#22D3EE", line_width=3, fill="tozeroy", fillcolor="rgba(34,211,238,.10)",
                          textposition=["top center" if i % 2 == 0 else "bottom center" for i in range(len(evol))],
                          cliponaxis=False, marker=dict(size=[13 if m == mes_fin else 7 for m in evol["Mês"]],
                                      color=["#FFFFFF" if m == mes_fin else "#22D3EE" for m in evol["Mês"]]),
                          hovertemplate="%{x}: %{text}<extra></extra>")
        fig.update_xaxes(type="category")
        fig.update_yaxes(rangemode="tozero")
        st.plotly_chart(estilo(fig, 380), config=SEM_BARRA, **LARGURA)
    with g2:
        secao(f"Status · {mes_fin}")
        if df_mes.empty:
            st.info("Sem líderes nesse filtro.")
        else:
            fig = px.pie(df_mes, names="Pago", color="Pago", hole=0.64,
                         color_discrete_map={"Sim": "#22D3EE", "Não": "#FB7185"},
                         category_orders={"Pago": ["Sim", "Não"]})
            fig.update_traces(textposition="inside", textinfo="percent+label", marker_line_width=0)
            st.plotly_chart(estilo(fig, 380), config=SEM_BARRA, **LARGURA)

# --- ABA 3: ADMIN ---
if tab3 is not None:
    with tab3:
        secao("💰 Lançamento de dízimos", "o status vira “Sim” quando o valor é maior que zero")
        a1, a2 = st.columns([1, 1.3])
        mes_adm = a1.selectbox("Mês de lançamento", MESES, index=IDX_MES_ATUAL, key="adm_m")
        cat_adm = a2.radio("Filtrar por categoria", ["Jovens", "Adolescentes", "Todos"], horizontal=True,
                           key="cat_adm_fin")

        base_diz = df_diz[df_diz["Mês"] == mes_adm]
        if cat_adm != "Todos":
            base_diz = base_diz[base_diz["Categoria"] == cat_adm]
        base_diz = base_diz.reset_index(drop=True)

        pendentes = base_diz[base_diz["Pago"] != "Sim"]
        grade([
            cartao("Lançado no mês", formatar_brl(base_diz[base_diz["Pago"] == "Sim"]["Valor"].sum()), cor="#34D399"),
            cartao("Com dízimo", f"{len(base_diz) - len(pendentes)} de {len(base_diz)}", cor="#22D3EE"),
            cartao("Sem lançamento", len(pendentes), cor="#FB7185"),
        ])

        with st.form("form_diz"):
            editado_diz = st.data_editor(
                base_diz, hide_index=True, column_order=["Líder", "Categoria", "Valor", "Pago"],
                key=f"ed_diz_{mes_adm}_{cat_adm}_{st.session_state.rev}",
                column_config={"Líder": st.column_config.Column(disabled=True),
                               "Categoria": st.column_config.Column(disabled=True),
                               "Valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f", min_value=0.0),
                               "Pago": st.column_config.Column("Status", disabled=True)},
                **LARGURA)
            if st.form_submit_button("💾 Salvar dízimos"):
                try:
                    mudancas = salvar_dizimos(base_diz, editado_diz)
                except Exception as erro:
                    st.error(f"Não foi possível salvar, nada foi alterado: {erro}")
                else:
                    if mudancas:
                        concluir(f"Dízimos de {mes_adm} salvos ({mudancas} valor(es) alterado(s)).")
                    else:
                        st.info("Nenhum valor foi alterado.")

        if not pendentes.empty:
            with st.expander(f"Ver quem está sem lançamento em {mes_adm} ({len(pendentes)})"):
                st.dataframe(pendentes[["Líder", "Categoria"]].reset_index(drop=True), hide_index=True, **LARGURA)

        secao("👥 Gestão de líderes")
        l1, l2 = st.columns(2)
        with l1:
            with st.form("form_add", clear_on_submit=True):
                st.markdown("**Adicionar líder**")
                nome_novo = st.text_input("Nome")
                cat_nova = st.selectbox("Categoria", CATEGORIAS)
                if st.form_submit_button("➕ Confirmar adição"):
                    nome_novo = nome_novo.strip()
                    if not nome_novo:
                        st.warning("Digite o nome.")
                    else:
                        try:
                            adicionar_lider(nome_novo, cat_nova)
                        except Exception as erro:
                            st.error(f"Não foi possível adicionar: {erro}")
                        else:
                            concluir(f"{nome_novo} adicionado(a) em {cat_nova}.")
        with l2:
            with st.form("form_del"):
                st.markdown("**Remover líder**")
                lider_ex = st.selectbox("Escolher para remover", sorted(df_diz["Líder"].astype(str).unique()))
                confirma = st.checkbox("Confirmo: apagar todos os lançamentos dessa pessoa")
                if st.form_submit_button("🗑️ Excluir permanentemente"):
                    if not confirma:
                        st.warning("Marque a confirmação para excluir.")
                    else:
                        try:
                            remover_lider(lider_ex)
                        except Exception as erro:
                            st.error(f"Não foi possível remover: {erro}")
                        else:
                            concluir(f"{lider_ex} removido(a).")

        secao("💾 Cópia de segurança", "baixa as duas abas como estão na planilha")
        carimbo = AGORA.strftime("%Y-%m-%d")
        b1, b2 = st.columns(2)
        b1.download_button("⬇️ Baixar Dizimos (CSV)", bruto_diz.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{carimbo}_Dizimos.csv", mime="text/csv")
        b2.download_button("⬇️ Baixar Frequencia (CSV)", bruto_freq.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{carimbo}_Frequencia.csv", mime="text/csv")

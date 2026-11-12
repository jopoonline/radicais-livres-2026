import base64
import calendar
import hmac
import os
import urllib.parse
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Radicais Livres", layout="wide", page_icon="⛪")

# --- CONEXÃO GOOGLE SHEETS (igual à versão anterior) ---
conn = st.connection("gsheets", type=GSheetsConnection)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1ptEbNIYh9_vVHJhnYLVoicAZ9REHTuIsBO4c1h7PsIs/edit#gid=0"

# --- CONFIGURAÇÕES ---
ANO_BASE = 2026  # o ano que já está nas abas "Dizimos" e "Frequencia"
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
GRUPOS_DISCIPULADORES = {
    "Jovens": ["André e Larissa", "Lucas e Rosana", "Deric e Nayara"],
    "Adolescentes": ["Giovana", "Gui&La", "Bella", "Pedro"],
}
TODOS_DISCIPULADORES = GRUPOS_DISCIPULADORES["Jovens"] + GRUPOS_DISCIPULADORES["Adolescentes"]
CATEGORIAS = ["Jovens", "Adolescentes"]
TIPOS = ["Célula", "Culto de Jovens"]
NOME_TIPO = {"Célula": "Células", "Culto de Jovens": "Culto"}
INDICADORES = {"ME": "Membros", "FA": "FA", "VI": "Visitantes"}
CORES_IND = {"Membros": "#22D3EE", "FA": "#818CF8", "Visitantes": "#FBBF24"}
CORES_TIPO = {"Célula": "#22D3EE", "Culto de Jovens": "#818CF8"}
COLS_S = [f"S{i}_{ind}" for i in range(1, 6) for ind in INDICADORES]
COLS_DIZIMOS = ["Mês", "Líder", "Categoria", "Valor", "Pago"]
COLS_FREQ = ["Mês", "Discipulador", "Categoria", "Tipo"] + COLS_S

FUSO = ZoneInfo("America/Sao_Paulo")
AGORA = datetime.now(FUSO)
ANOS = list(range(ANO_BASE, max(AGORA.year, ANO_BASE) + 2))


def abas_do_ano(ano):
    """2026 continua nas abas originais; cada ano seguinte ganha um par de abas próprio."""
    if ano == ANO_BASE:
        return "Dizimos", "Frequencia"
    return f"Dizimos_{ano}", f"Frequencia_{ano}"


def sabados_do_mes(ano, idx_mes):
    return [date(ano, idx_mes + 1, sem[calendar.SATURDAY])
            for sem in calendar.monthcalendar(ano, idx_mes + 1) if sem[calendar.SATURDAY]]


def _versao_streamlit():
    try:
        return tuple(int(p) for p in st.__version__.split(".")[:2])
    except Exception:
        return (0, 0)


# Versões novas do Streamlit trocaram use_container_width por width="stretch".
LARGURA = {"width": "stretch"} if _versao_streamlit() >= (1, 52) else {"use_container_width": True}
SEM_BARRA = {"displayModeBar": False}


def senha_admin():
    """A senha fica nos Secrets do app (chave senha_admin), fora do código."""
    try:
        valor = st.secrets["senha_admin"]
        return str(valor) if valor else None
    except Exception:
        return None


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
.hero-marca { display: flex; align-items: center; gap: 18px; }
.hero-logo { height: 76px; width: auto; max-width: 160px; object-fit: contain; border-radius: 14px; }
.hero-emoji { font-size: 46px; line-height: 1; }
.stTabs [role="tablist"] { overflow-x: auto; scrollbar-width: none; }
.stTabs [role="tab"] { white-space: nowrap; flex-shrink: 0; }
</style>
""", unsafe_allow_html=True)

# --- FORMATAÇÃO ---
def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def num(valor, casas=1):
    return f"{valor:.{casas}f}".replace(".", ",")


def pct_txt(parte, total):
    return f"{parte / total * 100:.0f}%" if total else "—"


def cartao(rotulo, valor, detalhe="", cor="#22D3EE", cheio=False):
    classe = "kpi cheio" if cheio else "kpi"
    return (f'<div class="{classe}" style="--cor:{cor}"><div class="kpi-rotulo">{rotulo}</div>'
            f'<div class="kpi-valor">{valor}</div>'
            f'<div class="kpi-detalhe">{detalhe or "&nbsp;"}</div></div>')


def grade(cartoes, minimo=150):
    st.markdown(f'<div class="kpi-grade" style="grid-template-columns:repeat(auto-fit,minmax({minimo}px,1fr))">'
                + "".join(cartoes) + '</div>', unsafe_allow_html=True)


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


def grafico(fig, altura=360):
    st.plotly_chart(estilo(fig, altura), config=SEM_BARRA, **LARGURA)


@st.cache_data(show_spinner=False)
def logo_html():
    """Se existir um arquivo logo.png (ou .jpg/.webp/.svg) ao lado do app, ele entra no cabeçalho."""
    tipos = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp",
             "svg": "image/svg+xml"}
    for ext, mime in tipos.items():
        caminho = f"logo.{ext}"
        if os.path.exists(caminho):
            with open(caminho, "rb") as arq:
                dados = base64.b64encode(arq.read()).decode()
            return f'<img class="hero-logo" alt="Logo" src="data:{mime};base64,{dados}">'
    return '<span class="hero-emoji">⛪</span>'


# --- DADOS ---
class ErroDados(Exception):
    pass


class AnoInexistente(Exception):
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
        if type(erro).__name__ == "WorksheetNotFound":
            raise AnoInexistente(aba) from erro
        raise ErroDados(f"não consegui ler a aba {aba}: {erro}") from erro
    df = df.dropna(how="all")
    df = df[[c for c in df.columns if not (str(c).startswith("Unnamed") and df[c].isna().all())]]
    faltando = [c for c in obrigatorias if c not in df.columns]
    if faltando:
        raise ErroDados(f"a aba {aba} veio sem as colunas: " + ", ".join(faltando))
    if df.empty:
        raise ErroDados(f"a aba {aba} veio vazia")
    return df.reset_index(drop=True)


def ler_dizimos(ano):
    return _ler_aba(abas_do_ano(ano)[0], COLS_DIZIMOS)


def ler_freq(ano):
    return _ler_aba(abas_do_ano(ano)[1], COLS_FREQ)


@st.cache_data(ttl=60, show_spinner="Carregando dados da planilha…")
def carregar_dados(ano):
    return ler_dizimos(ano), ler_freq(ano), datetime.now(FUSO).strftime("%H:%M")


def gravar(aba, df):
    conn.update(spreadsheet=URL_PLANILHA, worksheet=aba, data=df)
    st.cache_data.clear()


def salvar_frequencia(ano, base, editado, colunas):
    """Relê a planilha e grava só as células que mudaram na tela."""
    atual = ler_freq(ano)
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
        gravar(abas_do_ano(ano)[1], atual)
    return mudancas


def salvar_dizimos(ano, base, editado):
    atual = ler_dizimos(ano)
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
        gravar(abas_do_ano(ano)[0], atual)
    return mudancas


def adicionar_lider(ano, nome, categoria):
    diz, freq = ler_dizimos(ano), ler_freq(ano)
    if nome.lower() in diz["Líder"].astype(str).str.strip().str.lower().values:
        raise ErroDados(f"já existe um líder chamado {nome}")
    novas_d = pd.DataFrame([{"Mês": m, "Líder": nome, "Categoria": categoria, "Valor": 0.0, "Pago": "Não"}
                            for m in MESES])
    novas_f = pd.DataFrame([{"Mês": m, "Discipulador": nome, "Categoria": categoria, "Tipo": t,
                             **{c: 0 for c in COLS_S}} for m in MESES for t in TIPOS])
    aba_d, aba_f = abas_do_ano(ano)
    gravar(aba_d, pd.concat([diz, novas_d], ignore_index=True))
    gravar(aba_f, pd.concat([freq, novas_f], ignore_index=True))


def remover_lider(ano, nome):
    diz, freq = ler_dizimos(ano), ler_freq(ano)
    novo_d = diz[diz["Líder"] != nome]
    novo_f = freq[freq["Discipulador"] != nome]
    if novo_d.empty or novo_f.empty:
        raise ErroDados("essa remoção deixaria a planilha vazia; nada foi gravado")
    aba_d, aba_f = abas_do_ano(ano)
    gravar(aba_d, novo_d)
    if len(novo_f) != len(freq):
        gravar(aba_f, novo_f)


def _aba_existe(leitor, ano):
    try:
        leitor(ano)
        return True
    except AnoInexistente:
        return False


def criar_ano(ano):
    """Cria as abas de um ano novo, zeradas, copiando líderes e discipuladores do ano anterior.

    Nunca escreve numa aba que já existe.
    """
    try:
        diz_ant, freq_ant = ler_dizimos(ano - 1), ler_freq(ano - 1)
    except AnoInexistente:
        raise ErroDados(f"crie {ano - 1} antes de {ano}") from None
    aba_d, aba_f = abas_do_ano(ano)
    lideres = diz_ant.drop_duplicates("Líder")[["Líder", "Categoria"]]
    novo_d = pd.DataFrame([{"Mês": m, "Líder": l, "Categoria": c, "Valor": 0.0, "Pago": "Não"}
                           for m in MESES for l, c in lideres.itertuples(index=False)])[COLS_DIZIMOS]
    grupos = freq_ant.drop_duplicates(["Discipulador", "Tipo"])[["Discipulador", "Categoria", "Tipo"]]
    novo_f = pd.DataFrame([{"Mês": m, "Discipulador": d, "Categoria": c, "Tipo": t, **{k: 0 for k in COLS_S}}
                           for m in MESES for d, c, t in grupos.itertuples(index=False)])[COLS_FREQ]
    criadas = []
    planilha = conn.client._open_spreadsheet(spreadsheet=URL_PLANILHA)
    for aba, df, leitor in ((aba_d, novo_d, ler_dizimos), (aba_f, novo_f, ler_freq)):
        if _aba_existe(leitor, ano):
            continue
        planilha.add_worksheet(title=aba, rows=len(df) + 1, cols=len(df.columns))
        gravar(aba, df)
        criadas.append(aba)
    st.cache_data.clear()
    return criadas


def formato_longo(df, sabados):
    longo = df.melt(id_vars=["Mês", "Discipulador", "Categoria", "Tipo"], value_vars=COLS_S,
                    var_name="col", value_name="Valor")
    longo["Semana"] = longo["col"].str[1].astype(int)
    longo["Indicador"] = longo["col"].str[3:]
    n_sab = longo["Mês"].map({m: len(s) for m, s in sabados.items()}).fillna(0)
    return longo[longo["Semana"] <= n_sab].drop(columns="col")


def ordenar_meses(df):
    """Deixa as linhas em ordem de calendário, para as linhas dos gráficos não voltarem para trás."""
    if "Mês" not in df.columns:
        return df
    return (df.assign(_m=df["Mês"].map({m: i for i, m in enumerate(MESES)}))
              .sort_values("_m", kind="stable").drop(columns="_m").reset_index(drop=True))


def resumo(base, mes, tipo):
    """Totais por indicador e quantidade de sábados com lançamento."""
    f = base[(base["Mês"] == mes) & (base["Tipo"] == tipo)]
    por_sabado = f.groupby("Semana")["Valor"].sum()
    totais = f.groupby("Indicador")["Valor"].sum().reindex(list(INDICADORES)).fillna(0)
    return totais, int((por_sabado > 0).sum())


def media_por_sabado(base, chaves):
    """Média de presenças por sábado, contando só os sábados que têm lançamento."""
    por_sab = base.groupby(chaves + ["Semana"], as_index=False)["Valor"].sum()
    por_sab = por_sab[por_sab["Valor"] > 0]
    media = por_sab.groupby(chaves, as_index=False)["Valor"].mean().round(1).rename(columns={"Valor": "Média"})
    return ordenar_meses(media)


def taxa_visitantes(base, chaves):
    """Percentual de visitantes sobre o público total, por grupo."""
    total = base.groupby(chaves)["Valor"].sum()
    visit = base[base["Indicador"] == "VI"].groupby(chaves)["Valor"].sum()
    taxa = (visit / total * 100).where(total > 0).round(1).dropna()
    return ordenar_meses(taxa.reset_index(name="Taxa"))


# --- SIDEBAR (ano e acesso) ---
SENHA = senha_admin()
with st.sidebar:
    ano_padrao = min(max(AGORA.year, ANO_BASE), ANOS[-1])
    ANO = st.selectbox("📆 Ano", ANOS, index=ANOS.index(ano_padrao), key="ano")
    st.markdown("### 🔐 Acesso")
    senha = st.text_input("Senha administrativa", type="password", disabled=SENHA is None)
    is_admin = bool(senha) and SENHA is not None and hmac.compare_digest(senha.encode(), SENHA.encode())
    if SENHA is None:
        st.caption("Admin desativado: defina `senha_admin` nos Secrets do app.")
    elif is_admin:
        st.caption("✅ Modo administrador")
    elif senha:
        st.caption("Senha incorreta.")
    if st.button("🔄 Sincronizar"):
        st.cache_data.clear()
        st.rerun()

SABADOS = {m: sabados_do_mes(ANO, i) for i, m in enumerate(MESES)}
HOJE = AGORA.date()
if ANO == AGORA.year:
    IDX_MES_ATUAL = AGORA.month - 1
else:
    IDX_MES_ATUAL = 11 if ANO < AGORA.year else 0


def rotulo_sab(d):
    return d.strftime("%d/%m")


def cabecalho(chip):
    st.markdown(
        f'<div class="hero"><div class="hero-marca">{logo_html()}<div>'
        f'<div class="hero-kicker">Painel {ANO}</div>'
        '<div class="hero-titulo">Radicais Livres</div>'
        '<div class="hero-sub">Frequência de células e cultos · Dízimos</div></div></div>'
        f'<div class="hero-chip"><span class="ponto"></span>{chip}</div></div>',
        unsafe_allow_html=True)


if "rev" not in st.session_state:
    st.session_state.rev = 0


def concluir(mensagem):
    st.session_state.rev += 1
    st.session_state.aviso = mensagem
    st.rerun()


# --- CARGA ---
try:
    bruto_diz, bruto_freq, hora_carga = carregar_dados(ANO)
except AnoInexistente:
    cabecalho(f"{ANO} ainda não criado")
    if "aviso" in st.session_state:
        st.success(st.session_state.pop("aviso"))
    st.info(f"As abas de {ANO} ainda não existem na planilha. Escolha outro ano na barra lateral"
            + (" ou crie o ano abaixo." if is_admin else ", ou peça ao administrador para criar."))
    if is_admin:
        st.write(f"Isso cria as abas **{abas_do_ano(ANO)[0]}** e **{abas_do_ano(ANO)[1]}**, zeradas, com os mesmos "
                 f"líderes e discipuladores de {ANO - 1}. As abas dos outros anos não são alteradas.")
        if st.button(f"📆 Criar planilhas de {ANO}"):
            try:
                criar_ano(ANO)
            except Exception as erro:
                st.error(f"Não foi possível criar {ANO}: {erro}")
            else:
                concluir(f"Ano {ANO} criado.")
    st.stop()
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
freq_painel = df_freq[df_freq["Discipulador"].isin(TODOS_DISCIPULADORES)]
longo_todos = formato_longo(freq_painel, SABADOS)


def filtra_cat(df, categoria):
    return df if categoria == "Todos" else df[df["Categoria"] == categoria]


cabecalho(f"Planilha lida às {hora_carga}")
if "aviso" in st.session_state:
    st.success(st.session_state.pop("aviso"))

nomes_abas = ["🏠 Visão geral", "📊 Frequência", "📅 Ano", "👤 Discipulador", "💰 Finanças"]
if is_admin:
    nomes_abas.append("⚙️ Admin")
abas = st.tabs(nomes_abas)
tab_geral, tab_freq, tab_ano, tab_disc, tab_fin = abas[:5]
tab_admin = abas[5] if is_admin else None

# --- ABA: VISÃO GERAL ---
with tab_geral:
    v1, v2 = st.columns([1, 1.7])
    mes_vg = v1.selectbox("📅 Mês", MESES, index=IDX_MES_ATUAL, key="vg_mes")
    cat_vg = v2.radio("📂 Categoria", ["Todos", "Jovens", "Adolescentes"], horizontal=True, key="vg_cat")
    sab_vg = SABADOS[mes_vg]
    longo_vg = filtra_cat(longo_todos, cat_vg)
    tot_cel, n_cel = resumo(longo_vg, mes_vg, "Célula")
    tot_cul, n_cul = resumo(longo_vg, mes_vg, "Culto de Jovens")
    publico = int(tot_cel.sum() + tot_cul.sum())
    visitantes = int(tot_cel["VI"] + tot_cul["VI"])
    diz_vg = filtra_cat(df_diz, cat_vg)
    diz_mes = diz_vg[diz_vg["Mês"] == mes_vg]
    diz_pagos = diz_mes[diz_mes["Pago"] == "Sim"]
    total_diz = diz_pagos["Valor"].sum()

    grade([
        cartao("Presenças em células", int(tot_cel.sum()),
               f"média {num(tot_cel.sum() / n_cel)} por sábado" if n_cel else "sem lançamento", cor="#22D3EE"),
        cartao("Presenças no culto", int(tot_cul.sum()),
               f"média {num(tot_cul.sum() / n_cul)} por sábado" if n_cul else "sem lançamento", cor="#818CF8"),
        cartao("Visitantes", visitantes, f"{pct_txt(visitantes, publico)} do público", cor="#FBBF24"),
        cartao("Dízimos no mês", formatar_brl(total_diz), cor="#34D399", cheio=True),
        cartao("Líderes com dízimo", f"{len(diz_pagos)} de {len(diz_mes)}",
               f"{len(diz_mes) - len(diz_pagos)} sem lançamento", cor="#FB7185"),
    ], minimo=230)

    do_mes_vg = longo_vg[longo_vg["Mês"] == mes_vg]
    o1, o2 = st.columns([1.5, 1])
    with o1:
        secao(f"Público por sábado · {mes_vg}")
        if do_mes_vg["Valor"].sum() == 0:
            st.info(f"Ainda não há lançamentos de frequência em {mes_vg}.")
        else:
            ps = do_mes_vg.groupby(["Semana", "Tipo"], as_index=False)["Valor"].sum()
            ps["Sábado"] = ps["Semana"].map(lambda i: rotulo_sab(sab_vg[i - 1]))
            fig = px.bar(ps, x="Sábado", y="Valor", color="Tipo", barmode="group", text="Valor",
                         color_discrete_map=CORES_TIPO,
                         category_orders={"Sábado": [rotulo_sab(d) for d in sab_vg], "Tipo": TIPOS})
            fig.update_xaxes(type="category")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            grafico(fig, 340)
    with o2:
        secao("Falta lançar", "sábados que já passaram")
        passados = [i + 1 for i, d in enumerate(sab_vg) if d <= HOJE]
        faltas = []
        if passados:
            soma = do_mes_vg[do_mes_vg["Semana"].isin(passados)].groupby(
                ["Discipulador", "Tipo", "Semana"], as_index=False)["Valor"].sum()
            for (disc, tipo), grupo in soma[soma["Valor"] == 0].groupby(["Discipulador", "Tipo"]):
                faltas.append({"Discipulador": disc, "Tipo": NOME_TIPO[tipo],
                               "Sábados": ", ".join(rotulo_sab(sab_vg[i - 1]) for i in sorted(grupo["Semana"]))})
        if faltas:
            st.dataframe(pd.DataFrame(faltas), hide_index=True, **LARGURA)
        elif passados:
            st.success("Frequência em dia: todos os sábados passados têm lançamento.")
        else:
            st.info("Nenhum sábado deste mês passou ainda.")
        st.caption(f"Dízimos: {len(diz_mes) - len(diz_pagos)} líder(es) sem lançamento em {mes_vg}.")

    # Resumo pronto para o WhatsApp
    linhas = [f"*Radicais Livres · {mes_vg}/{ANO}*" + ("" if cat_vg == "Todos" else f" ({cat_vg})"), ""]
    for tipo, emoji, tot, n in (("Célula", "🏠", tot_cel, n_cel), ("Culto de Jovens", "🎸", tot_cul, n_cul)):
        if n:
            linhas.append(f"{emoji} *{NOME_TIPO[tipo]}*: {int(tot.sum())} presenças em {n} sábado(s), "
                          f"média {num(tot.sum() / n)}")
            linhas.append(f"   Membros {int(tot['ME'])} · FA {int(tot['FA'])} · Visitantes {int(tot['VI'])}")
        else:
            linhas.append(f"{emoji} *{NOME_TIPO[tipo]}*: sem lançamento")
    if publico:
        linhas.append(f"🙋 *Visitantes*: {visitantes} ({pct_txt(visitantes, publico)} do público)")
        por_d = do_mes_vg.groupby("Discipulador")["Valor"].sum().sort_values(ascending=False)
        linhas += ["", "*Por discipulador*"] + [f"• {d}: {int(v)}" for d, v in por_d.items()]
    linhas += ["", f"💰 *Dízimos*: {formatar_brl(total_diz)} · {len(diz_pagos)} de {len(diz_mes)} líderes"]
    texto_resumo = "\n".join(linhas)
    with st.expander("📲 Resumo do mês para o WhatsApp"):
        st.code(texto_resumo, language=None)
        st.caption("Use o ícone de copiar no canto do quadro, ou abra direto no WhatsApp.")
        if hasattr(st, "link_button"):
            st.link_button("Abrir no WhatsApp", "https://wa.me/?text=" + urllib.parse.quote(texto_resumo))

# --- ABA: FREQUÊNCIA ---
with tab_freq:
    f1, f2, f3 = st.columns([1, 1.7, 2])
    mes_sel = f1.selectbox("📅 Mês", MESES, index=IDX_MES_ATUAL, key="f_mes")
    cat_freq = f2.radio("📂 Categoria", ["Jovens", "Adolescentes", "Todos"], horizontal=True, key="cat_freq")

    idx_mes = MESES.index(mes_sel)
    sab_datas = SABADOS[mes_sel]
    sabados = [rotulo_sab(d) for d in sab_datas]
    n_sab = len(sabados)
    mes_ant = MESES[idx_mes - 1] if idx_mes > 0 else None

    df_base = filtra_cat(freq_painel[freq_painel["Mês"] == mes_sel], cat_freq)
    nomes = sorted(df_base["Discipulador"].unique())
    selecao = f3.multiselect("👥 Discipuladores", nomes, default=nomes, key=f"f_disc_{cat_freq}")

    if not selecao:
        st.info("Selecione pelo menos um discipulador para ver os dados.")
    else:
        longo = filtra_cat(longo_todos[longo_todos["Discipulador"].isin(selecao)], cat_freq)

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
            st.info(f"Ainda não há lançamentos em {mes_sel}. Use o lançamento no fim da página.")
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
            grafico(fig, 380)

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
                grafico(fig, 360)
            with g2:
                secao("Por discipulador", f"total em {mes_sel}")
                por_disc = do_mes.groupby(["Discipulador", "Indicador"], as_index=False)["Valor"].sum()
                por_disc["Indicador"] = por_disc["Indicador"].map(INDICADORES)
                ordem_disc = por_disc.groupby("Discipulador")["Valor"].sum().sort_values(ascending=False).index.tolist()
                fig = px.bar(por_disc, y="Discipulador", x="Valor", color="Indicador", orientation="h",
                             barmode="stack", text="Valor", color_discrete_map=CORES_IND,
                             category_orders={"Discipulador": ordem_disc, "Indicador": list(INDICADORES.values())})
                fig.update_traces(marker_line_width=0, insidetextanchor="middle")
                grafico(fig, 360)

            secao("Taxa de visitantes", "visitantes ÷ público total de cada sábado")
            taxa = taxa_visitantes(do_mes, ["Semana", "Tipo"])
            taxa["Sábado"] = taxa["Semana"].map(lambda i: sabados[i - 1])
            taxa["Rótulo"] = taxa["Taxa"].map(lambda v: f"{v:.0f}%")
            fig = px.line(taxa, x="Sábado", y="Taxa", color="Tipo", markers=True, text="Rótulo",
                          color_discrete_map=CORES_TIPO, category_orders={"Sábado": sabados, "Tipo": TIPOS})
            fig.update_xaxes(type="category")
            fig.update_yaxes(ticksuffix="%", rangemode="tozero")
            fig.update_traces(line_width=3, marker_size=9, cliponaxis=False)
            fig.for_each_trace(lambda t: t.update(textposition="bottom center" if t.name == TIPOS[1] else "top center"))
            grafico(fig, 300)

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

        if not modo_edicao:
            st.dataframe(df_view, column_config=conf, column_order=ordem, hide_index=True, **LARGURA)
        else:
            modo = st.radio("Como lançar", ["Rápido (um sábado)", "Tabela completa"], horizontal=True, key="modo_lanc")
            if modo.startswith("Rápido"):
                passados = [i for i, d in enumerate(sab_datas) if d <= HOJE]
                q1, q2, q3 = st.columns(3)
                disc_q = q1.selectbox("Discipulador", nomes, key=f"q_disc_{cat_freq}")
                sab_q = q2.selectbox("Sábado", sabados, index=passados[-1] if passados else 0, key=f"q_sab_{mes_sel}")
                tipo_q = q3.radio("Tipo", TIPOS, horizontal=True, key="q_tipo")
                linha = df_base[(df_base["Discipulador"] == disc_q) & (df_base["Tipo"] == tipo_q)].reset_index(drop=True)
                if len(linha) != 1:
                    st.warning("Não encontrei a linha desse discipulador na planilha para este mês.")
                else:
                    s = sabados.index(sab_q) + 1
                    sufixo = f"{mes_sel}_{disc_q}_{tipo_q}_{s}_{st.session_state.rev}"
                    with st.form("form_rapido"):
                        st.markdown(f"**{disc_q} · {NOME_TIPO[tipo_q]} · {sab_q}**")
                        n1, n2, n3 = st.columns(3)
                        v_me = n1.number_input("Membros", min_value=0, step=1, value=int(linha.loc[0, f"S{s}_ME"]),
                                               key=f"q_me_{sufixo}")
                        v_fa = n2.number_input("FA", min_value=0, step=1, value=int(linha.loc[0, f"S{s}_FA"]),
                                               key=f"q_fa_{sufixo}")
                        v_vi = n3.number_input("Visitantes", min_value=0, step=1, value=int(linha.loc[0, f"S{s}_VI"]),
                                               key=f"q_vi_{sufixo}")
                        if st.form_submit_button("💾 Salvar"):
                            novo = linha.copy()
                            novo.loc[0, [f"S{s}_ME", f"S{s}_FA", f"S{s}_VI"]] = [v_me, v_fa, v_vi]
                            try:
                                mudancas = salvar_frequencia(ANO, linha, novo, [f"S{s}_ME", f"S{s}_FA", f"S{s}_VI"])
                            except Exception as erro:
                                st.error(f"Não foi possível salvar, nada foi alterado: {erro}")
                            else:
                                if mudancas:
                                    concluir(f"Salvo: {disc_q}, {NOME_TIPO[tipo_q]}, {sab_q}.")
                                else:
                                    st.info("Nenhum valor foi alterado.")
            else:
                with st.form("form_freq"):
                    chave = f"ed_freq_{mes_sel}_{cat_freq}_{'|'.join(selecao)}_{st.session_state.rev}"
                    editado = st.data_editor(df_view, column_config=conf, column_order=ordem, hide_index=True,
                                             key=chave, **LARGURA)
                    if st.form_submit_button("💾 Salvar frequência"):
                        try:
                            mudancas = salvar_frequencia(ANO, df_view, editado, visiveis)
                        except Exception as erro:
                            st.error(f"Não foi possível salvar, nada foi alterado: {erro}")
                        else:
                            if mudancas:
                                concluir(f"Frequência de {mes_sel} salva ({mudancas} valor(es) alterado(s)).")
                            else:
                                st.info("Nenhum valor foi alterado.")

# --- ABA: ANO ---
with tab_ano:
    y1, y2, y3 = st.columns([1.5, 1.2, 1])
    cat_ano = y1.radio("📂 Categoria", ["Todos", "Jovens", "Adolescentes"], horizontal=True, key="ano_cat")
    tipo_ano = y2.radio("Tipo", TIPOS, horizontal=True, key="ano_tipo", format_func=lambda t: NOME_TIPO[t])
    ind_ano = y3.selectbox("Indicador", ["Total"] + list(INDICADORES.values()), key="ano_ind")

    base_ano = filtra_cat(longo_todos, cat_ano)
    base_ano = base_ano[base_ano["Tipo"] == tipo_ano]
    por_sab_ano = base_ano.groupby(["Mês", "Semana"])["Valor"].sum()
    lancados = int((por_sab_ano > 0).sum())
    total_ano = int(base_ano["Valor"].sum())
    visit_ano = int(base_ano[base_ano["Indicador"] == "VI"]["Valor"].sum())
    grade([
        cartao("Sábados com lançamento", f"{lancados} de {sum(len(s) for s in SABADOS.values())}", cor="#22D3EE"),
        cartao("Média por sábado", num(total_ano / lancados) if lancados else "—", "público total", cor="#818CF8"),
        cartao("Visitantes no ano", visit_ano, cor="#FBBF24"),
        cartao("Taxa de visitantes", pct_txt(visit_ano, total_ano), "do público do ano", cor="#34D399"),
    ])

    secao(f"Mapa do ano · {NOME_TIPO[tipo_ano]}", f"{ind_ano.lower()} em cada sábado de {ANO}")
    alvo = base_ano if ind_ano == "Total" else base_ano[base_ano["Indicador"].map(INDICADORES) == ind_ano]
    matriz = (alvo.groupby(["Mês", "Semana"])["Valor"].sum().unstack("Semana")
              .reindex(index=MESES, columns=range(1, 6)))
    datas = [[rotulo_sab(SABADOS[m][i]) if i < len(SABADOS[m]) else "" for i in range(5)] for m in MESES]
    matriz = matriz.astype(float)
    for li, m in enumerate(MESES):
        for i in range(5):
            if i >= len(SABADOS[m]):
                matriz.iloc[li, i] = None
    fig = px.imshow(matriz.values.astype(float), x=[f"{i}º sábado" for i in range(1, 6)], y=MESES, aspect="auto",
                    color_continuous_scale=[[0, "#141B30"], [0.5, "#1D6FA5"], [1, "#22D3EE"]])
    fig.update_traces(customdata=datas, texttemplate="%{z:.0f}", xgap=4, ygap=4,
                      hovertemplate="%{customdata}: %{z:.0f}<extra></extra>")
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(side="top")
    grafico(fig, 520)

    secao("Taxa de visitantes por mês", f"{NOME_TIPO[tipo_ano]}")
    taxa_ano = taxa_visitantes(base_ano, ["Mês"])
    if taxa_ano.empty:
        st.info("Sem lançamentos para calcular.")
    else:
        taxa_ano["Rótulo"] = taxa_ano["Taxa"].map(lambda v: f"{v:.0f}%")
        taxa_ano["Mês curto"] = taxa_ano["Mês"].str[:3]
        fig = px.line(taxa_ano, x="Mês curto", y="Taxa", markers=True, text="Rótulo",
                      category_orders={"Mês curto": [m[:3] for m in MESES]})
        fig.update_xaxes(type="category")
        fig.update_yaxes(ticksuffix="%", rangemode="tozero")
        fig.update_traces(line_color="#FBBF24", line_width=3, marker_size=9, textposition="top center",
                          cliponaxis=False)
        grafico(fig, 300)

# --- ABA: DISCIPULADOR ---
with tab_disc:
    presentes = [d for d in TODOS_DISCIPULADORES if d in set(freq_painel["Discipulador"])]
    if not presentes:
        st.info("Nenhum discipulador encontrado na planilha.")
    else:
        disc = st.selectbox("👤 Discipulador", presentes, key="disc_sel")
        base_d = longo_todos[longo_todos["Discipulador"] == disc]
        categoria_d = base_d["Categoria"].iloc[0] if len(base_d) else ""
        st.markdown(f'<div class="painel-titulo">{disc}<small>{categoria_d} · {ANO}</small></div>',
                    unsafe_allow_html=True)
        itens = []
        for tipo, cor in (("Célula", "#22D3EE"), ("Culto de Jovens", "#818CF8")):
            bt = base_d[base_d["Tipo"] == tipo]
            n = int((bt.groupby(["Mês", "Semana"])["Valor"].sum() > 0).sum())
            total = int(bt["Valor"].sum())
            itens.append(cartao(f"{NOME_TIPO[tipo]} · média por sábado", num(total / n) if n else "—",
                                f"{n} sábado(s) lançado(s)", cor=cor))
        visit_d = int(base_d[base_d["Indicador"] == "VI"]["Valor"].sum())
        itens.append(cartao("Visitantes no ano", visit_d, cor="#FBBF24"))
        itens.append(cartao("Taxa de visitantes", pct_txt(visit_d, int(base_d["Valor"].sum())), cor="#34D399"))
        grade(itens)

        if base_d["Valor"].sum() == 0:
            st.info(f"{disc} ainda não tem lançamentos em {ANO}.")
        else:
            secao("Evolução no ano", "média de presenças por sábado lançado")
            evo = media_por_sabado(base_d, ["Mês", "Tipo"])
            evo["Mês curto"] = evo["Mês"].str[:3]
            fig = px.line(evo, x="Mês curto", y="Média", color="Tipo", markers=True, text="Média",
                          color_discrete_map=CORES_TIPO,
                          category_orders={"Mês curto": [m[:3] for m in MESES], "Tipo": TIPOS})
            fig.update_xaxes(type="category")
            fig.update_yaxes(rangemode="tozero")
            fig.update_traces(line_width=3, marker_size=9, cliponaxis=False)
            fig.for_each_trace(lambda t: t.update(textposition="bottom center" if t.name == TIPOS[1] else "top center"))
            grafico(fig, 340)

            secao("Composição por mês", "membros, FA e visitantes")
            comp = base_d.groupby(["Mês", "Tipo", "Indicador"], as_index=False)["Valor"].sum()
            comp["Indicador"] = comp["Indicador"].map(INDICADORES)
            comp["Mês curto"] = comp["Mês"].str[:3]
            fig = px.bar(comp, x="Mês curto", y="Valor", color="Indicador", barmode="stack", facet_col="Tipo",
                         color_discrete_map=CORES_IND,
                         category_orders={"Mês curto": [m[:3] for m in MESES], "Tipo": TIPOS,
                                          "Indicador": list(INDICADORES.values())})
            fig.update_xaxes(type="category")
            fig.update_traces(marker_line_width=0)
            grafico(fig, 360)

# --- ABA: FINANÇAS ---
with tab_fin:
    c1, c2 = st.columns([1.3, 1])
    cat_fin = c1.radio("🔍 Ver finanças de", ["Todos", "Jovens", "Adolescentes"], horizontal=True, key="cat_fin")
    mes_fin = c2.selectbox("📅 Mês", MESES, index=IDX_MES_ATUAL, key="mes_fin_stat")
    idx_fin = MESES.index(mes_fin)

    df_fin = filtra_cat(df_diz, cat_fin)
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
                          cliponaxis=False,
                          marker=dict(size=[13 if m == mes_fin else 7 for m in evol["Mês"]],
                                      color=["#FFFFFF" if m == mes_fin else "#22D3EE" for m in evol["Mês"]]),
                          hovertemplate="%{x}: %{text}<extra></extra>")
        fig.update_xaxes(type="category")
        fig.update_yaxes(rangemode="tozero")
        grafico(fig, 380)
    with g2:
        secao(f"Status · {mes_fin}")
        if df_mes.empty:
            st.info("Sem líderes nesse filtro.")
        else:
            fig = px.pie(df_mes, names="Pago", color="Pago", hole=0.64,
                         color_discrete_map={"Sim": "#22D3EE", "Não": "#FB7185"},
                         category_orders={"Pago": ["Sim", "Não"]})
            fig.update_traces(textposition="inside", textinfo="percent+label", marker_line_width=0)
            grafico(fig, 380)

# --- ABA: ADMIN ---
if tab_admin is not None:
    with tab_admin:
        secao("💰 Lançamento de dízimos", "o status vira “Sim” quando o valor é maior que zero")
        a1, a2 = st.columns([1, 1.3])
        mes_adm = a1.selectbox("Mês de lançamento", MESES, index=IDX_MES_ATUAL, key="adm_m")
        cat_adm = a2.radio("Filtrar por categoria", ["Jovens", "Adolescentes", "Todos"], horizontal=True,
                           key="cat_adm_fin")

        base_diz = filtra_cat(df_diz[df_diz["Mês"] == mes_adm], cat_adm).reset_index(drop=True)
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
                    mudancas = salvar_dizimos(ANO, base_diz, editado_diz)
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

        secao("👥 Gestão de líderes", f"vale para {ANO}")
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
                            adicionar_lider(ANO, nome_novo, cat_nova)
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
                            remover_lider(ANO, lider_ex)
                        except Exception as erro:
                            st.error(f"Não foi possível remover: {erro}")
                        else:
                            concluir(f"{lider_ex} removido(a).")

        secao("📆 Próximo ano", f"prepara {ANO + 1} sem mexer em {ANO}")
        st.write(f"Cria as abas **{abas_do_ano(ANO + 1)[0]}** e **{abas_do_ano(ANO + 1)[1]}**, zeradas, com os "
                 f"líderes e discipuladores de {ANO}. Se elas já existirem, nada é alterado.")
        if st.button(f"📆 Criar planilhas de {ANO + 1}"):
            try:
                criadas = criar_ano(ANO + 1)
            except Exception as erro:
                st.error(f"Não foi possível criar {ANO + 1}: {erro}")
            else:
                if criadas:
                    concluir(f"Ano {ANO + 1} criado. Escolha o ano na barra lateral para abrir.")
                else:
                    st.info(f"{ANO + 1} já existe na planilha.")

        secao("💾 Cópia de segurança", f"baixa as duas abas de {ANO} como estão na planilha")
        carimbo = AGORA.strftime("%Y-%m-%d")
        b1, b2 = st.columns(2)
        b1.download_button("⬇️ Baixar Dizimos (CSV)", bruto_diz.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{carimbo}_{abas_do_ano(ANO)[0]}.csv", mime="text/csv")
        b2.download_button("⬇️ Baixar Frequencia (CSV)", bruto_freq.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{carimbo}_{abas_do_ano(ANO)[1]}.csv", mime="text/csv")

##################################
# Agente Economico De IA v2      #
# Version Streamlit              #
# (FRED + Frankfurter)           #
##################################

# Importacion para el ambiente
from dotenv import load_dotenv

# Importacion para el LLM
from groq import Groq

# Importacion para el manejo de sistema y formato JSON
import os
import json

# Importacion para el manejo de fechas y zonas horarias
from datetime import datetime
from zoneinfo import ZoneInfo

# Importacion para la interfaz y las graficas
import streamlit as st
import plotly.graph_objects as go

# Importacion de herramientas y memoria propias
from intermediate_tools_v2 import IntermediateTools
from memoria_v2 import AlmacenLocal, MemoriaChat


# =========================
# CONFIGURACION
# =========================

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

now = datetime.now(ZoneInfo("America/Guatemala"))

MODELO = "openai/gpt-oss-120b"
LIMITE_RECIENTES = 10      # mensajes completos que se mandan al modelo
MAX_ITERACIONES = 6        # tope de seguridad para el ciclo de herramientas

tools = IntermediateTools()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
almacen = AlmacenLocal(os.path.join(BASE_DIR, "historial"))


# =========================
# IDENTIDAD Y ESTILO
# =========================

APP_NAME = "Fedra"
APP_TAGLINE = "Tu agente de la Reserva Federal, tasas y tipos de cambio"
AUTORA = "Renata"
CURSO = "Data Analytics · Universidad Rafael Landívar"

FONDO = "#FFF7FA"       # fondo de la app (rosa muy claro)
PANEL = "#FCEAF1"       # sidebar
TARJETA = "#FFFFFF"     # tarjetas y entrada de texto
BORDE = "#F4D3E1"       # bordes suaves
ROSA = "#E5608F"        # acento principal
ROSA_CLARO = "#F9D3E2"
LAVANDA = "#A98BDB"     # acento secundario
MENTA = "#6CC3A0"       # sube
MALVA = "#5A3550"       # titulos
TEXTO = "#6B4A5F"       # texto principal
SUAVE = "#A88799"       # texto secundario

AVATAR_AGENTE = "🌸"
AVATAR_USUARIA = "🎀"

st.set_page_config(page_title=APP_NAME, page_icon="🌸", layout="centered")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;1,500;1,600&family=DM+Mono:wght@400;500&display=swap');

:root {{ color-scheme: light; }}
html, body, .stApp, .stMarkdown, button, input, textarea {{
    font-family: 'Quicksand', sans-serif !important;
}}
.stApp {{
    background: radial-gradient(circle at 15% 0%, #FFE6EF 0%, {FONDO} 38%),
                radial-gradient(circle at 100% 100%, #F1E8FF 0%, {FONDO} 45%);
    background-blend-mode: multiply;
    color: {TEXTO};
}}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {{ display: none !important; }}
.block-container {{ max-width: 780px; padding-top: 2.2rem; padding-bottom: 8rem; }}

/* Mensajes */
[data-testid="stChatMessage"] {{
    background: {TARJETA}; border: 1px solid {BORDE}; border-radius: 22px;
    padding: 0.9rem 1.1rem; margin: 0.7rem 0;
    box-shadow: 0 4px 18px rgba(229, 96, 143, 0.07);
}}
[data-testid="stChatMessage"]:has(.msg-usuaria) {{
    background: linear-gradient(135deg, #FFE3EE 0%, #F6E9FF 100%); border: none;
}}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {{
    color: {TEXTO}; line-height: 1.7; font-size: 1rem; font-weight: 500;
}}
[data-testid="stChatMessage"] strong {{ color: {MALVA}; }}
[data-testid="stChatMessage"] table {{ border-radius: 12px; overflow: hidden; font-size: 0.9rem; }}
[data-testid="stChatMessage"] th {{ background: {PANEL}; color: {MALVA}; }}
code {{ font-family: 'DM Mono', monospace !important; background: {PANEL} !important; color: {MALVA} !important; }}

/* Entrada de chat */
[data-testid="stBottom"], [data-testid="stBottom"] > div {{ background: transparent !important; }}
[data-testid="stChatInput"], [data-testid="stChatInput"] > div, [data-testid="stChatInput"] div[data-baseweb] {{
    background: {TARJETA} !important;
}}
[data-testid="stChatInput"] {{
    border: 1.5px solid {ROSA_CLARO} !important; border-radius: 999px !important;
    box-shadow: 0 6px 22px rgba(229, 96, 143, 0.13);
}}
[data-testid="stChatInput"]:focus-within {{ border-color: {ROSA} !important; }}
[data-testid="stChatInput"] textarea {{
    color: {MALVA} !important; -webkit-text-fill-color: {MALVA} !important; background: transparent !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{ color: {SUAVE} !important; -webkit-text-fill-color: {SUAVE} !important; }}
[data-testid="stChatInputSubmitButton"] {{ background: {ROSA} !important; border-radius: 999px !important; }}
[data-testid="stChatInputSubmitButton"] svg {{ fill: #FFFFFF !important; color: #FFFFFF !important; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background: {PANEL}; border-right: 1px solid {BORDE}; }}
[data-testid="stSidebar"] * {{ color: {TEXTO}; }}
.marca {{ font-family: 'Playfair Display', serif; font-style: italic; font-size: 1.9rem;
          font-weight: 600; color: {ROSA} !important; margin: 0 0 0.1rem 0.2rem; }}
.marca-sub {{ font-size: 0.8rem; color: {SUAVE} !important; margin: 0 0 1.1rem 0.25rem; }}
.titulo-lateral {{ font-size: 0.74rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
                   color: {SUAVE} !important; margin: 1.4rem 0 0.4rem 0.3rem; }}
.pie {{ margin-top: 2rem; padding-top: 0.9rem; border-top: 1px dashed {ROSA_CLARO};
        font-size: 0.8rem; color: {SUAVE} !important; line-height: 1.65; }}
.pie b {{ color: {MALVA} !important; }}

/* Botones */
.stButton > button {{
    background: {TARJETA} !important; color: {TEXTO} !important; border: 1.5px solid {BORDE} !important;
    border-radius: 999px !important; font-weight: 600; padding: 0.55rem 1rem;
    transition: all .15s ease;
}}
.stButton > button p {{ color: {TEXTO} !important; font-weight: 600; }}
.stButton > button:hover {{ border-color: {ROSA} !important; background: #FFF0F6 !important; transform: translateY(-1px); }}
.stButton > button:hover p {{ color: {ROSA} !important; }}
[data-testid="stSidebar"] .stButton > button {{ border: none !important; background: transparent !important;
    justify-content: flex-start !important; border-radius: 14px !important; padding: 0.45rem 0.7rem; }}
[data-testid="stSidebar"] .stButton > button div {{ justify-content: flex-start !important; width: 100%; }}
[data-testid="stSidebar"] .stButton > button p {{ text-align: left; overflow: hidden; text-overflow: ellipsis;
    white-space: nowrap; font-weight: 500; }}
[data-testid="stSidebar"] .stButton > button:hover {{ background: #F9DCE8 !important; transform: none; }}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {{ background: {TARJETA} !important;
    box-shadow: 0 2px 10px rgba(229, 96, 143, 0.12); }}
[data-testid="stSidebar"] .stButton > button[kind="primary"] p,
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] p {{ color: {ROSA} !important; font-weight: 700; }}
.boton-nuevo .stButton > button, [data-testid="stSidebar"] .st-key-btn_nuevo button {{
    background: {ROSA} !important; justify-content: center !important; border-radius: 999px !important;
    box-shadow: 0 6px 16px rgba(229, 96, 143, 0.3);
}}
[data-testid="stSidebar"] .st-key-btn_nuevo button p {{ color: #FFFFFF !important; text-align: center; font-weight: 700; }}
[data-testid="stSidebar"] .st-key-btn_nuevo button div {{ justify-content: center !important; }}
[data-testid="stSidebar"] .st-key-btn_nuevo button:hover {{ background: #D94C7E !important; }}

[data-testid="stExpander"] {{ border: 1px solid {BORDE}; border-radius: 16px; background: {TARJETA}; }}
[data-testid="stExpander"] summary, [data-testid="stExpander"] details {{ background: {TARJETA} !important; color: {TEXTO} !important; }}
[data-testid="stPlotlyChart"] {{ background: {TARJETA}; border-radius: 18px; padding: 0.4rem 0.2rem 0 0.2rem;
    border: 1px solid {BORDE}; margin: 0.6rem 0; }}

/* Portada */
.portada {{ text-align: center; margin: 9vh 0 2rem 0; }}
.portada .flor {{ font-size: 2.6rem; }}
.portada .nombre {{ font-family: 'Playfair Display', serif; font-style: italic; font-size: 3.3rem;
    font-weight: 600; color: {ROSA}; line-height: 1.1; }}
.portada .sub {{ color: {TEXTO}; margin-top: 0.5rem; font-size: 1.05rem; font-weight: 500; }}
.portada .chips {{ margin-top: 1rem; }}
.portada .chip {{ display: inline-block; background: {TARJETA}; border: 1px solid {BORDE}; color: {SUAVE};
    border-radius: 999px; padding: 0.2rem 0.75rem; margin: 0.15rem; font-size: 0.8rem; font-weight: 600; }}

/* Tarjetas de resultados */
.tarjetas {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.6rem; margin: 0.7rem 0; }}
.tarjeta {{ background: linear-gradient(160deg, #FFFFFF 0%, #FFF3F8 100%); border: 1px solid {BORDE};
    border-radius: 18px; padding: 0.75rem 0.9rem; }}
.tarjeta .et {{ font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: {SUAVE}; }}
.tarjeta .val {{ font-family: 'DM Mono', monospace; font-size: 1.2rem; color: {MALVA}; margin-top: 0.15rem; }}
.tarjeta-titulo {{ font-family: 'Playfair Display', serif; font-style: italic; color: {MALVA};
    font-size: 1.05rem; margin: 0.8rem 0 0 0.2rem; }}
.msg-usuaria {{ display: none; }}
[data-testid="stChatMessage"]:has(.msg-usuaria) [data-testid="stElementContainer"]:has(.msg-usuaria) {{ display: none; }}
.nota {{ font-size: 0.8rem; color: {SUAVE}; margin: 0.2rem 0 0 0.2rem; }}
</style>
""", unsafe_allow_html=True)


# =========================
# PROMPT Y HERRAMIENTAS
# =========================

SYSTEM_PROMPT = f"""
Eres Fedra, un Agente Económico especializado en análisis cuantitativo con
enfoque en mercados y política monetaria de Estados Unidos. Hablas en español,
de forma clara, cálida y concisa.

Fecha actual (Guatemala): {now.strftime('%Y-%m-%d')}

Tu objetivo es ayudar al usuario a consultar variables económicas y financieras
(tipo de cambio actual, tipo de cambio histórico entre monedas específicas,
series económicas de la Reserva Federal de EE.UU.) y a analizar
estadísticamente esos datos (variación, media, desviación estándar).

Herramientas disponibles:
- consultar_tipo_cambio_api: da el tipo de cambio actual de una moneda respecto
  al resto (moneda obligatoria). Para "¿cuántos quetzales vale 1 dólar?", llamá
  con moneda="USD" y leé rates["GTQ"].
- consultar_tipo_cambio_historico_api: da el tipo de cambio entre dos monedas
  específicas en una fecha dada o "latest" (moneda_origen y moneda_destino
  obligatorias). Solo soporta monedas de referencia del Banco Central Europeo
  (no incluye GTQ). Si el usuario pide GTQ, informale la limitación y usá
  consultar_tipo_cambio_api en su lugar.
- consultar_serie_fred_api: da una serie histórica de un indicador económico
  de EE.UU. desde la Reserva Federal (serie_id, fecha_inicio, fecha_fin en
  formato YYYY-MM-DD, todos obligatorios). Series comunes: FEDFUNDS (tasa de
  fondos federales), DGS10 (bono del Tesoro a 10 años), CPIAUCSL (índice de
  precios al consumidor), UNRATE (desempleo), SP500 (índice S&P 500), VIXCLS
  (índice de volatilidad VIX).
  Si la serie es diaria y el rango es largo, la herramienta devuelve un objeto
  con las llaves "serie" (ya resampleada a mensual) y "nota". En ese caso usá
  los valores de data["serie"] y mencioná brevemente que se resumieron a nivel
  mensual.
- calcular_variacion_porcentual: variación entre periodos consecutivos de una
  lista de valores (valores obligatorio, etiquetas opcional). Usá es_tasa=true
  si la serie ya es una tasa o porcentaje (FEDFUNDS, UNRATE, DGS10);
  es_tasa=false para niveles (SP500, CPIAUCSL, VIXCLS). Pasá las fechas de la
  serie como etiquetas.
- calcular_estadisticas_descriptivas: media, desviación estándar, mínimo,
  máximo y coeficiente de variación de una lista de valores.

Reglas:
- Si el usuario pide un análisis estadístico (variación, volatilidad,
  tendencia), primero llamá a la herramienta que trae los datos y luego, con
  esos valores, a la herramienta de cálculo correspondiente.
- Si solo pide los datos, no llames a las herramientas de cálculo por tu cuenta.
- Las gráficas y tarjetas se muestran solas en la interfaz a partir de los
  resultados de las herramientas; no hace falta dibujar nada.
- Nunca inventes valores: si una herramienta no trae datos suficientes, dilo.
- No des recomendaciones de inversión (comprar/vender); limitate a presentar
  los datos y las métricas calculadas de forma objetiva.
- Nunca llames herramientas que no estén en esta lista.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_tipo_cambio_api",
            "description": (
                "Consulta el tipo de cambio actual de una moneda respecto al resto de monedas. "
                "Se debe enviar como argumento el código de la moneda."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "moneda": {"type": "string", "description": "Código de la moneda base, por ejemplo USD, GTQ"}
                },
                "required": ["moneda"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_tipo_cambio_historico_api",
            "description": (
                "Consulta el tipo de cambio entre dos monedas específicas del Banco Central "
                "Europeo, ya sea el más reciente o en una fecha determinada."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "moneda_origen": {"type": "string", "description": "Código de la moneda de origen, ej. USD"},
                    "moneda_destino": {"type": "string", "description": "Código de la moneda de destino, ej. EUR, MXN"},
                    "fecha": {"type": "string", "description": "Fecha YYYY-MM-DD, o 'latest' para el más reciente"}
                },
                "required": ["moneda_origen", "moneda_destino"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_serie_fred_api",
            "description": (
                "Consulta una serie histórica de un indicador económico de EE.UU. desde la "
                "Reserva Federal (FRED)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "serie_id": {
                        "type": "string",
                        "description": (
                            "Código de la serie en FRED. Ejemplos: FEDFUNDS (tasa de fondos "
                            "federales), DGS10 (bono del Tesoro 10 años), CPIAUCSL (inflación), "
                            "UNRATE (desempleo), SP500 (S&P 500), VIXCLS (índice VIX)"
                        )
                    },
                    "fecha_inicio": {"type": "string", "description": "Fecha inicial en formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha final en formato YYYY-MM-DD"}
                },
                "required": ["serie_id", "fecha_inicio", "fecha_fin"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_variacion_porcentual",
            "description": (
                "Calcula la variación entre periodos consecutivos de una lista de valores "
                "numéricos. Usar después de obtener una serie de datos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "valores": {"type": "array", "items": {"type": "number"}, "description": "Valores en orden cronológico"},
                    "etiquetas": {"type": "array", "items": {"type": "string"}, "description": "Etiquetas (fechas) opcionales"},
                    "es_tasa": {"type": "boolean", "description": "true si la serie ya es un % o tasa, false si son niveles"}
                },
                "required": ["valores"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_estadisticas_descriptivas",
            "description": (
                "Calcula media, desviación estándar, mínimo, máximo y coeficiente de variación "
                "de una lista de valores numéricos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "valores": {"type": "array", "items": {"type": "number"}, "description": "Lista de valores numéricos"}
                },
                "required": ["valores"]
            }
        }
    }
]


def ejecutar_herramienta(name, args):
    if name == "consultar_tipo_cambio_api":
        return tools.consultar_tipo_cambio_api(moneda=args.get("moneda", ""))
    elif name == "consultar_tipo_cambio_historico_api":
        return tools.consultar_tipo_cambio_historico_api(
            moneda_origen=args.get("moneda_origen", ""),
            moneda_destino=args.get("moneda_destino", ""),
            fecha=args.get("fecha", "latest") or "latest"
        )
    elif name == "consultar_serie_fred_api":
        return tools.consultar_serie_fred_api(
            serie_id=args.get("serie_id", ""),
            fecha_inicio=args.get("fecha_inicio", ""),
            fecha_fin=args.get("fecha_fin", "")
        )
    elif name == "calcular_variacion_porcentual":
        return tools.calcular_variacion_porcentual(
            valores=args.get("valores", []),
            etiquetas=args.get("etiquetas"),
            es_tasa=args.get("es_tasa", False)
        )
    elif name == "calcular_estadisticas_descriptivas":
        return tools.calcular_estadisticas_descriptivas(valores=args.get("valores", []))
    print(f"Se intentó llamar a una herramienta desconocida {name}")
    return {"error": f"Herramienta desconocida: {name}"}


# =========================
# VISUALES (graficas y tarjetas)
# =========================
# De cada herramienta se guarda solo lo necesario para dibujar ("visual").
# Asi el chat guardado pesa poco y las graficas se redibujan al abrirlo.

SERIES_FRED = {
    "FEDFUNDS": ("Tasa de fondos federales", "%"),
    "DGS10": ("Bono del Tesoro a 10 años", "%"),
    "DGS2": ("Bono del Tesoro a 2 años", "%"),
    "T10Y2Y": ("Diferencial 10 años – 2 años", "puntos porcentuales"),
    "CPIAUCSL": ("Índice de precios al consumidor", "índice 1982-84 = 100"),
    "UNRATE": ("Tasa de desempleo", "%"),
    "SP500": ("S&P 500", "puntos"),
    "VIXCLS": ("Índice de volatilidad VIX", "puntos"),
    "GDP": ("PIB de EE.UU.", "miles de millones de USD"),
    "M2SL": ("Oferta monetaria M2", "miles de millones de USD"),
}

MONEDAS_DESTACADAS = ["GTQ", "USD", "EUR", "MXN", "GBP", "JPY", "CAD", "CRC"]


def crear_visual(name, args, resultado):
    """Convierte el resultado de una herramienta en un 'visual' (o None)."""
    if isinstance(resultado, str):      # las herramientas devuelven texto cuando hay error
        return None

    if name == "consultar_serie_fred_api":
        serie = resultado["serie"] if isinstance(resultado, dict) else resultado
        if not serie:
            return None
        return {"tipo": "serie_fred", "serie_id": str(args.get("serie_id", "")).upper(),
                "fechas": [p["fecha"] for p in serie], "valores": [p["valor"] for p in serie],
                "resampleada": isinstance(resultado, dict)}

    if name == "calcular_variacion_porcentual" and isinstance(resultado, list) and resultado:
        en_pp = "variacion_puntos_porcentuales" in resultado[0]
        clave = "variacion_puntos_porcentuales" if en_pp else "variacion_pct"
        return {"tipo": "variacion", "en_pp": en_pp,
                "etiquetas": [str(d["hasta"]) for d in resultado],
                "valores": [d.get(clave) for d in resultado]}

    if name == "calcular_estadisticas_descriptivas" and isinstance(resultado, dict):
        return {"tipo": "estadisticas", "datos": resultado}

    if name == "consultar_tipo_cambio_historico_api" and isinstance(resultado, dict):
        tasas = resultado.get("rates", {})
        if not tasas:
            return None
        return {"tipo": "cambio_par", "base": resultado.get("base", args.get("moneda_origen", "")),
                "fecha": resultado.get("date", ""), "tasas": tasas}

    if name == "consultar_tipo_cambio_api" and isinstance(resultado, dict):
        tasas = resultado.get("rates", {})
        base = resultado.get("base_code", str(args.get("moneda", "")).upper())
        elegidas = {m: tasas[m] for m in MONEDAS_DESTACADAS if m in tasas and m != base}
        if not elegidas:
            return None
        fecha = resultado.get("time_last_update_utc", "")[:16]
        return {"tipo": "cambio_actual", "base": base, "fecha": fecha, "tasas": elegidas}

    return None


FUENTE = "Quicksand, sans-serif"
FUENTE_NUM = "DM Mono, monospace"


def estilo_grafica(fig, titulo, subtitulo, altura=340):
    fig.update_layout(
        title=dict(
            text=(f"<span style='font-family:Playfair Display, serif;font-style:italic'>{titulo}</span>"
                  f"<br><span style='font-size:12px;color:{SUAVE}'>{subtitulo}</span>"),
            x=0.02, xanchor="left", y=0.95, yanchor="top",
            font=dict(size=18, color=MALVA, family=FUENTE),
        ),
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=12, r=24, t=78, b=36),
        font=dict(family=FUENTE, color=SUAVE, size=12),
        showlegend=False, hovermode="x",
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=ROSA_CLARO,
                        font=dict(family=FUENTE_NUM, color=MALVA, size=12)),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showline=False, ticks="",
                     tickfont=dict(color=SUAVE))
    fig.update_yaxes(showgrid=True, gridcolor="#F7E3EC", gridwidth=1, zeroline=False,
                     showline=False, tickfont=dict(color=SUAVE, family=FUENTE_NUM, size=11))
    return fig


def grafica_serie_fred(v):
    fechas, valores = v["fechas"], v["valores"]
    nombre, unidad = SERIES_FRED.get(v["serie_id"], (v["serie_id"], ""))
    sufijo = "%" if unidad == "%" else ""
    n = len(valores)
    i_max = max(range(n), key=lambda i: valores[i])
    i_min = min(range(n), key=lambda i: valores[i])
    margen = (valores[i_max] - valores[i_min]) * 0.2 or 1
    piso = valores[i_min] - margen

    fig = go.Figure()
    # Area con degradado: una linea invisible en el piso y la serie rellenando hasta ella
    fig.add_trace(go.Scatter(x=fechas, y=[piso] * n, mode="lines", line=dict(width=0), hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=fechas, y=valores, mode="lines", line=dict(width=2.6, color=ROSA, shape="spline", smoothing=0.6),
        fill="tonexty", fillgradient=dict(type="vertical", colorscale=[[0, "rgba(229,96,143,0)"],
                                                                       [1, "rgba(229,96,143,0.22)"]]),
        hovertemplate="<b>%{y:,.2f}" + sufijo + "</b> · %{x}<extra></extra>",
    ))

    # Puntos destacados: ultimo valor (rosa), maximo y minimo (lavanda)
    destacados = [(n - 1, ROSA, f"{valores[-1]:,.2f}{sufijo}", "middle right")]
    if i_max != n - 1:
        destacados.append((i_max, LAVANDA, f"máx {valores[i_max]:,.2f}{sufijo}", "top center"))
    if i_min not in (n - 1, i_max):
        destacados.append((i_min, LAVANDA, f"mín {valores[i_min]:,.2f}{sufijo}", "bottom center"))
    for i, color, texto, pos in destacados:
        fig.add_trace(go.Scatter(
            x=[fechas[i]], y=[valores[i]], mode="markers+text", text=[texto], textposition=pos,
            marker=dict(size=11, color=color, line=dict(width=3, color="#FFFFFF")),
            textfont=dict(family=FUENTE_NUM, size=12, color=color), hoverinfo="skip", cliponaxis=False,
        ))

    fig.update_yaxes(range=[piso, valores[i_max] + margen], ticksuffix=sufijo)
    fig.update_xaxes(type="date")
    subt = f"{unidad} · {fechas[0]} a {fechas[-1]} · Fuente: FRED"
    if v.get("resampleada"):
        subt += " (mensual)"
    return estilo_grafica(fig, nombre, subt)


def grafica_variacion(v):
    pares = [(e, x) for e, x in zip(v["etiquetas"], v["valores"]) if x is not None]
    if not pares:
        return None
    etiquetas = [p[0].replace("periodo_", "periodo ") for p in pares]
    valores = [p[1] for p in pares]
    unidad = " pp" if v["en_pp"] else "%"
    promedio = sum(valores) / len(valores)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=etiquetas, y=valores,
        marker=dict(color=[MENTA if x >= 0 else ROSA for x in valores], cornerradius=8),
        hovertemplate="<b>%{y:+.2f}" + unidad + "</b> · %{x}<extra></extra>",
    ))
    fig.add_hline(y=0, line_width=1, line_color=BORDE)
    fig.add_hline(y=promedio, line_dash="dot", line_width=1.5, line_color=LAVANDA,
                  annotation_text=f"promedio {promedio:+.2f}{unidad}", annotation_position="top left",
                  annotation_font=dict(family=FUENTE_NUM, size=11, color=LAVANDA))
    fig.update_xaxes(type="category", tickangle=-35 if len(etiquetas) > 8 else 0)
    if not v["en_pp"]:
        fig.update_yaxes(ticksuffix="%")
    subt = ("Cambio en puntos porcentuales" if v["en_pp"] else "Cambio porcentual") + \
           " respecto al periodo anterior · verde sube, rosa baja"
    return estilo_grafica(fig, "Variación entre periodos", subt, altura=320)


def tarjetas_html(titulo, pares, nota=""):
    celdas = "".join(f'<div class="tarjeta"><div class="et">{et}</div><div class="val">{val}</div></div>'
                     for et, val in pares)
    html = f'<div class="tarjeta-titulo">{titulo}</div><div class="tarjetas">{celdas}</div>'
    if nota:
        html += f'<div class="nota">{nota}</div>'
    return html


def numero(x, decimales=2):
    return "—" if x is None else f"{x:,.{decimales}f}"


def mostrar_visual(v, clave):
    tipo = v.get("tipo")
    if tipo == "serie_fred":
        st.plotly_chart(grafica_serie_fred(v), config={"displayModeBar": False}, key=clave)
    elif tipo == "variacion":
        fig = grafica_variacion(v)
        if fig is not None:
            st.plotly_chart(fig, config={"displayModeBar": False}, key=clave)
    elif tipo == "estadisticas":
        d = v["datos"]
        cv = d.get("coeficiente_variacion_pct")
        st.markdown(tarjetas_html("Estadísticas descriptivas ✿", [
            ("Observaciones", d.get("n_observaciones", "—")),
            ("Media", numero(d.get("media"))),
            ("Desv. estándar", numero(d.get("desviacion_estandar"))),
            ("Mínimo", numero(d.get("minimo"))),
            ("Máximo", numero(d.get("maximo"))),
            ("Coef. variación", "—" if cv is None else f"{cv:.2f}%"),
        ], d.get("nota_cv", "")), unsafe_allow_html=True)
    elif tipo == "cambio_par":
        pares = [(f"1 {v['base']} =", f"{numero(t, 4)} {m}") for m, t in v["tasas"].items()]
        st.markdown(tarjetas_html("Tipo de cambio ✿", pares,
                                  f"Banco Central Europeo (Frankfurter) · {v['fecha']}"),
                    unsafe_allow_html=True)
    elif tipo == "cambio_actual":
        pares = [(f"{m} por 1 {v['base']}", numero(t, 4)) for m, t in v["tasas"].items()]
        st.markdown(tarjetas_html(f"1 {v['base']} hoy ✿", pares,
                                  f"open.er-api · actualizado {v['fecha']}"),
                    unsafe_allow_html=True)


# =========================
# LOGICA DEL AGENTE
# =========================

def process_response(client: Groq, memory_messages: list, resumen: str, user_text: str):
    """Devuelve (texto_final, lista_de_visuales)."""
    system_content = SYSTEM_PROMPT
    if resumen:
        system_content += f"\n\nResumen de lo conversado antes en este chat (memoria de largo plazo):\n{resumen}"

    messages = [{"role": "system", "content": system_content}]
    messages.extend(memory_messages)
    messages.append({"role": "user", "content": user_text})

    visuales = []

    for _ in range(MAX_ITERACIONES):
        try:
            resp = client.chat.completions.create(model=MODELO, messages=messages, tools=TOOLS)
        except Exception as e:
            print(f"Error al llamar al modelo: {e}")
            error = str(e).lower()
            if "rate_limit" in error or "429" in error:
                return "⚠️ Groq alcanzó su límite por minuto. Esperá unos segundos y volvé a intentar 💗", visuales
            if "tool_use_failed" in error or "not in request.tools" in error:
                return "⚠️ El modelo intentó usar una herramienta que no existe. Probá reformular la pregunta.", visuales
            return f"⚠️ Ocurrió un error inesperado: {e}", visuales

        msg = resp.choices[0].message

        # Si no hay llamados a herramientas, ya es la respuesta final
        if not getattr(msg, "tool_calls", None):
            return msg.content or "", visuales

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [tc.model_dump() for tc in msg.tool_calls]
        })

        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            result = ejecutar_herramienta(name, args)

            try:
                visual = crear_visual(name, args, result)
                if visual:
                    visuales.append(visual)
            except Exception as e:
                print(f"No se pudo preparar la gráfica de {name}: {e}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })

    return ("⚠️ El agente encadenó demasiadas herramientas sin llegar a una respuesta. "
            "Probá con una pregunta más específica."), visuales


# =========================
# MANEJO DE CHATS
# =========================

def abrir_chat(chat_id=None):
    st.session_state.memoria = MemoriaChat(client, almacen, chat_id,
                                           limite_recientes=LIMITE_RECIENTES, modelo=MODELO)


def nuevo_chat():
    if st.session_state.memoria.pantalla:      # evita acumular chats vacios
        abrir_chat(None)


def borrar_chat(chat_id):
    almacen.eliminar(chat_id)
    if st.session_state.memoria.id == chat_id:
        restantes = almacen.listar()
        abrir_chat(restantes[0]["id"] if restantes else None)


if "memoria" not in st.session_state:
    _chats = almacen.listar()
    abrir_chat(_chats[0]["id"] if _chats else None)

memoria = st.session_state.memoria


# =========================
# SIDEBAR
# =========================

with st.sidebar:
    st.markdown(f'<div class="marca">✿ {APP_NAME}</div>'
                f'<div class="marca-sub">agente económico</div>', unsafe_allow_html=True)
    st.button("＋  Nuevo chat", width="stretch", on_click=nuevo_chat, key="btn_nuevo")

    chats = almacen.listar()
    if chats:
        st.markdown('<div class="titulo-lateral">Mis chats</div>', unsafe_allow_html=True)
    for chat in chats:
        col_chat, col_borrar = st.columns([7, 1], gap="small", vertical_alignment="center")
        with col_chat:
            st.button(chat["titulo"], key=f"abrir_{chat['id']}", width="stretch",
                      type="primary" if chat["id"] == memoria.id else "secondary",
                      on_click=abrir_chat, args=(chat["id"],))
        with col_borrar:
            st.button("✕", key=f"borrar_{chat['id']}", help="Eliminar este chat",
                      on_click=borrar_chat, args=(chat["id"],))

    if memoria.resumen:
        st.markdown('<div class="titulo-lateral">Memoria</div>', unsafe_allow_html=True)
        with st.expander("Lo que recuerdo de este chat 💭"):
            st.write(memoria.resumen)

    st.markdown(f'<div class="pie"><b>{AUTORA}</b><br>{CURSO}<br>'
                'Fuentes: FRED (Reserva Federal), Frankfurter (BCE), open.er-api</div>',
                unsafe_allow_html=True)


# =========================
# CONVERSACION
# =========================

EJEMPLOS = [
    "💵 ¿Cuántos quetzales vale 1 dólar hoy?",
    "🏦 Mostrame la tasa de la Fed desde 2020",
    "📈 ¿Qué tan volátil ha sido el VIX este año?",
    "💶 ¿Cuánto valía el euro en dólares el 2024-01-02?",
]

# Marca invisible para darle otro estilo (degradado) a los mensajes de la usuaria
MARCA_USUARIA = '<span class="msg-usuaria"></span>'

consulta_pendiente = st.session_state.pop("consulta_pendiente", None)

if not memoria.pantalla and not consulta_pendiente:
    st.markdown(
        f'<div class="portada"><div class="flor">🌸</div>'
        f'<div class="nombre">{APP_NAME}</div>'
        f'<div class="sub">{APP_TAGLINE}</div>'
        '<div class="chips"><span class="chip">FRED</span><span class="chip">Tipo de cambio</span>'
        '<span class="chip">Estadística</span></div></div>',
        unsafe_allow_html=True,
    )
    columnas = st.columns(2)
    for i, ejemplo in enumerate(EJEMPLOS):
        with columnas[i % 2]:
            if st.button(ejemplo, key=f"ej_{i}", width="stretch"):
                st.session_state.consulta_pendiente = ejemplo.split(" ", 1)[1]
                st.rerun()

for i, mensaje in enumerate(memoria.pantalla):
    avatar = AVATAR_USUARIA if mensaje["role"] == "user" else AVATAR_AGENTE
    with st.chat_message(mensaje["role"], avatar=avatar):
        if mensaje["role"] == "user":
            st.markdown(MARCA_USUARIA, unsafe_allow_html=True)
        st.markdown(mensaje["content"])
        for j, visual in enumerate(mensaje.get("visuales", [])):
            mostrar_visual(visual, f"v_{memoria.id}_{i}_{j}")


# =========================
# ENTRADA DEL USUARIO
# =========================

user_text = st.chat_input("Preguntale a Fedra sobre tasas, inflación, el VIX o el tipo de cambio…")
if not user_text and consulta_pendiente:
    user_text = consulta_pendiente

if user_text and user_text.strip():
    user_text = user_text.strip()

    with st.chat_message("user", avatar=AVATAR_USUARIA):
        st.markdown(MARCA_USUARIA, unsafe_allow_html=True)
        st.markdown(user_text)

    with st.chat_message("assistant", avatar=AVATAR_AGENTE):
        with st.spinner("Fedra está consultando los datos… ✨"):
            respuesta, visuales = process_response(
                client, memoria.mensajes_para_modelo(), memoria.resumen, user_text
            )
        st.markdown(respuesta)
        for j, visual in enumerate(visuales):
            mostrar_visual(visual, f"v_nuevo_{j}")

    with st.spinner("Guardando en la memoria…"):
        memoria.registrar_turno(user_text, respuesta, visuales)

    st.rerun()

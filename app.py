import streamlit as st
import pandas as pd
import datetime
import os
import io
import json
from PIL import Image, ImageDraw, ImageFont

# Importação condicional do yfinance para captura do VIX em tempo real
try:
    import yfinance as yf
    HAS_YF = True
except ImportError:
    HAS_YF = False

# Importação condicional do ReportLab para PDF
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# Importação da SDK do Google GenAI para IA Multimodal (Gemini Free API)
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA INTERFACE WEB (Design Minimalista Institutional Fund Grade)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="GenilTrader [▲] — Diretor Quant Global",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Minimalista e de Alto Padrão Institucional
st.markdown("""
    <style>
    @import url('https://googleapis.com');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #090D16;
        color: #E2E8F0;
    }
    
    .stApp {
        background: radial-gradient(circle at 50% 0%, #111827 0%, #090D16 100%);
    }
    
    .main-header {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(212, 175, 55, 0.2);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .main-title { 
        font-size: 24px; 
        font-weight: 700; 
        color: #D4AF37; 
        letter-spacing: -0.5px;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .sub-title { 
        font-size: 13px; 
        color: #94A3B8; 
        margin-top: 6px;
        font-weight: 400;
    }
    
    .metric-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 16px;
        transition: all 0.2s ease-in-out;
    }
    .metric-card:hover {
        border-color: rgba(212, 175, 55, 0.4);
        transform: translateY(-2px);
    }
    .metric-title { font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 20px; color: #F8FAFC; font-weight: 700; margin: 4px 0; }
    .metric-sub { font-size: 11px; color: #10B981; font-weight: 500; }
    
    /* Customização de Botões */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #D4AF37 0%, #B8860B 100%) !important;
        color: #090D16 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 20px !important;
        box-shadow: 0 2px 10px rgba(212, 175, 55, 0.2) !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        opacity: 0.95;
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(212, 175, 55, 0.3) !important;
    }
    
    textarea { font-family: 'Inter', monospace !important; font-size: 13px !important; border-radius: 8px !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div class="main-title">🛡️ GENILTRADER [▲] — ENGINE DE INTELIGÊNCIA QUANT & ANÁLISE INSTITUCIONAL</div>
    <div class="sub-title">Mapeamento de Regiões de Liquidez Executiva, VJE (Vetor de Janelas Estruturais IPDA) e Zonas Complementares de Suporte e Resistência Semanal</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CONVERSOR INTERNO SIGILOSO CORRIGIDO (DERIVATIVOS -> CFDs OPERADOS)
# -----------------------------------------------------------------------------
def converter_dados_coleta_para_cfd(ativo_alvo, spot_in, zce_in, zae_in, er_in, alfa_in, omega_in, ratio_custom=None):
    try:
        spot = float(str(spot_in).replace('$', '').replace(',', ''))
        zce  = float(str(zce_in).replace('$', '').replace(',', ''))
        zae  = float(str(zae_in).replace('$', '').replace(',', ''))
        er   = float(str(er_in).replace('$', '').replace(',', ''))
        alfa = float(str(alfa_in).replace('$', '').replace(',', '')) if alfa_in else None
        omega= float(str(omega_in).replace('$', '').replace(',', '')) if omega_in else None
    except Exception:
        return spot_in, zce_in, zae_in, er_in, alfa_in, omega_in

    if ratio_custom and ratio_custom > 0:
        factor = ratio_custom
    elif "USTEC" in ativo_alvo or "NQ" in ativo_alvo or "QQQ" in ativo_alvo:
        factor = 54.0 if spot < 1000 else 1.0
    elif "US500" in ativo_alvo or "ES" in ativo_alvo or "SPY" in ativo_alvo:
        factor = 10.0 if spot < 1000 else 1.0
    else:
        factor = 1.0

    c_spot = round(spot * factor, 2)
    c_zce  = round(zce * factor, 2)
    c_zae  = round(zae * factor, 2)
    c_er   = round(er * factor, 2)
    c_alfa = round(alfa * factor, 2) if alfa else None
    c_omega= round(omega * factor, 2) if omega else None

    return f"${c_spot:,.2f}", f"${c_zce:,.2f}", f"${c_zae:,.2f}", f"${c_er:,.2f}", f"${c_alfa:,.2f}" if c_alfa else "", f"${c_omega:,.2f}" if c_omega else ""

# =============================================================================
# MÓDULO VIX QUANT — CAPTURA AUTOMÁTICA DE VOLATILIDADE EM TEMPO REAL
# =============================================================================
def renderizar_modulo_vix_quant():
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Volatilidade Dinâmica (VIX)")

    if HAS_YF:
        try:
            ticker_vix = yf.Ticker("^VIX")
            dados_vix = ticker_vix.history(period="2d")
            if not dados_vix.empty and len(dados_vix) >= 2:
                vix_atual = dados_vix['Close'].iloc[-1]
                vix_anterior = dados_vix['Close'].iloc[-2]
                variacao_vix = ((vix_atual - vix_anterior) / vix_anterior) * 100

                st.sidebar.metric(
                    label="Índice VIX (Tempo Real)",
                    value=f"{vix_atual:.2f}",
                    delta=f"{variacao_vix:+.2f}%",
                    delta_color="inverse"
                )

                if vix_atual > 20.0:
                    regime = "🔴 SHORT GAMMA — Expansão de Volatilidade"
                    filtro = "Pressão Vendedora Ativa"
                elif vix_atual < 14.0:
                    regime = "🟢 LONG GAMMA — Contração de Volatilidade"
                    filtro = "Pressão Compradora Ativa"
                else:
                    regime = "🟡 TRANSIÇÃO — Gama Neutro"
                    filtro = "Regime de Neutralidade / Lateral"

                return f"{vix_atual:.2f}", filtro
        except Exception:
            pass

    vix_manual = st.sidebar.text_input("Índice VIX (Manual)", "15.40")
    filtro_manual = st.sidebar.selectbox(
        "Regime VIX Manual",
        ["Regime de Neutralidade / Lateral", "Pressão Vendedora Ativa", "Pressão Compradora Ativa"]
    )
    return vix_manual, filtro_manual

# =============================================================================
# MÓDULO BOLETIM BLINDADO — CORREÇÃO DOS 29 MIL E EXCESSO DE ZEROS
# =============================================================================
def obter_template_boletim_blindado(dados, vix_valor, pressao):
    data_atual = datetime.date.today().strftime("%d/%m/%Y")
    try:
        er_v  = float(str(dados.get('er', 0)).replace('$','').replace(',',''))
        zce_v = float(str(dados.get('zce', 0)).replace('$','').replace(',',''))
        zae_v = float(str(dados.get('zae', 0)).replace('$','').replace(',',''))
        
        alfa_raw = float(str(dados.get('alfa', 0)).replace('$','').replace(',',''))
        omega_raw = float(str(dados.get('omega', 0)).replace('$','').replace(',',''))
        
        alfa_v = alfa_raw / 40.0 if alfa_raw > 100000 else alfa_raw
        omega_v = omega_raw / 40.0 if omega_raw > 100000 else omega_raw
        vix_f = float(str(vix_valor).replace(',','.'))
    except Exception:
        er_v=zce_v=zae_v=alfa_v=omega_v=vix_f=0.0

    texto = f"""[PT]
## 🔒 1. ARQUITETURA DE REGIMES DE PREÇO E VOLATILIDADE
O ativo USTEC opera sob o Eixo de Rotação (ER) posicionado em ${er_v:,.2f}, que atua como o divisor de águas algorítmico da sessão. A sustentação acima deste nível valida a busca por liquidez na Z-CE (${zce_v:,.2f}). A quebra do ER desloca o fluxo vendedor rumo à Z-AE (${zae_v:,.2f}). Métrica de Volatilidade (VIX): {vix_f:.2f} — Filtro de Pressão Sistêmica: {pressao}.

## ⚔️ 2. ZONAS DE EXAUSTÃO DIÁRIA E VETORES DE ARBITRAGEM
Fronteira Alfa (${alfa_v:,.2f}) e Fronteira Ômega (${omega_v:,.2f}) definem os extremos estatísticos. Rejeições nessas extremidades com Velas de Absorção Crítica oferecem janelas de alta assimetria matemática.

## 🛡️ 3. CLÁUSULA DE EXECUÇÃO E ASSIMETRIA MATEMÁTICA
- Acima do ER: Priorizar absorção compradora em retornos técnicos. Alvo: Z-CE (${zce_v:,.2f}).
- Abaixo do ER: Mapear exaustão de repiques. Alvo: Z-AE (${zae_v:,.2f}).
- Gerenciamento de Risco: Relação mínima de 1:2 de Payoff em todas as estruturas.

## 🎯 4. GUIA TÁTICO DE MARCAÇÃO NO GRÁFICO (ATENÇÃO ASSINANTE)
📌 PONTOS CRÍTICOS PARA INSERIR NO SEU GRÁFICO (TRADINGVIEW/METATRADER):

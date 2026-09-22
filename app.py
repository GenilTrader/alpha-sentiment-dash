import streamlit as st
import pandas as pd
import datetime
import os
import io
from PIL import Image

# Importação condicional do ReportLab para PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
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
    
    /* Textareas e Inputs */
    textarea { font-family: 'Inter', monospace !important; font-size: 13px !important; border-radius: 8px !important; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #1E293B;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 6px;
        padding: 0 16px;
        font-size: 13px;
        font-weight: 500;
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(212, 175, 55, 0.1) !important;
        color: #D4AF37 !important;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div class="main-title">🛡️ GENILTRADER [▲] — ENGINE DE INTELIGÊNCIA QUANT & ANÁLISE INSTITUCIONAL</div>
    <div class="sub-title">Mapeamento de Regiões de Liquidez Executiva, VJE (Vetor de Janelas Estruturais IPDA) e Níveis Secundários de Volatilidade</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CONVERSOR INTERNO SIGILOSO (DERIVATIVOS -> CFDs OPERADOS)
# -----------------------------------------------------------------------------
def converter_dados_coleta_para_cfd(ativo_alvo, spot_in, zce_in, zae_in, er_in, alfa_in, omega_in, ratio_custom=None):
    """
    Mapeia e converte valores coletados dos dados originais para a escala
    exata dos ativos que efetivamente operamos (USTEC, US500, etc.),
    sem expor a fonte de dados no relatório final.
    """
    try:
        spot = float(str(spot_in).replace('$', '').replace(',', ''))
        zce  = float(str(zce_in).replace('$', '').replace(',', ''))
        zae  = float(str(zae_in).replace('$', '').replace(',', ''))
        er   = float(str(er_in).replace('$', '').replace(',', ''))
        alfa = float(str(alfa_in).replace('$', '').replace(',', '')) if alfa_in else None
        omega= float(str(omega_in).replace('$', '').replace(',', '')) if omega_in else None
    except Exception:
        return spot_in, zce_in, zae_in, er_in, alfa_in, omega_in

    # Se o usuário especificou um fator customizado
    if ratio_custom and ratio_custom > 0:
        factor = ratio_custom
    elif "USTEC" in ativo_alvo or "NQ" in ativo_alvo or "QQQ" in ativo_alvo:
        # Se os dados informados foram na escala QQQ (~500-600) e o alvo é USTEC (~20000)
        factor = 40.0 if spot < 1000 else 1.0
    elif "US500" in ativo_alvo or "ES" in ativo_alvo or "SPY" in ativo_alvo:
        # Se os dados informados foram na escala SPY (~560-600) e o alvo é US500 (~5700)
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

# -----------------------------------------------------------------------------
# FUNÇÕES DE CÁLCULO QUANT E PROBABILIDADE INSTITUCIONAL
# -----------------------------------------------------------------------------
def calcular_regioes_e_probabilidade(spot, zce, zae, er, alfa=None, omega=None):
    try:
        spot_val = float(str(spot).replace('$', '').replace(',', ''))
        zce_val = float(str(zce).replace('$', '').replace(',', ''))
        zae_val = float(str(zae).replace('$', '').replace(',', ''))
        er_val = float(str(er).replace('$', '').replace(',', ''))
    except Exception:
        return {}

    dist_zce_pct = ((zce_val - spot_val) / spot_val) * 100
    dist_zae_pct = ((spot_val - zae_val) / spot_val) * 100
    dist_er_pct = ((spot_val - er_val) / spot_val) * 100

    if spot_val > er_val:
        vies = "Comprador (Acima do ER)"
        prob_testar_zce = max(40, min(92, 85 - abs(dist_zce_pct) * 5))
        prob_testar_zae = max(10, min(50, 30 - dist_zae_pct * 3))
    else:
        vies = "Vendedor (Abaixo do ER)"
        prob_testar_zae = max(40, min(92, 85 - abs(dist_zae_pct) * 5))
        prob_testar_zce = max(10, min(50, 30 - dist_zce_pct * 3))

    risco = abs(spot_val - er_val) if abs(spot_val - er_val) > 0 else 1.0
    alvo = abs(zce_val - spot_val) if spot_val > er_val else abs(spot_val - zae_val)
    rr_ratio = round(alvo / risco, 2) if risco > 0 else 1.0

    res = {
        "spot": spot_val,
        "zce": zce_val,
        "zae": zae_val,
        "er": er_val,
        "dist_zce_pct": round(dist_zce_pct, 2),
        "dist_zae_pct": round(dist_zae_pct, 2),
        "dist_er_pct": round(dist_er_pct, 2),
        "vies": vies,
        "prob_zce": round(prob_testar_zce, 1),
        "prob_zae": round(prob_testar_zae, 1),
        "rr_ratio": rr_ratio
    }

    if alfa and omega:
        try:
            alfa_val = float(str(alfa).replace('$', '').replace(',', ''))
            omega_val = float(str(omega).replace('$', '').replace(',', ''))
            res["alfa"] = alfa_val
            res["omega"] = omega_val
        except Exception:
            pass

    return res

# -----------------------------------------------------------------------------
# MOTOR DE IA INSTITUCIONAL (DIRETOR QUANT GLOBAL & ARQUITETO CHEFE)
# -----------------------------------------------------------------------------
def gerar_analise_ia(ativo_nome, spot, zce, zae, er, alfa, omega, vje_ipda, odtc_semanal, odtc_diario, macro_filtro, api_key=None, list_images=None):
    """
    Gera o relatório analítico bilingue [PT] e [EN] agindo rigorosamente como
    Diretor Quant Global de Hedge Fund com sigilo industrial absoluto.
    """
    calc = calcular_regioes_e_probabilidade(spot, zce, zae, er, alfa, omega)
    
    prompt_base = f"""
Você é o Diretor Quant Global & Arquiteto Chefe da marca global GenilTrader [▲].
Seu objetivo é gerar relatórios de mercado de altíssima exclusividade e apelo institucional, protegendo o nosso segredo industrial.

SUA TAREFA:
Gerar uma análise técnica e institucional cirúrgica para o ativo: {ativo_nome}.

DADOS CONTEXTUAIS DA SESSÃO:
- Ativo Operado: {ativo_nome}
- Preço Spot / Ajuste Inicial: {spot}
- Z-CE (Zona de Contração Executiva): {zce} (Distância: {calc.get('dist_zce_pct', 0)}% | Probabilidade de Teste: {calc.get('prob_zce', 0)}%)
- Z-AE (Zona de Absorção Executiva): {zae} (Distância: {calc.get('dist_zae_pct', 0)}% | Probabilidade de Teste: {calc.get('prob_zae', 0)}%)
- ER (Eixo de Rotação Algorítmico): {er} (Viés Atual: {calc.get('vies', 'Neutro')})
- Fronteira Alfa (Máxima): {alfa if alfa else 'N/A'}
- Fronteira Ômega (Mínima): {omega if omega else 'N/A'}
- VJE - Vetor de Janelas Estruturais (Liquidez IPDA / Swing Target): {vje_ipda if vje_ipda else 'Níveis de Varredura Intraday'}
- Nível Secundário de Volatilidade Semanal: {odtc_semanal if odtc_semanal else 'N/A'}
- Nível Secundário de Volatilidade Diário (Abertura NY): {odtc_diario if odtc_diario else 'N/A'}
- Filtro de Pressão Macroeconômica: {macro_filtro}
- Relação Risco:Retorno Estimada (R:R): 1:{calc.get('rr_ratio', 1.0)}

PROIBIÇÕES ABSOLUTAS (SIGILO INDUSTRIAL):
Está TERMINANTEMENTE PROIBIDO utilizar os termos de varejo públicos ou expor fontes de dados: "GEX", "Gamma Exposure", "Call Wall", "Put Wall", "Zero Gamma", "Overnight High/Low", "QQQ", "SPY", "ODTC", "CME" ou "IPDA".

NOMENCLATURA PROPRIETÁRIA OBRIGATÓRIA:
- Call Wall -> Z-CE (Zona de Contração Executiva / Executive Contraction Zone)
- Put Wall -> Z-AE (Zona de Absorção Executiva / Executive Absorption Zone)
- Zero Gamma -> ER (Eixo de Rotação / Rotation Axis)
- High/Low -> Fronteira Alfa (Máxima) e Fronteira Ômega (Mínima) / Alpha & Omega Frontiers
- Candles Laranjas/Volume -> Gatilhos de Ignição / Velas de Absorção Crítica (Critical Absorption Candles)
- Divergência SMT/Preço -> VAE (Vetor de Arbitragem Estatística / Statistical Arbitrage Vector)
- Captura de Liquidez IPDA -> VJE (Vetor de Janelas Estruturais / Structural Window Vector)
- ODTC -> Níveis Secundários de Volatilidade Semanal / Zonas Complementares de Suporte e Resistência

FORMATO EXATO EXIGIDO PARA A RESPOSTA (Copie a estrutura com [PT] e [EN]):

## 🔒 1. ARQUITETURA DE REGIMES DE PREÇO / PRICE REGIME ARCHITECTURE
[PT]
(Escreva a análise detalhada em Português sobre o comportamento projetado para {ativo_nome} na Z-CE, Z-AE, ER e a confluência com o VJE e os Níveis Secundários).
[EN]
(Escreva a mesma análise traduzida para o Inglês Institucional de Hedge Fund).

## ⚔️ 2. ZONAS DE EXAUSTÃO DIÁRIA E VETORES DE ARBITRAGEM / EXHAUSTION ZONES & ARBITRAGE VECTORS
[PT]
(Instruções de como rastrear o VAE entre o {ativo_nome} e seu par correlacionado no gráfico intraday e a reação nas Fronteiras Alfa/Ômega e nos Níveis Secundários de Volatilidade).
[EN]
(As mesmas instruções em Inglês institucional).

## 🛡️ 3. CLÁUSULA DE EXECUÇÃO E ASSIMETRIA MATEMÁTICA / EXECUTION RULES & ASYMMETRY
[PT]
(Regras estritas de gerenciamento de risco, confirmação por Velas de Absorção Crítica e invalidação técnica).
[EN]
(As mesmas regras em Inglês institucional).

## 🎯 4. GUIA TÁTICO DE MARCAÇÃO NO GRÁFICO / CHART MAPPING & OPERATIONAL CONDUCT
[PT]
📌 O QUE MARCAR NO SEU GRÁFICO (TRADINGVIEW / METATRADER):
- 🟡 LINHA AMARELA (Amarelo Ouro): ER (Eixo de Rotação) em {er} -> Divisor de águas principal da sessão.
- 🔴 LINHA VERMELHA (Resistência / Teto): Z-CE (Zona de Contração Executiva) em {zce} -> Região de topo institucional.
- 🟢 LINHA VERDE (Suporte / Piso): Z-AE (Zona de Absorção Executiva) em {zae} -> Região de suporte estrutural.
- 🟣 LINHAS ROXAS TRACEJADAS: Fronteira Alfa ({alfa if alfa else 'N/A'}) e Fronteira Ômega ({omega if omega else 'N/A'}) -> Extremos de volatilidade.
- 🔵 LINHA AZUL / CIANO: VJE (Vetor de Janelas Estruturais) em {vje_ipda if vje_ipda else 'Zonas de Liquidez'} -> Níveis primários de busca de liquidez.
- ⚪ LINHAS CINZAS DISCRETAS: Níveis Secundários de Volatilidade Semanal em {odtc_semanal if odtc_semanal else 'N/A'} -> Barreiras estatísticas complementares.

🎯 CONDUTA OPERACIONAL PASSO A PASSO:
1. Ponto de Equilíbrio (ER {er}): Acima do ER = Viés Comprador rumo à Z-CE; Abaixo do ER = Viés Vendedor rumo à Z-AE.
2. Reação no VJE ({vje_ipda if vje_ipda else 'Liquidez'}): Aguarde a varredura da liquidez e rejeição imediata com Vela de Absorção Crítica.
3. Invalidação: Fechamento de candle cheio além de Alfa/Ômega invalida o plano operacional.
[EN]
📌 CHART MAPPING GUIDE (TRADINGVIEW / METATRADER):
- 🟡 GOLDEN YELLOW LINE: ER (Rotation Axis) at {er} -> Core session equilibrium.
- 🔴 RED LINE (Resistance / Ceiling): Z-CE (Executive Contraction Zone) at {zce} -> Top institutional boundary.
- 🟢 GREEN LINE (Support / Floor): Z-AE (Executive Absorption Zone) at {zae} -> Deep structural support.
- 🟣 PURPLE DASHED LINES: Alpha ({alfa if alfa else 'N/A'}) & Omega ({omega if omega else 'N/A'}) Frontiers -> Extreme volatility boundaries.
- 🔵 CYAN LINE: VJE (Structural Window Vector) at {vje_ipda if vje_ipda else 'Liquidity Pools'} -> Primary liquidity targets.
- ⚪ GREY DASHED LINES: Secondary Volatility Levels (Weekly) at {odtc_semanal if odtc_semanal else 'N/A'} -> Complementary statistical barriers.

🎯 OPERATIONAL EXECUTION STEP-BY-STEP:
1. Equilibrium Point (ER {er}): Above ER = Bullish target Z-CE; Below ER = Bearish target Z-AE.
2. VJE Reaction ({vje_ipda if vje_ipda else 'Liquidity'}): Monitor liquidity sweeps and immediate rejection with Critical Absorption Candles.
3. Technical Invalidation: Full candle close beyond Alpha/Omega invalidates setup.
"""

    if api_key and HAS_GENAI:
        try:
            client = genai.Client(api_key=api_key)
            contents = []
            
            if list_images:
                for img_file in list_images:
                    try:
                        img_file.seek(0)
                        pil_img = Image.open(img_file)
                        contents.append(pil_img)
                    except Exception:
                        pass
                        
            contents.append(prompt_base)
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents
            )
            if response and response.text:
                return response.text
        except Exception as e:
            st.warning(f"⚠️ Erro na chamada da API Gemini ({str(e)}). Alternando para o Motor Quant Algorítmico Nativo.")

    # MOTOR QUANT ALGORÍTMICO NATIVO
    vies_str = calc.get('vies', 'Neutro')
    rr_str = f"1:{calc.get('rr_ratio', 1.0)}"
    zce_prob = calc.get('prob_zce', 50)
    zae_prob = calc.get('prob_zae', 50)

    texto_nativo = f"""[PT]
## 🔒 1. ARQUITETURA DE REGIMES DE PREÇO / PRICE REGIME ARCHITECTURE
O ativo {ativo_nome} opera sob o regime de {vies_str}. O Eixo de Rotação (ER) cravado em {er} atua como o principal ponto de equilíbrio algorítmico da sessão. A sustentação acima do ER mantém a probabilidade de {zce_prob}% para o teste da Z-CE (Zona de Contração Executiva) em {zce}, onde projeta-se forte absorção de ordens por parte das grandes tesourarias. Inversamente, a perda sustentada do ER acionará a distribuição de liquidez em direção à Z-AE (Zona de Absorção Executiva) em {zae} (probabilidade de {zae_prob}%). O VJE (Vetor de Janelas Estruturais) apontado em {vje_ipda if vje_ipda else 'Zonas Recentes'} atua como o principal alvo de varredura de liquidez.

## ⚔️ 2. ZONAS DE EXAUSTÃO DIÁRIA E VETORES DE ARBITRAGEM / EXHAUSTION ZONES & ARBITRAGE VECTORS
Aguardaremos o preço testar os limites das regiões institucionais (Fronteira Alfa {alfa if alfa else ''} ou Fronteira Ômega {omega if omega else ''}) ou os Níveis Secundários de Volatilidade Semanal ({odtc_semanal if odtc_semanal else 'N/A'}). O gatilho operacional de alta assimetria no gráfico intraday ocorrerá estritamente com o aparecimento de uma Vela de Absorção Crítica combinada com o acionamento do VAE (Vetor de Arbitragem Estatística) — caracterizado pela divergência do {ativo_nome} perante o filtro macroeconômico ({macro_filtro}).

## 🛡️ 3. CLÁUSULA DE EXECUÇÃO E ASSIMETRIA MATEMÁTICA / EXECUTION RULES & ASYMMETRY
Mantenha o risco estritamente limitado com assimetria estimada de {rr_str}. A invalidação técnica da tese ocorrerá caso o preço confirme o fechamento de uma barra cheia além das zonas de exaustão demarcadas. Não persiga o preço fora das regiões operacionais proprietárias.

## 🎯 4. GUIA TÁTICO DE MARCAÇÃO NO GRÁFICO / CHART MAPPING & OPERATIONAL CONDUCT
📌 O QUE MARCAR NO SEU GRÁFICO (TRADINGVIEW / METATRADER):
- 🟡 LINHA AMARELA (Amarelo Ouro): ER (Eixo de Rotação) em {er} -> Divisor de águas (Acima do ER = Viés Comprador; Abaixo do ER = Viés Vendedor).
- 🔴 LINHA VERMELHA (Resistência / Teto): Z-CE (Zona de Contração Executiva) em {zce} -> Região de topo. Procurar exaustão compradora para gatilhos de venda.
- 🟢 LINHA VERDE (Suporte / Piso): Z-AE (Zona de Absorção Executiva) em {zae} -> Região de fundo. Procurar suporte por absorção de volume para gatilhos de compra.
- 🟣 LINHAS ROXAS TRACEJADAS: Fronteira Alfa ({alfa if alfa else 'N/A'}) e Fronteira Ômega ({omega if omega else 'N/A'}) -> Extremos de volatilidade da sessão.
- 🔵 LINHA AZUL / CIANO: VJE (Vetor de Janelas Estruturais IPDA) em {vje_ipda if vje_ipda else 'Zonas de Liquidez'}.
- ⚪ LINHAS CINZAS TRACEJADAS: Níveis Secundários de Volatilidade Semanal em {odtc_semanal if odtc_semanal else 'N/A'}.

🎯 CONDUTA OPERACIONAL PASSO A PASSO:
1. Ponto de Equilíbrio (ER {er}): Se o preço estiver acima, busque compras nos recuos rumo à Z-CE ({zce}). Se estiver abaixo, busque vendas nos repiques rumo à Z-AE ({zae}).
2. Reação na Z-CE ({zce}): Não compre no topo! Aguarde Vela de Absorção Crítica de 1min/5min para entrar vendido buscando o retorno ao ER.
3. Reação na Z-AE ({zae}): Não venda no fundo! Aguarde absorção de ordens para entrar comprado buscando retorno ao ER.
4. Invalidação: Fechamento de candle cheio além de Alfa/Ômega invalida o setup operacional.

[EN]
## 🔒 1. PRICE REGIME ARCHITECTURE
The asset {ativo_nome} is trading under a {vies_str} regime. The Rotation Axis (ER) mapped at {er} serves as the core algorithmic equilibrium point for the session. Sustained price action above the ER maintains a {zce_prob}% probability of retesting the Z-CE (Executive Contraction Zone) at {zce}. The VJE (Structural Window Vector) at {vje_ipda if vje_ipda else 'Recent Pools'} serves as the primary liquidity sweep target.

## ⚔️ 2. EXHAUSTION ZONES & ARBITRAGE VECTORS
We will monitor price action near institutional boundary zones (Alpha Frontier {alfa if alfa else ''} / Omega Frontier {omega if omega else ''}) and Secondary Weekly Volatility Levels ({odtc_semanal if odtc_semanal else 'N/A'}). The execution trigger strictly requires a Critical Absorption Candle aligned with the Statistical Arbitrage Vector (VAE).

## 🛡️ 3. EXECUTION RULES & ASYMMETRY
Keep risk strictly contained with an estimated R:R ratio of {rr_str}. Technical invalidation is mandatory if a full candle body closes beyond the defined exhaustion zones.

## 🎯 4. CHART MAPPING GUIDE & OPERATIONAL CONDUCT
📌 CHART MAPPING GUIDE (TRADINGVIEW / METATRADER):
- 🟡 GOLDEN YELLOW LINE: ER (Rotation Axis) at {er} -> Session Equilibrium.
- 🔴 RED LINE (Resistance / Ceiling): Z-CE (Executive Contraction Zone) at {zce}.
- 🟢 GREEN LINE (Support / Floor): Z-AE (Executive Absorption Zone) at {zae}.
- 🟣 PURPLE DASHED LINES: Alpha ({alfa if alfa else 'N/A'}) & Omega ({omega if omega else 'N/A'}) Frontiers.
- 🔵 CYAN LINE: VJE (Structural Window Vector) at {vje_ipda if vje_ipda else 'Liquidity Target'}.
- ⚪ GREY DASHED LINES: Secondary Weekly Volatility Levels at {odtc_semanal if odtc_semanal else 'N/A'}.

🎯 OPERATIONAL EXECUTION STEP-BY-STEP:
1. Equilibrium Point (ER {er}): Above ER = Long towards Z-CE; Below ER = Short towards Z-AE.
2. Invalidation: Full candle body close beyond Alpha/Omega invalidates setup."""

    return texto_nativo

# -----------------------------------------------------------------------------
# FUNÇÃO DE COMPILAÇÃO DO PDF INSTITUCIONAL
# -----------------------------------------------------------------------------
def compilar_pdf(filename, lang, titulo, sub_titulo, label_ativo, label_ajuste, label_zce, label_zae, label_er, data_h, u_spot, u_zce, u_zae, u_er, s_spot, s_zce, s_zae, s_er, v_macro, analise_text, up_files, lista_legendas):
    doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    style_h1 = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=colors.HexColor('#0F172A'), spaceAfter=2)
    style_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#64748B'), spaceAfter=12)
    style_h2 = ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#B8860B'), spaceBefore=10, spaceAfter=4)
    style_body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=13, textColor=colors.HexColor('#334155'), spaceAfter=4)
    style_caption = ParagraphStyle('Caption', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#64748B'), alignment=1, spaceBefore=4, spaceAfter=8)
    
    elements = []
    elements.append(Paragraph(titulo, style_h1))
    elements.append(Paragraph(f"{sub_titulo} — Date/Data: {data_h}", style_sub))
    
    elements.append(Paragraph("🎯 ARQUITETURA DE REGIMES DE PREÇO / PRICE REGIME", style_h2))
    
    table_data = [
        [Paragraph(f"<b>{label_ativo}</b>", style_body), Paragraph(f"<b>{label_ajuste}</b>", style_body), Paragraph(f"<b>{label_zce}</b>", style_body), Paragraph(f"<b>{label_zae}</b>", style_body), Paragraph(f"<b>{label_er}</b>", style_body)],
        [Paragraph(f"<b>Vetor Principal</b>", style_body), str(u_spot), str(u_zce), str(u_zae), str(u_er)],
        [Paragraph(f"<b>Vetor Secundário</b>", style_body), str(s_spot), str(s_zce), str(s_zae), str(s_er)]
    ]
    
    prop_table = Table(table_data, colWidths=[106.4, 106.4, 106.4, 106.4, 106.4])
    prop_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F8FAFC')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
        ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor('#D4AF37')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0'))
    ]))
    elements.append(prop_table)
    elements.append(Spacer(1, 4))
    
    label_macro = "Filtro de Pressão Sistêmica Global" if lang == "PT" else "Global Systemic Pressure Filter"
    elements.append(Paragraph(f"<b>{label_macro}:</b> {v_macro}", style_body))
    
    elements.append(Paragraph("📝 DIRETRIZES TÁTICAS OPERACIONAIS / OPERATIONAL THESES", style_h2))
    
    linhas = analise_text.split('\n')
    bloco_valido = False
    texto_adicionado = False
    
    for l in linhas:
        if f"[{lang}]" in l:
            bloco_valido = True
            continue
        if l.strip().startswith("[") and f"[{lang}]" not in l:
            bloco_valido = False
            
        if bloco_valido and l.strip():
            elements.append(Paragraph(l, style_body))
            texto_adicionado = True
            
    if not texto_adicionado:
        for l in linhas:
            if l.strip() and not l.strip().startswith("["):
                elements.append(Paragraph(l, style_body))
                
    if up_files:
        elements.append(Paragraph("🖼️ MAPA VISUAL E ESTRUTURAL", style_h2))
        for idx, file in enumerate(up_files):
            try:
                temp_img_path = f"temp_chart_{lang}_{idx}.jpg"
                file.seek(0)
                img = Image.open(file)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
                img.save(temp_img_path, "JPEG", quality=85)
                
                max_width = 480
                w, h = img.size
                aspect = h / w if w > 0 else 0.75
                
                elements.append(RLImage(temp_img_path, width=max_width, height=max_width * aspect))
                legenda_atual = lista_legendas[idx] if idx < len(lista_legendas) else ""
                elements.append(Paragraph(f"<b>Figura {idx+1}:</b> {legenda_atual}", style_caption))
                elements.append(Spacer(1, 4))
            except Exception as err:
                st.error(f"Erro ao processar imagem {idx+1}: {err}")
        
    elements.append(Spacer(1, 10))
    aviso_text = "PROPRIEDADE INTELECTUAL RETIDA — DISTRIBUIÇÃO PROIBIDA EXTRA ASSINANTES" if lang == "PT" else "PROPRIETARY INTELLECTUAL PROPERTY — UNAUTHORIZED DISTRIBUTION IS STRICTLY PROHIBITED"
    style_aviso = ParagraphStyle('Aviso', parent=styles['Normal'], fontName='Helvetica-BoldOblique', fontSize=7.5, textColor=colors.HexColor('#94A3B8'), alignment=1)
    elements.append(Paragraph(f"{aviso_text} — GENILTRADER [▲]", style_aviso))
    
    doc.build(elements)

# -----------------------------------------------------------------------------
# SIDEBAR DE CONFIGURAÇÃO & CONVERSOR DE DADOS
# -----------------------------------------------------------------------------
st.sidebar.header("🎛️ Painel de Controle GenilTrader")

secret_key = ""
try:
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        secret_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    secret_key = ""

gemini_key_input = st.sidebar.text_input(
    "🔑 Gemini API Key (Opcional)",
    value=secret_key,
    type="password",
    help="Cole aqui sua chave gratuita do Google AI Studio!"
)
gemini_key = gemini_key_input if gemini_key_input else secret_key

st.sidebar.markdown("---")
data_hoje = st.sidebar.text_input("Data da Sessão", datetime.datetime.now().strftime("%d/%m/%Y"))

# Seletor de Ativo e Coleta de Dados
st.sidebar.subheader("🎯 Seletor de Ativo Operado (CFD)")
categoria_ativo = st.sidebar.selectbox("Classe de Ativo:", [
    "Índices / CFDs (USTEC / US500)", 
    "Commodities (XAUUSD / USOIL)", 
    "Forex (EURUSD / GBPUSD)", 
    "Ações / CFDs (NVDA / AAPL)", 
    "Crypto (BTCUSD / ETHUSD)", 
    "Outro / Personalizado"
])

if categoria_ativo == "Índices / CFDs (USTEC / US500)":
    ativo_p1 = "USTEC (Nasdaq CFD)"
    ativo_p2 = "US500 (S&P 500 CFD)"
elif categoria_ativo == "Commodities (XAUUSD / USOIL)":
    ativo_p1 = "XAUUSD (Ouro)"
    ativo_p2 = "USOIL (WTI)"
elif categoria_ativo == "Forex (EURUSD / GBPUSD)":
    ativo_p1 = "EURUSD"
    ativo_p2 = "GBPUSD"
elif categoria_ativo == "Ações / CFDs (NVDA / AAPL)":
    ativo_p1 = "NVDA"
    ativo_p2 = "AAPL"
elif categoria_ativo == "Crypto (BTCUSD / ETHUSD)":
    ativo_p1 = "BTCUSD"
    ativo_p2 = "ETHUSD"
else:
    ativo_p1 = st.sidebar.text_input("Ativo Principal:", "USTEC")
    ativo_p2 = st.sidebar.text_input("Ativo Correlacionado:", "US500")

# PAINEL DE COLETA E CONVERSÃO SIGILOSA
st.sidebar.markdown("---")
st.sidebar.markdown(f"### 📥 Coleta de Dados & Conversor Sigiloso")
st.sidebar.caption("Cole os valores brutos coletados nos prints. O app converterá e plotará estritamente nas regiões do ativo operado.")

col_conv1, col_conv2 = st.sidebar.columns(2)
with col_conv1:
    in_spot = st.text_input("Preço Ajuste/Spot", "$520.30")
    in_zce  = st.text_input("Z-CE (Resistência)", "$525.00")
    in_zae  = st.text_input("Z-AE (Suporte)", "$510.00")
with col_conv2:
    in_er   = st.text_input("ER (Eixo Rotação)", "$518.40")
    in_alfa = st.text_input("Fronteira Alfa", "$528.50")
    in_omega= st.text_input("Fronteira Ômega", "$505.00")

fator_multiplicador = st.sidebar.number_input("Fator Multiplicador CFD (Auto se 0)", value=0.0, step=1.0)

# CONVERSÃO AUTOMÁTICA EM TEMPO REAL
u_spot_in, u_zce_in, u_zae_in, u_er_in, u_alfa_in, u_omega_in = converter_dados_coleta_para_cfd(
    ativo_p1, in_spot, in_zce, in_zae, in_er, in_alfa, in_omega, ratio_custom=fator_multiplicador
)

st.sidebar.markdown("##### 📌 Níveis Complementares & Secundários")
vje_ipda_in = st.sidebar.text_input("VJE (Vetor Janelas IPDA / Sweep Target)", "$20,840.00")
odtc_sem_in = st.sidebar.text_input("Nível Secundário Volatilidade Semanal", "$20,780.00")
odtc_dia_in = st.sidebar.text_input("Nível Secundário Volatilidade Diária (NY)", "$20,810.00")

# Parâmetros Ativo Secundário
st.sidebar.markdown(f"**Parâmetros: {ativo_p2}**")
s_spot_in = st.sidebar.text_input(f"{ativo_p2} — Preço Spot", "$5,720.00")
s_zce_in  = st.sidebar.text_input(f"{ativo_p2} — Z-CE", "$5,750.00")
s_zae_in  = st.sidebar.text_input(f"{ativo_p2} — Z-AE", "$5,680.00")
s_er_in   = st.sidebar.text_input(f"{ativo_p2} — ER", "$5,710.00")

st.sidebar.subheader("📺 Vetor Macroeconômico")
vetor_macro_pt = st.sidebar.selectbox("Filtro de Pressão (PT)", ["Regime de Neutralidade / Lateral", "Pressão Vendedora Ativa", "Pressão Compradora Ativa"])

st.sidebar.markdown("---")
bt_processar = st.sidebar.button("🔥 EMITIR BOLETINS INTERNACIONAIS", use_container_width=True)
st.sidebar.markdown("---")

if os.path.exists("boletim_alfa_PT.pdf") or os.path.exists("boletim_alfa_EN.pdf"):
    st.sidebar.subheader("📥 Downloads Disponibilizados")
    if os.path.exists("boletim_alfa_PT.pdf"):
        with open("boletim_alfa_PT.pdf", "rb") as f_pt:
            st.sidebar.download_button(
                "📥 BOLETIM PORTUGUÊS [PDF]",
                data=f_pt,
                file_name=f"Boletim_Alfa_PT_{data_hoje.replace('/', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    if os.path.exists("boletim_alfa_EN.pdf"):
        with open("boletim_alfa_EN.pdf", "rb") as f_en:
            st.sidebar.download_button(
                "📥 ENGLISH VERSION [PDF]",
                data=f_en,
                file_name=f"Alpha_Sentiment_EN_{data_hoje.replace('/', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# -----------------------------------------------------------------------------
# CORPO PRINCIPAL COM ABAS NAVEGÁVEIS
# -----------------------------------------------------------------------------
tab_analise, tab_auditoria, tab_manual = st.tabs([
    "📝 Análise & Gerador Quant", 
    "📈 Auditoria & Base de Dados", 
    "📖 Manual & Diretrizes Quant"
])

# -----------------------------------------------------------------------------
# ABA 1: ANÁLISE DA MANHÃ & GERADOR QUANT MULTIMODAL
# -----------------------------------------------------------------------------
with tab_analise:
    calc_res = calcular_regioes_e_probabilidade(u_spot_in, u_zce_in, u_zae_in, u_er_in, u_alfa_in, u_omega_in)
    
    st.subheader(f"📊 Diagnóstico em Tempo Real — Regiões Convertidas para {ativo_p1}")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    with m_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Viés Algorítmico</div>
            <div class="metric-value" style="color: {'#10B981' if 'Comprador' in calc_res.get('vies','') else '#EF4444'};">{calc_res.get('vies', 'Calculando...')}</div>
            <div class="metric-sub">Dist. ER: {calc_res.get('dist_er_pct', 0)}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with m_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Z-CE (Contração)</div>
            <div class="metric-value">{u_zce_in}</div>
            <div class="metric-sub">Prob. Teste: {calc_res.get('prob_zce', 0)}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with m_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Z-AE (Absorção)</div>
            <div class="metric-value">{u_zae_in}</div>
            <div class="metric-sub">Prob. Teste: {calc_res.get('prob_zae', 0)}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with m_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Assimetria (R:R)</div>
            <div class="metric-value" style="color: #D4AF37;">1 : {calc_res.get('rr_ratio', 1.0)}</div>
            <div class="metric-sub">Alvo / Risco no ER</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    col_text, col_graph = st.columns(2)

    with col_graph:
        st.subheader("🖼️ Galeria de Prints e Comparação Gráfica")
        st.caption("Selecione múltiplos prints gráficos simultaneamente (ex: 15min e 5min):")
        
        uploaded_files = st.file_uploader(
            "Arrastar múltiplos prints gráficos aqui",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.session_state['uploaded_files_cache'] = uploaded_files
            st.info(f"📸 {len(uploaded_files)} gráfico(s) carregado(s). Insira as legendas abaixo:")

        legendas_pt = []
        legendas_en = []

        if uploaded_files:
            for idx, file in enumerate(uploaded_files):
                st.markdown(f"**Figura {idx+1}: {file.name}**")
                leg_pt = st.text_input(f"Legenda (PT) #{idx+1}", f"Mapeamento Operacional {ativo_p1} - Gráfico {idx+1}", key=f"leg_pt_{idx}")
                leg_en = st.text_input(f"Caption (EN) #{idx+1}", f"Operational Mapping {ativo_p1} - Chart {idx+1}", key=f"leg_en_{idx}")
                legendas_pt.append(leg_pt)
                legendas_en.append(leg_en)

    with col_text:
        st.subheader("📝 Diretrizes Táticas Operacionais")
        
        if st.button("🤖 GERAR ANÁLISE POR IA (DIRETOR QUANT GLOBAL)", use_container_width=True):
            with st.spinner("Analisando métricas quant e gerando relatório PDF completo..."):
                texto_gerado = gerar_analise_ia(
                    ativo_nome=ativo_p1,
                    spot=u_spot_in,
                    zce=u_zce_in,
                    zae=u_zae_in,
                    er=u_er_in,
                    alfa=u_alfa_in,
                    omega=u_omega_in,
                    vje_ipda=vje_ipda_in,
                    odtc_semanal=odtc_sem_in,
                    odtc_diario=odtc_dia_in,
                    macro_filtro=vetor_macro_pt,
                    api_key=gemini_key,
                    list_images=st.session_state.get('uploaded_files_cache', None)
                )
                st.session_state['analise_texto_key'] = texto_gerado

                vetor_macro_en = "Neutral Regime / Lateral" if "Neutralidade" in vetor_macro_pt else ("Active Selling Pressure" if "Vendedora" in vetor_macro_pt else "Active Buying Pressure")
                
                compilar_pdf(
                    filename="boletim_alfa_PT.pdf",
                    lang="PT",
                    titulo=f"BOLETIM ALFA — {ativo_p1}",
                    sub_titulo="Relatório Quantitativo Institucional Exclusivo",
                    label_ativo="Ativo Operado",
                    label_ajuste="Spot / Ajuste",
                    label_zce="Z-CE (Contração)",
                    label_zae="Z-AE (Absorção)",
                    label_er="ER (Eixo Rotação)",
                    data_h=data_hoje,
                    u_spot=u_spot_in, u_zce=u_zce_in, u_zae=u_zae_in, u_er=u_er_in,
                    s_spot=s_spot_in, s_zce=s_zce_in, s_zae=s_zae_in, s_er=s_er_in,
                    v_macro=vetor_macro_pt,
                    analise_text=texto_gerado,
                    up_files=uploaded_files,
                    lista_legendas=legendas_pt
                )

                compilar_pdf(
                    filename="boletim_alfa_EN.pdf",
                    lang="EN",
                    titulo=f"ALPHA BULLETIN — {ativo_p1}",
                    sub_titulo="Exclusive Institutional Quantitative Report",
                    label_ativo="Traded Asset",
                    label_ajuste="Spot / Settlement",
                    label_zce="Z-CE (Contraction)",
                    label_zae="Z-AE (Absorption)",
                    label_er="ER (Rotation Axis)",
                    data_h=data_hoje,
                    u_spot=u_spot_in, u_zce=u_zce_in, u_zae=u_zae_in, u_er=u_er_in,
                    s_spot=s_spot_in, s_zce=s_zce_in, s_zae=s_zae_in, s_er=s_er_in,
                    v_macro=vetor_macro_en,
                    analise_text=texto_gerado,
                    up_files=uploaded_files,
                    lista_legendas=legendas_en
                )
                st.success("Análise e Relatórios PDF em Português e Inglês gerados com sucesso!")

        analise_texto = st.text_area(
            "Boletim Proprietário Bilíngue",
            value=st.session_state.get('analise_texto_key', ""),
            height=380,
            placeholder="Clique no botão acima para a IA gerar automaticamente..."
        )

        if os.path.exists("boletim_alfa_PT.pdf") or os.path.exists("boletim_alfa_EN.pdf"):
            st.markdown("##### 📥 Baixar Relatórios em PDF:")
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                if os.path.exists("boletim_alfa_PT.pdf"):
                    with open("boletim_alfa_PT.pdf", "rb") as f_pt:
                        st.download_button(
                            "📥 BOLETIM PORTUGUÊS [PDF]",
                            data=f_pt,
                            file_name=f"Boletim_Alfa_PT_{data_hoje.replace('/', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
            with d_col2:
                if os.path.exists("boletim_alfa_EN.pdf"):
                    with open("boletim_alfa_EN.pdf", "rb") as f_en:
                        st.download_button(
                            "📥 DOWNLOAD ENGLISH BULLETIN [PDF]",
                            data=f_en,
                            file_name=f"Alpha_Bulletin_EN_{data_hoje.replace('/', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

    if bt_processar:
        if not analise_texto.strip():
            st.error("⚠️ Insira ou gere o texto da análise antes de emitir os boletins!")
        else:
            with st.spinner("Compilando relatórios PDF em Português e Inglês..."):
                vetor_macro_en = "Neutral Regime / Lateral" if "Neutralidade" in vetor_macro_pt else ("Active Selling Pressure" if "Vendedora" in vetor_macro_pt else "Active Buying Pressure")
                
                compilar_pdf(
                    filename="boletim_alfa_PT.pdf",
                    lang="PT",
                    titulo=f"BOLETIM ALFA — {ativo_p1}",
                    sub_titulo="Relatório Quantitativo Institucional Exclusivo",
                    label_ativo="Ativo Operado",
                    label_ajuste="Spot / Ajuste",
                    label_zce="Z-CE (Contração)",
                    label_zae="Z-AE (Absorção)",
                    label_er="ER (Eixo Rotação)",
                    data_h=data_hoje,
                    u_spot=u_spot_in, u_zce=u_zce_in, u_zae=u_zae_in, u_er=u_er_in,
                    s_spot=s_spot_in, s_zce=s_zce_in, s_zae=s_zae_in, s_er=s_er_in,
                    v_macro=vetor_macro_pt,
                    analise_text=analise_texto,
                    up_files=uploaded_files,
                    lista_legendas=legendas_pt
                )

                compilar_pdf(
                    filename="boletim_alfa_EN.pdf",
                    lang="EN",
                    titulo=f"ALPHA BULLETIN — {ativo_p1}",
                    sub_titulo="Exclusive Institutional Quantitative Report",
                    label_ativo="Traded Asset",
                    label_ajuste="Spot / Settlement",
                    label_zce="Z-CE (Contraction)",
                    label_zae="Z-AE (Absorption)",
                    label_er="ER (Rotation Axis)",
                    data_h=data_hoje,
                    u_spot=u_spot_in, u_zce=u_zce_in, u_zae=u_zae_in, u_er=u_er_in,
                    s_spot=s_spot_in, s_zce=s_zce_in, s_zae=s_zae_in, s_er=s_er_in,
                    v_macro=vetor_macro_en,
                    analise_text=analise_texto,
                    up_files=uploaded_files,
                    lista_legendas=legendas_en
                )

                st.success("🔥 BOLETIM PT E BOLETIM EN GERADOS COM SUCESSO!")

# -----------------------------------------------------------------------------
# ABA 2: AUDITORIA DE PERFORMANCE & BASE DE DADOS
# -----------------------------------------------------------------------------
with tab_auditoria:
    st.subheader("📈 Auditoria de Performance & Banco de Dados de Confluência")
    st.caption("Registre e monitore a taxa de assertividade por região institucional.")
    
    hist_file = "historico_trades.csv"
    if os.path.exists(hist_file):
        try:
            df_hist = pd.read_csv(hist_file)
        except Exception:
            df_hist = pd.DataFrame(columns=["Data", "Ativo", "Regiao_Reacao", "Direcao", "Resultado", "R_Multiplo"])
    else:
        df_hist = pd.DataFrame(columns=["Data", "Ativo", "Regiao_Reacao", "Direcao", "Resultado", "R_Multiplo"])

    col_form, col_stats = st.columns([1, 2])

    with col_form:
        st.markdown("##### 📝 Novo Registro de Sessão/Trade")
        reg_ativo = st.text_input("Ativo / CFD Operado:", value=ativo_p1)
        reg_regiao = st.selectbox("Região de Reação do Preço:", ["Z-CE (Zona Contração)", "Z-AE (Zona Absorção)", "ER (Eixo Rotação)", "VJE (Vetor Janelas)", "Fronteira Alfa", "Fronteira Ômega"])
        reg_direcao = st.selectbox("Direcional:", ["COMPRA (Long)", "VENDA (Short)"])
        reg_resultado = st.selectbox("Resultado:", ["GAIN (Lucro)", "LOSS (Stop)", "BE (Empate)"])
        reg_rmult = st.number_input("Múltiplo R:R Alcançado:", min_value=0.0, max_value=20.0, value=2.0, step=0.5)

        if st.button("💾 Salvar Registro no Banco de Dados", use_container_width=True):
            novo_row = pd.DataFrame([{
                "Data": data_hoje,
                "Ativo": reg_ativo,
                "Regiao_Reacao": reg_regiao,
                "Direcao": reg_direcao,
                "Resultado": reg_resultado,
                "R_Multiplo": reg_rmult
            }])
            df_hist = pd.concat([df_hist, novo_row], ignore_index=True)
            df_hist.to_csv(hist_file, index=False)
            st.success("Trade registrado com sucesso na base de cálculo!")

    with col_stats:
        st.markdown("##### 📊 Estatísticas Acumuladas")
        if not df_hist.empty:
            total_trades = len(df_hist)
            gains = (df_hist["Resultado"] == "GAIN (Lucro)").sum()
            win_rate = (gains / total_trades) * 100 if total_trades > 0 else 0
            
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Total de Registros", total_trades)
            sc2.metric("Assertividade (Win Rate)", f"{win_rate:.1f}%")
            sc3.metric("Média R:R", f"{df_hist['R_Multiplo'].mean():.2f} R")

            st.markdown("##### 📋 Tabela de Histórico Acumulado")
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.warning("Nenhum trade registrado ainda.")

# -----------------------------------------------------------------------------
# ABA 3: MANUAL DE OPERAÇÃO & DIRETRIZES QUANT
# -----------------------------------------------------------------------------
with tab_manual:
    st.header("📖 Manual Operacional e Diretrizes Institucionais GenilTrader [▲]")
    
    st.markdown("""
    ### 🔑 1. Como Obter a Chave Gratuita do Google Gemini
    Acesse o **Google AI Studio** ([https://aistudio.google.com/](https://aistudio.google.com/)), crie uma API key e insira no campo da barra lateral.

    ---

    ### 🎯 2. Arquitetura de Regiões e Sigilo Operacional
    - **Z-CE (Zona de Contração Executiva)**: Barreira teto onde grandes tesourarias posicionam travas institucionais.
    - **Z-AE (Zona de Absorção Executiva)**: Suporte estrutural de compras de proteção.
    - **ER (Eixo de Rotação Algorítmico)**: Ponto de equilíbrio justo (Fair Value).
    - **VJE (Vetor de Janelas Estruturais IPDA)**: Varredura de liquidez em janelas temporais fractais (Draw on Liquidity).
    - **Níveis Secundários de Volatilidade Semanal**: Barreiras complementares de desvio estatístico.
    """)

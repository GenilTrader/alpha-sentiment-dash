import streamlit as st
import pandas as pd
import datetime
import os
import io
import json
from PIL import Image, ImageDraw, ImageFont

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
# MÓDULO 1: SNAPSHOT DIÁRIO COM TIMESTAMP
# -----------------------------------------------------------------------------
SNAPSHOT_FILE = "snapshots_diarios.json"

def salvar_snapshot(ativo, spot, zce, zae, er, alfa, omega, vje, odtc_sem, macro):
    """Salva um snapshot dos níveis do dia com timestamp exato para histórico."""
    snapshot = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": datetime.datetime.now().strftime("%d/%m/%Y"),
        "ativo": ativo,
        "spot": spot, "zce": zce, "zae": zae, "er": er,
        "alfa": alfa, "omega": omega,
        "vje": vje, "odtc_semanal": odtc_sem,
        "macro": macro
    }
    historico = []
    if os.path.exists(SNAPSHOT_FILE):
        try:
            with open(SNAPSHOT_FILE, 'r', encoding='utf-8') as f:
                historico = json.load(f)
        except Exception:
            historico = []
    historico.append(snapshot)
    with open(SNAPSHOT_FILE, 'w', encoding='utf-8') as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)
    return snapshot

# -----------------------------------------------------------------------------
# MÓDULO 3: GERADOR DE CARD VISUAL PARA REDES SOCIAIS (PNG 1080x1080)
# -----------------------------------------------------------------------------
def gerar_card_visual(ativo, data, spot, zce, zae, er, vje, odtc_sem, vies, rr):
    """
    Gera um card PNG 1080x1080 pronto para Instagram/Stories/WhatsApp
    com visual GenilTrader [▲] sem expor nenhuma fonte de dados.
    """
    W, H = 1080, 1080
    img = Image.new('RGB', (W, H), color='#090D16')
    draw = ImageDraw.Draw(img)

    # Gradiente de fundo simulado
    for y in range(H):
        alpha = int(20 * (1 - y / H))
        r = min(255, 17 + alpha)
        g = min(255, 24 + alpha)
        b = min(255, 39 + alpha)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Borda dourada superior
    draw.rectangle([(0, 0), (W, 8)], fill='#D4AF37')
    draw.rectangle([(0, H-8), (W, H)], fill='#D4AF37')

    # Linha decorativa lateral
    draw.rectangle([(0, 0), (6, H)], fill='#D4AF37')
    draw.rectangle([(W-6, 0), (W, H)], fill='#D4AF37')

    # Tentar usar fontes do sistema; se não, usa padrão
    try:
        fnt_title  = ImageFont.truetype("arial.ttf", 56)
        fnt_sub    = ImageFont.truetype("arial.ttf", 30)
        fnt_label  = ImageFont.truetype("arialbd.ttf", 26)
        fnt_value  = ImageFont.truetype("arialbd.ttf", 46)
        fnt_small  = ImageFont.truetype("arial.ttf", 22)
        fnt_brand  = ImageFont.truetype("arialbd.ttf", 32)
    except Exception:
        fnt_title  = ImageFont.load_default()
        fnt_sub    = fnt_title
        fnt_label  = fnt_title
        fnt_value  = fnt_title
        fnt_small  = fnt_title
        fnt_brand  = fnt_title

    # Header
    draw.text((54, 30), "GENILTRADER [▲]", font=fnt_brand, fill='#D4AF37')
    draw.text((54, 78), "BOLETIM ALFA — ANÁLISE INSTITUCIONAL", font=fnt_small, fill='#94A3B8')

    # Linha separadora
    draw.rectangle([(54, 122), (W-54, 125)], fill='#1E293B')

    # Ativo e Data
    draw.text((54, 140), ativo, font=fnt_title, fill='#F8FAFC')
    draw.text((W-250, 158), data, font=fnt_sub, fill='#64748B')

    # Viés
    vies_cor = '#10B981' if 'Comprador' in vies else '#EF4444'
    vies_texto = '▲ REGIME COMPRADOR' if 'Comprador' in vies else '▼ REGIME VENDEDOR'
    draw.text((54, 230), vies_texto, font=fnt_sub, fill=vies_cor)

    # Linha separadora
    draw.rectangle([(54, 285), (W-54, 287)], fill='#1E293B')

    # Regiões principais — layout de grid
    regioes = [
        ("🔴  Z-CE  —  Zona de Contração",   zce,  '#EF4444'),
        ("🟡  ER    —  Eixo de Rotação",      er,   '#D4AF37'),
        ("🟢  Z-AE  —  Zona de Absorção",     zae,  '#10B981'),
        ("🔵  VJE   —  Vetor de Janelas",     vje,  '#38BDF8'),
    ]
    y_pos = 308
    for label, valor, cor in regioes:
        draw.text((70, y_pos), label, font=fnt_label, fill='#94A3B8')
        draw.text((70, y_pos + 34), str(valor) if valor else 'N/A', font=fnt_value, fill=cor)
        y_pos += 130

    # Nível secundário
    draw.rectangle([(54, y_pos), (W-54, y_pos+1)], fill='#1E293B')
    draw.text((70, y_pos+14), f"Nível Secundário Semanal:  {odtc_sem if odtc_sem else 'N/A'}", font=fnt_small, fill='#64748B')
    draw.text((70, y_pos+44), f"R:R Estimado:  1:{rr}   |   Spot:  {spot}", font=fnt_small, fill='#64748B')

    # Rodapé
    draw.rectangle([(54, H-120), (W-54, H-119)], fill='#1E293B')
    draw.text((54, H-108), "Propriedade Intelectual Retida — Exclusivo para Assinantes", font=fnt_small, fill='#334155')
    draw.text((54, H-78), "GenilTrader [▲] — Distribuição Proibida Extra Assinantes", font=fnt_small, fill='#334155')
    draw.text((54, H-48), "www.geniltrader.com", font=fnt_small, fill='#D4AF37')

    card_path = "card_social_media.png"
    img.save(card_path, 'PNG', quality=95)
    return card_path

# Extração de valores de imagem via IA (PRIVADO - nunca vai ao PDF)
def extrair_valores_de_imagem(imagem_file, api_key):
    """
    Usa a visão computacional do Gemini para ler valores numéricos
    de um print de referência. Os valores são retornados para preenchimento
    automático. A imagem NUNCA é armazenada nem inserida no relatório.
    """
    if not api_key or not HAS_GENAI:
        return None
    try:
        imagem_file.seek(0)
        pil_img = Image.open(imagem_file)
        client = genai.Client(api_key=api_key)
        prompt_extracao = """
        Analise esta imagem e extraia APENAS os valores numéricos das seguintes categorias:
        1. Call Wall (nível de resistência superior)
        2. Put Wall (nível de suporte inferior)  
        3. Zero Gamma / Gamma Flip (ponto de equilíbrio)
        4. Spot / Preço atual
        
        Retorne APENAS um JSON puro sem markdown, no seguinte formato exato:
        {"call_wall": 000.00, "put_wall": 000.00, "zero_gamma": 000.00, "spot": 000.00}
        
        Se não encontrar algum valor, coloque null. Não inclua texto adicional.
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[pil_img, prompt_extracao]
        )
        if response and response.text:
            texto = response.text.strip()
            # Limpa markdown se veio
            if '```' in texto:
                texto = texto.split('```')[1].replace('json', '').strip()
            dados = json.loads(texto)
            return dados
    except Exception as e:
        return {"erro": str(e)}
    return None

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
tab_analise, tab_coleta, tab_auditoria, tab_manual = st.tabs([
    "📝 Análise & Gerador Quant",
    "🔍 Coleta Privada (Nunca no Relatório)",
    "📈 Auditoria & Base de Dados", 
    "📖 Manual & Glossário Quant"
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
                
                # MÓDULO 1: Salvar snapshot automático com timestamp
                salvar_snapshot(
                    ativo=ativo_p1, spot=u_spot_in, zce=u_zce_in,
                    zae=u_zae_in, er=u_er_in, alfa=u_alfa_in,
                    omega=u_omega_in, vje=vje_ipda_in,
                    odtc_sem=odtc_sem_in, macro=vetor_macro_pt
                )

                # MÓDULO 3: Gerar card visual para redes sociais
                try:
                    calc_card = calcular_regioes_e_probabilidade(u_spot_in, u_zce_in, u_zae_in, u_er_in)
                    card_path = gerar_card_visual(
                        ativo=ativo_p1,
                        data=data_hoje,
                        spot=u_spot_in, zce=u_zce_in,
                        zae=u_zae_in, er=u_er_in,
                        vje=vje_ipda_in, odtc_sem=odtc_sem_in,
                        vies=calc_card.get('vies',''),
                        rr=calc_card.get('rr_ratio', 1.0)
                    )
                    st.session_state['card_path'] = card_path
                except Exception as e_card:
                    st.warning(f"Card visual não gerado: {e_card}")

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

    # Download do Card Visual Social Media
    if st.session_state.get('card_path') and os.path.exists(st.session_state.get('card_path', '')):
        st.markdown("---")
        st.subheader("📸 Card Visual para Redes Sociais (1080x1080)")
        st.caption("Pronto para Instagram, Stories e WhatsApp. Não contém nenhuma referência à fonte de dados.")
        with open(st.session_state['card_path'], 'rb') as f_card:
            col_img, col_btn = st.columns([2, 1])
            with col_img:
                st.image(st.session_state['card_path'], use_container_width=True)
            with col_btn:
                st.download_button(
                    "📥 BAIXAR CARD SOCIAL MEDIA (PNG)",
                    data=f_card,
                    file_name=f"GenilTrader_Card_{data_hoje.replace('/', '_')}.png",
                    mime="image/png",
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
# ABA 2: COLETA PRIVADA — IMAGENS NUNCA VÃO AO RELATÓRIO
# -----------------------------------------------------------------------------
with tab_coleta:
    st.subheader("🔍 Módulo de Coleta Privada — Leitura de Referência")
    st.warning("""
    ⚠️ **ZONA RESTRITA — SOMENTE PARA USO INTERNO**
    As imagens carregadas aqui são usadas APENAS para leitura automática de valores pela IA.
    Elas NUNCA são armazenadas permanentemente nem aparecem em nenhum relatório ou PDF gerado.
    """)
    
    col_col1, col_col2 = st.columns([1,1])
    
    with col_col1:
        st.markdown("##### 📎 Carregar Print de Referência (Coleta Interna)")
        st.caption("Faça upload do seu print de referência dos dados de opções. A IA extrai os valores automaticamente.")
        
        arquivo_coleta = st.file_uploader(
            "Upload do print de dados de referência (uso interno)",
            type=["png", "jpg", "jpeg"],
            key="upload_coleta_privada",
            help="Este arquivo é usado APENAS para leitura de valores. NUNCA aparecerá no relatório."
        )
        
        if arquivo_coleta:
            st.image(arquivo_coleta, caption="Print de referência (não vai ao relatório)", use_container_width=True)
            
            if gemini_key and HAS_GENAI:
                if st.button("🤖 EXTRAIR VALORES AUTOMATICAMENTE (IA)", use_container_width=True):
                    with st.spinner("IA lendo os valores numéricos da imagem..."):
                        arquivo_coleta.seek(0)
                        dados_extraidos = extrair_valores_de_imagem(arquivo_coleta, gemini_key)
                        if dados_extraidos and 'erro' not in dados_extraidos:
                            st.session_state['dados_extraidos'] = dados_extraidos
                            st.success("✅ Valores extraídos com sucesso! Copie os valores abaixo para os campos da barra lateral.")
                        elif dados_extraidos and 'erro' in dados_extraidos:
                            st.error(f"Erro na extração: {dados_extraidos['erro']}")
                        else:
                            st.warning("Não foi possível extrair os valores. Verifique a imagem.")
            else:
                st.info("Configure a chave Gemini API na barra lateral para habilitar a extração automática.")
    
    with col_col2:
        st.markdown("##### 📊 Valores Extraídos (Referência Interna)")
        
        dados = st.session_state.get('dados_extraidos', {})
        
        if dados:
            st.markdown("**Valores lidos pela IA da imagem de referência:**")
            
            cw = dados.get('call_wall', None)
            pw = dados.get('put_wall', None)
            zg = dados.get('zero_gamma', None)
            sp = dados.get('spot', None)
            
            # Mostrar em cards internos
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Call Wall → Z-CE", f"{cw}" if cw else "N/A")
                st.metric("Zero Gamma → ER", f"{zg}" if zg else "N/A")
            with col_b:
                st.metric("Put Wall → Z-AE", f"{pw}" if pw else "N/A")
                st.metric("Spot Lido", f"{sp}" if sp else "N/A")
                
            st.info("""💡 **Como usar estes valores:**
            \n1. Copie o **Call Wall** → cole em **Z-CE** na barra lateral
            \n2. Copie o **Put Wall** → cole em **Z-AE** na barra lateral
            \n3. Copie o **Zero Gamma** → cole em **ER** na barra lateral
            \n4. Copie o **Spot** → cole em **Preço Ajuste/Spot** na barra lateral
            \n5. O app converte automaticamente para a escala do seu CFD!""")
            
            if st.button("🗑️ Limpar Dados Extraídos", use_container_width=True):
                st.session_state['dados_extraidos'] = {}
                st.rerun()
        else:
            st.info("Carregue um print de referência e clique em 'Extrair Valores' para ver os dados aqui.")
        
        # Histórico de snapshots
        st.markdown("---")
        st.markdown("##### 🕐 Histórico de Snapshots Diários")
        if os.path.exists(SNAPSHOT_FILE):
            try:
                with open(SNAPSHOT_FILE, 'r', encoding='utf-8') as f:
                    snaps = json.load(f)
                if snaps:
                    df_snaps = pd.DataFrame(snaps)
                    st.dataframe(df_snaps[['timestamp','ativo','zce','zae','er','vje']].tail(10), use_container_width=True)
                    with open(SNAPSHOT_FILE, 'rb') as f_down:
                        st.download_button("📥 Exportar Histórico de Snapshots (JSON)", data=f_down,
                            file_name="snapshots_geniltrader.json", mime="application/json", use_container_width=True)
                else:
                    st.info("Nenhum snapshot salvo ainda.")
            except Exception:
                st.info("Nenhum snapshot salvo ainda.")
        else:
            st.info("Os snapshots são salvos automaticamente ao gerar relatórios.")

# -----------------------------------------------------------------------------
# ABA 3: AUDITORIA DE PERFORMANCE & BASE DE DADOS
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
# ABA 4: MANUAL DE OPERAÇÃO, GLOSSÁRIO E GUIA DIÁRIO
# -----------------------------------------------------------------------------
with tab_manual:
    st.header("📖 Manual Operacional, Glossário e Guia de Rotina Diária — GenilTrader [▲]")

    sec1, sec2, sec3 = st.tabs(["📋 Rotina Diária", "🔤 Glossário de Nomenclatura", "🔑 API & Configuração"])

    with sec1:
        st.markdown("""
## 🗓️ GUIA DE ROTINA DIÁRIA — PASSO A PASSO

> Siga este roteiro todos os dias antes da abertura de NY para gerar e publicar o Boletim Alpha GenilTrader [▲].

---

### ⏰ ETAPA 1 — Coleta dos Níveis (09h30 – 10h30 BRT)

1. Acesse seu site de referência de dados de opções
2. Anote os seguintes valores do **ativo principal (ex: Nasdaq / QQQ)**:
   - 📌 **Call Wall** (resistência principal) → vai virar Z-CE
   - 📌 **Put Wall** (suporte principal) → vai virar Z-AE
   - 📌 **Zero Gamma / Gamma Flip** (equilíbrio) → vai virar ER
   - 📌 **Preço atual / Spot** do ativo
   - 📌 **Máxima e Mínima esperada** → viram Fronteira Alfa e Ômega
3. Repita para o **ativo secundário (ex: S&P 500 / SPY)**
4. Anote os **Níveis de Volatilidade Semanal** do seu indicador ODTC
5. Anote os pontos de liquidez do seu **IPDA** (topos e fundos de janelas anteriores)

---

### 🖥️ ETAPA 2 — Abrir o App e Inserir os Dados (10h30 – 11h00 BRT)

1. Abra o terminal e execute: `streamlit run app.py`
2. Na **barra lateral**, configure:
   - **Data da Sessão** → data atual
   - **Classe de Ativo** → Índices / CFDs (USTEC / US500)
3. No **Painel de Coleta & Conversor Sigiloso**:
   - Cole o **Call Wall** no campo `Z-CE (Resistência)`
   - Cole o **Put Wall** no campo `Z-AE (Suporte)`
   - Cole o **Zero Gamma** no campo `ER (Eixo Rotação)`
   - Cole o **Spot** no campo `Preço Ajuste/Spot`
   - Cole as fronteiras nos campos `Fronteira Alfa` e `Fronteira Ômega`
4. Em **Níveis Complementares & Secundários**:
   - Cole o ponto IPDA no campo `VJE (Vetor Janelas IPDA)`
   - Cole o nível semanal ODTC no campo `Nível Secundário Volatilidade Semanal`
5. Selecione o **Filtro de Pressão Macroeconômico** (Neutro/Comprador/Vendedor)

> 💡 **Dica**: O app converte automaticamente os valores para a escala do USTEC/US500.

---

### 📸 ETAPA 3 — Capturar Prints Limpos dos Gráficos (10h45 – 11h10 BRT)

1. Abra o **TradingView** ou **MetaTrader**
2. Configure o gráfico do ativo operado (USTEC, US500, etc.)
3. **Remova todos os indicadores** da tela (deixe APENAS as velas)
4. Capture 2 prints:
   - **Print 1**: Gráfico Diário ou Semanal (contexto macro)
   - **Print 2**: Gráfico de 15 minutos (posição atual do preço)
5. ⚠️ **NUNCA capture prints do site de dados de opções** — isso expõe a fonte

---

### 🤖 ETAPA 4 — Gerar a Análise e o Relatório (11h10 – 11h30 BRT)

1. Na aba **"📝 Análise & Gerador Quant"**, clique em **"GERAR ANÁLISE POR IA"**
2. Carregue os prints dos gráficos na **galeria de imagens**
3. Aguarde a geração automática dos PDFs (PT e EN)
4. O app também gera automaticamente:
   - 📊 **Snapshot diário** (salvo internamente com timestamp)
   - 📸 **Card visual 1080x1080** para Instagram/WhatsApp
5. Revise o boletim no campo de texto e faça ajustes se necessário

---

### 📲 ETAPA 5 — Publicação (11h30 BRT ou conforme estratégia)

1. Baixe o **Card Visual PNG** (botão na área de análise)
2. Baixe os **PDFs PT e EN** (barra lateral ou botões da aba de análise)
3. Publique o **card** nas redes sociais (Instagram, Twitter/X, WhatsApp)
4. Envie os **PDFs** para o canal/grupo de assinantes
5. Registre o resultado do dia na aba **"📈 Auditoria"** ao final do pregão

---

### ⏰ Resumo do Horário Ideal

| Horário BRT | Ação |
| :--- | :--- |
| 09h30 – 10h30 | Coleta dos níveis de opções |
| 10h30 – 11h00 | Inserção dos dados no app |
| 10h45 – 11h10 | Captura de prints limpos dos gráficos |
| 11h10 – 11h30 | Geração da análise e relatório |
| 11h30+ | Publicação nas redes e envio aos assinantes |
        """)

    with sec2:
        st.markdown("""
## 🔤 GLOSSÁRIO COMPLETO DE NOMENCLATURA PROPRIETÁRIA GenilTrader [▲]

> Use este glossário para nunca se perder nos termos. À esquerda: o nome real da fonte. À direita: nosso nome exclusivo e seu significado operacional.

---

### Correspondência de Termos (Referência Interna)

| 🔒 Nossa Nomenclatura | Correspondência Real (NUNCA use publicamente) | O que representa na prática |
| :--- | :--- | :--- |
| **Z-CE** | Call Wall | Barreira de resistência teto onde institucionais vendem opções de compra (calls). Preço tende a desacelerar ou reverter ao testar este nível. |
| **Z-AE** | Put Wall | Barreira de suporte piso onde institucionais vendem opções de venda (puts). Preço tende a ser absorvido ou reverter ao testar este nível. |
| **ER** | Zero Gamma / Gamma Flip | Ponto neutro de equilíbrio. Acima = market makers compram quedas (bullish). Abaixo = market makers vendem altas (bearish). |
| **Fronteira Alfa** | Overnight High / Máxima esperada | Limite superior de volatilidade esperada para a sessão. |
| **Fronteira Ômega** | Overnight Low / Mínima esperada | Limite inferior de volatilidade esperada para a sessão. |
| **VJE** | IPDA Lookback / Draw on Liquidity | Pontos de liquidez (topos e fundos) de janelas temporais anteriores que o preço tende a buscar (varredura). |
| **Níveis Secundários de Volatilidade Semanal** | ODTC (regra CME) | Desvios percentuais de volatilidade calculados com base no preço de fechamento semanal. |
| **VAE** | Divergência SMT / Correlação | Quando dois ativos correlacionados (ex: USTEC e US500) divergem na direção, sinalizando manipulação ou falso rompimento. |
| **Vela de Absorção Crítica** | Candle de volume / GVF candle laranja | Candle que mostra absorção massiva de ordens em uma zona institucional. |
| **Gatilho de Ignição** | Candle de volume ou reversão | Vela que confirma o início de um movimento direcional a partir de uma zona. |

---

### Regimes de Preço

| Situação do Preço | Regime | Viés Operacional |
| :--- | :--- | :--- |
| Preço **acima do ER** | 🟢 Regime Comprador | Buscar compras em recuos rumo à Z-CE |
| Preço **abaixo do ER** | 🔴 Regime Vendedor | Buscar vendas em repiques rumo à Z-AE |
| Preço **dentro de ±0.3% do ER** | 🟡 Regime Neutro | Aguardar rompimento e confirmação do lado |

---

### Como Marcar no Gráfico

| Região | Cor da Linha | Tipo | Ação Esperada |
| :--- | :--- | :--- | :--- |
| **ER** | 🟡 Amarelo Ouro | Horizontal sólida | Ponto de equilíbrio — divisor de viés |
| **Z-CE** | 🔴 Vermelho | Horizontal sólida | Teto institucional — exaustão compradora |
| **Z-AE** | 🟢 Verde | Horizontal sólida | Piso institucional — absorção vendedora |
| **Fronteira Alfa** | 🟣 Roxo tracejado | Horizontal tracejada | Limite máximo de volatilidade |
| **Fronteira Ômega** | 🟣 Roxo tracejado | Horizontal tracejada | Limite mínimo de volatilidade |
| **VJE** | 🔵 Azul ciano | Horizontal tracejada | Alvo de varredura de liquidez |
| **Nível Secundário** | ⚪ Cinza claro | Horizontal fina | Barreira estatística complementar |
        """)

    with sec3:
        st.markdown("""
## 🔑 Configuração da API Gemini (IA Gratuita)

1. Acesse: [https://aistudio.google.com/](https://aistudio.google.com/)
2. Faça login com conta Google
3. Clique em **"Get API key"** → **"Create API key"**
4. Copie o código gerado (começa com `AIzaSy...`)
5. Cole no campo **"Gemini API Key"** na barra lateral do app

### Para uso permanente (Streamlit Cloud):
- Adicione nos *Secrets* do projeto: `GEMINI_API_KEY = "sua-chave"`

### Sem a chave:
- O app funciona normalmente com o **Motor Quant Nativo** (offline)
- A extração automática de valores da aba de coleta privada fica indisponível
        """)

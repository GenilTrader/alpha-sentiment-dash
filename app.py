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
# CONFIGURAÇÃO DA INTERFACE WEB (Estética Premium Dark)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="GenilTrader [▲] — Engine de Inteligência Quant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Customização CSS Avançada (Glassmorphism & Gold/Slate Palette)
st.markdown("""
    <style>
    .main-title { 
        font-size: 30px; 
        font-weight: 800; 
        color: #D4AF37; 
        margin-bottom: 2px; 
        font-family: 'Helvetica Neue', sans-serif;
        letter-spacing: -0.5px;
    }
    .sub-title { 
        font-size: 14px; 
        color: #94A3B8; 
        margin-bottom: 20px; 
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 10px;
    }
    .metric-title { font-size: 12px; color: #94A3B8; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 20px; color: #F8FAFC; font-weight: bold; }
    .metric-sub { font-size: 11px; color: #10B981; }
    div.stButton > button:first-child {
        background-color: #D4AF37 !important;
        color: #0F172A !important;
        font-weight: bold !important;
        font-size: 14px !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #F59E0B !important;
        transform: scale(1.01);
    }
    textarea { font-family: 'Courier New', Courier, monospace !important; font-size: 13px !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛡️ GENILTRADER [▲] — ENGINE DE INTELIGÊNCIA QUANT & ANÁLISE INSTITUCIONAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Mapeamento de Barreiras Macroeconômicas, Exaustão de Liquidez e Relatórios Multimodais para Qualquer Ativo (CFD)</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FUNÇÕES DE CÁLCULO QUANT E PROBABILIDADE INSTITUCIONAL
# -----------------------------------------------------------------------------
def calcular_regioes_e_probabilidade(spot, zce, zae, er, alfa=None, omega=None):
    """
    Calcula as distâncias percentuais, relação risco-retorno e probabilidades
    de exaustão/reação em cada zona institucional protegida.
    """
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

    # Determina o viés do regime atual em relação ao Eixo de Rotação (ER)
    if spot_val > er_val:
        vies = "Comprador (Acima do ER)"
        prob_testar_zce = max(40, min(92, 85 - abs(dist_zce_pct) * 5))
        prob_testar_zae = max(10, min(50, 30 - dist_zae_pct * 3))
    else:
        vies = "Vendedor (Abaixo do ER)"
        prob_testar_zae = max(40, min(92, 85 - abs(dist_zae_pct) * 5))
        prob_testar_zce = max(10, min(50, 30 - dist_zce_pct * 3))

    # Assimetria R:R aproximada para entrada no ER em direção à Z-CE ou Z-AE
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
# MOTOR DE IA INSTITUCIONAL (HÍBRIDO: GEMINI FREE API + ENGINE ALGORÍTMICA NATIVA)
# -----------------------------------------------------------------------------
def gerar_analise_ia(ativo_nome, spot, zce, zae, er, alfa, omega, macro_filtro, api_key=None, list_images=None):
    """
    Gera o relatório analítico bilingue [PT] e [EN] com nomenclatura protegida.
    Prioriza a API do Google Gemini se a chave for fornecida; caso contrário,
    utiliza o motor quant algorítmico nativo (100% gratuito e offline).
    """
    calc = calcular_regioes_e_probabilidade(spot, zce, zae, er, alfa, omega)
    
    # SYSTEM PROMPT INSTITUCIONAL RIGOROSO
    prompt_base = f"""
Você é o Diretor Quant Global & Arquiteto Chefe da metodologia proprietária GenilTrader [▲].
Sua tarefa é gerar uma análise técnica e institucional cirúrgica para o ativo/CFD: {ativo_nome}.

DADOS CONTEXTUAIS DA SESSÃO:
- Preço Spot / Ajuste Inicial: {spot}
- Z-CE (Zona de Contração Executiva): {zce} (Distância: {calc.get('dist_zce_pct', 0)}% | Probabilidade de Teste: {calc.get('prob_zce', 0)}%)
- Z-AE (Zona de Absorção Executiva): {zae} (Distância: {calc.get('dist_zae_pct', 0)}% | Probabilidade de Teste: {calc.get('prob_zae', 0)}%)
- ER (Eixo de Rotação Algorítmico): {er} (Viés Atual: {calc.get('vies', 'Neutro')})
- Fronteira Alfa (Máxima): {alfa if alfa else 'N/A'}
- Fronteira Ômega (Mínima): {omega if omega else 'N/A'}
- Filtro de Pressão Macroeconômica: {macro_filtro}
- Relação Risco:Retorno Estimada (R:R): 1:{calc.get('rr_ratio', 1.0)}

REGRAS DE SEGURANÇA E TERMINOLOGIA PROTEGIDA (OBRIGATÓRIO):
Está estritamente PROIBIDO usar termos de varejo públicos como "GEX", "Gamma", "Call Wall", "Put Wall", "Zero Gamma", "Overnight High/Low".
Use EXCLUSIVAMENTE a Nomenclatura Proprietária:
- Call Wall -> Z-CE (Zona de Contração Executiva / Executive Contraction Zone)
- Put Wall -> Z-AE (Zona de Absorção Executiva / Executive Absorption Zone)
- Zero Gamma -> ER (Eixo de Rotação / Rotation Axis)
- High/Low -> Fronteira Alfa (Máxima) e Fronteira Ômega (Mínima) / Alpha & Omega Frontiers
- Velas de Volume -> Velas de Absorção Crítica (Critical Absorption Candles)
- Divergência SMT/Preço -> Vetor de Arbitragem Estatística (VAE / Statistical Arbitrage Vector)

FORMATO EXATO EXIGIDO PARA A RESPOSTA (Copie a estrutura com [PT] e [EN]):

## 🔒 1. ARQUITETURA DE REGIMES DE PREÇO / PRICE REGIME ARCHITECTURE
[PT]
(Escreva a análise detalhada em Português sobre o comportamento projetado para {ativo_nome} na Z-CE, Z-AE e ER).
[EN]
(Escreva a mesma análise traduzida para o Inglês Institucional de Hedge Fund).

## ⚔️ 2. ZONAS DE EXAUSTÃO DIÁRIA E VETORES DE ARBITRAGEM / EXHAUSTION ZONES & ARBITRAGE VECTORS
[PT]
(Instruções de como rastrear o VAE e a reação esperada nas Fronteiras Alfa/Ômega e exaustão no gráfico intraday).
[EN]
(As mesmas instruções em Inglês institucional).

## 🛡️ 3. CLÁUSULA DE EXECUÇÃO E ASSIMETRIA MATEMÁTICA / EXECUTION RULES & ASYMMETRY
[PT]
(Regras estritas de gerenciamento de risco no pavio do candle de gatilho e invalidação técnica).
[EN]
(As mesmas regras em Inglês institucional).
"""

    # Se a chave da API Gemini foi informada e a SDK está disponível
    if api_key and HAS_GENAI:
        try:
            client = genai.Client(api_key=api_key)
            contents = []
            
            # Se houver imagens carregadas, insere no contexto multimodal para visão computacional
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

    # MOTOR QUANT ALGORÍTMICO NATIVO (Offline / Free Fallback)
    vies_str = calc.get('vies', 'Neutro')
    rr_str = f"1:{calc.get('rr_ratio', 1.0)}"
    zce_prob = calc.get('prob_zce', 50)
    zae_prob = calc.get('prob_zae', 50)

    texto_nativo = f"""[PT]
1. ARQUITETURA DE REGIMES DE PREÇO
O ativo {ativo_nome} opera sob o regime de {vies_str}. O Eixo de Rotação (ER) cravado em {er} atua como o principal ponto de equilíbrio algorítmico da sessão. A sustentação acima do ER mantém a probabilidade de {zce_prob}% para o teste da Z-CE (Zona de Contração Executiva) em {zce}, onde projeta-se forte absorção de ordens por parte das grandes tesourarias. Inversamente, a perda sustentada do ER acionará a distribuição de liquidez em direção à Z-AE (Zona de Absorção Executiva) em {zae} (probabilidade de {zae_prob}%).

2. ZONAS DE EXAUSTÃO DIÁRIA E VETORES DE ARBITRAGEM
Aguardaremos o preço testar os limites das regiões institucionais (Fronteira Alfa {alfa if alfa else ''} ou Fronteira Ômega {omega if omega else ''}). O gatilho operacional de alta assimetria no gráfico intraday ocorrerá estritamente com o aparecimento de uma Vela de Absorção Crítica combinada com o acionamento do Vetor de Arbitragem Estatística (VAE) — caracterizado pelo descolamento do {ativo_nome} em relação ao filtro macroeconômico ({macro_filtro}).

3. CLÁUSULA DE EXECUÇÃO E ASSIMETRIA MATEMÁTICA
Mantenha o risco estritamente limitado com assimetria estimada de {rr_str}. A invalidação técnica da tese ocorrerá caso o preço confirme o fechamento de uma barra cheia além das zonas de exaustão demarcadas. Não persiga o preço fora das regiões operacionais proprietárias.

[EN]
1. PRICE REGIME ARCHITECTURE
The asset {ativo_nome} is trading under a {vies_str} regime. The Rotation Axis (ER) mapped at {er} serves as the core algorithmic equilibrium point for the session. Sustained price action above the ER maintains a {zce_prob}% probability of retesting the Z-CE (Executive Contraction Zone) at {zce}, where heavy institutional order absorption is anticipated. Conversely, losing the ER will trigger liquidity distribution down to the Z-AE (Executive Absorption Zone) at {zae} (probability of {zae_prob}%).

2. EXHAUSTION ZONES & ARBITRAGE VECTORS
We will monitor price action near institutional boundary zones (Alpha Frontier {alfa if alfa else ''} / Omega Frontier {omega if omega else ''}). The high-asymmetry execution trigger on the intraday chart will strictly require the print of a Critical Absorption Candle aligned with the Statistical Arbitrage Vector (VAE) — confirmed by {ativo_nome} price divergence against the systemic macro filter ({macro_filtro}).

3. EXECUTION RULES & ASYMMETRY
Keep risk strictly contained with an estimated R:R ratio of {rr_str}. Technical invalidation is mandatory if a full candle body closes beyond the defined exhaustion zones. Do not chase price action outside our proprietary operational zones."""

    return texto_nativo

# -----------------------------------------------------------------------------
# FUNÇÃO DE COMPILAÇÃO DO PDF (REPORTLAB + PILLOW compression + colWidths=[106.4]*5)
# -----------------------------------------------------------------------------
def compilar_pdf(filename, lang, titulo, sub_titulo, label_ativo, label_ajuste, label_zce, label_zae, label_er, data_h, u_spot, u_zce, u_zae, u_er, s_spot, s_zce, s_zae, s_er, v_macro, analise_text, up_files, lista_legendas):
    """
    Gera síncronamente os relatórios em PDF com formatação rígida de 532pt
    e tratamento de imagem via Pillow para otimização no Streamlit Cloud.
    """
    doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    style_h1 = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#0F172A'), spaceAfter=3)
    style_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#64748B'), spaceAfter=14)
    style_h2 = ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#D4AF37'), spaceBefore=12, spaceAfter=6)
    style_body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=14, textColor=colors.HexColor('#334155'), spaceAfter=5)
    style_caption = ParagraphStyle('Caption', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#64748B'), alignment=1, spaceBefore=4, spaceAfter=10)
    
    elements = []
    elements.append(Paragraph(titulo, style_h1))
    elements.append(Paragraph(f"{sub_titulo} — Date/Data: {data_h}", style_sub))
    
    elements.append(Paragraph("🎯 ARQUITETURA DE REGIMES DE PREÇO / PRICE REGIME", style_h2))
    
    table_data = [
        [Paragraph(f"<b>{label_ativo}</b>", style_body), Paragraph(f"<b>{label_ajuste}</b>", style_body), Paragraph(f"<b>{label_zce}</b>", style_body), Paragraph(f"<b>{label_zae}</b>", style_body), Paragraph(f"<b>{label_er}</b>", style_body)],
        [Paragraph(f"<b>Vetor Principal</b>", style_body), str(u_spot), str(u_zce), str(u_zae), str(u_er)],
        [Paragraph(f"<b>Vetor Secundário</b>", style_body), str(s_spot), str(s_zce), str(s_zae), str(s_er)]
    ]
    
    # 5 colunas x 106.4 pt = 532 pt (Largura exata da folha Letter com 40pt de margem de cada lado)
    prop_table = Table(table_data, colWidths=[106.4, 106.4, 106.4, 106.4, 106.4])
    prop_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F8FAFC')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor('#D4AF37')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0'))
    ]))
    elements.append(prop_table)
    elements.append(Spacer(1, 6))
    
    label_macro = "Filtro de Pressão Sistêmica Global" if lang == "PT" else "Global Systemic Pressure Filter"
    elements.append(Paragraph(f"<b>{label_macro}:</b> {v_macro}", style_body))
    
    elements.append(Paragraph("📝 DIRETRIZES TÁTICAS OPERACIONAIS / OPERATIONAL THESES", style_h2))
    
    # Parser inteligente de texto para extrair os blocos [PT] ou [EN]
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
            
    # Fallback seguro se o usuário não usou as tags [PT] / [EN]
    if not texto_adicionado:
        for l in linhas:
            if l.strip() and not l.strip().startswith("["):
                elements.append(Paragraph(l, style_body))
                
    # Inserção de imagens com resize via Pillow (largura máxima 500pt)
    if up_files:
        elements.append(Paragraph("🖼️ VISUALIZAÇÃO E ESTRUTURAÇÃO DO MAPA VISUAL", style_h2))
        for idx, file in enumerate(up_files):
            try:
                temp_img_path = f"temp_chart_{lang}_{idx}.jpg"
                file.seek(0)
                img = Image.open(file)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
                img.save(temp_img_path, "JPEG", quality=85)
                
                max_width = 500
                w, h = img.size
                aspect = h / w if w > 0 else 0.75
                
                elements.append(RLImage(temp_img_path, width=max_width, height=max_width * aspect))
                legenda_atual = lista_legendas[idx] if idx < len(lista_legendas) else ""
                elements.append(Paragraph(f"<b>Figura {idx+1}:</b> {legenda_atual}", style_caption))
                elements.append(Spacer(1, 6))
            except Exception as err:
                st.error(f"Erro ao processar imagem {idx+1}: {err}")
        
    elements.append(Spacer(1, 12))
    aviso_text = "PROPRIEDADE INTELECTUAL RETIDA — DISTRIBUIÇÃO PROIBIDA EXTRA ASSINANTES" if lang == "PT" else "PROPRIETARY INTELLECTUAL PROPERTY — UNAUTHORIZED DISTRIBUTION IS STRICTLY PROHIBITED"
    style_aviso = ParagraphStyle('Aviso', parent=styles['Normal'], fontName='Helvetica-BoldOblique', fontSize=7.5, textColor=colors.HexColor('#94A3B8'), alignment=1)
    elements.append(Paragraph(f"{aviso_text} — GENILTRADER [▲]", style_aviso))
    
    doc.build(elements)

# -----------------------------------------------------------------------------
# SIDEBAR DE CONFIGURAÇÃO & CONTROLE UNIVERSAL
# -----------------------------------------------------------------------------
st.sidebar.header("🎛️ Painel de Controle GenilTrader")

# 1. Configuração da API Key Gratuita do Gemini
st.sidebar.subheader("🔑 Conexão IA (Google Gemini Free)")
gemini_key = st.sidebar.text_input(
    "Gemini API Key (Opcional)",
    type="password",
    help="Cole aqui sua chave gratuita do Google AI Studio. Se em branco, o sistema usará a Engine Quant Algorítmica nativa!"
)
st.sidebar.markdown("👉 [Obter chave gratuita no Google AI Studio](https://aistudio.google.com/)")

st.sidebar.markdown("---")
data_hoje = st.sidebar.text_input("Data da Sessão", datetime.datetime.now().strftime("%d/%m/%Y"))

# 2. Seletor de Ativo Universal (CFD / Ações / Crypto / Forex)
st.sidebar.subheader("🎯 Seletor de Ativo / CFD")
categoria_ativo = st.sidebar.selectbox("Classe de Ativo:", ["Índices / CFDs (USTEC, US500)", "Commodities (XAUUSD/Ouro, USOIL)", "Forex (EURUSD, GBPUSD)", "Ações / CFDs (NVDA, AAPL)", "Crypto (BTCUSD, ETHUSD)", "Outro / Personalizado"])

if categoria_ativo == "Índices / CFDs (USTEC, US500)":
    ativo_p1 = "USTEC (QQQ)"
    ativo_p2 = "US500 (SPY)"
elif categoria_ativo == "Commodities (XAUUSD/Ouro, USOIL)":
    ativo_p1 = "XAUUSD (Ouro)"
    ativo_p2 = "USOIL (WTI)"
elif categoria_ativo == "Forex (EURUSD, GBPUSD)":
    ativo_p1 = "EURUSD"
    ativo_p2 = "GBPUSD"
elif categoria_ativo == "Ações / CFDs (NVDA, AAPL)":
    ativo_p1 = "NVDA"
    ativo_p2 = "AAPL"
elif categoria_ativo == "Crypto (BTCUSD, ETHUSD)":
    ativo_p1 = "BTCUSD"
    ativo_p2 = "ETHUSD"
else:
    ativo_p1 = st.sidebar.text_input("Ativo Principal:", "EURUSD")
    ativo_p2 = st.sidebar.text_input("Ativo Correlacionado:", "GBPUSD")

st.sidebar.markdown(f"**Parâmetros: {ativo_p1}**")
u_spot_in = st.sidebar.text_input(f"{ativo_p1} — Preço Spot/Ajuste", "$720.32")
u_zce_in  = st.sidebar.text_input(f"{ativo_p1} — Z-CE (Contração)", "$725.00")
u_zae_in  = st.sidebar.text_input(f"{ativo_p1} — Z-AE (Absorção)", "$700.00")
u_er_in   = st.sidebar.text_input(f"{ativo_p1} — ER (Eixo de Rotação)", "$718.40")
u_alfa_in = st.sidebar.text_input(f"{ativo_p1} — Fronteira Alfa (Máxima)", "$728.50")
u_omega_in= st.sidebar.text_input(f"{ativo_p1} — Fronteira Ômega (Mínima)", "$695.00")

st.sidebar.markdown(f"**Parâmetros: {ativo_p2}**")
s_spot_in = st.sidebar.text_input(f"{ativo_p2} — Preço Spot/Ajuste", "$762.33")
s_zce_in  = st.sidebar.text_input(f"{ativo_p2} — Z-CE (Contração)", "$767.00")
s_zae_in  = st.sidebar.text_input(f"{ativo_p2} — Z-AE (Absorção)", "$760.00")
s_er_in   = st.sidebar.text_input(f"{ativo_p2} — ER (Eixo de Rotação)", "$763.54")

st.sidebar.subheader("📺 Vetor Macroeconômico")
vetor_macro_pt = st.sidebar.selectbox("Filtro de Pressão (PT)", ["Regime de Neutralidade / Lateral", "Pressão Vendedora Ativa", "Pressão Compradora Ativa"])

st.sidebar.markdown("---")
bt_processar = st.sidebar.button("🔥 EMITIR BOLETINS INTERNACIONAIS", use_container_width=True)
st.sidebar.markdown("---")

# Seção de Download dos PDFs na Sidebar
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
    "📖 Manual de Operação & Guia Gemini"
])

# -----------------------------------------------------------------------------
# ABA 1: ANÁLISE DA MANHÃ & GERADOR QUANT MULTIMODAL
# -----------------------------------------------------------------------------
with tab_analise:
    # 1. Cards de Métricas Quant em Destaque
    calc_res = calcular_regioes_e_probabilidade(u_spot_in, u_zce_in, u_zae_in, u_er_in, u_alfa_in, u_omega_in)
    
    st.subheader(f"📊 Diagnóstico em Tempo Real — {ativo_p1}")
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

    # 2. Área de Texto e Galeria de Prints
    col_text, col_graph = st.columns(2)

    with col_text:
        st.subheader("📝 Diretrizes Táticas Operacionais")
        
        # Botão para invocar a IA Quant
        if st.button("🤖 GERAR ANÁLISE POR IA (MULTIMODAL & NATIVA)", use_container_width=True):
            with st.spinner("Analisando métricas quant e imagens com a IA..."):
                texto_gerado = gerar_analise_ia(
                    ativo_nome=ativo_p1,
                    spot=u_spot_in,
                    zce=u_zce_in,
                    zae=u_zae_in,
                    er=u_er_in,
                    alfa=u_alfa_in,
                    omega=u_omega_in,
                    macro_filtro=vetor_macro_pt,
                    api_key=gemini_key,
                    list_images=st.session_state.get('uploaded_files_cache', None)
                )
                st.session_state['analise_texto_key'] = texto_gerado
                st.success("Análise gerada com sucesso!")

        analise_texto = st.text_area(
            "Boletim Proprietário Bilíngue",
            value=st.session_state.get('analise_texto_key', ""),
            height=430,
            placeholder="Clique no botão acima para a IA gerar automaticamente ou cole suas diretrizes aqui contendo as tags [PT] e [EN]..."
        )

    with col_graph:
        st.subheader("🖼️ Galeria de Prints e Comparação Gráfica")
        st.caption("Selecione ou arraste MÚLTIPLOS prints gráficos simultaneamente (ex: 15min e 5min):")
        
        uploaded_files = st.file_uploader(
            "Arrastar múltiplos prints gráficos aqui",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.session_state['uploaded_files_cache'] = uploaded_files
            st.info(f"📸 {len(uploaded_files)} gráfico(s) carregado(s). Insira as legendas abaixo:")

        # Correção estrita de recuo: Legendagem em linhas simples empilhadas (sem bloco 'with c_l1:')
        legendas_pt = []
        legendas_en = []

        if uploaded_files:
            for idx, file in enumerate(uploaded_files):
                st.markdown(f"**Figura {idx+1}: {file.name}**")
                leg_pt = st.text_input(f"Legenda (PT) #{idx+1}", f"Mapeamento Operacional {ativo_p1} - Gráfico {idx+1}", key=f"leg_pt_{idx}")
                leg_en = st.text_input(f"Caption (EN) #{idx+1}", f"Operational Mapping {ativo_p1} - Chart {idx+1}", key=f"leg_en_{idx}")
                legendas_pt.append(leg_pt)
                legendas_en.append(leg_en)

    # 3. Processamento de PDF ao clicar na Sidebar
    if bt_processar:
        if not analise_texto.strip():
            st.error("⚠️ Insira ou gere o texto da análise antes de emitir os boletins!")
        else:
            with st.spinner("Compilando relatórios PDF em Português e Inglês..."):
                vetor_macro_en = "Neutral Regime / Lateral" if "Neutralidade" in vetor_macro_pt else ("Active Selling Pressure" if "Vendedora" in vetor_macro_pt else "Active Buying Pressure")
                
                # Compilar PDF Português
                compilar_pdf(
                    filename="boletim_alfa_PT.pdf",
                    lang="PT",
                    titulo=f"BOLETIM ALFA — {ativo_p1}",
                    sub_titulo="Relatório Quantitativo Institucional Exclusivo",
                    label_ativo="Ativo / CFD",
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

                # Compilar PDF Inglês
                compilar_pdf(
                    filename="boletim_alfa_EN.pdf",
                    lang="EN",
                    titulo=f"ALPHA BULLETIN — {ativo_p1}",
                    sub_titulo="Exclusive Institutional Quantitative Report",
                    label_ativo="Asset / CFD",
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

                st.success("🔥 BOLETIM PT E BOLETIM EN GERADOS COM SUCESSO! Baixe na barra lateral.")

# -----------------------------------------------------------------------------
# ABA 2: AUDITORIA DE PERFORMANCE & BASE DE DADOS HÍBRIDA
# -----------------------------------------------------------------------------
with tab_auditoria:
    st.subheader("📈 Auditoria de Performance & Banco de Dados de Confluência")
    st.caption("Registre e monitore a taxa de assertividade por região institucional para aperfeiçoar sua base de cálculo.")
    
    # Carregar ou criar histórico local CSV
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
        reg_regiao = st.selectbox("Região de Reação do Preço:", ["Z-CE (Zona Contração)", "Z-AE (Zona Absorção)", "ER (Eixo Rotação)", "Fronteira Alfa", "Fronteira Ômega"])
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
            st.warning("Nenhum trade registrado ainda. Registre as sessões acima para alimentar sua base de cálculo.")

# -----------------------------------------------------------------------------
# ABA 3: MANUAL DE OPERAÇÃO & GUIA DE INSERÇÃO DA CHAVE GEMINI
# -----------------------------------------------------------------------------
with tab_manual:
    st.header("📖 Manual Operacional e Guia Completo da Chave Gratuita Gemini")
    
    st.markdown("""
    ### 🔑 1. Como Obter a Chave Gratuita do Google Gemini (Passo a Passo)

    Você **NÃO precisa de API paga** nem de cartão de crédito para usar a inteligência artificial do Google no aplicativo!

    1. Acesse o site oficial do **Google AI Studio**: [https://aistudio.google.com/](https://aistudio.google.com/)
    2. Faça login com qualquer **conta Google (Gmail)** gratuita.
    3. No menu lateral esquerdo ou superior, clique no botão **"Get API key"** (Obter chave de API).
    4. Clique em **"Create API key"** (Criar chave de API) e selecione qualquer projeto padrão sugerido.
    5. Copie a chave gerada (um código longo começando com `AIzaSy...`).
    6. **Inserção no App**:
       - **Local / Teste**: Cole a chave diretamente no campo **"Gemini API Key (Opcional)"** na barra lateral esquerda deste aplicativo.
       - **Streamlit Cloud / GitHub**: Adicione nos *Secrets* do aplicativo no menu da nuvem (`GEMINI_API_KEY = "sua-chave"`).

    ---

    ### 🎯 2. Como Funciona a Calculadora e Por Que Aponta as Regiões de Interesse?

    O **GenilTrader Engine** foi projetado para traduzir a dinâmica da **liquidez de grandes tesourarias institucionais** e derivativos para qualquer ativo do mercado (CFDs, Índices, Forex, Crypto ou Ações).

    #### 🛡️ As Regiões de Atenção Protegidas:
    - **Z-CE (Zona de Contração Executiva)**:
      - *O porquê:* Representa a barreira teto onde grandes institucionais posicionam travas de proteção ou venda. Quando o preço se aproxima da Z-CE, o volume tende a desacelerar e ocorrer forte absorção.
    - **Z-AE (Zona de Absorção Executiva)**:
      - *O porquê:* É a zona de suporte estrutural profundo onde ocorrem compras massivas de proteção. Atua como um "chão" temporário de liquidez no intraday.
    - **ER (Eixo de Rotação Algorítmico)**:
      - *O porquê:* É o nível neutro de equilíbrio de gama/opções e preço justo (Fair Value). Se o preço está **acima do ER**, o viés intraday é predominantemente comprador; se está **abaixo do ER**, o viés se torna vendedor.
    - **Fronteiras Alfa (Máxima) e Ômega (Mínima)**:
      - *O porquê:* Correspondem aos extremos de volatilidade esperada da sessão. O teste dessas extremidades oferece as maiores assimetrias de Risco:Retorno (R:R).

    ---

    ### 🖼️ 3. Análise Multimodal de Múltiplos Gráficos
    Você pode enviar **mais de um print simultaneamente** (ex: um gráfico de 15 minutos mostrando os níveis macro e um de 5 minutos mostrando a exaustão de velas).
    A IA processa a visão computacional de todas as imagens juntas para identificar **divergências de arbitragem (VAE)** e sugerir entradas assimétricas.
    """)

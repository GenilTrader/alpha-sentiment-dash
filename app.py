import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image
import os

# Configuração da Interface Web (Estética Premium Dark)
st.set_page_config(page_title="GenilTrader — Engine de Relatórios", layout="wide")

# Customização CSS Avançada para consertar contraste, botões e espaçamentos
st.markdown("""
    <style>
    .main-title { font-size:32px; font-weight:bold; color:#D4AF37; margin-bottom:5px; font-family:'Helvetica Neue', sans-serif; }
    .sub-title { font-size:15px; color:#94A3B8; margin-bottom:25px; }
    div.stButton > button:first-child {
        background-color: #D4AF37 !important;
        color: #0F172A !important;
        font-weight: bold !important;
        font-size: 16px !important;
        border-radius: 6px !important;
        border: none !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #F59E0B !important;
        transform: scale(1.01);
    }
    textarea { font-family: 'Courier New', Courier, monospace !important; font-size: 14px !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛡️ GENILTRADER [▲] — ENGINE DE RELATÓRIOS BILÍNGUE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Algoritmo Quant Proprietário — Mapeamento Internacional de Barreiras Macroeconômicas</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR DE INPUTS (Carregado com os dados reais do seu print da GEX)
# -----------------------------------------------------------------------------
st.sidebar.header("🎛️ Parâmetros do Pré-Mercado")
data_hoje = st.sidebar.text_input("Data da Sessão", pd.Timestamp.now().strftime("%d/%m/%Y"))

st.sidebar.subheader("🎯 Níveis Canal USTEC (QQQ)")
ustec_spot = st.sidebar.text_input("Preço de Ajuste Inicial", "$720.32")
ustec_zce  = st.sidebar.text_input("Z-CE (Zona de Contração)", "$725.00")
ustec_zae  = st.sidebar.text_input("Z-AE (Zona de Absorção)", "$700.00")
ustec_er   = st.sidebar.text_input("ER (Eixo de Rotação)", "$718.40")

st.sidebar.subheader("🎯 Níveis Canal US500 (SPY)")
us500_spot = st.sidebar.text_input("Preço de Referência Base", "$762.33")
us500_zce  = st.sidebar.text_input("Z-CE (Zona de Contração)", "$767.00")
us500_zae  = st.sidebar.text_input("Z-AE (Zona de Absorção)", "$760.00")
us500_er   = st.sidebar.text_input("ER (Eixo de Rotação)", "$763.54")

st.sidebar.subheader("📺 Vetor Macroeconômico")
vetor_macro_pt = st.sidebar.selectbox("Filtro de Pressão (PT)", ["Regime de Neutralidade / Lateral", "Pressão Vendedora Ativa", "Pressão Compradora Ativa"])
vetor_macro_en = "Neutral Regime / Lateral" if "Neutralidade" in vetor_macro_pt else ("Active Selling Pressure" if "Vendedora" in vetor_macro_pt else "Active Buying Pressure")

# -----------------------------------------------------------------------------
# CORPO PRINCIPAL
# -----------------------------------------------------------------------------
col_text, col_graph = st.columns(2)

with col_text:
    st.subheader("📝 Diretrizes Ocultas (Claude Engine)")
    st.caption("Cole o texto gerado pela nova Skill Internacional do Claude (com as marcações [PT] e [EN]):")
    analise_texto = st.text_area("Boletim Proprietário", height=380, placeholder="1. ARQUITETURA DE REGIMES DE PREÇO...\n[PT] O Vetor USTEC...\n[EN] The USTEC Vector...")

with col_graph:
    st.subheader("🖼️ Mapeamento Gráfico do Vetor")
    st.caption("Anexe o print limpo com as suas linhas manuais plotadas:")
    uploaded_file = st.file_uploader("Arrastar imagem do gráfico aqui", type=["png", "jpg", "jpeg"])
    
    anotacao_grafico_pt = "Regiões táticas identificadas através do cruzamento das Fronteiras Alfa/Ômega e Vetores de Arbitragem."
    anotacao_grafico_en = "Tactical zones identified through the intersection of Alpha/Omega Frontiers and Arbitrage Vectors."
    
    if uploaded_file:
        st.image(uploaded_file, caption="Mapeamento Estrutural Carregado", use_container_width=True)
        anotacao_grafico_pt = st.text_input("📌 Legenda do Gráfico (Português):", anotacao_grafico_pt)
        anotacao_grafico_en = st.text_input("📌 Legenda do Gráfico (Inglês):", anotacao_grafico_en)

# -----------------------------------------------------------------------------
# FUNÇÃO DE COMPILAÇÃO ISOLADA DO PDF
# -----------------------------------------------------------------------------
def compilar_pdf(filename, lang, titulo, sub_titulo, label_ativo, label_ajuste, label_zce, label_zae, label_er, v_macro, legenda_img):
    doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    style_h1 = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=19, textColor=colors.HexColor('#0F172A'), spaceAfter=3)
    style_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#64748B'), spaceAfter=15)
    style_h2 = ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#D4AF37'), spaceBefore=14, spaceAfter=6)
    style_body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=14, textColor=colors.HexColor('#334155'), spaceAfter=5)
    style_caption = ParagraphStyle('Caption', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#64748B'), alignment=1, spaceBefore=4)
    
    elements = []
    elements.append(Paragraph(titulo, style_h1))
    elements.append(Paragraph(f"{sub_titulo} — Date/Data: {data_hoje}", style_sub))
    
    # Tabela com tradução limpa das colunas
    elements.append(Paragraph("🎯 ARQUITETURA DE REGIMES DE PREÇO / PRICE REGIME", style_h2))
    table_data = [
        [Paragraph(f"<b>{label_ativo}</b>", style_body), Paragraph(f"<b>{label_ajuste}</b>", style_body), Paragraph(f"<b>{label_zce}</b>", style_body), Paragraph(f"<b>{label_zae}</b>", style_body), Paragraph(f"<b>{label_er}</b>", style_body)],
        [Paragraph("<b>Vetor USTEC</b> (QQQ)", style_body), ustec_spot, ustec_zce, ustec_zae, ustec_er],
        [Paragraph("<b>Vetor US500</b> (SPY)", style_body), us500_spot, us500_zce, us500_zae, us500_er]
    ]
    
    prop_table = Table(table_data, colWidths=[110, 95, 105, 105, 105])
    prop_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F8FAFC')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor('#D4AF37')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0'))
    ]))
    elements.append(prop_table)
    elements.append(Spacer(1, 5))
    
    # Filtro Macro
    label_macro = "Filtro de Pressão Sistêmica Global" if lang == "PT" else "Global Systemic Pressure Filter"
    elements.append(Paragraph(f"<b>{label_macro}:</b> {v_macro}", style_body))
    
    # Filtro Inteligente do Bloco de Texto correspondente ao Idioma
    elements.append(Paragraph("📝 DIRETRIZES TÁTICAS OPERACIONAIS / OPERATIONAL THESES", style_h2))
    linhas = analise_texto.split('\n')
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
        # Se não houver tags de separação, joga o texto inteiro na caixa
        for l in linhas:
            if l.strip() and not l.strip().startswith("["):
                elements.append(Paragraph(l, style_body))
                
    # Gráfico
    if uploaded_file:
        elements.append(Paragraph("🖼️ VISUALIZAÇÃO E ESTRUTURAÇÃO DO MAPA", style_h2))
        temp_img_path = f"temp_chart_{lang}.png"
        img = Image.open(uploaded_file)
        img.save(temp_img_path)
        
        max_width = 520
        w, h = img.size
        aspect = h / w
        elements.append(RLImage(temp_img_path, width=max_width, height=max_width * aspect))
        elements.append(Paragraph(f"<b>Figura 1:</b> {legenda_img}", style_caption))
        
    # Aviso de Direitos Autorais
    elements.append(Spacer(1, 15))
    aviso_text = "PROPRIEDADE INTELECTUAL RETIDA — DISTRIBUIÇÃO PROIBIDA EXTRA ASSINANTES" if lang == "PT" else "PROPRIETARY INTELLECTUAL PROPERTY — UNAUTHORIZED DISTRIBUTION IS STRICTLY PROHIBITED"
    style_aviso = ParagraphStyle('Aviso', parent=styles['Normal'], fontName='Helvetica-BoldOblique', fontSize=7.5, textColor=colors.HexColor('#94A3B8'), alignment=1)
    elements.append(Paragraph(f"{aviso_text} — GENILTRADER [▲]", style_aviso))
    
    doc.build(elements)

# -----------------------------------------------------------------------------
# BOTÕES DE EXECUÇÃO E PROCESSAMENTO
# -----------------------------------------------------------------------------
st.markdown("---")
if st.button("🔥 PROCESSAR COMPILAÇÃO DOS BOLETIMS ALFA (PT & EN)", use_container_width=True):
    # Compila a versão em Português
    compilar_pdf("boletim_alfa_PT.pdf", "PT", "GENILTRADER — BOLETIM ALFA", "Estudo Proprietário Pré-Mercado — Sessão de NY", "Ativo Analisado", "Ajuste Inicial", "Z-CE (Teto)", "Z-AE (Chão)", "ER (Eixo Rotação)", vetor_macro_pt, anotacao_grafico_pt)
    
    # Compila a versão em Inglês

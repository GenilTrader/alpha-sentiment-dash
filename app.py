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

st.markdown('<div class="main-title">🛡️ GENILTRADER [▲] — ENGINE DE RELATÓRIOS</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Algoritmo Quant Proprietário — Mapeamento de Barreiras Macroeconômicas e Vetores de Arbitragem</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR DE INPUTS (Formulário Blindado com Nomenclatura Própria)
# -----------------------------------------------------------------------------
st.sidebar.header("🎛️ Parâmetros do Pré-Mercado")
data_hoje = st.sidebar.text_input("Data da Sessão", pd.Timestamp.now().strftime("%d/%m/%Y"))

st.sidebar.subheader("🎯 Níveis Canal USTEC")
ustec_spot = st.sidebar.text_input("Preço de Ajuste Inicial", "$19,850")
ustec_zce  = st.sidebar.text_input("Z-CE (Zona de Contração)", "$20,000")
ustec_zae  = st.sidebar.text_input("Z-AE (Zona de Absorção)", "$19,700")
ustec_er   = st.sidebar.text_input("ER (Eixo de Rotação)", "$19,820")

st.sidebar.subheader("🎯 Níveis Canal US500")
us500_spot = st.sidebar.text_input("Preço de Referência Base", "$5,720")
us500_zce  = st.sidebar.text_input("Z-CE (Zona de Contração)", "$5,760")
us500_zae  = st.sidebar.text_input("Z-AE (Zona de Absorção)", "$5,680")
us500_er   = st.sidebar.text_input("ER (Eixo de Rotação)", "$5,710")

st.sidebar.subheader("📺 Vetor Macroeconômico")
vetor_macro = st.sidebar.selectbox("Filtro de Pressão Sistêmica (US10Y)", ["Pressão Vendedora Ativa", "Pressão Compradora Ativa", "Regime de Neutralidade / Lateral"])

# -----------------------------------------------------------------------------
# CORPO PRINCIPAL: ENTRADA DE TESES + INPUT GRÁFICO
# -----------------------------------------------------------------------------
col_text, col_graph = st.columns(2)

with col_text:
    st.subheader("📝 Diretrizes do Modelo (Claude Engine)")
    st.caption("Cole abaixo o texto analítico gerado pela Skill do Claude:")
    analise_texto = st.text_area("Boletim Proprietário", height=380, placeholder="1. ARQUITETURA DE REGIMES DE PREÇO...\n2. ZONAS DE EXAUSTÃO DIÁRIA E VETORES DE ARBITRAGEM...")

with col_graph:
    st.subheader("🖼️ Mapeamento Gráfico do Vetor")
    st.caption("Anexe o print limpo com as suas linhas vermelhas manuais plotadas:")
    uploaded_file = st.file_uploader("Arrastar imagem do gráfico aqui", type=["png", "jpg", "jpeg"])
    
    anotacao_grafico = ""
    if uploaded_file:
        st.image(uploaded_file, caption="Mapeamento Estrutural Carregado", use_container_width=True)
        anotacao_grafico = st.text_input("📌 Nota do Analista para o rodapé da imagem:", "Regiões táticas identificadas através do cruzamento das Fronteiras Alfa/Ômega e Vetores de Arbitragem.")

# -----------------------------------------------------------------------------
# GERAÇÃO DO ARQUIVO PDF PREMIUM DO BOLETIM ALFA
# -----------------------------------------------------------------------------
st.markdown("---")
if st.button("🔥 COMPILAR E EMITIR BOLETIM ALFA [ACESSO RESTRITO]", use_container_width=True):
    pdf_filename = "boletim_alfa_premium.pdf"
    
    # Setup de Margens e Formato Executivo
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    # Cores Corporativas: Midnight Navy (#0F172A), Gold Premium (#D4AF37) e Charcoal (#334155)
    style_h1 = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=20, textColor=colors.HexColor('#0F172A'), spaceAfter=3)
    style_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#64748B'), spaceAfter=15)
    style_h2 = ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#0F172A'), spaceBefore=14, spaceAfter=6)
    style_body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=14, textColor=colors.HexColor('#334155'), spaceAfter=5)
    style_caption = ParagraphStyle('Caption', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#64748B'), alignment=1, spaceBefore=4)
    
    elements = []
    
    # Cabeçalho de Alta Autoridade
    elements.append(Paragraph("GENILTRADER — BOLETIM ALFA EXCLUSIVO", style_h1))
    elements.append(Paragraph(f"Estudo Proprietário Pré-Mercado — Sessão de Nova York — Data: {data_hoje}", style_sub))
    
    # Matriz Proprietária de Preço (Tabela Corrigida)
    elements.append(Paragraph("🎯 ARQUITETURA DE REGIMES DE PREÇO INTERNO", style_h2))
    table_data = [
        [Paragraph("<b>Ativo Analisado</b>", style_body), Paragraph("<b>Ajuste Inicial</b>", style_body), Paragraph("<b>Z-CE (Teto)</b>", style_body), Paragraph("<b>Z-AE (Chão)</b>", style_body), Paragraph("<b>Eixo de Rotação (ER)</b>", style_body)],
        [Paragraph("<b>Vetor USTEC</b> (Nasdaq)", style_body), ustec_spot, ustec_zce, ustec_zae, ustec_er],
        [Paragraph("<b>Vetor US500</b> (S&P 500)", style_body), us500_spot, us500_zce, us500_zae, us500_er]
    ]
    
    prop_table = Table(table_data, colWidths=[130, 95, 95, 95, 115])
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
    elements.append(Paragraph(f"<b>Filtro de Pressão Sistêmica Global:</b> {vetor_macro}", style_body))
    
    # Injeção das Teses Textuais Ocultas
    elements.append(Paragraph("📝 DIRETRIZES TÁTICAS OPERACIONAIS", style_h2))
    if text_content := analise_texto.strip():
        paragraphs = text_content.split('\n')
        for p in paragraphs:
            if p.strip():
                elements.append(Paragraph(p, style_body))
    else:
        elements.append(Paragraph("Nenhuma diretriz de texto inserida para esta sessão.", style_body))
        
    # Anexação Inteligente do Gráfico do Trader
    if uploaded_file:
        elements.append(Paragraph("🖼️ VISUALIZAÇÃO E ESTRUTURAÇÃO DO MAPA", style_h2))
        
        temp_img_path = "temp_chart.png"
        img = Image.open(uploaded_file)
        img.save(temp_img_path)
        
        max_width = 520
        w, h = img.size
        aspect = h / w
        final_width = max_width
        final_height = max_width * aspect
        
        elements.append(RLImage(temp_img_path, width=final_width, height=final_height))
        elements.append(Paragraph(f"<b>Figura 1:</b> {anotacao_grafico}", style_caption))
        
    # Cláusula de Direitos e Confidencialidade
    elements.append(Spacer(1, 15))
    style_aviso = ParagraphStyle('Aviso', parent=styles['Normal'], fontName='Helvetica-BoldOblique', fontSize=7.5, textColor=colors.HexColor('#94A3B8'), alignment=1)
    elements.append(Paragraph("PROPRIEDADE INTELECTUAL RETIDA — DISTRIBUIÇÃO PROIBIDA EXTRA ASSINANTES GENILTRADER [▲]", style_aviso))
    
    # Compilar PDF
    doc.build(elements)
    
    # Botão Interativo de Download
    with open(pdf_filename, "rb") as file:
        st.download_button(
            label="📥 BAIXAR BOLETIM ALFA FORMATADO [PDF]",
            data=file,
            file_name=f"Boletim_Alfa_{data_hoje.replace('/', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    st.success("Boletim Alfa compilado com sucesso! Clique no botão acima para baixar.")

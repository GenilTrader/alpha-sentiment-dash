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

# Customização CSS Avançada
st.markdown("""
    <style>
    .main-title { font-size:32px; font-weight:bold; color:#D4AF37; margin-bottom:5px; font-family:'Helvetica Neue', sans-serif; }
    .sub-title { font-size:15px; color:#94A3B8; margin-bottom:25px; }
    div.stButton > button:first-child {
        background-color: #D4AF37 !important;
        color: #0F172A !important;
        font-weight: bold !important;
        font-size: 14px !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 10px 15px !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #F59E0B !important;
        transform: scale(1.02);
    }
    textarea { font-family: 'Courier New', Courier, monospace !important; font-size: 14px !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛡️ GENILTRADER [▲] — ENGINE DE RELATÓRIOS MULTI-GRAPH</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Algoritmo Quant Proprietário — Mapeamento Internacional de Barreiras Macroeconômicas</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FUNÇÃO DE COMPILAÇÃO ISOLADA DO PDF (Largura de Colunas Travada e Corrigida)
# -----------------------------------------------------------------------------
def compilar_pdf(filename, lang, titulo, sub_titulo, label_ativo, label_ajuste, label_zce, label_zae, label_er, data_h, u_spot, u_zce, u_zae, u_er, s_spot, s_zce, s_zae, s_er, v_macro, analise_text, up_files, lista_legendas):
    doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    style_h1 = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=19, textColor=colors.HexColor('#0F172A'), spaceAfter=3)
    style_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#64748B'), spaceAfter=15)
    style_h2 = ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#D4AF37'), spaceBefore=14, spaceAfter=6)
    style_body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=14, textColor=colors.HexColor('#334155'), spaceAfter=5)
    style_caption = ParagraphStyle('Caption', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#64748B'), alignment=1, spaceBefore=4, spaceAfter=10)
    
    elements = []
    elements.append(Paragraph(titulo, style_h1))
    elements.append(Paragraph(f"{sub_titulo} — Date/Data: {data_h}", style_sub))
    
    elements.append(Paragraph("🎯 ARQUITETURA DE REGIMES DE PREÇO / PRICE REGIME", style_h2))
    table_data = [
        [Paragraph(f"<b>{label_ativo}</b>", style_body), Paragraph(f"<b>{label_ajuste}</b>", style_body), Paragraph(f"<b>{label_zce}</b>", style_body), Paragraph(f"<b>{label_zae}</b>", style_body), Paragraph(f"<b>{label_er}</b>", style_body)],
        [Paragraph("<b>Vetor USTEC</b> (QQQ)", style_body), u_spot, u_zce, u_zae, u_er],
        [Paragraph("<b>Vetor US500</b> (SPY)", style_body), s_spot, s_zce, s_zae, s_er]
    ]
    
    # CORREÇÃO CRUCIAL DA LINHA TRAVADA: 5 colunas fixas de 106.4 pontos (Indestrutível)
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
    elements.append(Spacer(1, 5))
    
    label_macro = "Filtro de Pressão Sistêmica Global" if lang == "PT" else "Global Systemic Pressure Filter"
    elements.append(Paragraph(f"<b>{label_macro}:</b> {v_macro}", style_body))
    
    elements.append(Paragraph("📝 DIRETRIZES TÁTICAS OPERACIONAIS / OPERATIONAL THESES", style_h2))
    
    # Processamento de texto livre sem travas de tags complexas
    linhas = analise_text.split('\n')
    for l in linhas:
        if l.strip() and not l.strip().startswith("[PT]") and not l.strip().startswith("[EN]"):
            elements.append(Paragraph(l, style_body))
                
    if up_files:
        elements.append(Paragraph("🖼️ VISUALIZAÇÃO E ESTRUTURAÇÃO DO MAPA VISUAL", style_h2))
        for idx, file in enumerate(up_files):
            temp_img_path = f"temp_chart_{lang}_{idx}.png"
            img = Image.open(file)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
            img.save(temp_img_path, "JPEG", quality=85)
            
            max_width = 500
            w, h = img.size
            aspect = h / w
            
            elements.append(RLImage(temp_img_path, width=max_width, height=max_width * aspect))
            legenda_atual = lista_legendas[idx] if idx < len(lista_legendas) else ""
            elements.append(Paragraph(f"<b>Figura {idx+1}:</b> {legenda_atual}", style_caption))
            elements.append(Spacer(1, 5))
        
    elements.append(Spacer(1, 15))
    aviso_text = "PROPRIEDADE INTELECTUAL RETIDA — DISTRIBUIÇÃO PROIBIDA EXTRA ASSINANTES" if lang == "PT" else "PROPRIETARY INTELLECTUAL PROPERTY — UNAUTHORIZED DISTRIBUTION IS STRICTLY PROHIBITED"
    style_aviso = ParagraphStyle('Aviso', parent=styles['Normal'], fontName='Helvetica-BoldOblique', fontSize=7.5, textColor=colors.HexColor('#94A3B8'), alignment=1)
    elements.append(Paragraph(f"{aviso_text} — GENILTRADER [▲]", style_aviso))
    
    doc.build(elements)

# -----------------------------------------------------------------------------
# SIDEBAR DE CONFIGURAÇÕES (Central de Controle Otimizada)
# -----------------------------------------------------------------------------
st.sidebar.header("🎛️ Painel de Controle GenilTrader")
data_hoje = st.sidebar.text_input("Data da Sessão", pd.Timestamp.now().strftime("%d/%m/%Y"))

st.sidebar.markdown("---")
bt_processar = st.sidebar.button("🔥 EMITIR BOLETINS INTERNACIONAIS", use_container_width=True)
st.sidebar.markdown("---")

# Os botões de download aparecem de forma estável na barra lateral esquerda assim que gerados
if os.path.exists("boletim_alfa_PT.pdf") or os.path.exists("boletim_alfa_EN.pdf"):
    st.sidebar.subheader("📥 Downloads Disponibilizados")
    if os.path.exists("boletim_alfa_PT.pdf"):
        with open("boletim_alfa_PT.pdf", "rb") as f_pt:
            st.sidebar.download_button("📥 BOLETIM EM PORTUGUÊS [PDF]", data=f_pt, file_name=f"Boletim_Alfa_PT_{data_hoje.replace('/', '_')}.pdf", mime="application/pdf", use_container_width=True)
    if os.path.exists("boletim_alfa_EN.pdf"):
        with open("boletim_alfa_EN.pdf", "rb") as f_en:
            st.sidebar.download_button("📥 DOWNLOAD ENGLISH VERSION [PDF]", data=f_en, file_name=f"Alpha_Sentiment_EN_{data_hoje.replace('/', '_')}.pdf", mime="application/pdf", use_container_width=True)
    st.sidebar.markdown("---")

st.sidebar.subheader("🎯 Níveis Canal USTEC (QQQ)")
ustec_spot = st.sidebar.text_input("Preço de Ajuste Inicial", "$720.32")
ustec_zce  = st.sidebar.text_input("Z-CE (Zona de Contração)", "$725.00")
ustec_zae  = st.sidebar.text_input("Z-AE (Zona de Absorção)", "$700.00")
ustec_er   = st.sidebar.text_input("ER (Eixo de Rotação)", "$718.40")

st.sidebar.subheader("🎯 Níveis Canal US500 (SPY)")
us500_spot = st.sidebar.text_input("Preço de Referência Base", "$5,720")
us500_zce  = st.sidebar.text_input("Z-CE (Zona de Contração)", "$5,760")
us500_zae  = st.sidebar.text_input("Z-AE (Zona de Absorção)", "$5,680")
us500_er   = st.sidebar.text_input("ER (Eixo de Rotação)", "$5,710")

st.sidebar.subheader("📺 Vetor Macroeconômico")
vetor_macro_pt = st.sidebar.selectbox("Filtro de Pressão (PT)", ["Regime de Neutralidade / Lateral", "Pressão Vendedora Ativa", "Pressão Compradora Ativa"])
vetor_macro_en = "Neutral Regime / Lateral" if "Neutralidade" in vetor_macro_pt else ("Active Selling Pressure" if "Vendedora" in vetor_macro_pt else "Active Buying Pressure")

# -----------------------------------------------------------------------------
# CORPO PRINCIPAL DE INSERÇÃO DE DADOS
# -----------------------------------------------------------------------------
col_text, col_graph = st.columns(2)

with col_text:
    st.subheader("📝 Diretrizes Ocultas (Claude Engine)")
    st.caption("Cole o texto gerado pela sua análise:")
    analise_texto = st.text_area("Boletim Proprietário", height=450, placeholder="Digite ou cole as diretrizes táticas operacionais aqui...")

with col_graph:
    st.subheader("🖼️ Galeria de Prints e Mapeamentos")
    st.caption("Selecione ou arraste múltiplos arquivos de imagem ao mesmo tempo:")
    uploaded_files = st.file_uploader("Arrastar múltiplos prints gráficos aqui", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    legendas_pt = []
    legendas_en = []
    
    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} imagens prontas para compilação.")
        for idx, file in enumerate(uploaded_files):
            c_l1, c_l2 = st.columns(2)
            with c_l1:

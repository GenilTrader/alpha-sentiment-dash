import streamlit as st
import pandas as pd

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
        padding: 12px 24px !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #F59E0B !important;
        transform: scale(1.01);
    }
    textarea { font-family: 'Courier New', Courier, monospace !important; font-size: 14px !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛡️ GENILTRADER [▲] — ENGINE DE RELATÓRIOS PREMIUM</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Algoritmo Quant Proprietário — Mapeamento Internacional de Barreiras Macroeconômicas</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR DE CONFIGURAÇÕES (Central de Controle Otimizada)
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
# CORPO PRINCIPAL DE INSERÇÃO DE DADOS
# -----------------------------------------------------------------------------
st.subheader("📝 Diretrizes Ocultas (Claude Engine)")
st.caption("Cole abaixo a tese analítica gerada pelo Claude:")
analise_texto = st.text_area("Boletim Proprietário", height=350, placeholder="Digite ou cole as diretrizes táticas operacionais aqui...")

# -----------------------------------------------------------------------------
# FUNÇÃO PARA CONSTRUIR O TEXTO DO BOLETIM SEM DEPENDER DE BIBLIOTECAS DE TERCEIROS
# -----------------------------------------------------------------------------
def construir_boletim_texto(lang, titulo, sub_titulo, label_macro, v_macro):
    doc_text = f"""# {titulo}
### {sub_titulo} — Data: {data_hoje}

## 🎯 ARQUITETURA DE REGIMES DE PREÇO / PRICE REGIME
*   **Vetor USTEC (QQQ):** Ajuste: {ustec_spot} | Z-CE: {ustec_zce} | Z-AE: {ustec_zae} | ER: {ustec_er}
*   **Vetor US500 (SPY):** Referência: {us500_spot} | Z-CE: {us500_zce} | Z-AE: {us500_zae} | ER: {us500_er}

**{label_macro}:** {v_macro}

## 📝 DIRETRIZES TÁTICAS OPERACIONAIS
"""
    # Separação Inteligente de Idiomas baseada nas tags
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
            doc_text += f"\n{l}\n"
            texto_adicionado = True
            
    if not texto_adicionado:
        for l in linhas:
            if l.strip() and not l.strip().startswith("["):
                doc_text += f"\n{l}\n"
                
    doc_text += f"\n\n---\n*PROPRIEDADE INTELECTUAL RETIDA — DISTRIBUIÇÃO PROIBIDA EXTRA ASSINANTES GENILTRADER [▲]*\n"
    return doc_text

# -----------------------------------------------------------------------------
# BOTÕES DE EXPORTAÇÃO IMEDIATA (NUNCA TRAVAM)
# -----------------------------------------------------------------------------
st.markdown("---")
if analise_texto.strip():
    st.subheader("📥 Central de Downloads Disponibilizados")
    st.info("Sua tese foi identificada. Baixe os documentos de exclusividade nos botões abaixo:")
    
    # Gera os textos limpos na memória sem salvar arquivos em pastas do servidor
    texto_pt = construir_boletim_texto("PT", "GENILTRADER — BOLETIM ALFA", "Estudo Proprietário Pré-Market — Sessão de NY", "Filtro de Pressão Sistêmica Global", vetor_macro_pt)
    texto_en = construir_boletim_texto("EN", "GENILTRADER — ALPHA SENTIMENT REPORT", "Proprietary Pre-Market Study — NY Session", "Global Systemic Pressure Filter", vetor_macro_en)
    
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            label="📥 BAIXAR BOLETIM EM PORTUGUÊS [.MD]",
            data=texto_pt,
            file_name=f"Boletim_Alfa_PT_{data_hoje.replace('/', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    with c2:
        st.download_button(
            label="📥 DOWNLOAD ENGLISH VERSION [.MD]",
            data=texto_en,
            file_name=f"Alpha_Sentiment_EN_{data_hoje.replace('/', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )
else:
    st.warning("Aguardando inserção de dados na caixa 'Boletim Proprietário' para liberar a Central de Downloads.")

import streamlit as st
from PIL import Image, ImageOps
import io

def montar_folha_3x4(foto, dpi=300, borda=False):
    # Tamanho do papel 10x15 cm em pixels
    largura_papel_px = int(15 * dpi / 2.54)
    altura_papel_px = int(10 * dpi / 2.54)
    
    # Tamanho da foto 3x4 cm em pixels
    largura_foto_px = int(3 * dpi / 2.54)
    altura_foto_px = int(4 * dpi / 2.54)

    # Redimensionar foto para 3x4
    foto_redimensionada = foto.resize((largura_foto_px, altura_foto_px))

    # Se a pessoa quiser borda, adiciona
    if borda:
        foto_redimensionada = ImageOps.expand(foto_redimensionada, border=10, fill="white")

    # Criar folha em branco
    folha = Image.new("RGB", (largura_papel_px, altura_papel_px), "white")

    # Colar 10 fotos (5 colunas x 2 linhas)
    for linha in range(2):
        for coluna in range(5):
            x = coluna * foto_redimensionada.width
            y = linha * foto_redimensionada.height
            folha.paste(foto_redimensionada, (x, y))

    return folha

# ------------------- INTERFACE STREAMLIT -------------------

st.title("Gerador de Fotos 3x4 em Folha 10x15 📸")

# Criar abas
tab1, tab2 = st.tabs(["Gerador de Fotos", "Sobre o Projeto"])

with tab1:
    uploaded_file = st.file_uploader("Envie sua foto", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        foto = Image.open(uploaded_file).convert("RGB")

        # Opção de borda
        borda = st.checkbox("Adicionar borda branca em cada foto")

        folha = montar_folha_3x4(foto, borda=borda)

        st.image(folha, caption="Prévia da folha 10x15 com fotos 3x4", use_column_width=True)

        buf = io.BytesIO()
        folha.save(buf, format="JPEG", quality=95, dpi=(300, 300))
        byte_im = buf.getvalue()

        st.download_button(
            label="📥 Baixar arquivo pronto (10x15 cm)",
            data=byte_im,
            file_name="fotos_3x4_em_10x15.jpg",
            mime="image/jpeg"
        )

with tab2:
    st.header("Sobre o Projeto")
    
    st.markdown("""
    ## Descrição do Código: Gerador de Fotos 3x4 em Folha 10x15

    Este é um aplicativo web desenvolvido em **Streamlit** que automatiza a criação de folhas de fotos 3x4 no formato 10x15 cm, prontas para impressão.

    ### Funcionalidades Principais:

    **📷 Processamento de Imagens:**
    - Converte qualquer foto enviada pelo usuário em múltiplas fotos 3x4
    - Organiza 10 fotos (5 colunas × 2 linhas) em uma única folha 10x15 cm
    - Mantém a alta qualidade com resolução de 300 DPI para impressão

    **⚙️ Opções Personalizáveis:**
    - Adição opcional de borda branca em cada foto 3x4
    - Suporte aos formatos JPG, JPEG e PNG

    **📱 Interface Amigável:**
    - Upload fácil de arquivos via drag-and-drop
    - Pré-visualização da folha antes do download
    - Botão de download direto da imagem processada

    ### Tecnologias Utilizadas:
    - **Streamlit** para a interface web
    - **PIL (Pillow)** para processamento de imagens
    - **Python** para a lógica de negócio

    ### Como Funciona:
    1. O usuário faz upload de uma foto
    2. O sistema redimensiona a imagem para 3×4 cm
    3. Repete a foto 10 vezes em uma folha 10×15 cm
    4. Gera um arquivo JPEG de alta qualidade para impressão

    Ideal para quem precisa de fotos 3x4 para documentos, evitando a necessidade de serviços especializados de revelação.
    """)
    
    st.info("""
    💡 **Dica:** Para melhores resultados, use uma foto com fundo neutro e boa iluminação, 
    seguindo os padrões usuais para fotos documentais.
    """)

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

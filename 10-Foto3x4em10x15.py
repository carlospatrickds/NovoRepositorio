import streamlit as st
from PIL import Image, ImageOps
import io

def corrigir_rotacao(image):
    """Corrige a rotação automática baseada em metadados EXIF"""
    try:
        # Verificar se há informações de orientação EXIF
        exif = image._getexif()
        if exif:
            orientation = exif.get(0x0112)
            if orientation:
                # Rotacionar conforme a orientação EXIF
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
    except Exception:
        pass
    return image

def rotacionar_imagem(image, angulo):
    """Rotaciona a imagem pelo ângulo especificado"""
    return image.rotate(angulo, expand=True)

def montar_folha_3x4(foto, dpi=300, borda=False, espacamento=0):
    # Tamanho do papel 10x15 cm em pixels
    largura_papel_px = int(15 * dpi / 2.54)
    altura_papel_px = int(10 * dpi / 2.54)
    
    # Tamanho da foto 3x4 cm em pixels
    largura_foto_px = int(3 * dpi / 2.54)
    altura_foto_px = int(4 * dpi / 2.54)

    # Redimensionar foto para 3x4 mantendo a proporção e fazendo crop
    foto_redimensionada = redimensionar_e_recortar(foto, (largura_foto_px, altura_foto_px))

    # Se a pessoa quiser borda, adiciona
    if borda:
        foto_redimensionada = ImageOps.expand(foto_redimensionada, border=10, fill="white")

    # Criar folha em branco
    folha = Image.new("RGB", (largura_papel_px, altura_papel_px), "white")

    # Calcular espaçamento entre fotos
    espacamento_x = espacamento
    espacamento_y = espacamento
    
    # Colar 10 fotos (5 colunas x 2 linhas)
    for linha in range(2):
        for coluna in range(5):
            x = coluna * (foto_redimensionada.width + espacamento_x)
            y = linha * (foto_redimensionada.height + espacamento_y)
            folha.paste(foto_redimensionada, (x, y))

    return folha

def redimensionar_e_recortar(image, target_size):
    """Redimensiona a imagem mantendo a proporção e recortando o centro"""
    target_width, target_height = target_size
    width, height = image.size
    
    # Calcular ratio para redimensionamento
    target_ratio = target_width / target_height
    image_ratio = width / height
    
    if image_ratio > target_ratio:
        # Imagem é mais larga que o alvo
        new_height = target_height
        new_width = int(width * (target_height / height))
    else:
        # Imagem é mais alta que o alvo
        new_width = target_width
        new_height = int(height * (target_width / width))
    
    # Redimensionar
    image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Recortar o centro
    left = (new_width - target_width) / 2
    top = (new_height - target_height) / 2
    right = (new_width + target_width) / 2
    bottom = (new_height + target_height) / 2
    
    return image.crop((left, top, right, bottom))

# ------------------- INTERFACE STREAMLIT -------------------

st.set_page_config(
    page_title="Gerador de Fotos 3x4",
    page_icon="📸",
    layout="wide"
)

# Criar abas
tab1, tab2, tab3 = st.tabs(["Gerador de Fotos", "Como Usar", "Sobre o Projeto"])

with tab1:
    st.title("Gerador de Fotos 3x4 em Folha 10x15 📸")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader("Envie sua foto", type=["jpg", "jpeg", "png"])
        
        if uploaded_file:
            foto = Image.open(uploaded_file).convert("RGB")
            
            # Corrigir rotação automática
            foto = corrigir_rotacao(foto)
            
            # Opções de personalização
            st.subheader("Opções de Personalização")
            borda = st.checkbox("Adicionar borda branca em cada foto", value=True)
            espacamento = st.slider("Espaçamento entre fotos (pixels)", 0, 20, 0)
            
            # Controles de rotação com botões para 90, 180 e 270 graus
            st.subheader("Controles de Rotação")
            col_rot1, col_rot2, col_rot3, col_rot4 = st.columns(4)
            
            with col_rot1:
                if st.button("90° ⤾", use_container_width=True):
                    st.session_state.rotacao = (st.session_state.get('rotacao', 0) + 90) % 360
                    
            with col_rot2:
                if st.button("180° ↻", use_container_width=True):
                    st.session_state.rotacao = (st.session_state.get('rotacao', 0) + 180) % 360
                    
            with col_rot3:
                if st.button("270° ⤿", use_container_width=True):
                    st.session_state.rotacao = (st.session_state.get('rotacao', 0) + 270) % 360
                    
            with col_rot4:
                if st.button("Redefinir ↺", use_container_width=True):
                    st.session_state.rotacao = 0
            
            # Aplicar rotação se especificado
            rotacao = st.session_state.get('rotacao', 0)
            if rotacao != 0:
                foto = rotacionar_imagem(foto, rotacao)
                st.info(f"Foto rotacionada em {rotacao} graus")
            
            col1_1, col1_2 = st.columns(2)
            with col1_1:
                st.image(foto, caption="Sua foto (após ajustes)", use_column_width=True)
    
    with col2:
        if uploaded_file:
            folha = montar_folha_3x4(foto, borda=borda, espacamento=espacamento)
            st.image(folha, caption="Prévia da folha 10x15 com fotos 3x4", use_column_width=True)
            
            # Preparar arquivo para download
            buf = io.BytesIO()
            folha.save(buf, format="JPEG", quality=100, dpi=(300, 300))
            byte_im = buf.getvalue()
            
            st.download_button(
                label="📥 Baixar arquivo pronto (10x15 cm)",
                data=byte_im,
                file_name="fotos_3x4_em_10x15.jpg",
                mime="image/jpeg",
                use_container_width=True
            )
            
            st.info("💡 A imagem está otimizada para impressão em alta qualidade (300 DPI).")
        else:
            st.info("👈 Faça upload de uma foto para gerar sua folha de fotos 3x4")

with tab2:
    st.header("Como Usar o Gerador de Fotos 3x4")
    
    st.markdown("""
    ### Instruções Passo a Passo:
    
    1. **Envie sua foto**: Clique em "Browse files" ou arraste uma foto para a área de upload
    2. **Ajuste a orientação**: Use os botões de rotação (90°, 180°, 270°) para corrigir a orientação
    3. **Personalize**: 
       - Adicione bordas brancas se desejar
       - Ajuste o espaçamento entre as fotos
    4. **Visualize**: Veja a prévia da folha com 10 fotos 3x4
    5. **Baixe**: Clique no botão de download para salvar a imagem pronta para impressão
    
    ### Controles de Rotação:
    - **90° ⤾**: Gira a foto 90 graus no sentido anti-horário
    - **180° ↻**: Gira a foto 180 graus (de cabeça para baixo)
    - **270° ⤿**: Gira a foto 270 graus no sentido anti-horário (ou 90 graus no sentido horário)
    - **Redefinir ↺**: Volta a foto à sua orientação original
    
    ### Dicas para Melhores Resultados:
    - Use uma foto com fundo neutro (branco ou claro)
    - Certifique-se de que o rosto está bem iluminado e centralizado
    - Fotografias com boa resolução produzem melhores resultados
    - Para documentos formais, use trajes apropriados e expressão facial neutra
    """)
    
    st.image("https://images.unsplash.com/photo-1567690346811-22291ebe92ed?w=400&h=300&fit=crop", 
             caption="Exemplo de foto adequada para documentos")

with tab3:
    st.header("Sobre o Projeto")
    
    st.markdown("""
    ## Descrição do Código: Gerador de Fotos 3x4 em Folha 10x15

    Este é um aplicativo web desenvolvido em **Streamlit** que automatiza a criação de folhas de fotos 3x4 no formato 10x15 cm, prontas para impressão.

    ### Funcionalidades Principais:

    **📷 Processamento de Imagens:**
    - Converte qualquer foto enviada pelo usuário em múltiplas fotos 3x4
    - Organiza 10 fotos (5 colunas × 2 linhas) em uma única folha 10x15 cm
    - Mantém a alta qualidade com resolução de 300 DPI para impressão
    - **Corrige automaticamente a rotação** baseada em metadados EXIF
    - **Controles de rotação manual** em incrementos de 90 graus

    **⚙️ Opções Personalizáveis:**
    - Adição opcional de borda branca em cada foto 3x4
    - Controle de espaçamento entre as fotos
    - Correção manual de rotação (90°, 180°, 270°)
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
    2. O sistema corrige a rotação automática baseada em metadados EXIF
    3. O usuário pode ajustar adicionalmente a rotação com controles de 90°
    4. Redimensiona a imagem para 3×4 cm mantendo a proporção
    5. Repete a foto 10 vezes em uma folha 10×15 cm
    6. Gera um arquivo JPEG de alta qualidade para impressão

    Ideal para quem precisa de fotos 3x4 para documentos, evitando a necessidade de serviços especializados de revelação.
    """)
    
    st.info("""
    💡 **Dica:** Muitos dispositivos móveis aplicam rotação automática às fotos com base nos sensores 
    do aparelho. Nosso sistema tenta detectar e corrigir isso automaticamente, mas você também pode 
    usar os controles manuais de rotação para ajustes precisos.
    """)

# Adicionar um footer
st.markdown("---")
st.markdown("📸 *Gerador de Fotos 3x4 - Criado com Streamlit*")

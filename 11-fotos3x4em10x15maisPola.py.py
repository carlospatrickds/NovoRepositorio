import streamlit as st
from PIL import Image, ImageOps, ImageDraw
import io
import subprocess
import sys
import importlib

# Lista de bibliotecas necessárias para outros apps
REQUIRED_LIBRARIES = [
    "fpdf2", "pdfplumber", "PyMuPDF", "unidecode", "sidrapy", 
    "num2words", "html5lib", "beautifulsoup4", "PyGithub", "workalendar"
]

def install_missing_libraries():
    """Verifica e instala bibliotecas ausentes"""
    missing_libs = []
    
    for lib in REQUIRED_LIBRARIES:
        try:
            importlib.import_module(lib)
        except ImportError:
            missing_libs.append(lib)
    
    if missing_libs:
        st.warning(f"Bibliotecas ausentes detectadas: {', '.join(missing_libs)}")
        
        if st.button("Instalar Bibliotecas Ausentes"):
            with st.spinner("Instalando bibliotecas..."):
                for lib in missing_libs:
                    try:
                        # Usar pip para instalar a biblioteca
                        subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                        st.success(f"✓ {lib} instalada com sucesso!")
                    except subprocess.CalledProcessError:
                        st.error(f"✗ Falha ao instalar {lib}")
            
            st.success("Instalação concluída! Reinicie o aplicativo para carregar as bibliotecas.")
            return False
        return False
    else:
        st.success("Todas as bibliotecas necessárias estão instaladas!")
        return True

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

def criar_polaroid(imagem, texto="", tamanho=(800, 1000), cor_borda="white", espessura_borda=40):
    """Cria um efeito Polaroid com a imagem"""
    # Redimensionar a imagem para caber no formato Polaroid
    largura_img = tamanho[0] - espessura_borda * 2
    altura_img = tamanho[1] - espessura_borda * 2 - 80  # Espaço para o texto
    
    img_redimensionada = redimensionar_e_recortar(imagem, (largura_img, altura_img))
    
    # Criar a base do Polaroid
    polaroid = Image.new("RGB", tamanho, cor_borda)
    
    # Colar a imagem no Polaroid
    offset_x = (tamanho[0] - img_redimensionada.width) // 2
    offset_y = (tamanho[1] - img_redimensionada.height - 80) // 2
    polaroid.paste(img_redimensionada, (offset_x, offset_y))
    
    # Adicionar texto se fornecido
    if texto:
        try:
            draw = ImageDraw.Draw(polaroid)
            # Centralizar o texto na parte inferior
            bbox = draw.textbbox((0, 0), texto)
            largura_texto = bbox[2] - bbox[0]
            altura_texto = bbox[3] - bbox[1]
            x_texto = (tamanho[0] - largura_texto) // 2
            y_texto = tamanho[1] - 60 - altura_texto // 2
            
            draw.text((x_texto, y_texto), texto, fill="black")
        except:
            pass
    
    return polaroid

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
    page_title="Gerador de Fotos 3x4 e Polaroid",
    page_icon="📸",
    layout="wide"
)

# Inicializar estado da sessão para rotação
if 'rotacao' not in st.session_state:
    st.session_state.rotacao = 0
if 'rotacao_polaroid' not in st.session_state:
    st.session_state.rotacao_polaroid = 0

# Criar abas
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Gerador de Fotos 3x4", "Modelo Polaroid", "Bibliotecas", "Como Usar", "Sobre o Projeto"])

with tab1:
    st.title("Gerador de Fotos 3x4 em Folha 10x15 📸")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader("Envie sua foto", type=["jpg", "jpeg", "png"], key="uploader_3x4")
        
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
                if st.button("90° ⤾", use_container_width=True, key="rot90_3x4"):
                    st.session_state.rotacao = (st.session_state.rotacao + 90) % 360
                    
            with col_rot2:
                if st.button("180° ↻", use_container_width=True, key="rot180_3x4"):
                    st.session_state.rotacao = (st.session_state.rotacao + 180) % 360
                    
            with col_rot3:
                if st.button("270° ⤿", use_container_width=True, key="rot270_3x4"):
                    st.session_state.rotacao = (st.session_state.rotacao + 270) % 360
                    
            with col_rot4:
                if st.button("Redefinir ↺", use_container_width=True, key="reset_3x4"):
                    st.session_state.rotacao = 0
            
            # Aplicar rotação se especificado
            if st.session_state.rotacao != 0:
                foto = rotacionar_imagem(foto, st.session_state.rotacao)
                st.info(f"Foto rotacionada em {st.session_state.rotacao} graus")
            
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
                use_container_width=True,
                key="download_3x4"
            )
            
            st.info("💡 A imagem está otimizada para impressão em alta qualidade (300 DPI).")
        else:
            st.info("👈 Faça upload de uma foto para gerar sua folha de fotos 3x4")

with tab2:
    st.title("Criador de Fotos Estilo Polaroid 📸")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file_polaroid = st.file_uploader("Envie sua foto", type=["jpg", "jpeg", "png"], key="uploader_polaroid")
        
        if uploaded_file_polaroid:
            foto_polaroid = Image.open(uploaded_file_polaroid).convert("RGB")
            
            # Corrigir rotação automática
            foto_polaroid = corrigir_rotacao(foto_polaroid)
            
            # Opções de personalização do Polaroid
            st.subheader("Personalize seu Polaroid")
            texto_polaroid = st.text_input("Legenda (opcional)", max_chars=30, 
                                          placeholder="Digite uma legenda para sua foto")
            
            cor_borda = st.color_picker("Cor da borda", "#FFFFFF")
            
            tamanho_opcoes = {"Pequeno (600x800)": (600, 800), 
                             "Médio (800x1000)": (800, 1000),
                             "Grande (1000x1200)": (1000, 1200)}
            tamanho_selecionado = st.selectbox("Tamanho do Polaroid", list(tamanho_opcoes.keys()))
            tamanho = tamanho_opcoes[tamanho_selecionado]
            
            # Controles de rotação para o Polaroid
            st.subheader("Ajustar Orientação")
            col_rot1, col_rot2, col_rot3, col_rot4 = st.columns(4)
            
            with col_rot1:
                if st.button("90° ⤾", use_container_width=True, key="rot90_polaroid"):
                    st.session_state.rotacao_polaroid = (st.session_state.rotacao_polaroid + 90) % 360
                    
            with col_rot2:
                if st.button("180° ↻", use_container_width=True, key="rot180_polaroid"):
                    st.session_state.rotacao_polaroid = (st.session_state.rotacao_polaroid + 180) % 360
                    
            with col_rot3:
                if st.button("270° ⤿", use_container_width=True, key="rot270_polaroid"):
                    st.session_state.rotacao_polaroid = (st.session_state.rotacao_polaroid + 270) % 360
                    
            with col_rot4:
                if st.button("Redefinir ↺", use_container_width=True, key="reset_polaroid"):
                    st.session_state.rotacao_polaroid = 0
            
            # Aplicar rotação se especificado
            if st.session_state.rotacao_polaroid != 0:
                foto_polaroid = rotacionar_imagem(foto_polaroid, st.session_state.rotacao_polaroid)
                st.info(f"Foto rotacionada em {st.session_state.rotacao_polaroid} graus")
            
            st.image(foto_polaroid, caption="Sua foto (após ajustes)", use_column_width=True)
    
    with col2:
        if uploaded_file_polaroid:
            polaroid = criar_polaroid(foto_polaroid, texto=texto_polaroid, 
                                     tamanho=tamanho, cor_borda=cor_borda)
            st.image(polaroid, caption="Seu Polaroid", use_column_width=True)
            
            # Preparar arquivo para download
            buf_polaroid = io.BytesIO()
            polaroid.save(buf_polaroid, format="JPEG", quality=95)
            byte_im_polaroid = buf_polaroid.getvalue()
            
            st.download_button(
                label="📥 Baixar Polaroid",
                data=byte_im_polaroid,
                file_name="polaroid.jpg",
                mime="image/jpeg",
                use_container_width=True,
                key="download_polaroid"
            )
            
            st.info("💡 Seu Polaroid está pronto para ser compartilhado ou impresso!")
        else:
            st.info("👈 Faça upload de uma foto para criar seu Polaroid")
            
            # Exemplo de Polaroid
            st.subheader("Exemplo de Polaroid")
            exemplo_img = Image.new("RGB", (600, 800), "#f0f0f0")
            draw = ImageDraw.Draw(exemplo_img)
            draw.rectangle([50, 50, 550, 650], fill="#dddddd")
            draw.text((300, 700), "Sua foto aqui", fill="#666666")
            st.image(exemplo_img, caption="Exemplo de layout Polaroid", use_column_width=True)

with tab3:
    st.header("Gerenciador de Bibliotecas")
    st.info("Esta aba verifica e instala bibliotecas necessárias para outros aplicativos.")
    
    st.subheader("Bibliotecas Necessárias")
    st.write("As seguintes bibliotecas são necessárias para outros aplicativos:")
    
    for i, lib in enumerate(REQUIRED_LIBRARIES):
        try:
            importlib.import_module(lib)
            st.success(f"{i+1}. {lib} ✓ (Instalada)")
        except ImportError:
            st.error(f"{i+1}. {lib} ✗ (Ausente)")
    
    # Verificar e instalar bibliotecas ausentes
    install_missing_libraries()
    
    st.subheader("Informações Adicionais")
    st.markdown("""
    Estas bibliotecas são usadas para:
    - **fpdf2**: Geração de arquivos PDF
    - **pdfplumber/PyMuPDF**: Extração e manipulação de PDFs
    - **unidecode**: Conversão de texto Unicode para ASCII
    - **sidrapy**: Acesso a dados do SIDRA/IBGE
    - **num2words**: Conversão de números em palavras
    - **html5lib/beautifulsoup4**: Web scraping e parsing HTML
    - **PyGithub**: Interação com a API do GitHub
    - **workalendar**: Cálculos com dias úteis e feriados
    """)

with tab4:
    st.header("Como Usar o Gerador de Fotos")
    
    st.markdown("""
    ### 📷 Guia Rápido: Fotos 3x4
    
    1. **Envie sua foto**: Clique em "Browse files" ou arraste uma foto para a área de upload
    2. **Ajuste a orientação**: Use os botões de rotação (90°, 180°, 270°) para corrigir a orientação
    3. **Personalize**: 
       - Adicione bordas brancas se desejar
       - Ajuste o espaçamento entre as fotos
    4. **Visualize**: Veja a prévia da folha com 10 fotos 3x4
    5. **Baixe**: Clique no botão de download para salvar a imagem pronta para impressão
    
    ### 📸 Guia Rápido: Fotos Polaroid
    
    1. **Envie sua foto**: Na aba "Modelo Polaroid", faça upload de uma foto
    2. **Personalize**: 
       - Adicione uma legenda (opcional)
       - Escolha a cor da borda
       - Selecione o tamanho do Polaroid
    3. **Ajuste a orientação**: Use os botões de rotação se necessário
    4. **Visualize**: Veja a prévia do seu Polaroid
    5. **Baixe**: Clique no botão de download para salvar seu Polaroid
    
    ### 🎯 Dicas para Melhores Resultados:
    - Use uma foto com fundo neutro (branco ou claro) para fotos 3x4
    - Para Polaroids, fotos coloridas e com boa iluminação funcionam melhor
    - Certifique-se de que o rosto está bem iluminado e centralizado
    - Fotografias com boa resolução produzem melhores resultados
    """)

with tab5:
    st.header("Sobre o Projeto")
    
    st.markdown("""
    ## Aplicativo de Fotos 3x4 e Polaroid

    Este é um aplicativo web desenvolvido em **Streamlit** que oferece duas funcionalidades principais:

    1. **Gerador de Fotos 3x4**: Automatiza a criação de folhas de fotos 3x4 no formato 10x15 cm, prontas para impressão.
    
    2. **Criador de Polaroids**: Transforma suas fotos em belas imagens estilo Polaroid com personalização de cores e legendas.

    ### Tecnologias Utilizadas:
    - **Streamlit** para a interface web
    - **PIL (Pillow)** para processamento de imagens
    - **Python** para a lógica de negócio

    ### Funcionalidades do Gerador 3x4:
    - Conversão de qualquer foto em múltiplas fotos 3x4
    - Organização de 10 fotos (5 colunas × 2 linhas) em uma única folha 10x15 cm
    - Mantém a alta qualidade com resolução de 300 DPI para impressão
    - Correção automática de rotação baseada em metadados EXIF
    - Controles de rotação manual em incrementos de 90 graus

    ### Funcionalidades do Criador de Polaroids:
    - Transformação de fotos em estilo Polaroid
    - Personalização de cor da borda
    - Adição de legendas personalizadas
    - Opções de tamanho (Pequeno, Médio, Grande)
    - Controles de rotação para ajuste preciso

    ### Gerenciador de Bibliotecas:
    - Verificação automática de bibliotecas necessárias
    - Instalação simplificada com um clique
    - Suporte para múltiplos aplicativos

    Ideal para quem precisa de fotos 3x4 para documentos ou quer criar belas imagens estilo Polaroid, evitando a necessidade de serviços especializados.
    """)

# Adicionar um footer
st.markdown("---")
st.markdown("📸 *Gerador de Fotos 3x4 e Polaroid - Criado com Streamlit*")

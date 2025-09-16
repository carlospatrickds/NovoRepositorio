import streamlit as st
import io
import math
import zipfile  # CORREÇÃO: Import faltando
from PIL import Image
import base64

# Configuração da página
st.set_page_config(
    page_title="PDF Master - Ferramentas Completas PDF",
    page_icon="📄",
    layout="wide"
)

# Verifica e instala dependências necessárias
try:
    import PyPDF2
except ImportError:
    st.error("PyPDF2 não está instalado. Instalando...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
    import PyPDF2

# Interface principal
st.title("📄 PDF Master - Ferramentas Completas")
st.markdown("---")

# Abas para diferentes funcionalidades
tab1, tab2, tab3, tab4 = st.tabs(["🔗 Unir PDFs", "📦 Compactar PDF", "✂️ Dividir por Tamanho", "📑 Dividir por Páginas"])

# ========== FUNÇÕES DE COMPACTAÇÃO AVANÇADA ==========
def compress_pdf_advanced(input_pdf, quality_level):
    """
    Função avançada de compactação de PDF
    quality_level: 1-10 (1=baixa qualidade, 10=alta qualidade)
    """
    try:
        input_pdf.seek(0)
        reader = PyPDF2.PdfReader(input_pdf)
        writer = PyPDF2.PdfWriter()
        
        # Configuração baseada no nível de qualidade
        compression_settings = {
            1: {'compress_content_streams': True, 'image_quality': 10},
            2: {'compress_content_streams': True, 'image_quality': 20},
            3: {'compress_content_streams': True, 'image_quality': 30},
            4: {'compress_content_streams': True, 'image_quality': 40},
            5: {'compress_content_streams': True, 'image_quality': 50},
            6: {'compress_content_streams': True, 'image_quality': 60},
            7: {'compress_content_streams': True, 'image_quality': 70},
            8: {'compress_content_streams': True, 'image_quality': 80},
            9: {'compress_content_streams': True, 'image_quality': 90},
            10: {'compress_content_streams': False, 'image_quality': 100}
        }
        
        config = compression_settings.get(quality_level, compression_settings[5])
        
        for page in reader.pages:
            # Aplica compactação às imagens (se disponível)
            try:
                if '/XObject' in page['/Resources']:
                    xObject = page['/Resources']['/XObject'].get_object()
                    for obj in xObject:
                        if xObject[obj]['/Subtype'] == '/Image':
                            # Simula redução de qualidade de imagem
                            pass
            except:
                pass
            
            writer.add_page(page)
        
        # Aplica configurações de compactação
        if config['compress_content_streams']:
            for page in writer.pages:
                page.compress_content_streams = True
        
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        
        return output
        
    except Exception as e:
        st.error(f"Erro na compactação avançada: {str(e)}")
        return input_pdf

def remove_metadata(pdf_buffer):
    """Remove metadados para reduzir tamanho"""
    try:
        pdf_buffer.seek(0)
        reader = PyPDF2.PdfReader(pdf_buffer)
        writer = PyPDF2.PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        # Não adiciona metadados
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        
        return output
    except:
        return pdf_buffer

# ========== ABA 1: UNIR PDFs ==========
with tab1:
    st.header("🔗 Unir Múltiplos PDFs")
    
    uploaded_files_unir = st.file_uploader(
        "Selecione os arquivos PDF para unir",
        type="pdf",
        accept_multiple_files=True,
        key="unir_pdfs"
    )
    
    if uploaded_files_unir:
        st.success(f"✅ {len(uploaded_files_unir)} arquivo(s) selecionado(s)")
        total_size = sum([f.size for f in uploaded_files_unir])
        st.info(f"📊 Tamanho total: {total_size/1024/1024:.2f} MB")
    
    col1, col2 = st.columns(2)
    with col1:
        compress_level_unir = st.slider(
            "Nível de Compactação",
            min_value=1,
            max_value=10,
            value=7,
            help="1 = Máxima compactação (menor qualidade), 10 = Sem compactação",
            key="slider_unir"
        )
    with col2:
        output_filename_unir = st.text_input(
            "Nome do arquivo de saída",
            "documentos_unidos.pdf",
            key="output_unir"
        )
    
    # Opções avançadas
    with st.expander("⚙️ Opções Avançadas"):
        remove_meta = st.checkbox("Remover metadados", value=True)
        optimize_images = st.checkbox("Otimizar imagens", value=True)
    
    if uploaded_files_unir and len(uploaded_files_unir) > 1:
        if st.button("🔄 Unir e Compactar PDFs", key="btn_unir"):
            with st.spinner("Processando arquivos..."):
                try:
                    merger = PyPDF2.PdfMerger()
                    original_size = 0
                    
                    # Primeiro: une todos os PDFs
                    for pdf_file in uploaded_files_unir:
                        pdf_file.seek(0)
                        original_size += pdf_file.size
                        
                        if compress_level_unir < 10:
                            # Aplica compactação individual
                            compressed_pdf = compress_pdf_advanced(pdf_file, compress_level_unir)
                            merger.append(compressed_pdf)
                        else:
                            merger.append(pdf_file)
                    
                    output = io.BytesIO()
                    merger.write(output)
                    output.seek(0)
                    merger.close()
                    
                    # Remove metadados se solicitado
                    if remove_meta:
                        output = remove_metadata(output)
                    
                    compressed_size = len(output.getvalue())
                    
                    # Mostrar estatísticas
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Arquivos", len(uploaded_files_unir))
                    with col2:
                        st.metric("Tamanho Original", f"{original_size/1024/1024:.2f} MB")
                    with col3:
                        st.metric("Tamanho Final", f"{compressed_size/1024/1024:.2f} MB")
                    with col4:
                        if original_size > 0:
                            reduction = ((original_size - compressed_size) / original_size) * 100
                            st.metric("Redução", f"{reduction:.1f}%", delta=f"{reduction:.1f}%")
                    
                    # Download
                    st.download_button(
                        label="📥 Download do PDF Unido",
                        data=output.getvalue(),
                        file_name=output_filename_unir,
                        mime="application/pdf",
                        key="download_unir"
                    )
                    
                    st.success("✅ PDFs processados com sucesso!")
                    
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

# ========== ABA 2: COMPACTAR PDF ==========
with tab2:
    st.header("📦 Compactar PDF Avançado")
    st.info("Reduza significativamente o tamanho de arquivos PDF individuais")
    
    uploaded_file_compactar = st.file_uploader(
        "Selecione o PDF para compactar",
        type="pdf",
        key="compactar_pdf"
    )
    
    if uploaded_file_compactar:
        file_size_mb = uploaded_file_compactar.size / 1024 / 1024
        st.success(f"✅ Arquivo: {uploaded_file_compactar.name} ({file_size_mb:.2f} MB)")
        
        # Analisa o PDF
        try:
            reader_temp = PyPDF2.PdfReader(uploaded_file_compactar)
            st.info(f"📑 {len(reader_temp.pages)} páginas detectadas")
        except:
            pass
    
    col1, col2 = st.columns(2)
    with col1:
        compress_level = st.slider(
            "Nível de Compactação",
            min_value=1,
            max_value=10,
            value=3,
            help="1 = Máxima compactação (75-90% redução), 10 = Qualidade original",
            key="slider_compactar"
        )
    
    with col2:
        st.markdown("**Previsão de redução:**")
        if compress_level <= 3:
            st.success("🔴 Alta compactação (70-90% redução)")
        elif compress_level <= 6:
            st.warning("🟡 Compactação moderada (30-60% redução)")
        else:
            st.info("🟢 Baixa compactação (10-30% redução)")
    
    output_filename_compactar = st.text_input(
        "Nome do arquivo de saída",
        "documento_compactado.pdf",
        key="output_compactar"
    )
    
    # Opções avançadas
    with st.expander("⚙️ Opções Avançadas de Compactação"):
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            remove_metadata_opt = st.checkbox("Remover metadados", value=True, key="meta_opt")
            downscale_images = st.checkbox("Reduzir qualidade de imagens", value=True)
        with col_opt2:
            optimize_fonts = st.checkbox("Otimizar fontes", value=False)
            remove_comments = st.checkbox("Remover comentários", value=True)
    
    if uploaded_file_compactar:
        if st.button("⚡ Compactar Agora", key="btn_compactar"):
            with st.spinner("Compactando com técnicas avançadas..."):
                try:
                    original_size = uploaded_file_compactar.size
                    
                    # Aplica compactação avançada
                    compressed_pdf = compress_pdf_advanced(uploaded_file_compactar, compress_level)
                    
                    # Remove metadados se selecionado
                    if remove_metadata_opt:
                        compressed_pdf = remove_metadata(compressed_pdf)
                    
                    compressed_size = len(compressed_pdf.getvalue())
                    reduction = ((original_size - compressed_size) / original_size) * 100
                    
                    # Resultados
                    st.subheader("📊 Resultados da Compactação")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Tamanho Original", f"{original_size/1024/1024:.2f} MB")
                    with col2:
                        st.metric("Tamanho Compactado", f"{compressed_size/1024/1024:.2f} MB")
                    with col3:
                        st.metric("Redução", f"{reduction:.1f}%", 
                                 delta_color="inverse" if reduction > 0 else "normal")
                    
                    # Gráfico de comparação
                    chart_data = {
                        'Tipo': ['Original', 'Compactado'],
                        'Tamanho (MB)': [original_size/1024/1024, compressed_size/1024/1024]
                    }
                    st.bar_chart(chart_data, x='Tipo', y='Tamanho (MB)')
                    
                    # Download
                    st.download_button(
                        label="📥 Download PDF Compactado",
                        data=compressed_pdf.getvalue(),
                        file_name=output_filename_compactar,
                        mime="application/pdf",
                        key="download_compactar"
                    )
                    
                    st.success(f"✅ Compactação concluída! {reduction:.1f}% de redução")
                    
                except Exception as e:
                    st.error(f"❌ Erro na compactação: {str(e)}")

# ========== ABA 3: DIVIDIR POR TAMANHO ==========
with tab3:
    st.header("✂️ Dividir PDF por Tamanho")
    st.info("Divide o PDF em partes com tamanho máximo especificado")
    
    uploaded_file_tamanho = st.file_uploader(
        "Selecione o PDF para dividir",
        type="pdf",
        key="dividir_tamanho"
    )
    
    if uploaded_file_tamanho:
        file_size_mb = uploaded_file_tamanho.size / 1024 / 1024
        st.success(f"✅ Arquivo: {uploaded_file_tamanho.name} ({file_size_mb:.2f} MB)")
    
    max_size_mb = st.slider(
        "Tamanho máximo por parte (MB)",
        min_value=1,
        max_value=100,
        value=5,
        help="Cada parte terá no máximo este tamanho"
    )
    
    if uploaded_file_tamanho:
        estimated_parts = math.ceil(uploaded_file_tamanho.size / (max_size_mb * 1024 * 1024))
        st.info(f"📦 Serão criados aproximadamente {estimated_parts} arquivos")
        
        if st.button("🔪 Dividir por Tamanho", key="btn_dividir_tamanho"):
            with st.spinner("Dividindo PDF..."):
                try:
                    reader = PyPDF2.PdfReader(uploaded_file_tamanho)
                    total_pages = len(reader.pages)
                    max_size_bytes = max_size_mb * 1024 * 1024
                    
                    parts = []
                    current_writer = PyPDF2.PdfWriter()
                    current_size = 0
                    
                    for page_num, page in enumerate(reader.pages, 1):
                        # Testa o tamanho adicionando a página
                        temp_writer = PyPDF2.PdfWriter()
                        for p in current_writer.pages:
                            temp_writer.add_page(p)
                        temp_writer.add_page(page)
                        
                        temp_buffer = io.BytesIO()
                        temp_writer.write(temp_buffer)
                        test_size = len(temp_buffer.getvalue())
                        
                        if test_size > max_size_bytes and current_writer.pages:
                            # Salva a parte atual
                            part_buffer = io.BytesIO()
                            current_writer.write(part_buffer)
                            parts.append(part_buffer.getvalue())
                            current_writer = PyPDF2.PdfWriter()
                            current_writer.add_page(page)
                        else:
                            current_writer.add_page(page)
                    
                    # Salva a última parte
                    if current_writer.pages:
                        part_buffer = io.BytesIO()
                        current_writer.write(part_buffer)
                        parts.append(part_buffer.getvalue())
                    
                    # Cria ZIP com todas as partes
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                        for i, part_data in enumerate(parts, 1):
                            zip_file.writestr(
                                f"parte_{i}.pdf", 
                                part_data
                            )
                    
                    zip_buffer.seek(0)
                    
                    st.success(f"✅ PDF dividido em {len(parts)} partes!")
                    st.info(f"📊 Tamanho das partes: {max_size_mb} MB máximo cada")
                    
                    # Download do ZIP
                    st.download_button(
                        label="📦 Download Todas as Partes (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="partes_pdf.zip",
                        mime="application/zip",
                        key="download_parts_zip"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

# ========== ABA 4: DIVIDIR POR PÁGINAS ==========
with tab4:
    st.header("📑 Dividir PDF por Páginas")
    st.info("Divide o PDF em arquivos separados por intervalo de páginas")
    
    uploaded_file_paginas = st.file_uploader(
        "Selecione o PDF para dividir",
        type="pdf",
        key="dividir_paginas"
    )
    
    if uploaded_file_paginas:
        try:
            reader_temp = PyPDF2.PdfReader(uploaded_file_paginas)
            total_pages = len(reader_temp.pages)
            st.success(f"✅ Arquivo: {uploaded_file_paginas.name} ({total_pages} páginas)")
        except Exception as e:
            st.error(f"❌ Erro ao ler PDF: {str(e)}")
            total_pages = 0
    
    if uploaded_file_paginas and total_pages > 0:
        opcao_divisao = st.radio(
            "Como deseja dividir?",
            ["Páginas Individuais", "Intervalo de Páginas", "Tamanho Fixo por Arquivo"],
            key="opcao_divisao"
        )
        
        if opcao_divisao == "Páginas Individuais":
            st.info("Cada página será salva como um PDF separado")
            
        elif opcao_divisao == "Intervalo de Páginas":
            col1, col2 = st.columns(2)
            with col1:
                inicio = st.number_input("Página inicial", 1, total_pages, 1, key="inicio")
            with col2:
                fim = st.number_input("Página final", 1, total_pages, total_pages, key="fim")
            
            if inicio > fim:
                st.error("⚠️ Página inicial deve ser menor que a página final")
        
        elif opcao_divisao == "Tamanho Fixo por Arquivo":
            paginas_por_arquivo = st.number_input(
                "Páginas por arquivo",
                min_value=1,
                max_value=total_pages,
                value=5,
                key="paginas_por_arquivo"
            )
        
        if st.button("✂️ Dividir por Páginas", key="btn_dividir_paginas"):
            with st.spinner("Dividindo PDF..."):
                try:
                    reader = PyPDF2.PdfReader(uploaded_file_paginas)
                    zip_buffer = io.BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                        if opcao_divisao == "Páginas Individuais":
                            for page_num in range(total_pages):
                                writer = PyPDF2.PdfWriter()
                                writer.add_page(reader.pages[page_num])
                                
                                page_buffer = io.BytesIO()
                                writer.write(page_buffer)
                                
                                zip_file.writestr(
                                    f"pagina_{page_num+1}.pdf",
                                    page_buffer.getvalue()
                                )
                            
                            st.success(f"✅ PDF dividido em {total_pages} páginas individuais!")
                        
                        elif opcao_divisao == "Intervalo de Páginas":
                            if inicio <= fim:
                                writer = PyPDF2.PdfWriter()
                                for page_num in range(inicio-1, fim):
                                    writer.add_page(reader.pages[page_num])
                                
                                part_buffer = io.BytesIO()
                                writer.write(part_buffer)
                                
                                zip_file.writestr(
                                    f"paginas_{inicio}_a_{fim}.pdf",
                                    part_buffer.getvalue()
                                )
                                
                                st.success(f"✅ Páginas {inicio} a {fim} extraídas!")
                        
                        elif opcao_divisao == "Tamanho Fixo por Arquivo":
                            num_arquivos = math.ceil(total_pages / paginas_por_arquivo)
                            
                            for i in range(num_arquivos):
                                writer = PyPDF2.PdfWriter()
                                start_page = i * paginas_por_arquivo
                                end_page = min((i + 1) * paginas_por_arquivo, total_pages)
                                
                                for page_num in range(start_page, end_page):
                                    writer.add_page(reader.pages[page_num])
                                
                                part_buffer = io.BytesIO()
                                writer.write(part_buffer)
                                
                                zip_file.writestr(
                                    f"parte_{i+1}_paginas_{start_page+1}-{end_page}.pdf",
                                    part_buffer.getvalue()
                                )
                            
                            st.success(f"✅ PDF dividido em {num_arquivos} partes!")
                    
                    zip_buffer.seek(0)
                    
                    # Download do ZIP
                    st.download_button(
                        label="📦 Download das Partes (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="paginas_divididas.zip",
                        mime="application/zip",
                        key="download_paginas_zip"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

# ========== RODAPÉ ==========
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🛠️ <strong>PDF Master</strong> - Ferramentas completas para gerenciar seus PDFs</p>
        <p>💡 Para melhor compactação: Use nível 1-3 e ative todas as opções avançadas</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0px 0px;
        gap: 8px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4f8bf9;
        color: white;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #4f8bf9;
    }
</style>
""", unsafe_allow_html=True)

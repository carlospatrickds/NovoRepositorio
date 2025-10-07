import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import altair as alt
from fpdf import FPDF
import base64

# Configuração da página
st.set_page_config(
    page_title="Gestão de Processos Judiciais",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    .stat-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin-bottom: 1rem;
    }
    .upload-section {
        border: 2px dashed #dee2e6;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    .assunto-completo {
        white-space: normal !important;
        max-width: 300px;
    }
</style>
""", unsafe_allow_html=True)

def processar_dados(df):
    """Processa os dados do CSV similar à planilha original"""
    
    # Criar cópia para não modificar o original
    processed_df = df.copy()
    
    # Processar tags - separar a coluna tagsProcessoList
    def extrair_servidor(tags):
        if pd.isna(tags):
            return "Sem etiqueta"
        tags_list = str(tags).split(', ')
        for tag in tags_list:
            if 'Servidor' in tag or 'Supervisão' in tag:
                return tag
        return "Não atribuído"
    
    def extrair_vara(tags):
        if pd.isna(tags):
            return "Vara não identificada"
        tags_list = str(tags).split(', ')
        for tag in tags_list:
            if 'Vara Federal' in tag:
                return tag
        return "Vara não identificada"
    
    def extrair_data_chegada(data_str):
        """Extrai data de chegada para ordenação cronológica"""
        if pd.isna(data_str):
            return None
        try:
            data_part = str(data_str).split(',')[0].strip()
            return datetime.strptime(data_part, '%d/%m/%Y')
        except:
            return None
    
    def extrair_mes_data(data_str):
        if pd.isna(data_str):
            return None
        try:
            data_part = str(data_str).split(',')[0].strip()
            data_obj = datetime.strptime(data_part, '%d/%m/%Y')
            return data_obj.month
        except:
            return None
    
    def extrair_dia_data(data_str):
        if pd.isna(data_str):
            return None
        try:
            data_part = str(data_str).split(',')[0].strip()
            data_obj = datetime.strptime(data_part, '%d/%m/%Y')
            return data_obj.day
        except:
            return None
    
    # Aplicar processamento
    processed_df['servidor'] = processed_df['tagsProcessoList'].apply(extrair_servidor)
    processed_df['vara'] = processed_df['tagsProcessoList'].apply(extrair_vara)
    processed_df['data_chegada_obj'] = processed_df['dataChegada'].apply(extrair_data_chegada)
    processed_df['mes'] = processed_df['dataChegada'].apply(extrair_mes_data)
    processed_df['dia'] = processed_df['dataChegada'].apply(extrair_dia_data)
    
    # Formatar data de chegada (apenas data)
    processed_df['data_chegada_formatada'] = processed_df['dataChegada'].apply(
        lambda x: str(x).split(',')[0] if pd.notna(x) else ''
    )
    
    # Ordenar por data de chegada (mais recente primeiro)
    processed_df = processed_df.sort_values('data_chegada_obj', ascending=False)
    
    return processed_df

def criar_estatisticas(df):
    """Cria estatísticas similares à planilha dados_individuais"""
    
    stats = {}
    
    # Estatísticas por Polo Passivo (ordenado do maior para o menor)
    polo_passivo_stats = df['poloPassivo'].value_counts().head(10)
    stats['polo_passivo'] = polo_passivo_stats
    
    # Estatísticas por Mês
    mes_stats = df['mes'].value_counts().sort_index()
    stats['mes'] = mes_stats
    
    # Estatísticas por Servidor
    servidor_stats = df['servidor'].value_counts()
    stats['servidor'] = servidor_stats
    
    # Estatísticas por Vara
    vara_stats = df['vara'].value_counts().head(10)
    stats['vara'] = vara_stats
    
    # Estatísticas por Assunto
    assunto_stats = df['assuntoPrincipal'].value_counts().head(10)
    stats['assunto'] = assunto_stats
    
    return stats

def criar_grafico_barras(dados, titulo, eixo_x, eixo_y):
    """Cria gráfico de barras usando Altair"""
    df_plot = pd.DataFrame({
        eixo_x: dados.index,
        eixo_y: dados.values
    })
    
    chart = alt.Chart(df_plot).mark_bar().encode(
        x=alt.X(f'{eixo_x}:N', title=eixo_x, axis=alt.Axis(labelAngle=-45), sort='-y'),
        y=alt.Y(f'{eixo_y}:Q', title=eixo_y),
        tooltip=[eixo_x, eixo_y]
    ).properties(
        title=titulo,
        width=600,
        height=400
    )
    
    return chart

def criar_grafico_pizza_com_legenda(dados, titulo):
    """Cria gráfico de pizza com legenda e valores"""
    df_plot = pd.DataFrame({
        'categoria': dados.index,
        'valor': dados.values,
        'percentual': (dados.values / dados.values.sum() * 100).round(1)
    })
    
    # Criar labels com valores
    df_plot['label'] = df_plot['categoria'] + ' (' + df_plot['valor'].astype(str) + ' - ' + df_plot['percentual'].astype(str) + '%)'
    
    chart = alt.Chart(df_plot).mark_arc().encode(
        theta=alt.Theta(field="valor", type="quantitative"),
        color=alt.Color(field="label", type="nominal", legend=alt.Legend(title="Servidores")),
        tooltip=['categoria', 'valor', 'percentual']
    ).properties(
        title=titulo,
        width=500,
        height=400
    )
    
    return chart

def criar_relatorio_visao_geral(stats, total_processos):
    """Cria relatório PDF para a aba Visão Geral"""
    
    class PDF(FPDF):
        def header(self):
            # Cabeçalho
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'PODER JUDICIÁRIO', 0, 1, 'C')
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'JUSTIÇA FEDERAL EM PERNAMBUCO - JUIZADOS ESPECIAIS FEDERAIS', 0, 1, 'C')
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'PLANILHA DE CONTROLE DE PROCESSOS - PJE2X', 0, 1, 'C')
            self.ln(5)
    
    pdf = PDF()
    pdf.add_page()
    
    # Título do relatório
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'RELATÓRIO - VISÃO GERAL', 0, 1, 'C')
    pdf.ln(5)
    
    # Informações gerais
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'INFORMAÇÕES GERAIS', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Total de Processos: {total_processos}', 0, 1)
    pdf.cell(0, 6, f'Data de geração: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    pdf.ln(10)
    
    # Estatísticas por Polo Passivo
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'DISTRIBUIÇÃO POR POLO PASSIVO', 0, 1)
    pdf.set_font('Arial', '', 10)
    for polo, quantidade in stats['polo_passivo'].items():
        pdf.cell(0, 6, f'{polo}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    # Estatísticas por Mês
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'DISTRIBUIÇÃO POR MÊS', 0, 1)
    pdf.set_font('Arial', '', 10)
    for mes, quantidade in stats['mes'].items():
        pdf.cell(0, 6, f'Mês {mes}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    # Estatísticas por Servidor
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'DISTRIBUIÇÃO POR SERVIDOR', 0, 1)
    pdf.set_font('Arial', '', 10)
    for servidor, quantidade in stats['servidor'].items():
        pdf.cell(0, 6, f'{servidor}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    # Estatísticas por Assunto
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'PRINCIPAIS ASSUNTOS', 0, 1)
    pdf.set_font('Arial', '', 10)
    for assunto, quantidade in stats['assunto'].items():
        pdf.cell(0, 6, f'{assunto}: {quantidade}', 0, 1)
    
    # Data e hora no final
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 6, f'Relatório gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}', 0, 1)
    
    return pdf

def criar_relatorio_lista_processos(df):
    """Cria relatório PDF para a aba Lista de Processos"""
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'PODER JUDICIÁRIO', 0, 1, 'C')
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'JUSTIÇA FEDERAL EM PERNAMBUCO - JUIZADOS ESPECIAIS FEDERAIS', 0, 1, 'C')
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'PLANILHA DE CONTROLE DE PROCESSOS - PJE2X', 0, 1, 'C')
            self.ln(5)
    
    pdf = PDF()
    pdf.add_page()
    
    # Título do relatório
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'RELATÓRIO - LISTA DE PROCESSOS', 0, 1, 'C')
    pdf.ln(5)
    
    # Informações gerais
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Total de Processos: {len(df)}', 0, 1)
    pdf.cell(0, 6, f'Data de geração: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    pdf.ln(10)
    
    # Tabela de processos
    pdf.set_font('Arial', 'B', 9)
    colunas = ['Nº Processo', 'Polo Ativo', 'Data', 'Servidor', 'Assunto']
    larguras = [35, 45, 20, 30, 60]
    
    # Cabeçalho da tabela
    for i, coluna in enumerate(colunas):
        pdf.cell(larguras[i], 10, coluna, 1, 0, 'C')
    pdf.ln()
    
    # Dados da tabela
    pdf.set_font('Arial', '', 7)
    for _, row in df.head(50).iterrows():
        n_processo = str(row['Nº Processo']) if pd.notna(row['Nº Processo']) else ''
        polo_ativo = str(row['Polo Ativo']) if pd.notna(row['Polo Ativo']) else ''
        data_chegada = str(row['Data Chegada']) if pd.notna(row['Data Chegada']) else ''
        servidor = str(row['Servidor']) if pd.notna(row['Servidor']) else ''
        assunto = str(row['Assunto Principal']) if pd.notna(row['Assunto Principal']) else ''
        
        pdf.cell(larguras[0], 8, n_processo[:20], 1)
        pdf.cell(larguras[1], 8, polo_ativo[:25], 1)
        pdf.cell(larguras[2], 8, data_chegada[:10], 1)
        pdf.cell(larguras[3], 8, servidor[:15], 1)
        pdf.cell(larguras[4], 8, assunto[:40], 1)
        pdf.ln()
    
    if len(df) > 50:
        pdf.ln(5)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 8, f'* Mostrando os primeiros 50 de {len(df)} processos', 0, 1)
    
    # Data e hora no final
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 6, f'Relatório gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}', 0, 1)
    
    return pdf

def criar_relatorio_estatisticas(stats):
    """Cria relatório PDF para a aba Estatísticas"""
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'PODER JUDICIÁRIO', 0, 1, 'C')
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'JUSTIÇA FEDERAL EM PERNAMBUCO - JUIZADOS ESPECIAIS FEDERAIS', 0, 1, 'C')
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'PLANILHA DE CONTROLE DE PROCESSOS - PJE2X', 0, 1, 'C')
            self.ln(5)
    
    pdf = PDF()
    pdf.add_page()
    
    # Título do relatório
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'RELATÓRIO - ESTATÍSTICAS DETALHADAS', 0, 1, 'C')
    pdf.ln(5)
    
    # Informações gerais
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Data de geração: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    pdf.ln(10)
    
    # Estatísticas por Polo Passivo
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'POR POLO PASSIVO', 0, 1)
    pdf.set_font('Arial', '', 10)
    for polo, quantidade in stats['polo_passivo'].items():
        pdf.cell(0, 6, f'{polo}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    # Estatísticas por Mês
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'POR MÊS', 0, 1)
    pdf.set_font('Arial', '', 10)
    for mes, quantidade in stats['mes'].items():
        pdf.cell(0, 6, f'Mês {mes}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    # Estatísticas por Servidor
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'POR SERVIDOR', 0, 1)
    pdf.set_font('Arial', '', 10)
    for servidor, quantidade in stats['servidor'].items():
        pdf.cell(0, 6, f'{servidor}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    # Estatísticas por Vara
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'POR VARA', 0, 1)
    pdf.set_font('Arial', '', 10)
    for vara, quantidade in stats['vara'].items():
        pdf.cell(0, 6, f'{vara}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    # Estatísticas por Assunto
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'POR ASSUNTO', 0, 1)
    pdf.set_font('Arial', '', 10)
    for assunto, quantidade in stats['assunto'].items():
        pdf.cell(0, 6, f'{assunto}: {quantidade}', 0, 1)
    
    # Data e hora no final
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 6, f'Relatório gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}', 0, 1)
    
    return pdf

def criar_relatorio_filtros(df_filtrado, filtros_aplicados):
    """Cria relatório PDF para a aba Filtros Avançados"""
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'PODER JUDICIÁRIO', 0, 1, 'C')
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'JUSTIÇA FEDERAL EM PERNAMBUCO - JUIZADOS ESPECIAIS FEDERAIS', 0, 1, 'C')
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'PLANILHA DE CONTROLE DE PROCESSOS - PJE2X', 0, 1, 'C')
            self.ln(5)
    
    pdf = PDF()
    pdf.add_page()
    
    # Título do relatório
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'RELATÓRIO - FILTROS APLICADOS', 0, 1, 'C')
    pdf.ln(5)
    
    # Informações dos filtros
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'FILTROS APLICADOS:', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, filtros_aplicados, 0, 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Total de processos filtrados: {len(df_filtrado)}', 0, 1)
    pdf.cell(0, 6, f'Data de geração: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    pdf.ln(10)
    
    # Tabela de processos
    pdf.set_font('Arial', 'B', 9)
    colunas = ['Nº Processo', 'Polo Ativo', 'Data', 'Servidor', 'Assunto']
    larguras = [35, 45, 20, 30, 60]
    
    # Cabeçalho da tabela
    for i, coluna in enumerate(colunas):
        pdf.cell(larguras[i], 10, coluna, 1, 0, 'C')
    pdf.ln()
    
    # Dados da tabela
    pdf.set_font('Arial', '', 7)
    for _, row in df_filtrado.head(50).iterrows():
        n_processo = str(row['Nº Processo']) if pd.notna(row['Nº Processo']) else ''
        polo_ativo = str(row['Polo Ativo']) if pd.notna(row['Polo Ativo']) else ''
        data_chegada = str(row['Data Chegada']) if pd.notna(row['Data Chegada']) else ''
        servidor = str(row['Servidor']) if pd.notna(row['Servidor']) else ''
        assunto = str(row['Assunto Principal']) if pd.notna(row['Assunto Principal']) else ''
        
        pdf.cell(larguras[0], 8, n_processo[:20], 1)
        pdf.cell(larguras[1], 8, polo_ativo[:25], 1)
        pdf.cell(larguras[2], 8, data_chegada[:10], 1)
        pdf.cell(larguras[3], 8, servidor[:15], 1)
        pdf.cell(larguras[4], 8, assunto[:40], 1)
        pdf.ln()
    
    if len(df_filtrado) > 50:
        pdf.ln(5)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 8, f'* Mostrando os primeiros 50 de {len(df_filtrado)} processos', 0, 1)
    
    # Data e hora no final
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 6, f'Relatório gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}', 0, 1)
    
    return pdf

def gerar_link_download_pdf(pdf, nome_arquivo):
    """Gera link de download para o PDF"""
    try:
        pdf_output = pdf.output()
        b64 = base64.b64encode(pdf_output).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{nome_arquivo}">📄 Baixar Relatório PDF</a>'
        return href
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")
        return ""

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>PODER JUDICIÁRIO</h1>
        <h3>JUSTIÇA FEDERAL EM PERNAMBUCO - JUIZADOS ESPECIAIS FEDERAIS</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload de arquivo
    st.markdown("### 📁 Upload do Arquivo CSV do PJE")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo CSV exportado do PJE",
        type=['csv'],
        help="Arquivo CSV com até 5.000 linhas, separado por ponto e vírgula"
    )
    
    if uploaded_file is not None:
        try:
            # Ler arquivo CSV
            df = pd.read_csv(uploaded_file, delimiter=';', encoding='utf-8')
            
            # Mostrar informações básicas do arquivo
            st.success(f"✅ Arquivo carregado com sucesso! {len(df)} processos encontrados.")
            
            # Processar dados
            with st.spinner('Processando dados...'):
                processed_df = processar_dados(df)
                stats = criar_estatisticas(processed_df)
            
            # Abas para organização
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Visão Geral", "📋 Lista de Processos", "📈 Estatísticas", "🔍 Filtros Avançados"])
            
            with tab1:
                st.markdown("### 📊 Dashboard - Visão Geral")
                
                # Botão para gerar relatório
                col1, col2, col3, col4 = st.columns(4)
                with col4:
                    if st.button("📄 Gerar Relatório - Visão Geral", key="relatorio_visao"):
                        with st.spinner("Gerando relatório..."):
                            pdf = criar_relatorio_visao_geral(stats, len(processed_df))
                            nome_arquivo = f"relatorio_visao_geral_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                            href = gerar_link_download_pdf(pdf, nome_arquivo)
                            if href:
                                st.markdown(href, unsafe_allow_html=True)
                
                # Métricas principais
                with col1:
                    st.metric("Total de Processos", len(processed_df))
                
                with col2:
                    servidores_unicos = processed_df['servidor'].nunique()
                    st.metric("Servidores Envolvidos", servidores_unicos)
                
                with col3:
                    varas_unicas = processed_df['vara'].nunique()
                    st.metric("Varas Federais", varas_unicas)
                
                # Gráficos principais
                col1, col2 = st.columns(2)
                
                with col1:
                    if not stats['polo_passivo'].empty:
                        st.altair_chart(
                            criar_grafico_barras(
                                stats['polo_passivo'], 
                                "Distribuição por Polo Passivo", 
                                "Polo Passivo", 
                                "Quantidade"
                            ), 
                            use_container_width=True
                        )
                    
                    with st.expander("📊 Ver dados - Polo Passivo"):
                        st.dataframe(stats['polo_passivo'])
                
                with col2:
                    if not stats['mes'].empty:
                        st.altair_chart(
                            criar_grafico_barras(
                                stats['mes'], 
                                "Distribuição por Mês", 
                                "Mês", 
                                "Quantidade"
                            ), 
                            use_container_width=True
                        )
                    
                    with st.expander("📊 Ver dados - Distribuição por Mês"):
                        st.dataframe(stats['mes'])
                
                # Gráficos secundários
                col3, col4 = st.columns(2)
                
                with col3:
                    if not stats['servidor'].empty:
                        st.altair_chart(
                            criar_grafico_pizza_com_legenda(
                                stats['servidor'],
                                "Distribuição por Servidor"
                            ),
                            use_container_width=True
                        )
                
                with col4:
                    if not stats['assunto'].empty:
                        df_assunto = pd.DataFrame({
                            'Assunto': stats['assunto'].index,
                            'Quantidade': stats['assunto'].values
                        })
                        
                        chart_assunto = alt.Chart(df_assunto).mark_bar().encode(
                            x='Quantidade:Q',
                            y=alt.Y('Assunto:N', sort='-x', title='Assunto'),
                            tooltip=['Assunto', 'Quantidade']
                        ).properties(
                            title="Principais Assuntos",
                            width=600,
                            height=400
                        )
                        st.altair_chart(chart_assunto, use_container_width=True)
            
            with tab2:
                st.markdown("### 📋 Lista de Processos - Visualização Consolidada")
                
                # Botão para gerar relatório
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("📄 Gerar Relatório - Lista", key="relatorio_lista"):
                        with st.spinner("Gerando relatório..."):
                            pdf = criar_relatorio_lista_processos(processed_df)
                            nome_arquivo = f"relatorio_lista_processos_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                            href = gerar_link_download_pdf(pdf, nome_arquivo)
                            if href:
                                st.markdown(href, unsafe_allow_html=True)
                
                # Seleção de colunas para exibir
                colunas_base = [
                    'numeroProcesso', 'poloAtivo', 'poloPassivo', 'data_chegada_formatada',
                    'mes', 'dia', 'servidor', 'vara', 'assuntoPrincipal'
                ]
                
                # DataFrame para exibição
                display_df = processed_df[colunas_base].copy()
                display_df.columns = [
                    'Nº Processo', 'Polo Ativo', 'Polo Passivo', 'Data Chegada',
                    'Mês', 'Dia', 'Servidor', 'Vara', 'Assunto Principal'
                ]
                
                # Paginação
                page_size = 100
                total_pages = max(1, len(display_df) // page_size + (1 if len(display_df) % page_size else 0))
                
                page_number = st.number_input(
                    "Página", 
                    min_value=1, 
                    max_value=total_pages, 
                    value=1,
                    help=f"Mostrando {page_size} processos por página"
                )
                
                start_idx = (page_number - 1) * page_size
                end_idx = start_idx + page_size
                
                # Exibir tabela
                st.dataframe(
                    display_df.iloc[start_idx:end_idx],
                    use_container_width=True,
                    height=600
                )
                
                st.write(f"Mostrando processos {start_idx + 1} a {min(end_idx, len(display_df))} de {len(display_df)}")
                
                # Botão de exportação Excel
                if st.button("📥 Exportar para Excel"):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        display_df.to_excel(writer, sheet_name='Processos', index=False)
                    
                    st.download_button(
                        label="⬇️ Baixar arquivo Excel",
                        data=output.getvalue(),
                        file_name=f"processos_judiciais_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            with tab3:
                st.markdown("### 📈 Estatísticas Detalhadas")
                
                # Botão para gerar relatório
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("📄 Gerar Relatório - Estatísticas", key="relatorio_estatisticas"):
                        with st.spinner("Gerando relatório..."):
                            pdf = criar_relatorio_estatisticas(stats)
                            nome_arquivo = f"relatorio_estatisticas_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                            href = gerar_link_download_pdf(pdf, nome_arquivo)
                            if href:
                                st.markdown(href, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Por Polo Passivo")
                    st.dataframe(stats['polo_passivo'], use_container_width=True)
                    
                    st.markdown("#### Por Servidor")
                    st.dataframe(stats['servidor'], use_container_width=True)
                
                with col2:
                    st.markdown("#### Por Mês")
                    st.dataframe(stats['mes'], use_container_width=True)
                    
                    st.markdown("#### Por Vara")
                    st.dataframe(stats['vara'], use_container_width=True)
            
            with tab4:
                st.markdown("### 🔍 Filtros Avançados")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    servidor_filter = st.multiselect(
                        "Filtrar por Servidor",
                        options=sorted(processed_df['servidor'].unique()),
                        default=None
                    )
                    
                    mes_filter = st.multiselect(
                        "Filtrar por Mês",
                        options=sorted(processed_df['mes'].dropna().unique()),
                        default=None
                    )
                
                with col2:
                    polo_passivo_filter = st.multiselect(
                        "Filtrar por Polo Passivo",
                        options=sorted(processed_df['poloPassivo'].unique()),
                        default=None
                    )
                    
                    assunto_filter = st.multiselect(
                        "Filtrar por Assunto",
                        options=sorted(processed_df['assuntoPrincipal'].dropna().unique()),
                        default=None
                    )
                
                with col3:
                    vara_filter = st.multiselect(
                        "Filtrar por Vara",
                        options=sorted(processed_df['vara'].unique()),
                        default=None
                    )
                
                # Aplicar filtros
                filtered_df = processed_df.copy()
                filtros_aplicados = []
                
                if servidor_filter:
                    filtered_df = filtered_df[filtered_df['servidor'].isin(servidor_filter)]
                    filtros_aplicados.append(f"Servidor: {', '.join(servidor_filter)}")
                
                if mes_filter:
                    filtered_df = filtered_df[filtered_df['mes'].isin(mes_filter)]
                    filtros_aplicados.append(f"Mês: {', '.join(map(str, mes_filter))}")
                
                if polo_passivo_filter:
                    filtered_df = filtered_df[filtered_df['poloPassivo'].isin(polo_passivo_filter)]
                    filtros_aplicados.append(f"Polo Passivo: {', '.join(polo_passivo_filter)}")
                
                if assunto_filter:
                    filtered_df = filtered_df[filtered_df['assuntoPrincipal'].isin(assunto_filter)]
                    filtros_aplicados.append(f"Assunto: {', '.join(assunto_filter)}")
                
                if vara_filter:
                    filtered_df = filtered_df[filtered_df['vara'].isin(vara_filter)]
                    filtros_aplicados.append(f"Vara: {', '.join(vara_filter)}")
                
                filtros_texto = " | ".join(filtros_aplicados) if filtros_aplicados else "Nenhum filtro aplicado"
                
                st.metric("Processos Filtrados", len(filtered_df))
                
                if len(filtered_df) > 0:
                    # Exibir dados filtrados
                    colunas_filtro = [
                        'numeroProcesso', 'poloAtivo', 'poloPassivo', 'data_chegada_formatada',
                        'mes', 'dia', 'servidor', 'vara', 'assuntoPrincipal'
                    ]
                    
                    display_filtered = filtered_df[colunas_filtro].copy()
                    display_filtered.columns = [
                        'Nº Processo', 'Polo Ativo', 'Polo Passivo', 'Data Chegada',
                        'Mês', 'Dia', 'Servidor', 'Vara', 'Assunto Principal'
                    ]
                    
                    st.dataframe(display_filtered, use_container_width=True)
                    
                    # Botão para gerar relatório PDF
                    st.markdown("---")
                    st.markdown("### 📄 Gerar Relatório com Filtros")
                    
                    if st.button("🖨️ Gerar Relatório PDF com Filtros Atuais", key="relatorio_filtros"):
                        with st.spinner("Gerando relatório..."):
                            try:
                                pdf = criar_relatorio_filtros(display_filtered, filtros_texto)
                                nome_arquivo = f"relatorio_filtros_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                                href = gerar_link_download_pdf(pdf, nome_arquivo)
                                if href:
                                    st.markdown(href, unsafe_allow_html=True)
                                else:
                                    st.error("Erro ao gerar o relatório PDF")
                            except Exception as e:
                                st.error(f"Erro ao gerar PDF: {e}")
                
                else:
                    st.warning("Nenhum processo encontrado com os filtros aplicados.")
        
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
    
    else:
        # Tela inicial quando não há arquivo
        st.markdown("""
        <div class="upload-section">
            <h3>👋 Bem-vindo ao Sistema de Gestão de Processos Judiciais</h3>
            <p>Faça o upload do arquivo CSV exportado do PJE para começar a análise.</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import io
import altair as alt
from fpdf import FPDF
import base64

# --- CONFIGURAÇÕES E CSS ---

# Configuração da página
st.set_page_config(
    page_title="Gestão de Processos Judiciais Unificada",
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

# --- MAPA DE COLUNAS UNIFICADO ---

# Novo Nome (PADRÃO) -> Lista de Nomes Possíveis nos CSVs
COLUNA_MAP = {
    'NUMERO_PROCESSO': ['Número do Processo', 'numeroProcesso'],
    'POLO_ATIVO': ['Polo Ativo', 'poloAtivo'],
    'POLO_PASSIVO': ['Polo Passivo', 'poloPassivo'],
    'ORGAO_JULGADOR': ['Órgão Julgador', 'orgaoJulgador'],
    'ASSUNTO_PRINCIPAL': ['Assunto', 'assuntoPrincipal'],
    'TAREFA': ['Tarefa', 'nomeTarefa'],
    'ETIQUETAS': ['Etiquetas', 'tagsProcessoList'],
    'DIAS': ['Dias'],  # Coluna 'Dias' do primeiro arquivo
    'DATA_CHEGADA_RAW': ['Data Último Movimento', 'dataChegada'] # Coluna bruta de data para processamento
}

# --- FUNÇÕES AUXILIARES ---

def get_local_time():
    """Obtém o horário local do Brasil (UTC-3)"""
    utc_now = datetime.now(timezone.utc)
    brasil_tz = timezone(timedelta(hours=-3))
    return utc_now.astimezone(brasil_tz)

@st.cache_data
def mapear_e_padronizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia as colunas do DataFrame para um padrão único."""
    colunas_padronizadas = {}
    
    for padrao, possiveis in COLUNA_MAP.items():
        coluna_encontrada = next((col for col in possiveis if col in df.columns), None)
        
        if coluna_encontrada:
            colunas_padronizadas[coluna_encontrada] = padrao
        
    df.rename(columns=colunas_padronizadas, inplace=True)
    return df

@st.cache_data
def processar_dados(df):
    """Processa os dados do CSV, usando APENAS nomes de colunas padronizados."""
    
    processed_df = df.copy()
    
    if 'ETIQUETAS' not in processed_df.columns:
        st.error("Coluna 'ETIQUETAS' (ou 'tagsProcessoList') não encontrada. O arquivo não está no formato esperado.")
        return processed_df
    
    # --- 1. Processar Tags ---
    
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
        
    processed_df['servidor'] = processed_df['ETIQUETAS'].apply(extrair_servidor)
    processed_df['vara'] = processed_df['ETIQUETAS'].apply(extrair_vara)

    # --- 2. Processar Datas e Calcular Dias ---
    
    if 'DATA_CHEGADA_RAW' in processed_df.columns:
        
        def extrair_data_chegada(data_str):
            """Tenta extrair a data de chegada no formato DD/MM/YYYY para objeto datetime."""
            if pd.isna(data_str):
                return None
            data_str = str(data_str)
            
            try:
                data_part = data_str.split(',')[0].strip()
                return datetime.strptime(data_part, '%d/%m/%Y')
            except:
                pass
            
            try:
                if len(data_str) > 10 and data_str.isdigit():
                    return pd.to_datetime(int(data_str), unit='ms').to_pydatetime()
            except:
                pass
                
            return None

        processed_df['data_chegada_obj'] = processed_df['DATA_CHEGADA_RAW'].apply(extrair_data_chegada)
        
        processed_df['mes'] = processed_df['data_chegada_obj'].dt.month
        processed_df['dia'] = processed_df['data_chegada_obj'].dt.day
        
        processed_df['data_chegada_formatada'] = processed_df['data_chegada_obj'].dt.strftime('%d/%m/%Y')
        
        # Calcular coluna 'DIAS' se não existir
        if 'DIAS' not in processed_df.columns:
            data_referencia = pd.to_datetime('2025-10-07') 
            
            processed_df['DIAS'] = (data_referencia - processed_df['data_chegada_obj']).dt.days
            processed_df['DIAS'] = processed_df['DIAS'].fillna(0).astype(int)
        
        processed_df = processed_df.sort_values('data_chegada_obj', ascending=False)
        
    cols_to_keep = list(COLUNA_MAP.keys()) + ['servidor', 'vara', 'data_chegada_obj', 'mes', 'dia', 'data_chegada_formatada']
    processed_df = processed_df.filter(items=cols_to_keep)

    return processed_df

def criar_estatisticas(df):
    """Cria estatísticas usando APENAS nomes de colunas padronizados."""
    
    stats = {}
    
    if 'POLO_PASSIVO' in df.columns:
        stats['polo_passivo'] = df['POLO_PASSIVO'].value_counts().head(10)
    else:
        stats['polo_passivo'] = pd.Series(dtype='int64')

    if 'mes' in df.columns:
        stats['mes'] = df['mes'].value_counts().sort_index()
    else:
        stats['mes'] = pd.Series(dtype='int64')

    if 'servidor' in df.columns:
        stats['servidor'] = df['servidor'].value_counts()
    else:
        stats['servidor'] = pd.Series(dtype='int64')

    if 'vara' in df.columns:
        stats['vara'] = df['vara'].value_counts().head(10)
    else:
        stats['vara'] = pd.Series(dtype='int64')

    if 'ASSUNTO_PRINCIPAL' in df.columns:
        stats['assunto'] = df['ASSUNTO_PRINCIPAL'].value_counts().head(10)
    else:
        stats['assunto'] = pd.Series(dtype='int64')
    
    return stats

# As funções de gráfico e relatório (PDF) não precisam ser alteradas, mas foram incluídas abaixo para manter a integridade do código completo.

def criar_grafico_barras(dados, titulo, eixo_x, eixo_y):
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
    df_plot = pd.DataFrame({
        'categoria': dados.index,
        'valor': dados.values,
        'percentual': (dados.values / dados.values.sum() * 100).round(1)
    })
    
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
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'RELATÓRIO - VISÃO GERAL', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'INFORMAÇÕES GERAIS', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Total de Processos: {total_processos}', 0, 1)
    pdf.cell(0, 6, f'Data de geração: {get_local_time().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    pdf.ln(10)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'DISTRIBUIÇÃO POR POLO PASSIVO (Top 10)', 0, 1)
    pdf.set_font('Arial', '', 10)
    for polo, quantidade in stats['polo_passivo'].items():
        pdf.cell(0, 6, f'{polo}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'DISTRIBUIÇÃO POR MÊS', 0, 1)
    pdf.set_font('Arial', '', 10)
    for mes, quantidade in stats['mes'].items():
        pdf.cell(0, 6, f'Mês {mes}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'DISTRIBUIÇÃO POR SERVIDOR', 0, 1)
    pdf.set_font('Arial', '', 10)
    for servidor, quantidade in stats['servidor'].items():
        pdf.cell(0, 6, f'{servidor}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'PRINCIPAIS ASSUNTOS (Top 10)', 0, 1)
    pdf.set_font('Arial', '', 10)
    for assunto, quantidade in stats['assunto'].items():
        pdf.cell(0, 6, f'{assunto}: {quantidade}', 0, 1)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 6, f'Relatório gerado em: {get_local_time().strftime("%d/%m/%Y às %H:%M:%S")}', 0, 1)
    
    return pdf

def criar_relatorio_estatisticas(stats):
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
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'RELATÓRIO - ESTATÍSTICAS DETALHADAS', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Data de geração: {get_local_time().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    pdf.ln(10)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'POR POLO PASSIVO (Top 10)', 0, 1)
    pdf.set_font('Arial', '', 10)
    for polo, quantidade in stats['polo_passivo'].items():
        pdf.cell(0, 6, f'{polo}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'POR MÊS', 0, 1)
    pdf.set_font('Arial', '', 10)
    for mes, quantidade in stats['mes'].items():
        pdf.cell(0, 6, f'Mês {mes}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'POR SERVIDOR', 0, 1)
    pdf.set_font('Arial', '', 10)
    for servidor, quantidade in stats['servidor'].items():
        pdf.cell(0, 6, f'{servidor}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'POR VARA (Top 10)', 0, 1)
    pdf.set_font('Arial', '', 10)
    for vara, quantidade in stats['vara'].items():
        pdf.cell(0, 6, f'{vara}: {quantidade}', 0, 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'POR ASSUNTO (Top 10)', 0, 1)
    pdf.set_font('Arial', '', 10)
    for assunto, quantidade in stats['assunto'].items():
        pdf.cell(0, 6, f'{assunto}: {quantidade}', 0, 1)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 6, f'Relatório gerado em: {get_local_time().strftime("%d/%m/%Y às %H:%M:%S")}', 0, 1)
    
    return pdf

def criar_relatorio_filtros(df_filtrado, filtros_aplicados):
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
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'RELATÓRIO - FILTROS APLICADOS', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'FILTROS APLICADOS:', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, filtros_aplicados)
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Total de processos filtrados: {len(df_filtrado)}', 0, 1)
    pdf.cell(0, 6, f'Data de geração: {get_local_time().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    pdf.ln(10)
    
    if len(df_filtrado) > 0:
        pdf.set_font('Arial', 'B', 8)
        colunas = ['Nº Processo', 'Polo Ativo', 'Data', 'Orgão Julgador', 'Servidor', 'Assunto']
        larguras = [30, 35, 18, 25, 25, 55] 
        
        for i, coluna in enumerate(colunas):
            pdf.cell(larguras[i], 10, coluna, 1, 0, 'C')
        pdf.ln()
        
        pdf.set_font('Arial', '', 6)
        for _, row in df_filtrado.iterrows():
            n_processo = str(row.get('Nº Processo', ''))[:20]
            polo_ativo = str(row.get('Polo Ativo', ''))[:20]
            data_chegada = str(row.get('Data Chegada', ''))[:10]
            orgao_julgador = str(row.get('Órgão Julgador', ''))[:15]
            servidor = str(row.get('Servidor', ''))[:15]
            assunto = str(row.get('Assunto Principal', ''))[:30]
            
            pdf.cell(larguras[0], 8, n_processo, 1)
            pdf.cell(larguras[1], 8, polo_ativo, 1)
            pdf.cell(larguras[2], 8, data_chegada, 1)
            pdf.cell(larguras[3], 8, orgao_julgador, 1)
            pdf.cell(larguras[4], 8, servidor, 1)
            pdf.cell(larguras[5], 8, assunto, 1)
            pdf.ln()
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 6, f'Relatório gerado em: {get_local_time().strftime("%d/%m/%Y às %H:%M:%S")}', 0, 1)
    
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
        
def gerar_csv_edicoes(edicoes_df):
    """Gera o link de download para o CSV de edições."""
    csv_data = edicoes_df.to_csv(index=False, sep=';', encoding='utf-8-sig')
    b64 = base64.b64encode(csv_data.encode()).decode()
    nome_arquivo = f"edicoes_servidor_pje_{get_local_time().strftime('%Y%m%d_%H%M')}.csv"
    href = f'<a href="data:text/csv;base64,{b64}" download="{nome_arquivo}">💾 Baixar CSV das Edições</a>'
    return href


# --- FUNÇÃO PRINCIPAL (MAIN) ---

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>PODER JUDICIÁRIO</h1>
        <h3>JUSTIÇA FEDERAL EM PERNAMBUCO - JUIZADOS ESPECIAIS FEDERAIS</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # --- LÓGICA DE PERSISTÊNCIA E UPLOAD ---
    
    processed_df = None
    uploaded_file = None
    
    # 1. Tentar carregar dados processados do estado da sessão (persiste no F5)
    if 'processed_data' in st.session_state and st.session_state['processed_data'] is not None:
        st.success("✅ Dados carregados da sessão anterior. Faça um novo upload para substituir.")
        processed_df = st.session_state['processed_data']
        uploaded_file = 'DATA_LOADED' 
    
    # 2. Se não houver dados, exibir o uploader
    if uploaded_file is None:
        st.markdown("### 📁 Upload do Arquivo CSV do PJE")
        uploaded_file = st.file_uploader(
            "Selecione o arquivo CSV exportado do PJE",
            type=['csv'],
            help="Arquivo CSV com até 5.000 linhas, separado por ponto e vírgula"
        )

    # 3. Processar o arquivo recém-enviado
    if uploaded_file is not None and uploaded_file != 'DATA_LOADED':
        try:
            df = pd.read_csv(uploaded_file, delimiter=';', encoding='utf-8')
            
            with st.spinner('Padronizando cabeçalhos...'):
                df_padronizado = mapear_e_padronizar_colunas(df)
            
            st.success(f"✅ Arquivo carregado com sucesso! {len(df_padronizado)} processos encontrados.")
            
            with st.spinner('Processando dados...'):
                processed_df = processar_dados(df_padronizado)
                
                # SALVAR NA SESSÃO para persistir no F5
                st.session_state['processed_data'] = processed_df
                
            uploaded_file = 'DATA_LOADED'
            
        except UnicodeDecodeError:
            st.error("Erro de codificação. Certifique-se de que o arquivo está em formato CSV delimitado por ponto e vírgula (;) e com codificação UTF-8 ou Latin-1.")
            if 'processed_data' in st.session_state: del st.session_state['processed_data']
            uploaded_file = None
        except Exception as e:
            st.error(f"❌ Ocorreu um erro ao processar o arquivo. Detalhes: {e}")
            if 'processed_data' in st.session_state: del st.session_state['processed_data']
            uploaded_file = None

    # 4. Bloco de Exibição das Abas
    if uploaded_file == 'DATA_LOADED' and processed_df is not None:
        stats = criar_estatisticas(processed_df)
        
        tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "📈 Estatísticas", "🔍 Filtros Avançados"])
        
        with tab1:
            st.markdown("### 📊 Dashboard - Visão Geral")
            
            col1, col2, col3, col4 = st.columns(4)
            with col4:
                if st.button("📄 Gerar Relatório - Visão Geral", key="relatorio_visao"):
                    with st.spinner("Gerando relatório..."):
                        pdf = criar_relatorio_visao_geral(stats, len(processed_df))
                        nome_arquivo = f"relatorio_visao_geral_{get_local_time().strftime('%Y%m%d_%H%M')}.pdf"
                        href = gerar_link_download_pdf(pdf, nome_arquivo)
                        if href:
                            st.markdown(href, unsafe_allow_html=True)
            
            with col1:
                st.metric("Total de Processos", len(processed_df))
            
            with col2:
                servidores_unicos = processed_df['servidor'].nunique() if 'servidor' in processed_df.columns else 0
                st.metric("Servidores Envolvidos", servidores_unicos)
            
            with col3:
                varas_unicas = processed_df['vara'].nunique() if 'vara' in processed_df.columns else 0
                st.metric("Varas Federais", varas_unicas)
            
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
                
                with st.expander("📊 Ver dados - Distribuição por Servidor"):
                    st.dataframe(stats['servidor'])
            
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
                
                with st.expander("📊 Ver dados - Principais Assuntos"):
                    st.dataframe(stats['assunto'])
        
        with tab2:
            st.markdown("### 📈 Estatísticas Detalhadas")
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("📄 Gerar Relatório - Estatísticas", key="relatorio_estatisticas"):
                    with st.spinner("Gerando relatório..."):
                        pdf = criar_relatorio_estatisticas(stats)
                        nome_arquivo = f"relatorio_estatisticas_{get_local_time().strftime('%Y%m%d_%H%M')}.pdf"
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
        
        with tab3:
            st.markdown("### 🔍 Filtros Avançados")
            
            if 'servidor' not in processed_df.columns:
                st.error("Não foi possível processar a coluna de Servidor ('Etiquetas'/'tagsProcessoList'). Os filtros podem estar incompletos.")
                return

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
                    options=sorted(processed_df['POLO_PASSIVO'].unique()),
                    default=None
                )
                
                assunto_filter = st.multiselect(
                    "Filtrar por Assunto",
                    options=sorted(processed_df['ASSUNTO_PRINCIPAL'].dropna().unique()),
                    default=None
                )
            
            with col3:
                vara_filter = st.multiselect(
                    "Filtrar por Vara",
                    options=sorted(processed_df['vara'].unique()),
                    default=None
                )
                
                orgao_julgador_filter = st.multiselect(
                    "Filtrar por Órgão Julgador",
                    options=sorted(processed_df['ORGAO_JULGADOR'].dropna().unique()),
                    default=None
                )
            
            filtered_df = processed_df.copy()
            filtros_aplicados = []
            
            # Lógica de Filtragem
            if servidor_filter:
                filtered_df = filtered_df[filtered_df['servidor'].isin(servidor_filter)]
                filtros_aplicados.append(f"Servidor: {', '.join(servidor_filter)}")
            
            if mes_filter:
                filtered_df = filtered_df[filtered_df['mes'].isin(mes_filter)]
                filtros_aplicados.append(f"Mês: {', '.join(map(str, mes_filter))}")
            
            if polo_passivo_filter:
                filtered_df = filtered_df[filtered_df['POLO_PASSIVO'].isin(polo_passivo_filter)]
                filtros_aplicados.append(f"Polo Passivo: {', '.join(polo_passivo_filter)}")
            
            if assunto_filter:
                filtered_df = filtered_df[filtered_df['ASSUNTO_PRINCIPAL'].isin(assunto_filter)]
                filtros_aplicados.append(f"Assunto: {', '.join(assunto_filter)}")
            
            if vara_filter:
                filtered_df = filtered_df[filtered_df['vara'].isin(vara_filter)]
                filtros_aplicados.append(f"Vara: {', '.join(vara_filter)}")
                
            if orgao_julgador_filter:
                filtered_df = filtered_df[filtered_df['ORGAO_JULGADOR'].isin(orgao_julgador_filter)]
                filtros_aplicados.append(f"Órgão Julgador: {', '.join(orgao_julgador_filter)}")
            
            filtros_texto = " | ".join(filtros_aplicados) if filtros_aplicados else "Nenhum filtro aplicado"
            
            st.metric("Processos Filtrados", len(filtered_df))
            
            if len(filtered_df) > 0:
                # Exibir dados filtrados (incluindo Órgão Julgador)
                colunas_filtro = [
                    'NUMERO_PROCESSO', 'POLO_ATIVO', 'POLO_PASSIVO', 'ORGAO_JULGADOR',
                    'data_chegada_formatada', 'mes', 'dia', 'servidor', 'vara', 'ASSUNTO_PRINCIPAL'
                ]
                
                colunas_existentes = [col for col in colunas_filtro if col in filtered_df.columns]
                display_filtered = filtered_df[colunas_existentes].copy()
                
                display_filtered.columns = [
                    'Nº Processo', 'Polo Ativo', 'Polo Passivo', 'Órgão Julgador',
                    'Data Chegada', 'Mês', 'Dia', 'Servidor', 'Vara', 'Assunto Principal'
                ][:len(display_filtered.columns)]
                
                st.dataframe(display_filtered, use_container_width=True)
                
                # Botão para gerar relatório PDF
                st.markdown("---")
                st.markdown("### 📄 Gerar Relatório com Filtros")
                
                if st.button("🖨️ Gerar Relatório PDF com Filtros Atuais", key="relatorio_filtros"):
                    with st.spinner("Gerando relatório..."):
                        try:
                            pdf = criar_relatorio_filtros(display_filtered, filtros_texto)
                            nome_arquivo = f"relatorio_filtros_{get_local_time().strftime('%Y%m%d_%H%M')}.pdf"
                            href = gerar_link_download_pdf(pdf, nome_arquivo)
                            if href:
                                st.markdown(href, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Erro ao gerar PDF: {e}")
            
            else:
                st.warning("Nenhum processo encontrado com os filtros aplicados.")
                
            # --- SEÇÃO DE EDIÇÃO TEMPORÁRIA (AGRUPADA POR ASSUNTO) ---
            st.markdown("---")
            st.markdown("### ✍️ Edição Temporária de Servidor (Processos Sem Etiqueta)")

            df_sem_etiqueta = processed_df[processed_df['servidor'] == 'Sem etiqueta'].copy()

            if df_sem_etiqueta.empty:
                st.info("🎉 Excelente! Nenhum processo 'Sem etiqueta' encontrado na planilha.")
            else:
                st.info(f"Processos sem etiqueta: **{len(df_sem_etiqueta)}**")
                
                if 'edicoes_servidor' not in st.session_state:
                    st.session_state['edicoes_servidor'] = {}

                servidores_disponiveis = sorted(processed_df['servidor'].unique())
                servidores_para_atribuir = [s for s in servidores_disponiveis if s not in ["Sem etiqueta", "Não atribuído"]]
                
                # NOVO: Agrupar por Assunto Principal
                grouped_by_assunto = df_sem_etiqueta.groupby('ASSUNTO_PRINCIPAL')
                
                for assunto, group_df in grouped_by_assunto:
                    # Usar um expander para cada assunto
                    with st.expander(f"📚 **{assunto}** ({len(group_df)} processos)"):
                        
                        for index, row in group_df.iterrows():
                            num_proc = row['NUMERO_PROCESSO']
                            default_value = st.session_state['edicoes_servidor'].get(num_proc, '')
                            
                            polo_passivo = row.get('POLO_PASSIVO', 'N/D')
                            
                            # Exibe Polo Passivo (fonte menor) e Assunto
                            st.markdown(f"""
                                <p style="font-size: 11px; margin: 0; padding: 0;">Réu: **{polo_passivo}**</p>
                                <p style="font-size: 13px; margin: 0; padding: 0; margin-top: 5px;">Processo: **{num_proc}** - Data Chegada: ({row.get('data_chegada_formatada', 'N/D')})</p>
                            """, unsafe_allow_html=True)

                            # Campo de seleção editável para cada processo
                            initial_index = servidores_para_atribuir.index(default_value) + 1 if default_value in servidores_para_atribuir else 0
                            
                            novo_servidor = st.selectbox(
                                "Atribuir Servidor:", # Rótulo simplificado, visível se a edição for feita
                                options=[''] + servidores_para_atribuir,
                                key=f"edit_{num_proc}",
                                index=initial_index,
                                label_visibility='collapsed' # Oculta o label acima do selectbox
                            )
                            
                            # Atualiza o estado da sessão com a edição
                            if novo_servidor:
                                st.session_state['edicoes_servidor'][num_proc] = novo_servidor
                            elif not novo_servidor and num_proc in st.session_state['edicoes_servidor']:
                                del st.session_state['edicoes_servidor'][num_proc]
                            
                            st.markdown("---") # Linha separadora entre processos

                # 3. Gerar o CSV de Edições
                
                edicoes_validas = {k: v for k, v in st.session_state['edicoes_servidor'].items() if v}
                
                if edicoes_validas:
                    st.success(f"**{len(edicoes_validas)}** edições temporárias prontas para download.")

                    edicoes_list = []
                    for num_proc, novo_servidor in edicoes_validas.items():
                        original_row = processed_df[processed_df['NUMERO_PROCESSO'] == num_proc].iloc[0]
                        
                        orgao_vara = original_row.get('ORGAO_JULGADOR', '')
                        if orgao_vara and original_row.get('vara'):
                            orgao_vara += f" ({original_row.get('vara')})"
                        elif original_row.get('vara'):
                            orgao_vara = original_row.get('vara')

                        edicoes_list.append({
                            'NUMERO_PROCESSO': num_proc,
                            'DATA_CHEGADA': original_row.get('data_chegada_formatada', 'N/D'),
                            'ORGAO_JULGADOR_VARA': orgao_vara,
                            'NOVA_ATRIBUICAO_SERVIDOR': novo_servidor,
                            'POLO_PASSIVO': original_row.get('POLO_PASSIVO', 'N/D'),
                            'ASSUNTO': original_row.get('ASSUNTO_PRINCIPAL', 'N/D'),
                            'OBSERVACAO': 'Atribuição Temporária Feita no Painel PJE2X'
                        })
                    
                    edicoes_df = pd.DataFrame(edicoes_list)
                    
                    st.markdown(gerar_csv_edicoes(edicoes_df), unsafe_allow_html=True)
                    
                    with st.expander("Ver Edições Prontas"):
                        st.dataframe(edicoes_df, use_container_width=True)

                else:
                    st.info("Nenhuma edição temporária de servidor registrada ainda.")

    else:
        # Tela inicial quando não há arquivo e não há dados na sessão
        st.markdown("""
        <div class="upload-section">
            <h3>👋 Bem-vindo ao Sistema de Gestão de Processos Judiciais</h3>
            <p>Faça o upload do arquivo CSV exportado do PJE para começar a análise. Funciona com formatos de painel variados!</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

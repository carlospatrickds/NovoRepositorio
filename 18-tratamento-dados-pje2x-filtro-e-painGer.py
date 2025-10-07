
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
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

def get_local_time():
    """Obtém o horário local do Brasil (UTC-3)"""
    utc_now = datetime.now(timezone.utc)
    brasil_tz = timezone(timedelta(hours=-3))
    return utc_now.astimezone(brasil_tz)

def detectar_tipo_tabela(df):
    """Detecta automaticamente o tipo de tabela baseado nas colunas disponíveis"""
    colunas = df.columns.tolist()
    
    # Verificar se é tabela do Painel Gerencial (baseado no arquivo fornecido)
    colunas_painel_gerencial = ['Número do Processo', 'Classe', 'Polo Ativo', 'Polo Passivo', 'Órgão Julgador', 'Assunto']
    if all(coluna in colunas for coluna in colunas_painel_gerencial):
        return "painel_gerencial"
    
    # Verificar se é tabela do Filtro de Tarefas (baseado no código anterior)
    colunas_filtro_tarefas = ['numeroProcesso', 'poloAtivo', 'poloPassivo', 'tagsProcessoList', 'dataChegada']
    if any(coluna in colunas for coluna in colunas_filtro_tarefas):
        return "filtro_tarefas"
    
    # Tentativa de detecção por padrões de nomes de colunas
    if any('Processo' in col for col in colunas) and any('Polo' in col for col in colunas):
        return "painel_gerencial"
    
    return "desconhecido"

def processar_painel_gerencial(df):
    """Processa dados do Painel Gerencial (formato do arquivo fornecido)"""
    processed_df = df.copy()
    
    # Renomear colunas para padronização
    mapeamento_colunas = {
        'Número do Processo': 'numeroProcesso',
        'Classe': 'classe',
        'Polo Ativo': 'poloAtivo', 
        'Polo Passivo': 'poloPassivo',
        'Órgão Julgador': 'orgaoJulgador',
        'Assunto': 'assuntoPrincipal',
        'Tarefa': 'tarefa',
        'Etiquetas': 'tagsProcessoList',
        'Dias': 'dias',
        'Sigiloso': 'sigiloso',
        'Prioridade': 'prioridade',
        'Cargo Judicial': 'cargoJudicial',
        'Última Movimentação': 'ultimaMovimentacao',
        'Data Último Movimento': 'dataUltimoMovimento'
    }
    
    # Aplicar renomeação apenas para colunas existentes
    colunas_para_renomear = {k: v for k, v in mapeamento_colunas.items() if k in processed_df.columns}
    processed_df = processed_df.rename(columns=colunas_para_renomear)
    
    # Extrair informações das etiquetas
    def extrair_servidor(tags):
        if pd.isna(tags) or tags == "":
            return "Sem etiqueta"
        tags_list = str(tags).split(', ')
        for tag in tags_list:
            if 'Servidor' in tag or 'Supervisão' in tag:
                return tag
        return "Não atribuído"
    
    def extrair_vara(tags):
        if pd.isna(tags) or tags == "":
            # Tentar extrair do órgão julgador
            if 'orgaoJulgador' in processed_df.columns:
                orgao = str(processed_df.loc[processed_df['tagsProcessoList'] == tags, 'orgaoJulgador'].iloc[0]) if not processed_df[processed_df['tagsProcessoList'] == tags].empty else ""
                if 'Vara' in orgao:
                    return orgao
            return "Vara não identificada"
        
        tags_list = str(tags).split(', ')
        for tag in tags_list:
            if 'Vara Federal' in tag:
                return tag
        return "Vara não identificada"
    
    # Aplicar extração
    processed_df['servidor'] = processed_df['tagsProcessoList'].apply(extrair_servidor)
    processed_df['vara'] = processed_df['tagsProcessoList'].apply(extrair_vara)
    
    # Processar data - usar data atual como referência para Painel Gerencial
    data_atual = get_local_time()
    processed_df['data_chegada_obj'] = data_atual
    processed_df['mes'] = data_atual.month
    processed_df['dia'] = data_atual.day
    processed_df['data_chegada_formatada'] = data_atual.strftime('%d/%m/%Y')
    
    # Adicionar coluna de tipo de tabela
    processed_df['tipo_tabela'] = 'painel_gerencial'
    
    return processed_df

def processar_filtro_tarefas(df):
    """Processa dados do Filtro de Tarefas (formato original)"""
    processed_df = df.copy()
    
    # Extrair informações das etiquetas
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
    
    # Adicionar coluna de tipo de tabela
    processed_df['tipo_tabela'] = 'filtro_tarefas'
    
    # Ordenar por data de chegada (mais recente primeiro)
    if 'data_chegada_obj' in processed_df.columns:
        processed_df = processed_df.sort_values('data_chegada_obj', ascending=False)
    
    return processed_df

def processar_dados(df):
    """Processa os dados do CSV detectando automaticamente o tipo de tabela"""
    
    tipo_tabela = detectar_tipo_tabela(df)
    st.info(f"📋 Tipo de tabela detectado: {tipo_tabela.replace('_', ' ').title()}")
    
    if tipo_tabela == "painel_gerencial":
        return processar_painel_gerencial(df)
    elif tipo_tabela == "filtro_tarefas":
        return processar_filtro_tarefas(df)
    else:
        st.warning("⚠️ Tipo de tabela não reconhecido. Tentando processamento genérico...")
        # Tentativa de processamento genérico
        processed_df = df.copy()
        processed_df['tipo_tabela'] = 'desconhecido'
        return processed_df

def criar_estatisticas(df):
    """Cria estatísticas baseadas nos dados processados"""
    
    stats = {}
    
    # Verificar quais colunas estão disponíveis
    colunas_disponiveis = df.columns.tolist()
    
    # Estatísticas por Polo Passivo
    if 'poloPassivo' in colunas_disponiveis:
        polo_passivo_stats = df['poloPassivo'].value_counts().head(10)
        stats['polo_passivo'] = polo_passivo_stats
    else:
        stats['polo_passivo'] = pd.Series(dtype=int)
    
    # Estatísticas por Mês
    if 'mes' in colunas_disponiveis:
        mes_stats = df['mes'].value_counts().sort_index()
        stats['mes'] = mes_stats
    else:
        stats['mes'] = pd.Series(dtype=int)
    
    # Estatísticas por Servidor
    if 'servidor' in colunas_disponiveis:
        servidor_stats = df['servidor'].value_counts()
        stats['servidor'] = servidor_stats
    else:
        stats['servidor'] = pd.Series(dtype=int)
    
    # Estatísticas por Vara
    if 'vara' in colunas_disponiveis:
        vara_stats = df['vara'].value_counts().head(10)
        stats['vara'] = vara_stats
    else:
        stats['vara'] = pd.Series(dtype=int)
    
    # Estatísticas por Assunto
    if 'assuntoPrincipal' in colunas_disponiveis:
        assunto_stats = df['assuntoPrincipal'].value_counts().head(10)
        stats['assunto'] = assunto_stats
    else:
        stats['assunto'] = pd.Series(dtype=int)
    
    return stats

# ... (o restante das funções permanece igual: criar_grafico_barras, criar_grafico_pizza_com_legenda, 
# criar_relatorio_visao_geral, criar_relatorio_estatisticas, criar_relatorio_filtros, 
# gerar_link_download_pdf, main) ...

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
        help="Arquivo CSV do Painel Gerencial ou Filtro de Tarefas"
    )
    
    if uploaded_file is not None:
        try:
            # Ler arquivo CSV
            df = pd.read_csv(uploaded_file, delimiter=';', encoding='utf-8')
            
            # Mostrar informações básicas do arquivo
            st.success(f"✅ Arquivo carregado com sucesso! {len(df)} processos encontrados.")
            
            # Mostrar tipo de tabela detectado
            tipo_tabela = detectar_tipo_tabela(df)
            st.info(f"📋 **Tipo de tabela detectado:** {tipo_tabela.replace('_', ' ').title()}")
            
            # Processar dados
            with st.spinner('Processando dados...'):
                processed_df = processar_dados(df)
                stats = criar_estatisticas(processed_df)
            
            # Abas para organização
            tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "📈 Estatísticas", "🔍 Filtros Avançados"])
            
            with tab1:
                st.markdown("### 📊 Dashboard - Visão Geral")
                
                # Botão para gerar relatório
                col1, col2, col3, col4 = st.columns(4)
                with col4:
                    if st.button("📄 Gerar Relatório - Visão Geral", key="relatorio_visao"):
                        with st.spinner("Gerando relatório..."):
                            pdf = criar_relatorio_visao_geral(stats, len(processed_df))
                            nome_arquivo = f"relatorio_visao_geral_{get_local_time().strftime('%Y%m%d_%H%M')}.pdf"
                            href = gerar_link_download_pdf(pdf, nome_arquivo)
                            if href:
                                st.markdown(href, unsafe_allow_html=True)
                
                # Métricas principais
                with col1:
                    st.metric("Total de Processos", len(processed_df))
                
                with col2:
                    servidores_unicos = processed_df['servidor'].nunique() if 'servidor' in processed_df.columns else 0
                    st.metric("Servidores Envolvidos", servidores_unicos)
                
                with col3:
                    varas_unicas = processed_df['vara'].nunique() if 'vara' in processed_df.columns else 0
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
            
            # ... (o restante do código das abas 2 e 3 permanece igual) ...

        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
            st.info("💡 **Dica:** Verifique se o arquivo é um CSV válido do PJE com separador ponto e vírgula")
    
    else:
        # Tela inicial quando não há arquivo
        st.markdown("""
        <div class="upload-section">
            <h3>👋 Bem-vindo ao Sistema de Gestão de Processos Judiciais</h3>
            <p>Faça o upload do arquivo CSV exportado do PJE para começar a análise.</p>
            <p><strong>Tipos de arquivo suportados:</strong></p>
            <ul>
                <li>📋 Painel Gerencial PJE+R</li>
                <li>📊 Filtro de Tarefas PJE</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

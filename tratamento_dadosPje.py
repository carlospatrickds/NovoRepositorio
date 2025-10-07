import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import plotly.express as px
import plotly.graph_objects as go

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
</style>
""", unsafe_allow_html=True)

def processar_dados(df):
    """Processa os dados do CSV similar à planilha original"""
    
    # Criar cópia para não modificar o original
    processed_df = df.copy()
    
    # Processar tags - separar a coluna tagsProcessoList
    def extrair_servidor(tags):
        if pd.isna(tags):
            return "Não atribuído"
        tags_list = str(tags).split(', ')
        for tag in tags_list:
            if 'Servidor' in tag:
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
    
    def extrair_mes_data(data_str):
        if pd.isna(data_str):
            return None
        try:
            # Extrair apenas a data (ignorar hora)
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
    processed_df['mes'] = processed_df['dataChegada'].apply(extrair_mes_data)
    processed_df['dia'] = processed_df['dataChegada'].apply(extrair_dia_data)
    
    # Formatar data de chegada (apenas data)
    processed_df['data_chegada_formatada'] = processed_df['dataChegada'].apply(
        lambda x: str(x).split(',')[0] if pd.notna(x) else ''
    )
    
    return processed_df

def criar_estatisticas(df):
    """Cria estatísticas similares à planilha dados_individuais"""
    
    stats = {}
    
    # Estatísticas por Polo Passivo
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
                
                # Métricas principais
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total de Processos", len(processed_df))
                
                with col2:
                    servidores_unicos = processed_df['servidor'].nunique()
                    st.metric("Servidores Envolvidos", servidores_unicos)
                
                with col3:
                    varas_unicas = processed_df['vara'].nunique()
                    st.metric("Varas Federais", varas_unicas)
                
                with col4:
                    processos_recentes = processed_df[processed_df['mes'] == datetime.now().month].shape[0]
                    st.metric("Processos Este Mês", processos_recentes)
                
                # Gráficos principais
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de Polo Passivo
                    if not stats['polo_passivo'].empty:
                        fig_polo = px.bar(
                            x=stats['polo_passivo'].index,
                            y=stats['polo_passivo'].values,
                            title="Distribuição por Polo Passivo",
                            labels={'x': 'Polo Passivo', 'y': 'Quantidade'}
                        )
                        fig_polo.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_polo, use_container_width=True)
                
                with col2:
                    # Gráfico por Mês
                    if not stats['mes'].empty:
                        fig_mes = px.bar(
                            x=stats['mes'].index,
                            y=stats['mes'].values,
                            title="Distribuição por Mês",
                            labels={'x': 'Mês', 'y': 'Quantidade'}
                        )
                        st.plotly_chart(fig_mes, use_container_width=True)
                
                # Gráficos secundários
                col3, col4 = st.columns(2)
                
                with col3:
                    # Gráfico por Servidor
                    if not stats['servidor'].empty:
                        fig_servidor = px.pie(
                            names=stats['servidor'].index,
                            values=stats['servidor'].values,
                            title="Distribuição por Servidor"
                        )
                        st.plotly_chart(fig_servidor, use_container_width=True)
                
                with col4:
                    # Gráfico por Assunto
                    if not stats['assunto'].empty:
                        fig_assunto = px.bar(
                            x=stats['assunto'].values,
                            y=stats['assunto'].index,
                            orientation='h',
                            title="Principais Assuntos",
                            labels={'x': 'Quantidade', 'y': 'Assunto'}
                        )
                        st.plotly_chart(fig_assunto, use_container_width=True)
            
            with tab2:
                st.markdown("### 📋 Lista de Processos - Visualização Consolidada")
                
                # Seleção de colunas para exibir
                colunas_base = [
                    'numeroProcesso', 'poloAtivo', 'poloPassivo', 'data_chegada_formatada',
                    'dia', 'mes', 'servidor', 'vara', 'assuntoPrincipal'
                ]
                
                # DataFrame para exibição
                display_df = processed_df[colunas_base].copy()
                display_df.columns = [
                    'Nº Processo', 'Polo Ativo', 'Polo Passivo', 'Data Chegada',
                    'Dia', 'Mês', 'Servidor', 'Vara', 'Assunto Principal'
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
                
                # Informações de paginação
                st.write(f"Mostrando processos {start_idx + 1} a {min(end_idx, len(display_df))} de {len(display_df)}")
                
                # Botão de exportação
                if st.button("📥 Exportar para Excel"):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        display_df.to_excel(writer, sheet_name='Processos', index=False)
                    st.download_button(
                        label="⬇️ Baixar arquivo Excel",
                        data=output.getvalue(),
                        file_name=f"processos_judiciais_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.ms-excel"
                    )
            
            with tab3:
                st.markdown("### 📈 Estatísticas Detalhadas")
                
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
                    
                    vara_filter = st.multiselect(
                        "Filtrar por Vara",
                        options=sorted(processed_df['vara'].unique()),
                        default=None
                    )
                
                with col2:
                    polo_passivo_filter = st.multiselect(
                        "Filtrar por Polo Passivo",
                        options=sorted(processed_df['poloPassivo'].unique()),
                        default=None
                    )
                    
                    mes_filter = st.multiselect(
                        "Filtrar por Mês",
                        options=sorted(processed_df['mes'].dropna().unique()),
                        default=None
                    )
                
                with col3:
                    assunto_filter = st.multiselect(
                        "Filtrar por Assunto",
                        options=sorted(processed_df['assuntoPrincipal'].dropna().unique()),
                        default=None
                    )
                
                # Aplicar filtros
                filtered_df = processed_df.copy()
                
                if servidor_filter:
                    filtered_df = filtered_df[filtered_df['servidor'].isin(servidor_filter)]
                
                if vara_filter:
                    filtered_df = filtered_df[filtered_df['vara'].isin(vara_filter)]
                
                if polo_passivo_filter:
                    filtered_df = filtered_df[filtered_df['poloPassivo'].isin(polo_passivo_filter)]
                
                if mes_filter:
                    filtered_df = filtered_df[filtered_df['mes'].isin(mes_filter)]
                
                if assunto_filter:
                    filtered_df = filtered_df[filtered_df['assuntoPrincipal'].isin(assunto_filter)]
                
                st.metric("Processos Filtrados", len(filtered_df))
                
                if len(filtered_df) > 0:
                    # Exibir dados filtrados
                    display_filtered = filtered_df[colunas_base].copy()
                    display_filtered.columns = [
                        'Nº Processo', 'Polo Ativo', 'Polo Passivo', 'Data Chegada',
                        'Dia', 'Mês', 'Servidor', 'Vara', 'Assunto Principal'
                    ]
                    
                    st.dataframe(display_filtered, use_container_width=True)
                else:
                    st.warning("Nenhum processo encontrado com os filtros aplicados.")
        
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
            st.info("""
            **Dicas para solucionar problemas:**
            - Verifique se o arquivo é um CSV válido exportado do PJE
            - Confirme que o separador é ponto e vírgula (;)
            - Certifique-se de que o encoding é UTF-8
            """)
    
    else:
        # Tela inicial quando não há arquivo
        st.markdown("""
        <div class="upload-section">
            <h3>👋 Bem-vindo ao Sistema de Gestão de Processos Judiciais</h3>
            <p>Faça o upload do arquivo CSV exportado do PJE para começar a análise.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### 📋 Como usar:
        
        1. **Exporte o CSV do PJE** com os dados dos processos
        2. **Faça o upload** do arquivo usando o seletor acima
        3. **Visualize os dados** processados nas diferentes abas
        4. **Analise as estatísticas** e exporte os resultados
        
        ### 🎯 Funcionalidades:
        
        - **Processamento automático** de tags e datas
        - **Dashboard interativo** com gráficos e métricas
        - **Tabela filtrada** similar à sua planilha "base"
        - **Estatísticas detalhadas** como "dados_individuais"
        - **Filtros avançados** para análise específica
        - **Exportação** para Excel
        """)

if __name__ == "__main__":
    main()

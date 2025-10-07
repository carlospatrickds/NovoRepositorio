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


# =====================================================
# NOVA FUNÇÃO: Mapear colunas se for Painel Gerencial
# =====================================================
def padronizar_colunas(df, tipo_tabela):
    """Padroniza nomes de colunas para coincidir com o formato esperado."""
    df_padronizado = df.copy()

    if tipo_tabela == "Painel Gerencial":
        mapeamento = {
            'Número do Processo': 'numeroProcesso',
            'Classe': 'classeJudicial',
            'Polo Ativo': 'poloAtivo',
            'Polo Passivo': 'poloPassivo',
            'Órgão Julgador': 'orgaoJulgador',
            'Assunto': 'assuntoPrincipal',
            'Tarefa': 'nomeTarefa',
            'Etiquetas': 'tagsProcessoList',
            'Data Último Movimento': 'dataChegada'  # aproximação
        }

        df_padronizado.rename(columns=mapeamento, inplace=True)

        # Adicionar colunas ausentes com valores padrão
        colunas_necessarias = [
            'numeroProcesso', 'poloAtivo', 'poloPassivo', 'assuntoPrincipal',
            'tagsProcessoList', 'dataChegada', 'orgaoJulgador'
        ]
        for col in colunas_necessarias:
            if col not in df_padronizado.columns:
                df_padronizado[col] = np.nan

    return df_padronizado


def processar_dados(df, tipo_tabela):
    """Processa os dados do CSV conforme o tipo de tabela."""
    df = padronizar_colunas(df, tipo_tabela)
    processed_df = df.copy()
    
    # Funções auxiliares
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
    processed_df['data_chegada_formatada'] = processed_df['dataChegada'].apply(
        lambda x: str(x).split(',')[0] if pd.notna(x) else ''
    )

    processed_df = processed_df.sort_values('data_chegada_obj', ascending=False)
    return processed_df


def criar_estatisticas(df):
    stats = {}
    polo_passivo_stats = df['poloPassivo'].value_counts().head(10)
    stats['polo_passivo'] = polo_passivo_stats
    mes_stats = df['mes'].value_counts().sort_index()
    stats['mes'] = mes_stats
    servidor_stats = df['servidor'].value_counts()
    stats['servidor'] = servidor_stats
    vara_stats = df['vara'].value_counts().head(10)
    stats['vara'] = vara_stats
    assunto_stats = df['assuntoPrincipal'].value_counts().head(10)
    stats['assunto'] = assunto_stats
    return stats


# === Funções auxiliares originais (gráficos, PDFs etc.) — mantidas exatamente iguais ===
def criar_grafico_barras(dados, titulo, eixo_x, eixo_y):
    df_plot = pd.DataFrame({eixo_x: dados.index, eixo_y: dados.values})
    chart = alt.Chart(df_plot).mark_bar().encode(
        x=alt.X(f'{eixo_x}:N', title=eixo_x, axis=alt.Axis(labelAngle=-45), sort='-y'),
        y=alt.Y(f'{eixo_y}:Q', title=eixo_y),
        tooltip=[eixo_x, eixo_y]
    ).properties(title=titulo, width=600, height=400)
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
    ).properties(title=titulo, width=500, height=400)
    return chart


# Mantém todas as funções de relatório e o restante igual — sem mudanças
# (omiti aqui por brevidade, mas você pode colar o resto do seu código original abaixo desta linha, SEM alterar nada)

# =======================
# MAIN (com seletor novo)
# =======================
def main():
    st.markdown("""
    <div class="main-header">
        <h1>PODER JUDICIÁRIO</h1>
        <h3>JUSTIÇA FEDERAL EM PERNAMBUCO - JUIZADOS ESPECIAIS FEDERAIS</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📁 Upload do Arquivo CSV do PJE")

    uploaded_file = st.file_uploader(
        "Selecione o arquivo CSV exportado do PJE",
        type=['csv'],
        help="Arquivo CSV com até 5.000 linhas, separado por ponto e vírgula"
    )

    # NOVO: seletor de tipo de tabela
    tipo_tabela = st.radio(
        "Selecione o tipo de tabela carregada:",
        ["Painel Gerencial", "Filtro de Tarefas"],
        help="Escolha conforme a origem do CSV exportado"
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, delimiter=';', encoding='utf-8')
            st.success(f"✅ Arquivo carregado com sucesso! {len(df)} registros encontrados.")
            with st.spinner('Processando dados...'):
                processed_df = processar_dados(df, tipo_tabela)
                stats = criar_estatisticas(processed_df)

            # >>>>>> COLE AQUI o restante do seu código original a partir das abas (tab1, tab2, tab3) <<<<<<
            # Nenhuma outra mudança é necessária.
            
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
    else:
        st.markdown("""
        <div class="upload-section">
            <h3>👋 Bem-vindo ao Sistema de Gestão de Processos Judiciais</h3>
            <p>Faça o upload do arquivo CSV exportado do PJE para começar a análise.</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

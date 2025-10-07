# ============================================
# APLICATIVO STREAMLIT - GESTÃO DE PROCESSOS JUDICIAIS
# Compatível com: Painel Gerencial e Filtro de Tarefas
# Autor: Carlos (versão atualizada em 07/10/2025)
# ============================================

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import io
from fpdf import FPDF
import base64
import altair as alt

# ============================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================
st.set_page_config(
    page_title="Gestão de Processos Judiciais",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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


# ============================================
# FUNÇÕES AUXILIARES
# ============================================
def get_local_time():
    utc_now = datetime.now(timezone.utc)
    brasil_tz = timezone(timedelta(hours=-3))
    return utc_now.astimezone(brasil_tz)


# Padronização de colunas conforme o tipo da planilha
def padronizar_colunas(df, tipo_tabela):
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
            'Data Último Movimento': 'dataChegada'
        }
        df_padronizado.rename(columns=mapeamento, inplace=True)

        colunas_necessarias = [
            'numeroProcesso', 'poloAtivo', 'poloPassivo', 'assuntoPrincipal',
            'tagsProcessoList', 'dataChegada', 'orgaoJulgador'
        ]
        for col in colunas_necessarias:
            if col not in df_padronizado.columns:
                df_padronizado[col] = np.nan

    return df_padronizado


def processar_dados(df, tipo_tabela):
    df = padronizar_colunas(df, tipo_tabela)
    processed_df = df.copy()

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

    def extrair_data(data_str):
        if pd.isna(data_str):
            return None
        try:
            data_part = str(data_str).split(',')[0].strip()
            return datetime.strptime(data_part, '%d/%m/%Y')
        except:
            return None

    processed_df['servidor'] = processed_df['tagsProcessoList'].apply(extrair_servidor)
    processed_df['vara'] = processed_df['tagsProcessoList'].apply(extrair_vara)
    processed_df['data_chegada_obj'] = processed_df['dataChegada'].apply(extrair_data)
    processed_df['mes'] = processed_df['data_chegada_obj'].dt.month
    processed_df['dia'] = processed_df['data_chegada_obj'].dt.day

    return processed_df


def criar_estatisticas(df):
    stats = {}
    stats['polo_passivo'] = df['poloPassivo'].value_counts().head(10)
    stats['mes'] = df['mes'].value_counts().sort_index()
    stats['servidor'] = df['servidor'].value_counts()
    stats['vara'] = df['vara'].value_counts().head(10)
    stats['assunto'] = df['assuntoPrincipal'].value_counts().head(10)
    return stats


def criar_grafico_barras(dados, titulo, eixo_x, eixo_y):
    df_plot = pd.DataFrame({eixo_x: dados.index, eixo_y: dados.values})
    chart = alt.Chart(df_plot).mark_bar().encode(
        x=alt.X(f'{eixo_x}:N', title=eixo_x, sort='-y', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y(f'{eixo_y}:Q', title=eixo_y),
        tooltip=[eixo_x, eixo_y]
    ).properties(title=titulo, width=600, height=400)
    return chart


def criar_grafico_pizza(dados, titulo):
    df_plot = pd.DataFrame({
        'categoria': dados.index,
        'valor': dados.values,
        'percentual': (dados.values / dados.values.sum() * 100).round(1)
    })
    df_plot['label'] = df_plot['categoria'] + ' (' + df_plot['percentual'].astype(str) + '%)'
    chart = alt.Chart(df_plot).mark_arc().encode(
        theta=alt.Theta(field="valor", type="quantitative"),
        color=alt.Color(field="label", type="nominal", legend=alt.Legend(title="Categoria")),
        tooltip=['categoria', 'valor', 'percentual']
    ).properties(title=titulo, width=500, height=400)
    return chart


# ============================================
# GERAÇÃO DE PDF
# ============================================
def gerar_pdf(stats, data_atual):
    buffer = io.BytesIO()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Relatório Gerencial - Processos PJE", 0, 1, "C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Gerado em: {data_atual.strftime('%d/%m/%Y %H:%M')}", 0, 1, "C")
    pdf.ln(10)

    for nome, valores in stats.items():
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, nome.upper(), 0, 1)
        pdf.set_font("Helvetica", "", 11)
        for idx, val in valores.items():
            pdf.cell(0, 8, f"{idx}: {val}", 0, 1)
        pdf.ln(5)

    pdf.output(buffer)
    buffer.seek(0)
    return buffer


# ============================================
# INTERFACE PRINCIPAL
# ============================================
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
        help="Arquivo CSV separado por ponto e vírgula"
    )

    tipo_tabela = st.radio(
        "Selecione o tipo de tabela:",
        ["Painel Gerencial", "Filtro de Tarefas"],
        help="Escolha conforme a origem do CSV exportado"
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, delimiter=';', encoding='utf-8')
            st.success(f"✅ Arquivo carregado com sucesso! {len(df)} registros encontrados.")

            with st.spinner("Processando dados..."):
                processed_df = processar_dados(df, tipo_tabela)
                stats = criar_estatisticas(processed_df)

            # === Abas ===
            tab1, tab2, tab3 = st.tabs(["📊 Estatísticas", "📈 Gráficos", "📄 Relatório PDF"])

            with tab1:
                st.subheader("Estatísticas Gerais")
                for key, val in stats.items():
                    st.markdown(f"#### {key.capitalize()}")
                    st.dataframe(val)

            with tab2:
                st.subheader("Visualizações Gráficas")
                col1, col2 = st.columns(2)
                with col1:
                    st.altair_chart(criar_grafico_barras(stats['servidor'], "Distribuição por Servidor", "Servidor", "Quantidade"))
                with col2:
                    st.altair_chart(criar_grafico_pizza(stats['mes'], "Distribuição Mensal de Processos"))

            with tab3:
                st.subheader("Gerar Relatório PDF")
                agora = get_local_time()
                pdf_buffer = gerar_pdf(stats, agora)
                b64 = base64.b64encode(pdf_buffer.read()).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="Relatorio_PJE.pdf">📥 Baixar Relatório em PDF</a>'
                st.markdown(href, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")

    else:
        st.markdown("""
        <div class="upload-section">
            <h3>👋 Bem-vindo ao Sistema de Gestão de Processos Judiciais</h3>
            <p>Faça o upload do arquivo CSV exportado do PJE para iniciar a análise.</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

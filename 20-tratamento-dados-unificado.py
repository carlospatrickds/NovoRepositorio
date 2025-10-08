# 20-tratamento-dados-unificado.py
# Versão unificada do app Streamlit para leitura dos dois tipos de CSV do PJe2x

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import io
import altair as alt
from fpdf import FPDF
import base64

# --- CONFIGURAÇÕES E CSS ---

st.set_page_config(
    page_title="Gestão de Processos Judiciais Unificada",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {text-align: center; padding: 1rem 0; border-bottom: 2px solid #e0e0e0; margin-bottom: 2rem;}
    .upload-section {border: 2px dashed #dee2e6; border-radius: 0.5rem; padding: 2rem; text-align: center; margin-bottom: 2rem;}
    .assunto-destaque {background-color: #fff3cd; padding: 0.5rem; border-radius: 0.25rem; border-left: 4px solid #ffc107; margin: 0.5rem 0; font-weight: 500;}
</style>
""", unsafe_allow_html=True)

# --- MAPEAMENTO DE COLUNAS ---

COLUNA_MAP = {
    'NUMERO_PROCESSO': ['Número do Processo', 'numeroProcesso'],
    'POLO_ATIVO': ['Polo Ativo', 'poloAtivo'],
    'POLO_PASSIVO': ['Polo Passivo', 'poloPassivo'],
    'ORGAO_JULGADOR': ['Órgão Julgador', 'orgaoJulgador'],
    'ASSUNTO_PRINCIPAL': ['Assunto', 'assuntoPrincipal'],
    'TAREFA': ['Tarefa', 'nomeTarefa'],
    'ETIQUETAS': ['Etiquetas', 'tagsProcessoList'],
    'DIAS': ['Dias'],
    'DATA_CHEGADA_RAW': ['Data Último Movimento', 'dataChegada']
}

# --- FUNÇÕES AUXILIARES ---

def get_local_time():
    utc_now = datetime.now(timezone.utc)
    brasil_tz = timezone(timedelta(hours=-3))
    return utc_now.astimezone(brasil_tz)

def mapear_e_padronizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    colunas_padronizadas = {}
    for padrao, possiveis in COLUNA_MAP.items():
        coluna_encontrada = next((col for col in possiveis if col in df.columns), None)
        if coluna_encontrada:
            colunas_padronizadas[coluna_encontrada] = padrao
    df.rename(columns=colunas_padronizadas, inplace=True)
    return df

def extrair_data_chegada(data_str):
    if pd.isna(data_str):
        return None
    data_str = str(data_str).strip()
    try:
        # Caso "dd/mm/yyyy, hh:mm:ss"
        data_part = data_str.split(',')[0]
        return datetime.strptime(data_part, '%d/%m/%Y')
    except:
        pass
    try:
        # Caso timestamp numérico (milissegundos ou segundos)
        if data_str.isdigit():
            ts = int(data_str)
            if ts > 253402300799:  # milissegundos
                ts /= 1000
            return datetime.fromtimestamp(ts)
    except:
        pass
    return None

def processar_dados(df):
    df = df.copy()
    if 'ETIQUETAS' not in df.columns:
        st.error("Coluna de etiquetas ('Etiquetas' ou 'tagsProcessoList') não encontrada.")
        return df

    def extrair_servidor(tags):
        if pd.isna(tags):
            return "Sem etiqueta"
        tags_list = str(tags).split(', ')
        for tag in tags_list:
            if 'Servidor' in tag or 'Supervisão' in tag:
                return tag
        return "Sem etiqueta"

    def extrair_vara(tags):
        if pd.isna(tags):
            return "Vara não identificada"
        tags_list = str(tags).split(', ')
        for tag in tags_list:
            if 'Vara Federal' in tag:
                return tag
        return "Vara não identificada"

    df['servidor'] = df['ETIQUETAS'].apply(extrair_servidor)
    df['vara'] = df['ETIQUETAS'].apply(extrair_vara)

    if 'DATA_CHEGADA_RAW' in df.columns:
        df['data_chegada_obj'] = df['DATA_CHEGADA_RAW'].apply(extrair_data_chegada)
        df = df[df['data_chegada_obj'].notna()]
        df['mes'] = df['data_chegada_obj'].dt.month
        df['ano'] = df['data_chegada_obj'].dt.year
        df['mes_ano'] = df['data_chegada_obj'].dt.strftime('%m/%Y')
        df['data_chegada_formatada'] = df['data_chegada_obj'].dt.strftime('%d/%m/%Y')
        if 'DIAS' not in df.columns:
            data_ref = get_local_time()
            df['DIAS'] = (data_ref - df['data_chegada_obj']).dt.days.astype(int)
        df.sort_values('data_chegada_obj', ascending=False, inplace=True)

    return df

# --- INTERFACE STREAMLIT ---

def main():
    st.markdown("""<div class='main-header'><h1>PODER JUDICIÁRIO</h1>
    <h3>JUSTIÇA FEDERAL EM PERNAMBUCO - JUIZADOS ESPECIAIS FEDERAIS</h3></div>""", unsafe_allow_html=True)

    st.markdown("### 📁 Upload do Arquivo CSV do PJE")
    uploaded_file = st.file_uploader("Selecione o arquivo CSV exportado do PJE", type=['csv'])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, delimiter=';', encoding='utf-8', on_bad_lines='skip')
            df = mapear_e_padronizar_colunas(df)
            df_proc = processar_dados(df)

            st.success(f"✅ Arquivo carregado com sucesso! {len(df_proc)} processos encontrados.")
            st.dataframe(df_proc.head(50))

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
    else:
        st.markdown("""<div class='upload-section'><h3>📤 Faça o upload do arquivo CSV do PJE</h3>
        <p>Suporta os formatos: Painel Gerencial e Cálculo - Elaborar</p></div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

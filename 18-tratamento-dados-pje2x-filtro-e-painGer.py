import streamlit as st
import pandas as pd
import numpy as np

# --- 1. Mapeamento e Funções de Processamento de Dados ---

# Mapeamento de colunas: Novo Nome (Padrão) -> Lista de Nomes Possíveis nos CSVs
COLUNA_MAP = {
    'NUMERO_PROCESSO': ['Número do Processo', 'numeroProcesso'],
    'POLO_ATIVO': ['Polo Ativo', 'poloAtivo'],
    'POLO_PASSIVO': ['Polo Passivo', 'poloPassivo'],
    'ORGAO_JULGADOR': ['Órgão Julgador', 'orgaoJulgador'],
    'ASSUNTO': ['Assunto', 'assuntoPrincipal'],
    'TAREFA': ['Tarefa', 'nomeTarefa'],
    'DIAS': ['Dias'],  # Coluna 'Dias' do primeiro arquivo
    'DATA_CHEGADA': ['Data Último Movimento', 'dataChegada'] # Para calcular 'DIAS' no segundo arquivo
}

def padronizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza os nomes das colunas e calcula 'DIAS' se necessário."""
    
    colunas_padronizadas = {}
    for padrao, possiveis in COLUNA_MAP.items():
        # Encontra o nome da coluna que existe no arquivo atual
        coluna_encontrada = next((col for col in possiveis if col in df.columns), None)
        
        if coluna_encontrada:
            colunas_padronizadas[coluna_encontrada] = padrao

    # Renomeia as colunas do DataFrame
    df.rename(columns=colunas_padronizadas, inplace=True)
    
    # Adiciona a coluna 'DIAS' se não existir, mas tiver 'DATA_CHEGADA'
    if 'DATA_CHEGADA' in df.columns and 'DIAS' not in df.columns:
        st.info("Calculando a coluna 'DIAS' a partir de 'DATA_CHEGADA'...")
        try:
            # Converte a data de chegada para datetime. 
            # A data pode vir com horário (CSV do PJE+R) ou ser apenas a data (modelotester)
            # Tentativa 1: Modelo PJE+R com timestamp no final
            df['DATA_REF'] = df['DATA_CHEGADA'].astype(str).str.split(',').str[0]
            
            # Tentativa de conversão de data, pode falhar em diferentes formatos
            df['DATA_REF'] = pd.to_datetime(df['DATA_REF'], format='%d/%m/%Y', errors='coerce')

            # Se a conversão acima falhar, tentar converter o timestamp do PJE+R 
            # (Exemplo: 1750190530868 para o 1º CSV)
            if df['DATA_REF'].isnull().all() and 'Data Último Movimento' in colunas_padronizadas.keys():
                 # Se for o timestamp do primeiro arquivo: 
                 # O valor na coluna "Data Último Movimento" do primeiro arquivo (Processos_Painel_Gerencial_PJE+R_07-10-2025_14-51.csv)
                 # é um timestamp Unix com milissegundos.
                df['DATA_REF'] = pd.to_datetime(df['DATA_CHEGADA'], unit='ms', errors='coerce')

            # Define a data de referência como a data de extração original (07/10/2025)
            data_referencia = pd.to_datetime('2025-10-07')
            
            # Calcula a diferença em dias
            df['DIAS'] = (data_referencia - df['DATA_REF']).dt.days
            
            # Limpa colunas temporárias
            df.drop(columns=['DATA_REF'], inplace=True)
            
        except Exception as e:
            st.error(f"Erro ao calcular a coluna 'DIAS' a partir da data. Verifique o formato da data no seu arquivo. Erro: {e}")
            df['DIAS'] = np.nan
    
    # Converte 'DIAS' para numérico, tratando erros e valores vazios
    if 'DIAS' in df.columns:
        df['DIAS'] = pd.to_numeric(df['DIAS'], errors='coerce')
        df['DIAS'] = df['DIAS'].fillna(0).astype(int) # Preenche NaNs com 0 para evitar erros no Streamlit

    return df

def executar_analises(df: pd.DataFrame):
    """Executa e exibe as análises solicitadas."""
    st.header("Resultados das Análises:")
    
    # --- Análise 1: Contagem de Processos por Órgão Julgador ---
    if 'ORGAO_JULGADOR' in df.columns:
        st.subheader("1. Contagem de Processos por Órgão Julgador")
        contagem_orgao = df['ORGAO_JULGADOR'].value_counts().reset_index()
        contagem_orgao.columns = ['Órgão Julgador', 'Total de Processos']
        st.dataframe(contagem_orgao, use_container_width=True)
    else:
        st.warning("Coluna 'Órgão Julgador' não encontrada para esta análise.")

    # --- Análise 2: Média de Dias na Tarefa Específica ---
    tarefa_alvo = '[JEF] Cálculo - Elaborar'
    if 'DIAS' in df.columns and 'TAREFA' in df.columns:
        st.subheader(f"2. Média de Dias na Tarefa: **{tarefa_alvo}**")
        
        # Filtra e calcula a média apenas se houver dados
        df_calculo = df[df['TAREFA'] == tarefa_alvo]
        if not df_calculo.empty:
            media_dias = df_calculo['DIAS'].mean()
            st.metric(label="Média de Dias (Processos na Tarefa)", value=f"{media_dias:,.2f} dias")
            
            # Tabela de suporte para a média
            st.write(f"Detalhe: {df_calculo.shape[0]} processo(s) encontrado(s) na tarefa.")
        else:
            st.info(f"Nenhum processo encontrado para a tarefa '{tarefa_alvo}' no arquivo.")
    else:
        st.warning("Colunas 'DIAS' ou 'TAREFA' não encontradas para esta análise.")

    # --- Análise 3: Top 5 Assuntos Mais Comuns ---
    if 'ASSUNTO' in df.columns:
        st.subheader("3. Top 5 Assuntos Mais Comuns")
        top_assuntos = df['ASSUNTO'].value_counts().nlargest(5).reset_index()
        top_assuntos.columns = ['Assunto', 'Total de Processos']
        st.dataframe(top_assuntos, use_container_width=True)
    else:
        st.warning("Coluna 'Assunto' não encontrada para esta análise.")

# --- 2. Interface Streamlit ---

st.set_page_config(
    page_title="Analisador de Painel de Processos Unificado",
    layout="wide"
)

st.title("📊 Analisador de Painel de Processos (PJE+R)")
st.markdown("Este aplicativo analisa automaticamente seus arquivos CSV do painel gerencial, padronizando os cabeçalhos de colunas diferentes.")

# Seção de upload de arquivo
uploaded_file = st.file_uploader(
    "**Escolha o seu arquivo CSV (Delimitado por ';')**", 
    type=['csv']
)

if uploaded_file is not None:
    try:
        # Carrega o arquivo, usando o delimitador correto (;)
        df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
        
        # Exibe o cabeçalho para confirmação
        st.subheader("Arquivo Carregado com Sucesso")
        st.caption("Primeiras 5 linhas do seu arquivo:")
        st.dataframe(df.head(), use_container_width=True)

        # Processamento e análise
        df_processado = padronizar_colunas(df.copy())
        
        # Garante que as colunas padronizadas existem antes de prosseguir
        if any(col in df_processado.columns for col in COLUNA_MAP.keys()):
            executar_analises(df_processado)
        else:
            st.error("Não foi possível identificar as colunas essenciais (Órgão Julgador, Tarefa, Assunto) no arquivo. Verifique o formato do cabeçalho.")

    except UnicodeDecodeError:
        st.error("Erro de codificação. Certifique-se de que o arquivo está em formato CSV delimitado por ponto e vírgula (;) e com codificação UTF-8 ou Latin-1.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo. Detalhes: {e}")

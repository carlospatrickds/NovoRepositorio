import streamlit as st
from datetime import date, timedelta, datetime
from collections import defaultdict
import locale
import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from fpdf import FPDF
import tempfile
from io import StringIO
from unidecode import unidecode
from workalendar.america import Brazil

# Configuração inicial
st.set_page_config(page_title="Multa Corrigida por Mês", layout="centered")

# Criação das abas
abas = st.tabs(["📘 Aplicação", "📄 Tutorial da Multa"])

# === FUNÇÃO GERAR PDF - MOVIDA PARA O TOPO ===
def gerar_pdf(res, numero_processo, nome_autor, nome_reu, observacao=None):
    try:
        FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        pdf = FPDF()
        pdf.add_page()
        
        # Configurar margens menores
        pdf.set_margins(left=10, top=10, right=10)
        
        # === ADICIONAR LOGO CENTRALIZADA ===
        try:
            # URL da sua imagem no GitHub (usando raw.githubusercontent.com)
            logo_url = "https://raw.githubusercontent.com/carlospatrickds/NovoRepositorio/main/logjfpe.png"
            
            # Baixar a imagem
            response = requests.get(logo_url)
            response.raise_for_status()
            
            # Salvar temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                tmp_img.write(response.content)
                tmp_img_path = tmp_img.name
            
            # Adicionar logo centralizada no topo
            # Calcular posição centralizada: (largura_página - largura_imagem) / 2
            largura_pagina = 190  # 210mm - 10mm de margem esquerda - 10mm direita
            largura_imagem = 80   # Ajuste conforme necessário
            posicao_x = (largura_pagina - largura_imagem) / 2 + 10  # +10 para compensar margem
            
            pdf.image(tmp_img_path, x=posicao_x, y=8, w=largura_imagem)
            pdf.ln(40)  # Espaço após a logo
            
            # Limpar arquivo temporário
            import os
            os.unlink(tmp_img_path)
            
        except Exception as img_error:
            st.warning(f"Não foi possível carregar a logo: {img_error}")
            # Cabeçalho alternativo sem logo
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, unidecode("Relatório de Multa Diária Corrigida"), ln=True, align="C")
            pdf.ln(5)
        
        # Configurar a fonte (com fallback)
        try:
            pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
            pdf.set_font("DejaVu", size=10)
        except:
            pdf.set_font("Arial", size=10)
            st.warning("Fonte DejaVu não encontrada, usando Arial como fallback.")
        
        # Dados do processo (AGORA ABAIXO DA LOGO)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, unidecode(f"Número do Processo: {numero_processo}"), ln=True)
        pdf.cell(0, 8, unidecode(f"Autor: {nome_autor}"), ln=True)
        pdf.cell(0, 8, unidecode(f"Réu: {nome_reu}"), ln=True)
        pdf.ln(10)

        # Detalhamento das Faixas
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, unidecode("Detalhamento das Faixas:"), ln=True)
        pdf.set_font("Arial", "", 10)

        for i, faixa in enumerate(st.session_state.faixas):
            # CALCULA DIAS CORRETAMENTE BASEADO NO TIPO SELECIONADO
            if faixa.get("dias_uteis", False):
                cal = Brazil()
                dia = faixa["inicio"]
                dias_contabilizados = 0
                while dia <= faixa["fim"]:
                    if cal.is_working_day(dia) and dia.weekday() < 5:  # Dias úteis
                        dias_contabilizados += 1
                    dia += timedelta(days=1)
                dias_contabilizados = max(0, dias_contabilizados - faixa.get("dias_abatidos", 0))
                tipo_dias = "dias úteis"
            else:
                dias_contabilizados = (faixa["fim"] - faixa["inicio"]).days + 1 - faixa.get("dias_abatidos", 0)
                tipo_dias = "dias corridos"
            
            linha = (
                f"Faixa {i+1}: {faixa['inicio'].strftime('%d/%m/%Y')} a {faixa['fim'].strftime('%d/%m/%Y')} | "
                f"{dias_contabilizados} {tipo_dias} | "
                f"Valor: {moeda_br(faixa['valor'])}/dia | "
                f"Total: {moeda_br(dias_contabilizados * faixa['valor'])}"
            )
            pdf.multi_cell(0, 6, unidecode(linha))
            pdf.ln(2)

        pdf.ln(5)

        # Atualização da multa
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, unidecode("Atualização da multa:"), ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(90, 6, unidecode(f"Data de atualização:"), 0, 0)
        pdf.cell(0, 6, unidecode(f"{res['data_atualizacao'].strftime('%d/%m/%Y')}"), ln=True)
        pdf.cell(90, 6, unidecode(f"Total de dias em atraso:"), 0, 0)
        pdf.cell(0, 6, unidecode(f"{res['total_dias']}"), ln=True)
        pdf.cell(90, 6, unidecode(f"Multa sem correção:"), 0, 0)
        pdf.cell(0, 6, unidecode(f"{moeda_br(res['total_sem_correcao'])}"), ln=True)

        # Detalhamento mensal
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, unidecode("Correção mês a mês:"), ln=True)
        pdf.set_font("Arial", "", 10)

        for mes in res["meses_ordenados"]:
            bruto = res["totais_mensais"][mes]
            indice = res["indices"].get(mes, 0.0)
            corrigido = bruto * (1 + indice)
            data_formatada = f"{mes[5:]}/{mes[:4]}"
            linha = f"{data_formatada}: {moeda_br(bruto)} x {indice*100:.2f}% = {moeda_br(corrigido)}"
            pdf.cell(0, 6, unidecode(linha), ln=True)

        # Multa corrigida final
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(90, 6, unidecode(f"Multa corrigida:"), 0, 0)
        pdf.cell(0, 6, unidecode(f"{moeda_br(res['total_corrigido'])}"), ln=True)

        pdf.ln(8)

        # Observação
        if observacao and observacao.strip():
            pdf.ln(3)
            pdf.set_font("Arial", "I", 8)
            pdf.multi_cell(0, 6, f"Observação: {unidecode(observacao.strip())}")
        
        # Rodapé
        pdf.ln(8)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(
            0, 6,
            "Nota: A correção foi realizada com base na taxa SELIC acumulada, conforme fatores disponíveis no site do Banco Central do Brasil",
            ln=True
        )

        pdf.ln(6)
        pdf.cell(
            0, 6,
            "Este documento é assinado e datado eletronicamente.",
            ln=True
        )
        
        # Gerar PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            pdf.output(tmp_file.name)
            tmp_file.seek(0)
            return tmp_file.read()

    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# === ABA TUTORIAL DA MULTA ===
with abas[1]:
    st.markdown("## 📄 Quando começa a multa por descumprimento da obrigação de fazer?")
    st.markdown("""
### 📌 Situação exemplo:
- **Tipo de documento**: Intimação para Obrigação de Fazer  
- **Representante**: Procuradoria da CEAB-DJ INSS  
- **Expedição eletrônica**: `25/02/2025 14:25:47`  
- **Sistema registrou ciência**: `07/03/2025 23:59:59`  
- **Prazo concedido**: 20 dias

---

### 📅 Contagem de prazo (para cumprimento):
- O prazo começa no **dia útil seguinte à ciência**, ou seja: `08/03/2025`
- A contagem é **corrida**, se não houver disposição em contrário
- O prazo termina em: `04/04/2025 às 23:59:59`

---

### ❗ Início da Multa:
- A multa começa a contar **a partir de 05/04/2025**
- Ou seja, no **dia seguinte ao término do prazo** sem o cumprimento da obligação

---

### 📚 Base legal e entendimento:
- Art. 219, caput, do CPC: prazos são contados **em dias úteis** apenas para prazos processuais — não se aplicando automaticamente às obrigações de fazer.
- Jurisprudência considera que a multa inicia no **1º dia após o término do prazo concedido na intimação**, se não houver cumprimento.

> “Considera-se em mora o devedor a partir do momento em que se esgota o prazo conferido judicialmente para o cumprimento da obrigação.” (STJ)
    """)

# === ABA APLICAÇÃO ===
with abas[0]:
    st.title("📅 Cálculo de Multa Diária Corrigida por Faixa")
    st.markdown("""
Adicione faixas de multa com valores diferentes. O total por mês será corrigido por índice informado manualmente ou automaticamente pela SELIC.<br>\n
<b>Dias úteis</b>: Considera apenas dias de segunda a sexta-feira.<br>
<b>Dias abatidos</b>: Dias que não devem ser contabilizados (ex: feriados e prazos suspensos).
""", unsafe_allow_html=True)

# Função para configurar locale brasileiro
def set_brazilian_locale():
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        return True
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
            return True
        except locale.Error:
            return False

br_locale_ok = set_brazilian_locale()

def moeda_br(valor):
    """Formata valor para moeda brasileira"""
    if br_locale_ok:
        return locale.currency(valor, grouping=True)
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Função para obter taxas SELIC com tratamento robusto
def get_selic_rates():
    """Obtém taxas SELIC do repositório GitHub com tratamento robusto"""
    url = "https://raw.githubusercontent.com/carlospatrickds/vscode_python/master/selic.csv"
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        meses_pt_eng = {
            'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr',
            'mai': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug',
            'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec',
            'mr': 'Mar', 'det': 'Dec'  # Tratamento para erros comuns
        }
        
        dados = []
        for linha in response.text.split('\n'):
            linha = linha.strip()
            if ';' in linha:
                partes = linha.split(';')
                if len(partes) >= 2:
                    mes_ano = partes[0].strip().lower()
                    taxa = partes[1].strip()
                    
                    # Extrai mês (3 primeiras letras)
                    mes = mes_ano[:3]
                    
                    # Remove caracteres especiais do ano
                    ano = ''.join(c for c in mes_ano[3:] if c.isdigit())
                    
                    # Corrige anos com 2 dígitos (assume 2000+)
                    if len(ano) == 2:
                        ano = '20' + ano
                    elif len(ano) == 1:
                        ano = '200' + ano
                    
                    # Limpa a taxa (remove caracteres não numéricos)
                    taxa_limpa = ''.join(c for c in taxa.replace(',', '.') if c.isdigit() or c == '.')
                    
                    if mes in meses_pt_eng and ano and taxa_limpa:
                        try:
                            mes_eng = meses_pt_eng[mes]
                            data = f"{mes_eng}/{ano}"
                            taxa_float = float(taxa_limpa)
                            dados.append({'Data': data, 'Taxa': taxa_float})
                        except (ValueError, KeyError):
                            continue
        
        if not dados:
            st.error("Nenhum dado válido encontrado no arquivo SELIC")
            return None
            
        # Cria DataFrame e converte datas
        df = pd.DataFrame(dados)
        df['Data'] = pd.to_datetime(df['Data'], format='%b/%Y', errors='coerce')
        df = df.dropna(subset=['Data', 'Taxa'])
        df = df.sort_values('Data')
        
        return df[['Data', 'Taxa']]

    except Exception as e:
        st.error(f"Erro ao carregar dados SELIC: {str(e)}")
        if 'response' in locals():
            st.error(f"Conteúdo recebido (primeiros 200 caracteres): {response.text[:200]}")
        return None

def calcular_correcao_selic(totais_mensais, data_atualizacao):
    """Calcula correção pela SELIC"""
    selic_data = get_selic_rates()
    if selic_data is None:
        st.error("Dados SELIC não disponíveis para cálculo")
        return None

    # Garante que data_atualizacao seja datetime
    if isinstance(data_atualizacao, date):
        data_atualizacao = datetime(data_atualizacao.year, data_atualizacao.month, data_atualizacao.day)

    indices_selic = {}
    meses_ordenados = sorted(totais_mensais.keys())

    for mes_str in meses_ordenados:
        ano, mes = map(int, mes_str.split('-'))
        data_mes = datetime(ano, mes, 1)

        fator_correcao = 1.0
        data_correcao = data_mes

        while data_correcao <= data_atualizacao:
            # Filtra usando ano e mês diretamente
            mes_data = selic_data[
                (selic_data['Data'].dt.year == data_correcao.year) & 
                (selic_data['Data'].dt.month == data_correcao.month)
            ]
            
            if not mes_data.empty:
                taxa_mes = mes_data.iloc[0]['Taxa']
                fator_correcao *= (1 + taxa_mes)
            
            # Avança para o próximo mês
            if data_correcao.month == 12:
                data_correcao = datetime(data_correcao.year + 1, 1, 1)
            else:
                data_correcao = datetime(data_correcao.year, data_correcao.month + 1, 1)

        indice_percentual = (fator_correcao - 1) * 100
        indices_selic[mes_str] = indice_percentual

    return indices_selic

def distribuir_valores_por_mes(inicio, fim, valor_diario, dias_uteis=False, dias_abatidos=0):
    """Distribui valores por mês considerando dias úteis e abatidos"""
    valores_mes = defaultdict(float)
    cal = Brazil() if dias_uteis else None
    
    dia = inicio
    dias_totais = 0
    
    while dia <= fim:
        if not dias_uteis or (cal.is_working_day(dia) and dia.weekday() < 5):
            chave = dia.strftime("%Y-%m")
            valores_mes[chave] += valor_diario
            dias_totais += 1
        dia += timedelta(days=1)
    
    # Aplica abatimento de dias (prazo suspenso)
    dias_totais = max(0, dias_totais - dias_abatidos)
    
    # Redistribui o valor considerando os dias abatidos
    if dias_abatidos > 0:
        fator = dias_totais / (dias_totais + dias_abatidos) if (dias_totais + dias_abatidos) > 0 else 0
        for mes in valores_mes:
            valores_mes[mes] *= fator
    
    return valores_mes, dias_totais

# Funções de manipulação de faixas
def remover_faixa(idx):
    """Remove faixa pelo índice"""
    if 0 <= idx < len(st.session_state.faixas):
        st.session_state.faixas.pop(idx)

def adicionar_faixa(nova_faixa):
    """Adiciona nova faixa"""
    st.session_state.faixas.append(nova_faixa)

# Inicialização do session state
if "faixas" not in st.session_state:
    st.session_state.faixas = []

# Interface de adição de faixas
with st.form("nova_faixa", clear_on_submit=True):
    # Configura datas padrão
    if st.session_state.faixas:
        data_inicio_padrao = st.session_state.faixas[-1]["fim"] + timedelta(days=1)
    else:
        data_inicio_padrao = date(2025, 1, 7)
    
    data_fim_padrao = data_inicio_padrao + timedelta(days=5)

    # Campos do formulário
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input(
            "Início da faixa",
            value=data_inicio_padrao,
            format="DD/MM/YYYY"
        )
    with col2:
        data_fim = st.date_input(
            "Fim da faixa",
            value=data_fim_padrao,
            format="DD/MM/YYYY"
        )
    
    valor_diario = st.number_input(
        "Valor diário (R$)",
        min_value=0.0,
        step=1.0,
        value=50.0
    )
    
    tipo_dias = st.selectbox(
        "Tipo de contagem",
        ["Dias úteis", "Dias corridos"],
        index=0
    )
    
    dias_abatidos = st.number_input(
        "Dias abatidos (prazo suspenso)",
        min_value=0,
        max_value=50,
        value=0,
        step=1
    )

    # Botão de submit
    submitted = st.form_submit_button("➕ Adicionar faixa")

    if submitted:
        if data_inicio <= data_fim:
            st.session_state.faixas.append({
                "inicio": data_inicio,
                "fim": data_fim,
                "valor": valor_diario,
                "dias_uteis": tipo_dias == "Dias úteis",
                "dias_abatidos": dias_abatidos
            })
            st.rerun()
        else:
            st.error("A data final deve ser igual ou posterior à data inicial!")

# Lista faixas adicionadas
if st.session_state.faixas:
    st.markdown("### ✅ Faixas adicionadas:")
    for i, f in enumerate(st.session_state.faixas):
        col1, col2, col3 = st.columns([4, 3, 1])
        with col1:
            st.markdown(
                f"- Faixa {i+1}: {f['inicio'].strftime('%d/%m/%Y')} a {f['fim'].strftime('%d/%m/%Y')} – {moeda_br(f['valor'])}/dia"
            )
            st.caption(f"Tipo: {'Dias úteis' if f.get('dias_uteis', False) else 'Dias corridos'} | Dias abatidos: {f.get('dias_abatidos', 0)}")
        
        with col2:
            # Permite edição dos parâmetros
            novo_tipo = st.selectbox(
                "Alterar tipo de contagem",
                ["Dias corridos", "Dias úteis"],
                index=1 if f.get("dias_uteis", False) else 0,
                key=f"edit_tipo_{i}"
            )
            
            novos_dias_abatidos = st.number_input(
                "Alterar dias abatidos",
                min_value=0,
                max_value=50,
                value=f.get("dias_abatidos", 0),
                key=f"edit_dias_{i}"
            )
            
            # Atualiza a faixa com as novas informações
            st.session_state.faixas[i]["dias_uteis"] = novo_tipo == "Dias úteis"
            st.session_state.faixas[i]["dias_abatidos"] = novos_dias_abatidos
        
        with col3:
            if st.button(f"🗑️ Excluir", key=f"excluir_{i}"):
                remover_faixa(i)
                st.rerun()

st.markdown("---")

# Data de atualização
st.subheader("📅 Data de atualização dos índices")
data_atualizacao = st.date_input("Data de atualização", value=date.today(), format="DD/MM/YYYY")

# Link para tabela CJF
st.markdown("### 🔗 Acesso rápido ao site do Banco Central")
if st.button("Abrir site do BC"):
    js = "window.open('https://www.bcb.gov.br/estabilidadefinanceira/selicfatoresacumulados')"
    st.components.v1.html(f"<script>{js}</script>", height=0, width=0)

# Cálculo dos totais mensais
totais_mensais = defaultdict(float)
total_dias = 0
for faixa in st.session_state.faixas:
    distribuido, dias_faixa = distribuir_valores_por_mes(
        faixa["inicio"], 
        faixa["fim"], 
        faixa["valor"],
        dias_uteis=faixa.get("dias_uteis", False),
        dias_abatidos=faixa.get("dias_abatidos", 0)
    )
    for mes, valor in distribuido.items():
        totais_mensais[mes] += valor
    total_dias += dias_faixa

# Seção de índices
st.subheader("📊 Índices por mês (%)")
if st.button("🔍 Carregar índices SELIC automaticamente"):
    with st.spinner("Calculando correção SELIC..."):
        indices_selic = calcular_correcao_selic(totais_mensais, data_atualizacao)
        if indices_selic:
            st.session_state.indices_selic = indices_selic
            st.success("Índices SELIC calculados com sucesso!")
            st.json({k: f"{v:.2f}%" for k, v in indices_selic.items()})
        else:
            st.error("Não foi possível calcular os índices. Verifique os dados de entrada.")

meses_ordenados = sorted(totais_mensais.keys())
indices = {}
indices_selic_carregados = st.session_state.get('indices_selic', {})

for mes in meses_ordenados:
    col1, col2 = st.columns([1.2, 3])
    with col1:
        data_formatada = f"{mes[5:]}/{mes[:4]}"
        st.markdown(f"**{data_formatada}**")
    with col2:
        valor_padrao = indices_selic_carregados.get(mes, 0.0)
        indice = st.number_input(
            f"Índice (%) - {data_formatada}", 
            key=f"indice_{mes}", 
            value=float(valor_padrao), 
            step=0.01, 
            format="%.2f"
        )
        indices[mes] = indice / 100

# Cálculo final - VERSÃO CORRIGIDA
if st.button("💰 Calcular Multa Corrigida"):
    try:
        # Debug: verificar se há dados para calcular
        if not totais_mensais:
            st.error("Nenhuma faixa adicionada para cálculo.")
            st.stop()
            
        if not meses_ordenados:
            st.error("Nenhum mês encontrado para cálculo.")
            st.stop()
            
        total_sem_correcao = sum(totais_mensais.values())
        total_corrigido = 0.0

        for mes in meses_ordenados:
            bruto = totais_mensais[mes]
            indice = indices.get(mes, 0.0)
            fator = 1 + indice
            corrigido = bruto * fator
            total_corrigido += corrigido

        st.session_state.resultado_multa = {
            "total_dias": total_dias,
            "total_sem_correcao": total_sem_correcao,
            "total_corrigido": total_corrigido,
            "data_atualizacao": data_atualizacao,
            "meses_ordenados": meses_ordenados,
            "totais_mensais": totais_mensais,
            "indices": indices,
        }
        
        st.success("Cálculo concluído com sucesso!")
        
    except Exception as e:
        st.error(f"Erro durante o cálculo: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

# Exibição dos resultados - VERSÃO CORRIGIDA
if "resultado_multa" in st.session_state:
    try:
        res = st.session_state.resultado_multa
        
        # Verifica se os dados necessários existem
        if not res or "meses_ordenados" not in res:
            st.error("Erro nos dados calculados. Tente novamente.")
        else:
            st.subheader("📋 Detalhamento por mês:")
            for mes in res["meses_ordenados"]:
                bruto = res["totais_mensais"][mes]
                indice = res["indices"].get(mes, 0.0)
                corrigido = bruto * (1 + indice)
                data_formatada = f"{mes[5:]}/{mes[:4]}"
                if indice == 0.0:
                    st.markdown(f"- **{data_formatada}**: {moeda_br(bruto)}")
                else:
                    st.markdown(f"- **{data_formatada}**: base {moeda_br(bruto)} + índice {indice*100:.2f}% → corrigido: {moeda_br(corrigido)}")

            st.markdown("---")
            st.subheader("✅ Resultado Final")
            st.markdown(f"- **Total de dias em atraso:** {res['total_dias']}")
            st.markdown(f"- **Multa sem correção:** {moeda_br(res['total_sem_correcao'])}")
            st.markdown(f"- **Multa corrigida até {res['data_atualizacao'].strftime('%m/%Y')}:** {moeda_br(res['total_corrigido'])}")
            
    except Exception as e:
        st.error(f"Erro ao exibir resultados: {str(e)}")
        st.error("Por favor, verifique os dados e tente novamente.")

# Formulário para PDF - VERSÃO CORRIGIDA
if "resultado_multa" in st.session_state:
    with st.expander("📄 Gerar Relatório PDF", expanded=True):
        col1, col2 = st.columns([2, 3])
        
        with col1:
            numero_processo = st.text_input("Nº do Processo", key="proc_input")
            nome_autor = st.text_input("Autor", key="autor_input")
            nome_reu = st.text_input("Réu", key="reu_input")
            
        with col2:
            observacao = st.text_area("Observações", height=206, key="obs_input")

        if st.button("🖨️ Gerar PDF", type="primary", key="pdf_button"):
            if not numero_processo:
                st.error("Informe o número do processo")
            else:
                with st.spinner("Gerando documento..."):
                    try:
                        pdf_data = gerar_pdf(
                            st.session_state.resultado_multa,
                            numero_processo,
                            nome_autor,
                            nome_reu,
                            observacao
                        )
                        if pdf_data:
                            st.download_button(
                                "⬇️ Baixar PDF",
                                pdf_data,
                                file_name=f"relatorio_{numero_processo}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"Erro ao gerar PDF: {str(e)}")

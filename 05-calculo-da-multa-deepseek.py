import streamlit as st
from datetime import date, timedelta, datetime
from collections import defaultdict
import locale
import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from fpdf import FPDF
import tempfile
from workalendar.america import Brazil

# =========================
# Funções utilitárias
# =========================

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
    if br_locale_ok:
        return locale.currency(valor, grouping=True)
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calcular_data_final(data_inicio, num_dias, dias_uteis=False):
    cal = Brazil() if dias_uteis else None
    if dias_uteis:
        data_final = data_inicio
        dias_contados = 1  # Começa contando o próprio dia inicial
        while dias_contados < num_dias:
            data_final += timedelta(days=1)
            if cal.is_working_day(data_final) and data_final.weekday() < 5:
                dias_contados += 1
    else:
        data_final = data_inicio + timedelta(days=num_dias - 1)
    return data_final

def get_selic_rates():
    url = "https://raw.githubusercontent.com/carlospatrickds/vscode_python/master/selic.csv"
    try:
        response = requests.get(url)
        response.raise_for_status()
        meses_pt_eng = {
            'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr',
            'mai': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug',
            'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec',
            'mr': 'Mar', 'det': 'Dec'
        }
        dados = []
        for linha in response.text.split('\n'):
            linha = linha.strip()
            if ';' in linha:
                partes = linha.split(';')
                if len(partes) >= 2:
                    mes_ano = partes[0].strip().lower()
                    taxa = partes[1].strip()
                    mes = mes_ano[:3]
                    ano = ''.join(c for c in mes_ano[3:] if c.isdigit())
                    if len(ano) == 2:
                        ano = '20' + ano
                    elif len(ano) == 1:
                        ano = '200' + ano
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
    selic_data = get_selic_rates()
    if selic_data is None:
        st.error("Dados SELIC não disponíveis para cálculo")
        return None
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
            mes_data = selic_data[
                (selic_data['Data'].dt.year == data_correcao.year) & 
                (selic_data['Data'].dt.month == data_correcao.month)
            ]
            if not mes_data.empty:
                taxa_mes = mes_data.iloc[0]['Taxa']
                fator_correcao *= (1 + taxa_mes)
            if data_correcao.month == 12:
                data_correcao = datetime(data_correcao.year + 1, 1, 1)
            else:
                data_correcao = datetime(data_correcao.year, data_correcao.month + 1, 1)
        indice_percentual = (fator_correcao - 1) * 100
        indices_selic[mes_str] = indice_percentual
    return indices_selic

def distribuir_valores_por_mes(inicio, fim, valor_diario, dias_uteis=False, dias_abatidos=0):
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
    dias_totais = max(0, dias_totais - dias_abatidos)
    if dias_abatidos > 0:
        fator = dias_totais / (dias_totais + dias_abatidos) if (dias_totais + dias_abatidos) > 0 else 0
        for mes in valores_mes:
            valores_mes[mes] *= fator
    return valores_mes, dias_totais

def remover_faixa(idx):
    if 0 <= idx < len(st.session_state.faixas):
        st.session_state.faixas.pop(idx)
        st.experimental_rerun()

def gerar_pdf(res, numero_processo, nome_autor, nome_reu, observacao=None, fonte_obs="Arial", tam_obs=8):
    try:
        FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(left=10, top=10, right=10)
        try:
            if fonte_obs == "DejaVu":
                pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
            pdf.set_font("DejaVu" if fonte_obs == "DejaVu" else "Arial", size=10)
        except:
            pdf.set_font("Arial", size=10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Relatório de Multa Diária Corrigida", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, f"Número do Processo: {numero_processo}", ln=True)
        pdf.cell(0, 6, f"Autor: {nome_autor}", ln=True)
        pdf.cell(0, 6, f"Réu: {nome_reu}", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Cálculo do Início da Multa:", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(90, 6, "Data do despacho/intimação:", 0, 0)
        pdf.cell(0, 6, res['data_despacho'].strftime('%d/%m/%Y'), ln=True)
        pdf.cell(90, 6, "Prazo para cumprimento:", 0, 0)
        pdf.cell(0, 6, f"{res['prazo_cumprimento']} {res['tipo_prazo'].lower()}", ln=True)
        pdf.cell(90, 6, "Fim do prazo:", 0, 0)
        pdf.cell(0, 6, res['data_fim_prazo'].strftime('%d/%m/%Y'), ln=True)
        pdf.cell(90, 6, "Início da multa:", 0, 0)
        pdf.cell(0, 6, res['data_inicio_multa'].strftime('%d/%m/%Y'), ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Detalhamento das Faixas:", ln=True)
        pdf.set_font("Arial", "", 10)
        for i, faixa in enumerate(st.session_state.faixas):
            if faixa.get("dias_uteis", False):
                cal = Brazil()
                dia = faixa["inicio"]
                dias_contabilizados = 0
                while dia <= faixa["fim"]:
                    if cal.is_working_day(dia) and dia.weekday() < 5:
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
            pdf.multi_cell(0, 6, linha)
            pdf.ln(2)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Atualização da multa:", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(90, 6, "Data de atualização:", 0, 0)
        pdf.cell(0, 6, res['data_atualizacao'].strftime('%d/%m/%Y'), ln=True)
        pdf.cell(90, 6, "Total de dias em atraso:", 0, 0)
        pdf.cell(0, 6, f"{res['total_dias']}", ln=True)
        pdf.cell(90, 6, "Multa sem correção:", 0, 0)
        pdf.cell(0, 6, moeda_br(res['total_sem_correcao']), ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Correção mês a mês:", ln=True)
        pdf.set_font("Arial", "", 10)
        for mes in res["meses_ordenados"]:
            bruto = res["totais_mensais"][mes]
            indice = res["indices"].get(mes, 0.0)
            corrigido = bruto * (1 + indice)
            data_formatada = f"{mes[5:]}/{mes[:4]}"
            linha = f"{data_formatada}: {moeda_br(bruto)} x {indice*100:.2f}% = {moeda_br(corrigido)}"
            pdf.cell(0, 6, linha, ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(90, 6, "Multa corrigida:", 0, 0)
        pdf.cell(0, 6, moeda_br(res['total_corrigido']), ln=True)
        pdf.ln(8)
        if observacao and observacao.strip():
            pdf.ln(3)
            pdf.set_font(fonte_obs, "I", tam_obs)
            pdf.multi_cell(0, 6, f"Observação: {observacao.strip()}")
        pdf.ln(8)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(
            0, 6,
            "Nota: A correção foi realizada com base na taxa SELIC acumulada, conforme fatores disponíveis no site do Banco Central do Brasil",
            ln=True
        )
        pdf.ln(6)
        pdf.set_font("Arial", size=10)
        pdf.cell(
            0, 6,
            "Documento é assinado e datado eletronicamente.",
            ln=True
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            pdf.output(tmp_file.name)
            tmp_file.seek(0)
            return tmp_file.read()
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# =========================
# Interface Streamlit
# =========================

st.set_page_config(page_title="Multa Corrigida por Mês", layout="centered")
abas = st.tabs(["📘 Aplicação", "📄 Tutorial da Multa"])

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
- Ou seja, no **dia seguinte ao término do prazo** sem o cumprimento da obrigação

---

### 📚 Base legal e entendimento:
- Art. 219, caput, do CPC: prazos são contados **em dias úteis** apenas para prazos processuais — não se aplicando automaticamente às obrigações de fazer.
- Jurisprudência considera que a multa inicia no **1º dia após o término do prazo concedido na intimação**, se não houver cumprimento.

> "Considera-se em mora o devedor a partir do momento em que se esgota o prazo conferido judicialmente para o cumprimento da obrigação." (STJ)
    """)

with abas[0]:
    st.title("📅 Cálculo de Multa Diária Corrigida por Faixa")
    st.markdown("""
Adicione faixas de multa com valores diferentes. O total por mês será corrigido por índice informado manualmente ou automaticamente pela SELIC.<br>
<b>Dias úteis</b>: Considera apenas dias de segunda a sexta-feira.<br>
<b>Dias abatidos</b>: Dias que não devem ser contabilizados (ex: feriados e prazos suspensos).
""", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Data de Início da Multa")
    col_despacho, col_prazo = st.columns(2)
    with col_despacho:
        data_despacho = st.date_input(
            "Data do despacho/intimação",
            value=date.today(),
            format="DD/MM/YYYY",
            help="Data em que foi publicado o despacho ou intimação"
        )
    with col_prazo:
        prazo_cumprimento = st.number_input(
            "Prazo para cumprimento (dias)",
            min_value=1,
            max_value=365,
            value=15,
            step=1,
            help="Prazo em dias para cumprimento da obrigação"
        )
        tipo_prazo = st.selectbox(
            "Tipo de prazo",
            ["Dias úteis", "Dias corridos"],
            index=0,
            help="Se o prazo para cumprimento conta apenas dias úteis ou dias corridos"
        )
    def calcular_inicio_multa(data_despacho, prazo_dias, dias_uteis=False):
        cal = Brazil() if dias_uteis else None
        if dias_uteis:
            data_fim_prazo = data_despacho
            dias_contados = 1
            while dias_contados < prazo_dias:
                data_fim_prazo += timedelta(days=1)
                if cal.is_working_day(data_fim_prazo) and data_fim_prazo.weekday() < 5:
                    dias_contados += 1
        else:
            data_fim_prazo = data_despacho + timedelta(days=prazo_dias - 1)
        data_inicio_multa = data_fim_prazo + timedelta(days=1)
        return data_fim_prazo, data_inicio_multa

    data_fim_prazo, data_inicio_multa = calcular_inicio_multa(
        data_despacho, 
        prazo_cumprimento, 
        tipo_prazo == "Dias úteis"
    )
    col_result1, col_result2 = st.columns(2)
    with col_result1:
        st.info(f"**Fim do prazo:** {data_fim_prazo.strftime('%d/%m/%Y')}")
    with col_result2:
        st.success(f"**Início da multa:** {data_inicio_multa.strftime('%d/%m/%Y')}")
    st.markdown("---")

    # ==== Faixa Dinâmica ====
    if "faixas" not in st.session_state:
        st.session_state.faixas = []
    if "modo_entrada" not in st.session_state:
        st.session_state.modo_entrada = "Definir data final"
    if "indices_selic" not in st.session_state:
        st.session_state.indices_selic = {}

    modo_entrada = st.radio(
        "Como deseja definir a faixa?",
        ["Definir data final", "Definir número de dias"],
        horizontal=True,
        key="modo_entrada"
    )

    if st.session_state.faixas:
        data_inicio_padrao = st.session_state.faixas[-1]["fim"] + timedelta(days=1)
    else:
        data_inicio_padrao = data_inicio_multa

    data_inicio = st.date_input("Início da faixa", value=data_inicio_padrao, key="data_inicio_faixa")

    if st.session_state.modo_entrada == "Definir número de dias":
        num_dias = st.number_input("Número de dias", min_value=1, max_value=365, value=5, step=1, key="num_dias_faixa")
        tipo_dias = st.selectbox("Tipo de contagem", ["Dias úteis", "Dias corridos"], index=0, key="tipo_dias_faixa")
        data_fim = calcular_data_final(data_inicio, num_dias, tipo_dias == "Dias úteis")
        st.info(f"**Data final calculada:** {data_fim.strftime('%d/%m/%Y')}")
    else:
        data_fim = st.date_input("Fim da faixa", value=data_inicio + timedelta(days=5), key="data_fim_faixa")
        tipo_dias = st.selectbox("Tipo de contagem", ["Dias úteis", "Dias corridos"], index=0, key="tipo_dias_faixa")

    # Só adicionar faixa com botão
    with st.form("nova_faixa", clear_on_submit=True):
        valor_diario = st.number_input("Valor diário (R$)", min_value=0.0, step=1.0, value=50.0, key="valor_faixa")
        dias_abatidos = st.number_input("Dias abatidos (prazo suspenso)", min_value=0, max_value=50, value=0, step=1, key="abatidos_faixa")
        submitted = st.form_submit_button("➕ Adicionar faixa")
        if submitted:
            st.session_state.faixas.append({
                "inicio": data_inicio,
                "fim": data_fim,
                "valor": valor_diario,
                "dias_uteis": tipo_dias == "Dias úteis",
                "dias_abatidos": dias_abatidos
            })
            st.success("Faixa adicionada!")

    if st.session_state.faixas:
        st.markdown("### ✅ Faixas adicionadas:")
        for i, f in enumerate(st.session_state.faixas):
            col1, col2, col3 = st.columns([4, 3, 1])
            with col1:
                if f.get("dias_uteis", False):
                    cal = Brazil()
                    dia = f["inicio"]
                    dias_contabilizados = 0
                    while dia <= f["fim"]:
                        if cal.is_working_day(dia) and dia.weekday() < 5:
                            dias_contabilizados += 1
                        dia += timedelta(days=1)
                    dias_contabilizados = max(0, dias_contabilizados - f.get("dias_abatidos", 0))
                else:
                    dias_contabilizados = (f["fim"] - f["inicio"]).days + 1 - f.get("dias_abatidos", 0)
                st.markdown(
                    f"- Faixa {i+1}: {f['inicio'].strftime('%d/%m/%Y')} a {f['fim'].strftime('%d/%m/%Y')} – {moeda_br(f['valor'])}/dia"
                )
                st.caption(f"Tipo: {'Dias úteis' if f.get('dias_uteis', False) else 'Dias corridos'} | Dias: {dias_contabilizados} | Dias abatidos: {f.get('dias_abatidos', 0)}")
            with col2:
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
                st.session_state.faixas[i]["dias_uteis"] = novo_tipo == "Dias úteis"
                st.session_state.faixas[i]["dias_abatidos"] = novos_dias_abatidos
            with col3:
                if st.button(f"🗑️ Excluir", key=f"excluir_{i}"):
                    remover_faixa(i)
    st.markdown("---")

    # ... (restante do código para índices, cálculo, detalhamento e PDF permanece igual ao anterior)
# ... [todo o código anterior permanece] ...

    # ---------- A PARTIR DAQUI SEGUE O RESTANTE COMPLETO ------------

    st.markdown("---")
    st.subheader("📅 Data de atualização dos índices")
    data_atualizacao = st.date_input("Data de atualização", value=date.today(), format="DD/MM/YYYY")

    st.markdown("### 🔗 Acesso rápido ao site do Banco Central")
    if st.button("Abrir site do BC"):
        js = "window.open('https://www.bcb.gov.br/estabilidadefinanceira/selicfatoresacumulados')"
        st.components.v1.html(f"<script>{js}</script>", height=0, width=0)

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

    st.subheader("📊 Índices por mês (%)")
    if st.button("🔍 Carregar índices SELIC automaticamente"):
        with st.spinner("Calculando correção SELIC..."):
            indices_selic = calcular_correcao_selic(totais_mensais, data_atualizacao)
            if indices_selic:
                st.session_state.indices_selic = indices_selic
                for mes, valor in indices_selic.items():
                    st.session_state[f"indice_{mes}"] = float(valor)
                st.success("Índices SELIC calculados com sucesso!")
                st.json({k: f"{v:.2f}%" for k, v in indices_selic.items()})
            else:
                st.error("Não foi possível calcular os índices. Verifique os dados de entrada.")

    meses_ordenados = sorted(totais_mensais.keys())
    indices = {}
    indices_selic_carregados = st.session_state.get('indices_selic', {})

    for mes in meses_ordenados:
        valor_padrao = indices_selic_carregados.get(mes, 0.0)
        key = f"indice_{mes}"
        if key not in st.session_state:
            st.session_state[key] = float(valor_padrao)

    for mes in meses_ordenados:
        col1, col2 = st.columns([1.2, 3])
        with col1:
            data_formatada = f"{mes[5:]}/{mes[:4]}"
            st.markdown(f"**{data_formatada}**")
        with col2:
            key = f"indice_{mes}"
            indice = st.number_input(
                f"Índice (%) - {data_formatada}", 
                key=key, 
                value=st.session_state[key],
                step=0.01, 
                format="%.2f"
            )
            indices[mes] = indice / 100

    if st.button("💰 Calcular Multa Corrigida"):
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
            "data_despacho": data_despacho,
            "prazo_cumprimento": prazo_cumprimento,
            "tipo_prazo": tipo_prazo,
            "data_fim_prazo": data_fim_prazo,
            "data_inicio_multa": data_inicio_multa
        }

    # Detalhamento visual bonito
    if "resultado_multa" in st.session_state:
        res = st.session_state.resultado_multa
        detalhamento = []
        for mes in res["meses_ordenados"]:
            bruto = res["totais_mensais"][mes]
            indice = res["indices"].get(mes, 0.0)
            corrigido = bruto * (1 + indice)
            data_formatada = f"{mes[5:]}/{mes[:4]}"
            detalhamento.append([data_formatada, moeda_br(bruto), f"{indice*100:.2f}%", moeda_br(corrigido)])
        df_detalhamento = pd.DataFrame(detalhamento, columns=["Mês/Ano", "Base", "Índice", "Corrigido"])
        st.markdown("### 🗒️ Detalhamento por mês:")
        st.table(df_detalhamento)

        st.markdown("---")
        st.subheader("✅ Resultado Final")
        st.markdown(f"- **Data de início da multa:** {res['data_inicio_multa'].strftime('%d/%m/%Y')}")
        st.markdown(f"- **Total de dias em atraso:** {res['total_dias']}")
        st.markdown(f"- **Multa sem correção:** {moeda_br(res['total_sem_correcao'])}")
        st.markdown(f"- **Multa corrigida até {res['data_atualizacao'].strftime('%m/%Y')}:** {moeda_br(res['total_corrigido'])}")

        with st.expander("📄 Gerar Relatório PDF", expanded=True):
            col1, col2 = st.columns([2, 3])
            with col1:
                numero_processo = st.text_input("Nº do Processo", key="proc_input")
                nome_autor = st.text_input("Autor", key="autor_input")
                nome_reu = st.text_input("Réu", key="reu_input")
                fonte_obs = st.selectbox("Fonte das observações", ["Arial", "DejaVu"], key="fonte_obs")
                tam_obs = st.slider("Tamanho da fonte das observações", 8, 10, 8, key="tam_obs")
            with col2:
                observacao = st.text_area("Observações", height=415, key="obs_input")
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
                                observacao,
                                fonte_obs,
                                tam_obs
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

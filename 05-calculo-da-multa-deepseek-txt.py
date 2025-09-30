# ======= Funções de Salvar/Abrir Arquivo =======
import json
import base64

def salvar_dados():
    """Salva todos os dados atuais em um arquivo JSON codificado"""
    dados = {
        "data_despacho": st.session_state.get("data_despacho", date.today()).isoformat(),
        "prazo_cumprimento": st.session_state.get("prazo_cumprimento", 15),
        "tipo_prazo": st.session_state.get("tipo_prazo", "Dias úteis"),
        "faixas": [
            {
                "inicio": faixa["inicio"].isoformat(),
                "fim": faixa["fim"].isoformat(),
                "valor": faixa["valor"],
                "dias_uteis": faixa.get("dias_uteis", False),
                "dias_abatidos": faixa.get("dias_abatidos", 0)
            }
            for faixa in st.session_state.get("faixas", [])
        ],
        "data_atualizacao": st.session_state.get("data_atualizacao", date.today()).isoformat(),
        "indices_selic": st.session_state.get("indices_selic", {}),
        "indices_manuais": {
            key: value for key, value in st.session_state.items() 
            if key.startswith("indice_") and isinstance(value, (int, float))
        }
    }
    
    # Codifica os dados em base64 para evitar problemas de encoding
    dados_json = json.dumps(dados, ensure_ascii=False, indent=2)
    dados_codificados = base64.b64encode(dados_json.encode('utf-8')).decode('utf-8')
    
    return dados_codificados

def carregar_dados(dados_codificados):
    """Carrega dados de um arquivo JSON codificado"""
    try:
        dados_json = base64.b64decode(dados_codificados.encode('utf-8')).decode('utf-8')
        dados = json.loads(dados_json)
        
        # Restaura os dados principais
        st.session_state.data_despacho = date.fromisoformat(dados["data_despacho"])
        st.session_state.prazo_cumprimento = dados["prazo_cumprimento"]
        st.session_state.tipo_prazo = dados["tipo_prazo"]
        st.session_state.data_atualizacao = date.fromisoformat(dados["data_atualizacao"])
        
        # Restaura as faixas
        st.session_state.faixas = []
        for faixa in dados["faixas"]:
            st.session_state.faixas.append({
                "inicio": date.fromisoformat(faixa["inicio"]),
                "fim": date.fromisoformat(faixa["fim"]),
                "valor": faixa["valor"],
                "dias_uteis": faixa.get("dias_uteis", False),
                "dias_abatidos": faixa.get("dias_abatidos", 0)
            })
        
        # Restaura índices SELIC
        st.session_state.indices_selic = dados.get("indices_selic", {})
        
        # Restaura índices manuais
        for key, value in dados.get("indices_manuais", {}).items():
            st.session_state[key] = value
            
        st.success("Dados carregados com sucesso!")
        
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {str(e)}")

def limpar_dados():
    """Limpa todos os dados atuais"""
    st.session_state.faixas = []
    st.session_state.indices_selic = {}
    st.session_state.data_despacho = date.today()
    st.session_state.prazo_cumprimento = 15
    st.session_state.tipo_prazo = "Dias úteis"
    st.session_state.data_atualizacao = date.today()
    
    # Limpa índices manuais
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith("indice_")]
    for key in keys_to_remove:
        del st.session_state[key]
    
    st.success("Dados limpos com sucesso!")

    st.markdown("### 🔗 Acesso rápido ao site do Banco Central")
    if st.button("Abrir site do BC"):
        js = "window.open('https://www.bcb.gov.br/estabilidadefinanceira/selicfatoresacumulados')"
        st.components.v1.html(f"<script>{js}</script>", height=0, width=0)

    # === NOVA SEÇÃO: SALVAR E ABRIR ARQUIVO ===
    st.markdown("---")
    st.subheader("💾 Salvar / Abrir Projeto")
    
    col_salvar, col_abrir, col_limpar = st.columns(3)
    
    with col_salvar:
        st.markdown("**Salvar projeto atual**")
        dados_salvos = salvar_dados()
        st.download_button(
            label="💾 Salvar Arquivo",
            data=dados_salvos,
            file_name=f"multa_calculada_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            help="Salva todos os dados atuais em um arquivo para usar depois"
        )
    
    with col_abrir:
        st.markdown("**Abrir projeto salvo**")
        arquivo_carregado = st.file_uploader(
            "Selecione o arquivo .txt",
            type=['txt'],
            key="file_uploader",
            label_visibility="collapsed"
        )
        if arquivo_carregado is not None:
            dados_carregados = arquivo_carregado.read().decode('utf-8')
            if st.button("📂 Carregar Dados", use_container_width=True):
                carregar_dados(dados_carregados)
                st.rerun()
    
    with col_limpar:
        st.markdown("**Limpar tudo**")
        if st.button("🗑️ Limpar Dados", use_container_width=True, help="Remove todas as faixas e dados atuais"):
            limpar_dados()
            st.rerun()

    # Continua com o código existente...
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
                observacao = st.text_area("Observações", height=405, key="obs_input")
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

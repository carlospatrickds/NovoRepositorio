import streamlit as st
import math

st.set_page_config(
    page_title="Calculadora de Estantes - Engenharia",
    page_icon="🏗️",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .result-box {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🏗️ Calculadora de Estantes - Análise de Engenharia</h1>', unsafe_allow_html=True)

# Propriedades dos materiais (valores reais de engenharia)
PROPRIEDADES_MADEIRA = {
    "Madeira (Pinho)": {
        "densidade": 500,  # kg/m³
        "modulo_elasticidade": 10e9,  # Pa
        "tensao_admissivel": 8e6,  # Pa
        "capacidade_base": 12  # kg para vão padrão
    },
    "Madeira (MDF 15mm)": {
        "densidade": 700,
        "modulo_elasticidade": 3e9,
        "tensao_admissivel": 5e6,
        "capacidade_base": 18
    },
    "Madeira (MDF 18mm)": {
        "densidade": 700,
        "modulo_elasticidade": 3e9,
        "tensao_admissivel": 6e6,
        "capacidade_base": 25
    },
    "Madeira (Compensado)": {
        "densidade": 600,
        "modulo_elasticidade": 8e9,
        "tensao_admissivel": 7e6,
        "capacidade_base": 20
    },
    "Aço": {
        "densidade": 7850,
        "modulo_elasticidade": 200e9,
        "tensao_admissivel": 150e6,
        "capacidade_base": 50
    }
}

# Capacidade dos parafusos (com fator segurança 4:1)
CAPACIDADE_PARAFUSO = {
    "Bucha plástica 6mm": 15,  # kg por parafuso
    "Bucha plástica 8mm": 25,  # kg por parafuso
    "Bucha química": 40,       # kg por parafuso
    "Parafuso em concreto": 35 # kg por parafuso
}

# Criando as abas
tab1, tab2, tab3 = st.tabs([
    "📊 Estante de Cremalheira", 
    "🔨 Prateleira com Mão Francesa", 
    "📋 Análise de Engenharia"
])

with tab1:
    st.markdown('<h2 class="section-header">📊 Calculadora - Estante de Cremalheira</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Configuração da Estrutura")
        num_trilhos = st.number_input("Número de trilhos", min_value=2, max_value=6, value=2, step=1)
        num_parafusos_por_trilho = st.number_input("Parafusos por trilho", min_value=2, max_value=6, value=3, step=1)
        altura_instalacao = st.number_input("Altura de instalação (cm do chão)", min_value=0.0, max_value=100.0, value=30.0, step=5.0)
        
        st.subheader("Dimensões da Estante")
        largura_estante = st.number_input("Largura da estante (cm)", min_value=30.0, max_value=300.0, value=80.0, step=5.0)
        altura_trilho = st.number_input("Altura do trilho (cm)", min_value=50.0, max_value=300.0, value=100.0, step=5.0)
        
        # Tamanhos comerciais de suportes
        tamanho_suporte = st.selectbox("Tamanho do suporte (cm)", [20, 25, 30, 40, 50, 60])
        profundidade_estante = st.number_input("Profundidade da prateleira (cm)", 
                                             min_value=15.0, 
                                             max_value=float(tamanho_suporte), 
                                             value=float(min(40, tamanho_suporte)), 
                                             step=2.5)
        
        num_prateleiras = st.number_input("Número de prateleiras", min_value=1, max_value=10, value=4, step=1)
        
        st.subheader("Materiais e Fixação")
        material_prateleira = st.selectbox("Material da prateleira", list(PROPRIEDADES_MADEIRA.keys()))
        tipo_fixacao = st.selectbox("Tipo de fixação", list(CAPACIDADE_PARAFUSO.keys()))
    
    with col2:
        st.subheader("Cálculos de Carga")
        peso_por_prateleira = st.number_input("Peso estimado por prateleira (kg)", min_value=1.0, max_value=100.0, value=15.0, step=1.0)
        
        # CÁLCULOS DE ENGENHARIA
        # 1. Capacidade da fixação
        capacidade_fixacao_total = num_trilhos * num_parafusos_por_trilho * CAPACIDADE_PARAFUSO[tipo_fixacao]
        
        # 2. Capacidade por prateleira considerando distribuição
        fator_distribuicao = 1.2  # 20% de margem para distribuição não uniforme
        capacidade_por_prateleira_fixacao = capacidade_fixacao_total / (num_prateleiras * fator_distribuicao)
        
        # 3. Cálculo de flexão da madeira
        def calcular_capacidade_flexao(largura_cm, profundidade_cm, material, espessura=0.018):
            """
            Calcula a capacidade da prateleira baseada na flexão máxima admissível
            Fórmula simplificada: σ = (P * L) / (4 * Z) onde Z = (b * h²)/6
            """
            L = largura_cm / 100  # metros
            b = profundidade_cm / 100  # metros
            h = espessura  # metros (espessura da madeira)
            
            Z = (b * h**2) / 6  # Módulo de seção
            tensao_admissivel = PROPRIEDADES_MADEIRA[material]["tensao_admissivel"]
            
            # Para carga distribuída: P_max = (4 * σ * Z) / L
            P_max = (4 * tensao_admissivel * Z) / L  # Newtons
            P_max_kg = P_max / 9.81  # Converter para kg
            
            return max(0, P_max_kg * 0.7)  # Aplicar fator de segurança
        
        capacidade_flexao = calcular_capacidade_flexao(largura_estante, profundidade_estante, material_prateleira)
        
        # 4. Cálculo de capacidade do suporte (alavanca)
        def capacidade_suporte(tamanho_suporte_cm):
            """Capacidade reduzida devido ao efeito de alavanca"""
            capacidades = {
                20: 25,  # Menor alavanca
                25: 22,
                30: 18,
                40: 15,
                50: 12,
                60: 10   # Maior alavanca, menor capacidade
            }
            return capacidades.get(tamanho_suporte_cm, 15)
        
        capacidade_suporte_kg = capacidade_suporte(tamanho_suporte)
        
        # 5. Carga total
        carga_total = peso_por_prateleira * num_prateleiras
        
        # VERIFICAÇÕES DE VIABILIDADE
        viabilidade_fixacao = peso_por_prateleira <= capacidade_por_prateleira_fixacao
        viabilidade_flexao = peso_por_prateleira <= capacidade_flexao
        viabilidade_suporte = peso_por_prateleira <= capacidade_suporte_kg
        viabilidade_total = carga_total <= capacidade_fixacao_total
        
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader("📈 Resultados de Engenharia")
        
        st.write("**Capacidades Calculadas:**")
        st.write(f"• Fixação total: {capacidade_fixacao_total:.0f} kg")
        st.write(f"• Por prateleira (fixação): {capacidade_por_prateleira_fixacao:.1f} kg")
        st.write(f"• Flexão da madeira: {capacidade_flexao:.1f} kg")
        st.write(f"• Capacidade do suporte: {capacidade_suporte_kg:.0f} kg")
        st.write(f"• Carga total estimada: {carga_total:.0f} kg")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # RESULTADO FINAL
        if all([viabilidade_fixacao, viabilidade_flexao, viabilidade_suporte, viabilidade_total]):
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.success("✅ PROJETO VIÁVEL - Estrutura segura")
            st.write("Todas as verificações de engenharia foram atendidas:")
            st.write("✓ Fixação na parede adequada")
            st.write("✓ Prateleira resiste à flexão")
            st.write("✓ Suportes adequados para o peso")
            st.write("✓ Carga total dentro da capacidade")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            st.error("❌ PROJETO NÃO VIÁVEL - Ajustes necessários")
            if not viabilidade_fixacao:
                st.write(f"• Fixação insuficiente: necessita {capacidade_por_prateleira_fixacao:.1f} kg por prateleira")
            if not viabilidade_flexao:
                st.write(f"• Flexão excessiva: máximo {capacidade_flexao:.1f} kg")
            if not viabilidade_suporte:
                st.write(f"• Suporte inadequado: máximo {capacidade_suporte_kg} kg")
            if not viabilidade_total:
                st.write(f"• Carga total excessiva: máximo {capacidade_fixacao_total} kg")
            st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown('<h2 class="section-header">🔨 Calculadora - Prateleira com Mão Francesa</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Configuração da Prateleira")
        largura_prateleira = st.number_input("Largura da prateleira (cm)", min_value=20.0, max_value=200.0, value=80.0, step=5.0, key="largura_francesa")
        profundidade_prateleira = st.number_input("Profundidade da prateleira (cm)", min_value=15.0, max_value=60.0, value=25.0, step=2.5, key="profundidade_francesa")
        
        st.subheader("Mão Francesa")
        num_maos_francesas = st.number_input("Número de mãos francesas", min_value=2, max_value=6, value=2, step=1)
        comprimento_mao_francesa = st.number_input("Comprimento mão francesa (cm)", min_value=10, max_value=30, value=20, step=2)
        
        # Verificação de proporção
        margem_maxima = comprimento_mao_francesa + 10  # 10cm de margem
        if profundidade_prateleira > margem_maxima:
            st.warning(f"⚠️ Profundidade muito grande para mão francesa de {comprimento_mao_francesa}cm")
        
        st.subheader("Materiais e Fixação")
        material_prateleira_fr = st.selectbox("Material da prateleira", list(PROPRIEDADES_MADEIRA.keys()), key="material_fr")
        tipo_fixacao_fr = st.selectbox("Tipo de fixação", list(CAPACIDADE_PARAFUSO.keys()), key="fixacao_fr")
        espessura_madeira = st.number_input("Espessura da madeira (mm)", min_value=10, max_value=30, value=18, step=2, key="espessura_fr")
    
    with col2:
        st.subheader("Cálculos de Carga")
        peso_estimado = st.number_input("Peso estimado na prateleira (kg)", min_value=1.0, max_value=50.0, value=10.0, step=1.0, key="peso_francesa")
        
        # CÁLCULOS PARA MÃO FRANCESA
        # 1. Capacidade da fixação
        parafusos_por_mao = 2  # Cada mão francesa geralmente tem 2 parafusos
        capacidade_fixacao_fr = num_maos_francesas * parafusos_por_mao * CAPACIDADE_PARAFUSO[tipo_fixacao_fr]
        
        # 2. Capacidade da mão francesa (alavanca)
        def capacidade_mao_francesa(comprimento_cm, profundidade_prateleira_cm):
            """Capacidade reduzida pelo efeito de alavanca"""
            fator_alavanca = 1 - (profundidade_prateleira_cm - comprimento_cm) / 50
            capacidade_base = 15  # kg por mão francesa
            return max(5, capacidade_base * fator_alavanca)
        
        capacidade_mao = capacidade_mao_francesa(comprimento_mao_francesa, profundidade_prateleira)
        capacidade_total_maos = capacidade_mao * num_maos_francesas
        
        # 3. Flexão da madeira
        capacidade_flexao_fr = calcular_capacidade_flexao(
            largura_prateleira, 
            profundidade_prateleira, 
            material_prateleira_fr, 
            espessura_madeira/1000
        )
        
        # VERIFICAÇÕES
        viabilidade_fixacao_fr = peso_estimado <= capacidade_fixacao_fr
        viabilidade_maos = peso_estimado <= capacidade_total_maos
        viabilidade_flexao_fr = peso_estimado <= capacidade_flexao_fr
        
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader("📈 Resultados de Engenharia")
        
        st.write("**Capacidades Calculadas:**")
        st.write(f"• Fixação total: {capacidade_fixacao_fr:.0f} kg")
        st.write(f"• Mãos francesas: {capacidade_total_maos:.1f} kg")
        st.write(f"• Flexão da madeira: {capacidade_flexao_fr:.1f} kg")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # RESULTADO FINAL
        if all([viabilidade_fixacao_fr, viabilidade_maos, viabilidade_flexao_fr]):
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.success("✅ PROJETO VIÁVEL - Prateleira segura")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            st.error("❌ PROJETO NÃO VIÁVEL")
            if not viabilidade_fixacao_fr:
                st.write(f"• Fixação insuficiente")
            if not viabilidade_maos:
                st.write(f"• Mãos francesas inadequadas")
            if not viabilidade_flexao_fr:
                st.write(f"• Flexão excessiva da madeira")
            st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown('<h2 class="section-header">📋 Análise de Engenharia Detalhada</h2>', unsafe_allow_html=True)
    
    st.subheader("🧮 Fórmulas e Princípios Utilizados")
    
    with st.expander("🔧 Cálculo de Flexão de Vigas"):
        st.markdown("""
        **Fórmula da Flexão:**
        ```
        σ = (M × y) / I
        Onde:
        σ = Tensão na viga
        M = Momento fletor = (P × L) / 4  (para carga central)
        y = Distância do eixo neutro = h/2
        I = Momento de inércia = (b × h³) / 12
        ```
        
        **Para carga distribuída:**
        ```
        P_max = (4 × σ_admissível × Z) / L
        Z = Módulo de seção = (b × h²) / 6
        ```
        """)
    
    with st.expander("📐 Cálculo de Capacidade de Fixação"):
        st.markdown("""
        **Capacidade Total da Fixação:**
        ```
        Capacidade_total = Nº_trilhos × Nº_parafusos_por_trilho × Capacidade_parafuso
        ```
        
        **Capacidade por Prateleira:**
        ```
        Capacidade_por_prateleira = Capacidade_total / (Nº_prateleiras × 1.2)
        ```
        *Fator 1.2 para distribuição não uniforme*
        """)
    
    with st.expander("⚖️ Efeito de Alavanca nos Suportes"):
        st.markdown("""
        **Quanto maior o suporte, menor a capacidade:**
        - Suporte de 20cm: 25kg
        - Suporte de 60cm: 10kg
        
        **Princípio físico:** Momento = Força × Distância
        Quanto maior a distância, maior o momento na fixação.
        """)
    
    st.subheader("🎯 Recomendações de Segurança")
    st.markdown("""
    1. **Sempre use nível** durante a instalação
    2. **Teste a fixação** com carga gradual
    3. **Verifique o tipo de parede** - evite drywall para cargas pesadas
    4. **Distribua o peso** uniformemente nas prateleiras
    5. **Faça manutenção periódica** da estrutura
    6. **Considere margem de segurança** de 20-30% além do cálculo
    """)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <i>⚠️ ESTA CALCULADORA UTILIZA FÓRMULAS DE ENGENHARIA REAIS. 
    PARA PROJETOS CRÍTICOS, CONSULTE UM ENGENHEIRO CIVIL.</i>
</div>
""", unsafe_allow_html=True)

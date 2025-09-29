import streamlit as st
import math

st.set_page_config(
    page_title="Calculadora de Estantes",
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
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🏗️ Calculadora de Estantes e Prateleiras</h1>', unsafe_allow_html=True)

# Criando as abas
tab1, tab2, tab3 = st.tabs([
    "📊 Estante de Cremalheira", 
    "🔨 Prateleira com Mão Francesa", 
    "📋 Resumo e Explicações"
])

with tab1:
    st.markdown('<h2 class="section-header">📊 Calculadora - Estante de Cremalheira</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Dimensões da Estante")
        largura_estante = st.number_input("Largura da estante (cm)", min_value=30.0, max_value=300.0, value=120.0, step=5.0)
        altura_estante = st.number_input("Altura da estante (cm)", min_value=50.0, max_value=300.0, value=200.0, step=5.0)
        profundidade_estante = st.number_input("Profundidade da estante (cm)", min_value=20.0, max_value=100.0, value=40.0, step=2.5)
        num_prateleiras = st.number_input("Número de prateleiras", min_value=2, max_value=10, value=4, step=1)
        
        st.subheader("Materiais")
        material_prateleira = st.selectbox("Material da prateleira", ["Madeira (Pinho)", "Madeira (MDF 15mm)", "Madeira (MDF 18mm)", "Madeira (Compensado)", "Aço"])
        tipo_cremalheira = st.selectbox("Tipo de cremalheira", ["Aço leve (até 15kg)", "Aço médio (até 25kg)", "Aço pesado (até 50kg)", "Alumínio (até 20kg)"])
    
    with col2:
        st.subheader("Cálculos de Carga")
        peso_por_prateleira = st.number_input("Peso estimado por prateleira (kg)", min_value=1.0, max_value=100.0, value=15.0, step=1.0)
        
        # Cálculos
        area_prateleira = (largura_estante * profundidade_estante) / 10000  # m²
        carga_total = peso_por_prateleira * num_prateleiras
        
        # Capacidades baseadas no material
        capacidades = {
            "Madeira (Pinho)": 12,
            "Madeira (MDF 15mm)": 18,
            "Madeira (MDF 18mm)": 25,
            "Madeira (Compensado)": 20,
            "Aço": 50
        }
        
        capacidades_cremalheira = {
            "Aço leve (até 15kg)": 15,
            "Aço médio (até 25kg)": 25,
            "Aço pesado (até 50kg)": 50,
            "Alumínio (até 20kg)": 20
        }
        
        capacidade_material = capacidades[material_prateleira]
        capacidade_cremalheira = capacidades_cremalheira[tipo_cremalheira]
        
        # Verificações de viabilidade
        viabilidade_material = peso_por_prateleira <= capacidade_material
        viabilidade_cremalheira = peso_por_prateleira <= capacidade_cremalheira
        viabilidade_total = carga_total <= (capacidade_cremalheira * num_prateleiras)
        
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader("📈 Resultados")
        st.write(f"**Área por prateleira:** {area_prateleira:.2f} m²")
        st.write(f"**Carga total estimada:** {carga_total:.0f} kg")
        st.write(f"**Capacidade do material:** {capacidade_material} kg/prateleira")
        st.write(f"**Capacidade da cremalheira:** {capacidade_cremalheira} kg/prateleira")
        
        if viabilidade_material and viabilidade_cremalheira and viabilidade_total:
            st.success("✅ Projeto VIÁVEL")
            st.write("Todos os componentes suportam as cargas estimadas.")
        else:
            st.error("❌ Projeto NÃO VIÁVEL")
            if not viabilidade_material:
                st.write(f"- Material da prateleira insuficiente (suporta {capacidade_material}kg)")
            if not viabilidade_cremalheira:
                st.write(f"- Cremalheira insuficiente (suporta {capacidade_cremalheira}kg)")
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<h2 class="section-header">🔨 Calculadora - Prateleira com Mão Francesa</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Dimensões da Prateleira")
        largura_prateleira = st.number_input("Largura da prateleira (cm)", min_value=20.0, max_value=200.0, value=80.0, step=5.0, key="largura_francesa")
        profundidade_prateleira = st.number_input("Profundidade da prateleira (cm)", min_value=15.0, max_value=60.0, value=25.0, step=2.5, key="profundidade_francesa")
        espessura_madeira = st.number_input("Espessura da madeira (mm)", min_value=10, max_value=30, value=18, step=2)
        
        st.subheader("Fixação")
        num_maos_francesas = st.number_input("Número de mãos francesas", min_value=2, max_value=6, value=2, step=1)
        tipo_fixacao = st.selectbox("Tipo de fixação na parede", ["Bucha plástica 6mm", "Bucha plástica 8mm", "Bucha química", "Parafuso em concreto"])
    
    with col2:
        st.subheader("Cálculos de Carga")
        peso_estimado = st.number_input("Peso estimado na prateleira (kg)", min_value=1.0, max_value=50.0, value=10.0, step=1.0, key="peso_francesa")
        
        # Cálculos para mão francesa
        area_prateleira_francesa = (largura_prateleira * profundidade_prateleira) / 10000
        
        # Capacidade baseada na espessura e número de mãos francesas
        capacidade_por_mao = {
            10: 3, 12: 5, 15: 8, 18: 12, 20: 15, 25: 20, 30: 25
        }
        
        capacidade_fixacao = {
            "Bucha plástica 6mm": 8,
            "Bucha plástica 8mm": 15,
            "Bucha química": 30,
            "Parafuso em concreto": 25
        }
        
        capacidade_mao = capacidade_por_mao.get(espessura_madeira, 8)
        capacidade_total_maos = capacidade_mao * num_maos_francesas
        capacidade_fix = capacidade_fixacao[tipo_fixacao]
        
        # Verificações
        viabilidade_maos = peso_estimado <= capacidade_total_maos
        viabilidade_fixacao = peso_estimado <= capacidade_fixacao[tipo_fixacao]
        
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader("📈 Resultados")
        st.write(f"**Área da prateleira:** {area_prateleira_francesa:.2f} m²")
        st.write(f"**Capacidade por mão francesa:** {capacidade_mao} kg")
        st.write(f"**Capacidade total das mãos francesas:** {capacidade_total_maos} kg")
        st.write(f"**Capacidade da fixação:** {capacidade_fix} kg")
        
        if viabilidade_maos and viabilidade_fixacao:
            st.success("✅ Projeto VIÁVEL")
            st.write("A prateleira e a fixação suportam o peso estimado.")
        else:
            st.error("❌ Projeto NÃO VIÁVEL")
            if not viabilidade_maos:
                st.write(f"- Mãos francesas insuficientes (suportam {capacidade_total_maos}kg)")
            if not viabilidade_fixacao:
                st.write(f"- Fixação insuficiente (suporta {capacidade_fix}kg)")
        st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<h2 class="section-header">📋 Resumo e Explicações Técnicas</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Resumo dos Cálculos")
        
        # Coletar dados das outras abas
        st.write("**Estante de Cremalheira:**")
        st.write(f"- Dimensões: {largura_estante}cm x {altura_estante}cm x {profundidade_estante}cm")
        st.write(f"- Prateleiras: {num_prateleiras}")
        st.write(f"- Carga por prateleira: {peso_por_prateleira}kg")
        st.write(f"- Carga total: {carga_total}kg")
        
        st.write("**Prateleira com Mão Francesa:**")
        st.write(f"- Dimensões: {largura_prateleira}cm x {profundidade_prateleira}cm")
        st.write(f"- Mãos francesas: {num_maos_francesas}")
        st.write(f"- Carga estimada: {peso_estimado}kg")
    
    with col2:
        st.subheader("🎯 Recomendações")
        
        st.markdown("""
        **Para Estante de Cremalheira:**
        - Use pelo menos 2 suportes por prateleira
        - Distribua o peso uniformemente
        - Verifique a qualidade da parede
        - Considere margem de segurança de 20%
        
        **Para Mão Francesa:**
        - Instale em paredes estruturais
        - Use nível durante a instalação
        - Prefira madeira maciça para maior resistência
        - Teste a fixação antes do uso
        """)
    
    st.markdown("---")
    
    st.subheader("📚 Explicações Técnicas")
    
    with st.expander("🔍 Como funcionam os cálculos?"):
        st.markdown("""
        **Estante de Cremalheira:**
        - A capacidade depende do material da prateleira e do tipo de cremalheira
        - Cálculo considera carga distribuída uniformemente
        - Fator de segurança incorporado nos valores
        
        **Mão Francesa:**
        - Capacidade baseada na espessura da madeira
        - Considera o número de suportes
        - Inclui capacidade da fixação na parede
        """)
    
    with st.expander("⚠️ Fatores de Segurança"):
        st.markdown("""
        **Importante considerar:**
        - Tipo de parede (alvenaria, drywall, concreto)
        - Distribuição do peso
        - Qualidade dos materiais
        - Variações na instalação
        
        **Recomenda-se sempre:**
        - Adicionar 20-30% de margem de segurança
        - Testar com carga gradual
        - Verificar periodicamente a fixação
        """)
    
    with st.expander("🛠️ Dicas de Instalação"):
        st.markdown("""
        **Ferramentas necessárias:**
        - Nível
        - Furadeira
        - Parafusos adequados
        - Fita métrica
        
        **Passos básicos:**
        1. Marque os pontos com nível
        2. Faça furos pilotos
        3. Instale as buchas
        4. Fixe os suportes
        5. Teste a estabilidade
        """)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <i>⚠️ Esta calculadora fornece estimativas. Sempre consulte um profissional para projetos críticos.</i>
</div>
""", unsafe_allow_html=True)

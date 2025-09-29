# app_prateleira_completa.py
import streamlit as st

st.set_page_config(page_title="Calculadora de Prateleira Avançada", page_icon="📚")
st.title("Calculadora de Prateleira Avançada")

# --- Dados predefinidos ---
materiais = {
    "pinus": 55e6,
    "mdf": 30e6,
    "madeira_berço": 60e6
}

parafuso_bucha = {
    "Alvenaria/Concreto": {"parafuso": "6 mm", "bucha": "8 mm", "carga_kg": 25},
    "Drywall": {"parafuso": "6 mm", "bucha": "nylon", "carga_kg": 8}
}

# --- Funções ---
def carga_prateleira(largura_cm, profundidade_cm, espessura_cm, material, prof_suporte, num_suportes, num_parafusos, tipo_parede):
    # Viga simples com múltiplos apoios
    L = largura_cm / 100
    b = profundidade_cm / 100
    h = espessura_cm / 100
    sigma = materiais.get(material, 55e6)
    I = (b * h**3) / 12
    q_prat_newton = (sigma * I * 6) / L**2
    q_prat_kg = q_prat_newton / 9.81

    # Fator de suporte
    fator_suporte = 1 + 0.01 * prof_suporte * num_suportes
    q_suporte = q_prat_kg * fator_suporte

    # Fixação
    carga_parafuso = parafuso_bucha[tipo_parede]["carga_kg"]
    q_fixacao = num_parafusos * carga_parafuso

    q_max_segura = min(q_prat_kg, q_suporte, q_fixacao)
    return round(q_max_segura, 1), parafuso_bucha[tipo_parede]["parafuso"], parafuso_bucha[tipo_parede]["bucha"]

def carga_mao_francesa(largura_cm, profundidade_cm, espessura_cm, material, tamanho_mao, tipo_parede, num_parafusos=2):
    # Limitar comprimento máximo da prateleira por tamanho da mão francesa
    limites = {20:40, 25:50, 30:60, 40:80, 50:100, 60:120} # cm
    if largura_cm > limites[tamanho_mao]:
        return None, None, None, f"A prateleira é longa demais para mãos francesas de {tamanho_mao} cm (máx {limites[tamanho_mao]} cm)."

    # Simplificação: carga segura proporcional ao tamanho da mão francesa
    fator_tamanho = tamanho_mao / 20  # referência 20 cm
    carga_base, parafuso, bucha = carga_prateleira(largura_cm, profundidade_cm, espessura_cm, material, tamanho_mao, 2, num_parafusos, tipo_parede)
    carga_max_segura = carga_base * fator_tamanho
    return round(carga_max_segura,1), parafuso, bucha, None

# --- Abas ---
abas = st.tabs(["Cremalheira", "Mão Francesa", "Explicação"])

# --- Aba Cremalheira ---
with abas[0]:
    st.subheader("Prateleira com Cremalheira")
    largura = st.number_input("Comprimento da prateleira (cm)", value=80.0, key="cremalheira_l")
    profundidade = st.number_input("Profundidade da prateleira (cm)", value=20.0, key="cremalheira_p")
    espessura = st.number_input("Espessura da prateleira (cm)", value=2.0, key="cremalheira_e")
    material = st.selectbox("Material", list(materiais.keys()), key="cremalheira_m")
    prof_suporte = st.number_input("Profundidade do suporte (cm)", value=20.0, key="cremalheira_ps")
    num_suportes = st.number_input("Número de suportes", value=2, key="cremalheira_ns")
    num_trilhos = st.number_input("Número de trilhos", value=2, min_value=1, key="cremalheira_nt")
    comp_trilho = st.number_input("Comprimento de cada trilho (cm)", value=100.0, key="cremalheira_ct")
    num_parafusos = st.number_input("Número total de parafusos", value=6, key="cremalheira_np")
    tipo_parede = st.selectbox("Tipo de parede", list(parafuso_bucha.keys()), key="cremalheira_tp")

    if st.button("Calcular Cremalheira", key="btn_cremalheira"):
        carga_max, parafuso, bucha = carga_prateleira(largura, profundidade, espessura, material, prof_suporte, num_suportes, num_parafusos, tipo_parede)
        st.success(f"Carga máxima segura: {carga_max} kg")
        st.info(f"Recomenda-se parafusos: {parafuso}, buchas: {bucha}")

# --- Aba Mão Francesa ---
with abas[1]:
    st.subheader("Prateleira com Mão Francesa")
    largura = st.number_input("Comprimento da prateleira (cm)", value=60.0, key="mf_l")
    profundidade = st.number_input("Profundidade da prateleira (cm)", value=20.0, key="mf_p")
    espessura = st.number_input("Espessura da prateleira (cm)", value=2.0, key="mf_e")
    material = st.selectbox("Material", list(materiais.keys()), key="mf_m")
    tamanho_mao = st.selectbox("Tamanho da mão francesa (cm)", [20,25,30,40,50,60], key="mf_tm")
    tipo_parede = st.selectbox("Tipo de parede", list(parafuso_bucha.keys()), key="mf_tp")

    if st.button("Calcular Mão Francesa", key="btn_mf"):
        carga_max, parafuso, bucha, erro = carga_mao_francesa(largura, profundidade, espessura, material, tamanho_mao, tipo_parede)
        if erro:
            st.error(erro)
        else:
            st.success(f"Carga máxima segura: {carga_max} kg")
            st.info(f"Recomenda-se parafusos: {parafuso}, buchas: {bucha}")

# --- Aba Explicação ---
with abas[2]:
    st.subheader("Como são feitos os cálculos")
    st.markdown("""
    **1. Cremalheira**
    - A prateleira é considerada uma viga apoiada nos suportes.
    - Carga máxima é limitada por:
      - Resistência da madeira (tensão à flexão)
      - Capacidade dos suportes
      - Capacidade dos parafusos e buchas
    - Se houver múltiplos trilhos, os apoios adicionais reduzem a flecha e aumentam a carga segura.

    **2. Mão Francesa**
    - Cada mão francesa cria um ponto de apoio.
    - O tamanho da mão francesa limita o comprimento máximo da prateleira para evitar curvatura excessiva.
    - A carga máxima também depende da madeira e da fixação na parede.
    
    **3. Fixação**
    - O tipo de parede e número de parafusos determina a carga máxima segura por fixação.
    - Recomenda-se sempre utilizar a menor das três restrições como limite seguro.
    """)

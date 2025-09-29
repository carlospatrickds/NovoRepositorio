# app_prateleira_avancada.py
import streamlit as st

st.set_page_config(page_title="Calculadora de Prateleira Avançada", page_icon="📚")
st.title("Calculadora Avançada de Capacidade de Prateleira com Cremalheira")

# --- Entrada de dados ---
largura = st.number_input("Comprimento da prateleira (cm)", value=80.0)
profundidade = st.number_input("Profundidade da prateleira (cm)", value=20.0)
espessura = st.number_input("Espessura da prateleira (cm)", value=2.0)
material = st.selectbox("Material da prateleira", ["pinus", "mdf", "madeira_berço"])
prof_suporte = st.number_input("Profundidade do suporte (cm)", value=20.0)
num_suportes = st.number_input("Número de suportes", value=2)
dist_trilhos = st.number_input("Distância entre trilhos (cm)", value=60.0)
num_parafusos = st.number_input("Número total de parafusos (todos os trilhos)", value=6)
tipo_parede = st.selectbox("Tipo de parede", ["Alvenaria/Concreto", "Drywall"])

# --- Materiais ---
materiais = {
    "pinus": 55e6,
    "mdf": 30e6,
    "madeira_berço": 60e6
}

parafuso_bucha = {
    "Alvenaria/Concreto": {"parafuso": "6 mm", "bucha": "8 mm", "carga_kg": 25},
    "Drywall": {"parafuso": "6 mm", "bucha": "nylon", "carga_kg": 8}
}

# --- Função de cálculo ---
def calcular_carga_max(largura_cm, profundidade_cm, espessura_cm, material, prof_suporte, num_suportes, num_parafusos, tipo_parede):
    # Prateleira
    L = largura_cm / 100
    b = profundidade_cm / 100
    h = espessura_cm / 100
    sigma = materiais.get(material, 55e6)
    I = (b * h**3) / 12
    q_prat_newton = (sigma * I * 6) / L**2
    q_prat_kg = q_prat_newton / 9.81

    # Suporte (fator aproximado)
    fator_suporte = 1 + 0.01 * prof_suporte * num_suportes  # cada cm adiciona ~1%
    q_suporte = q_prat_kg * fator_suporte

    # Fixação
    carga_parafuso = parafuso_bucha[tipo_parede]["carga_kg"]
    q_fixacao = num_parafusos * carga_parafuso

    # Carga máxima segura final
    q_max_segura = min(q_prat_kg, q_suporte, q_fixacao)

    return round(q_max_segura,1), parafuso_bucha[tipo_parede]["parafuso"], parafuso_bucha[tipo_parede]["bucha"]

# --- Botão de cálculo ---
if st.button("Calcular"):
    carga_max, parafuso, bucha = calcular_carga_max(
        largura, profundidade, espessura, material, prof_suporte, num_suportes, num_parafusos, tipo_parede
    )
    st.success(f"Carga máxima segura da prateleira: {carga_max} kg")
    st.info(f"Recomenda-se parafusos: {parafuso} e buchas: {bucha}")

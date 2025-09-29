# app_prateleira.py
import streamlit as st
import math

st.set_page_config(page_title="Calculadora de Prateleira", page_icon="📚")
st.title("Calculadora de Capacidade de Prateleira com Cremalheira")

# --- Entrada de dados ---
largura = st.number_input("Comprimento da prateleira (cm)", value=80.0)
profundidade = st.number_input("Profundidade da prateleira (cm)", value=20.0)
espessura = st.number_input("Espessura da prateleira (cm)", value=2.0)
material = st.selectbox("Material da prateleira", ["pinus", "mdf", "madeira_berço"])

# Dicionário de resistências à flexão (Pa)
materiais = {
    "pinus": 55e6,
    "mdf": 30e6,
    "madeira_berço": 60e6
}

def calcular_carga_maxima(largura_cm, profundidade_cm, espessura_cm, material):
    # Conversão para metros
    L = largura_cm / 100
    b = profundidade_cm / 100
    h = espessura_cm / 100

    sigma = materiais.get(material, 55e6)

    # Momento de inércia de uma viga retangular
    I = (b * h**3) / 12

    # Carga distribuída máxima aproximada (N)
    q_newton = (sigma * I * 6) / L**2

    # Converter para kgf
    q_kg = q_newton / 9.81
    return round(q_kg, 1)

# --- Botão de cálculo ---
if st.button("Calcular"):
    carga_max = calcular_carga_maxima(largura, profundidade, espessura, material)
    st.success(f"Carga máxima aproximada da prateleira: {carga_max} kg")
    st.info("Estimativa conservadora considerando apenas a madeira e dimensões da prateleira.")

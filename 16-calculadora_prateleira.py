# calculadora_prateleira.py

"""
Calculadora de capacidade de prateleira com cremalheira
Base: madeira pinus maciça, suportes, distância entre trilhos
"""

import math

# Dicionário de madeiras predefinidas (resistência à flexão em MPa)
materiais = {
    "pinus": 55,
    "mdf": 30,
    "madeira_berço": 60
}

def calcular_massa_maxima(largura_cm, profundidade_cm, espessura_cm, material="pinus"):
    """
    Calcula carga máxima aproximada (kg) de uma prateleira
    largura_cm: comprimento da prateleira em cm
    profundidade_cm: profundidade da prateleira em cm
    espessura_cm: espessura da madeira em cm
    material: chave do dicionário materiais
    """
    # Convertendo para metros
    L = largura_cm / 100
    b = profundidade_cm / 100
    h = espessura_cm / 100

    # Propriedades do material
    sigma = materiais.get(material, 55) * 1e6  # Pa

    # Momento de inércia (viga retangular)
    I = (b * h**3) / 12

    # Carga distribuída máxima aproximada (kgf)
    # Fórmula simplificada para viga bi-apoiada: q = (sigma * I * 6) / L^2
    q_newton = (sigma * I * 6) / L**2
    q_kg = q_newton / 9.81  # converter N para kgf

    return round(q_kg, 1)

if __name__ == "__main__":
    print("Calculadora de carga máxima de prateleira")
    largura = float(input("Comprimento da prateleira (cm): "))
    profundidade = float(input("Profundidade (cm): "))
    espessura = float(input("Espessura (cm): "))
    material = input("Material (pinus/mdf/madeira_berço): ").lower()

    carga_max = calcular_massa_maxima(largura, profundidade, espessura, material)
    print(f"Carga máxima aproximada: {carga_max} kg")

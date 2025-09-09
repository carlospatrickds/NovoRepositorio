import streamlit as st



# --- VERIFICAÇÃO DE SENHA ---
SENHA_CORRETA = "23"
senha_digitada = st.text_input("Digite a senha para acessar a lista de links:", type="password")

if senha_digitada != SENHA_CORRETA:
    if senha_digitada:  # Só mostra erro se o usuário já digitou algo
        st.error("Senha incorreta! Acesso negado.")
    st.stop()  # Para aqui se a senha estiver errada ou vazia


# Configuração da página
st.set_page_config(
    page_title="Repositório de Links - Meus Projetos",
    page_icon="🎅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado (mesmo código anterior)
st.markdown("""
<style>
    .link-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .link-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    .title {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        text-align: center;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 30px;
        font-size: 2.5em;
        font-weight: bold;
    }
    .link-button {
        background-color: #ffffff;
        color: #667eea;
        border: none;
        padding: 12px 25px;
        border-radius: 8px;
        font-weight: bold;
        text-decoration: none;
        display: inline-block;
        margin-top: 15px;
        transition: background-color 0.3s ease;
    }
    .link-button:hover {
        background-color: #f1f2f6;
        text-decoration: none;
        color: #667eea;
    }
    .section-header {
        color: #2c3e50;
        border-left: 5px solid #ff6b6b;
        padding-left: 15px;
        margin: 30px 0 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# LISTA DE PROJETOS - AQUI VOCÊ ATUALIZA!
projetos = [
    {
        "categoria": "Trabalhista",
        "nome": "📅 Cálculo de Multa Diária Corrigida por Faixa",
        "url": "https://07-calcmulta-logo.streamlit.app/",
        "descricao": "Adicione faixas de multa com valores diferentes. O total por mês será corrigido por índice informado manualmente ou automaticamente pela SELIC."
    },
    {
        "categoria": "Trabalhista", 
        "nome": "⭐ Sistema de Cálculo de Adicionais Trabalhistas - AnaClara",
        "url": "https://03-anaclara2.streamlit.app/",
        "descricao": "Sistema com verificação da periculosidade para cálculo de adicionais trabalhistas."
    },
    {
        "categoria": "Previdenciária",
        "nome": "📊 Cálculo de Acumulação de Benefícios Previdenciários",
        "url": "https://01-beneficioredutor.streamlit.app/",
        "descricao": "Calculadora conforme as regras de redução na acumulação de benefícios (EC 103/2019)."
    },
    {
        "categoria": "Técnica",
        "nome": "🔓 Desbloqueador de Projetos VBA Excel",
        "url": "https://06-quebrasenhavba.streamlit.app/",
        "descricao": "Ferramenta para desbloquear e recuperar projetos VBA no Excel."
    },
    {
        "categoria": "Trabalhista",
        "nome": "⭐ Sistema de Cálculo de Adicionais Trabalhistas - AnaClara",
        "url": "https://02-anaclara.streamlit.app/",
        "descricao": "Versão original do sistema de cálculo de adicionais trabalhistas."
    },
    # ⬇️ ADICIONE NOVOS PROJETOS AQUI! ⬇️
    {
        "categoria": "Técnica",
        "nome": "🚀 Novo Projeto Incrível",
        "url": "https://novo-projeto.streamlit.app/",
        "descricao": "Descrição do seu novo projeto fantástico!"
    }
]

# Cabeçalho
st.markdown('<div class="title">🚀 Meu Repositório de Projetos</div>', unsafe_allow_html=True)

# Separar projetos por categoria
projetos_trabalhistas = [p for p in projetos if p["categoria"] == "Trabalhista"]
projetos_tecnicos = [p for p in projetos if p["categoria"] == "Técnica"]
projetos_previdenciarios = [p for p in projetos if p["categoria"] == "Previdenciária"]

# Layout em colunas
col1, col2 = st.columns(2)

with col1:
    st.markdown('<h3 class="section-header">📊 Ferramentas Trabalhistas e Previdenciárias</h3>', unsafe_allow_html=True)
    
    for projeto in projetos_trabalhistas + projetos_previdenciarios:
        st.markdown(f"""
        <div class="link-card">
            <h3>{projeto['nome']}</h3>
            <p>{projeto['descricao']}</p>
            <a href="{projeto['url']}" target="_blank">
                <button class="link-button">🔗 Acessar Ferramenta</button>
            </a>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown('<h3 class="section-header">⚙️ Ferramentas Técnicas e Produtividade</h3>', unsafe_allow_html=True)
    
    for projeto in projetos_tecnicos:
        st.markdown(f"""
        <div class="link-card">
            <h3>{projeto['nome']}</h3>
            <p>{projeto['descricao']}</p>
            <a href="{projeto['url']}" target="_blank">
                <button class="link-button">🔗 Acessar Ferramenta</button>
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    # Espaço para futuros projetos
    if len(projetos_tecnicos) < 3:
        st.markdown(f"""
        <div class="link-card">
            <h3>🚧 Novo Projeto em Desenvolvimento</h3>
            <p>Em breve uma nova ferramenta estará disponível aqui!</p>
            <button class="link-button" style="background-color: #95a5a6; color: white;" disabled>
                ⏳ Em Breve
            </button>
        </div>
        """, unsafe_allow_html=True)

# ... (restante do código igual) ...

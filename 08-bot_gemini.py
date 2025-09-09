import streamlit as st
import time
from datetime import datetime
import google.generativeai as genai

# Configuração da página
st.set_page_config(
    page_title="Chatbot Gemini - Assistente Inteligente",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS para melhorar a aparência
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #f0f2f6;
    }
    .assistant-message {
        background-color: #e6f7ff;
    }
    .timestamp {
        font-size: 0.8rem;
        color: #666;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# Título e descrição
st.title("💬 Assistente Virtual com Gemini")
st.markdown("""
Bem-vindo ao seu assistente inteligente! Converse comigo sobre diversos temas usando a tecnologia do Google Gemini.
""")

# Inicialização do estado da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "model" not in st.session_state:
    st.session_state.model = "gemini-1.5-flash"
if "chat_initialized" not in st.session_state:
    st.session_state.chat_initialized = False

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações do Assistente")
    
    # Input para a API Key
    api_key = st.text_input(
        "🔑 Chave da API Gemini", 
        type="password",
        value=st.session_state.api_key,
        help="Obtenha sua chave em: https://aistudio.google.com/"
    )
    
    # Seleção do modelo
    model_option = st.selectbox(
        "🧠 Modelo Gemini",
        ["gemini-1.5-flash", "gemini-1.0-pro"],
        index=0,
        help="Gemini 1.5 Flash é mais rápido, Gemini 1.0 Pro pode ser mais criativo"
    )
    
    # Configurações de geração
    st.subheader("🎛️ Configurações de Resposta")
    temperature = st.slider(
        "🌡️ Temperatura", 
        0.0, 1.0, 0.7, 
        help="Controla a criatividade (0 = mais factual, 1 = mais criativo)"
    )
    max_tokens = st.slider(
        "📏 Comprimento máximo", 
        100, 2048, 1024,
        help="Número máximo de tokens na resposta"
    )
    
    # Botões de ação
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Limpar Conversa", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_initialized = False
            st.rerun()
    
    with col2:
        if st.button("🔄 Reiniciar Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_initialized = False
            st.rerun()
    
    st.divider()
    
    # Informações
    st.markdown("### 📊 Informações")
    st.info("""
    **Recursos disponíveis:**
    - 💡 Respostas inteligentes
    - 📚 Conhecimento geral
    - 🔄 Contexto de conversa
    - ⚡ Respostas rápidas
    """)
    
    st.markdown("### 🔗 Links Úteis")
    st.page_link("https://aistudio.google.com/", label="Google AI Studio", icon="🔑")
    st.page_link("https://makersuite.google.com/", label="MakerSuite", icon="⚙️")

# Atualizar configurações na sessão
st.session_state.api_key = api_key
st.session_state.model = model_option

# Verificar se a API key foi fornecida
if not st.session_state.api_key:
    st.warning("""
    🔑 **API Key necessária**
    
    Para começar a conversar, você precisa:
    1. Acessar [Google AI Studio](https://aistudio.google.com/)
    2. Criar uma API Key
    3. Colar a chave na barra lateral
    """)
    st.stop()

# Configurar a API do Gemini
try:
    genai.configure(api_key=st.session_state.api_key)
    
    # Configuração do modelo
    generation_config = {
        "temperature": temperature,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": max_tokens,
    }
    
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    
    # Inicializar o modelo
    model = genai.GenerativeModel(
        model_name=st.session_state.model,
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    
    # Inicializar o chat se não estiver inicializado
    if not st.session_state.chat_initialized:
        chat = model.start_chat(history=[])
        st.session_state.chat = chat
        st.session_state.chat_initialized = True
        
except Exception as e:
    st.error(f"❌ Erro na configuração: {str(e)}")
    st.stop()

# Exibir mensagens do chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "timestamp" in message:
            st.caption(f"🕒 {message['timestamp']}")

# Mensagem de boas-vindas se não houver mensagens
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("""
        👋 Olá! Sou seu assistente virtual com tecnologia Gemini. 
        
        Posso ajudar você com:
        - 📚 Responder perguntas gerais
        - 💡 Dar ideias e sugestões
        - 🔍 Explicar conceitos complexos
        - 📝 Auxiliar com escrita e edição
        
        **Como posso ajudar você hoje?**
        """)
        st.caption(f"🕒 {datetime.now().strftime('%H:%M:%S')}")

# Input do usuário
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    # Adicionar mensagem do usuário ao histórico
    timestamp = datetime.now().strftime("%H:%M:%S")
    user_message = {"role": "user", "content": prompt, "timestamp": timestamp}
    st.session_state.messages.append(user_message)
    
    # Exibir mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(f"🕒 {timestamp}")
    
    # Gerar resposta do assistente
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("▌")
        
        try:
            # Simular digitação para melhor UX
            full_response = ""
            
            # Enviar mensagem para o Gemini
            response = st.session_state.chat.send_message(prompt, stream=True)
            
            # Processar resposta stream
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.02)  # Efeito de digitação
            
            # Remover cursor piscando
            message_placeholder.markdown(full_response)
            
            # Adicionar resposta ao histórico
            timestamp = datetime.now().strftime("%H:%M:%S")
            assistant_message = {"role": "assistant", "content": full_response, "timestamp": timestamp}
            st.session_state.messages.append(assistant_message)
            
            # Exibir timestamp
            st.caption(f"🕒 {timestamp}")
            
        except Exception as e:
            error_message = f"⚠️ Desculpe, ocorreu um erro: {str(e)}"
            message_placeholder.markdown(error_message)
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.messages.append({"role": "assistant", "content": error_message, "timestamp": timestamp})
            st.caption(f"🕒 {timestamp}")

# Rodapé
st.divider()
st.caption("""
🤖 Desenvolvido com Google Gemini API + Streamlit | 
📦 Versão 1.0 | 
🔒 Suas conversas não são armazenadas permanentemente
""")

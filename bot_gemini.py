import streamlit as st
import google.generativeai as genai
from datetime import datetime
import time
import os

# Configuração da página
st.set_page_config(
    page_title="Chatbot Gemini",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Título e descrição
st.title("💬 Chatbot com Google Gemini")
st.markdown("Converse com um chatbot alimentado pela inteligência artificial do Google Gemini.")

# Inicialização do estado da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "model" not in st.session_state:
    st.session_state.model = "gemini-1.5-flash"

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Input para a API Key
    api_key = st.text_input(
        "Chave da API Gemini", 
        type="password",
        value=st.session_state.api_key,
        help="Obtenha sua chave em: https://aistudio.google.com/"
    )
    
    # Seleção do modelo
    model_option = st.selectbox(
        "Modelo Gemini",
        ["gemini-1.5-flash", "gemini-1.0-pro"],
        index=0 if st.session_state.model == "gemini-1.5-flash" else 1
    )
    
    # Configurações de geração
    temperature = st.slider("Temperatura", 0.0, 1.0, 0.7, help="Controla a criatividade das respostas. Valores mais altos = mais criativo.")
    max_tokens = st.slider("Tokens máximos", 1, 2048, 1024, help="Limite máximo de tokens por resposta.")
    
    # Botão para limpar histórico
    if st.button("🧹 Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.markdown("### 📊 Sobre")
    st.markdown("""
    Este chatbot utiliza a API do Google Gemini para gerar respostas.
    - Desenvolvido com Streamlit
    - Modelos: Gemini 1.5 Flash ou Gemini 1.0 Pro
    - Código aberto no GitHub
    """)

# Atualizar configurações na sessão
st.session_state.api_key = api_key
st.session_state.model = model_option

# Verificar se a API key foi fornecida
if not st.session_state.api_key:
    st.info("👈 Por favor, adicione sua API Key do Gemini na barra lateral para começar a conversar.")
    st.stop()

# Configurar a API do Gemini
try:
    genai.configure(api_key=st.session_state.api_key)
    
    # Configuração do modelo
    generation_config = {
        "temperature": temperature,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": max_tokens,
    }
    
    # Inicializar o modelo
    model = genai.GenerativeModel(
        model_name=st.session_state.model,
        generation_config=generation_config
    )
except Exception as e:
    st.error(f"Erro ao configurar a API: {str(e)}")
    st.stop()

# Exibir mensagens do chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "timestamp" in message:
            st.caption(f"{message['timestamp']}")

# Input do usuário
if prompt := st.chat_input("Digite sua mensagem..."):
    # Adicionar mensagem do usuário ao histórico
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({"role": "user", "content": prompt, "timestamp": timestamp})
    
    # Exibir mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(timestamp)
    
    # Gerar resposta do assistente
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("▌")
        
        try:
            # Construir histórico de conversa para o modelo
            history_for_model = []
            for msg in st.session_state.messages[:-1]:  # Excluir a última mensagem (a atual)
                role = "user" if msg["role"] == "user" else "model"
                history_for_model.append({role: msg["content"]})
            
            # Gerar resposta
            response = model.generate_content(
                contents=history_for_model + [{"user": prompt}]
            )
            
            # Exibir resposta
            full_response = response.text
            message_placeholder.markdown(full_response)
            
            # Adicionar resposta ao histórico
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.messages.append({"role": "assistant", "content": full_response, "timestamp": timestamp})
            
            # Exibir timestamp
            st.caption(timestamp)
            
        except Exception as e:
            error_message = f"Desculpe, ocorreu um erro: {str(e)}"
            message_placeholder.markdown(error_message)
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.messages.append({"role": "assistant", "content": error_message, "timestamp": timestamp})
            st.caption(timestamp)

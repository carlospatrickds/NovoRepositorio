import google.generativeai as genai

# 1. Configure a sua chave de API
genai.configure(api_key="SUA_CHAVE_API_AQUI")

# 2. Escolha um modelo (Gemini 1.5 Flash é rápido e bom para chat)
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. Inicie uma sessão de chat
chat = model.start_chat(history=[])

print("Chatbot Gemini inicializado! Digite 'sair' para encerrar.\n")

# 4. Loop principal de conversação
while True:
    user_input = input("Você: ")
    
    if user_input.lower() == 'sair':
        print("Até mais!")
        break

    # 5. Envia a mensagem do usuário e obtém a resposta
    response = chat.send_message(user_input)
    
    # 6. Imprime a resposta do modelo
    print("Bot: " + response.text + "\n")

# (Opcional) 7. Veja o histórico completo da conversa
print("\n--- Histórico da Conversa ---")
for message in chat.history:
    # Verifica se a mensagem é do usuário ou do modelo e imprime
    print(f"{'Você' if message.role == 'user' else 'Bot'}: {message.parts[0].text}")

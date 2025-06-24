import os
from core.google_api_search import buscar_place_id, obter_reviews_place_id
from LLM1.llm_interface import consulta_llm
from LLM1.prompt_builder import construir_prompt_google

def chat_google_places(api_key):
    print("💬 Pergunta sobre qualquer hotel ou local turístico (ex: 'Como é a piscina do Pestana Dom João II?')")
    print("Escreve 'sair' para terminar.\n")

    historico_mensagens = [
        {"role": "system", "content": (
            "És um assistente especializado em análise de reviews de locais turísticos. "
            "Responde sempre em português de Portugal, de forma objetiva e educada. "
            "Baseia as respostas nas avaliações fornecidas. "
            "Mantém o contexto das perguntas anteriores nesta conversa."
        )}
    ]

    while True:
        pergunta = input("❓ Pergunta: ")
        if pergunta.strip().lower() == 'sair':
            print("👋 Até à próxima!")
            break

        place_id = buscar_place_id(pergunta, api_key)
        if not place_id:
            print("❌ Local não encontrado no Google.")
            continue

        detalhes = obter_reviews_place_id(place_id, api_key)
        if not detalhes or "reviews" not in detalhes:
            print("⚠️ Não foram encontradas avaliações para o local mencionado.")
            continue

        mensagens = construir_prompt_google(pergunta, detalhes)

        # Junta o histórico anterior com as novas mensagens geradas
        historico_mensagens += mensagens


        try:
            resposta = consulta_llm("resumidor", historico_mensagens)
            historico_mensagens.append({"role": "assistant", "content": resposta})
            print(f"\n💬 {resposta}\n")
        except Exception as e:
            print("❌ Erro ao contactar o modelo:", e)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY não definida no .env")
    else:
        chat_google_places(api_key)

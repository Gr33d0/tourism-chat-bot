import requests

def consulta_llm(mensagens):
    response = requests.post("http://localhost:11434/api/chat", json={
        "model": "hotel-review",
        "messages": mensagens,
        "stream": False
    })
    data = response.json()
    if "message" not in data:
        raise ValueError("Erro na resposta do modelo:", data)
    return data["message"]["content"]

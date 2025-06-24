# llm_interface.py
import requests

import requests
import json

def gerar_resposta_mistral_streaming(prompt):
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            "model": "guia-algarve",
            "prompt": prompt,
            "stream": True
        },
        stream=True
    )

    for linha in response.iter_lines():
        if linha:
            try:
                linha_json = json.loads(linha.decode("utf-8"))
                if "response" in linha_json:
                    yield linha_json["response"]
            except Exception:
                continue


def formatar_resposta_para_llm(cidade, lugares):
    texto = f"Olá! Se estiveres por {cidade}, aqui vão algumas sugestões incríveis:\n\n"
    for lugar in lugares:
        texto += f"- {lugar['nome']} (classificação: {lugar['rating']})\n  {lugar['endereco']}\n"
    texto += "\nEspero que aproveites ao máximo a tua visita! 😊"
    return texto

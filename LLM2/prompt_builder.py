def construir_prompt_google(pergunta, lugar_info):
    if not lugar_info or "reviews" not in lugar_info:
        return "Não foram encontradas avaliações para o local mencionado."

    reviews_texto = "\n\n".join([
        f"Autor: {r.get('author_name')}\nNota: {r.get('rating')}\nComentário: {r.get('text')}"
        for r in lugar_info["reviews"]
    ])

    exemplos = """
        [Exemplo 1]
        Pergunta: Como é o pequeno-almoço?
        Resposta: "Várias avaliações mencionam que o pequeno-almoço é excelente, com boa variedade e qualidade."

        [Exemplo 2]
        Pergunta: A piscina é boa?
        Resposta: "Os hóspedes elogiaram bastante a piscina, especialmente pela limpeza e pela vista."

        [Exemplo 3]
        Pergunta: E o atendimento?
        Resposta: "A maioria dos comentários destaca um atendimento simpático e prestável, embora alguns referiram demoras no check-in."
        """

    return [
        {"role": "system", "content": (
            "És um assistente especializado em análise de reviews de locais turísticos. "
            "Responde sempre em português de Portugal, com base apenas nas avaliações fornecidas. "
            "Segue o estilo dos exemplos abaixo:\n" + exemplos
        )},
        {"role": "user", "content": f"""Estas são as avaliações de clientes: {reviews_texto}
         Pergunta: {pergunta}
        """}
    ]

# core_logic.py
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import json
from core.google_api import get_places
from core.dados_lugares import get_lugares_por_cidade

load_dotenv()

TERMOS_CATEGORIA = {
    "praia": ["praia", "praias", "banho", "mar", "areia", "litoral", "praia de", "praia das", "praia do", "praia da", "praia dos"],
    "trilhos": ["caminhada", "caminhadas", "trilho", "trilhos", "trilhas", "trilha", "caminho", "caminhos", "percursos pedestres", "percursos pedestre"],
    "cultura": ["museu", "história", "igreja", "cultura"],
    "desporto": ["padel", "ténis", "golfe", "desporto", "atividades desportivas", "atividades ao ar livre", "atividades de aventura"],
    "restaurante_sushi": ["sushi", "japonês", "cozinha japonesa", "restaurante japonês", "sushi bar", "restaurante sushi", "restaurantes sushi", "sushi take away", "sushi delivery"],
    "restaurante": ["gastronomia", "restaurante", "comida", "culinária", "gastronomia local"],
    "viagem_aquatica": ["grutas", "passeio de barco", "viagem aquática", "passeio de barco pelas grutas", "visita às grutas", "grutas de benagil", "golfinhos", "observação de golfinhos", "andar de barco", "viagem aquatica"],
    "monumento": ["igreja", "capela", "santuário", "templo", "religião", "culto", "lugar de culto", "lugar religioso", "sítio religioso", "monumento religioso", "religiao", "monumento"],
    "hotel": ["hotel", "pousada", "alojamento", "hospedagem", "resort", "acomodação", "estadia", "hospedaria", "hostel", "hoteis"]
}

def guardar_feedback_csv(troca, tipo_feedback, cidade=None):
    df_novo = pd.DataFrame([{ 
        "pergunta": troca["pergunta"],
        "resposta": troca["resposta"],
        "feedback": tipo_feedback,
        "cidade": cidade if cidade else "Desconhecida",
        "timestamp": datetime.now().isoformat()
    }])
    caminho = "feedback.csv"
    if os.path.exists(caminho):
        try:
            df_existente = pd.read_csv(caminho)
            df_final = pd.concat([df_existente, df_novo], ignore_index=True)
        except pd.errors.EmptyDataError:
            df_final = df_novo
    else:
        df_final = df_novo
    df_final.to_csv(caminho, index=False)

def carregar_feedback_ponderado():
    caminho = "feedback.csv"
    if os.path.exists(caminho):
        try:
            df = pd.read_csv(caminho)
            df_grouped = df.groupby("resposta")["feedback"].value_counts().unstack(fill_value=0)
            df_grouped["score"] = df_grouped.get("positivo", 0) - df_grouped.get("negativo", 0)
            return df_grouped.sort_values("score", ascending=False)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def detectar_categoria(pergunta):
    pergunta = pergunta.lower()
    for categoria, termos in TERMOS_CATEGORIA.items():
        if any(t in pergunta for t in termos):
            return categoria
    return None

def processar_lugares(cidade, categoria):
    lugares = []
    fonte = "base_dados"

    if cidade:
        todos = get_lugares_por_cidade(cidade, max_resultados=50)
        if categoria:
            filtrados = [l for l in todos if l["categoria"].lower() == categoria]
            if filtrados:
                lugares = filtrados[:10]
            else:
                lugares_api = get_places(cidade)
                lugares = [{
                    "nome": l.get("nome"),
                    "descricao": l.get("endereco", "Local turístico"),
                    "avaliacao": l.get("rating", "Sem avaliação"),
                    "categoria": "desconhecida"
                } for l in lugares_api]
                fonte = "api"
        else:
            if todos:
                lugares = todos[:10]
            else:
                lugares_api = get_places(cidade)
                lugares = [{
                    "nome": l.get("nome"),
                    "descricao": l.get("endereco", "Local turístico"),
                    "avaliacao": l.get("rating", "Sem avaliação"),
                    "categoria": "desconhecida"
                } for l in lugares_api]
                fonte = "api"

    return lugares, fonte

def construir_prompt(mensagem_utilizador, historico, cidade=None, lugares=None):
    sistema = (
        "[INSTRUÇÕES PARA O MODELO - NÃO INCLUIR NA RESPOSTA]\n"
        "És um guia turístico português especializado exclusivamente no Algarve.\n"
        "A tua função é recomendar locais turísticos, culturais, gastronómicos e atividades usando apenas a informação fornecida.\n"
        "Não inventes locais. Se não tiveres dados, diz que não tens informação.\n"
        "Fala de forma entusiástica e informal, como se estivesses a dar dicas a um amigo.\n"
        "Organiza a resposta em parágrafos e não uses listas diretas.\n"
        "Fala exclusivamente da cidade mencionada na pergunta.\n"
        "[FIM DAS INSTRUÇÕES]\n"
    )

    entrada = f"Utilizador: {mensagem_utilizador}\nGuia:"

    if cidade and lugares:
        entrada += "\n\nInformações úteis (não mostrar diretamente):\n"
        for l in lugares[:5]:
            entrada += f"- {l['nome']}, {l.get('descricao', 'localização desconhecida')}, avaliação: {l.get('avaliacao', 'Sem avaliação')}\n"

    if cidade and lugares and not all(l.get("categoria") == "desconhecida" for l in lugares):
        melhores = carregar_feedback_ponderado()
        if not melhores.empty:
            boas = melhores[melhores["score"] > 0]
            for r in boas.index:
                if cidade.lower() in r.lower():
                    entrada += f"\n\nExemplo de resposta anterior bem avaliada (não mostrar diretamente):\n{r}\n"
                    break

    return sistema + "\n" + entrada

import streamlit as st
import os
from dotenv import load_dotenv
import json
from core.cidade_detector import extrair_cidade
from LLM1.prompt_builder import detectar_categoria, processar_lugares, construir_prompt, guardar_feedback_csv
from core.google_api_reviews import buscar_place_id, obter_reviews_place_id
from LLM1.llm_interface import gerar_resposta_mistral_streaming
from LLM2.llm_interface import consulta_llm as consulta_reviews
from LLM2.prompt_builder import construir_prompt_google

# Carrega variáveis do .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

st.set_page_config(page_title="Guia Turístico com IA", layout="centered")
st.title("💬 Assistente Turístico Inteligente")

# Inicializar estados
for key in ["chat_history", "feedback", "votados", "resposta_final", "tipo_llm"]:
    if key not in st.session_state:
        if key == "chat_history":
            st.session_state[key] = []
        elif key == "votados":
            st.session_state[key] = set()
        else:
            st.session_state[key] = []

# Sidebar
st.sidebar.title("Guia Turístico do Algarve")
st.sidebar.markdown("Conversa com um guia turístico inteligente sobre qualquer região do Algarve 🇵🇹.")

if st.sidebar.button("🧹 Limpar Conversa"):
    st.session_state.chat_history = []
    st.session_state.feedback = []
    st.session_state.votados = set()

if st.sidebar.checkbox("📊 Ver feedback registado"):
    if st.session_state.feedback:
        for f in st.session_state.feedback:
            st.sidebar.write(f"- **{f['feedback'].capitalize()}**: {f['pergunta']}")
    else:
        st.sidebar.write("Ainda não foi registado feedback.")

# Mostrar histórico de conversa
for idx, troca in enumerate(st.session_state.chat_history):
    st.chat_message("user").write(troca["pergunta"])
    st.chat_message("assistant").write(troca["resposta"])
    if idx not in st.session_state.votados:
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"👍 Útil {idx}", key=f"like_{idx}"):
                cidade = extrair_cidade(troca["pergunta"])
                guardar_feedback_csv(troca, "positivo", cidade)
                st.session_state.feedback.append({"pergunta": troca["pergunta"], "resposta": troca["resposta"], "feedback": "positivo"})
                st.session_state.votados.add(idx)
                st.success("Obrigado pelo feedback positivo! 😊")
        with col2:
            if st.button(f"👎 Pouco útil {idx}", key=f"dislike_{idx}"):
                cidade = extrair_cidade(troca["pergunta"])
                guardar_feedback_csv(troca, "negativo", cidade)
                st.session_state.feedback.append({"pergunta": troca["pergunta"], "resposta": troca["resposta"], "feedback": "negativo"})
                st.session_state.votados.add(idx)
                st.info("Obrigado! Vamos tentar melhorar. 🙏")
    else:
        st.caption("✅ Já deste feedback para esta resposta.")

# Entrada do utilizador
pergunta = st.chat_input("Faz uma pergunta sobre o Algarve ou um hotel...")
if pergunta:
    st.chat_message("user").write(pergunta)

    tipo_llm = "LLM2" if any(p in pergunta.lower() for p in [
        "piscina", "quarto", "pequeno-almoço", "pequeno almoco", "cafe da manha",
        "atendimento", "limpeza", "barulho", "funcionários", "internet", "wifi", "cama", "staff"]
    ) else "LLM1"

    resposta_final = ""
    feedbacks = [h for h in st.session_state.chat_history if h["llm"] == tipo_llm and h.get("liked") is not None]
    n_pos = sum(1 for f in feedbacks if f["liked"])
    n_neg = sum(1 for f in feedbacks if not f["liked"])

    if tipo_llm == "LLM1":
        cidade = extrair_cidade(pergunta)
        categoria = detectar_categoria(pergunta)
        lugares, origem = processar_lugares(cidade, categoria)

        if cidade:
            if lugares:
                if origem == "base_dados":
                    st.info(f"✅ Dados encontrados na base de dados local para '{categoria or 'genérico'}' em {cidade}.")
                else:
                    st.warning(f"⚠️ Nenhum local encontrado na base de dados. Dados obtidos da API externa para {cidade}.")
            else:
                st.warning(f"⚠️ Nenhum local encontrado em {cidade}.")


        prompt = construir_prompt(pergunta, st.session_state.chat_history, cidade, lugares)

        if n_neg > n_pos:
            prompt = "Sê mais claro, direto e útil. Evita ambiguidades.\n\n" + prompt

        resposta_area = st.chat_message("assistant")
        resposta_placeholder = resposta_area.empty()
        for parte in gerar_resposta_mistral_streaming(prompt):
            resposta_final += parte
            resposta_placeholder.markdown(resposta_final + "▌")
        resposta_placeholder.markdown(resposta_final)

    elif tipo_llm == "LLM2":
        place_id = buscar_place_id(pergunta, api_key)
        if not place_id:
            resposta_final = "❌ Local não encontrado no Google."
        else:
            detalhes = obter_reviews_place_id(place_id, api_key)
            if not detalhes or "reviews" not in detalhes:
                resposta_final = "⚠️ Nenhuma avaliação encontrada."
            else:
                mensagens = construir_prompt_google(pergunta, detalhes)
                if n_neg > n_pos:
                    mensagens.insert(0, {
                        "role": "system",
                        "content": "Tenta ser mais direto, claro e responder com base em reviews reais."
                    })
                try:
                    resposta_final = consulta_reviews(mensagens)
                except Exception as e:
                    resposta_final = f"❌ Erro ao contactar o modelo: {e}"
        st.chat_message("assistant").write(resposta_final)

    st.session_state.chat_history.append({"pergunta": pergunta, "resposta": resposta_final, "llm": tipo_llm})
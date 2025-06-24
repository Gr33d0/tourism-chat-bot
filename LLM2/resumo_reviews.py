import os
import streamlit as st
from core.google_api_reviews import buscar_place_id, obter_reviews_place_id
from LLM2.llm_interface import consulta_llm
from LLM2.prompt_builder import construir_prompt_google

def chat_google_places_streamlit(api_key):
    st.subheader("🔍 Análise de reviews de hotel")

    pergunta = st.text_input("Faz uma pergunta sobre um hotel (ex: 'Como é o pequeno-almoço no Pestana Dom João II?')")

    if pergunta:
        with st.spinner("🔎 A procurar informações..."):
            place_id = buscar_place_id(pergunta, api_key)
            if not place_id:
                st.error("❌ Local não encontrado no Google.")
                return

            detalhes = obter_reviews_place_id(place_id, api_key)
            if not detalhes or "reviews" not in detalhes:
                st.warning("⚠️ Não foram encontradas avaliações para este local.")
                return

            mensagens = construir_prompt_google(pergunta, detalhes)

            try:
                resposta = consulta_llm(mensagens)
                st.success("💬 Resposta baseada nas reviews:")
                st.markdown(resposta)
            except Exception as e:
                st.error(f"❌ Erro ao contactar o modelo: {e}")

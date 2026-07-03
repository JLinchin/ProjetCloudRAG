import os
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv("conf.env")
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="RAG Barack Obama", page_icon="", layout="centered")

st.title("Projet final Cloud")
st.write("Chargez un fichier texte puis posez lui des questions !")

uploaded_file = st.file_uploader("Chargement du fichier texte", type="txt")

if uploaded_file:
    if st.button("1. Envoyer le document (upload)"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        r = requests.post(f"{API_URL}/upload", files=files)
        if r.ok:
            st.session_state["filename"] = uploaded_file.name
            st.success(f"Document envoyé : {r.json()}")
        else:
            st.error(r.text)

if "filename" in st.session_state:
    if st.button("2. Indexer le document"):
        r = requests.post(f"{API_URL}/index", params={"filename": st.session_state["filename"]})
        if r.ok:
            st.success(f"Indexation terminée : {r.json()}")
        else:
            st.error(r.text)

question = st.text_input("3. Poser une question", placeholder="Que dit le texte sur l'éducation ?")

if question and st.button("Obtenir une réponse"):
    r = requests.post(f"{API_URL}/ask", params={"question": question})
    if r.ok:
        result = r.json()
        st.subheader("Réponse")
        st.write(result["answer"])

        st.subheader("Sources")
        for source in result["sources"]:
            st.markdown(
                f"**{source['filename']}** — passage n°{source['passage_num']} "
                f"(score : {source['score']:.3f})"
            )
            st.caption(source["extrait"])
    else:
        st.error(r.text)


import os
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv("conf.env")
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

st.set_page_config(page_title="RAG Barack Obama", page_icon="", layout="centered")

st.title("Projet final Cloud")
st.write("Chargez un fichier texte puis posez lui des questions !")

uploaded_file = st.file_uploader("Chargement du fichier texte", type="txt")

if uploaded_file:
    question = st.text_input("Saisir une question", placeholder="Quelle est la réponse à la vie, l'univers et tout et tout ?")
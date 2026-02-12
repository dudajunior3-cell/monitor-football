import streamlit as st
import pandas as pd

st.set_page_config(page_title="PAINEL LIVE", layout="wide")
st.title("⚽ Football Studio - Monitor de Sinais")

# Aqui o app apenas lê um arquivo que o seu PC vai atualizar
try:
    df = pd.read_csv("historico.csv")
    st.write(df.tail(10)) # Mostra os últimos 10 resultados
except:
    st.info("Aguardando dados do robô local...")

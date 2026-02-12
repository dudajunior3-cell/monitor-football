import streamlit as st
import pandas as pd

st.set_page_config(page_title="PAINEL LIVE", layout="wide")
st.title("⚽ Football Studio - Monitor PRO")

# O painel lê um arquivo que você atualizará do seu PC
try:
    # Vamos usar uma URL direta do GitHub para os dados
    URL_DADOS = "https://raw.githubusercontent.com"
    df = pd.read_csv(URL_DADOS)
    
    # Exibe o sinal baseado no último resultado
    ultimo = df['resultado'].iloc[-1]
    cor = "#2563eb" if ultimo == 'H' else "#dc2626" if ultimo == 'A' else "#16a34a"
    st.markdown(f"<div style='background:{cor}; padding:30px; border-radius:15px; text-align:center; color:white;'><h1>ENTRADA: {ultimo}</h1></div>", unsafe_allow_html=True)
    
    st.subheader("🕒 Histórico Recente")
    st.table(df.tail(10))
except:
    st.info("Aguardando dados do robô local...")


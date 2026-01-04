import streamlit as st
import psycopg2

def get_connection():
    """Estabelece conexão com o Supabase usando os secrets"""
    try:
        # Pega a URL do arquivo .streamlit/secrets.toml
        url = st.secrets["connections"]["postgresql"]["url"]
        conn = psycopg2.connect(url)
        return conn
    except Exception as e:
        st.error(f"Erro crítico de conexão: {e}")
        return None
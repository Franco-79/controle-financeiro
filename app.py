import streamlit as st
from datetime import date
import time

# Importando nossos novos módulos
from services.crud import criar_tabelas, adicionar_movimento, ler_movimentos
from views.dashboard import show_dashboard
from views.assinaturas import show_assinaturas

st.set_page_config(page_title="Minhas Finanças Pro", layout="wide")

# --- LOGIN ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🔐 Login Supabase")
        if st.text_input("Usuário") == "admin" and st.text_input("Senha", type="password") == "1234":
            if st.button("Entrar"):
                st.session_state['logado'] = True
                st.rerun()
    st.stop()

# --- SISTEMA ---
criar_tabelas() # Garante que as tabelas existem no Supabase

LISTA_CATEGORIAS = ["Alimentação", "Moradia", "Transporte", "Assinaturas/Streaming", "Lazer", "Saúde", "Receita (Salário)", "Outros"]

# --- SIDEBAR GLOBAL ---
st.sidebar.title("Menu")
navegacao = st.sidebar.radio("Ir para:", ["Dashboard", "Assinaturas"])
st.sidebar.markdown("---")

with st.sidebar.expander("➕ Nova Transação"):
    with st.form("add_form"):
        d = st.date_input("Data", date.today())
        c = st.selectbox("Categoria", LISTA_CATEGORIAS)
        desc = st.text_input("Descrição")
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        v = st.number_input("Valor", min_value=0.0, step=0.01)
        f = st.checkbox("Fixo?")
        p = st.checkbox("Pago?", value=True)
        
        if st.form_submit_button("Salvar"):
            val_final = v * -1 if t == "Despesa" else v
            adicionar_movimento(d, c, desc, t, val_final, f, p)
            st.success("Salvo no Supabase!")
            st.rerun()

st.sidebar.button("Sair", on_click=lambda: st.session_state.update(logado=False))

# Carrega dados uma vez
df = ler_movimentos()

# --- ROTEAMENTO DE TELAS ---
if navegacao == "Dashboard":
    show_dashboard(df, LISTA_CATEGORIAS)
elif navegacao == "Assinaturas":
    show_assinaturas(df)
import streamlit as st
from datetime import date
from services.crud import criar_usuario, autenticar_usuario, adicionar_movimento, ler_movimentos
from views.dashboard import show_dashboard
from views.assinaturas import show_assinaturas

st.set_page_config(page_title="Finanças Multi-User", layout="wide")

# --- GERENCIAMENTO DE SESSÃO ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False
if 'usuario_id' not in st.session_state:
    st.session_state['usuario_id'] = None
if 'usuario_nome' not in st.session_state:
    st.session_state['usuario_nome'] = ""

def login_sucesso(id, nome):
    st.session_state['logado'] = True
    st.session_state['usuario_id'] = id
    st.session_state['usuario_nome'] = nome
    st.rerun()

def logout():
    st.session_state['logado'] = False
    st.session_state['usuario_id'] = None
    st.session_state['usuario_nome'] = ""
    st.rerun()

# --- TELA DE LOGIN / REGISTRO ---
if not st.session_state['logado']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("💰 Minhas Finanças")
        tab_login, tab_cadastro = st.tabs(["🔐 Login", "📝 Criar Conta"])
        
        # --- CORREÇÃO AQUI: Usando st.form para evitar o "pisca-pisca" ---
        with tab_login:
            with st.form(key="form_login"): # O form segura a execução
                st.subheader("Acesse sua conta")
                email_login = st.text_input("Email")
                senha_login = st.text_input("Senha", type="password")
                
                # O botão agora faz parte do form
                submit_login = st.form_submit_button("Entrar")
                
                if submit_login:
                    usuario = autenticar_usuario(email_login, senha_login)
                    if usuario:
                        login_sucesso(usuario[0], usuario[1])
                    else:
                        st.error("Email ou senha incorretos.")
        
        with tab_cadastro:
            with st.form(key="form_cadastro"):
                st.subheader("Novo por aqui?")
                nome_cad = st.text_input("Seu Nome")
                email_cad = st.text_input("Seu Email")
                senha_cad = st.text_input("Crie uma Senha", type="password")
                
                submit_cad = st.form_submit_button("Cadastrar")
                
                if submit_cad:
                    if criar_usuario(nome_cad, email_cad, senha_cad):
                        st.success("Conta criada! Faça login na aba ao lado.")
                    else:
                        st.error("Erro ao criar. Email já existe?")
    st.stop()

# ========================================================
# ÁREA LOGADA (SÓ CHEGA AQUI SE TIVER LOGADO)
# ========================================================

user_id = st.session_state['usuario_id']
user_nome = st.session_state['usuario_nome']

# --- SIDEBAR ---
st.sidebar.write(f"Olá, **{user_nome}**! 👋")
st.sidebar.button("Sair", on_click=logout)
st.sidebar.markdown("---")

st.sidebar.title("Menu")
navegacao = st.sidebar.radio("Ir para:", ["Dashboard", "Assinaturas"])
st.sidebar.markdown("---")

LISTA_CATEGORIAS = ["Alimentação", "Moradia", "Transporte", "Assinaturas/Streaming", "Lazer", "Saúde", "Receita (Salário)", "Outros"]

with st.sidebar.expander("➕ Nova Transação"):
    with st.form("add_form"):
        d = st.date_input("Data", date.today())
        c = st.selectbox("Categoria", LISTA_CATEGORIAS)
        desc = st.text_input("Descrição")
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        v = st.number_input("Valor", min_value=0.0, step=0.01)
        f = st.checkbox("Fixo?")
        p = st.checkbox("Pago?", value=True)
        
        # O botão aqui já era submit, por isso funcionava bem
        if st.form_submit_button("Salvar"):
            val_final = v * -1 if t == "Despesa" else v
            adicionar_movimento(user_id, d, c, desc, t, val_final, f, p)
            st.success("Salvo!")
            st.rerun()

# --- CARREGA DADOS DO USUÁRIO ESPECÍFICO ---
df = ler_movimentos(user_id)

if navegacao == "Dashboard":
    show_dashboard(user_id, df, LISTA_CATEGORIAS)
elif navegacao == "Assinaturas":
    show_assinaturas(df)
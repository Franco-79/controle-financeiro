import pandas as pd
import streamlit as st
from services.database import get_connection

# --- AUTENTICAÇÃO ---

def criar_usuario(nome, email, senha):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", (nome, email, senha))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Erro ao criar usuário (Email já existe?): {e}")
            conn.close()
            return False

def autenticar_usuario(email, senha):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        # Busca o usuário pelo email e senha
        cursor.execute("SELECT id, nome FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
        usuario = cursor.fetchone()
        conn.close()
        return usuario # Retorna uma tupla (id, nome) ou None se falhar

# --- DADOS FINANCEIROS (Agora com user_id) ---

def ler_movimentos(user_id):
    conn = get_connection()
    if conn:
        # O filtro WHERE user_id = %s é o segredo do Multi-Tenant!
        query = "SELECT * FROM movimentos WHERE user_id = %s"
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        return df
    return pd.DataFrame()

def adicionar_movimento(user_id, data, categoria, descricao, tipo, valor, fixo, pago):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO movimentos (user_id, data, categoria, descricao, tipo, valor, fixo, pago)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, data, categoria, descricao, tipo, valor, fixo, pago))
        conn.commit()
        conn.close()

def atualizar_movimento(id_mov, user_id, data, categoria, descricao, valor, fixo):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        # Garantimos que o usuário só edita o SEU próprio movimento (AND user_id = ...)
        cursor.execute("""
            UPDATE movimentos 
            SET data=%s, categoria=%s, descricao=%s, valor=%s, fixo=%s
            WHERE id=%s AND user_id=%s
        """, (data, categoria, descricao, valor, fixo, id_mov, user_id))
        conn.commit()
        conn.close()

def mudar_status_pago(id_mov, user_id, novo_status):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE movimentos SET pago=%s WHERE id=%s AND user_id=%s", (novo_status, id_mov, user_id))
        conn.commit()
        conn.close()

def excluir_movimento(id_mov, user_id):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM movimentos WHERE id=%s AND user_id=%s", (id_mov, user_id))
        conn.commit()
        conn.close()

def salvar_meta(user_id, categoria, valor):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        # Agora a meta é única por Categoria E Usuário
        cursor.execute("""
            INSERT INTO metas (user_id, categoria, valor_limite) VALUES (%s, %s, %s)
            ON CONFLICT (categoria, user_id) DO UPDATE SET valor_limite = EXCLUDED.valor_limite
        """, (user_id, categoria, valor))
        conn.commit()
        conn.close()

def ler_metas(user_id):
    conn = get_connection()
    if conn:
        df = pd.read_sql_query("SELECT * FROM metas WHERE user_id = %s", conn, params=(user_id,))
        conn.close()
        return df
    return pd.DataFrame()
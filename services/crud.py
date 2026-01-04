import pandas as pd
from services.database import get_connection

def criar_tabelas():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimentos (
                id SERIAL PRIMARY KEY,
                data DATE,
                categoria TEXT,
                descricao TEXT,
                tipo TEXT,
                valor REAL,
                fixo BOOLEAN,
                pago BOOLEAN
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metas (
                categoria TEXT PRIMARY KEY,
                valor_limite REAL
            );
        """)
        conn.commit()
        conn.close()

def ler_movimentos():
    conn = get_connection()
    if conn:
        query = "SELECT * FROM movimentos"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    return pd.DataFrame()

def adicionar_movimento(data, categoria, descricao, tipo, valor, fixo, pago):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO movimentos (data, categoria, descricao, tipo, valor, fixo, pago)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (data, categoria, descricao, tipo, valor, fixo, pago))
        conn.commit()
        conn.close()

def atualizar_movimento(id_mov, data, categoria, descricao, valor, fixo):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE movimentos 
            SET data=%s, categoria=%s, descricao=%s, valor=%s, fixo=%s
            WHERE id=%s
        """, (data, categoria, descricao, valor, fixo, id_mov))
        conn.commit()
        conn.close()

def mudar_status_pago(id_mov, novo_status):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE movimentos SET pago=%s WHERE id=%s", (novo_status, id_mov))
        conn.commit()
        conn.close()

def excluir_movimento(id_mov):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM movimentos WHERE id=%s", (id_mov,))
        conn.commit()
        conn.close()

def salvar_meta(categoria, valor):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metas (categoria, valor_limite) VALUES (%s, %s)
            ON CONFLICT (categoria) DO UPDATE SET valor_limite = EXCLUDED.valor_limite
        """, (categoria, valor))
        conn.commit()
        conn.close()

def ler_metas():
    conn = get_connection()
    if conn:
        df = pd.read_sql_query("SELECT * FROM metas", conn)
        conn.close()
        return df
    return pd.DataFrame()
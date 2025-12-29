import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import time

# --- Configuração da Página ---
st.set_page_config(page_title="Minhas Finanças", layout="wide")

# --- LOGIN ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

def check_login(usuario, senha):
    if usuario == "admin" and senha == "1234":
        st.session_state['logado'] = True
        st.success("Bem-vindo!")
        time.sleep(0.5)
        st.rerun()
    else:
        st.error("Dados incorretos.")

def logout():
    st.session_state['logado'] = False
    st.rerun()

if not st.session_state['logado']:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🔐 Login")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            check_login(usuario, senha)
    st.stop()

# ========================================================
# SISTEMA PRINCIPAL
# ========================================================

st.sidebar.button("Sair", on_click=logout)
st.sidebar.markdown("---")

st.title("💰 Controle Financeiro Pessoal")

# --- Backend ---
def conectar_db():
    conn = sqlite3.connect("financas.db")
    return conn

def criar_tabelas():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            categoria TEXT,
            descricao TEXT,
            tipo TEXT,
            valor REAL,
            fixo INTEGER,
            pago INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metas (
            categoria TEXT PRIMARY KEY,
            valor_limite REAL
        )
    """)
    conn.commit()
    conn.close()

def adicionar_movimento(data, categoria, descricao, tipo, valor, fixo, pago):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO movimentos (data, categoria, descricao, tipo, valor, fixo, pago) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (data, categoria, descricao, tipo, valor, fixo, pago))
    conn.commit()
    conn.close()

# Função NOVA: Atualizar dados completos (Edição)
def atualizar_movimento_completo(id_mov, nova_data, nova_cat, nova_desc, novo_valor, novo_fixo):
    conn = conectar_db()
    cursor = conn.cursor()
    # Mantemos o status de pagamento (pago) inalterado nesta edição, ou poderíamos editar também
    cursor.execute("""
        UPDATE movimentos 
        SET data = ?, categoria = ?, descricao = ?, valor = ?, fixo = ?
        WHERE id = ?
    """, (nova_data, nova_cat, nova_desc, novo_valor, novo_fixo, id_mov))
    conn.commit()
    conn.close()

def mudar_status_pago(id_movimento, novo_status):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE movimentos SET pago = ? WHERE id = ?", (novo_status, id_movimento))
    conn.commit()
    conn.close()

def excluir_movimento(id_movimento):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movimentos WHERE id = ?", (id_movimento,))
    conn.commit()
    conn.close()

def salvar_meta(categoria, valor):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO metas (categoria, valor_limite) VALUES (?, ?)", (categoria, valor))
    conn.commit()
    conn.close()

def ler_movimentos():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM movimentos", conn)
    conn.close()
    return df

def ler_metas():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM metas", conn)
    conn.close()
    return df

# Inicializa
criar_tabelas()
LISTA_CATEGORIAS = ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Receita (Salário)", "Outros"]

# --- Frontend Lateral ---
with st.sidebar.expander("➕ Nova Transação", expanded=True):
    with st.form("form_transacao"):
        data_input = st.date_input("Data Vencimento", date.today())
        categoria_input = st.selectbox("Categoria", LISTA_CATEGORIAS)
        descricao_input = st.text_input("Detalhe")
        tipo_input = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        valor_input = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        c1, c2 = st.columns(2)
        is_fixo = c1.checkbox("Fixo Mensal? 🔄")
        is_pago = c2.checkbox("Já Pago? ✅", value=True)
        
        if st.form_submit_button("Salvar"):
            if valor_input > 0:
                val = valor_input * -1 if tipo_input == "Despesa" else valor_input
                fix = 1 if is_fixo else 0
                pg = 1 if is_pago else 0
                adicionar_movimento(data_input, categoria_input, descricao_input, tipo_input, val, fix, pg)
                st.success("Salvo!")
                st.rerun()

st.sidebar.markdown("---")

# Ferramentas
df_bruto = ler_movimentos()
if not df_bruto.empty:
    df_bruto['data'] = pd.to_datetime(df_bruto['data'])
    df_bruto['mes_ano'] = df_bruto['data'].dt.strftime('%Y-%m')
    
    with st.sidebar.expander("🛠️ Ferramentas"):
        st.markdown("**🔄 Virar o Mês**")
        lista_meses = sorted(df_bruto['mes_ano'].unique(), reverse=True)
        mes_origem = st.selectbox("Copiar de:", lista_meses)
        if st.button("Clonar Pendências"):
            fixos = df_bruto[(df_bruto['mes_ano'] == mes_origem) & (df_bruto['fixo'] == 1)]
            if not fixos.empty:
                for _, row in fixos.iterrows():
                    nova_data = row['data'] + pd.DateOffset(months=1)
                    adicionar_movimento(nova_data.date(), row['categoria'], row['descricao'], row['tipo'], row['valor'], 1, 0)
                st.success("Próximo mês gerado!")
                st.rerun()
            else:
                st.warning("Nada fixo.")
        st.divider()
        csv = df_bruto.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar Backup", csv, "financas.csv", "text/csv")

    with st.sidebar.expander("🎯 Metas"):
        cat_meta = st.selectbox("Categoria", [c for c in LISTA_CATEGORIAS if "Receita" not in c])
        valor_meta = st.number_input("Limite (R$)", min_value=0.0, step=50.0)
        if st.button("Salvar Meta"):
            salvar_meta(cat_meta, valor_meta)
            st.success("Atualizado!")
            st.rerun()

# --- ÁREA PRINCIPAL ---
if not df_bruto.empty:
    lista_meses = sorted(df_bruto['mes_ano'].unique(), reverse=True)
    col_top1, col_top2 = st.columns([1,3])
    with col_top1:
        mes_selecionado = st.selectbox("📅 Mês:", lista_meses)
    
    df_mes = df_bruto[df_bruto['mes_ano'] == mes_selecionado].copy()
    
    # Cards
    receitas = df_mes[df_mes["valor"] > 0]["valor"].sum()
    despesas = df_mes[df_mes["valor"] < 0]["valor"].sum()
    saldo = receitas + despesas
    falta_pagar = df_mes[(df_mes["valor"] < 0) & (df_mes["pago"] == 0)]["valor"].sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo Previsto", f"R$ {saldo:,.2f}", delta=saldo)
    c4.metric("A Pagar", f"R$ {falta_pagar:,.2f}", delta_color="off")
    
    st.divider()
    
    # Metas (Resumido)
    df_metas = ler_metas()
    if not df_metas.empty:
        gastos_cat = df_mes[df_mes["valor"] < 0].copy()
        gastos_cat["valor"] = gastos_cat["valor"].abs()
        gastos_por_cat = gastos_cat.groupby("categoria")["valor"].sum()
        cols = st.columns(len(df_metas) if len(df_metas) < 4 else 4)
        idx = 0
        for index, row in df_metas.iterrows():
            cat = row['categoria']
            teto = row['valor_limite']
            gasto = gastos_por_cat.get(cat, 0.0)
            perc = min(gasto / teto, 1.0) if teto > 0 else 0
            with cols[idx % 4]:
                st.caption(f"{cat}")
                st.progress(perc)
            idx += 1
    
    st.divider()

    # Extrato e Gestão
    c_graf, c_tab = st.columns([1,2])
    
    with c_graf:
        st.subheader("Gráfico")
        df_desp = df_mes[df_mes["valor"] < 0].copy()
        if not df_desp.empty:
            df_desp["abs"] = df_desp["valor"].abs()
            st.bar_chart(df_desp.groupby("categoria")["abs"].sum())

    with c_tab:
        st.subheader("Gestão de Lançamentos")
        df_show = df_mes.copy()
        df_show['data_str'] = df_show['data'].dt.strftime('%d/%m')
        df_show['status'] = df_show['pago'].apply(lambda x: "✅" if x==1 else "🕒")
        
        st.dataframe(
            df_show[["id", "data_str", "status", "categoria", "descricao", "valor"]], 
            hide_index=True, use_container_width=True, height=200
        )
        
        # --- ÁREA DE AÇÃO UNIFICADA (Abas) ---
        if not df_show.empty:
            opcoes = df_show.apply(lambda x: f"{x['id']}: {x['descricao']} ({x['valor']})", axis=1)
            item_sel = st.selectbox("Selecione o item:", options=opcoes)
            id_sel = int(item_sel.split(":")[0])
            
            # Buscamos os dados atuais do item selecionado para preencher o formulário
            item_atual = df_show[df_show['id'] == id_sel].iloc[0]

            tab1, tab2, tab3 = st.tabs(["⚡ Status", "✏️ Editar", "🗑️ Excluir"])
            
            with tab1:
                st.caption("Mudar de Pago para Pendente (ou vice-versa)")
                if st.button("Alterar Status"):
                    novo_status = 0 if item_atual['pago'] == 1 else 1
                    mudar_status_pago(id_sel, novo_status)
                    st.success("Status alterado!")
                    time.sleep(0.5)
                    st.rerun()

            with tab2:
                st.caption("Corrigir valores ou descrições")
                # Formulário de Edição
                with st.form("form_edicao"):
                    col_e1, col_e2 = st.columns(2)
                    nova_desc = col_e1.text_input("Descrição", value=item_atual['descricao'])
                    novo_valor = col_e2.number_input("Valor (Sinal negativo para despesa)", value=float(item_atual['valor']), step=0.01)
                    
                    col_e3, col_e4 = st.columns(2)
                    nova_cat = col_e3.selectbox("Categoria", LISTA_CATEGORIAS, index=LISTA_CATEGORIAS.index(item_atual['categoria']) if item_atual['categoria'] in LISTA_CATEGORIAS else 0)
                    nova_data = col_e4.date_input("Data", value=item_atual['data'])
                    
                    novo_fixo_bool = st.checkbox("Fixo Mensal?", value=(item_atual['fixo'] == 1))
                    
                    if st.form_submit_button("Atualizar Dados"):
                        novo_fixo_int = 1 if novo_fixo_bool else 0
                        atualizar_movimento_completo(id_sel, nova_data, nova_cat, nova_desc, novo_valor, novo_fixo_int)
                        st.success("Dados atualizados!")
                        st.rerun()

            with tab3:
                st.caption("Cuidado: Isso apaga do banco de dados.")
                if st.button("Excluir Definitivamente"):
                    excluir_movimento(id_sel)
                    st.success("Apagado!")
                    st.rerun()

else:
    st.warning("Sem dados.")
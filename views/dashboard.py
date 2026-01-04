import streamlit as st
import pandas as pd
from services.crud import adicionar_movimento, mudar_status_pago, atualizar_movimento, excluir_movimento, salvar_meta, ler_metas

# Agora a função recebe o user_id vindo do Login
def show_dashboard(user_id, df_bruto, lista_categorias):
    st.title("📊 Painel Financeiro")

    if df_bruto.empty:
        st.info("Bem-vindo! Comece adicionando seus dados na barra lateral.")
        # Não damos return aqui para permitir ver a sidebar e adicionar itens

    # Preparar dados (só faz se tiver dados)
    if not df_bruto.empty:
        df_bruto['data'] = pd.to_datetime(df_bruto['data'])
        df_bruto['mes_ano'] = df_bruto['data'].dt.strftime('%Y-%m')
        lista_meses = sorted(df_bruto['mes_ano'].unique(), reverse=True)
    else:
        lista_meses = []

    # --- Ferramentas ---
    with st.sidebar.expander("🛠️ Ferramentas"):
        st.markdown("**🔄 Clonar Mês**")
        if lista_meses:
            mes_origem = st.selectbox("Copiar de:", lista_meses)
            if st.button("Clonar Pendências"):
                fixos = df_bruto[(df_bruto['mes_ano'] == mes_origem) & (df_bruto['fixo'] == True)]
                if not fixos.empty:
                    for _, row in fixos.iterrows():
                        nova_data = row['data'] + pd.DateOffset(months=1)
                        # Passamos o user_id aqui!
                        adicionar_movimento(user_id, nova_data.date(), row['categoria'], row['descricao'], row['tipo'], row['valor'], True, False)
                    st.success("Gerado!")
                    st.rerun()
                else:
                    st.warning("Nada fixo.")
        else:
            st.caption("Cadastre dados primeiro.")

    # --- Metas ---
    with st.sidebar.expander("🎯 Metas"):
        cat_meta = st.selectbox("Categoria", [c for c in lista_categorias if "Receita" not in c])
        valor_meta = st.number_input("Limite (R$)", min_value=0.0, step=50.0)
        if st.button("Salvar Meta"):
            salvar_meta(user_id, cat_meta, valor_meta) # Passamos user_id
            st.success("Salvo!")
            st.rerun()

    # Se não houver dados, paramos aqui o visual principal
    if df_bruto.empty:
        return

    # --- Filtro Principal ---
    col1, col2 = st.columns([1, 3])
    with col1:
        mes_selecionado = st.selectbox("📅 Mês:", lista_meses)
    
    df_mes = df_bruto[df_bruto['mes_ano'] == mes_selecionado].copy()

    # Cards e Métricas
    receitas = df_mes[df_mes["valor"] > 0]["valor"].sum()
    despesas = df_mes[df_mes["valor"] < 0]["valor"].sum()
    saldo = receitas + despesas
    falta_pagar = df_mes[(df_mes["valor"] < 0) & (df_mes["pago"] == False)]["valor"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo", f"R$ {saldo:,.2f}", delta=saldo)
    c4.metric("A Pagar", f"R$ {falta_pagar:,.2f}")

    st.divider()

    # --- Monitor de Metas ---
    df_metas = ler_metas(user_id) # Passamos user_id
    if not df_metas.empty:
        gastos_cat = df_mes[df_mes["valor"] < 0].copy()
        gastos_cat["valor"] = gastos_cat["valor"].abs()
        gastos_por_cat = gastos_cat.groupby("categoria")["valor"].sum()
        
        cols = st.columns(3)
        idx = 0
        for _, row in df_metas.iterrows():
            cat = row['categoria']
            teto = row['valor_limite']
            gasto = gastos_por_cat.get(cat, 0.0)
            perc = min(gasto / teto, 1.0) if teto > 0 else 0
            
            with cols[idx % 3]:
                st.markdown(f"**{cat}**")
                st.progress(perc)
                st.caption(f"{gasto:,.0f} / {teto:,.0f} ({perc*100:.0f}%)")
            idx += 1
    
    st.divider()

    # --- Gráficos e Tabelas ---
    c_graf, c_tab = st.columns([1, 2])
    with c_graf:
        st.subheader("Gráfico")
        df_desp = df_mes[df_mes["valor"] < 0].copy()
        if not df_desp.empty:
            df_desp["abs"] = df_desp["valor"].abs()
            st.bar_chart(df_desp.groupby("categoria")["abs"].sum())

    with c_tab:
        st.subheader("Lançamentos")
        df_show = df_mes.copy()
        df_show['status'] = df_show['pago'].apply(lambda x: "✅" if x else "🕒")
        st.dataframe(df_show[["id", "data", "status", "categoria", "descricao", "valor"]], hide_index=True, use_container_width=True)

        if not df_show.empty:
            opcoes = df_show.apply(lambda x: f"{x['id']}: {x['descricao']} ({x['valor']})", axis=1)
            item_sel = st.selectbox("Selecionar Item:", options=opcoes)
            id_sel = int(item_sel.split(":")[0])
            item_atual = df_show[df_show['id'] == id_sel].iloc[0]

            t1, t2, t3 = st.tabs(["Status", "Editar", "Excluir"])
            with t1:
                if st.button("Mudar Status Pago/Pendente"):
                    mudar_status_pago(id_sel, user_id, not item_atual['pago']) # User ID aqui
                    st.success("Feito!")
                    st.rerun()
            with t2:
                with st.form("edit"):
                    n_desc = st.text_input("Desc", item_atual['descricao'])
                    n_val = st.number_input("Valor", float(item_atual['valor']))
                    n_cat = st.selectbox("Cat", lista_categorias, index=lista_categorias.index(item_atual['categoria']) if item_atual['categoria'] in lista_categorias else 0)
                    n_dat = st.date_input("Data", item_atual['data'])
                    n_fix = st.checkbox("Fixo?", item_atual['fixo'])
                    if st.form_submit_button("Salvar Edição"):
                        atualizar_movimento(id_sel, user_id, n_dat, n_cat, n_desc, n_val, n_fix) # User ID aqui
                        st.success("Atualizado!")
                        st.rerun()
            with t3:
                if st.button("Excluir Definitivamente"):
                    excluir_movimento(id_sel, user_id) # User ID aqui
                    st.success("Tchau!")
                    st.rerun()
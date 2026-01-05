import streamlit as st
import pandas as pd
import plotly.express as px
from views.styles import apply_custom_style
from services.crud import adicionar_movimento, mudar_status_pago, atualizar_movimento, excluir_movimento, salvar_meta, ler_metas

# Função auxiliar para formatar dinheiro BR
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Função para colorir a tabela (Pandas Styler)
def colorir_valores(val):
    color = '#ef4444' if "-" in val else '#16a34a'
    return f'color: {color}; font-weight: bold'

def show_dashboard(user_id, df_bruto, lista_categorias):
    apply_custom_style()

    st.markdown("## 📊 Painel Financeiro")
    st.caption("Visão geral estratégica das suas contas")

    if df_bruto.empty:
        st.info("Bem-vindo! Use o menu lateral para adicionar sua primeira movimentação.")
        return

    # Preparação de Dados
    df_bruto['data'] = pd.to_datetime(df_bruto['data'])
    df_bruto['mes_ano'] = df_bruto['data'].dt.strftime('%Y-%m')
    lista_meses = sorted(df_bruto['mes_ano'].unique(), reverse=True)

    # --- SIDEBAR ---
    with st.sidebar.expander("🛠️ Clonar Mês Anterior"):
        if lista_meses:
            mes_origem = st.selectbox("Copiar de:", lista_meses)
            if st.button("Clonar Pendências"):
                fixos = df_bruto[(df_bruto['mes_ano'] == mes_origem) & (df_bruto['fixo'] == True)]
                if not fixos.empty:
                    for _, row in fixos.iterrows():
                        nova_data = row['data'] + pd.DateOffset(months=1)
                        adicionar_movimento(user_id, nova_data.date(), row['categoria'], row['descricao'], row['tipo'], row['valor'], True, False)
                    st.success("Gerado!")
                    st.rerun()
                else:
                    st.warning("Nada fixo.")

    with st.sidebar.expander("🎯 Definir Metas"):
        cat_meta = st.selectbox("Categoria", [c for c in lista_categorias if "Receita" not in c])
        valor_meta = st.number_input("Limite Mensal (R$)", min_value=0.0, step=50.0)
        if st.button("Salvar Meta"):
            salvar_meta(user_id, cat_meta, valor_meta)
            st.success("Salvo!")
            st.rerun()

    # --- FILTRO ---
    col_filtro, _ = st.columns([1, 3])
    with col_filtro:
        mes_selecionado = st.selectbox("📅 Período:", lista_meses)
    
    df_mes = df_bruto[df_bruto['mes_ano'] == mes_selecionado].copy()

    # --- CÁLCULOS ---
    receitas = df_mes[df_mes["valor"] > 0]["valor"].sum()
    despesas = df_mes[df_mes["valor"] < 0]["valor"].sum()
    saldo = receitas + despesas
    falta_pagar = df_mes[(df_mes["valor"] < 0) & (df_mes["pago"] == False)]["valor"].sum()

    # --- CARDS DE KPI ---
    st.markdown("<br>", unsafe_allow_html=True) 
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""
        <div class="card receita">
            <div class="card-title">Receitas</div>
            <div class="card-value">{formatar_real(receitas)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="card despesa">
            <div class="card-title">Despesas</div>
            <div class="card-value" style="color: #ef4444;">{formatar_real(despesas)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        cor_saldo = "#3b82f6" if saldo >= 0 else "#ef4444"
        st.markdown(f"""
        <div class="card saldo">
            <div class="card-title">Saldo Atual</div>
            <div class="card-value" style="color: {cor_saldo};">{formatar_real(saldo)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="card pagar">
            <div class="card-title">A Pagar</div>
            <div class="card-value">{formatar_real(falta_pagar)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- METAS ---
    df_metas = ler_metas(user_id)
    if not df_metas.empty:
        st.subheader("🎯 Metas do Mês")
        gastos_cat = df_mes[df_mes["valor"] < 0].copy()
        gastos_cat["valor"] = gastos_cat["valor"].abs()
        gastos_por_cat = gastos_cat.groupby("categoria")["valor"].sum()
        
        cols_meta = st.columns(3)
        idx = 0
        for _, row in df_metas.iterrows():
            cat = row['categoria']
            teto = row['valor_limite']
            gasto = gastos_por_cat.get(cat, 0.0)
            perc = min(gasto / teto, 1.0) if teto > 0 else 0
            
            with cols_meta[idx % 3]:
                st.markdown(f"**{cat}**")
                if perc >= 1.0:
                    st.error(f"🚨 {formatar_real(gasto)} / {formatar_real(teto)}")
                    st.progress(1.0)
                elif perc > 0.8:
                    st.warning(f"⚠️ {formatar_real(gasto)}")
                    st.progress(perc)
                else:
                    st.caption(f"{formatar_real(gasto)} de {formatar_real(teto)}")
                    st.progress(perc)
            idx += 1
        st.divider()

    # --- ÁREA PRINCIPAL ---
    col_graf, col_tab = st.columns([1, 2])

    with col_graf:
        with st.container(border=True):
            st.subheader("Gastos")
            df_desp = df_mes[df_mes["valor"] < 0].copy()
            if not df_desp.empty:
                df_desp["abs_valor"] = df_desp["valor"].abs()
                total_abs = df_desp["abs_valor"].sum()
                
                fig = px.pie(df_desp, values='abs_valor', names='categoria', hole=0.65, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.add_annotation(text=f"<b>R$ {total_abs:,.0f}</b>", x=0.5, y=0.5, showarrow=False, font_size=18, font_color="#555")
                fig.update_traces(textposition='outside', textinfo='percent+label')
                fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20), height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados.")

    with col_tab:
        with st.container(border=True):
            st.subheader("Extrato Detalhado")
            df_show = df_mes.copy()
            df_show['Vencimento'] = df_show['data'].dt.strftime('%d/%m')
            df_show['Status'] = df_show['pago'].apply(lambda x: "✅" if x else "🕒")
            df_show['Valor_Visual'] = df_show['valor'].apply(formatar_real)

            cols_show = ["id", "Vencimento", "categoria", "descricao", "Valor_Visual", "Status"]
            
            st.dataframe(
                df_show[cols_show].style.map(colorir_valores, subset=['Valor_Visual']),
                hide_index=True,
                use_container_width=True,
                height=350
            )

            # --- AQUI ESTÁ A CORREÇÃO: ABAS PARA GERENCIAR ---
            with st.expander("⚡ Gerenciar Lançamento (Editar / Excluir)"):
                if not df_show.empty:
                    # Seletor do Item
                    opcoes = df_show.apply(lambda x: f"{x['id']} - {x['descricao']} ({x['Valor_Visual']})", axis=1)
                    item_sel = st.selectbox("Selecione o item para alterar:", options=opcoes)
                    
                    if item_sel:
                        id_sel = int(item_sel.split(" -")[0])
                        item_atual = df_mes[df_mes['id'] == id_sel].iloc[0]

                        # Criamos abas para separar ações rápidas da edição completa
                        tab_acoes, tab_editar = st.tabs(["⚡ Ações Rápidas", "📝 Editar Dados"])

                        # ABA 1: Botões Rápidos
                        with tab_acoes:
                            c_e1, c_e2 = st.columns(2)
                            with c_e1:
                                if st.button("🔄 Alternar Status (Pago/Pendente)", key="btn_status"):
                                    mudar_status_pago(id_sel, user_id, not item_atual['pago'])
                                    st.success("Status alterado!")
                                    st.rerun()
                            with c_e2:
                                if st.button("🗑️ Excluir Registro", key="btn_excluir", type="primary"):
                                    excluir_movimento(id_sel, user_id)
                                    st.success("Excluído!")
                                    st.rerun()

                        # ABA 2: Formulário de Edição
                        with tab_editar:
                            with st.form(key="form_editar"):
                                c1, c2 = st.columns(2)
                                n_desc = c1.text_input("Descrição", value=item_atual['descricao'])
                                n_val = c2.number_input("Valor (Positivo=Receita / Negativo=Despesa)", value=float(item_atual['valor']), step=0.01)
                                
                                c3, c4 = st.columns(2)
                                # Lógica para garantir que a categoria atual esteja na lista
                                idx_cat = lista_categorias.index(item_atual['categoria']) if item_atual['categoria'] in lista_categorias else 0
                                n_cat = c3.selectbox("Categoria", lista_categorias, index=idx_cat)
                                n_dat = c4.date_input("Data Vencimento", value=item_atual['data'])
                                
                                n_fix = st.checkbox("É uma conta fixa mensal?", value=item_atual['fixo'])
                                
                                if st.form_submit_button("💾 Salvar Alterações"):
                                    atualizar_movimento(id_sel, user_id, n_dat, n_cat, n_desc, n_val, n_fix)
                                    st.success("Dados atualizados com sucesso!")
                                    st.rerun()
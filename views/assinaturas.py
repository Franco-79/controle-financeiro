import streamlit as st
import pandas as pd

def show_assinaturas(df_bruto):
    st.title("📺 Assinaturas")
    
    if df_bruto.empty:
        st.warning("Sem dados.")
        return

    df_subs = df_bruto[df_bruto['categoria'] == "Assinaturas/Streaming"].copy()
    
    if not df_subs.empty:
        df_subs['data'] = pd.to_datetime(df_subs['data'])
        df_subs['mes_ano'] = df_subs['data'].dt.strftime('%Y-%m')
        
        # Pega o último mês com dados
        ultimo_mes = sorted(df_subs['mes_ano'].unique())[-1]
        df_atual = df_subs[df_subs['mes_ano'] == ultimo_mes]
        
        custo = df_atual['valor'].sum()
        
        st.metric("Mensalidade Total", f"R$ {abs(custo):,.2f}")
        st.metric("Custo Anual Estimado", f"R$ {abs(custo)*12:,.2f}")
        
        st.dataframe(df_atual[["descricao", "valor", "data"]], use_container_width=True)
    else:
        st.info("Nenhuma conta 'Assinaturas/Streaming' encontrada.")
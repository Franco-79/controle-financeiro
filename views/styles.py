import streamlit as st

def apply_custom_style():
    st.markdown("""
    <style>
    /* Fonte Geral */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Cards de KPI */
    .card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #ccc;
        margin-bottom: 10px;
    }

    /* Cores Específicas das Bordas */
    .card.receita { border-left-color: #22c55e; } /* Verde */
    .card.despesa { border-left-color: #ef4444; } /* Vermelho */
    .card.saldo   { border-left-color: #3b82f6; } /* Azul */
    .card.pagar   { border-left-color: #f97316; } /* Laranja */

    /* Tipografia do Card */
    .card-title {
        font-size: 14px;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 5px;
    }
    .card-value {
        font-size: 24px;
        font-weight: 700;
        color: #1e293b;
    }
    </style>
    """, unsafe_allow_html=True)
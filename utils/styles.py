import streamlit as st

def cargar_estilos():
    st.markdown("""
    <style>
        .main {
            background-color: #F7FAFC;
        }

        .title {
            font-size: 42px;
            font-weight: 800;
            color: #1E3A5F;
            text-align: center;
            margin-bottom: 5px;
        }

        .subtitle {
            font-size: 18px;
            color: #4A5568;
            text-align: center;
            margin-bottom: 30px;
        }

        .card {
            background-color: white;
            padding: 28px;
            border-radius: 20px;
            box-shadow: 0px 4px 14px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }

        .metric-card {
            background: linear-gradient(135deg, #E0F2FE, #F0FDFA);
            padding: 22px;
            border-radius: 18px;
            text-align: center;
            box-shadow: 0px 3px 10px rgba(0,0,0,0.07);
        }

        .metric-number {
            font-size: 34px;
            font-weight: 800;
            color: #0F766E;
        }

        .metric-label {
            font-size: 15px;
            color: #475569;
        }

        .level-box {
            background: linear-gradient(135deg, #2563EB, #0F766E);
            color: white;
            padding: 28px;
            border-radius: 22px;
            text-align: center;
            margin-bottom: 20px;
        }

        .level-title {
            font-size: 28px;
            font-weight: 800;
        }
    </style>
    """, unsafe_allow_html=True)
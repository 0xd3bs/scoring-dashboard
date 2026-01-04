"""
Dashboard de Control con Streamlit - Conecta con AgentCore
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import boto3
import os

st.set_page_config(
    page_title="Fintech Scoring Dashboard",
    page_icon="💰",
    layout="wide"
)

# Configuración AWS desde secrets de Streamlit o variables de entorno
if "aws" in st.secrets:
    AGENT_ARN = st.secrets["agent"]["AGENT_ARN"]
    boto3_client = boto3.client(
        "bedrock-agentcore",
        region_name=st.secrets["aws"]["AWS_DEFAULT_REGION"],
        aws_access_key_id=st.secrets["aws"]["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
    )
else:
    AGENT_ARN = os.getenv("AGENT_ARN", "arn:aws:bedrock-agentcore:us-east-1:545009829420:runtime/agentcore-l1wRnE2RMs")
    boto3_client = boto3.client("bedrock-agentcore", region_name="us-east-1")

def invoke_agent(cliente: dict, salud_cartera: dict) -> dict:
    """Invoca el agente CRO en AgentCore"""
    payload = json.dumps({"cliente": cliente, "salud_cartera": salud_cartera}).encode()
    response = boto3_client.invoke_agent_runtime(agentRuntimeArn=AGENT_ARN, payload=payload)
    content = [chunk.decode("utf-8") for chunk in response.get("response", [])]
    return json.loads("".join(content))

def main():
    st.title("🏦 Dashboard de Control - Sistema de Scoring Crediticio")
    st.markdown("---")
    
    with st.sidebar:
        st.header("⚙️ Configuración de Cartera")
        capital_disponible = st.number_input("Capital Disponible ($)", min_value=0.0, value=1000000.0, step=10000.0)
        tasa_mora = st.slider("Tasa de Mora Actual (%)", min_value=0.0, max_value=20.0, value=3.5, step=0.1) / 100
        objetivo_mensual = st.number_input("Objetivo Mensual ($)", min_value=0.0, value=500000.0, step=10000.0)
    
    tab1, tab2, tab3 = st.tabs(["📊 Evaluación Individual", "📈 Análisis de Cartera", "🔍 Simulaciones"])
    
    with tab1:
        st.header("Evaluación Individual de Cliente")
        
        col1, col2 = st.columns(2)
        with col1:
            edad = st.number_input("Edad", min_value=18, max_value=80, value=35)
            ingresos = st.number_input("Ingresos Anuales ($)", min_value=0.0, value=50000.0, step=1000.0)
        with col2:
            estabilidad = st.number_input("Estabilidad Laboral (años)", min_value=0.0, value=3.0, step=0.5)
            ratio_deuda = st.slider("Ratio Deuda/Ingreso", min_value=0.0, max_value=1.0, value=0.3, step=0.01)
        
        if st.button("🔍 Evaluar Cliente", type="primary"):
            cliente = {"edad": edad, "ingresos": ingresos, "estabilidad_laboral": estabilidad, "ratio_deuda_ingreso": ratio_deuda}
            salud_cartera = {"capital_disponible": capital_disponible, "tasa_mora_actual": tasa_mora, "objetivo_mensual_desembolso": objetivo_mensual}
            
            try:
                with st.spinner("Evaluando cliente..."):
                    resultado = invoke_agent(cliente, salud_cartera)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Score ML", f"{resultado['score_ml']:.3f}")
                with col2:
                    decision = resultado["decision"]["decision"]
                    color = "green" if decision == "APROBADO" else "red"
                    st.markdown(f"<h3 style='color: {color}'>{decision}</h3>", unsafe_allow_html=True)
                with col3:
                    st.metric("Score Final", resultado["decision"].get("score_final", "N/A"))
                
                st.subheader("Justificación")
                st.write(resultado["decision"]["justificacion"])
                
                if "recomendaciones" in resultado["decision"]:
                    st.info(resultado["decision"]["recomendaciones"])
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with tab2:
        st.header("Salud de Cartera")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Capital Disponible", f"${capital_disponible:,.0f}")
        with col2:
            st.metric("Tasa de Mora", f"{tasa_mora:.1%}")
        with col3:
            st.metric("Objetivo Mensual", f"${objetivo_mensual:,.0f}")
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=tasa_mora * 100,
            title={'text': "Riesgo de Cartera (%)"},
            gauge={'axis': {'range': [0, 20]},
                   'steps': [{'range': [0, 3], 'color': "lightgreen"},
                            {'range': [3, 7], 'color': "yellow"},
                            {'range': [7, 20], 'color': "red"}]}
        ))
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("Simulaciones de Escenarios")
        
        import numpy as np
        
        n_clientes = st.slider("Número de clientes a simular", 10, 100, 20)
        
        if st.button("🎲 Generar y Evaluar Clientes"):
            np.random.seed(42)
            resultados = []
            progress_bar = st.progress(0)
            
            for i in range(n_clientes):
                cliente = {
                    "edad": float(np.clip(np.random.normal(35, 12), 18, 70)),
                    "ingresos": float(np.random.lognormal(10, 0.5)),
                    "estabilidad_laboral": float(np.random.uniform(0, 10)),
                    "ratio_deuda_ingreso": float(np.random.beta(2, 5))
                }
                salud = {
                    "capital_disponible": capital_disponible,
                    "tasa_mora_actual": tasa_mora,
                    "objetivo_mensual_desembolso": objetivo_mensual
                }
                
                try:
                    resultado = invoke_agent(cliente, salud)
                    resultados.append({
                        "id": i+1,
                        "edad": cliente["edad"],
                        "ingresos": cliente["ingresos"],
                        "score_ml": resultado["score_ml"],
                        "decision": resultado["decision"]["decision"]
                    })
                except Exception as e:
                    st.warning(f"Error en cliente {i+1}: {e}")
                
                progress_bar.progress((i+1)/n_clientes)
            
            if resultados:
                df = pd.DataFrame(resultados)
                
                col1, col2, col3 = st.columns(3)
                aprobados = len(df[df["decision"] == "APROBADO"])
                with col1:
                    st.metric("Aprobados", aprobados, f"{aprobados/len(df)*100:.1f}%")
                with col2:
                    st.metric("Score Promedio", f"{df['score_ml'].mean():.3f}")
                with col3:
                    st.metric("Total Evaluados", len(df))
                
                fig1 = px.histogram(df, x="score_ml", color="decision", title="Distribución de Scores")
                st.plotly_chart(fig1, use_container_width=True)
                
                st.dataframe(df)

if __name__ == "__main__":
    main()

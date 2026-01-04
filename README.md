# Scoring Dashboard

Dashboard para el sistema de scoring crediticio. Se conecta con el agente CRO deployado en Amazon Bedrock AgentCore.

## Configuración

```bash
pip install -r requirements.txt
```

## Variables de entorno

```bash
export AWS_PROFILE=strands-agent
export AWS_REGION=us-east-1
export AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:545009829420:runtime/agentcore-l1wRnE2RMs
```

## Ejecución local

```bash
streamlit run app.py
```

## Deploy

### Streamlit Community Cloud
1. Subir a GitHub
2. Conectar en share.streamlit.io
3. Configurar secrets de AWS

import os
import re
import json
import anthropic
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class SearchRequest(BaseModel):
    query: str

@app.get("/")
def root():
    return FileResponse("index.html")

@app.post("/sniper")
def sniper(request: SearchRequest):
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": """Busca en internet oportunidades reales de inversion infravaloradas en: """ + request.query + """

Busca listados reales actuales. Luego responde UNICAMENTE con un JSON array, sin texto antes ni despues, con este formato exacto:
[
  {
    "titulo": "nombre del producto",
    "precio_detectado": 1000,
    "moneda": "EUR",
    "valor_mercado": 1500,
    "descuento_pct": 33,
    "score": 85,
    "decision": "COMPRAR",
    "riesgo": "bajo",
    "liquidez": "alta",
    "motivo": "explicacion de por que es oportunidad",
    "urgencia": "explicacion de urgencia",
    "verificacion": "pasos para verificar",
    "url": "https://url-real.com"
  }
]

Incluye 3-5 oportunidades. SOLO el JSON array, nada mas."""
        }]
    )

    full_text = ""
    for block in message.content:
        if hasattr(block, "text"):
            full_text += block.text

    m = re.search(r'\[[\s\S]*\]', full_text)
    if m:
        return {"result": m.group(), "query": request.query}
    return {"result": full_text, "query": request.query}

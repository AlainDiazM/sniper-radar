import os
import json
import anthropic
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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

SYSTEM_PROMPT = """Eres SNIPER RADAR, un sistema experto en detectar oportunidades de inversión y coleccionismo infravaloradas en internet.

Tu misión: buscar en internet productos reales que se vendan muy por debajo de su valor real (mínimo 25% de descuento sobre valor de mercado).

Para cada oportunidad detectada, devuelve un JSON array con esta estructura exacta:
[
  {
    "titulo": "nombre del producto",
    "precio_detectado": número,
    "moneda": "EUR o USD",
    "valor_mercado": número,
    "descuento_pct": número,
    "score": número del 0 al 100,
    "decision": "COMPRAR" o "ANALIZAR RÁPIDO" o "DESCARTAR",
    "riesgo": "bajo" o "medio" o "alto",
    "liquidez": "alta" o "media" o "baja",
    "motivo": "explicación detallada de por qué es una oportunidad real",
    "urgencia": "explicación de urgencia temporal si aplica",
    "verificacion": "pasos clave para verificar antes de comprar",
    "url": "URL real y verificable donde se vende"
  }
]

Busca entre 3 y 5 oportunidades reales. Prioriza score >= 75.
Responde SOLO con el JSON array, sin texto adicional."""

@app.get("/")
def root():
    return {"status": "SNIPER R
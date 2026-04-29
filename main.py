import os
import anthropic
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    "decision": "COMPRAR" | "ANALIZAR RÁPIDO" | "DESCARTAR",
    "riesgo": "bajo" | "medio" | "alto",
    "liquidez": "alta" | "media" | "baja",
    "motivo": "explicación detallada de por qué es una oportunidad real",
    "urgencia": "explicación de urgencia temporal si aplica",
    "verificacion": "pasos clave para verificar antes de comprar",
    "url": "URL real y verificable donde se vende o referencia"
  }
]

Busca entre 3 y 5 oportunidades reales. Prioriza score >= 75.
Incluye URLs reales de plataformas como eBay, Catawiki, Wallapop, Idealista, subastas Christie's/Sotheby's, etc.
Sé específico con precios reales y motivos concretos (error de catalogación, venta urgente, mal tasado, etc.).
Responde SOLO con el JSON array, sin texto adicional."""

@app.get("/")
def root():
    return {"status": "SNIPER RADAR ACTIVO"}

@app.post("/sniper")
def sniper(request: SearchRequest):
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": f"Busca oportunidades reales infravaloradas en: {request.query}. Busca listados actuales reales con URLs verificables."
        }]
    )
    
    full_text = ""
    for block in message.content:
        if block.type == "text":
            full_text += block.text

    return {"result": full_text, "query": request.query}

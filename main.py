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

SYSTEM_PROMPT = "Eres SNIPER RADAR, experto en detectar oportunidades infravaloradas. Busca productos reales que se vendan mas del 25% por debajo de su valor de mercado. Devuelve SOLO un JSON array con campos: titulo, precio_detectado, moneda, valor_mercado, descuento_pct, score, decision, riesgo, liquidez, motivo, urgencia, verificacion, url. Sin texto adicional."

@app.get("/")
def root():
    return FileResponse("index.html")

@app.post("/sniper")
def sniper(request: SearchRequest):
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": "Busca oportunidades reales infravaloradas en: " + request.query}]
    )
    full_text = ""
    for block in message.content:
        if hasattr(block, "text"):
            full_text += block.text
    match = re.search(r'\[[\s\S]*\]', full_text)
    if match:
        return {"result": match.group(), "query": request.query}
    return {"result": full_text, "query": request.query}

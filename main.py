import os
import re
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
    fuentes: str = ""

@app.get("/")
def root():
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.post("/sniper")
def sniper(request: SearchRequest):
    fuentes = request.fuentes or "eBay, Catawiki, Wallapop, Todocoleccion"
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": """Eres un experto cazador de oportunidades de inversion y coleccionismo.

Busca ahora mismo en """ + fuentes + """ productos de la categoria: """ + request.query + """

Encuentra productos reales que se vendan por debajo de su valor. Devuelve exactamente este formato JSON, sin texto antes ni despues:

[{"titulo":"nombre del producto","precio_detectado":1000,"moneda":"EUR","valor_mercado":1500,"descuento_pct":33,"score":85,"decision":"COMPRAR","riesgo":"medio","liquidez":"alta","motivo":"razon concreta","urgencia":"tiempo disponible","verificacion":"como verificar","url":"https://enlace-real.com"}]

Incluye 3 a 5 productos reales. Solo el JSON, nada mas."""
        }]
    )

    full_text = ""
    for block in message.content:
        if hasattr(block, "text"):
            full_text += block.text

    m = re.search(r'\[[\s\S]*?\]', full_text)
    if m:
        return {"result": m.group(), "query": request.query}
    return {"result": full_text, "query": request.query}
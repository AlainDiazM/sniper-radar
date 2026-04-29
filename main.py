import os
import re
import anthropic
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
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
        max_tokens=3000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": "Actua como equipo de elite de deteccion de oportunidades de inversion y coleccionismo. Busca en " + fuentes + " productos de la categoria " + request.query + " que se esten vendiendo muy por debajo de su valor real. Para cada oportunidad encontrada devuelve SOLO un JSON array sin texto adicional con estos campos: titulo, precio_detectado, moneda, valor_mercado, descuento_pct, score, decision, riesgo, liquidez, motivo, urgencia, verificacion, url"
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

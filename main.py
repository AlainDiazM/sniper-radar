import os
import re
import requests
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
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")


class SearchRequest(BaseModel):
    query: str
    fuentes: str = ""


def firecrawl_search(query, num_results=8):
    url = "https://api.firecrawl.dev/v1/search"
    headers = {
        "Authorization": "Bearer " + FIRECRAWL_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "limit": num_results,
        "scrapeOptions": {"formats": ["markdown"]}
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        data = r.json()
        results = []
        for item in data.get("data", []):
            results.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "content": item.get("markdown", "")[:600]
            })
        return results
    except Exception as e:
        print("Firecrawl error:", e)
        return []


@app.get("/")
def root():
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.post("/sniper")
def sniper(request: SearchRequest):
    search_query = request.query + " comprar precio oferta infravalorado ebay catawiki wallapop"
    listings = firecrawl_search(search_query, num_results=8)

    listings_text = ""
    for i, l in enumerate(listings):
        listings_text += "\n" + str(i+1) + ". URL: " + l["url"] + "\nTitulo: " + l["title"] + "\nContenido: " + l["content"] + "\n"

    if not listings_text.strip():
        listings_text = "No se encontraron listings especificos."

    prompt = (
        "Eres un experto cazador de oportunidades de inversion y coleccionismo.\n\n"
        "Analiza estos listings reales encontrados en internet para la categoria: " + request.query + "\n\n"
        + listings_text +
        "\n\nPara cada listing que represente una oportunidad real de compra por debajo de su valor, "
        "devuelve SOLO un JSON array sin texto adicional con estos campos exactos: "
        "titulo, precio_detectado, moneda, valor_mercado, descuento_pct, score, decision, "
        "riesgo, liquidez, motivo, urgencia, verificacion, url. "
        "USA las URLs reales de los listings. "
        "decision debe ser COMPRAR o ANALIZAR RAPIDO o DESCARTAR. "
        "Incluye 3-5 oportunidades. Solo el JSON array, nada mas."
    )

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    full_text = ""
    for block in message.content:
        if hasattr(block, "text"):
            full_text += block.text

    m = re.search(r'\[[\s\S]*\]', full_text)
    if m:
        return {"result": m.group(), "query": request.query}
    return {"result": full_text, "query": request.query}

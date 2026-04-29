import os
import re
import json
import anthropic
import requests
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

def firecrawl_search(query, num_results=5):
    url = "https://api.firecrawl.dev/v1/search"
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
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
                "content": item.get("markdown", "")[:500]
            })
        return results
    except Exception as e:
        return []

@app.get("/")
def root():
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.post("/sniper")
def sniper(request: SearchRequest):
    fuentes = request.fuentes or "eBay, Catawiki, Wallapop, Todocoleccion"
    
    search_query = f"{request.query} comprar precio infravalorado site:ebay.es OR site:catawiki.com OR site:wallapop.com OR site:todocoleccion.net"
    listings = firecrawl_search(search_query, num_results=8)
    
    listings_text = ""
    for i, l in enumerate(listings):
        listings_text += f"\n{i+1}. URL: {l['url']}\nTitulo: {l['title']}\nContenido: {l['content']}\n"

    if not listings_text:
        listings_text = "No se encontraron listings. Usa tu conocimiento para sugerir oportunidades típicas."

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": f"""Eres un experto cazador de oportunidades de inversión y coleccionismo.

Analiza estos listings reales encontrados en internet para la categoría "{request.query}":

{listings_text}

Para cada listing que represente una oportunidad real de compra por debajo de su valor, devuelve SOLO este JSON array sin texto adicional:

[{{"titulo":"nombre del producto","precio_detectado":1000,"moneda":"EUR","valor_mercado":1500,"descuento_pct":33,"score":85,"decision":"COMPRAR","riesgo":"medio","liquidez":"alta","motivo":"razon concreta de por que esta infravalorado","urgencia":"tiempo disponible o urgencia","verificacion":"pasos para verificar antes de comprar","url":"URL real del listing"}}]

Incluye 3-5 oportunidades. USA las URLs reales de los listings. Solo el JSON."""
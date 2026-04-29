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

CATEGORY_SEARCHES = {
    "diamante": [
        "diamante GIA certificado venta precio euros catawiki.com",
        "diamante suelto ocasion venta directa todocoleccion.net",
        "diamond GIA certified sale ebay.es precio"
    ],
    "reloj": [
        "Rolex Submariner venta ocasion precio wallapop.com",
        "reloj lujo vintage venta particular precio euros",
        "Rolex Patek Philippe venta ebay.es precio ocasion"
    ],
    "comic": [
        "comic primera edicion marvel dc venta precio todocoleccion.net",
        "comic primera edicion occasion venta wallapop.com",
        "comic rare first edition sale price ebay.es"
    ],
    "vinilo": [
        "vinilo primera edicion coleccion venta precio discogs.com",
        "disco vinilo raro ocasion venta wallapop.com precio",
        "vinyl record first pressing rare sale ebay.es precio"
    ],
    "coche": [
        "coche clasico venta particular precio wallapop.com",
        "coche deportivo ocasion venta directa milanuncios.com precio",
        "classic car sale price coches.net ocasion"
    ],
    "inmueble": [
        "piso venta precio reducido ocasion idealista.com",
        "casa venta urgente precio bajo mercado fotocasa.es",
        "piso oportunidad precio rebajado habitaclia.com"
    ],
    "piso": [
        "piso venta precio reducido ocasion idealista.com",
        "casa venta urgente precio bajo mercado fotocasa.es",
        "piso oportunidad precio rebajado habitaclia.com"
    ],
    "joya": [
        "joya vintage oro venta precio ocasion catawiki.com",
        "joyeria antigua plata oro venta todocoleccion.net precio",
        "vintage jewelry gold sale price ebay.es ocasion"
    ],
    "arte": [
        "pintura oleo venta subasta precio catawiki.com",
        "obra arte original venta ocasion precio todocoleccion.net",
        "painting auction sale undervalued price catawiki.com"
    ]
}

def get_search_queries(query):
    query_lower = query.lower()
    for key in CATEGORY_SEARCHES:
        if key in query_lower:
            return CATEGORY_SEARCHES[key]
    return [
        query + " venta precio ocasion catawiki.com",
        query + " venta particular precio wallapop.com",
        query + " sale price undervalued ebay.es"
    ]

def firecrawl_search(query, num_results=5):
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
                "content": item.get("markdown", "")[:800]
            })
        return results
    except Exception as e:
        print("Firecrawl error:", e)
        return []


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
    queries = get_search_queries(request.query)
    all_listings = []
    for q in queries:
        results = firecrawl_search(q, num_results=4)
        all_listings.extend(results)

    seen_urls = set()
    unique_listings = []
    for l in all_listings:
        if l["url"] not in seen_urls:
            seen_urls.add(l["url"])
            unique_listings.append(l)

    listings_text = ""
    for i, l in enumerate(unique_listings[:10]):
        listings_text += "\n" + str(i+1) + ". URL: " + l["url"] + "\nTitulo: " + l["title"] + "\nContenido: " + l["content"] + "\n"

    if not listings_text.strip():
        listings_text = "No se encontraron listings especificos."

    prompt = (
        "Eres SNIPER RADAR, experto cazador de oportunidades de inversion y coleccionismo.\n\n"
        "Analiza estos listings reales de internet para la categoria: " + request.query + "\n\n"
        + listings_text +
        "\n\nIdentifica los productos con precio por debajo de su valor real de mercado. "
        "Si encuentras precios especificos, compara con el valor real. "
        "Devuelve SOLO un JSON array con estas oportunidades reales, sin texto adicional:\n"
        '[{"titulo":"nombre exacto","precio_detectado":1000,"moneda":"EUR","valor_mercado":1500,'
        '"descuento_pct":33,"score":85,"decision":"COMPRAR","riesgo":"medio","liquidez":"alta",'
        '"motivo":"razon concreta y especifica","urgencia":"tiempo disponible",'
        '"verificacion":"pasos concretos para verificar","url":"URL real del listing"}]\n\n'
        "USA las URLs reales encontradas. Solo el JSON array, nada mas."
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

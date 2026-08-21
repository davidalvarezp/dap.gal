import feedparser, requests, re, json, os
from datetime import datetime, date
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BLOG_ID           = "8727828863929929226"
TOKEN_FICHERO     = "/opt/sudofeed-blogger/token.json"
HISTORIAL_FICHERO = "/opt/sudofeed-blogger/historial.json"
OLLAMA_URL        = "http://localhost:11434/api/generate"
MODELO            = "qwen2.5:1.5b"

CATEGORIAS = {
    "noticias_it": {
        "label": "Noticias IT",
        "etiquetas": ["Noticias IT", "Tecnologia", "SudoFeed"],
        "feeds": [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://www.bleepingcomputer.com/feed/",
        ]
    },
    "ciberseguridad": {
        "label": "Ciberseguridad",
        "etiquetas": ["Ciberseguridad", "InfoSec", "Seguridad", "SudoFeed"],
        "feeds": [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://krebsonsecurity.com/feed/",
            "https://www.bleepingcomputer.com/feed/",
        ]
    },
    "vulnerabilidades": {
        "label": "Vulnerabilidades",
        "etiquetas": ["Vulnerabilidades", "CVE", "Exploit", "SudoFeed"],
        "feeds": [
            "https://www.darkreading.com/rss.xml",
            "https://isc.sans.edu/rssfeed_full.xml",
        ]
    },
    "linux": {
        "label": "Linux Tips",
        "etiquetas": ["Linux", "SysAdmin", "OpenSource", "SudoFeed"],
        "feeds": [
            "https://www.omglinux.com/feed/",
            "https://linuxhandbook.com/feed/",
            "https://itsfoss.com/feed/",
        ]
    },
    "software": {
        "label": "Software",
        "etiquetas": ["Software", "OpenSource", "SudoFeed"],
        "feeds": [
            "https://www.bleepingcomputer.com/feed/",
            "https://linuxhandbook.com/feed/",
        ]
    },
    "ia": {
        "label": "IA y Tecnologia",
        "etiquetas": ["Inteligencia Artificial", "AI", "MachineLearning", "SudoFeed"],
        "feeds": [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://www.darkreading.com/rss.xml",
        ]
    },
    "hacking_tools": {
        "label": "Herramientas de Hacking",
        "etiquetas": ["Hacking", "Pentesting", "CTF", "SudoFeed"],
        "feeds": [
            "https://www.welivesecurity.com/en/rss/feed/",
            "https://isc.sans.edu/rssfeed_full.xml",
        ]
    },
}

HORARIO = {
    8:  "noticias_it",
    10: "ciberseguridad",
    11: "vulnerabilidades",
    12: "linux",
    13: "software",
    14: "ia",
    17: "hacking_tools",
    18: "noticias_it",
    19: "ciberseguridad",
    20: "vulnerabilidades",
}

def cargar_historial():
    if not os.path.exists(HISTORIAL_FICHERO):
        return []
    try:
        with open(HISTORIAL_FICHERO, "r") as f:
            datos = json.load(f)
        hoy = date.today().isoformat()
        return [e for e in datos if e.get("fecha", "") >= hoy[:7]]
    except Exception:
        return []

def guardar_historial(historial, link):
    os.makedirs(os.path.dirname(HISTORIAL_FICHERO), exist_ok=True)
    historial.append({"link": link, "fecha": date.today().isoformat()})
    historial = historial[-200:]
    with open(HISTORIAL_FICHERO, "w") as f:
        json.dump(historial, f)

def obtener_credenciales():
    with open(TOKEN_FICHERO, "r") as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )
    if creds.expired:
        creds.refresh(Request())
        token_data["token"] = creds.token
        with open(TOKEN_FICHERO, "w") as f:
            json.dump(token_data, f)
    return creds

def obtener_noticias(feeds):
    noticias = []
    for url in feeds:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
            for entry in feed.entries[:8]:
                raw = entry.get("summary", entry.get("description", ""))
                resumen = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)).strip()
                noticias.append({
                    "titulo":  entry.get("title", "").strip(),
                    "link":    entry.get("link", ""),
                    "resumen": resumen[:2000],
                    "fuente":  feed.feed.get("title", "Desconocida"),
                })
        except Exception as e:
            print(f"[Aviso] Feed no disponible: {url} - {e}")
    return noticias

def elegir_noticia(noticias, historial):
    publicados = {e["link"] for e in historial}
    for n in noticias:
        if n["link"] not in publicados and n["titulo"] and n["link"]:
            return n
    return noticias[0] if noticias else None

def traducir_titulo(titulo):
    try:
        resp = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": titulo, "langpair": "en|es"},
            timeout=10,
        )
        datos = resp.json()
        if datos.get("responseStatus") == 200:
            return datos["responseData"]["translatedText"]
    except Exception as e:
        print(f"[Aviso] Error traduciendo titulo: {e}")
    return titulo

def redactar_articulo(titulo, resumen, categoria_label):
    prompt = f"""INSTRUCCION OBLIGATORIA: Responde UNICAMENTE en español de España. Absolutamente ninguna palabra en inglés en tu respuesta.

Eres un periodista tecnológico español senior especializado en {categoria_label}, con 15 años de experiencia escribiendo para medios como El País Tecnología y Xataka.

Tu tarea es redactar un artículo periodístico completo, extenso y profesional en español de España basándote en la siguiente noticia en inglés.

REGLAS ABSOLUTAS:
- TODO el artículo en español de España. Cero palabras en inglés.
- Vocabulario español: ordenador (no computadora), contraseña (no password), fichero (no archivo), parche (no patch), vulnerabilidad, cortafuegos, dirección IP, servidor, red
- Mínimo 600 palabras, idealmente 800
- Estructura periodística profesional con estas secciones en orden:
  1. Introducción impactante (1 párrafo)
  2. Contexto y antecedentes (1-2 párrafos)
  3. Detalles técnicos explicados para el lector (2-3 párrafos)
  4. Impacto y consecuencias (1-2 párrafos)
  5. Recomendaciones o conclusión (1 párrafo)
- Subtítulos descriptivos con <h2> para cada sección
- Párrafos con <p>, bien desarrollados, mínimo 3 frases cada uno
- Tono serio, riguroso y divulgativo
- No menciones que es una traducción ni que el artículo es automático
- No inventes datos, cifras ni nombres que no aparezcan en la noticia original
- Devuelve SOLO el HTML del artículo: etiquetas <h2>, <h3>, <p> únicamente
- Sin <html>, <head>, <body>, <div>, ni ninguna otra etiqueta

NOTICIA ORIGINAL EN INGLÉS:
Título: {titulo}
Contenido: {resumen}

ESCRIBE AHORA EL ARTÍCULO COMPLETO EN ESPAÑOL DE ESPAÑA:"""

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model":  MODELO,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature":  0.7,
                    "num_predict":  2048,
                    "top_p":        0.9,
                    "repeat_penalty": 1.1,
                }
            },
            timeout=300,
        )
        datos = resp.json()
        articulo = datos.get("response", "").strip()
        # Limpia posibles bloques de código markdown
        articulo = re.sub(r"```html?", "", articulo)
        articulo = re.sub(r"```", "", articulo)
        return articulo.strip()
    except Exception as e:
        print(f"[Error] Fallo al redactar con Ollama: {e}")
        return f"<p>{resumen}</p>"

def publicar_en_blogger(titulo, contenido, etiquetas, creds):
    servicio = build("blogger", "v3", credentials=creds)
    entrada = {
        "title":   titulo,
        "content": contenido,
        "labels":  etiquetas,
    }
    resultado = servicio.posts().insert(blogId=BLOG_ID, body=entrada, isDraft=False).execute()
    print(f"[OK] Publicado: {resultado.get('url')}")
    return resultado

def main():
    hora_actual = datetime.now().hour
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando SudoFeed Blogger...")

    if hora_actual not in HORARIO:
        print(f"[Info] Hora {hora_actual}:00 no programada. Saliendo.")
        return

    categoria_key = HORARIO[hora_actual]
    categoria     = CATEGORIAS[categoria_key]
    print(f"[Info] Categoria: {categoria_key}")

    historial = cargar_historial()
    noticias  = obtener_noticias(categoria["feeds"])

    if not noticias:
        print("[Error] No se obtuvieron noticias.")
        return

    noticia = elegir_noticia(noticias, historial)
    if not noticia:
        print("[Error] No hay noticias disponibles.")
        return

    print(f"[Info] Seleccionada: {noticia['titulo'][:60]}...")
    print("[Info] Traduciendo titulo...")

    titulo_es = traducir_titulo(noticia["titulo"])
    print(f"[Info] Titulo ES: {titulo_es[:60]}...")
    print(f"[Info] Redactando articulo con {MODELO}...")

    articulo_html = redactar_articulo(
        noticia["titulo"],
        noticia["resumen"],
        categoria["label"]
    )

    print(f"[Info] Articulo redactado ({len(articulo_html)} chars)")

    try:
        creds = obtener_credenciales()
        publicar_en_blogger(titulo_es, articulo_html, categoria["etiquetas"], creds)
        guardar_historial(historial, noticia["link"])
    except Exception as e:
        print(f"[Error] No se pudo publicar: {e}")

if __name__ == "__main__":
    main()
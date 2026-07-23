import feedparser, requests, re, json, os
from datetime import datetime, date
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BLOG_ID           = "8727828863929929226"
TOKEN_FICHERO     = "/opt/sudofeed-blogger/token.json"
HISTORIAL_FICHERO = "/opt/sudofeed-blogger/historial.json"
OLLAMA_URL        = "http://localhost:11434/api/generate"
MODELO            = "qwen2.5:7b"

CATEGORIAS = {
    "noticias_it": {
        "label": "Noticias IT",
        "etiquetas": ["Noticias IT", "Tecnologia", "SudoFeed"],
        "feeds": [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://www.darkreading.com/rss.xml",
        ]
    },
    "ciberseguridad": {
        "label": "Ciberseguridad",
        "etiquetas": ["Ciberseguridad", "InfoSec", "Seguridad", "SudoFeed"],
        "feeds": [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://krebsonsecurity.com/feed/",
            "https://www.welivesecurity.com/en/rss/feed/",
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
            "https://itsfoss.com/feed/",
        ]
    },
    "software": {
        "label": "Software",
        "etiquetas": ["Software", "OpenSource", "SudoFeed"],
        "feeds": [
            "https://itsfoss.com/feed/",
            "https://www.omglinux.com/feed/",
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
    0:  "linux",
    1:  "ciberseguridad",
    2:  "vulnerabilidades",
    3:  "software",
    4:  "ia",
    5:  "noticias_it",
    6:  "hacking_tools",
    7:  "linux",
    8:  "noticias_it",
    9:  "ciberseguridad",
    10: "vulnerabilidades",
    11: "software",
    12: "linux",
    13: "ia",
    14: "hacking_tools",
    15: "noticias_it",
    16: "ciberseguridad",
    17: "vulnerabilidades",
    18: "software",
    19: "linux",
    20: "ia",
    21: "hacking_tools",
    22: "noticias_it",
    23: "ciberseguridad",
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

def obtener_contenido_completo(url):
    """Obtiene el texto completo del artículo original para dar más contexto al LLM."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        # Elimina scripts, estilos y nav
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            tag.decompose()
        # Busca el contenido principal
        for selector in ["article", "main", ".post-content", ".entry-content", ".article-body", ".content"]:
            bloque = soup.select_one(selector)
            if bloque:
                texto = bloque.get_text(separator=" ", strip=True)
                texto = re.sub(r"\s+", " ", texto).strip()
                if len(texto) > 300:
                    return texto[:4000]
        # Fallback: todo el body
        texto = soup.get_text(separator=" ", strip=True)
        return re.sub(r"\s+", " ", texto).strip()[:4000]
    except Exception as e:
        print(f"[Aviso] No se pudo obtener contenido completo: {e}")
        return ""

def obtener_noticias(feeds):
    noticias = []
    for url in feeds:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
            for entry in feed.entries[:8]:
                raw = entry.get("summary", entry.get("description", ""))
                resumen = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)).strip()
                noticias.append({
                    "titulo": entry.get("title", "").strip(),
                    "link":   entry.get("link", ""),
                    "resumen": resumen[:2000],
                    "fuente": feed.feed.get("title", "Desconocida"),
                    "fuente_url": feed.feed.get("link", ""),
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

def redactar_articulo(titulo, resumen, contenido_completo, categoria_label):
    # Usa el contenido completo si está disponible, si no el resumen RSS
    contexto = contenido_completo if len(contenido_completo) > len(resumen) else resumen

    prompt = f"""Eres el redactor jefe de tecnología de un medio nacional español de referencia.
Tu misión es transformar la siguiente noticia en inglés en un artículo periodístico extenso, riguroso y completamente en español de España.

NORMAS DE IDIOMA Y ESTILO — OBLIGATORIAS:
- Todo el texto en español de España. Cero anglicismos.
- Vocabulario obligatorio: ordenador, contraseña, fichero, parche, cortafuegos, vulnerabilidad, red, servidor, dispositivo, móvil, navegador, pestaña, pinchar.
- Prohibido: password, file, patch, computer, hack (usa "ataque"), breach (usa "brecha"), leak (usa "filtración").
- Sin emojis. Sin exclamaciones. Sin muletillas de IA ("en el complejo mundo de...", "es importante destacar que...").
- Tono: riguroso, directo, informativo. Como El País Tecnología o Hispasec.

ESTRUCTURA OBLIGATORIA — USA EXACTAMENTE ESTAS ETIQUETAS HTML:
<p>Párrafo de introducción: qué ha ocurrido, quién se ve afectado y por qué es relevante ahora. Mínimo 4 frases.</p>
<p>Segundo párrafo introductorio: contexto inmediato del problema. Mínimo 4 frases.</p>
<h2>Análisis técnico</h2>
<p>Explica el funcionamiento técnico del problema o tecnología. Mínimo 4 frases.</p>
<p>Continúa el análisis técnico con más detalles. Mínimo 4 frases.</p>
<p>Tercer párrafo técnico si hay datos suficientes. Mínimo 3 frases.</p>
<h2>Contexto y antecedentes</h2>
<p>Sitúa esta noticia en el contexto del sector tecnológico o de la ciberseguridad. Mínimo 4 frases.</p>
<p>Amplía el contexto con tendencias o casos relacionados si los datos lo permiten. Mínimo 3 frases.</p>
<h2>Impacto y afectados</h2>
<p>Quién se ve afectado y cómo. Consecuencias reales para empresas o usuarios. Mínimo 4 frases.</p>
<p>Escala del problema y magnitud del impacto. Mínimo 3 frases.</p>
<h2>Medidas de mitigación y recomendaciones</h2>
<p>Pasos concretos que deben seguir los afectados. Mínimo 4 frases.</p>
<h2>Conclusión</h2>
<p>Valoración final sobre las implicaciones a medio y largo plazo. Cierre sólido. Mínimo 4 frases.</p>

REGLAS DE FORMATO — CRÍTICAS:
- Longitud mínima: 900 palabras.
- Cada párrafo <p> mínimo 4 frases completas y bien desarrolladas.
- SOLO etiquetas <h2>, <p>, <ul>, <li>. Prohibido <h1>, <div>, <html>, <body>.
- No escribas frases introductorias como "Aquí tienes el artículo" o "A continuación".
- Empieza directamente con el primer <p>.

NOTICIA ORIGINAL EN INGLÉS:
Título: {titulo}
Contenido: {contexto}

ESCRIBE EL ARTÍCULO AHORA EN ESPAÑOL DE ESPAÑA:"""

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model":  MODELO,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature":    0.6,
                    "num_predict":    3500,
                    "num_ctx":        6144,
                    "top_p":          0.9,
                    "repeat_penalty": 1.2,
                }
            },
            timeout=900,
        )
        datos = resp.json()
        articulo = datos.get("response", "").strip()
        articulo = re.sub(r"```html?", "", articulo)
        articulo = re.sub(r"```", "", articulo)
        return articulo.strip()
    except Exception as e:
        print(f"[Error] Fallo al redactar con Ollama: {e}")
        return f"<p>{resumen}</p>"

def añadir_fuente(articulo_html, noticia):
    """Añade el bloque de fuente al final del artículo."""
    fuente_html = f"""
<hr/>
<p style="font-size:0.85em;color:#666;">
  <strong>Fuente original:</strong>
  <a href="{noticia["link"]}" target="_blank" rel="noopener">{noticia["fuente"]}</a>
</p>"""
    return articulo_html + fuente_html

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
    print("[Info] Obteniendo contenido completo del articulo...")
    contenido_completo = obtener_contenido_completo(noticia["link"])
    print(f"[Info] Contenido obtenido: {len(contenido_completo)} chars")

    print("[Info] Traduciendo titulo...")
    titulo_es = traducir_titulo(noticia["titulo"])
    print(f"[Info] Titulo ES: {titulo_es[:60]}...")
    print(f"[Info] Redactando articulo con {MODELO}...")

    articulo_html = redactar_articulo(
        noticia["titulo"],
        noticia["resumen"],
        contenido_completo,
        categoria["label"]
    )

    articulo_html = añadir_fuente(articulo_html, noticia)
    print(f"[Info] Articulo redactado ({len(articulo_html)} chars)")

    try:
        creds = obtener_credenciales()
        publicar_en_blogger(titulo_es, articulo_html, categoria["etiquetas"], creds)
        guardar_historial(historial, noticia["link"])
    except Exception as e:
        print(f"[Error] No se pudo publicar: {e}")

if __name__ == "__main__":
    main()
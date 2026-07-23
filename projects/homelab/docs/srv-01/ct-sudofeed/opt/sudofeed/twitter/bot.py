import feedparser, requests, tweepy, random, re, json, os
from datetime import datetime, date

API_KEY             = "SlYgDml6aNKEdRTfnEeMKKIiJ"
API_SECRET          = "cHVPfDfQcefBmX5Mm2ebEVyGbkRTD0fVFDq48H9kkbC3xhxrMa"
ACCESS_TOKEN        = "2030995744706953216-9hX1TDet169XV4cxZJQdhu41wCZql4"
ACCESS_TOKEN_SECRET = "aolqDzU8gjDsRBaS41RZxBjQbY9L1wam7rRrauPUHdXaB"

HISTORIAL_FICHERO = "/opt/sudofeed/historial_tw.json"

CATEGORIAS = {
    "noticias_it": {
        "emoji": "📰",
        "hashtags": "#NoticiasIT #Tecnologia #SudoFeed",
        "feeds": [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://www.bleepingcomputer.com/feed/",
        ]
    },
    "ciberseguridad": {
        "emoji": "🔐",
        "hashtags": "#Ciberseguridad #InfoSec #SudoFeed",
        "feeds": [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://krebsonsecurity.com/feed/",
            "https://www.bleepingcomputer.com/feed/",
        ]
    },
    "vulnerabilidades": {
        "emoji": "🚨",
        "hashtags": "#Vulnerabilidades #CVE #SudoFeed",
        "feeds": [
            "https://www.darkreading.com/rss.xml",
            "https://isc.sans.edu/rssfeed_full.xml",
            "https://www.welivesecurity.com/en/rss/feed/",
        ]
    },
    "linux": {
        "emoji": "🐧",
        "hashtags": "#Linux #SysAdmin #SudoFeed",
        "feeds": [
            "https://www.omglinux.com/feed/",
            "https://linuxhandbook.com/feed/",
            "https://itsfoss.com/feed/",
        ]
    },
    "software": {
        "emoji": "💾",
        "hashtags": "#Software #OpenSource #SudoFeed",
        "feeds": [
            "https://www.bleepingcomputer.com/feed/",
            "https://linuxhandbook.com/feed/",
        ]
    },
    "ia": {
        "emoji": "🤖",
        "hashtags": "#IA #AI #MachineLearning #SudoFeed",
        "feeds": [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://www.darkreading.com/rss.xml",
        ]
    },
    "hacking_tools": {
        "emoji": "🛠️",
        "hashtags": "#Pentesting #HackingTools #SudoFeed",
        "feeds": [
            "https://www.welivesecurity.com/en/rss/feed/",
            "https://isc.sans.edu/rssfeed_full.xml",
        ]
    },
}

HORARIO = {
#    10: "noticias_it",
#    11: "ciberseguridad",
#    12: "vulnerabilidades",
#    13: "linux",
#    14: "software",
#    19: "ia",
#    20: "hacking_tools",
#    21: "noticias_it",
#    22: "ciberseguridad",
#    23: "vulnerabilidades",
    10: "noticias_it",
    12: "ciberseguridad",
    14: "vulnerabilidades",
    19: "ia",
    21: "hacking_tools",

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
                    "resumen": resumen[:1000],
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

def traducir(texto, intentos=3):
    if not texto or not texto.strip():
        return texto
    fragmentos = [texto[i:i+450] for i in range(0, len(texto), 450)]
    resultado = []
    for frag in fragmentos:
        for _ in range(intentos):
            try:
                resp = requests.get(
                    "https://api.mymemory.translated.net/get",
                    params={"q": frag, "langpair": "en|es"},
                    timeout=10,
                )
                datos = resp.json()
                if datos.get("responseStatus") == 200:
                    resultado.append(datos["responseData"]["translatedText"])
                    break
            except Exception as e:
                print(f"[Aviso] Error traduccion: {e}")
        else:
            resultado.append(frag)
    return " ".join(resultado)

def resumir(texto, max_frases=2):
    frases = re.split(r"(?<=[.!?])\s+", texto)
    sel = []
    for f in frases:
        f = f.strip()
        if len(f) > 40 and "http" not in f and len(sel) < max_frases:
            sel.append(f)
    return " ".join(sel) if sel else texto[:200]

def formatear_tweet(titulo_es, resumen_es, emoji, hashtags):
    cuerpo = f"{emoji} {titulo_es}\n\n{resumen_es}\n\n{hashtags}"
    if len(cuerpo) > 280:
        espacio = 280 - len(f"{emoji} {titulo_es}\n\n...\n\n{hashtags}") - 3
        resumen_corto = resumen_es[:max(0, espacio)] + "..."
        cuerpo = f"{emoji} {titulo_es}\n\n{resumen_corto}\n\n{hashtags}"
    if len(cuerpo) > 280:
        espacio = 280 - len(f"{emoji} ...\n\n{hashtags}") - 3
        titulo_corto = titulo_es[:max(0, espacio)] + "..."
        cuerpo = f"{emoji} {titulo_corto}\n\n{hashtags}"
    return cuerpo

def publicar_tweet(texto):
    cliente = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET,
    )
    cliente.create_tweet(text=texto)
    print(f"[OK] Tweet publicado a las {datetime.now().strftime('%H:%M:%S')}")

def main():
    hora_actual = datetime.now().hour
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando SudoFeed Twitter Bot...")

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

    titulo_es  = traducir(noticia["titulo"])
    resumen_es = traducir(resumir(noticia["resumen"]))

    print(f"[Info] Traducido: {titulo_es[:60]}...")

    tweet = formatear_tweet(titulo_es, resumen_es, categoria["emoji"], categoria["hashtags"])
    print(f"[Info] Tweet ({len(tweet)} chars):\n{tweet}\n")

    try:
        publicar_tweet(tweet)
        guardar_historial(historial, noticia["link"])
    except Exception as e:
        print(f"[Error] No se pudo publicar: {e}")

if __name__ == "__main__":
    main()
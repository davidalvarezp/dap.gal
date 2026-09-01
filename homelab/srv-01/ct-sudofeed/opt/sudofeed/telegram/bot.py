import feedparser, requests, random, re, json, os
from datetime import datetime, date

BOT_TOKEN = "8666353649:AAHN7_55QhpIlgLkpiMp1y3PRwtmNjETs94"
CHAT_ID   = "-1003953134559"

HISTORIAL_FICHERO = "/opt/sudofeed/historial_tg.json"

CATEGORIAS = {
    "noticias_it": {
        "emoji": "📰",
        "titulo": "Noticias IT",
        "hashtags": "#NoticiasIT #Tecnologia #SudoFeed",
        "feeds": [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://www.bleepingcomputer.com/feed/",
        ]
    },
    "ciberseguridad": {
        "emoji": "🔐",
        "titulo": "Ciberseguridad",
        "hashtags": "#Ciberseguridad #InfoSec #SudoFeed",
        "feeds": [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://krebsonsecurity.com/feed/",
            "https://www.bleepingcomputer.com/feed/",
        ]
    },
    "vulnerabilidades": {
        "emoji": "🚨",
        "titulo": "Vulnerabilidades",
        "hashtags": "#Vulnerabilidades #CVE #Exploit #SudoFeed",
        "feeds": [
            "https://www.darkreading.com/rss.xml",
            "https://isc.sans.edu/rssfeed_full.xml",
            "https://www.welivesecurity.com/en/rss/feed/",
        ]
    },
    "linux": {
        "emoji": "🐧",
        "titulo": "Linux Tips",
        "hashtags": "#Linux #SysAdmin #OpenSource #SudoFeed",
        "feeds": [
            "https://www.omglinux.com/feed/",
            "https://linuxhandbook.com/feed/",
            "https://itsfoss.com/feed/",
        ]
    },
    "software": {
        "emoji": "💾",
        "titulo": "Software",
        "hashtags": "#Software #OpenSource #Dev #SudoFeed",
        "feeds": [
            "https://www.bleepingcomputer.com/feed/",
            "https://linuxhandbook.com/feed/",
        ]
    },
    "ia": {
        "emoji": "🤖",
        "titulo": "IA & Tech",
        "hashtags": "#IA #AI #MachineLearning #SudoFeed",
        "feeds": [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://www.darkreading.com/rss.xml",
        ]
    },
    "hacking_tools": {
        "emoji": "🛠️",
        "titulo": "Herramientas Hacking",
        "hashtags": "#Pentesting #HackingTools #CTF #SudoFeed",
        "feeds": [
            "https://www.welivesecurity.com/en/rss/feed/",
            "https://isc.sans.edu/rssfeed_full.xml",
        ]
    },
}

HORARIO = {
    8:  "noticias_it",
    10: "ciberseguridad",
    12: "vulnerabilidades",
    14: "linux",
    16: "software",
    18: "ia",
    20: "hacking_tools",
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

def resumir(texto, max_frases=3):
    frases = re.split(r"(?<=[.!?])\s+", texto)
    sel = []
    for f in frases:
        f = f.strip()
        if len(f) > 40 and "http" not in f and len(sel) < max_frases:
            sel.append(f)
    return " ".join(sel) if sel else texto[:400]

def escapar_md(texto):
    for c in r"\_*[]()~`>#+-=|{}.!":
        texto = texto.replace(c, f"\\{c}")
    return texto

def formatear_mensaje(cat, titulo_es, resumen_es, link, fuente):
    hora  = datetime.now().strftime("%H:%M")
    return (
        f"{cat['emoji']} *{escapar_md(cat['titulo'])}* \- {escapar_md(hora)}h\n\n"
        f"📰 *{escapar_md(titulo_es)}*\n\n"
        f"📝 {escapar_md(resumen_es)}\n\n"
        f"🔗 [Leer noticia completa]({link})\n\n"
        f"📡 _{escapar_md(fuente)}_\n\n"
        f"{escapar_md(cat['hashtags'])}"
    )

def publicar(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":                  CHAT_ID,
        "text":                     mensaje,
        "parse_mode":               "MarkdownV2",
        "disable_web_page_preview": False,
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    print(f"[OK] Publicado a las {datetime.now().strftime('%H:%M:%S')}")

def main():
    hora_actual = datetime.now().hour
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando SudoFeed Telegram...")

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

    mensaje = formatear_mensaje(categoria, titulo_es, resumen_es, noticia["link"], noticia["fuente"])

    try:
        publicar(mensaje)
        guardar_historial(historial, noticia["link"])
    except Exception as e:
        print(f"[Error] No se pudo publicar: {e}")

if __name__ == "__main__":
    main()
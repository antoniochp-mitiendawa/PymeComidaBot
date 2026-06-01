#!/usr/bin/env python3
# ============================================================
#  MI TIENDA WA — Bot Principal v2
#  Motor de atención al cliente para restaurantes pequeños
#  Termux + WuzAPI — Sin dependencias externas de IA
# ============================================================

import os, json, sqlite3, threading, time, re, requests, random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

# ── Rutas ────────────────────────────────────────────────────
BASEDIR   = os.path.expanduser("~/mitiendawa")
DBPATH    = os.path.join(BASEDIR, "data", "tienda.db")
AUDIODIR  = os.path.join(BASEDIR, "audios")
TOKENPATH = os.path.join(BASEDIR, "data", "token.txt")
BPATH     = os.path.join(BASEDIR, "data", "telefono_b.txt")
LOGPATH   = os.path.join(BASEDIR, "bot.log")
WUZAPI    = "http://localhost:8080"

# ── Leer archivos de configuración ──────────────────────────
def leer_archivo(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except:
        return ""

# TOKEN y TELEFONO_B se leen al inicio y se recargan en __main__
TOKEN      = leer_archivo(TOKENPATH)
TELEFONO_B = leer_archivo(BPATH)

app = Flask(__name__)

# ── Logging ──────────────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{ts}] {msg}"
    print(linea)
    try:
        with open(LOGPATH, "a") as f:
            f.write(linea + "\n")
    except:
        pass

# ════════════════════════════════════════════════════════════
#  EMOJIS Y VARIEDAD DE RESPUESTAS
# ════════════════════════════════════════════════════════════
EMOJIS = {
    "saludo":    ["✨","🌤️","🌅","☕","🤝","👋","🎈","🍀","☀️","🌈","🙌","⭐","🌻","🌸","💫","🌟"],
    "menu":      ["📖","📗","📘","📙","📓","📒","📑","📚","🎓","🧠","🚀","💎","💡","📢","🔔"],
    "horario":   ["🕐","🕑","🕒","🕓","🕔","🕕","🕖","🕗","🕘","🕙","🕚","🕛","⏰","⌛","⏲️","⏱️"],
    "ubicacion": ["📍","🗺️","🧭","🏠","🏪","🏢","📌","🔍","🚩","🌐","🏘️"],
    "precio":    ["💰","🏷️","💵","💳","🎁","💎","💸","🪙","💹","🛒","💲","🎯","🔥"],
    "comida":    ["🍳","🥞","🥓","🍔","🍟","🍕","🌮","🥗","🍜","🍲","🥘","🍰","🍨","🍦","🌯","🥖","🍚"],
    "aprobacion":["✅","👍","👌","🔥","💪","😎","👏","🙌","✨","💯"],
    "despedida": ["👋","🙏","😊","✨","🌟","💫","🎉","🍽️","💚","⭐","🌈","🌸"]
}

RESPUESTAS = {
    "saludo_con_menu": [
        "{} ¡{}! Soy *{}* de *{}*. Ahora estamos en *{}* hasta las {}. ¿Te comparto el menú? 🍽️",
        "{} ¡Qué gusto saludarte! {} Aquí *{}* de *{}*. En este momento servimos *{}* (hasta {}). ¿Te interesa?",
        "{} ¡Bienvenido a *{}*! {} Soy *{}*. Estamos en horario de *{}* hasta las {}. ¿Quieres ver qué hay?",
        "{} ¡Hola! {} Te habla *{}* de *{}*. Ahora es hora de *{}* (cierra a las {}). ¿Te mando la info?",
        "{} ¡Gracias por escribir! {} Soy *{}*. En *{}* estamos con *{}* hasta las {}. ¿Te gustaría saber qué tenemos?"
    ],
    "saludo_sin_menu": [
        "{} ¡{}! {} Soy *{}* de *{}*. Ahora no tenemos servicio activo. Nuestro horario es *{}*. ¡Te esperamos!",
        "{} ¡Qué gusto verte! {} Aquí *{}* de *{}*. Por ahora no estamos sirviendo (horario: {}). ¡Te esperamos!",
        "{} ¡Hola! {} Te atiende *{}* de *{}*. Cerramos por ahora, abrimos en *{}*. ¡Gracias por escribir! 🙏"
    ],
    "menu_con_audio": [
        "{} ¡Claro! {} Te mando la información de nuestros *{}*:",
        "{} Con mucho gusto {} Te comparto el detalle de los *{}*:",
        "{} ¡Ahí te va! 🎙️ Escucha el menú de *{}* {}:",
        "{} Por supuesto {} Aquí tienes la información de *{}*:"
    ],
    "menu_sin_audio": [
        "{} Por el momento no tengo el menú disponible {} ¿Quieres que te llame alguien? 🤝",
        "{} ¡Ups! {} Aún no cargo el menú de *{}*. ¿Te parece si te contacta alguien? 📞",
        "{} Lo siento {} El menú de *{}* no está listo. ¿Prefieres que te llamemos? 🙏"
    ],
    "precio_con_audio": [
        "{} ¡Claro! {} En este audio te decimos los precios de *{}*: 💰",
        "{} Por supuesto {} Escucha los precios de nuestros *{}*: 🏷️",
        "{} ¡Ahí te va la info! {} Te comparto los precios de *{}*: 💸"
    ],
    "precio_sin_audio": [
        "{} Para darte información de precios {} ¿Quieres que te llamemos? 📞",
        "{} Lo siento {} No tengo los precios a la mano. ¿Te parece si alguien te contacta? 🤝"
    ],
    "ubicacion": [
        "{} *{}* se encuentra en:\n📍 {}\n\n📞 Teléfono: {}\n\n{} ¡Te esperamos! 🙏",
        "{} Estamos en:\n🏠 {}\n📞 {}\n\n{} ¡Llegar es fácil! 🚩",
        "{} Aquí nuestra dirección:\n📍 *{}*\n📞 {}\n\n{} ¿Necesitas indicaciones? 🧭"
    ],
    "horario": [
        "{} Te comparto nuestro horario {}:\n\n📅 *{}*\n🕐 *{}*\n\n{} Por categoría:\n{}\n{} ¡Te esperamos!",
        "{} Nuestros horarios {}:\n• Días: *{}*\n• General: *{}*\n\n{} Por comida:\n{}\n{} ¿Alguna duda? ✨"
    ],
    "pedido_pregunta": [
        "{} ¡Perfecto! {} ¿Quieres que te llamemos para coordinar tu pedido o nos visitas? 📞",
        "{} Con gusto te ayudamos {} ¿Te parece si alguien te llama para tu pedido? 🤝",
        "{} ¡Excelente! {} ¿Prefieres que te llamemos o vienes directo al local? 🏠"
    ],
    "cliente_si": [
        "{} ¡Perfecto! {} En unos momentos alguien se comunica contigo. ¡Gracias por preferirnos! 🙏",
        "{} ¡Genial! {} Ya avisé al equipo. Te contactarán en breve. 📞",
        "{} ¡Excelente! {} Gracias por tu interés. Pronto te llamamos. ✨"
    ],
    "cliente_no": [
        "{} Sin problema {} Gracias por contactarnos. ¡Que tengas excelente día! 🌟",
        "{} Entendido {} Estamos aquí cuando gustes. ¡Hasta pronto! 👋",
        "{} Gracias de todas formas {} Recuerda que siempre serás bienvenido. 🙏"
    ],
    "cliente_visita": [
        "{} ¡Perfecto! {} Te esperamos en *{}*.\n📍 {}\n\n¡Buen provecho! 🍽️",
        "{} ¡Qué gusto! {} Nos vemos en *{}*.\n📍 {}\n\n¡Te esperamos con gusto! 🙌"
    ],
    "despedida": [
        "{} ¡Gracias a ti! {} Fue un placer atenderte. ¡Hasta pronto! 👋",
        "{} ¡Qué gusto ayudarte! {} Te esperamos cuando gustes. 🌈",
        "{} ¡Nos vemos! {} Recuerda que *{}* siempre está para ti. 🙌"
    ],
    "desconocido": [
        "{} Gracias por contactar a *{}*, soy *{}*. No tengo esa información {} Voy a avisar para que alguien te contacte. 🙏",
        "{} ¡Hola! {} Soy *{}* de *{}*. No entendí bien tu mensaje. ¿Te parece si alguien del equipo te escribe? 📞"
    ],
    "cerrado": [
        "{} Hoy estamos cerrados ({}) {}\n\nNuestro horario habitual es *{}* ({}). ¡Te esperamos pronto! 🙏",
        "{} Lo sentimos {} Hoy descansamos ({}).\n\nTe atendemos en horario *{}* ({}). 🌟"
    ],
    "no_dia_laboral": [
        "{} Hoy descansamos {} Te atendemos *{}* en horario *{}*. ¡Gracias por escribir! 🙏",
        "{} Gracias por contactarnos {} Nuestros días de atención son *{}*. ¡Estaremos encantados de atenderte! 🌈"
    ],
    "categoria_inactiva_con_proxima": [
        "{} En este momento no tenemos servicio activo {} Pero a las *{}* comenzamos con *{}*. ¡Te esperamos! 🙏",
        "{} Cerramos por ahora {} Nuestra próxima categoría es *{}* a las *{}*. ¡Te esperamos! ✨",
        "{} Lo siento {} Ahora no estamos sirviendo. Abrimos de nuevo en *{}* a las *{}*. 🌟"
    ]
}

def get_emoji(categoria):
    return random.choice(EMOJIS.get(categoria, ["✨"]))

def get_respuesta(categoria):
    lista = RESPUESTAS.get(categoria, ["{} {}"])
    return random.choice(lista)

# ════════════════════════════════════════════════════════════
#  BASE DE DATOS
# ════════════════════════════════════════════════════════════
def init_db():
    con = sqlite3.connect(DBPATH)
    c = con.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS config (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            hora_inicio TEXT,
            hora_fin TEXT,
            audio_path TEXT,
            activa INTEGER DEFAULT 1
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS interesados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            fecha TEXT,
            hora TEXT,
            atendido INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS onboarding (
            numero TEXT PRIMARY KEY,
            paso TEXT,
            categoria_actual TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cierres (
            fecha TEXT PRIMARY KEY,
            motivo TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            numero TEXT PRIMARY KEY,
            nombre TEXT,
            primera_vez INTEGER DEFAULT 1,
            fecha_registro TEXT
        )
    """)
    con.commit()
    con.close()

def get_config(clave, default=""):
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("SELECT valor FROM config WHERE clave=?", (clave,))
    row = c.fetchone()
    con.close()
    return row[0] if row else default

def set_config(clave, valor):
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("INSERT OR REPLACE INTO config(clave,valor) VALUES(?,?)", (clave, valor))
    con.commit()
    con.close()

def get_onboarding(numero):
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("SELECT paso, categoria_actual FROM onboarding WHERE numero=?", (numero,))
    row = c.fetchone()
    con.close()
    if row:
        return {"paso": row[0], "categoria_actual": row[1] or ""}
    return None

def set_onboarding(numero, paso, categoria_actual=""):
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("INSERT OR REPLACE INTO onboarding(numero,paso,categoria_actual) VALUES(?,?,?)",
              (numero, paso, categoria_actual))
    con.commit()
    con.close()

def del_onboarding(numero):
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("DELETE FROM onboarding WHERE numero=?", (numero,))
    con.commit()
    con.close()

def get_categorias():
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("SELECT nombre, hora_inicio, hora_fin, audio_path FROM categorias WHERE activa=1")
    rows = c.fetchall()
    con.close()
    return [{"nombre": r[0], "inicio": r[1], "fin": r[2], "audio": r[3]} for r in rows]

def guardar_categoria(nombre, inicio, fin, audio_path):
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("""
        INSERT INTO categorias(nombre,hora_inicio,hora_fin,audio_path,activa)
        VALUES(?,?,?,?,1)
        ON CONFLICT(nombre) DO UPDATE SET
            hora_inicio=excluded.hora_inicio,
            hora_fin=excluded.hora_fin,
            audio_path=excluded.audio_path,
            activa=1
    """, (nombre, inicio, fin, audio_path))
    con.commit()
    con.close()

def eliminar_categoria(nombre):
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("UPDATE categorias SET activa=0 WHERE nombre=?", (nombre,))
    con.commit()
    con.close()

def registrar_interesado(numero):
    now = datetime.now()
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("INSERT INTO interesados(numero,fecha,hora) VALUES(?,?,?)",
              (numero, now.strftime("%Y-%m-%d"), now.strftime("%H:%M")))
    con.commit()
    con.close()
    tb = leer_archivo(BPATH)
    if tb:
        enviar_texto(tb,
            f"📞 *CLIENTE INTERESADO EN PEDIDO*\n\n"
            f"El cliente *{numero.replace('@s.whatsapp.net','')}* "
            f"solicita que lo llamen.\n\nHora: {now.strftime('%H:%M')}"
        )

def es_cierre_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("SELECT motivo FROM cierres WHERE fecha=?", (hoy,))
    row = c.fetchone()
    con.close()
    return row[0] if row else None

def guardar_cierre(fecha, motivo="Dia de descanso"):
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("INSERT OR REPLACE INTO cierres(fecha,motivo) VALUES(?,?)", (fecha, motivo))
    con.commit()
    con.close()

def get_cliente(numero):
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("SELECT nombre, primera_vez FROM clientes WHERE numero=?", (numero,))
    row = c.fetchone()
    con.close()
    if row:
        return {"nombre": row[0], "primera_vez": row[1]}
    return None

def registrar_cliente_nuevo(numero):
    """Registra al cliente con primera_vez=1 para capturar su nombre"""
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("INSERT OR IGNORE INTO clientes(numero,nombre,primera_vez,fecha_registro) VALUES(?,?,1,?)",
              (numero, "", datetime.now().strftime("%Y-%m-%d")))
    con.commit()
    con.close()

def guardar_nombre_cliente(numero, nombre):
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("INSERT OR REPLACE INTO clientes(numero,nombre,primera_vez,fecha_registro) VALUES(?,?,0,?)",
              (numero, nombre, datetime.now().strftime("%Y-%m-%d")))
    con.commit()
    con.close()

# ════════════════════════════════════════════════════════════
#  ENVÍO DE MENSAJES VÍA WUZAPI
# ════════════════════════════════════════════════════════════
def get_headers():
    tok = leer_archivo(TOKENPATH)
    return {"Token": tok, "Content-Type": "application/json"}

def enviar_texto(numero, texto):
    try:
        phone = numero.replace("@s.whatsapp.net", "").replace("@g.us", "")
        r = requests.post(f"{WUZAPI}/chat/send/text",
                          headers=get_headers(),
                          json={"Phone": phone, "Body": texto},
                          timeout=10)
        log(f"ENVIO → {phone}: {texto[:60]}")
        return r.status_code == 200
    except Exception as e:
        log(f"ERROR enviar texto: {e}")
        return False

def enviar_audio(numero, audio_path):
    try:
        import base64
        phone = numero.replace("@s.whatsapp.net", "").replace("@g.us", "")
        with open(audio_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        ext  = os.path.splitext(audio_path)[1].lower()
        mime = "audio/ogg; codecs=opus" if ext in [".ogg", ".opus"] else "audio/mpeg"
        r = requests.post(f"{WUZAPI}/chat/send/audio",
                          headers=get_headers(),
                          json={"Phone": phone, "Audio": data,
                                "FileName": os.path.basename(audio_path)},
                          timeout=20)
        log(f"ENVIO AUDIO → {phone}: {audio_path}")
        return r.status_code == 200
    except Exception as e:
        log(f"ERROR enviar audio: {e}")
        return False

def descargar_audio_wuzapi(msg_id, mime_type="audio/ogg"):
    try:
        r = requests.get(f"{WUZAPI}/chat/downloadmedia/{msg_id}",
                         headers=get_headers(), timeout=15)
        if r.status_code == 200:
            ext  = ".ogg" if "ogg" in mime_type else ".mp3"
            path = os.path.join(AUDIODIR, f"temp_{msg_id}{ext}")
            with open(path, "wb") as f:
                f.write(r.content)
            return path
    except Exception as e:
        log(f"ERROR descarga audio: {e}")
    return None

# ════════════════════════════════════════════════════════════
#  UTILIDADES DE TIEMPO
# ════════════════════════════════════════════════════════════
def hora_actual():
    return datetime.now().strftime("%H:%M")

def hora_a_minutos(h):
    try:
        partes = str(h).replace(".", ":").split(":")
        return int(partes[0]) * 60 + int(partes[1])
    except:
        return 0

def saludo_por_hora():
    h = int(datetime.now().strftime("%H"))
    if 5 <= h < 12:
        return random.choice(["¡Buenos días!", "¡Qué tal tu mañana!", "¡Excelente día!"])
    elif 12 <= h < 19:
        return random.choice(["¡Buenas tardes!", "¡Qué tal esta tarde!", "¡Linda tarde!"])
    else:
        return random.choice(["¡Buenas noches!", "¡Qué tal tu noche!", "¡Gracias por escribir!"])

def categoria_activa_ahora():
    ahora = hora_a_minutos(hora_actual())
    for cat in get_categorias():
        if hora_a_minutos(cat["inicio"]) <= ahora <= hora_a_minutos(cat["fin"]):
            return cat
    return None

def proxima_categoria():
    ahora = hora_a_minutos(hora_actual())
    proxima = None
    for cat in get_categorias():
        ini = hora_a_minutos(cat["inicio"])
        if ini > ahora:
            if proxima is None or ini < hora_a_minutos(proxima["inicio"]):
                proxima = cat
    return proxima

def dia_laboral_hoy():
    dias_config = get_config("dias_trabajo", "lunes a domingo").lower()
    hoy = datetime.now().weekday()  # 0=lunes
    if any(x in dias_config for x in ["lunes a domingo", "todos los dias", "toda la semana", "siete dias"]):
        return True
    if "lunes a viernes" in dias_config and hoy <= 4:
        return True
    if ("lunes a sabado" in dias_config or "lunes a sábado" in dias_config) and hoy <= 5:
        return True
    dias_map = {"lunes":0,"martes":1,"miercoles":2,"miércoles":2,"jueves":3,"viernes":4,"sabado":5,"sábado":5,"domingo":6}
    for nombre, num in dias_map.items():
        if nombre in dias_config and hoy == num:
            return True
    return False

# Helpers de config
def nombre_negocio():    return get_config("nombre_negocio", "nuestro negocio")
def nombre_asistente():  return get_config("nombre_asistente", "el asistente")
def horario_general():   return get_config("horario_general", "nuestro horario habitual")
def dias_trabajo():      return get_config("dias_trabajo", "todos los dias")
def get_direccion():     return get_config("direccion", "")
def get_telefono():      return get_config("telefono_contacto", "")
def get_redes():         return get_config("redes_sociales", "")
def respuesta_si():      return get_config("respuesta_si", "Gracias por tu interes, en breve nos comunicamos contigo.")

# ════════════════════════════════════════════════════════════
#  DETECCIÓN DE INTENCIÓN
# ════════════════════════════════════════════════════════════
INTENCIONES = {
    "saludo": [
        "hola","buenas","buenos dias","buenos días","buen dia","buen día",
        "buenas tardes","buenas noches","que tal","qué tal","hey","hi",
        "quiubo","quiúbo","que onda","qué onda","saludos","alo","aló","oiga","oye"
    ],
    "menu": [
        "menú","menu","que tienen","qué tienen","que hay","qué hay",
        "que tienen hoy","que sirven","que venden","que me recomiendas",
        "carta","platillos","para comer","de comer","desayuno","desayunos",
        "comida","comidas","cena","cenas","almuerzo","que ofrecen","mandame el menu",
        "mandame la carta","tienen desayuno","tienen comida","hay comida","hay desayuno"
    ],
    "ubicacion": [
        "donde estan","dónde estan","donde quedan","dónde quedan",
        "direccion","dirección","como llego","cómo llego",
        "donde se ubican","en que calle","domicilio","donde los ubico","como llegar"
    ],
    "horario": [
        "horario","a que hora abren","a qué hora abren",
        "a que hora cierran","cuando abren","estan abiertos","hasta que hora",
        "que dias trabajan","trabajan hoy","abren hoy","dias de atencion"
    ],
    "pedido": [
        "quiero pedir","hacer un pedido","quiero ordenar",
        "a domicilio","delivery","que me llamen","llamame","llámenme",
        "me hablan","quiero que me llamen","pueden llamarme"
    ],
    "ir_al_lugar": [
        "voy para alla","voy para allá","ahorita voy","ya voy","me voy para alla",
        "voy llegando","voy a ir","llego en","llego mas tarde","paso al rato",
        "voy a pasar","ire","voy a visitarlos"
    ],
    "confirmacion_llamada": [
        "si","sí","si por favor","claro","ok","esta bien","está bien",
        "adelante","por favor","si quiero","sí quiero","orale","órale","andale"
    ],
    "negacion_llamada": [
        "no","no gracias","ahorita no","ya no","no quiero",
        "no necesito","namas","nomás","solo queria saber"
    ],
    "precio": [
        "cuanto cuesta","cuánto cuesta","cuanto vale","precios","que precio",
        "qué precio","cuanto es","cuanto cobran","cuanto sale"
    ],
    "redes": [
        "facebook","instagram","redes sociales","red social","fan page","su instagram","su facebook"
    ],
    "despedida": [
        "gracias","muchas gracias","hasta luego","bye","adios","adiós","provecho","nos vemos"
    ]
}

# Estado por conversación — rastrea si se le preguntó si quiere llamada
ESPERANDO_RESPUESTA_LLAMADA = {}

def detectar_intencion(texto):
    t = texto.lower().strip()
    for intencion, palabras in INTENCIONES.items():
        for p in palabras:
            if p in t:
                return intencion
    return "desconocido"

# ════════════════════════════════════════════════════════════
#  RESPONDER AL CLIENTE
# ════════════════════════════════════════════════════════════
def responder_cliente(sender, texto):
    negocio   = nombre_negocio()
    asistente = nombre_asistente()
    saludo    = saludo_por_hora()
    cliente   = get_cliente(sender)

    # ── Cliente nuevo — registrar y pedir nombre ─────────────
    if not cliente:
        registrar_cliente_nuevo(sender)
        enviar_texto(sender,
            f"{get_emoji('saludo')} ¡Hola! {get_emoji('comida')} Bienvenido a *{negocio}*.\n\n"
            f"Soy *{asistente}*. ¿Me puedes decir tu nombre? 😊"
        )
        return

    # ── Esperando nombre del cliente ─────────────────────────
    if cliente["primera_vez"] == 1:
        nombre = texto.strip()
        if nombre and len(nombre) < 50 and not any(c.isdigit() for c in nombre):
            guardar_nombre_cliente(sender, nombre)
            enviar_texto(sender,
                f"{get_emoji('saludo')} ¡Mucho gusto *{nombre}*! {get_emoji('comida')} "
                f"¿En qué te puedo ayudar? (Desayuno, Comida, Horarios, Ubicación...) 😊"
            )
        else:
            enviar_texto(sender,
                f"{get_emoji('saludo')} No entendí tu nombre. ¿Me lo puedes escribir de nuevo? 🙏"
            )
        return

    # ── Verificar si está esperando respuesta a llamada ─────
    if ESPERANDO_RESPUESTA_LLAMADA.get(sender):
        intencion = detectar_intencion(texto)
        if intencion == "confirmacion_llamada":
            ESPERANDO_RESPUESTA_LLAMADA.pop(sender, None)
            registrar_interesado(sender)
            template = get_respuesta("cliente_si")
            enviar_texto(sender, template.format(get_emoji("aprobacion"), get_emoji("saludo"), respuesta_si()))
            return
        elif intencion == "negacion_llamada":
            ESPERANDO_RESPUESTA_LLAMADA.pop(sender, None)
            template = get_respuesta("cliente_no")
            enviar_texto(sender, template.format(get_emoji("despedida"), get_emoji("saludo")))
            return
        elif intencion == "ir_al_lugar":
            ESPERANDO_RESPUESTA_LLAMADA.pop(sender, None)
            template = get_respuesta("cliente_visita")
            enviar_texto(sender, template.format(get_emoji("aprobacion"), get_emoji("saludo"),
                                                  negocio, get_direccion()))
            return

    # ── Cierre especial hoy ──────────────────────────────────
    cierre = es_cierre_hoy()
    if cierre:
        template = get_respuesta("cerrado")
        enviar_texto(sender, template.format(get_emoji("saludo"), cierre,
                                              get_emoji("horario"), horario_general(), dias_trabajo()))
        return

    # ── No es día laboral ────────────────────────────────────
    if not dia_laboral_hoy():
        template = get_respuesta("no_dia_laboral")
        enviar_texto(sender, template.format(get_emoji("saludo"), get_emoji("horario"),
                                              dias_trabajo(), horario_general()))
        return

    intencion = detectar_intencion(texto)
    cat = categoria_activa_ahora()

    # ── SALUDO ───────────────────────────────────────────────
    if intencion == "saludo":
        if cat:
            template = get_respuesta("saludo_con_menu")
            enviar_texto(sender, template.format(get_emoji("saludo"), saludo, asistente,
                                                  negocio, cat["nombre"].capitalize(), cat["fin"]))
        else:
            prox = proxima_categoria()
            if prox:
                template = get_respuesta("categoria_inactiva_con_proxima")
                enviar_texto(sender, template.format(get_emoji("saludo"), get_emoji("horario"),
                                                      prox["inicio"], prox["nombre"].capitalize()))
            else:
                template = get_respuesta("saludo_sin_menu")
                enviar_texto(sender, template.format(get_emoji("saludo"), saludo,
                                                      get_emoji("horario"), asistente, negocio, horario_general()))
        return

    # ── MENÚ ─────────────────────────────────────────────────
    if intencion == "menu":
        if cat and cat.get("audio") and os.path.exists(cat["audio"]):
            template = get_respuesta("menu_con_audio")
            enviar_texto(sender, template.format(get_emoji("menu"), get_emoji("comida"),
                                                  cat["nombre"].capitalize(), get_emoji("aprobacion")))
            time.sleep(1)
            enviar_audio(sender, cat["audio"])
            time.sleep(1)
            # Invitar a pedir
            template2 = get_respuesta("pedido_pregunta")
            enviar_texto(sender, template2.format(get_emoji("comida"), get_emoji("aprobacion")))
            ESPERANDO_RESPUESTA_LLAMADA[sender] = True
        elif cat:
            template = get_respuesta("menu_sin_audio")
            enviar_texto(sender, template.format(get_emoji("menu"), get_emoji("saludo"),
                                                  cat["nombre"].capitalize()))
        else:
            prox = proxima_categoria()
            if prox:
                template = get_respuesta("categoria_inactiva_con_proxima")
                enviar_texto(sender, template.format(get_emoji("saludo"), get_emoji("horario"),
                                                      prox["inicio"], prox["nombre"].capitalize()))
            else:
                template = get_respuesta("saludo_sin_menu")
                enviar_texto(sender, template.format(get_emoji("saludo"), saludo,
                                                      get_emoji("horario"), asistente, negocio, horario_general()))
        return

    # ── PRECIO ───────────────────────────────────────────────
    if intencion == "precio":
        if cat and cat.get("audio") and os.path.exists(cat["audio"]):
            template = get_respuesta("precio_con_audio")
            enviar_texto(sender, template.format(get_emoji("precio"), get_emoji("comida"),
                                                  cat["nombre"].capitalize()))
            time.sleep(1)
            enviar_audio(sender, cat["audio"])
        else:
            template = get_respuesta("precio_sin_audio")
            enviar_texto(sender, template.format(get_emoji("precio"), get_emoji("saludo")))
        return

    # ── UBICACIÓN ─────────────────────────────────────────────
    if intencion == "ubicacion":
        tel = get_telefono() or "No disponible"
        template = get_respuesta("ubicacion")
        enviar_texto(sender, template.format(get_emoji("ubicacion"), negocio,
                                              get_direccion(), tel, get_emoji("saludo")))
        return

    # ── HORARIO ───────────────────────────────────────────────
    if intencion == "horario":
        cats_text = ""
        for c in get_categorias():
            cats_text += f"• *{c['nombre'].capitalize()}*: {c['inicio']} a {c['fin']}\n"
        template = get_respuesta("horario")
        enviar_texto(sender, template.format(get_emoji("horario"), get_emoji("saludo"),
                                              dias_trabajo(), horario_general(),
                                              get_emoji("menu"), cats_text, get_emoji("aprobacion")))
        return

    # ── PEDIDO ───────────────────────────────────────────────
    if intencion in ["pedido", "ir_al_lugar"]:
        if intencion == "ir_al_lugar":
            template = get_respuesta("cliente_visita")
            enviar_texto(sender, template.format(get_emoji("aprobacion"), get_emoji("saludo"),
                                                  negocio, get_direccion()))
        else:
            template = get_respuesta("pedido_pregunta")
            enviar_texto(sender, template.format(get_emoji("comida"), get_emoji("aprobacion")))
            ESPERANDO_RESPUESTA_LLAMADA[sender] = True
        return

    # ── REDES SOCIALES ────────────────────────────────────────
    if intencion == "redes":
        if get_redes():
            enviar_texto(sender,
                f"{get_emoji('saludo')} ¡Gracias por el interés! {get_emoji('aprobacion')}\n\n"
                f"{get_redes()}\n\n{get_emoji('despedida')} ¡Síguenos y comparte tu experiencia! ⭐"
            )
        else:
            enviar_texto(sender,
                f"{get_emoji('saludo')} Por el momento no tenemos redes sociales activas. "
                f"Puedes contactarnos directamente por aquí. 🙏"
            )
        return

    # ── DESPEDIDA ─────────────────────────────────────────────
    if intencion == "despedida":
        template = get_respuesta("despedida")
        enviar_texto(sender, template.format(get_emoji("despedida"), get_emoji("saludo"), negocio))
        return

    # ── DESCONOCIDO — notificar al dueño ─────────────────────
    template = get_respuesta("desconocido")
    enviar_texto(sender, template.format(get_emoji("saludo"), negocio, asistente, get_emoji("comida")))
    tb = leer_archivo(BPATH)
    if tb:
        enviar_texto(tb,
            f"⚠️ *CONSULTA SIN RESPUESTA*\n"
            f"Cliente *{sender.replace('@s.whatsapp.net','')}* preguntó:\n_{texto}_"
        )

# ════════════════════════════════════════════════════════════
#  ONBOARDING DEL DUEÑO
# ════════════════════════════════════════════════════════════
def procesar_onboarding(numero, texto, audio_path=None):
    estado = get_onboarding(numero)
    if not estado:
        return False

    paso = estado["paso"]
    cat  = estado["categoria_actual"]
    t    = texto.strip()

    if paso == "inicio":
        if "iniciar" in t.lower():
            set_onboarding(numero, "nombre_negocio")
            enviar_texto(numero,
                "¡Perfecto! Vamos a configurar tu negocio. 😊\n\n"
                "*¿Cómo se llama tu negocio o establecimiento?*"
            )
            return True
        return False

    if paso == "nombre_negocio":
        set_config("nombre_negocio", t)
        set_onboarding(numero, "nombre_asistente")
        enviar_texto(numero,
            f"✅ Nombre: *{t}*\n\n"
            f"*¿Con qué nombre se va a presentar tu asistente con los clientes?*\n"
            f"Ejemplo: _Miguel_, _Brenda_, _Asistente de {t}_"
        )
        return True

    if paso == "nombre_asistente":
        set_config("nombre_asistente", t)
        set_onboarding(numero, "direccion")
        enviar_texto(numero,
            f"✅ Asistente: *{t}*\n\n"
            f"*¿Cuál es la dirección de tu negocio?*\n"
            f"(Calle, número, colonia y ciudad)"
        )
        return True

    if paso == "direccion":
        set_config("direccion", t)
        set_onboarding(numero, "horario_general")
        enviar_texto(numero,
            f"✅ Dirección registrada.\n\n"
            f"*¿Cuál es tu horario general de atención?*\n"
            f"Ejemplo: _7 de la mañana a 8 de la noche_"
        )
        return True

    if paso == "horario_general":
        set_config("horario_general", t)
        set_onboarding(numero, "dias_trabajo")
        enviar_texto(numero,
            f"✅ Horario registrado.\n\n"
            f"*¿Qué días trabajas?*\n"
            f"Ejemplo: _lunes a viernes_, _lunes a sábado_, _todos los días_"
        )
        return True

    if paso == "dias_trabajo":
        set_config("dias_trabajo", t)
        set_onboarding(numero, "telefono_contacto")
        enviar_texto(numero,
            f"✅ Días registrados.\n\n"
            f"*¿Cuál es tu teléfono de contacto?*\n"
            f"(Si no quieres compartirlo responde *NO*)"
        )
        return True

    if paso == "telefono_contacto":
        if t.lower() != "no":
            set_config("telefono_contacto", t)
        set_onboarding(numero, "redes_sociales")
        enviar_texto(numero,
            f"✅ Listo.\n\n"
            f"*¿Tienes redes sociales?*\n"
            f"Ejemplo: _Facebook: Taquería El Paisa / Instagram: @taqueriaelpaisa_\n\n"
            f"Si no tienes, responde *NO*."
        )
        return True

    if paso == "redes_sociales":
        if t.lower() != "no":
            set_config("redes_sociales", t)
        set_onboarding(numero, "categorias_lista")
        enviar_texto(numero,
            f"✅ ¡Ya casi!\n\n"
            f"*¿Cuáles son las categorías de tu menú?*\n"
            f"Escríbelas separadas por coma.\n"
            f"Ejemplo: _desayunos, comidas_ o _desayunos, comidas, cenas_"
        )
        return True

    if paso == "categorias_lista":
        cats = [c.strip().lower() for c in t.replace(";", ",").split(",") if c.strip()]
        set_config("categorias_pendientes", json.dumps(cats))
        set_config("categorias_indice", "0")
        if cats:
            set_onboarding(numero, "categoria_horario", cats[0])
            enviar_texto(numero,
                f"✅ Categorías: *{', '.join(cats)}*\n\n"
                f"Ahora configura cada una.\n\n"
                f"*¿De qué hora a qué hora son los {cats[0].upper()}?*\n"
                f"Ejemplo: _8:00 a 10:30_"
            )
        else:
            finalizar_onboarding(numero)
        return True

    if paso == "categoria_horario":
        partes = re.split(r'[-–a]', t.replace("de","").replace("las","").strip())
        if len(partes) >= 2:
            inicio = partes[0].strip().replace(".",":").strip()
            fin    = partes[-1].strip().replace(".",":").strip()
            set_config(f"cat_{cat}_inicio", inicio)
            set_config(f"cat_{cat}_fin", fin)
            set_onboarding(numero, "categoria_audio", cat)
            enviar_texto(numero,
                f"✅ Horario de *{cat}*: {inicio} a {fin}\n\n"
                f"Ahora *manda el audio* con el menú de {cat.upper()}. 🎙️\n"
                f"Incluye platillos y precios. Este audio se enviará tal cual a tus clientes."
            )
        else:
            enviar_texto(numero, "No entendí el horario. Escríbelo así: _8:00 a 10:30_")
        return True

    if paso == "categoria_audio":
        if audio_path:
            ext  = os.path.splitext(audio_path)[1]
            dest = os.path.join(AUDIODIR, f"{cat}{ext}")
            os.rename(audio_path, dest)
            inicio = get_config(f"cat_{cat}_inicio", "")
            fin    = get_config(f"cat_{cat}_fin", "")
            guardar_categoria(cat, inicio, fin, dest)
            enviar_texto(numero, f"✅ Audio de *{cat}* guardado.")

            cats = json.loads(get_config("categorias_pendientes", "[]"))
            idx  = int(get_config("categorias_indice", "0")) + 1
            set_config("categorias_indice", str(idx))

            if idx < len(cats):
                siguiente = cats[idx]
                set_onboarding(numero, "categoria_horario", siguiente)
                enviar_texto(numero,
                    f"*¿De qué hora a qué hora son los {siguiente.upper()}?*\n"
                    f"Ejemplo: _13:00 a 17:00_"
                )
            else:
                finalizar_onboarding(numero)
        else:
            enviar_texto(numero, f"Necesito que mandes un *audio de voz* con el menú de {cat.upper()}. 🎙️")
        return True

    return False

def finalizar_onboarding(numero):
    del_onboarding(numero)
    cats     = get_categorias()
    cats_txt = "\n".join([f"• {c['nombre'].capitalize()}: {c['inicio']} a {c['fin']}" for c in cats])
    enviar_texto(numero,
        f"🎉 *¡Configuración completada!*\n\n"
        f"*{nombre_negocio()}* ya está listo para atender clientes. 🚀\n\n"
        f"Tu asistente: *{nombre_asistente()}*\n"
        f"Categorías activas:\n{cats_txt}\n\n"
        f"Envía *COMANDOS* para ver qué puedes modificar."
    )

# ════════════════════════════════════════════════════════════
#  COMANDOS DEL DUEÑO
# ════════════════════════════════════════════════════════════
LISTA_COMANDOS = """📋 *COMANDOS MI TIENDA WA*

*Configuración general:*
CAMBIAR NOMBRE [nuevo nombre]
CAMBIAR ASISTENTE [nuevo nombre]
CAMBIAR DIRECCION [nueva dirección]
CAMBIAR HORARIO [nuevo horario]
CAMBIAR DIAS [nuevos días]
CAMBIAR TELEFONO [nuevo teléfono]
CAMBIAR REDES [nuevas redes]
RESPUESTA SI [texto personalizado]

*Categorías y menú:*
ACTUALIZAR DESAYUNO → luego envía el audio
ACTUALIZAR COMIDA → luego envía el audio
ACTUALIZAR CENA → luego envía el audio
HORARIO DESAYUNO 8:00 12:00
HORARIO COMIDA 12:00 17:00
HORARIO CENA 18:00 22:00
ELIMINAR CATEGORIA [nombre]
VER CATEGORIAS

*Disponibilidad:*
HOY NO ABRIMOS
MANANA NO ABRIMOS
ABRIMOS NORMAL

*Información y control:*
ESTADO
VER CONFIG
REINICIAR SISTEMA
COMANDOS"""

def procesar_comando_dueno(numero, texto, audio_path=None):
    t  = texto.strip().upper()
    tl = texto.strip().lower()

    if t == "COMANDOS":
        enviar_texto(numero, LISTA_COMANDOS)
        return True

    if t == "ESTADO":
        try:
            r = requests.get(f"{WUZAPI}/session/status", headers=get_headers(), timeout=5)
            wuzapi_ok = "✅" if r.status_code == 200 else "❌"
        except:
            wuzapi_ok = "❌"
        cat = categoria_activa_ahora()
        cats_estado = ""
        for c in get_categorias():
            audio_ok = "✅" if c.get("audio") and os.path.exists(c["audio"]) else "⚠️ sin audio"
            cats_estado += f"• {c['nombre'].capitalize()}: {c['inicio']}-{c['fin']} {audio_ok}\n"
        cierre = es_cierre_hoy()
        enviar_texto(numero,
            f"📊 *ESTADO DEL SISTEMA*\n\n"
            f"🤖 Bot: ✅\n"
            f"📡 WuzAPI: {wuzapi_ok}\n"
            f"🕐 Hora: {hora_actual()}\n"
            f"🍽️ Categoría activa: {cat['nombre'].capitalize() if cat else 'Ninguna'}\n\n"
            f"*Categorías:*\n{cats_estado if cats_estado else 'Sin categorías'}\n"
            f"{'⛔ Hoy cerrado: ' + cierre if cierre else '✅ Abierto hoy'}"
        )
        return True

    if t == "VER CONFIG":
        enviar_texto(numero,
            f"⚙️ *CONFIGURACIÓN ACTUAL*\n\n"
            f"Negocio: {nombre_negocio()}\n"
            f"Asistente: {nombre_asistente()}\n"
            f"Dirección: {get_direccion() or '—'}\n"
            f"Horario: {horario_general()}\n"
            f"Días: {dias_trabajo()}\n"
            f"Teléfono: {get_telefono() or '—'}\n"
            f"Redes: {get_redes() or '—'}\n"
            f"Respuesta SÍ: {respuesta_si()}"
        )
        return True

    if t == "VER CATEGORIAS":
        cats = get_categorias()
        if cats:
            msg = "📋 *CATEGORÍAS ACTIVAS*\n\n"
            for c in cats:
                audio_ok = "✅" if c.get("audio") and os.path.exists(c["audio"]) else "⚠️ sin audio"
                msg += f"• *{c['nombre'].capitalize()}*: {c['inicio']} a {c['fin']} {audio_ok}\n"
        else:
            msg = "No hay categorías configuradas."
        enviar_texto(numero, msg)
        return True

    if t == "REINICIAR SISTEMA":
        enviar_texto(numero, "🔄 Reiniciando sistema...")
        threading.Thread(target=lambda: (
            time.sleep(2),
            os.system("bash ~/iniciar_mitiendawa.sh &")
        ), daemon=True).start()
        return True

    if t == "HOY NO ABRIMOS":
        hoy = datetime.now().strftime("%Y-%m-%d")
        guardar_cierre(hoy, "Dia de descanso")
        enviar_texto(numero, f"✅ Hoy ({hoy}) el sistema indicará que están cerrados.")
        return True

    if t in ["MANANA NO ABRIMOS", "MAÑANA NO ABRIMOS"]:
        manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        guardar_cierre(manana, "Dia de descanso")
        enviar_texto(numero, f"✅ Mañana ({manana}) el sistema indicará que están cerrados.")
        return True

    if t == "ABRIMOS NORMAL":
        hoy = datetime.now().strftime("%Y-%m-%d")
        con = sqlite3.connect(DBPATH)
        c = con.cursor()
        c.execute("DELETE FROM cierres WHERE fecha=?", (hoy,))
        con.commit()
        con.close()
        enviar_texto(numero, "✅ Cierre de hoy cancelado. El sistema atiende con normalidad.")
        return True

    # Comandos con valor en la misma línea
    cambios = [
        ("CAMBIAR NOMBRE ",    13, "nombre_negocio",   "✅ Nombre actualizado"),
        ("CAMBIAR ASISTENTE ", 17, "nombre_asistente", "✅ Asistente actualizado"),
        ("CAMBIAR DIRECCION ", 17, "direccion",        "✅ Dirección actualizada"),
        ("CAMBIAR HORARIO ",   15, "horario_general",  "✅ Horario actualizado"),
        ("CAMBIAR DIAS ",      12, "dias_trabajo",     "✅ Días actualizados"),
        ("CAMBIAR TELEFONO ",  16, "telefono_contacto","✅ Teléfono actualizado"),
        ("CAMBIAR REDES ",     13, "redes_sociales",   "✅ Redes actualizadas"),
    ]
    for cmd, offset, clave, msg in cambios:
        if t.startswith(cmd):
            valor = texto.strip()[offset:].strip()
            if valor:
                set_config(clave, valor)
                enviar_texto(numero, msg)
            else:
                enviar_texto(numero, f"❌ Escribe el valor después del comando.")
            return True

    if t.startswith("RESPUESTA SI "):
        valor = texto.strip()[13:].strip()
        if valor:
            set_config("respuesta_si", valor)
            enviar_texto(numero, "✅ Respuesta para cuando el cliente dice Sí actualizada.")
        else:
            enviar_texto(numero, "❌ Escribe el texto después de RESPUESTA SI")
        return True

    # Actualizar audios
    for cat_nombre in ["desayuno", "comida", "cena"]:
        if t == f"ACTUALIZAR {cat_nombre.upper()}":
            set_onboarding(numero, "cmd_actualizar_audio", cat_nombre)
            enviar_texto(numero, f"🎙️ Envía el audio con el menú de *{cat_nombre.upper()}*")
            return True

    # Horarios directos
    for cat_nombre in ["desayuno", "comida", "cena"]:
        if t.startswith(f"HORARIO {cat_nombre.upper()}"):
            partes = tl.replace(f"horario {cat_nombre}", "").strip().split()
            if len(partes) >= 2:
                inicio, fin = partes[0], partes[1]
                audio_guardado = get_config(f"cat_{cat_nombre}_audio", "")
                guardar_categoria(cat_nombre, inicio, fin, audio_guardado)
                set_config(f"cat_{cat_nombre}_inicio", inicio)
                set_config(f"cat_{cat_nombre}_fin", fin)
                enviar_texto(numero, f"✅ Horario de {cat_nombre}: {inicio} a {fin}")
            else:
                enviar_texto(numero, f"❌ Formato: HORARIO {cat_nombre.upper()} 8:00 12:00")
            return True

    if t.startswith("ELIMINAR CATEGORIA "):
        cat_nombre = tl.replace("eliminar categoria ", "").strip()
        if cat_nombre:
            eliminar_categoria(cat_nombre)
            enviar_texto(numero, f"✅ Categoría *{cat_nombre}* eliminada.")
        else:
            enviar_texto(numero, "❌ Especifica: ELIMINAR CATEGORIA desayuno")
        return True

    # Recibir audio para actualización
    estado = get_onboarding(numero)
    if estado and estado["paso"] == "cmd_actualizar_audio" and audio_path:
        cat_nombre = estado["categoria_actual"]
        ext  = os.path.splitext(audio_path)[1]
        dest = os.path.join(AUDIODIR, f"{cat_nombre}{ext}")
        os.rename(audio_path, dest)
        set_config(f"cat_{cat_nombre}_audio", dest)
        inicio = get_config(f"cat_{cat_nombre}_inicio", "")
        fin    = get_config(f"cat_{cat_nombre}_fin", "")
        guardar_categoria(cat_nombre, inicio, fin, dest)
        del_onboarding(numero)
        enviar_texto(numero, f"✅ Audio de *{cat_nombre}* actualizado correctamente.")
        return True

    return False

# ════════════════════════════════════════════════════════════
#  PROCESAR MENSAJES ENTRANTES
# ════════════════════════════════════════════════════════════
def procesar_mensaje(sender, texto, audio_path=None):
    phone = sender.replace("@s.whatsapp.net", "").replace("@g.us", "")
    tb    = leer_archivo(BPATH)

    log(f"MSG de {phone}: {texto[:80]}")

    # Ignorar grupos
    if "@g.us" in sender:
        return

    # ── Es el dueño ──────────────────────────────────────────
    if phone == tb or sender == tb:
        # Primero intentar onboarding
        if procesar_onboarding(phone, texto, audio_path):
            return
        # Luego comandos
        if procesar_comando_dueno(phone, texto, audio_path):
            return
        return

    # ── Es un cliente ────────────────────────────────────────
    if not get_config("nombre_negocio"):
        log("Sistema sin configurar, ignorando cliente")
        return

    responder_cliente(sender, texto)

# ════════════════════════════════════════════════════════════
#  WEBHOOK
# ════════════════════════════════════════════════════════════
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data       = request.get_json(force=True) or {}
        event_data = data.get("event", data)
        info       = event_data.get("Info", {})
        msg        = event_data.get("Message", {})

        sender   = info.get("Sender", info.get("sender", ""))
        from_me  = info.get("IsFromMe", info.get("fromMe", False))
        msg_id   = info.get("ID", info.get("id", ""))

        if from_me or not sender:
            return jsonify({"status": "ok"}), 200

        texto = (msg.get("conversation") or
                 msg.get("extendedTextMessage", {}).get("text") or "")

        audio_path = None
        audio_msg  = msg.get("audioMessage", {})
        if audio_msg or info.get("MediaType") == "audio":
            mime       = audio_msg.get("mimetype", "audio/ogg")
            audio_path = descargar_audio_wuzapi(msg_id, mime)
            if not texto:
                texto = "[audio]"

        if not texto and not audio_path:
            return jsonify({"status": "ok"}), 200

        threading.Thread(
            target=procesar_mensaje,
            args=(sender, texto, audio_path),
            daemon=True
        ).start()

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        log(f"ERROR webhook: {e}")
        return jsonify({"status": "error"}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "mitiendawa_ok"}), 200

# ════════════════════════════════════════════════════════════
#  INICIO
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    os.makedirs(AUDIODIR, exist_ok=True)
    os.makedirs(os.path.dirname(DBPATH), exist_ok=True)

    log("Iniciando MI TIENDA WA...")
    init_db()

    tb  = leer_archivo(BPATH)
    tok = leer_archivo(TOKENPATH)
    log(f"Token: {tok[:8]}..." if tok else "Token no encontrado")
    log(f"Telefono B: {tb}")

    # Iniciar onboarding si no hay negocio configurado
    if tb and not get_config("nombre_negocio"):
        set_onboarding(tb, "inicio")
        log(f"Onboarding iniciado para {tb}")

    log("Bot escuchando en puerto 9090...")
    app.run(host="0.0.0.0", port=9090, debug=False, threaded=True)

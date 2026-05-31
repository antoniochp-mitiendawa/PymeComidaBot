#!/usr/bin/env python3
# ============================================================
#  MI TIENDA WA — Bot Principal
#  Motor de atención al cliente para restaurantes pequeños
#  Funciona con WuzAPI + Termux en Android
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

# ── Token y teléfono B ───────────────────────────────────────
def leer_archivo(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except:
        return ""

TOKEN     = leer_archivo(TOKENPATH)
TELEFONO_B = leer_archivo(BPATH)

# ── Flask ────────────────────────────────────────────────────
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
    "saludo":   ["✨","🌤️","🌅","☕","🤝","👋","🎈","🍀","☀️","🌈","🙌","⭐","🌻","🔋","🌸","🍃","💫","🌟"],
    "menu":     ["📖","📗","📘","📙","📓","📒","📑","📚","🔬","🎓","🧠","🚀","💎","💡","📢","🔔"],
    "horario":  ["🕐","🕑","🕒","🕓","🕔","🕕","🕖","🕗","🕘","🕙","🕚","🕛","⏰","⌛","⏲️","⏱️"],
    "ubicacion":["📍","🗺️","🧭","🏠","🏪","🏢","📌","🔍","🚩","🌐","🏘️","🏚️","🗾"],
    "precio":   ["💰","🏷️","💵","💳","🎁","💎","💸","🪙","💹","🛒","💲","🎯","🔥","📦","💴","💶","💷"],
    "comida":   ["🍳","🥞","🥓","🍔","🍟","🍕","🌮","🥗","🍜","🍲","🥘","🍰","🍨","🍦","🍩","🥨","🥖","🍚"],
    "aprobacion":["✅","👍","👌","🔥","💪","😎","👏","🙌","✨","💯"],
    "despedida":["👋","🙏","😊","✨","🌟","💫","🎉","🍽️","🥡","💚","⭐","🌈","🌸"]
}

RESPUESTAS = {
    "saludo_con_menu": [
        "{} ¡{}! 🌅 Soy *{}* de *{}*. Ahora estamos en *{}* hasta las {}. ¿Te comparto el menú? 🍽️",
        "{} ¡Qué gusto saludarte! 🙌 Aquí *{}* de *{}*. En este momento servimos *{}* (hasta {}). ¿Te interesa? 📖",
        "{} ¡Bienvenido a *{}*! 🤝 Soy *{}*. Estamos en horario de *{}* hasta las {}. ¿Quieres que te cuente qué hay? 🎈",
        "{} ¡Hola! ☕ Te habla *{}* de *{}*. Ahora es hora de *{}* (cierra a las {}). ¿Te mando la información? ✨",
        "{} ¡Gracias por escribir! 🌻 Soy *{}*. En *{}* estamos con *{}* hasta las {}. ¿Te gustaría saber qué tenemos? 💫"
    ],
    "saludo_sin_menu": [
        "{} ¡{}! 🌅 Soy *{}* de *{}*. En este momento no tenemos servicio activo. Nuestro horario es *{}*. ¿Te esperamos más tarde? 🙏",
        "{} ¡Qué gusto verte! ✨ Aquí *{}*. Por ahora no estamos sirviendo (horario: {}). ¡Te esperamos en nuestro próximo horario! 🌈",
        "{} ¡Hola! ☕ Te atiende *{}*. Cerramos por ahora, pero abrimos en *{}*. ¿Quieres que te avise cuando abramos? 🔔",
        "{} ¡Bienvenido a *{}*! 🌟 Lamento informarte que en este momento no tenemos servicio. Nuestro horario es {}. ¡Gracias por escribir! 💫"
    ],
    "menu_con_audio": [
        "{} ¡Claro! 😊 Te mando la información de nuestros *{}* {}:",
        "{} Con mucho gusto {} Te comparto el detalle de los *{}*:",
        "{} ¡Ahí te va! 🎙️ Escucha el menú de *{}*:",
        "{} Por supuesto {} Aquí tienes la información de *{}*:"
    ],
    "menu_sin_audio": [
        "{} Por el momento no tengo el menú disponible {} ¿Quieres que te llame alguien para ayudarte? 🤝",
        "{} ¡Ups! {} Aún no cargo el menú de *{}*. ¿Te parece si te contacta un asesor? 📞",
        "{} Lo siento {} El menú de *{}* no está listo todavía. ¿Prefieres que te llamemos? 🙏"
    ],
    "precio_con_audio": [
        "{} ¡Claro! {} En este audio te decimos los precios de *{}*: 💰",
        "{} Por supuesto {} Escucha los precios de nuestros *{}*: 🏷️",
        "{} ¡Ahí te va la info! {} Te comparto los precios de *{}*: 💸"
    ],
    "precio_sin_audio": [
        "{} Para darte información de precios {} ¿Quieres que te llamemos? 📞",
        "{} Lo siento {} No tengo los precios a la mano. ¿Te parece si te contacta un asesor? 🤝"
    ],
    "ubicacion": [
        "{} *{}* se encuentra en:\n📍 {}\n\n📞 Teléfono: {}\n\n{} ¡Te esperamos! 🙏",
        "{} Estamos en {} 🌐\n📞 Contáctanos al {}\n\n📍 Dirección: {}\n\n{} ¿Necesitas indicaciones? 🧭",
        "{} Aquí está nuestra dirección:\n🏠 {}\n📞 {}\n\n{} ¡Llegar es fácil! 🚩"
    ],
    "horario": [
        "{} Te comparto nuestro horario {}:\n\n📅 *{}*\n🕐 *{}*\n\n{} Además, por categoría:\n{}\n\n{} ¡Te esperamos! 🙏",
        "{} Nuestros horarios son {}:\n• Días: *{}*\n• Horario general: *{}*\n\n{} Por tiempo de comida:\n{}\n\n{} ¿Alguna duda? ✨"
    ],
    "pedido_pregunta": [
        "{} ¡Perfecto! {} ¿Quieres que te llamemos para coordinar tu pedido? 📞",
        "{} Con gusto te ayudamos {} ¿Te parece si un asesor te llama para tomar tu pedido? 🤝",
        "{} ¡Excelente! {} ¿Preferes que te llamemos o vienes directamente al local? 🏠"
    ],
    "cliente_si": [
        "{} ¡Perfecto! {} En unos momentos alguien se comunica contigo. ¡Gracias por preferirnos! 🙏",
        "{} ¡Genial! {} Ya avisé al equipo. Te contactarán en breve. 📞",
        "{} ¡Excelente! {} Gracias por tu interés. Pronto te llamamos. ✨"
    ],
    "cliente_no": [
        "{} Sin problema {} Gracias por contactarnos. ¡Qué tengas un excelente día! 🌟",
        "{} Entendido {} Estamos aquí cuando gustes. ¡Hasta pronto! 👋",
        "{} Gracias de todas formas {} Recuerda que siempre serás bienvenido. 🙏"
    ],
    "despedida": [
        "{} ¡Gracias a ti! {} Fue un placer atenderte. ¡Hasta pronto! 👋",
        "{} ¡Qué gusto ayudarte! {} Te esperamos cuando gustes. 🌈",
        "{} ¡Nos vemos! {} Recuerda que *{}* siempre está para ti. 🙌"
    ],
    "desconocido": [
        "{} Gracias por contactar a *{}*, soy *{}*. No tengo esa información {} Voy a avisar para que alguien te contacte. 🙏",
        "{} ¡Hola! 🙌 Soy *{}* de *{}*. No entendí bien tu mensaje {} ¿Te parece si alguien del equipo te escribe? 📞"
    ],
    "cerrado": [
        "{} Hoy estamos cerrados ({}) {}\n\nNuestro horario habitual es {} ({}). ¡Te esperamos pronto! 🙏",
        "{} Lo sentimos mucho {} Hoy descansamos ({}) {}\n\nTe atendemos en horario {} ({}). 🌟"
    ],
    "no_dia_laboral": [
        "{} Hoy descansamos {} Te atendemos {} en horario {}. ¡Gracias por escribir! 🙏",
        "{} Gracias por contactarnos {} Nuestros días de atención son {}. Estaremos encantados de atenderte pronto. 🌈"
    ],
    "categoria_inactiva_con_proxima": [
        "{} En este momento no tenemos servicio activo {} Pero a las *{}* comenzamos con *{}*. ¿Te esperamos? 🙏",
        "{} Cerramos por ahora {} Nuestra próxima categoría es *{}* a las {}. ¡Te esperamos! ✨",
        "{} Lo siento {} Ahora no estamos sirviendo. Abrimos de nuevo en *{}* a las {}. 🌟"
    ]
}

def get_emoji(categoria):
    return random.choice(EMOJIS.get(categoria, ["✨"]))

def get_respuesta(categoria, idx=0):
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
    
    if TELEFONO_B:
        enviar_texto(TELEFONO_B,
            f"📞 *CLIENTE INTERESADO EN PEDIDO*\n\n"
            f"El cliente *{numero.replace('@s.whatsapp.net','')}* "
            f"solicita que lo llamen.\n\n"
            f"Hora: {now.strftime('%H:%M')}"
        )

def es_cierre_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("SELECT motivo FROM cierres WHERE fecha=?", (hoy,))
    row = c.fetchone()
    con.close()
    return row[0] if row else None

def guardar_cierre(fecha, motivo="Día de descanso"):
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

def guardar_cliente(numero, nombre):
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("INSERT OR REPLACE INTO clientes(numero,nombre,primera_vez,fecha_registro) VALUES(?,?,0,?)",
              (numero, nombre, datetime.now().strftime("%Y-%m-%d")))
    con.commit()
    con.close()

def marcar_cliente_atendido(numero):
    con = sqlite3.connect(DBPATH)
    c = con.cursor()
    c.execute("UPDATE clientes SET primera_vez=0 WHERE numero=?", (numero,))
    con.commit()
    con.close()

# ════════════════════════════════════════════════════════════
#  ENVÍO DE MENSAJES VÍA WUZAPI
# ════════════════════════════════════════════════════════════
def headers():
    return {"Token": TOKEN, "Content-Type": "application/json"}

def enviar_texto(numero, texto):
    try:
        phone = numero.replace("@s.whatsapp.net", "").replace("@g.us", "")
        r = requests.post(f"{WUZAPI}/chat/send/text",
                          headers=headers(),
                          json={"Phone": phone, "Body": texto},
                          timeout=10)
        log(f"ENVÍO TEXTO → {phone}: {texto[:60]}")
        return r.status_code == 200
    except Exception as e:
        log(f"ERROR enviando texto: {e}")
        return False

def enviar_audio(numero, audio_path):
    try:
        phone = numero.replace("@s.whatsapp.net", "").replace("@g.us", "")
        import base64
        with open(audio_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(audio_path)[1].lower()
        mime = "audio/ogg; codecs=opus" if ext in [".ogg", ".opus"] else "audio/mpeg"
        r = requests.post(f"{WUZAPI}/chat/send/audio",
                          headers=headers(),
                          json={"Phone": phone, "Audio": data, "FileName": os.path.basename(audio_path)},
                          timeout=20)
        log(f"ENVÍO AUDIO → {phone}: {audio_path}")
        return r.status_code == 200
    except Exception as e:
        log(f"ERROR enviando audio: {e}")
        return False

def descargar_audio_wuzapi(msg_id, mime_type="audio/ogg"):
    try:
        r = requests.get(f"{WUZAPI}/chat/downloadmedia/{msg_id}",
                         headers=headers(), timeout=15)
        if r.status_code == 200:
            ext = ".ogg" if "ogg" in mime_type else ".mp3"
            path = os.path.join(AUDIODIR, f"temp_{msg_id}{ext}")
            with open(path, "wb") as f:
                f.write(r.content)
            return path
    except Exception as e:
        log(f"ERROR descargando audio: {e}")
    return None

# ════════════════════════════════════════════════════════════
#  UTILIDADES DE TIEMPO
# ════════════════════════════════════════════════════════════
def hora_actual():
    return datetime.now().strftime("%H:%M")

def hora_a_minutos(h):
    try:
        partes = h.replace(".", ":").split(":")
        return int(partes[0]) * 60 + int(partes[1])
    except:
        return 0

def saludo_por_hora():
    h = int(datetime.now().strftime("%H"))
    if 5 <= h < 12:
        return random.choice(["¡Buenos días!", "¡Hermana mañana!", "¡Qué tal tu mañana!", "¡Excelente día!"])
    elif 12 <= h < 19:
        return random.choice(["¡Buenas tardes!", "¡Qué tal esta tarde!", "¡Linda tarde!", "¡Excelente tarde!"])
    else:
        return random.choice(["¡Buenas noches!", "¡Qué tal tu noche!", "¡Linda noche!", "¡Gracias por escribir tan noche!"])

def categoria_activa_ahora():
    ahora = hora_a_minutos(hora_actual())
    for cat in get_categorias():
        inicio = hora_a_minutos(cat["inicio"])
        fin    = hora_a_minutos(cat["fin"])
        if inicio <= ahora <= fin:
            return cat
    return None

def dia_laboral_hoy():
    dias_config = get_config("dias_trabajo", "lunes a domingo").lower()
    hoy_num = datetime.now().weekday()
    dias_map = {
        "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
        "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6
    }
    if "lunes a domingo" in dias_config or "todos los días" in dias_config or "toda la semana" in dias_config:
        return True
    if "lunes a viernes" in dias_config and hoy_num <= 4:
        return True
    if "lunes a sábado" in dias_config or "lunes a sabado" in dias_config:
        if hoy_num <= 5:
            return True
    for nombre, num in dias_map.items():
        if nombre in dias_config and hoy_num == num:
            return True
    return False

def nombre_negocio():
    return get_config("nombre_negocio", "nuestro negocio")

def nombre_asistente():
    return get_config("nombre_asistente", "el asistente")

def horario_general():
    return get_config("horario_general", "nuestro horario habitual")

def dias_trabajo():
    return get_config("dias_trabajo", "todos los días")

def direccion():
    return get_config("direccion", "")

def telefono_contacto():
    return get_config("telefono_contacto", "")

def redes_sociales():
    return get_config("redes_sociales", "")

def respuesta_si():
    return get_config("respuesta_si", "Gracias por tu interés, en breve nos comunicamos contigo.")

# ════════════════════════════════════════════════════════════
#  PROMPT MAESTRO — MOTOR DE RESPUESTAS AL CLIENTE (VARIADO)
# ════════════════════════════════════════════════════════════

INTENCIONES = {
    "saludo": [
        "hola", "buenas", "buenos días", "buenos dias", "buen día", "buen dia",
        "buenas tardes", "buenas noches", "qué tal", "que tal", "hey", "hi",
        "quiubo", "quiúbo", "qué onda", "que onda", "saludos"
    ],
    "menu": [
        "menú", "menu", "qué tienen", "que tienen", "qué hay", "que hay",
        "qué tienen hoy", "que tienen hoy", "qué comen", "que comen",
        "qué sirven", "que sirven", "qué venden", "que venden",
        "qué me recomiendas", "que me recomiendas", "carta", "platillos",
        "para comer", "de comer", "desayuno", "desayunos", "comida", "comidas",
        "cena", "cenas", "almuerzo", "qué ofrecen", "que ofrecen"
    ],
    "ubicacion": [
        "dónde están", "donde estan", "dónde quedan", "donde quedan",
        "dirección", "direccion", "cómo llego", "como llego",
        "dónde se ubican", "donde se ubican", "en qué calle", "domicilio"
    ],
    "horario": [
        "horario", "a qué hora abren", "a que hora abren",
        "a qué hora cierran", "a que hora cierran", "cuándo abren",
        "están abiertos", "hasta qué hora", "qué días trabajan"
    ],
    "pedido": [
        "quiero pedir", "hacer un pedido", "quiero ordenar",
        "a domicilio", "delivery", "que me llamen", "llámame"
    ],
    "precio": [
        "cuánto cuesta", "cuanto cuesta", "cuánto vale", "precios", "qué precio"
    ],
    "redes": [
        "facebook", "instagram", "redes sociales", "red social"
    ],
    "despedida": [
        "gracias", "muchas gracias", "hasta luego", "bye", "adios", "provecho"
    ]
}

def detectar_intencion(texto):
    t = texto.lower().strip()
    for intencion, palabras in INTENCIONES.items():
        for p in palabras:
            if p in t:
                return intencion
    return "desconocido"

def cliente_quiere_llamada(numero, texto):
    confirmaciones = ["sí", "si", "sí por favor", "claro", "ok", "está bien", "adelante", "por favor", "sí quiero", "si quiero"]
    negativas = ["no", "no gracias", "ahorita no", "ya no", "no quiero"]
    t = texto.lower().strip()
    
    if any(c in t for c in confirmaciones):
        registrar_interesado(numero)
        emo = get_emoji("aprobacion")
        template = get_respuesta("cliente_si")
        msg = template.format(emo, get_emoji("saludo"), respuesta_si())
        enviar_texto(numero, msg)
        return True
    if any(n in t for n in negativas):
        emo = get_emoji("saludo")
        template = get_respuesta("cliente_no")
        msg = template.format(emo, get_emoji("aprobacion"))
        enviar_texto(numero, msg)
        return True
    return False

def preguntar_nombre(numero):
    enviar_texto(numero, f"{get_emoji('saludo')} ¡Hola! {get_emoji('comida')} ¿Cómo te llamas? (Responde con tu nombre) 😊")

def responder_cliente(numero, texto):
    negocio = nombre_negocio()
    asistente = nombre_asistente()
    saludo_hora = saludo_por_hora()
    
    # Verificar si el cliente ya tiene nombre
    cliente = get_cliente(numero)
    if cliente and cliente["primera_vez"] == 1:
        # Es primera vez, preguntar nombre
        preguntar_nombre(numero)
        marcar_cliente_atendido(numero)
        return
    
    cierre = es_cierre_hoy()
    if cierre:
        emo = get_emoji("saludo")
        template = get_respuesta("cerrado")
        msg = template.format(emo, cierre, get_emoji("horario"), horario_general(), dias_trabajo())
        enviar_texto(numero, msg)
        return
    
    if not dia_laboral_hoy():
        emo = get_emoji("saludo")
        template = get_respuesta("no_dia_laboral")
        msg = template.format(emo, get_emoji("horario"), dias_trabajo(), horario_general())
        enviar_texto(numero, msg)
        return
    
    intencion = detectar_intencion(texto)
    cat = categoria_activa_ahora()
    
    nombre_cliente = cliente["nombre"] if cliente else ""
    
    if intencion == "saludo":
        if cat:
            template = get_respuesta("saludo_con_menu")
            msg = template.format(get_emoji("saludo"), saludo_hora, asistente, negocio, cat["nombre"].capitalize(), cat["fin"])
            enviar_texto(numero, msg)
        elif get_categorias():
            # Buscar próxima categoría
            ahora = hora_a_minutos(hora_actual())
            proxima = None
            for c in get_categorias():
                if hora_a_minutos(c["inicio"]) > ahora:
                    if proxima is None or hora_a_minutos(c["inicio"]) < hora_a_minutos(proxima["inicio"]):
                        proxima = c
            if proxima:
                template = get_respuesta("categoria_inactiva_con_proxima")
                msg = template.format(get_emoji("saludo"), get_emoji("horario"), proxima["nombre"].capitalize(), proxima["inicio"])
                enviar_texto(numero, msg)
            else:
                template = get_respuesta("saludo_sin_menu")
                msg = template.format(get_emoji("saludo"), saludo_hora, asistente, negocio, horario_general())
                enviar_texto(numero, msg)
        else:
            template = get_respuesta("saludo_sin_menu")
            msg = template.format(get_emoji("saludo"), saludo_hora, asistente, negocio, horario_general())
            enviar_texto(numero, msg)
        return
    
    if intencion == "menu":
        if cat and cat.get("audio") and os.path.exists(cat["audio"]):
            emo1 = get_emoji("menu")
            emo2 = get_emoji("comida")
            template = get_respuesta("menu_con_audio")
            msg = template.format(emo1, emo2, cat["nombre"].capitalize(), get_emoji("aprobacion"))
            enviar_texto(numero, msg)
            time.sleep(1)
            enviar_audio(numero, cat["audio"])
        else:
            emo = get_emoji("menu")
            template = get_respuesta("menu_sin_audio")
            cat_nombre = cat["nombre"] if cat else "comida"
            msg = template.format(emo, get_emoji("saludo"), cat_nombre.capitalize())
            enviar_texto(numero, msg)
        return
    
    if intencion == "precio":
        if cat and cat.get("audio") and os.path.exists(cat["audio"]):
            emo1 = get_emoji("precio")
            emo2 = get_emoji("comida")
            template = get_respuesta("precio_con_audio")
            msg = template.format(emo1, emo2, cat["nombre"].capitalize())
            enviar_texto(numero, msg)
            time.sleep(1)
            enviar_audio(numero, cat["audio"])
        else:
            emo = get_emoji("precio")
            template = get_respuesta("precio_sin_audio")
            msg = template.format(emo, get_emoji("saludo"))
            enviar_texto(numero, msg)
        return
    
    if intencion == "ubicacion":
        emo1 = get_emoji("ubicacion")
        emo2 = get_emoji("saludo")
        template = get_respuesta("ubicacion")
        telefono = telefono_contacto() if telefono_contacto() else "No disponible"
        msg = template.format(emo1, negocio, direccion(), telefono, emo2)
        enviar_texto(numero, msg)
        return
    
    if intencion == "horario":
        emo1 = get_emoji("horario")
        emo2 = get_emoji("saludo")
        emo3 = get_emoji("menu")
        template = get_respuesta("horario")
        cats_text = ""
        for c in get_categorias():
            cats_text += f"• *{c['nombre'].capitalize()}*: {c['inicio']} a {c['fin']}\n"
        msg = template.format(emo1, emo2, dias_trabajo(), horario_general(), emo3, cats_text, get_emoji("aprobacion"))
        enviar_texto(numero, msg)
        return
    
    if intencion == "pedido":
        emo = get_emoji("comida")
        template = get_respuesta("pedido_pregunta")
        msg = template.format(emo, get_emoji("aprobacion"))
        enviar_texto(numero, msg)
        return
    
    if intencion == "redes":
        if redes_sociales():
            enviar_texto(numero, f"{get_emoji('saludo')} ¡Gracias por el interés! {get_emoji('aprobacion')}\n\n{redes_sociales()}\n\n{get_emoji('despedida')} ¡Síguenos y comparte tu experiencia! ⭐")
        else:
            enviar_texto(numero, f"{get_emoji('saludo')} Por el momento no tenemos redes sociales activas {get_emoji('horario')} Pero puedes contactarnos directamente por aquí. 🙏")
        return
    
    if intencion == "despedida":
        emo = get_emoji("despedida")
        template = get_respuesta("despedida")
        msg = template.format(emo, get_emoji("saludo"), negocio)
        enviar_texto(numero, msg)
        return
    
    # Intención desconocida
    emo = get_emoji("saludo")
    template = get_respuesta("desconocido")
    msg = template.format(emo, negocio, asistente, get_emoji("comida"))
    enviar_texto(numero, msg)
    if TELEFONO_B:
        enviar_texto(TELEFONO_B, f"⚠️ *CONSULTA SIN RESPUESTA*\nCliente *{numero.replace('@s.whatsapp.net','')}* preguntó:\n_{texto}_")

# ════════════════════════════════════════════════════════════
#  COMANDOS DEL DUEÑO (TELÉFONO B) - SIN CAMBIOS
# ════════════════════════════════════════════════════════════
def procesar_comando_dueno(numero, texto, audio_path=None):
    t = texto.strip().upper()
    tl = texto.strip().lower()
    
    if t == "COMANDOS":
        cmds = """📋 *COMANDOS DISPONIBLES*
        
*Configuración:*
CAMBIAR NOMBRE
CAMBIAR ASISTENTE
CAMBIAR DIRECCION
CAMBIAR HORARIO
CAMBIAR DIAS
CAMBIAR TELEFONO
CAMBIAR REDES
RESPUESTA SI [texto]

*Categorías:*
ACTUALIZAR DESAYUNO (luego envía audio)
ACTUALIZAR COMIDA (luego envía audio)
ACTUALIZAR CENA (luego envía audio)
HORARIO DESAYUNO [inicio] [fin]
HORARIO COMIDA [inicio] [fin]
HORARIO CENA [inicio] [fin]
ELIMINAR CATEGORIA [nombre]
VER CATEGORIAS

*Estado y control:*
ESTADO
REINICIAR SISTEMA
VER CONFIG
HOY NO ABRIMOS
MAÑANA NO ABRIMOS
ABRIMOS NORMAL
"""
        enviar_texto(numero, cmds)
        return True
    
    if t == "ESTADO":
        bot_ok = "✅"
        wuzapi_ok = "❓"
        try:
            r = requests.get(f"{WUZAPI}/session/status", headers=headers(), timeout=5)
            wuzapi_ok = "✅" if r.status_code == 200 else "❌"
        except:
            wuzapi_ok = "❌"
        
        ahora = hora_actual()
        cat_activa = categoria_activa_ahora()
        cat_nombre = cat_activa["nombre"] if cat_activa else "Ninguna"
        
        desayuno_audio = "❌"
        comida_audio = "❌"
        cena_audio = "❌"
        for c in get_categorias():
            if c["nombre"] == "desayuno" and c.get("audio") and os.path.exists(c["audio"]):
                desayuno_audio = "✅"
            if c["nombre"] == "comida" and c.get("audio") and os.path.exists(c["audio"]):
                comida_audio = "✅"
            if c["nombre"] == "cena" and c.get("audio") and os.path.exists(c["audio"]):
                cena_audio = "✅"
        
        cierre = es_cierre_hoy()
        cierre_txt = f"❌ Hoy no hay cierre" if not cierre else f"✅ Hoy cerrado: {cierre}"
        
        estado_msg = f"""📊 *ESTADO DEL SISTEMA*

🤖 Bot: {bot_ok}
📡 Wuzapi: {wuzapi_ok}
🕐 Hora: {ahora}
🍽️ Categoría activa: {cat_nombre}

*Horarios configurados:*
• Desayuno: {get_config('cat_desayuno_inicio', 'No configurado')} a {get_config('cat_desayuno_fin', '')}
• Comida: {get_config('cat_comida_inicio', 'No configurado')} a {get_config('cat_comida_fin', '')}
• Cena: {get_config('cat_cena_inicio', 'No configurado')} a {get_config('cat_cena_fin', '')}

*Audios:*
🍳 Desayuno: {desayuno_audio}
🍽️ Comida: {comida_audio}
🌙 Cena: {cena_audio}

{cierre_txt}
"""
        enviar_texto(numero, estado_msg)
        return True
    
    if t == "REINICIAR SISTEMA":
        enviar_texto(numero, "🔄 Reiniciando sistema, en un momento vuelvo...")
        os.system("pkill -f bot.py; pkill -f wuzapi; pkill -f watchdog.sh")
        time.sleep(2)
        os.system("bash ~/iniciar_mitiendawa.sh &")
        return True
    
    if t == "VER CONFIG":
        config_msg = f"""⚙️ *CONFIGURACIÓN ACTUAL*

Negocio: {nombre_negocio()}
Asistente: {nombre_asistente()}
Dirección: {direccion()}
Horario general: {horario_general()}
Días: {dias_trabajo()}
Teléfono: {telefono_contacto() or 'No configurado'}
Redes: {redes_sociales() or 'No configurado'}
Respuesta automática SÍ: {respuesta_si()}
"""
        enviar_texto(numero, config_msg)
        return True
    
    if t.startswith("RESPUESTA SI"):
        nuevo_texto = texto.strip()[12:].strip()
        if nuevo_texto:
            set_config("respuesta_si", nuevo_texto)
            enviar_texto(numero, f"✅ Respuesta para cuando el cliente dice SÍ actualizada.")
        else:
            enviar_texto(numero, "❌ Escribe el texto después de RESPUESTA SI")
        return True
    
    if t.startswith("ACTUALIZAR DESAYUNO"):
        set_onboarding(numero, "cmd_actualizar_audio", "desayuno")
        enviar_texto(numero, "🎙️ Envía el audio con el menú de DESAYUNO")
        return True
    if t.startswith("ACTUALIZAR COMIDA"):
        set_onboarding(numero, "cmd_actualizar_audio", "comida")
        enviar_texto(numero, "🎙️ Envía el audio con el menú de COMIDA")
        return True
    if t.startswith("ACTUALIZAR CENA"):
        set_onboarding(numero, "cmd_actualizar_audio", "cena")
        enviar_texto(numero, "🎙️ Envía el audio con el menú de CENA")
        return True
    
    if t.startswith("HORARIO DESAYUNO"):
        partes = tl.replace("horario desayuno", "").strip().split()
        if len(partes) >= 2:
            set_config("cat_desayuno_inicio", partes[0])
            set_config("cat_desayuno_fin", partes[1])
            guardar_categoria("desayuno", partes[0], partes[1], get_config(f"cat_desayuno_audio", ""))
            enviar_texto(numero, f"✅ Horario de desayuno: {partes[0]} a {partes[1]}")
        else:
            enviar_texto(numero, "❌ Formato: HORARIO DESAYUNO 8:00 12:00")
        return True
    if t.startswith("HORARIO COMIDA"):
        partes = tl.replace("horario comida", "").strip().split()
        if len(partes) >= 2:
            set_config("cat_comida_inicio", partes[0])
            set_config("cat_comida_fin", partes[1])
            guardar_categoria("comida", partes[0], partes[1], get_config(f"cat_comida_audio", ""))
            enviar_texto(numero, f"✅ Horario de comida: {partes[0]} a {partes[1]}")
        else:
            enviar_texto(numero, "❌ Formato: HORARIO COMIDA 12:00 18:00")
        return True
    if t.startswith("HORARIO CENA"):
        partes = tl.replace("horario cena", "").strip().split()
        if len(partes) >= 2:
            set_config("cat_cena_inicio", partes[0])
            set_config("cat_cena_fin", partes[1])
            guardar_categoria("cena", partes[0], partes[1], get_config(f"cat_cena_audio", ""))
            enviar_texto(numero, f"✅ Horario de cena: {partes[0]} a {partes[1]}")
        else:
            enviar_texto(numero, "❌ Formato: HORARIO CENA 18:00 23:00")
        return True
    
    if t.startswith("ELIMINAR CATEGORIA"):
        cat_nombre = tl.replace("eliminar categoria", "").strip()
        if cat_nombre:
            eliminar_categoria(cat_nombre)
            enviar_texto(numero, f"✅ Categoría {cat_nombre} eliminada")
        else:
            enviar_texto(numero, "❌ Especifica: ELIMINAR CATEGORIA desayuno")
        return True
    
    if t == "VER CATEGORIAS":
        cats = get_categorias()
        if cats:
            msg = "📋 *CATEGORÍAS ACTIVAS*\n\n"
            for c in cats:
                audio_ok = "✅" if c["audio"] and os.path.exists(c["audio"]) else "⚠️ sin audio"
                msg += f"• {c['nombre'].capitalize()}: {c['inicio']} a {c['fin']} {audio_ok}\n"
        else:
            msg = "No hay categorías configuradas"
        enviar_texto(numero, msg)
        return True
    
    if t == "HOY NO ABRIMOS":
        hoy = datetime.now().strftime("%Y-%m-%d")
        guardar_cierre(hoy, "Día de descanso")
        enviar_texto(numero, f"✅ Registrado. Hoy ({hoy}) el sistema indicará que están cerrados.")
        return True
    
    if t == "MAÑANA NO ABRIMOS":
        manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        guardar_cierre(manana, "Día de descanso")
        enviar_texto(numero, f"✅ Registrado. Mañana ({manana}) cerrado.")
        return True
    
    if t == "ABRIMOS NORMAL":
        hoy = datetime.now().strftime("%Y-%m-%d")
        con = sqlite3.connect(DBPATH)
        c = con.cursor()
        c.execute("DELETE FROM cierres WHERE fecha=?", (hoy,))
        con.commit()
        con.close()
        enviar_texto(numero, "✅ Cierre cancelado. El sistema atiende con normalidad.")
        return True
    
    if t.startswith("CAMBIAR NOMBRE"):
        nuevo = texto.strip()[13:].strip()
        if nuevo:
            set_config("nombre_negocio", nuevo)
            enviar_texto(numero, f"✅ Nombre actualizado: {nuevo}")
        else:
            enviar_texto(numero, "❌ Escribe el nuevo nombre después de CAMBIAR NOMBRE")
        return True
    
    if t.startswith("CAMBIAR ASISTENTE"):
        nuevo = texto.strip()[16:].strip()
        if nuevo:
            set_config("nombre_asistente", nuevo)
            enviar_texto(numero, f"✅ Asistente actualizado: {nuevo}")
        else:
            enviar_texto(numero, "❌ Escribe el nuevo nombre del asistente")
        return True
    
    if t.startswith("CAMBIAR DIRECCION"):
        nuevo = texto.strip()[16:].strip()
        if nuevo:
            set_config("direccion", nuevo)
            enviar_texto(numero, f"✅ Dirección actualizada")
        else:
            enviar_texto(numero, "❌ Escribe la nueva dirección")
        return True
    
    if t.startswith("CAMBIAR HORARIO"):
        nuevo = texto.strip()[15:].strip()
        if nuevo:
            set_config("horario_general", nuevo)
            enviar_texto(numero, f"✅ Horario general actualizado")
        else:
            enviar_texto(numero, "❌ Escribe el nuevo horario")
        return True
    
    if t.startswith("CAMBIAR DIAS"):
        nuevo = texto.strip()[11:].strip()
        if nuevo:
            set_config("dias_trabajo", nuevo)
            enviar_texto(numero, f"✅ Días de trabajo actualizados")
        else:
            enviar_texto(numero, "❌ Escribe los nuevos días")
        return True
    
    if t.startswith("CAMBIAR TELEFONO"):
        nuevo = texto.strip()[15:].strip()
        if nuevo:
            set_config("telefono_contacto", nuevo)
            enviar_texto(numero, f"✅ Teléfono actualizado")
        else:
            enviar_texto(numero, "❌ Escribe el nuevo teléfono")
        return True
    
    if t.startswith("CAMBIAR REDES"):
        nuevo = texto.strip()[13:].strip()
        if nuevo:
            set_config("redes_sociales", nuevo)
            enviar_texto(numero, f"✅ Redes sociales actualizadas")
        else:
            enviar_texto(numero, "❌ Escribe las nuevas redes")
        return True
    
    estado = get_onboarding(numero)
    if estado and estado["paso"] == "cmd_actualizar_audio" and audio_path:
        categoria = estado["categoria_actual"]
        ext = os.path.splitext(audio_path)[1]
        dest = os.path.join(AUDIODIR, f"{categoria}{ext}")
        os.rename(audio_path, dest)
        set_config(f"cat_{categoria}_audio", dest)
        
        inicio = get_config(f"cat_{categoria}_inicio", "")
        fin = get_config(f"cat_{categoria}_fin", "")
        guardar_categoria(categoria, inicio, fin, dest)
        
        del_onboarding(numero)
        enviar_texto(numero, f"✅ Audio de {categoria} guardado correctamente.")
        return True
    
    return False

# ════════════════════════════════════════════════════════════
#  PROCESAR MENSAJES ENTRANTES
# ════════════════════════════════════════════════════════════
def procesar_mensaje(sender, texto, audio_path=None):
    phone = sender.replace("@s.whatsapp.net", "").replace("@g.us", "")
    tb = TELEFONO_B.replace("@s.whatsapp.net", "")
    
    log(f"MSG de {phone}: {texto[:80]}")
    
    # Es el dueño
    if phone == tb or sender == tb:
        estado = get_onboarding(sender)
        if estado and estado["paso"] == "cmd_actualizar_audio" and audio_path:
            procesar_comando_dueno(phone, texto, audio_path)
            return
        procesar_comando_dueno(phone, texto, audio_path)
        return
    
    # Es un cliente
    if not get_config("nombre_negocio"):
        log("Sistema sin configurar, ignorando mensaje de cliente")
        return
    
    if "@g.us" in sender:
        return
    
    # Verificar si el cliente está respondiendo su nombre (primera vez)
    cliente = get_cliente(sender)
    if cliente and cliente["primera_vez"] == 1:
        # Está respondiendo con su nombre
        nombre = texto.strip()
        if nombre and len(nombre) < 50:
            guardar_cliente(sender, nombre)
            enviar_texto(sender, f"{get_emoji('saludo')} ¡Mucho gusto {nombre}! {get_emoji('comida')} ¿En qué puedo ayudarte? (Desayuno, Comida, Cena, Horarios, Ubicación, etc.) 😊")
        else:
            enviar_texto(sender, f"{get_emoji('saludo')} No entendí tu nombre. ¿Puedes escribirlo de nuevo? (Solo texto, sin números) 🙏")
        return
    
    # Verificar si es respuesta a "¿quieres que te llamemos?"
    intencion = detectar_intencion(texto)
    if intencion in ["pedido", "saludo"] and cliente_quiere_llamada(sender, texto):
        return
    
    responder_cliente(sender, texto)

# ════════════════════════════════════════════════════════════
#  WEBHOOK — RECIBE EVENTOS DE WUZAPI
# ════════════════════════════════════════════════════════════
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True) or {}
        event_data = data.get("event", data)
        
        info = event_data.get("Info", {})
        msg = event_data.get("Message", {})
        
        sender = info.get("Sender", info.get("sender", ""))
        from_me = info.get("IsFromMe", info.get("fromMe", False))
        msg_id = info.get("ID", info.get("id", ""))
        
        if from_me or not sender:
            return jsonify({"status": "ok"}), 200
        
        texto = msg.get("conversation") or msg.get("extendedTextMessage", {}).get("text") or ""
        
        audio_path = None
        audio_msg = msg.get("audioMessage", {})
        if audio_msg or info.get("MediaType") == "audio":
            mime = audio_msg.get("mimetype", "audio/ogg")
            audio_path = descargar_audio_wuzapi(msg_id, mime)
            if not texto:
                texto = "[audio]"
        
        if not texto and not audio_path:
            return jsonify({"status": "ok"}), 200
        
        threading.Thread(target=procesar_mensaje, args=(sender, texto, audio_path), daemon=True).start()
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        log(f"ERROR en webhook: {e}")
        return jsonify({"status": "error"}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "mitiendawa_ok"}), 200

# ════════════════════════════════════════════════════════════
#  INICIO
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    log("Iniciando MI TIENDA WA...")
    init_db()
    
    os.makedirs(AUDIODIR, exist_ok=True)
    os.makedirs(os.path.dirname(DBPATH), exist_ok=True)
    
    global TELEFONO_B
    TELEFONO_B = leer_archivo(BPATH)
    TOKEN = leer_archivo(TOKENPATH)
    
    log(f"Token: {TOKEN[:8]}..." if TOKEN else "Token no encontrado")
    log(f"Teléfono B: {TELEFONO_B}")
    log("Bot escuchando en puerto 9090...")
    
    app.run(host="0.0.0.0", port=9090, debug=False, threaded=True)

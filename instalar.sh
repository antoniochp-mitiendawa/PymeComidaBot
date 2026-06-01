#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  MI TIENDA WA — Sistema de Atención por WhatsApp
#  Instalador completo para Termux + WuzAPI
#  github.com/TU_USUARIO/mitiendawa
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
info() { echo -e "${BLUE}▶${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
err()  { echo -e "${RED}✗ ERROR:${NC} $1"; exit 1; }
ask()  { echo -e "${CYAN}?${NC} $1"; }

clear
echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║         MI TIENDA WA                     ║"
echo "  ║   Sistema de Atención por WhatsApp       ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
sleep 1

# ── PASO 1: Permisos de almacenamiento ─────────────────────
info "Solicitando permisos de almacenamiento..."
termux-setup-storage 2>/dev/null || true
sleep 2

# ── PASO 2: Actualizar Termux ───────────────────────────────
info "Actualizando Termux..."
pkg update -y -o Dpkg::Options::="--force-confnew" 2>/dev/null | tail -3
ok "Termux actualizado"

# ── PASO 3: Instalar dependencias del sistema ───────────────
info "Instalando dependencias del sistema..."
pkg install -y \
    python \
    python-pip \
    wget \
    curl \
    jq \
    sqlite \
    openssl \
    openssl-tool \
    termux-api \
    2>/dev/null | tail -5
ok "Dependencias del sistema instaladas"

# ── PASO 4: Instalar librerías Python ──────────────────────
info "Instalando librerías Python..."
pip install --quiet flask requests 2>/dev/null
ok "Librerías Python instaladas"

# ── PASO 5: Crear estructura de directorios ─────────────────
info "Creando estructura de directorios..."
BASEDIR="$HOME/mitiendawa"
WUZDIR="$HOME/wuzapi"
AUDIODIR="$BASEDIR/audios"
DBDIR="$BASEDIR/data"

mkdir -p "$BASEDIR" "$WUZDIR" "$AUDIODIR" "$DBDIR"
ok "Directorios creados"

# ── PASO 6: Descargar WuzAPI ────────────────────────────────
info "Descargando WuzAPI..."
ARCH=$(uname -m)
if [[ "$ARCH" == "aarch64" ]]; then
    WUZURL="https://raw.githubusercontent.com/antoniochp-mitiendawa/PymeComidaBot/main/wuzapi"
else
    WUZURL="https://raw.githubusercontent.com/antoniochp-mitiendawa/PymeComidaBot/main/wuzapi"
fi

if wget -q --show-progress -O "$WUZDIR/wuzapi" "$WUZURL" 2>/dev/null; then
    chmod +x "$WUZDIR/wuzapi"
    ok "WuzAPI descargado"
else
    warn "No se pudo descargar WuzAPI automáticamente."
    warn "Descarga manual: https://github.com/asternic/wuzapi/releases"
    warn "Coloca el binario en: $WUZDIR/wuzapi y ejecuta: chmod +x $WUZDIR/wuzapi"
fi

# ── PASO 7: Generar token único ─────────────────────────────
TOKEN=$(openssl rand -hex 16)

# ── PASO 8: Configurar WuzAPI ───────────────────────────────
info "Configurando WuzAPI..."
cat > "$WUZDIR/.env" << ENVEOF
WUZAPI_ADMIN_TOKEN=$TOKEN
TZ=America/Mexico_City
WUZAPI_GLOBAL_WEBHOOK=http://localhost:9090/webhook
WEBHOOK_FORMAT=json
WUZAPI_PORT=8080
ENVEOF
ok "WuzAPI configurado"

# ── PASO 9: Scripts de control WuzAPI ──────────────────────
cat > "$WUZDIR/iniciar.sh" << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/wuzapi
while true; do
    ./wuzapi -skipmedia -logtype json >> ~/wuzapi/wuzapi.log 2>&1
    echo "[$(date)] WuzAPI reiniciando..." >> ~/wuzapi/wuzapi.log
    sleep 5
done
EOF

cat > "$WUZDIR/detener.sh" << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
pkill -f wuzapi 2>/dev/null && echo "WuzAPI detenido" || echo "WuzAPI no estaba activo"
EOF

chmod +x "$WUZDIR/iniciar.sh" "$WUZDIR/detener.sh"

# ── PASO 10: Descargar bot principal ───────────────────────
info "Descargando bot principal..."
BOT_URL="https://raw.githubusercontent.com/antoniochp-mitiendawa/PymeComidaBot/main/Bot.py"

if wget -q -O "$BASEDIR/bot.py" "$BOT_URL" 2>/dev/null; then
    ok "Bot descargado desde GitHub"
else
    warn "No se pudo descargar bot.py desde GitHub."
    warn "Coloca bot.py manualmente en: $BASEDIR/bot.py"
fi

# ── PASO 11: Script maestro de inicio ──────────────────────
cat > "$HOME/iniciar_mitiendawa.sh" << MASTEREOF
#!/data/data/com.termux/files/usr/bin/bash
echo ""
echo "  Iniciando MI TIENDA WA..."
echo ""

# Iniciar WuzAPI en background
nohup bash ~/wuzapi/iniciar.sh > /dev/null 2>&1 &
sleep 3

# Iniciar bot en background
nohup python ~/mitiendawa/bot.py > ~/mitiendawa/bot.log 2>&1 &
sleep 2

echo "  ✓ Sistema iniciado correctamente"
echo "  ✓ WuzAPI activo en puerto 8080"
echo "  ✓ Bot activo en puerto 9090"
echo ""
echo "  Log del bot:   tail -f ~/mitiendawa/bot.log"
echo "  Log WuzAPI:    tail -f ~/wuzapi/wuzapi.log"
echo ""
MASTEREOF

chmod +x "$HOME/iniciar_mitiendawa.sh"

# ── PASO 12: Guardar token para uso del bot ─────────────────
echo "$TOKEN" > "$DBDIR/token.txt"
ok "Token generado y guardado"

# ── PASO 13: Termux wake-lock ──────────────────────────────
termux-wake-lock 2>/dev/null || true

# ── PASO 14: Iniciar WuzAPI para emparejamiento ────────────
info "Iniciando WuzAPI..."
nohup bash "$WUZDIR/iniciar.sh" > /dev/null 2>&1 &
sleep 4

# ── PASO 15: EMPAREJAMIENTO CON WHATSAPP ───────────────────
echo ""
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo -e "${BOLD}  PASO: EMPAREJAMIENTO CON WHATSAPP       ${NC}"
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo ""
ask "Ingresa el número de teléfono de ESTE dispositivo (Teléfono A)"
ask "Formato: código de país + número, sin + ni espacios"
ask "Ejemplo para México: 5215512345678"
echo ""
read -p "  Número: " TELEFONO_A

if [[ -z "$TELEFONO_A" ]]; then
    err "Debes ingresar un número de teléfono"
fi

echo "$TELEFONO_A" > "$DBDIR/telefono_a.txt"

info "Creando sesión en WuzAPI..."
sleep 2

# Conectar sesión
CONNECT_RESP=$(curl -s -X POST \
    -H "Token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"Subscribe":["Message"],"Immediate":false}' \
    http://localhost:8080/session/connect 2>/dev/null)

sleep 2

# Solicitar código de emparejamiento
info "Solicitando código de emparejamiento..."
PAIR_RESP=$(curl -s \
    -H "Token: $TOKEN" \
    "http://localhost:8080/session/pairphone?phone=$TELEFONO_A" 2>/dev/null)

PAIR_CODE=$(echo "$PAIR_RESP" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    code = d.get('PairCode') or d.get('code') or d.get('Code') or ''
    print(code)
except:
    print('')
" 2>/dev/null)

echo ""
if [[ -n "$PAIR_CODE" ]]; then
    echo -e "${BOLD}  ══════════════════════════════════${NC}"
    echo -e "${BOLD}  CÓDIGO DE EMPAREJAMIENTO:         ${NC}"
    echo ""
    echo -e "${GREEN}${BOLD}       $PAIR_CODE       ${NC}"
    echo ""
    echo -e "${BOLD}  ══════════════════════════════════${NC}"
    echo ""
    echo "  1. Abre WhatsApp en el Teléfono A"
    echo "  2. Ve a: Menú → Dispositivos vinculados"
    echo "  3. Toca 'Vincular dispositivo'"
    echo "  4. Elige 'Vincular con número de teléfono'"
    echo "  5. Ingresa el código de arriba"
    echo ""
else
    warn "No se pudo obtener el código automáticamente."
    warn "Intenta manualmente: curl -H 'Token: $TOKEN' http://localhost:8080/session/pairphone?phone=$TELEFONO_A"
fi

echo ""
read -p "  Presiona ENTER cuando hayas vinculado WhatsApp..."

# ── PASO 16: REGISTRAR TELÉFONO B (DUEÑO) ──────────────────
echo ""
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo -e "${BOLD}  PASO: NÚMERO DEL DUEÑO (TELÉFONO B)    ${NC}"
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo ""
ask "Ingresa el número del dueño del negocio (Teléfono B)"
ask "Este número podrá dar instrucciones al sistema"
ask "Formato: 5215512345678"
echo ""
read -p "  Número del dueño: " TELEFONO_B

if [[ -z "$TELEFONO_B" ]]; then
    err "Debes ingresar el número del dueño"
fi

echo "$TELEFONO_B" > "$DBDIR/telefono_b.txt"
ok "Número del dueño registrado"

# ── PASO 17: Iniciar bot e iniciar onboarding ───────────────
info "Iniciando bot principal..."
nohup python "$BASEDIR/bot.py" > "$BASEDIR/bot.log" 2>&1 &
sleep 3

# Registrar webhook en WuzAPI
curl -s -X PUT \
    -H "Token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"WebhookURL":"http://localhost:9090/webhook"}' \
    http://localhost:8080/session/status > /dev/null 2>/dev/null

sleep 2

# Enviar mensaje de bienvenida al dueño
MENSAJE_BIENVENIDA="¡Hola! 👋 Soy el sistema *Mi Tienda WA*. Tu número ha sido registrado correctamente como administrador. ✅\n\nAhora vamos a configurar tu negocio. Te haré unas preguntas sencillas.\n\nResponde *INICIAR* cuando estés listo."

curl -s -X POST \
    -H "Token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"Phone\":\"$TELEFONO_B\",\"Body\":\"$MENSAJE_BIENVENIDA\"}" \
    http://localhost:8080/chat/send/text > /dev/null 2>/dev/null

# ── RESUMEN FINAL ───────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   ✅ INSTALACIÓN COMPLETADA              ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "  Teléfono A (Bot):   $TELEFONO_A"
echo "  Teléfono B (Dueño): $TELEFONO_B"
echo ""
echo "  Se ha enviado un mensaje de bienvenida al"
echo "  Teléfono B para iniciar la configuración."
echo ""
echo "  Para iniciar el sistema en el futuro:"
echo "  bash ~/iniciar_mitiendawa.sh"
echo ""
echo "  Para ver el log en tiempo real:"
echo "  tail -f ~/mitiendawa/bot.log"
echo ""

#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  MI TIENDA WA — Instalador completo
#  Un solo comando, sin intervención manual
# ============================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok() { echo -e "${GREEN}✓${NC} $1"; }
info() { echo -e "${BLUE}▶${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
err() { echo -e "${RED}✗ ERROR:${NC} $1"; exit 1; }
ask() { echo -e "${CYAN}?${NC} $1"; }

clear
echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║         MI TIENDA WA                     ║"
echo "  ║   Instalador automático                  ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
sleep 1

# ── Verificar Termux ─────────────────────────────────────────
if [[ ! -d /data/data/com.termux ]]; then
    err "Este script solo funciona en Termux para Android"
fi

# ── Solicitar permisos de almacenamiento ────────────────────
info "Solicitando permisos de almacenamiento..."
termux-setup-storage 2>/dev/null || true
sleep 2

# ── Actualizar lista de paquetes (solo update, no upgrade) ──
info "Actualizando lista de paquetes..."
pkg update -y
ok "Lista de paquetes actualizada"

# ── Instalar dependencias (sin upgrade previo) ──────────────
info "Instalando dependencias..."

pkg install -y python
pkg install -y python-pip
pkg install -y wget
pkg install -y curl
pkg install -y jq
pkg install -y sqlite
pkg install -y openssl
pkg install -y termux-api
pkg install -y git

ok "Dependencias instaladas"

# ── Instalar librerías Python ───────────────────────────────
info "Instalando librerías Python..."
pip install --upgrade pip
pip install flask requests
ok "Librerías Python instaladas"

# ── Crear estructura de directorios ─────────────────────────
info "Creando directorios..."
BASEDIR="$HOME/mitiendawa"
WUZDIR="$HOME/wuzapi"
AUDIODIR="$BASEDIR/audios"
DBDIR="$BASEDIR/data"

mkdir -p "$BASEDIR" "$WUZDIR" "$AUDIODIR" "$DBDIR"
ok "Directorios creados"

# ── Descargar WuzAPI ────────────────────────────────────────
info "Descargando WuzAPI..."
ARCH=$(uname -m)
if [[ "$ARCH" == "aarch64" ]]; then
    WUZURL="https://github.com/asternic/wuzapi/releases/latest/download/wuzapi-android-arm64"
else
    WUZURL="https://github.com/asternic/wuzapi/releases/latest/download/wuzapi-android-arm"
fi

wget -O "$WUZDIR/wuzapi" "$WUZURL"
if [[ $? -ne 0 ]]; then
    err "No se pudo descargar WuzAPI"
fi

chmod +x "$WUZDIR/wuzapi"
ok "WuzAPI descargado"

# ── Generar token único ─────────────────────────────────────
TOKEN=$(openssl rand -hex 16)

# ── Configurar WuzAPI ───────────────────────────────────────
info "Configurando WuzAPI..."
cat > "$WUZDIR/.env" << ENVEOF
WUZAPI_ADMIN_TOKEN=$TOKEN
TZ=America/Mexico_City
WUZAPI_GLOBAL_WEBHOOK=http://localhost:9090/webhook
WEBHOOK_FORMAT=json
WUZAPI_PORT=8080
ENVEOF
ok "WuzAPI configurado"

# ── Script para iniciar WuzAPI ──────────────────────────────
cat > "$WUZDIR/iniciar.sh" << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/wuzapi
while true; do
    ./wuzapi -skipmedia -logtype json >> ~/wuzapi/wuzapi.log 2>&1
    echo "[$(date)] WuzAPI reiniciando..." >> ~/wuzapi/wuzapi.log
    sleep 5
done
EOF

chmod +x "$WUZDIR/iniciar.sh"
ok "Script de inicio de WuzAPI creado"

# ── Descargar archivos desde GitHub ─────────────────────────
info "Descargando bot.py..."
wget -O "$BASEDIR/bot.py" "https://raw.githubusercontent.com/antoniochp-mitiendawa/PymeComidaBot/main/bot.py"
if [[ $? -ne 0 ]]; then
    err "No se pudo descargar bot.py"
fi
ok "bot.py descargado"

info "Descargando watchdog.sh..."
wget -O "$BASEDIR/watchdog.sh" "https://raw.githubusercontent.com/antoniochp-mitiendawa/PymeComidaBot/main/watchdog.sh"
if [[ $? -ne 0 ]]; then
    err "No se pudo descargar watchdog.sh"
fi
chmod +x "$BASEDIR/watchdog.sh"
ok "watchdog.sh descargado"

# ── Guardar token ───────────────────────────────────────────
echo "$TOKEN" > "$DBDIR/token.txt"

# ── Solicitar número del teléfono A ─────────────────────────
echo ""
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo -e "${BOLD}  PASO 1: TELÉFONO QUE ATENDERÁ CLIENTES  ${NC}"
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo ""
ask "Ingresa el número de teléfono de ESTE dispositivo (Teléfono A)"
ask "Formato: código de país + número, sin + ni espacios"
ask "Ejemplo México: 5215512345678"
echo ""
read -p "  Número: " TELEFONO_A

if [[ -z "$TELEFONO_A" ]]; then
    err "Debes ingresar un número"
fi

echo "$TELEFONO_A" > "$DBDIR/telefono_a.txt"
ok "Teléfono A guardado"

# ── Solicitar número del teléfono B ─────────────────────────
echo ""
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo -e "${BOLD}  PASO 2: NÚMERO DEL DUEÑO (TELÉFONO B)   ${NC}"
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo ""
ask "Ingresa tu número personal (Teléfono B)"
ask "Este número podrá dar instrucciones al sistema"
ask "Ejemplo: 5215512345678"
echo ""
read -p "  Número: " TELEFONO_B

if [[ -z "$TELEFONO_B" ]]; then
    err "Debes ingresar tu número"
fi

echo "$TELEFONO_B" > "$DBDIR/telefono_b.txt"
ok "Teléfono B guardado"

# ── Iniciar WuzAPI ──────────────────────────────────────────
info "Iniciando WuzAPI..."
nohup bash "$WUZDIR/iniciar.sh" > /dev/null 2>&1 &
sleep 8

# ── Emparejamiento con WhatsApp ─────────────────────────────
info "Solicitando código de emparejamiento..."
PAIR_RESP=$(curl -s -X GET \
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
    echo -e "${BOLD}  ══════════════════════════════════════${NC}"
    echo -e "${BOLD}  CÓDIGO DE EMPAREJAMIENTO:             ${NC}"
    echo ""
    echo -e "${GREEN}${BOLD}       $PAIR_CODE       ${NC}"
    echo ""
    echo -e "${BOLD}  ══════════════════════════════════════${NC}"
    echo ""
    echo "  1. Abre WhatsApp en el Teléfono A"
    echo "  2. Ve a: Menú → Dispositivos vinculados"
    echo "  3. Toca 'Vincular dispositivo'"
    echo "  4. Elige 'Vincular con número de teléfono'"
    echo "  5. Ingresa el código de arriba"
    echo ""
else
    warn "No se pudo obtener el código automáticamente."
fi

echo ""
read -p "  Presiona ENTER cuando hayas vinculado WhatsApp..."
ok "Emparejamiento confirmado"

# ── Iniciar el sistema completo ─────────────────────────────
info "Iniciando bot y watchdog..."
nohup python "$BASEDIR/bot.py" > "$BASEDIR/bot.log" 2>&1 &
sleep 3
nohup bash "$BASEDIR/watchdog.sh" > /dev/null 2>&1 &
sleep 2

# ── Enviar mensaje de bienvenida al dueño ───────────────────
ONBOARD_MSG="🎉 *¡Instalación completada!*

Ahora vamos a configurar tu negocio.

Responde *INICIAR* para comenzar con el nombre de tu negocio, dirección, horarios y para enviar los audios de tu menú.

Puedes usar el comando *COMANDOS* para ver todo lo que puedes hacer."

curl -s -X POST \
    -H "Token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"Phone\":\"$TELEFONO_B\",\"Body\":\"$ONBOARD_MSG\"}" \
    http://localhost:8080/chat/send/text > /dev/null 2>&1

# ── Configurar wake-lock persistente ────────────────────────
info "Configurando wake-lock persistente..."
if ! grep -q "termux-wake-lock" ~/.bashrc 2>/dev/null; then
    echo "termux-wake-lock" >> ~/.bashrc
fi
termux-wake-lock
ok "Wake-lock configurado"

# ── Configurar inicio automático ────────────────────────────
info "Configurando inicio automático..."
if ! grep -q "iniciar_mitiendawa.sh" ~/.bashrc 2>/dev/null; then
    echo "bash ~/iniciar_mitiendawa.sh" >> ~/.bashrc
fi
ok "Inicio automático configurado"

# ── Resumen final ───────────────────────────────────────────
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
echo "  Se ha enviado un mensaje a tu WhatsApp"
echo "  para iniciar la configuración."
echo ""
echo "  El sistema arrancará automáticamente cada vez"
echo "  que abras Termux."
echo ""

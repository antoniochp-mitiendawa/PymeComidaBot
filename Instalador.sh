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

# ── Actualizar repositorios (sin upgrade para no matar el shell) ──
info "Actualizando repositorios..."
pkg update -y -o Dpkg::Options::="--force-confnew" 2>/dev/null || true
ok "Repositorios actualizados"

# ── Instalar dependencias (una por una para evitar fallos) ──
info "Instalando dependencias..."

for pkg in python python-pip wget curl jq sqlite openssl termux-api git; do
    echo "  Instalando $pkg..."
    pkg install -y $pkg
done

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
    err "No se pudo descargar WuzAPI. Verifica tu conexión a internet."
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
wget -O "$BASEDIR/bot.py" "https://raw.githubusercontent.com/antoniochp-mitiendawa/PymeComidaBot/main/Bot.py"
if [[ $? -ne 0 ]]; then
    err "No se pudo descargar bot.py"
fi
ok "bot.py descargado"

info "Descargando watchdog.sh..."
wget -O "$BASEDIR/watchdog.sh" "https://raw.githubusercontent.com/antoniochp-mitiendawa/PymeComidaBot/main/Watchdog.sh"
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
ask "Ejemplo para México: 5215512345678"
echo ""
read -p "  Número: " TELEFONO_A

if [[ -z "$TELEFONO_A" ]]; then
    err "Debes ingresar un número de teléfono"
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
ask "Formato: 5215512345678"
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
sleep 5

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

# ── Verificar webhook ───────────────────────────────────────
info "Verificando webhook..."
sleep 3

# Iniciar el bot temporalmente
info "Iniciando bot para verificar webhook..."
nohup python "$BASEDIR/bot.py" > "$BASEDIR/bot.log" 2>&1 &
sleep 5

# Enviar mensaje de prueba al dueño
TEST_MSG="✅ Webhook funcionando correctamente

El sistema MI TIENDA WA está listo para atender a tus clientes.

Ahora vamos a configurar tu negocio. Responde INICIAR cuando estés listo."

curl -s -X POST \
    -H "Token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"Phone\":\"$TELEFONO_B\",\"Body\":\"$TEST_MSG\"}" \
    http://localhost:8080/chat/send/text > /dev/null 2>&1

echo ""
ask "¿Recibiste el mensaje de confirmación en tu WhatsApp (Teléfono B)? (s/n)"
read -p "  Respuesta: " CONFIRMACION

if [[ "$CONFIRMACION" != "s" && "$CONFIRMACION" != "S" ]]; then
    warn "No se recibió confirmación. Revisando logs..."
    tail -10 "$BASEDIR/bot.log"
    err "El webhook no funciona. Revisa tu conexión."
fi

ok "Webhook verificado correctamente"

# ── Matar el bot temporal ───────────────────────────────────
pkill -f bot.py 2>/dev/null
sleep 2

# ── Crear script maestro de inicio ──────────────────────────
cat > "$HOME/iniciar_mitiendawa.sh" << 'MASTEREOF'
#!/data/data/com.termux/files/usr/bin/bash
BASEDIR="$HOME/mitiendawa"
WUZDIR="$HOME/wuzapi"
pkill -f wuzapi 2>/dev/null
pkill -f bot.py 2>/dev/null
pkill -f watchdog.sh 2>/dev/null
sleep 2
nohup bash "$WUZDIR/iniciar.sh" > /dev/null 2>&1 &
sleep 3
nohup bash "$BASEDIR/watchdog.sh" > /dev/null 2>&1 &
sleep 2
nohup python "$BASEDIR/bot.py" > "$BASEDIR/bot.log" 2>&1 &
echo "✅ MI TIENDA WA iniciado"
MASTEREOF

chmod +x "$HOME/iniciar_mitiendawa.sh"

# ── Crear script para detener todo ──────────────────────────
cat > "$HOME/detener_mitiendawa.sh" << 'STOPEOF'
#!/data/data/com.termux/files/usr/bin/bash
pkill -f wuzapi 2>/dev/null
pkill -f bot.py 2>/dev/null
pkill -f watchdog.sh 2>/dev/null
echo "✅ MI TIENDA WA detenido"
STOPEOF

chmod +x "$HOME/detener_mitiendawa.sh"

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

# ── Iniciar el sistema completo ─────────────────────────────
info "Iniciando sistema completo..."
bash ~/iniciar_mitiendawa.sh
sleep 5

# ── Enviar mensaje de onboarding al dueño ───────────────────
ONBOARD_MSG="🎉 *¡Instalación completada!*

Ahora vamos a configurar tu negocio.

Responde *INICIAR* para comenzar con el nombre de tu negocio, dirección, horarios y para enviar los audios de tu menú.

Puedes usar el comando *COMANDOS* para ver todo lo que puedes hacer."

curl -s -X POST \
    -H "Token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"Phone\":\"$TELEFONO_B\",\"Body\":\"$ONBOARD_MSG\"}" \
    http://localhost:8080/chat/send/text > /dev/null 2>&1

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
echo "  para iniciar la configuración del negocio."
echo ""
echo "  Para detener el sistema: bash ~/detener_mitiendawa.sh"
echo "  Para reiniciar:         bash ~/iniciar_mitiendawa.sh"
echo ""
echo "  El sistema arrancará automáticamente cada vez"
echo "  que abras Termux."
echo ""

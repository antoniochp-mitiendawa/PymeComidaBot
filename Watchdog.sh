#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  MI TIENDA WA — Watchdog
#  Monitorea y reinicia automáticamente bot.py y Wuzapi
# ============================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
err()  { echo -e "${RED}✗${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }

BASEDIR="$HOME/mitiendawa"
WUZDIR="$HOME/wuzapi"
LOGPATH="$BASEDIR/watchdog.log"
TOKEN=$(cat "$BASEDIR/data/token.txt" 2>/dev/null)
TELEFONO_B=$(cat "$BASEDIR/data/telefono_b.txt" 2>/dev/null)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOGPATH"
}

notificar_dueno() {
    local msg="$1"
    if [[ -n "$TOKEN" && -n "$TELEFONO_B" ]]; then
        curl -s -X POST \
            -H "Token: $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"Phone\":\"$TELEFONO_B\",\"Body\":\"$msg\"}" \
            http://localhost:8080/chat/send/text > /dev/null 2>&1
    fi
}

log "Watchdog iniciado"

while true; do
    # Verificar Wuzapi
    if ! pgrep -f "wuzapi" > /dev/null; then
        warn "Wuzapi no está corriendo. Reiniciando..."
        log "Wuzapi caído, reiniciando"
        nohup bash "$WUZDIR/iniciar.sh" > /dev/null 2>&1 &
        sleep 5
        notificar_dueno "⚠️ *Watchdog:* Wuzapi se reinició automáticamente."
        ok "Wuzapi reiniciado"
    fi

    # Verificar bot.py
    if ! pgrep -f "python.*bot.py" > /dev/null; then
        warn "bot.py no está corriendo. Reiniciando..."
        log "bot.py caído, reiniciando"
        nohup python "$BASEDIR/bot.py" > "$BASEDIR/bot.log" 2>&1 &
        sleep 3
        notificar_dueno "⚠️ *Watchdog:* El bot se reinició automáticamente."
        ok "bot.py reiniciado"
    fi

    sleep 30
done

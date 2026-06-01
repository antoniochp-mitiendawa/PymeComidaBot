#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  MI TIENDA WA — Iniciar todo el sistema
#  Arranca Wuzapi, watchdog y el bot
# ============================================================

GREEN='\033[0;32m'
NC='\033[0m'

ok() { echo -e "${GREEN}✓${NC} $1"; }

BASEDIR="$HOME/mitiendawa"
WUZDIR="$HOME/wuzapi"

# Detener procesos existentes
pkill -f wuzapi 2>/dev/null
pkill -f bot.py 2>/dev/null
pkill -f watchdog.sh 2>/dev/null
sleep 2

# Iniciar Wuzapi
nohup bash "$WUZDIR/iniciar.sh" > /dev/null 2>&1 &
sleep 3
ok "Wuzapi iniciado"

# Iniciar watchdog
nohup bash "$BASEDIR/watchdog.sh" > /dev/null 2>&1 &
sleep 2
ok "Watchdog iniciado"

# Iniciar bot
nohup python "$BASEDIR/bot.py" > "$BASEDIR/bot.log" 2>&1 &
sleep 2
ok "Bot iniciado"

echo ""
echo "✅ MI TIENDA WA — Sistema funcionando"
echo "   Para ver logs: tail -f ~/mitiendawa/bot.log"
echo "   Para detener: bash ~/detener_mitiendawa.sh"

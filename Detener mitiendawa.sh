#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  MI TIENDA WA — Detener todo el sistema
#  Detiene Wuzapi, watchdog y el bot
# ============================================================

GREEN='\033[0;32m'
NC='\033[0m'

ok() { echo -e "${GREEN}✓${NC} $1"; }

# Detener todos los procesos
pkill -f wuzapi 2>/dev/null
pkill -f bot.py 2>/dev/null
pkill -f watchdog.sh 2>/dev/null

sleep 1
ok "Wuzapi detenido"
ok "Bot detenido"
ok "Watchdog detenido"

echo ""
echo "✅ MI TIENDA WA — Sistema detenido"
echo "   Para iniciar de nuevo: bash ~/iniciar_mitiendawa.sh"

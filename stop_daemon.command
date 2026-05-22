#!/bin/bash
# 语音输入守护进程停止脚本
cd "$(dirname "$0")"
SCRIPT_DIR="$(dirname "$0")"

pkill -f "$SCRIPT_DIR/voice_daemon.py" 2>/dev/null
python3 -c "import os; os.path.exists('/tmp/voice_daemon.pid') and os.remove('/tmp/voice_daemon.pid')" 2>/dev/null

echo "语音输入已停止"

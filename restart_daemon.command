#!/bin/bash
# 语音输入守护进程重启脚本
cd "$(dirname "$0")"
SCRIPT_DIR="$(dirname "$0")"

# 杀所有旧进程 & 清理 PID 文件
pkill -f "$SCRIPT_DIR/voice_daemon.py" 2>/dev/null
python3 -c "import os; os.path.exists('/tmp/voice_daemon.pid') and os.remove('/tmp/voice_daemon.pid')" 2>/dev/null

sleep 0.5

# 启动新进程
nohup python3 "$SCRIPT_DIR/voice_daemon.py" > /tmp/voice_daemon.log 2>&1 &
sleep 1
PID=$(pgrep -f "$SCRIPT_DIR/voice_daemon.py")
echo "语音输入已重启 (PID $PID)"

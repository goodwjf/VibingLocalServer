#!/bin/bash
# 语音输入守护进程启动脚本
cd "$(dirname "$0")"
nohup python3 "$(dirname "$0")/voice_daemon.py" > /tmp/voice_daemon.log 2>&1 &
echo "语音输入已启动 (PID $(pgrep -f voice_daemon))"

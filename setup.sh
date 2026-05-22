#!/bin/bash
# ============================================
# Voice Input — 一键环境配置脚本
# ============================================
set -e

echo "=============================="
echo " Voice Input 环境配置"
echo "=============================="

# 1. 安装 Python 依赖
echo ""
echo "[1/3] 安装 Python 依赖..."
pip3 install --upgrade sherpa_onnx sounddevice pynput numpy

# 2. 确保模型目录存在
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo ""
echo "[2/3] 创建模型目录..."
mkdir -p "$SCRIPT_DIR/models"

# 3. 打印后续步骤
echo ""
echo "[3/3] 完成!"
echo ""
echo "=============================="
echo " 接下来还需要："
echo "=============================="
echo ""
echo "1. 下载 SenseVoice 模型（~1GB）："
echo "   curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2 | tar xj -C \$SCRIPT_DIR/models/"
echo ""
echo "2. （可选）下载标点模型（~266MB）："
echo "   curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/punctuation-models/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12.tar.bz2 | tar xj -C \$SCRIPT_DIR/models/"
echo ""
echo "3. 授予终端辅助功能权限："
echo "   系统设置 → 隐私与安全性 → 辅助功能 → 添加「终端.app」"
echo ""
echo "4. 启动："
echo "   双击 start_daemon.command"
echo ""
echo "更多配置见 config.json（快捷键、模型路径等）"
echo "=============================="

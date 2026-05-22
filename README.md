# Voice Input — 本地语音输入工具

按住右 Option 说话，松开自动识别并粘贴。基于 SenseVoice + macOS Accessibility，完全离线。

## 从零搭建（分享给朋友）

```bash
# 1. 安装 Python 依赖
pip3 install sherpa_onnx sounddevice pynput numpy

# 2. 下载 SenseVoice 模型（~1GB）
curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2 | \
  tar xj -C ~/Library/Application\ Support/Memo/models/

# 3. （可选）下载标点模型（~266MB）
curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/punctuation-models/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12.tar.bz2 | \
  tar xj -C /path/to/VibingLocalServer/models/

# 4. 授予终端辅助功能权限
#    系统设置 → 隐私与安全性 → 辅助功能 → 添加「终端.app」

# 5. 启动
open /path/to/VibingLocalServer/start_daemon.command
```

或双击 `setup.sh` 一键安装依赖，然后手动下载模型。

## 使用

| 操作 | 方式 |
|---|---|
| 启动 | 双击 `start_daemon.command` |
| 停止 | 双击 `stop_daemon.command` |
| 重启 | 双击 `restart_daemon.command` |
| 输入 | 按住右 Option → 说话 → 松开 → 自动粘贴 |
| 开机自启 | 系统设置 → 通用 → 登录项 → 添加 `start_daemon.command` |

**提示音**: 按住时短促提示音，粘贴完成后清脆完成音。

## 管理命令

```bash
# 启动
nohup python3 ~/Documents/VibingLocalServer/voice_daemon.py > /tmp/voice_daemon.log 2>&1 &

# 停止
python3 ~/Documents/VibingLocalServer/voice_daemon.py --stop

# 查看日志
tail -f /tmp/voice_daemon.log
```

## 配置

编辑 `config.json`：

```json
{
  "models_dir": "~/Library/Application Support/Memo/models",
  "model_subdir": "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17",
  "model_filename": "model.int8.onnx",
  "punctuation_model_dir": "/path/to/models/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12",
  "hotkey": "alt_gr",
  "sample_rate": 16000,
  "pid_file": "/tmp/voice_daemon.pid",
  "ollama_enabled": false,
  "ollama_model": "gemma4-uncensored:latest"
}
```

| 字段 | 说明 |
|---|---|
| `models_dir` | SenseVoice 模型根目录 |
| `model_subdir` | 模型子文件夹名 |
| `model_filename` | ONNX 模型文件名 |
| `punctuation_model_dir` | 标点模型目录（可选，留空则不加标点） |
| `hotkey` | 快捷键（见下表） |
| `sample_rate` | 录音采样率，固定 16000 |
| `pid_file` | 存守护进程 PID，`--stop` 用它找到进程并关闭 |
| `ollama_enabled` | 是否用 Ollama 修正识别结果（速度较慢） |
| `ollama_model` | Ollama 模型名 |

快捷键 `hotkey` 可选值：

| 值 | 按键 |
|---|---|
| `alt_gr` | 右 Option（默认） |
| `alt` | 左 Option |
| `ctrl` | Control |
| `cmd` | Command |
| `shift` | Shift |
| `f19` | F19（配合 Karabiner 自定义） |

## 文件

| 文件 | 作用 |
|---|---|
| `voice_daemon.py` | 守护进程：监听按键、录音、识别、加标点、粘贴 |
| `start_daemon.command` | 启动快捷方式 |
| `stop_daemon.command` | 停止（杀所有进程实例） |
| `restart_daemon.command` | 一键重启 |
| `config.json` | 配置文件 |
| `setup.sh` | 一键安装 Python 依赖 |

## 环境

- macOS 14+
- Python 3.10+
- 需要**辅助功能**权限：系统设置 → 隐私与安全性 → 辅助功能 → 添加「终端.app」
- 模型文件（SenseVoice + 可选标点模型）

## 日志

```bash
tail -f /tmp/voice_daemon.log
```

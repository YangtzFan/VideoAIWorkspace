# audio_to_txt.py 使用说明

`scripts/audio_to_txt.py` 使用 faster-whisper 批量转写音频。它默认加载多语言 `small` 模型，优先使用 CUDA 和 `float16` 精度；CUDA 不可用时自动切换到 CPU 和 `int8` 精度。程序还会通过语音活动检测过滤长静音。

## 基本用法

在项目根目录运行：

```powershell
python scripts\audio_to_txt.py
```

默认读取 `audios`，将 UTF-8 TXT 写入 `texts`。支持 `.mp3`、`.wav`、`.m4a`、`.flac`、`.ogg`、`.opus` 和 `.aac`。

首次使用某个模型时会从 Hugging Face 下载文件。下载完成后，后续运行使用本机缓存。默认 `small` 模型在速度和准确率之间较均衡；模型越大，通常越准确，也越慢、占用更多内存。

Windows 上使用 NVIDIA GPU 时安装 CUDA 运行库：

```powershell
python -m pip install -r requirements-gpu.txt
```

该依赖会安装项目测试过的 CUDA 12.8 cuBLAS 和 CUDA Runtime，约需额外下载 568 MB。CTranslate2 自带 cuDNN 9，脚本会自动注册 Python 包中的 DLL 目录并预加载运行库，因此无需手动修改系统 `PATH` 或安装完整 CUDA Toolkit。显卡驱动需要支持 CUDA 12.8，可通过 `nvidia-smi` 查看驱动支持的 CUDA 版本。

## 参数

```text
--input-dir PATH          音频输入目录
--output-dir PATH         TXT 输出目录
--model NAME_OR_PATH      模型名称或本地模型目录，默认 small
--language CODE           zh、en 等语言代码；默认 auto
--device auto|cpu|cuda    推理设备，默认 auto
--compute-type TYPE       自定义计算精度；自动选择时 CUDA 使用 float16，CPU 使用 int8
--overwrite               覆盖已有 TXT
-h, --help                显示帮助
```

常用示例：

```powershell
# 固定中文并覆盖旧结果，设备仍自动选择
python scripts\audio_to_txt.py --language zh --overwrite

# 强制使用 CPU
python scripts\audio_to_txt.py --device cpu

# 强制使用 CUDA；失败时报告错误，不自动回退
python scripts\audio_to_txt.py --device cuda

# 使用更快、更省内存但准确率较低的模型
python scripts\audio_to_txt.py --model base

# 使用本地模型，适合离线环境
python scripts\audio_to_txt.py --model D:\Models\faster-whisper-small
```

## 自动设备选择

默认的 `--device auto` 先检查 CTranslate2 是否能发现 CUDA 设备。发现设备后使用 CUDA；如果 CUDA 在模型加载或实际推理时因为显存、cuBLAS、cuDNN 等问题失败，程序会加载 CPU 模型并重新转写当前文件。未发现 CUDA 设备时直接使用 CPU。

自动回退到 CPU 时使用 `int8` 精度，不沿用可能只适合 CUDA 的 `--compute-type`。显式指定 `--device cpu` 或 `--device cuda` 时，程序严格使用指定设备，不执行自动回退。

## 输出格式和错误处理

每个识别片段占一行，文件使用 UTF-8 编码。例如 `audios/example.mp3` 生成 `texts/example.txt`。脚本先写临时文件，转写成功后才替换正式输出；已有文本默认跳过。单个音频失败不会阻止后续音频处理，但最终退出码为 `1`。

## GPU 说明

检测到 NVIDIA 显卡并不代表 CUDA 推理环境已经完整。faster-whisper 使用 CTranslate2，CUDA 模式需要相匹配的 NVIDIA 驱动、cuBLAS、CUDA Runtime 和 cuDNN。安装 `requirements-gpu.txt` 后仍失败时，请显式运行 `python scripts\audio_to_txt.py --device cuda --overwrite` 查看具体错误；默认自动模式会在 CUDA 失败时回退到 CPU。

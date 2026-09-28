# Packaging — 打包与分发

把 PySide6 客户端打成各平台可分发产物。脚本放 `scripts/`，产物与配置不进 Git。

## 选型

| 方案 | 结论 |
|------|------|
| **pyside6-deploy** | 首选。官方工具，Nuitka 封装，自动生成 `pysidedeploy.spec` |
| Nuitka 裸用 | 备选，需要更细控制时 |
| PyInstaller | 兼容性好，但官方导向已是 Nuitka |

Qt for Python 6.4+ 官方推荐 `pyside6-deploy`，自动识别 Qt 模块插件、排除不需要的重模块，macOS 可写权限描述串。

## 命令

```bash
pip install pyside6-deploy nuitka ordered-set zstandard
pyside6-deploy client/main.py
```

生成 `pysidedeploy.spec`，可进版本库作打包配置（不是构建产物）。常用字段：

- `inputs.main`：入口
- `excluded_qml_plugins`：纯 Widgets 项目可全排除
- `macos.permissions`：截屏等权限描述
- `nuitka` 段：版本、`--company-name`、`--product-name`

Nuitka 裸用示例：

```bash
nuitka --standalone --onefile \
  --windows-disable-console \
  --enable-plugin=pyside6 \
  --include-data-files=config.json=config.json \
  client/main.py
```

依赖工具：Windows `dumpbin`（MSVC）、Linux `readelf`、macOS `dyld_info`（macOS 12+）。

## 分发形态

| 平台 | 形态 | 说明 |
|------|------|------|
| macOS | `.app` bundle | 便于 LaunchAgent 与登录项 |
| Windows | 目录 + Inno Setup 安装器 | 或 onefile 给极简场景 |
| Linux | AppImage 或 standalone 目录 + `.desktop` | |

开发与 CI 用 standalone 目录，启动快、好排查缺插件。正式发布再上单文件或安装包。

## 目录

```text
scripts/
├── build_client.py        调 pyside6-deploy / Nuitka
├── build_frontend.py      npm run build 并拷 dist
├── package_macos.sh
├── package_windows.ps1
└── package_linux.sh
```

打包配置 `pysidedeploy.spec`、安装器脚本可进库；`build/`、`dist/`、`*.AppImage` 不进。

## 资源与路径

编译后路径结构变化，禁止 cwd 相对路径：

```python
BASE = Path(sys.executable).parent if frozen else Path(__file__).resolve().parent
```

Nuitka 必须显式 `--include-data-files`。PyInstaller onefile 解压目录用 `sys._MEIPASS`。配置文件、图标、白名单一律走 `Path(__file__)` 或打包清单定位。

## 平台坑

### Qt 插件

缺 `platforms/qwindows`、`qcocoa` 会白屏或直接崩。Nuitka 用 `--enable-plugin=pyside6`；PyInstaller 靠 hooks，且必须在干净 venv 打包。

### 系统 PySide6 抢优先级

PyInstaller 可能绕过 venv 去用系统 site-packages。打包前卸载系统 PySide6/shiboken6，或统一 `python -m pip`、`python -m PyInstaller`。

### macOS 权限

截屏需 `NSScreenCaptureUsageDescription`，媒体采集需 Automation 授权。写进 `pysidedeploy.spec` 的 `macos.permissions`，否则 .app 静默无权限。菜单栏图标打包后仍要 `QIcon.setIsMask(True)`。

### Windows

- 图标嵌入
- 杀软误报常见，建议代码签名；Nuitka 传 `--company-name`、`--product-name` 元数据
- 自启注册表 Run 指向安装后的 exe 全路径

### Linux

- AppImage 需桌面集成 `.desktop`
- 自启写 `~/.config/autostart/heartbeat-client.desktop`，Exec 指向实际路径

## 自启与安装

安装脚本负责把 `AutostartProvider` 的可执行路径换成产物路径：

| 平台 | 动作 |
|------|------|
| Windows | 写 HKCU Run 值 |
| macOS | 写 LaunchAgent plist 并 `launchctl bootstrap` |
| Linux | 写 XDG `.desktop` |

卸载反向清理。业务代码不直接写平台分支，调 `client/autostart/` 的统一接口。

## 产物不进 Git

`.gitignore` 保持排除：

```text
build/
dist/
*.spec          # PyInstaller 生成物；pysidedeploy.spec 可单独放行
*.AppImage
*.app/
```

`pysidedeploy.spec` 若需版本管理，放到 `scripts/` 或根目录并写明用途。

## 检查清单

1. 干净 venv，只有项目依赖
2. `pyside6-deploy` 或 Nuitka 成功产出
3. 无控制台窗口（Windows GUI）
4. 托盘图标正常，macOS 明暗切换不脏
5. 截屏、媒体权限描述齐全并已授权
6. 配置读写路径正确，secrets 权限 0600
7. 自启指向产物路径
8. 断网时采集线程不崩，退避重试

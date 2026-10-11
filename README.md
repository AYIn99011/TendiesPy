# TendiesPy

将老格式 iOS 壁纸包（`.tendies`，基于 CollectionPoster 描述符）转换为 iOS 27 Clownfish 描述符结构、恢复景深效果的 Python 桌面工具。

> ⚠️ 转换效果因壁纸包结构而异，部分壁纸可能无法生效。如遇到问题，欢迎附带源文件提交 Issue 反馈。

## 背景

`.tendies` 是社区长期使用的 iOS 壁纸分发格式。随着 iOS 锁屏体系演进，老格式描述符在新系统上常出现渲染黑屏、图层偏移与景深丢失。TendiesPy 对壁纸包做解析、修复与现代化重写，使其符合当前 Clownfish 描述符规范；所有处理均在本地完成，不依赖网络服务。

转换核心基于 GoldenNugget 上游 `posterboard_converter.py` 的壁纸修复功能改写而来，在此感谢 GoldenNugget 的开源工作；另有两处针对实测问题的修复（见功能特性）；GUI 为全新编写的 tkinter 界面。

## 功能特性

### 格式转换
- 描述符迁移：将 CollectionPoster 描述符重写为 iOS 27 Clownfish 结构
- 景深三件套：`publishedObjectNames` 与各平面根图层 `id` 匹配、`family=Clownfish` 重盖章、双 depth plist 无条件写入（`configurableOptions.plist` + `renderingConfiguration.plist`）
- 崩溃防护：删除外部 `<scriptObject>` 脚本节点；含陷阱 CAML 操作（`LKStateAddElement` / `CAMeshTransform`）的平面压平成单张静态图
- 前景补齐：缺失 Foreground 平面时合成透明 Foreground
- 图层绑定修复：图层有名字但缺 `<contents>` 绑定时，按图层名在资源目录中匹配图片并补上绑定（网页预览按名字找图能显示，iOS 必须显式绑定）
- 纯色背景取色：多层纯色叠加时取视觉最上层的颜色渲染为背景图，而非最底层的
- 资源修复：按文件魔数纠正扩展名（如内容为 PNG 但后缀为 `.jpg` 的资源，iOS 按扩展名选解码器，错了会一直转圈）
- 画布规范：平面文档为逻辑屏幕尺寸，`_fit_scale` 带 5% 容差
- 命名规范：按 Clownfish skeleton 规范重命名描述符与平面目录
- 打包清理：跳过 `__MACOSX` 等 macOS 打包垃圾目录

### 批量转换
- 添加多个 `.tendies` 文件，一键批量转换
- 输出后缀、输出目录可在界面选项区修改（默认输出为 `原名.clownfish.tendies`）
- 多线程转换，进度条与时间戳日志实时显示

### 不做的事
- 无预览功能：转换前建议先用 CAPlayground 网页版确认效果
- 不自动合成 Floating 平面，不强制居中偏出屏幕的图层，不补全缺失的 Locked / Unlock / Sleep 状态定义

## 使用

1. 双击运行 `TendiesPy.exe`（免安装，单文件；或安装 Python 3 后运行 `python gui.py`）
2. 添加 `.tendies` 文件 → 开始转换
3. 输出为 `原名.clownfish.tendies`，用 GoldenNugget 刷入

## 打包与运行方式

### 直接运行（需 Python 3）
```bash
# 前置要求：Python 3（自带 tkinter）
# 转换功能仅需标准库；无需安装任何依赖
python gui.py
```

### 打包为单文件 exe（Windows）
```bash
# 前置要求：Python 3 + PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed --name TendiesPy gui.py
# 输出：dist/TendiesPy.exe（约 18MB，含 Python + tkinter，开箱即用）
```

本仓库的 exe 由 GitHub Actions 自动构建：每次 push 到 main 分支，`.github/workflows/build-windows.yml` 会在 Windows runner 上打包并上传 artifact。

## 相关项目

- [CAPlayground/CAPlayground](https://github.com/CAPlayground/CAPlayground) — 网页版 Core Animation 壁纸编辑器，可对壁纸做完整交互式预览与精细编辑。建议配合使用：TendiesPy 负责批量转换，CAPlayground 负责完整预览与精调。

## 免责

- 非官方逆向格式工具，使用前请自行备份源文件。

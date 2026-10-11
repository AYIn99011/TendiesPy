# TendiesPy

将老格式 `.tendies` 壁纸转换为 iOS 27 Clownfish 格式、恢复景深效果的 Python 桌面工具。

转换核心为 GoldenNugget 上游 `posterboard_converter.py` 的原始实现（未做任何修改），GUI 为全新编写。

## 景深是怎么实现的（上游实现）

GoldenNugget 的转换把老格式描述符重写为现代 Clownfish 布局，PosterKit 只有在以下条件全满足时才会开景深：

1. **publishedObjectNames**：每个平面 `*.ca/index.xml` 声明 `publishedObjectNames`；平面 `main.caml` 根 `CALayer` 携带与之匹配的 `id`——iOS 27 从 `publishedObjectNames` 解析浮动层/背景层，找不到匹配层就拒绝构建景深（浮动视图会被压进前景）。
2. **画布规范**：平面文档为逻辑屏幕尺寸，`scalesToFitInPlayer=true`、`unitsInPixelsInPlayer=false`。
3. **双 depth plist**（每次必写）：
   - `contents/` 下的 `.com.apple.posterkit.provider.contents.configurableOptions.plist`（`preferredRenderingConfiguration` 中 `depthEffectDisabled=false`）
   - `versions/1/` 下的 `com.apple.posterkit.provider.instance.renderingConfiguration.plist`（`depthEffectDisabled=false`）
4. **Wallpaper.plist 重盖章**：`family=Clownfish`（景深渲染器），`contentVersion` / `disableAdaptiveTime` / `maximumAdaptiveTimeMultiplier`，资源类型为 `LayeredAnimation`。
5. **根图层发布**：平面根 `CALayer` 的 `id` 设为角色名并重指向内部 `targetId`；像素画布补 fit scale。

## 修复项（上游自带的转换修复）

- 删外部 `<scriptObject src=...>` 脚本节点——会导致 WallpaperKit `EXC_BREAKPOINT` 崩溃，连带杀掉所有壁纸的快照/景深
- 含陷阱 CAML 状态操作（`LKStateAddElement` / `CAMeshTransform`）的平面压平成单张静态图——发布它会继续崩溃
- 偏出屏幕的图层自动居中（胶片带式排布在无动画状态下不可见）
- 纯色背景渲染成真实图片
- 图片资源扩展名与真实格式不符时修正（解码器按扩展名选，错了会转圈）
- 跳过 `__MACOSX` 资源派生目录

## 使用方法

1. 安装 Python 3（官网 python.org，自带 tkinter；如需 Pillow 仅用于预览，本工具转换不需要）
2. 双击运行 `gui.py`（或 `python gui.py`）
3. 添加 `.tendies` 文件 → 开始转换
4. 输出为 `原名.clownfish.tendies`，用 GoldenNugget 刷入

输出后缀、输出目录可在界面选项区修改。

## 文件说明

- `gui.py` — 图形界面（tkinter，多线程转换、进度条、时间戳日志）
- `converter.py` — 转换核心（GoldenNugget 上游原始实现，未修改）

## 注意事项

- 只转换老格式描述符；已是新格式的包会跳过（但仍会清理陷阱脚本/CAML）
- 复杂动画可能被压平，属正常现象
- 刷入前建议先用 CAPlayground 网页版预览确认效果

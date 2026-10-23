# comic2svg 🎨⚡

<p align="center">
  <b>专为扫描版老漫画、连环画/小人书、经典古籍线稿打造的高保真矢量化 (SVG) 与智能增强流水线。</b>
</p>

<p align="center">
  <a href="https://github.com/jimou78/comic2svg/actions/workflows/ci.yml"><img src="https://github.com/jimou78/comic2svg/actions/workflows/ci.yml/badge.svg" alt="CI 状态"></a>
  <a href="https://pypi.org/project/comic2svg/"><img src="https://img.shields.io/pypi/v/comic2svg.svg?color=blue" alt="PyPI 版本"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="开源协议: MIT"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/Language-English-orange.svg" alt="English Documentation"></a>
</p>

---

## 🌟 为什么需要 comic2svg？

在现代 4K / Retina 高清屏幕或墨水屏阅读器上重温经典连环画、老旧小人书或古籍时，往往会面临以下困扰：
- **纸张发黄、底色不均**：历史陈旧纸张常有大面积黄斑，直接阅读极为刺眼。
- **网点噪点与透墨渗透**：扫描件伴随大量微小杂斑和扫描仪颗粒感。
- **放大后发虚模糊**：位图格式放大后边缘产生严重锯齿或模糊。

传统的通用位图转矢量工具（如 Inkscape 或普通 Potrace）容易把纸张上的脏斑和泛黄阴影误识别为有效笔画，导致生成的 SVG 体积臃肿、线条杂乱。

**`comic2svg`** 针对这一场景提供了领域专用的预处理与矢量化方案：
1. **智能自适应底色消除与降噪**：基于 OpenCV 的自适应局部光照均衡与非局部均值滤波，在滤除泛黄底色与纸面杂质的同时，完整保留细微画工笔锋。
2. **基于 Rust 核心的高速矢量化**：集成 `vtracer` 引擎，将二值化线条精确拟合为轻量、平滑的贝塞尔曲线 Path，实现无级缩放与极小体积。
3. **多核多进程并行处理**：充分释放现代多核 CPU（如 Apple Silicon M 系列芯片）的并发性能，整本数百页的书籍几分钟内即可转换完毕。

---

## 🚀 快速上手

### 安装

```bash
# 推荐使用现代包管理器 uv (极速安装)
uv pip install comic2svg

# 或使用标准 pip
pip install comic2svg
```

### 1. 两步走高清增强工作流（PDF -> PNG -> 高清超分增强）

从 PDF 逐页提取 PNG 并进行 2x / 4x 超分辨率重建、平场去黄校正与线条锐化：

```bash
# 步骤 1 & 2: PDF -> PNG -> 2 倍高清超分线稿
comic2svg hd 老连环画.pdf --scale 2 --out ./hd_pages/

# 4 倍超清重构（开启断笔微隙重连 + 边缘反锐化遮罩）
comic2svg hd 老连环画.pdf --scale 4 --sharpen --reconnect --out ./ultra_hd/
```

### 2. 端到端矢量化（PDF -> 高清增强 -> 纯净矢量 SVG）

直接将老漫画 PDF 转为可在任意 4K/8K 屏幕无限放大的矢量 SVG：

```bash
# 开启 --hd 预增强，转出的 SVG 线条平滑度显著提升
comic2svg convert 老连环画.pdf --hd --scale 2 --out ./svg_output/

# 开启 --fast 极速降噪模式（适合数百页大部头书籍批量处理，速度提升 5~10 倍）
comic2svg convert 老连环画.pdf --fast --out ./svg_output/
```

仅转换指定页码（例如第 1 到 10 页）：

```bash
comic2svg convert 老连环画.pdf --pages "1-10" --out ./preview/
```

### 3. 本地可视化调参工坊 (`comic2svg webui`)

启动内置的交互式浏览器 Studio，支持**左右卷帘滑块实时对比（原图 ⟷ 高清矢量）**、实时调参、一键导出：

```bash
comic2svg webui
# 自动在浏览器打开 http://127.0.0.1:8080 (零额外 Web 框架依赖，开箱即用！)
```

### 4. 独立 SVG 无损瘦身压缩 (`comic2svg optimize`)

通过精简贝塞尔曲线坐标小数位、合并同类 Path、移除冗余元数据，**使 SVG 体积直接缩减 40% ~ 60%**：

```bash
# 批量优化整个目录的 SVG 文件
comic2svg optimize ./svg_pages/ --precision 2

### 5. 一键生成单文件 HTML5 矢量翻页阅读器 (`comic2svg flipbook`)

将转换出来的整部漫画打包为一个独立离线的 HTML5 翻页阅读器，支持键盘翻页、全屏模式与无损缩放：

```bash
# 转换时直接附带生成阅读器
comic2svg convert 老连环画.pdf --flipbook --out ./dist/

# 或将已有 SVG 目录打包为单文件翻页器
comic2svg flipbook ./svg_pages/ -o 连环画阅读器.html --title "三国演义连环画"
```

### 6. 高阶数字化预处理选项

```bash
# 智能拆分跨页中缝扫描（自动将 2 页拆分为 2 张独立页面）
comic2svg convert 跨页扫描.pdf --split-pages --out ./pages/

# 自动裁切去除扫描仪四周黑边与盖板阴影
comic2svg convert 扫描件.pdf --crop-borders --out ./cleaned/

# 消除历史印刷半色调网点（去网纹）
comic2svg convert 报纸漫画.pdf --descreen --out ./smooth/
```

---

## 🎛️ 场景预设 (Presets)

针对不同年代、不同印刷工艺的原稿，`comic2svg` 内置了细致调校的预设：

| 预设名称 | 适用媒介 | 核心调校策略 |
| :--- | :--- | :--- |
| `vintage-comic` *(默认)* | 老旧小人书、连环画、泛黄报纸漫画 | 自适应背景光照校正、中等去杂斑、抑制背面透墨 |
| `clean-line` | 现代高清白纸线稿、精修黑白线画 | 极小滤波，保留极致纤细的线条与排线细节 |
| `woodblock` | 木刻版画、高对比石印书、粗犷墨迹 | 增强纯黑剪影边界提取，锐化转角 |
| `color-flat` | 彩色漫画、平涂风格插画 | 多色区分割量化与分层矢量描边 |

在终端中快速查看全部预设：
```bash
comic2svg presets
```

---

## 🐍 Python 代码调用

你可以轻松将 `comic2svg` 集成进你自己的数字化流水线：

```python
from comic2svg import convert_file

# 转换 PDF 文件并获取生成的 SVG 路径列表
generated_svgs = convert_file(
    input_path="三国演义_连环画.pdf",
    output_dir="./dist_svg",
    preset="vintage-comic",
    dpi=300,
    page_range="1-5",
)

for path in generated_svgs:
    print(f"完成转换: {path}")
```

---

## 🗺️ 路线图 (Roadmap)

- [x] **v0.1.0**: 核心自适应二值化、PDF 批量提取、VTracer 矢量化引擎、预设系统与多核并行处理。
- [x] **v0.1.1**: 两步走高清超分重构管线（Lanczos-4 超分、平场去黄校正、反锐化边缘增强、微断笔重连）。
- [x] **v0.1.2**: 内置交互式可视化调参工坊 (`comic2svg webui`) 与独立 SVG 瘦身压缩器 (`comic2svg optimize`)。
- [x] **v0.1.3**: 高阶数字化套件：自动双页中缝切分、扫描黑边智能裁切、印刷半色调消网纹、自适应小开本 DPI、单文件 HTML5 矢量翻页阅读器。
- [ ] **v0.2.0**: 可插拔**智能上色管线 (Colorization Pipeline)**：
  - 基于连通区域与调色板的规则填色。
  - 支持可选的本地 ControlNet 线稿上色插件 (`pip install comic2svg[ai]`)。
- [ ] **v0.3.0**: 交互式 Web 调参界面，实时对比预览调参效果。

---

## 🤝 贡献与社区

欢迎提交 Issue 和 Pull Request！请参考 [CONTRIBUTING.md](CONTRIBUTING.md) 了解开发规范与测试流程。

---

## 📄 开源协议

本项目采用 [MIT 许可证](LICENSE)。

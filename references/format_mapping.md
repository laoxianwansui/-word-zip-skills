# 中文字号与 LaTeX 映射表

## 字号 → pt → LaTeX 命令

| 字号 | pt | LaTeX `\zihao{}` | 说明 |
|------|-----|-------------------|------|
| 初号 | 42 | `\zihao{0}` | 最大 |
| 小初 | 36 | `\zihao{-0}` | |
| 一号 | 26 | `\zihao{1}` | |
| 小一 | 24 | `\zihao{-1}` | |
| 二号 | 22 | `\zihao{2}` | |
| 小二 | 18 | `\zihao{-2}` | |
| 三号 | 16 | `\zihao{3}` | 摘要标题常用 |
| 小三 | 15 | `\zihao{-3}` | 封面信息常用 |
| 四号 | 14 | `\zihao{4}` | 章标题常用 |
| 小四 | 12 | `\zihao{-4}` | 正文常用 |
| 五号 | 10.5 | `\zihao{5}` | 参考文献/页眉常用 |
| 小五 | 9 | `\zihao{-5}` | 脚注常用 |

## 字体名 → LaTeX 命令 (ctex)

| 中文字体 | LaTeX 命令 | 英文字体 | LaTeX 命令 |
|---------|-----------|---------|-----------|
| 宋体 | `\songti` | Times New Roman | `\rmfamily` (默认衬线) |
| 黑体 | `\heiti` | Arial/Helvetica | `\sffamily` |
| 楷体 | `\kaishu` | | |
| 仿宋 | `\fangsong` | | |
| 隶书 | `\lishu` | | |
| 幼圆 | `\youyuan` | | |

## 对齐方式 → LaTeX

| Word 对齐 | LaTeX 命令/环境 |
|-----------|----------------|
| 居中 | `\centering` 或 `\begin{center}...\end{center}` |
| 左对齐 | `\raggedright` 或默认 |
| 右对齐 | `\raggedleft` |
| 两端对齐 | 默认（或 `\justifying`） |
| 顶格(无缩进) | `\noindent` |

## 间距规格

| Word 描述 | LaTeX 对应 |
|-----------|-----------|
| 段前X行 | `\vspace{X\baselineskip}` 或 titlesec 的 `beforesep` |
| 段后X行 | titlesec 的 `aftersep` |
| 1.5倍行距 | `\onehalfspacing` (setspace 宏包) |
| 双倍行距 | `\doublespacing` |
| 首行缩进2字符 | `\setlength{\parindent}{2em}` (ctex 默认) |
| 与内容空一行 | `\vspace{\baselineskip}` 或 `\\[1\baselineskip]` |

## 特殊字符处理

| Word 字符 | LaTeX 处理 |
|----------|-----------|
| 全角空格 (　) | `\quad` 或 `\hspace{1em}` |
| "摘  要" (中间空两格) | `摘\quad 要` 或 `摘\hspace{2em}要` |
| 中文标点，。！ | 直接使用，XeLaTeX 原生支持 |
| 半角空格用于句号后 | 英文模式下自动处理 |

## 图表公式编号

| 元素 | 格式 | LaTeX 命令 |
|------|------|-----------|
| 图编号 | 图X.Y (在下方) | `\caption{图\thechapter.\arabic{figure} ...}` |
| 表编号 | 表X.Y (在上方) | 同上，用 `\caption` 在表格前 |
| 公式编号 | (X-Y) (右对齐) | `\numberwithin{equation}{chapter}` 自动生成 |

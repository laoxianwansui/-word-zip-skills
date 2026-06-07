# Overleaf ZIP 上传规范

## 目录结构要求

ZIP 文件解压后，`main.tex` 必须在根目录：

```
thesis_template.zip
├── main.tex              ← Overleaf 首先寻找此文件
├── chapters/
│   ├── cover.tex
│   ├── abstract_cn.tex
│   ├── abstract_en.tex
│   ├── chapter1.tex
│   ├── conclusion.tex
│   ├── acknowledgement.tex
│   ├── references.tex
│   └── appendix.tex
├── figures/              ← 空目录，放图片
└── bibliography.bib      ← 参考文献数据库
```

## 编译设置

- **编译器**：XeLaTeX（ctex 宏包要求）
- **TeX Live 版本**：Overleaf 默认使用最新版
- **主文档**：main.tex

## 常见编译错误

1. **fontspec 错误** → 确保使用 XeLaTeX 编译器
2. **ctex 中文乱码** → 确保 .tex 文件编码为 UTF-8
3. **缺少宏包** → 只使用 CTAN 标准宏包
4. **参考文献编译失败** → 需要运行 latex → bibtex → latex → latex 四次

## ZIP 创建注意事项

- 使用 zipfile.ZIP_DEFLATED 压缩
- 路径分隔符使用正斜杠 `/`
- 不要在 ZIP 中包含上级目录路径
- 文件名不要包含中文或特殊字符

"""ZIP 打包器。

将生成的 LaTeX 项目目录打包为 Overleaf 兼容的 ZIP 文件。
"""

import os
import sys
import zipfile


def package_zip(source_dir: str, output_path: str = None) -> str:
    """将 LaTeX 项目目录打包为 Overleaf 兼容的 ZIP 文件。

    验证要求：
    - source_dir 必须包含 main.tex
    - ZIP 中所有路径使用正斜杠
    - 不包含上级目录路径

    Args:
        source_dir: LaTeX 项目源代码目录
        output_path: ZIP 输出路径。默认与 source_dir 同名 .zip

    Returns:
        ZIP 文件的路径

    Raises:
        FileNotFoundError: source_dir 中缺少 main.tex
    """
    main_tex = os.path.join(source_dir, "main.tex")
    if not os.path.exists(main_tex):
        raise FileNotFoundError(
            f"输出目录中缺少 main.tex 文件。请确保模板生成正确。\n"
            f"预期路径: {main_tex}"
        )

    if output_path is None:
        output_path = source_dir.rstrip("/\\") + ".zip"

    print(f"[打包] {source_dir} -> {output_path}")

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            # 过滤不需要的文件
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            for file in files:
                if (file.startswith('.') and file != '.keep') or file.endswith('.pyc'):
                    continue

                file_path = os.path.join(root, file)
                # 计算 ZIP 内的相对路径（使用正斜杠）
                arcname = os.path.relpath(file_path, source_dir).replace('\\', '/')

                zf.write(file_path, arcname)
                print(f"  + {arcname}")

    file_size = os.path.getsize(output_path)
    print(f"[打包] 完成。文件大小: {file_size / 1024:.1f} KB")
    return output_path

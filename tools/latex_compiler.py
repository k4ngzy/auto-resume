import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Union


def check_xelatex_installed() -> bool:
    """检查系统是否安装 xelatex"""
    return shutil.which("xelatex") is not None


def compile_latex_to_pdf(
    tex_content: str, output_dir: Union[str, Path], filename: str = "resume"
) -> Tuple[bool, Optional[Path], str]:
    """
    编译 LaTeX 到 PDF

    Args:
        tex_content: LaTeX 文件内容
        output_dir: 输出目录（字符串或 Path 对象）
        filename: 文件名（不含扩展名）

    Returns:
        (成功标志, PDF路径, 错误信息)
    """
    # 🔧 统一转换为 Path 对象
    output_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if not check_xelatex_installed():
        return False, None, "❌ 系统未安装 xelatex，请先安装 TeX Live 或 MacTeX"

    # 1. 保存 .tex 文件
    tex_path = output_dir / f"{filename}.tex"
    try:
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)
        print(f"✅ LaTeX 文件已保存: {tex_path}")
    except Exception as e:
        return False, None, f"❌ 保存失败: {str(e)}"

    # 2. 编译（在 output_dir 中执行）
    try:
        print("🔄 正在编译 LaTeX (第1次)...")
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", f"{filename}.tex"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(output_dir),
        )

        print("🔄 正在编译 LaTeX (第2次)...")
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", f"{filename}.tex"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(output_dir),
        )

        # 3. 检查 PDF
        pdf_path = output_dir / f"{filename}.pdf"
        if pdf_path.exists():
            # 清理辅助文件
            for ext in [".aux", ".log", ".out"]:
                aux_file = output_dir / f"{filename}{ext}"
                if aux_file.exists():
                    aux_file.unlink()

            print(f"✅ PDF 已生成: {pdf_path}")
            print(f"   大小: {pdf_path.stat().st_size} bytes")
            return True, pdf_path, ""
        else:
            return False, None, _analyze_latex_error(output_dir, filename, result)

    except subprocess.TimeoutExpired:
        return False, None, "❌ 编译超时（30秒）"
    except Exception as e:
        return False, None, f"❌ 编译过程出错: {str(e)}"


def _analyze_latex_error(output_dir: Path, filename: str, result) -> str:
    """分析 LaTeX 编译错误"""
    log_path = output_dir / f"{filename}.log"
    error_msg = "❌ 编译失败\n"

    if result.returncode != 0:
        error_msg += f"返回码: {result.returncode}\n"

    if log_path.exists():
        error_msg += f"日志文件: {log_path}\n"
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                log_content = f.read()

                # 提取错误行
                error_lines = [line for line in log_content.split("\n") if line.startswith("!")]
                if error_lines:
                    error_msg += "\n关键错误:\n" + "\n".join(error_lines[:5])

                # 检查常见问题
                if "resume.cls" in log_content and "not found" in log_content:
                    error_msg += "\n💡 缺少 resume.cls 文档类文件"
                if "zh_CN-Adobefonts_external" in log_content:
                    error_msg += "\n💡 缺少中文字体包"
                if "linespacing_fix" in log_content:
                    error_msg += "\n💡 缺少 linespacing_fix.sty 包"

        except Exception as e:
            error_msg += f"\n无法读取日志: {str(e)}"

    if result.stderr:
        error_msg += f"\nStderr:\n{result.stderr[:300]}"

    return error_msg

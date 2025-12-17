import io
from pathlib import Path

import docx
import pdfplumber
from fastapi import HTTPException


async def extract_text_from_file(content: bytes, filename: str) -> str:
    """从不同格式的文件中提取文本"""
    file_ext = Path(filename).suffix.lower()

    try:
        # TXT文件
        if file_ext == ".txt":
            try:
                return content.decode("utf-8")
            except UnicodeDecodeError:
                return content.decode("gbk")

        # PDF文件
        elif file_ext == ".pdf":
            pdf_file = io.BytesIO(content)
            text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                    # 可选：提取表格内容
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            text += " | ".join([cell or "" for cell in row]) + "\n"

            return text.strip()

        # DOCX文件
        elif file_ext == ".docx":
            doc_file = io.BytesIO(content)
            doc = docx.Document(doc_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file_ext}，请使用 .txt, .pdf, .docx 格式",
            )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析文件失败: {str(e)}")

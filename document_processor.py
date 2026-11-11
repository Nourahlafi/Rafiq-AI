"""المرحلة 1: قراءة الـPDF وتقطيعه إلى مقاطع"""
import os
import fitz  # PyMuPDF


def read_pdf(path):
    """يرجع قائمة (رقم الصفحة، نص الصفحة)"""
    doc = fitz.open(path)
    return [(i + 1, page.get_text()) for i, page in enumerate(doc)]


def chunk_text(text, size=1200, overlap=250):
    """يقطع النص لمقاطع متداخلة عشان ما يضيع المعنى بين مقطع ومقطع"""
    text = " ".join(text.split())
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def process_pdf(path, source=None):
    """يجهز المقاطع مع بياناتها (الملف + الصفحة) وأرقامها التعريفية"""
    source = source or os.path.basename(path)
    docs, metas, ids = [], [], []
    for page, text in read_pdf(path):
        for j, chunk in enumerate(chunk_text(text)):
            if len(chunk.strip()) < 30:
                continue
            docs.append(chunk)
            metas.append({"source": source, "page": page})
            ids.append(f"{source}-{page}-{j}")
    return docs, metas, ids

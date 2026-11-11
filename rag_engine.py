"""المرحلة 3: RAG = بحث في المقاطع + إجابة Gemini منها فقط"""
import os
import time
from google import genai
from google.genai import types

from document_processor import process_pdf
from vector_store import add_chunks, search_chunks

GEMINI_MODEL = "gemini-3.8-flash"
MIN_SCORE = 0.25
MODELS = [GEMINI_MODEL]

SYSTEM = """أنت رفيق، مساعد جامعي. أجب بالعربية الواضحة اعتماداً على المقاطع المرفقة فقط.
إذا كانت المقاطع بالإنجليزية فاشرحها بالعربية.
إذا لم تجد الجواب فيها، قل بالضبط: ما لقيت الجواب في المستند.
اذكر رقم الصفحة بين قوسين بعد المعلومة، مثل (ص4).
لا تخترع أي معلومة من خارج المقاطع."""


def ingest_pdf(path, source=None):
    """قراءة الملف -> تقطيع -> تخزين في Chroma"""
    docs, metas, ids = process_pdf(path, source)
    return add_chunks(docs, metas, ids)


def search(query, k=4, source=None):
    return search_chunks(query, k=k, source=source)


def ask_gemini(question, results):
    context = "\n\n".join(f"[ص{r['page']}] {r['text']}" for r in results)
    prompt = f"المقاطع:\n{context}\n\nالسؤال: {question}"
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options=types.HttpOptions(timeout=30000),
    )
    last_error = None
    for model in MODELS:
        for _ in range(4):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM),
                )
                return resp.text
            except Exception as e:
                last_error = e
                time.sleep(3)
    raise last_error


def answer_question(question, source):
    if "GEMINI_API_KEY" not in os.environ:
        return "مفتاح Gemini غير مضبوط. راجعي خطوة وضع المفتاح في التيرمنال."

    results = search(question, k=8, source=source)
    results = [r for r in results if r["score"] >= MIN_SCORE]
    if not results:
        return "ما لقيت الجواب في المستند."

    try:
        return ask_gemini(question, results)
    except Exception as e:
        return f"صار خطأ مع Gemini: {e}"
"""رفيق: RAG + وكيل (Agent) = بحث في المقاطع + أدوات يستدعيها Gemini"""
import os
from google import genai
from google.genai import types

from document_processor import process_pdf
from vector_store import add_chunks, search_chunks

GEMINI_MODEL = "gemini-3.8-flash"
MODELS = [GEMINI_MODEL, "gemini-flash-latest"]
MIN_SCORE = 0.25
GPA_WORDS = ("معدل", "gpa", "احسب")

SYSTEM = """أنت رفيق، مساعد جامعي. أجب بالعربية الواضحة اعتماداً على المقاطع المرفقة فقط.
إذا كانت المقاطع بالإنجليزية فاشرحها بالعربية.
إذا لم تجد الجواب فيها، قل بالضبط: ما لقيت الجواب في المستند.
اذكر رقم الصفحة بين قوسين بعد المعلومة، مثل (ص4).
لا تخترع أي معلومة من خارج المقاطع.
إذا طلب المستخدم حساب معدل، استخدم الأداة calculate_gpa ولا تحسب بنفسك."""


def calculate_gpa(grades: list[float], credit_hours: list[int]) -> str:
    """أداة الوكيل: تحسب المعدل الفصلي من نقاط كل مادة وعدد ساعاتها."""
    if not grades or len(grades) != len(credit_hours):
        return "عدد الدرجات لازم يساوي عدد الساعات."
    total = sum(g * h for g, h in zip(grades, credit_hours))
    return f"المعدل الفصلي = {total / sum(credit_hours):.2f}"


def ingest_pdf(path, source=None):
    """قراءة الملف -> تقطيع -> تخزين في Chroma"""
    docs, metas, ids = process_pdf(path, source)
    return add_chunks(docs, metas, ids)


def search(query, k=4, source=None):
    return search_chunks(query, k=k, source=source)


def ask_gemini(question, results):
    context = "\n\n".join(f"[ص{r['page']}] {r['text']}" for r in results) or "لا توجد مقاطع ذات صلة."
    prompt = f"المقاطع:\n{context}\n\nالسؤال: {question}"
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options=types.HttpOptions(timeout=60000),
    )
    use_tool = any(w in question.lower() for w in GPA_WORDS)
    first_error = None
    for model in MODELS:
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM,
                    tools=[calculate_gpa] if use_tool else None,
                ),
            )
            return resp.text
        except Exception as e:
            first_error = first_error or e
    raise first_error


def answer_question(question, source):
    if "GEMINI_API_KEY" not in os.environ:
        return "مفتاح Gemini غير مضبوط."

    results = search(question, k=4, source=source)
    results = [r for r in results if r["score"] >= MIN_SCORE]
    if not results and not any(w in question.lower() for w in GPA_WORDS):
        return "ما لقيت الجواب في المستند."

    try:
        return ask_gemini(question, results)
    except Exception as e:
        return f"صار خطأ مع Gemini: {e}"
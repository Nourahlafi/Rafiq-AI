"""رفيق: RAG + وكيل (Agent) = بحث في المقاطع + أدوات يستدعيها Gemini"""
import os
from google import genai
from google.genai import types

from document_processor import process_pdf
from vector_store import add_chunks, search_chunks

GEMINI_MODEL = "gemini-3.8-flash"
MODELS = [GEMINI_MODEL, "gemini-flash-latest"]
GPA_WORDS = ("معدل", "gpa", "احسب")

SYSTEM = """أنت رفيق، مساعد جامعي. أجب بالعربية الواضحة اعتماداً على المقاطع المرفقة فقط.
إذا كانت المقاطع بالإنجليزية فاشرحها بالعربية.
إذا لم تجد الجواب في المقاطع أو كانت غير مرتبطة بالسؤال، قل بالضبط: ما لقيت الجواب في المستند.
اذكر رقم الصفحة بين قوسين بعد المعلومة، مثل (ص4).
لا تخترع أي معلومة من خارج المقاطع.
إذا طلب المستخدم حساب معدل، استخدم الأداة calculate_gpa ولا تحسب بنفسك."""


def quick_gpa(question):
    """يحسب المعدل مباشرة بدون Gemini، ومن أي صيغة، بدون تحديد عدد المواد"""
    q = question.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    if not any(w in q.lower() for w in ("معد", "معج", "gpa")):
        return None
    get = lambda s: [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    if "ساع" in q:
        before, after = q.split("ساع", 1)
        grades, hours = get(before), get(after)
    else:
        nums = get(q)
        if len(nums) % 2 == 0:
            grades, hours = nums[:len(nums) // 2], nums[len(nums) // 2:]
        else:
            grades, hours = nums, [1] * len(nums)
    if not grades or len(grades) != len(hours):
        return None
    return calculate_gpa(grades, [int(h) for h in hours])


def ingest_pdf(path, source=None):
    """قراءة الملف -> تقطيع -> تخزين في Chroma، ويرجع عدد المقاطع"""
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
    wants_gpa = any(w in question.lower() for w in GPA_WORDS)
    if not results and not wants_gpa:
        return "ما لقيت نص في هذا الملف."

    try:
        return ask_gemini(question, results)
    except Exception as e:
        return f"صار خطأ مع Gemini: {e}"
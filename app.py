import os
import tempfile

import streamlit as st

from rag_engine import ingest_pdf, answer_question

st.set_page_config(page_title="رفيق | Rafiq AI", page_icon="\u2728", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;800&display=swap');

html, body, [class*="css"], .stApp { font-family:'Tajawal',sans-serif; }
.stApp {
  background: radial-gradient(circle at 20% 0%, #4c1d95 0%, #1e1b4b 45%, #0f172a 100%);
  direction: rtl;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { max-width: 760px; padding-top: 2rem; }

.hero { text-align:center; margin-bottom:1.8rem; }
.hero .badge { display:inline-block; padding:.25rem .9rem; border-radius:99px;
  background:rgba(45,212,191,.15); color:#5eead4; font-size:.85rem;
  border:1px solid rgba(45,212,191,.4); margin-bottom:.8rem; }
.hero h1 { font-size:3rem; font-weight:800; margin:0;
  background:linear-gradient(90deg,#5eead4,#c4b5fd,#f9a8d4);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.hero p { color:#cbd5e1; font-size:1.05rem; margin-top:.4rem; }

p, label, span, li, .stMarkdown { color:#e2e8f0 !important; }

[data-testid="stFileUploader"] section {
  background:rgba(255,255,255,.06); border:2px dashed rgba(196,181,253,.5);
  border-radius:18px; transition:.25s; }
[data-testid="stFileUploader"] section:hover {
  border-color:#5eead4; background:rgba(255,255,255,.1); }

[data-testid="stChatMessage"] {
  background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.1);
  border-radius:18px; padding:1rem; margin-bottom:.7rem;
  backdrop-filter:blur(8px); }

[data-testid="stChatInput"] { border-radius:16px;
  border:1px solid rgba(94,234,212,.5); }
[data-testid="stChatInput"]:focus-within {
  border-color:#5eead4 !important;
  box-shadow:0 0 0 1px #5eead4 !important; }

.stButton>button { background:linear-gradient(90deg,#14b8a6,#8b5cf6);
  color:#fff; border:0; border-radius:14px; font-weight:800;
  padding:.6rem 1.4rem; transition:.2s; }
.stButton>button:hover { transform:translateY(-2px);
  box-shadow:0 8px 20px rgba(139,92,246,.45); }
</style>

<div class="hero">
  <span class="badge">&#10024; رفيقك الجامعي</span>
  <h1>رفيق | Rafiq AI</h1>
  <p>أنا رفيق &#128075; ارفع ملفك واسألني، وأجاوبك من محتواه فقط</p>
</div>
""", unsafe_allow_html=True)


def prepare_file(uploaded_file):
    """يقرأ الملف مرة وحدة ويخزنه في Chroma"""
    if st.session_state.get("ingested") != uploaded_file.name:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(uploaded_file.getvalue())
        with st.spinner("أقرأ ملفك..."):
            ingest_pdf(f.name, source=uploaded_file.name)
        os.remove(f.name)
        st.session_state.ingested = uploaded_file.name


def get_answer(question: str, uploaded_file) -> str:
    if uploaded_file is None:
        return "ارفعي ملفاً أولاً عشان أقدر أجاوبك من محتواه."
    return answer_question(question, source=uploaded_file.name)


uploaded_file = st.file_uploader("ارفع ملفك الجامعي (PDF)", type=["pdf"])

if uploaded_file is not None:
    prepare_file(uploaded_file)
    st.success(f"تم رفع الملف: {uploaded_file.name}")

WELCOME = "هلا! أنا رفيق \u2728 ارفع ملفك الجامعي وأجاوبك من محتواه."

AI_ICON = ":material/auto_awesome:"
USER_ICON = ":material/face:"

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME}]

for msg in st.session_state.messages:
    icon = AI_ICON if msg["role"] == "assistant" else USER_ICON
    with st.chat_message(msg["role"], avatar=icon):
        st.markdown(msg["content"])

if question := st.chat_input("اكتب سؤالك هنا..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar=USER_ICON):
        st.markdown(question)

    with st.chat_message("assistant", avatar=AI_ICON):
        with st.spinner("أفكر..."):
            answer = get_answer(question, uploaded_file)
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

if len(st.session_state.messages) > 1:
    if st.button("محادثة جديدة"):
        st.session_state.messages = [{"role": "assistant", "content": WELCOME}]
        st.rerun()

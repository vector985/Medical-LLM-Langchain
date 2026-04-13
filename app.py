import os
import time
import traceback
import json
import re

import streamlit as st
from langchain.prompts import PromptTemplate

from service import Service
from utils import get_llm_model

MAX_HISTORY_TURNS = 20
DEFAULT_LLM_MODEL = 'deepseek-ai/DeepSeek-V3.2'
QUICK_QUESTIONS = [
    'What is rhinitis, and what are its common symptoms?',
    'Can pregnant women take ibuprofen?',
    'How should I handle a fever of 38.8 degrees Celsius?',
    'What diet considerations are important for people with hypertension?',
]
MEDICAL_NOTICE = (
    'This system provides medical information for reference and does not replace professional '
    'diagnosis, examinations, or treatment plans from licensed clinicians. '
    'If you have emergency symptoms such as chest pain, breathing difficulty, altered consciousness, '
    'or persistent high fever, seek immediate in-person medical care.'
)
FOLLOWUP_QUESTION_PROMPT = """
You are a follow-up recommendation assistant for a professional medical QA system.
Based on the recent conversation, generate 4 high-value and natural next-step follow-up questions in English.

Requirements:
1. Each question should be 8-24 words and sound natural.
2. Questions must be strongly relevant to the current conversation, prioritizing:
   causes, differential diagnosis, tests, medication, care-seeking timing, and lifestyle guidance.
3. Avoid duplicates, avoid vague phrasing, and avoid political/violent/sexual content.
4. Output JSON only, with no extra explanation.

Output format:
{{"questions":["Question 1","Question 2","Question 3","Question 4"]}}

Recent conversation:
{chat_history}
"""


def _error_message(e):
    err = str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__
    if os.getenv('VERBOSE', 'False').lower() in ('1', 'true', 'yes'):
        traceback.print_exc()
    return (
        f"Sorry, the request failed: {err}\n\n"
        "Please check:\n"
        "1. `SILICONFLOW_API_KEY` in `.env` is valid;\n"
        "2. Network access to `https://api.siliconflow.cn/v1` is available;\n"
        "3. If Neo4j is not running, graph-based QA may fail."
    )


def _apply_custom_style():
    st.markdown(
        """
<style>
:root {
  --medical-blue: #0f3c73;
  --medical-blue-soft: #eaf2fb;
  --medical-cyan: #1f7aa8;
  --medical-border: #d9e6f4;
  --medical-text: #153047;
  --medical-muted: #5a6d80;
}

html, body, [class*="css"]  {
  font-family: "Source Han Sans SC", "Noto Sans CJK SC", "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}

[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 5% 5%, #f2f8ff 0%, transparent 35%),
    radial-gradient(circle at 95% 10%, #eef7ff 0%, transparent 30%),
    #f8fbff;
}

[data-testid="stSidebar"] {
  background: #f4f8fd;
  border-right: 1px solid var(--medical-border);
}

.hero-card {
  border: 1px solid var(--medical-border);
  border-radius: 14px;
  padding: 18px 20px;
  margin-bottom: 16px;
  background: linear-gradient(110deg, #ffffff 0%, #f3f8ff 100%);
  box-shadow: 0 8px 24px rgba(15, 60, 115, 0.08);
}

.hero-title {
  color: var(--medical-blue);
  font-size: 30px;
  line-height: 1.25;
  font-weight: 700;
  margin: 0;
}

.hero-subtitle {
  color: var(--medical-muted);
  margin-top: 8px;
  font-size: 15px;
}

.intro-card {
  border: 1px solid var(--medical-border);
  border-radius: 12px;
  padding: 14px 16px;
  background: #ffffff;
  margin: 10px 0 14px 0;
}

.intro-title {
  color: var(--medical-text);
  font-weight: 700;
  margin-bottom: 6px;
}

.intro-text {
  color: var(--medical-muted);
  font-size: 14px;
  line-height: 1.55;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _init_session_state():
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'last_latency' not in st.session_state:
        st.session_state.last_latency = None
    if 'quick_questions' not in st.session_state:
        st.session_state.quick_questions = list(QUICK_QUESTIONS)


def _render_header():
    st.markdown(
        """
<div class="hero-card">
  <h1 class="hero-title">Professional Medical QA Assistant</h1>
  <div class="hero-subtitle">RAG + Medical Knowledge Graph + DeepSeek V3.2</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar(model_name):
    with st.sidebar:
        st.markdown('### System Status')
        st.caption(f'Current model: `{model_name}`')
        st.caption(f'Inference endpoint: `{os.getenv("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1")}`')

        st.metric('Conversation turns', value=len(st.session_state.history))
        if st.session_state.last_latency is not None:
            st.metric('Latest response time', value=f'{st.session_state.last_latency:.2f}s')

        st.markdown('### Session Controls')
        if st.button('Clear conversation', use_container_width=True):
            st.session_state.history = []
            st.session_state.last_latency = None
            st.session_state.quick_questions = list(QUICK_QUESTIONS)
            st.rerun()

        st.markdown('### Medical Notice')
        st.info(MEDICAL_NOTICE)


def _render_empty_state():
    st.markdown(
        """
<div class="intro-card">
  <div class="intro-title">Capabilities</div>
  <div class="intro-text">
    This system supports common symptom consultation, disease and medication QA,
    and retrieval-augmented answers based on both a document knowledge base and a graph.
    You can directly ask about symptoms, test indicators, medication usage, or follow-up concerns.
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _render_quick_questions():
    st.markdown('#### Suggested Follow-Up Questions')
    selected_question = None
    candidate_questions = st.session_state.quick_questions or QUICK_QUESTIONS
    col1, col2 = st.columns(2)
    for idx, question in enumerate(candidate_questions[:4]):
        container = col1 if idx % 2 == 0 else col2
        if container.button(question, key=f'quick_question_{idx}', use_container_width=True):
            selected_question = question
    return selected_question


def _render_history():
    for question, answer in st.session_state.history:
        with st.chat_message('user'):
            st.markdown(question)
        with st.chat_message('assistant'):
            st.markdown(answer)


@st.cache_resource
def get_service():
    return Service()


def _safe_parse_questions(text):
    if not text:
        return []
    candidate = text.strip()
    if '```' in candidate:
        parts = re.findall(r'```(?:json)?\s*(.*?)```', candidate, flags=re.S)
        if parts:
            candidate = parts[0].strip()
    try:
        parsed = json.loads(candidate)
    except Exception:
        match = re.search(r'\{.*\}', candidate, flags=re.S)
        if not match:
            return []
        try:
            parsed = json.loads(match.group(0))
        except Exception:
            return []

    questions = parsed.get('questions') if isinstance(parsed, dict) else None
    if not isinstance(questions, list):
        return []

    cleaned = []
    seen = set()
    for question in questions:
        if not isinstance(question, str):
            continue
        item = re.sub(r'\s+', ' ', question).strip()
        if len(item) < 6 or len(item) > 40:
            continue
        if item in seen:
            continue
        seen.add(item)
        cleaned.append(item)
    return cleaned[:4]


def _build_chat_context(history, turns=3):
    context_lines = []
    for question, answer in history[-turns:]:
        answer_text = re.sub(r'\s+', ' ', answer).strip()
        answer_text = answer_text[:260]
        context_lines.append(f'User: {question}\nAssistant: {answer_text}')
    return '\n\n'.join(context_lines)


def _generate_dynamic_quick_questions(history):
    if not history:
        return list(QUICK_QUESTIONS)

    context = _build_chat_context(history, turns=3)
    prompt = PromptTemplate.from_template(FOLLOWUP_QUESTION_PROMPT)
    llm = get_llm_model()

    try:
        prompt_text = prompt.format(chat_history=context)
        result = llm.invoke(prompt_text)
        content = result.content if hasattr(result, 'content') else str(result)
        questions = _safe_parse_questions(content)
        if questions:
            return questions
    except Exception:
        pass
    return list(QUICK_QUESTIONS)


def main():
    st.set_page_config(page_title='Professional Medical QA Assistant', layout='centered')
    model_name = os.getenv('SILICONFLOW_LLM_MODEL', DEFAULT_LLM_MODEL)

    _apply_custom_style()
    _init_session_state()
    _render_header()
    _render_sidebar(model_name)

    quick_query = None
    if not st.session_state.history:
        _render_empty_state()

    _render_history()
    quick_query = _render_quick_questions()

    user_query = st.chat_input('Ask your medical question, e.g., symptoms, medication, test results, or care advice')
    if user_query is not None and not user_query.strip():
        st.warning('Please enter a valid question.')
        return
    query = user_query.strip() if user_query else quick_query
    if not query:
        return

    history = list(st.session_state.history)
    service = get_service()
    with st.chat_message('user'):
        st.markdown(query)

    start = time.perf_counter()
    try:
        with st.chat_message('assistant'):
            with st.spinner('Analyzing your case and retrieving medical knowledge...'):
                answer = service.answer(query, history)
            st.markdown(answer)
    except Exception as e:
        answer = _error_message(e)
        with st.chat_message('assistant'):
            st.markdown(answer)

    st.session_state.last_latency = time.perf_counter() - start
    history.append((query, answer))
    st.session_state.history = history[-MAX_HISTORY_TURNS:]
    st.session_state.quick_questions = _generate_dynamic_quick_questions(st.session_state.history)
    st.rerun()


if __name__ == '__main__':
    main()

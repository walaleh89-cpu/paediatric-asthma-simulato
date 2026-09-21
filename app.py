import json
import re
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Asthma Simulated Patient", page_icon="🩺", layout="centered")
CASE = json.loads((Path(__file__).parent / "case.json").read_text(encoding="utf-8"))

# Every browser session has independent progress; nothing is written to disk.
def reset():
    st.session_state.messages = [{"role": "assistant", "content": CASE["opening"]}]
    st.session_state.completed = set()
    st.session_state.questions = 0
    st.session_state.feedback = False

if "messages" not in st.session_state or "completed" not in st.session_state or "questions" not in st.session_state or "feedback" not in st.session_state:
    reset()

STOPWORDS = {"a", "an", "the", "is", "are", "do", "does", "did", "you", "your", "he", "his", "of", "to", "for", "about", "any", "have", "has", "what", "how", "can", "i", "me", "please", "tell"}

def tokens(text):
    return set(re.findall(r"[a-z]+", text.lower())) - STOPWORDS

def find_fact(question):
    text = question.lower()
    words = tokens(text)
    best, best_score = None, 0
    for fact in CASE["facts"]:
        score = 0
        for keyword in fact["keywords"]:
            if " " in keyword:
                if keyword in text:
                    score += 4
            elif keyword in words:
                score += 3
            elif len(keyword) >= 4 and any(w.startswith(keyword) for w in words):
                score += 2
        if score > best_score:
            best, best_score = fact, score
    return best if best_score >= 2 else None

def answer(question):
    fact = find_fact(question)
    if fact is None:
        return "I'm not sure how to answer that. Could you ask me a more specific question? You can also request examination findings in the Assessment tab."
    st.session_state.completed.add(fact["id"])
    return fact["answer"]

st.title("🩺 Childhood asthma: simulated patient")
st.caption("Fictional educational case • Student practice • No patient data")
st.warning("Training only. Not for clinical decisions. If this were a real patient, assess and escalate concerning respiratory signs immediately.")
st.info("You are a student nurse interviewing the child's mother. Ask one focused question at a time. Request physical examination findings in the Assessment tab.")

chat_tab, assessment_tab, feedback_tab = st.tabs(["💬 History", "🫁 Assessment", "📋 Feedback"])
with chat_tab:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    question = st.chat_input("Ask the child's mother a question...")
    if question and question.strip():
        question = question.strip()[:500]
        st.session_state.questions += 1
        st.session_state.messages.append({"role": "user", "content": question})
        st.session_state.messages.append({"role": "assistant", "content": answer(question)})
        st.rerun()

with assessment_tab:
    st.write("Select an assessment to reveal the fictional examination findings. These are observations, not statements from the mother.")
    for item in CASE["assessment"]:
        if st.button("Examine: " + item["label"], key="exam_" + item["id"], use_container_width=True):
            st.session_state.completed.add(item["id"])
        if item["id"] in st.session_state.completed:
            st.success(item["finding"])
    st.error(CASE["safety_message"])

with feedback_tab:
    done = set(CASE["essential"]) & st.session_state.completed
    total = len(CASE["essential"])
    st.metric("Essential areas explored", f"{len(done)}/{total}")
    st.caption("Coverage indicator only; not a validated competency score. An educator must assess reasoning, sequencing, communication, and escalation.")
    if st.button("Finish encounter and show feedback", type="primary"):
        st.session_state.feedback = True
    if st.session_state.feedback:
        st.subheader("Areas explored")
        for item in CASE["facts"] + CASE["assessment"]:
            if item["id"] in CASE["essential"]:
                label = item.get("label", item["id"].replace("_", " ").title())
                st.write(("✅ " if item["id"] in done else "⬜ ") + label)
        st.warning("Clinical safety reflection: What findings warrant urgent escalation? What would you do first? Discuss with your educator using your local protocol.")
        st.info(CASE["safety_message"])
        st.write(f"Questions asked: {st.session_state.questions}")

st.divider()
if st.button("🔄 Restart encounter"):
    reset()
    st.rerun()
st.caption("No student login, database, analytics, or transcript export. Closing the session does not guarantee immediate server-side memory deletion; avoid personal information.")

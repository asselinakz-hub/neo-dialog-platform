# streamlit_app.py
import os
import json
import uuid
from datetime import datetime
import streamlit as st

from dialog_engine import get_steps
from scoring import make_report

DATA_DIR = "data"
CLIENTS_DIR = os.path.join(DATA_DIR, "clients")  # data/clients/<client_id>/

def ensure_dirs():
    os.makedirs(CLIENTS_DIR, exist_ok=True)

def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

st.set_page_config(page_title="NEO Диалог-диагностика", layout="wide")
ensure_dirs()

st.title("🟣 NEO Potentials — Диалог-диагностика")
st.caption("Это не тест. Это короткий разговор, который собирает твою схему.")

# --- профиль клиента ---
with st.sidebar:
    st.header("Профиль")
    name = st.text_input("Имя", value=st.session_state.get("client_name", ""))
    phone = st.text_input("Телефон/ник", value=st.session_state.get("client_phone", ""))
    if st.button("✅ Начать / продолжить"):
        st.session_state["client_name"] = name.strip()
        st.session_state["client_phone"] = phone.strip()
        if "client_id" not in st.session_state:
            st.session_state["client_id"] = uuid.uuid4().hex[:10]
        st.session_state.setdefault("answers", {})
        st.session_state.setdefault("step_idx", 0)
        st.success("Поехали.")

if "client_id" not in st.session_state:
    st.info("Заполни профиль слева и нажми **Начать / продолжить**.")
    st.stop()

client_id = st.session_state["client_id"]
client_dir = os.path.join(CLIENTS_DIR, client_id)
os.makedirs(client_dir, exist_ok=True)

# сохраним профиль сразу
profile = {
    "client_id": client_id,
    "name": st.session_state.get("client_name", ""),
    "phone": st.session_state.get("client_phone", ""),
    "updated_at": now_iso(),
}
save_json(os.path.join(client_dir, "profile.json"), profile)

steps = get_steps()
answers = st.session_state.get("answers", {})
step_idx = st.session_state.get("step_idx", 0)

st.subheader("Диалог")

# прогресс
st.progress(min(1.0, step_idx / max(1, len(steps))))

# если закончили — показываем отчёт
if step_idx >= len(steps):
    st.success("Готово! Формирую отчёт…")

    report = make_report(answers)
    save_json(os.path.join(client_dir, "responses.json"), answers)
    save_json(os.path.join(client_dir, "report.json"), report)

    st.subheader("📄 Результат")
    for block in report["table_pretty"]:
        st.markdown(f"### {block['title']}")
        st.write(f"• Ряд 1 (Силы): **{block['row1']}**")
        st.write(f"• Ряд 2 (Энергия): **{block['row2']}**")
        st.write(f"• Ряд 3 (Остаточно): **{block['row3']}**")

    st.divider()
    if st.button("🔁 Пройти заново (новый клиент)"):
        st.session_state.pop("client_id", None)
        st.session_state.pop("answers", None)
        st.session_state.pop("step_idx", None)
        st.rerun()

    st.caption(f"Файлы сохранены в: data/clients/{client_id}/")
    st.stop()

# --- текущий шаг ---
step = steps[step_idx]

st.markdown(f"### {step['title']}")
st.write(step["prompt"])

# выбор
choice_labels = [c["label"] for c in step["choices"]]
choice_ids = [c["id"] for c in step["choices"]]

selected = st.radio("Выбери ближе всего:", options=list(range(len(choice_labels))), format_func=lambda i: choice_labels[i])

free_text = ""
if step.get("allow_free_text"):
    free_text = st.text_area(step.get("free_text_label", "Свободный ответ:"), height=80)

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("➡️ Дальше"):
        answers[step["key"]] = {
            "choice": choice_ids[selected],
            "choice_label": choice_labels[selected],
            "free_text": free_text.strip(),
            "ts": now_iso()
        }
        st.session_state["answers"] = answers
        st.session_state["step_idx"] = step_idx + 1
        st.rerun()

with col2:
    if st.button("⬅️ Назад") and step_idx > 0:
        st.session_state["step_idx"] = step_idx - 1
        st.rerun()

# автосохранение “черновика”
save_json(os.path.join(client_dir, "responses_draft.json"), answers)

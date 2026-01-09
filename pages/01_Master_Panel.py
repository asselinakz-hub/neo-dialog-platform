# pages/01_Master_Panel.py
import os
import json
from pathlib import Path
import importlib.util
import streamlit as st

# --- optional auth.py ---
ROOT = Path(__file__).resolve().parents[1]
AUTH_PATH = ROOT / "auth.py"

if AUTH_PATH.exists():
    spec = importlib.util.spec_from_file_location("neo_auth_local", str(AUTH_PATH))
    auth_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auth_mod)
    if hasattr(auth_mod, "require_master_password"):
        auth_mod.require_master_password()

st.set_page_config(page_title="Master Panel — NEO", layout="wide")
st.title("🛠️ Master Panel — NEO (Диалог)")

DATA_DIR = "data"
CLIENTS_DIR = os.path.join(DATA_DIR, "clients")

def safe_read_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

if not os.path.exists(CLIENTS_DIR):
    st.info("Пока нет данных. Сначала пройди диагностику на главной странице.")
    st.stop()

client_ids = [d for d in sorted(os.listdir(CLIENTS_DIR)) if os.path.isdir(os.path.join(CLIENTS_DIR, d))]
if not client_ids:
    st.info("Пока нет клиентов.")
    st.stop()

clients = []
for cid in client_ids:
    prof = safe_read_json(os.path.join(CLIENTS_DIR, cid, "profile.json")) or {}
    label = prof.get("name") or cid
    clients.append((label, cid))

clients.sort(key=lambda x: x[0].lower())
label = st.selectbox("Выбери клиента:", [x[0] for x in clients])
cid = dict(clients)[label]

colA, colB = st.columns([1, 2])

with colA:
    st.subheader("Профиль")
    prof = safe_read_json(os.path.join(CLIENTS_DIR, cid, "profile.json")) or {}
    st.write(f"**Имя:** {prof.get('name','—')}")
    st.write(f"**Телефон:** {prof.get('phone','—')}")
    st.write(f"**client_id:** {cid}")

with colB:
    st.subheader("Отчёт")
    report_path = os.path.join(CLIENTS_DIR, cid, "report.json")
    report = safe_read_json(report_path)

    if not report:
        st.warning("report.json пока нет. Клиент не дошёл до конца.")
    else:
        for block in report.get("table_pretty", []):
            st.markdown(f"### {block['title']}")
            st.write(f"• Ряд 1 (Силы): **{block['row1']}**")
            st.write(f"• Ряд 2 (Энергия): **{block['row2']}**")
            st.write(f"• Ряд 3 (Остаточно): **{block['row3']}**")

        st.download_button(
            "⬇️ Скачать report.json",
            data=json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=f"{cid}_report.json",
            mime="application/json"
        )

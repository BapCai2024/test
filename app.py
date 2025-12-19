import streamlit as st
import json, uuid, random, datetime

try:
    import google.generativeai as genai
    HAS_GENAI = True
except:
    HAS_GENAI = False

from utils.export_docx import export_exam_docx

st.set_page_config(page_title="Tạo đề kiểm tra TT27", layout="wide")

# ---------------- Load data ----------------
@st.cache_data
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

curriculum = load_json("data/curriculum_kntt.json")
matrix = load_json("data/matrix_kntt.json")
questions_db = load_json("data/questions.json")

if "questions" not in st.session_state:
    st.session_state["questions"] = questions_db
if "gemini_api_key" not in st.session_state:
    st.session_state["gemini_api_key"] = None

# ---------------- Tabs ----------------
tab1, tab2 = st.tabs(["📘 Tạo đề", "📊 Ma trận liên kết"])

# ---------------- Tab 1 ----------------
with tab1:
    st.header("Tạo đề kiểm tra")

    # Sidebar API key
    st.sidebar.subheader("🔑 API Gemini")
    api_key_input = st.sidebar.text_input("Nhập API key", type="password")
    if st.sidebar.button("Lưu API"):
        st.session_state["gemini_api_key"] = api_key_input

    # Dropdown curriculum
    grade = st.selectbox("Lớp", list(curriculum.keys()))
    subject = st.selectbox("Môn", list(curriculum[grade].keys()))
    semester = st.selectbox("Học kỳ", list(curriculum[grade][subject].keys()))
    topics = curriculum[grade][subject][semester]
    topic = st.selectbox("Chủ đề", [t["Chủ đề"] for t in topics])
    lessons = [t["Bài học"] for t in topics if t["Chủ đề"] == topic][0].split(";")
    lesson = st.selectbox("Bài học", lessons)

    # Nút tạo câu hỏi duy nhất
    if st.button("➕ Tạo câu hỏi"):
        # Sinh câu hỏi bằng API hoặc fallback
        q_id = f"Q-{subject}-{grade}-{semester}-{str(uuid.uuid4())[:6]}"
        prompt = f"Sinh câu hỏi {subject} {grade} {semester}, {topic}, {lesson}"
        q = {
            "id": q_id,
            "grade": grade,
            "subject": subject,
            "semester": semester,
            "topic": topic,
            "lesson": lesson,
            "type": "MCQ",
            "level": "recognize",
            "points": 0.5,
            "prompt": f"Tính {random.randint(10,99)} + {random.randint(10,99)} = ?",
            "options": [20,30,40,50],
            "answer": 30,
            "explanation": "Cộng hai số tự nhiên.",
            "unit": "",
            "tags": [topic, lesson],
            "seed": random.randint(100000,999999),
            "variant": "offline"
        }
        st.session_state["questions"].append(q)
        with open("data/questions.json","w",encoding="utf-8") as f:
            json.dump(st.session_state["questions"], f, ensure_ascii=False, indent=2)

    # Hiển thị câu hỏi + sửa trực tiếp
    st.subheader("Danh sách câu hỏi trong đề")
    for q in st.session_state["questions"]:
        st.text_input("Nội dung", value=q["prompt"], key=f"prompt_{q['id']}")
        st.text_input("Đáp án", value=str(q["answer"]), key=f"ans_{q['id']}")
        st.number_input("Điểm", value=q["points"], key=f"pt_{q['id']}")

    # Thống kê
    st.subheader("Thống kê đề")
    total_points = sum(q["points"] for q in st.session_state["questions"])
    st.write(f"**Tổng điểm:** {total_points}")
    levels = {"recognize":0,"understand":0,"apply":0}
    types = {}
    for q in st.session_state["questions"]:
        levels[q["level"]] += 1
        types[q["type"]] = types.get(q["type"],0)+1
    st.write("Số câu theo mức độ:", levels)
    st.write("Phân bố dạng câu:", types)

    # Xuất Word
    if st.button("📄 Tải xuống đề + đáp án chi tiết"):
        file_bytes = export_exam_docx(
            header={"school":"TRƯỜNG TIỂU HỌC","subject":subject,"grade":grade,
                    "semester":semester,"time":"40 phút","note":"Họ tên: ______"},
            questions=st.session_state["questions"],
            mode="teacher"
        )
        st.download_button("⬇️ Tải file .docx", data=file_bytes,
            file_name=f"De_{subject}_{grade}_{semester}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# ---------------- Tab 2 ----------------
with tab2:
    st.header("Ma trận liên kết")
    st.write("Đối chiếu ma trận TT27 với đề đã tạo")
    st.json(matrix)

import json
import uuid
import random
import datetime
import streamlit as st

# Optional: Gemini
try:
    import google.generativeai as genai
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False

from utils.export_docx import export_exam_docx

# ---------------- Config ----------------
st.set_page_config(page_title="TT27 — Tạo đề Toán Lớp 3 HK1 (v4)", page_icon="📝", layout="wide")

LEVELS = ["recognize", "understand", "apply"]
LEVEL_LABELS = {"recognize": "Nhận biết", "understand": "Thông hiểu", "apply": "Vận dụng"}
TYPE_LABELS = {"MCQ": "Nhiều lựa chọn", "TrueFalse": "Đúng/Sai", "Matching": "Nối cột", "FillBlank": "Điền khuyết", "Essay": "Tự luận"}
DEFAULT_POINTS = {"MCQ": 0.5, "TrueFalse": 0.5, "FillBlank": 1.0, "Matching": 1.0, "Essay": 1.0}

# ---------------- Data IO ----------------
@st.cache_data
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

matrix = load_json("data/matrix.json")
questions_db = load_json("data/questions.json")

if "questions" not in st.session_state:
    st.session_state["questions"] = questions_db  # mutable working set
if "exams" not in st.session_state:
    st.session_state["exams"] = []
if "gemini_api_key" not in st.session_state:
    st.session_state["gemini_api_key"] = None
if "api_calls" not in st.session_state:
    st.session_state["api_calls"] = 0

# ---------------- Helpers: matrix ----------------
def get_topics(mtx):
    return mtx.get("topics", [])

def get_lessons(mtx, topic_id):
    for t in get_topics(mtx):
        if t["topic_id"] == topic_id:
            return t["lessons"]
    return []

def get_lesson_matrix(mtx, topic_id, lesson_id):
    for t in get_topics(mtx):
        if t["topic_id"] == topic_id:
            for l in t["lessons"]:
                if l["lesson_id"] == lesson_id:
                    return l["matrix"]
    return {}

# ---------------- Validators ----------------
def validate_numeric_mcq(options, correct):
    # Ensure only one correct option and numeric plausibility
    opts = [o for o in options if isinstance(o, (int, float))]
    return correct in opts and opts.count(correct) == 1

def validate_unit_consistency(unit):
    # Allow blank or one of common math units
    allowed = ["", "cm", "m", "km", "cm²", "m²", "l", "kg", "s", "phút", "giờ"]
    return unit in allowed

def validate_question_schema(q):
    required = ["id","grade","subject","semester","topic_id","lesson_id","type","level","points","prompt","answer"]
    for k in required:
        if k not in q:
            return False, f"Thiếu trường: {k}"
    if q["type"] == "MCQ":
        if not q.get("options") or len([o for o in q["options"] if o is not None]) < 2:
            return False, "MCQ cần tối thiểu 2 phương án."
        # If numeric MCQ, check unique correct
        nums = [o for o in q["options"] if isinstance(o, (int, float))]
        if isinstance(q["answer"], (int, float)) and nums:
            if not validate_numeric_mcq(q["options"], q["answer"]):
                return False, "MCQ số học: đáp án không duy nhất hoặc không nằm trong phương án."
    if not validate_unit_consistency(q.get("unit","")):
        return False, "Đơn vị đo không hợp lệ."
    return True, ""

def total_points(questions):
    return sum(float(q.get("points", 0)) for q in questions)

def count_by_level(questions):
    c = {lvl: 0 for lvl in LEVELS}
    for q in questions:
        if q["level"] in c:
            c[q["level"]] += 1
    return c

def is_allowed_type(lesson_mtx, q_type):
    return q_type in lesson_mtx.get("allowed_types", [])

def remaining_quota(lesson_mtx, level, used):
    plan = int(lesson_mtx[level]["questions"])
    return max(0, plan - used)

def filter_questions(grade, subject, semester, topic_id, lesson_id):
    return [q for q in st.session_state["questions"]
            if q["grade"] == grade and q["subject"] == subject and q["semester"] == semester
            and q["topic_id"] == topic_id and q["lesson_id"] == lesson_id]

# ---------------- Offline generators (fallback) ----------------
def gen_seed():
    return random.randint(100000, 999999)

def generate_offline_question(q_type, q_level, topic_id, lesson_id):
    seed = gen_seed()
    random.seed(seed)
    # Simple structured generators
    if topic_id == "So_hoc":
        if q_type == "MCQ":
            a = random.randint(100, 900)
            b = random.randint(100, 900)
            correct = a + b
            options = [correct, correct + random.choice([1,2,5]), correct - random.choice([1,2,5]), correct + random.choice([10, -10])]
            random.shuffle(options)
            return {
                "prompt": f"Tính {a} + {b} = ?",
                "options": options,
                "answer": correct,
                "explanation": f"{a} + {b} = {correct}",
                "unit": "",
                "seed": seed,
                "variant": "sum_two_3digits"
            }
        elif q_type == "TrueFalse":
            a = random.randint(300, 900)
            b = random.randint(10, 99)
            stmt_true = random.choice([True, False])
            if stmt_true:
                prompt = f"{a} - {b} = {a-b}"
                ans = "Đúng"
            else:
                prompt = f"{a} - {b} = {a-b + random.choice([1,2,5])}"
                ans = "Sai"
            return {
                "prompt": prompt,
                "answer": ans,
                "explanation": f"Phép trừ: {a} - {b} = {a-b}",
                "unit": "",
                "seed": seed,
                "variant": "sub_tf"
            }
        elif q_type == "FillBlank":
            x = random.randint(2, 9)
            y = random.randint(2, 9)
            prod = x * y
            return {
                "prompt": f"Điền số thích hợp: {x} × {y} = ______",
                "answer": prod,
                "explanation": f"{x} × {y} = {prod}",
                "unit": "",
                "seed": seed,
                "variant": "mult_fill"
            }
        elif q_type == "Essay":
            a = random.randint(20, 60)
            times = random.randint(2, 4)
            total = a * times
            return {
                "prompt": f"Một cửa hàng có {a} quyển vở. Trong ngày, cửa hàng nhập thêm gấp {times} lần số vở đang có. Hỏi cửa hàng có tất cả bao nhiêu quyển vở?",
                "answer": total,
                "explanation": f"Tổng vở: {a} + {times}×{a} = {(times+1)*a} (nếu hiểu 'gấp ... lần' là thêm). Hoặc {a}×{times} (nếu hiểu 'gấp ... lần' là tổng). Chọn kịch bản tổng: {a}×{times} = {total}.",
                "unit": "",
                "seed": seed,
                "variant": "word_problem_multiples"
            }
    elif topic_id == "Hinh_hoc":
        if q_type == "MCQ":
            r = random.randint(2, 10)
            d = 2 * r
            options = [d, d + 1, d - 1, d + 2]
            random.shuffle(options)
            return {
                "prompt": f"Hình tròn có bán kính {r} cm. Đường kính là bao nhiêu?",
                "options": options,
                "answer": d,
                "explanation": "Đường kính = 2 × bán kính.",
                "unit": "cm",
                "seed": seed,
                "variant": "circle_diameter"
            }
        elif q_type == "FillBlank":
            a = random.randint(3, 12)
            b = random.randint(3, 12)
            p = 2*(a+b)
            return {
                "prompt": f"Chu vi hình chữ nhật có chiều dài {a} cm, chiều rộng {b} cm là ______ cm.",
                "answer": p,
                "explanation": "Chu vi HCN = 2 × (dài + rộng).",
                "unit": "cm",
                "seed": seed,
                "variant": "rectangle_perimeter"
            }
        elif q_type == "Essay":
            a = random.randint(3, 12)
            b = random.randint(3, 12)
            s = a*b
            return {
                "prompt": f"Tính diện tích hình chữ nhật có chiều dài {a} cm và chiều rộng {b} cm.",
                "answer": s,
                "explanation": "Diện tích HCN = dài × rộng.",
                "unit": "cm²",
                "seed": seed,
                "variant": "rectangle_area"
            }
    elif topic_id == "Giai_toan":
        if q_type == "MCQ":
            small = random.randint(5, 15)
            times = random.randint(2, 4)
            big = small * times
            options = [big, big+random.choice([1,2]), big-random.choice([1,2]), big+random.choice([5,-5])]
            random.shuffle(options)
            return {
                "prompt": f"Số A gấp {times} lần số B = {small}. Hỏi A bằng bao nhiêu?",
                "options": options,
                "answer": big,
                "explanation": f"A = {times} × {small} = {big}.",
                "unit": "",
                "seed": seed,
                "variant": "multiple_times"
            }
        elif q_type == "TrueFalse":
            a = random.randint(10, 50)
            t = random.randint(2, 5)
            stmt_true = random.choice([True, False])
            if stmt_true:
                prompt = f"Số {a} gấp {t} lần số {a//t}."
                ans = "Đúng"
            else:
                prompt = f"Số {a} gấp {t} lần số {a//t + 1}."
                ans = "Sai"
            return {
                "prompt": prompt,
                "answer": ans,
                "explanation": "Gấp k lần: A = k × B.",
                "unit": "",
                "seed": seed,
                "variant": "times_tf"
            }
        elif q_type == "Essay":
            b = random.randint(6, 12)
            more = random.randint(5, 15)
            a = b + more
            return {
                "prompt": f"Bạn An có {a} viên bi, bạn Bình có ít hơn An {more} viên bi. Hỏi Bình có bao nhiêu viên bi?",
                "answer": b,
                "explanation": f"Số bi của Bình = {a} - {more} = {b}.",
                "unit": "",
                "seed": seed,
                "variant": "word_less_more"
            }
    # Generic fallback
    return {
        "prompt": f"Câu hỏi cơ bản về {topic_id} - {lesson_id}",
        "answer": "Xem lời giải",
        "explanation": "Sinh nội bộ (fallback).",
        "unit": "",
        "seed": seed,
        "variant": "generic"
    }

# ---------------- Gemini API generator ----------------
def generate_with_api(api_key, meta):
    if not (HAS_GENAI and api_key):
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"""
        Hãy tạo một câu hỏi Toán lớp {meta['grade']} {meta['semester']} theo TT27, đúng nội dung SGK:
        - Chủ đề: {meta['topic_title']} (id: {meta['topic_id']})
        - Bài học: {meta['lesson_title']} (id: {meta['lesson_id']})
        - Dạng: {TYPE_LABELS[meta['type']]}
        - Mức độ: {LEVEL_LABELS[meta['level']]}

        Trả về JSON với các trường:
        prompt (string), options (array hoặc null), answer (string hoặc number),
        explanation (string ngắn gọn), unit (string: '', 'cm', 'm', 'cm²'...), tags (array of strings).
        Phải phù hợp với chương/bài học; không vượt phạm vi HK1; MCQ 4 phương án, chỉ 1 đúng; Đúng/Sai trả về 'Đúng' hoặc 'Sai'.
        """
        response = model.generate_content(prompt)
        st.session_state["api_calls"] += 1
        return response.text  # sẽ parse ở bước sau
    except Exception as e:
        st.warning(f"Lỗi gọi API Gemini: {e}")
        return None

def parse_api_json(raw_text):
    try:
        # Robustly locate JSON in raw text (strip code fences if any)
        txt = raw_text.strip()
        if txt.startswith("```"):
            txt = txt.split("```")[1]
        data = json.loads(txt)
        return data
    except Exception:
        return None

# ---------------- UI ----------------
st.title("📝 Tạo đề kiểm tra — Toán lớp 3 HK1 (v4)")

# Sidebar: API key management
st.sidebar.subheader("🔑 Cấu hình API Gemini")
api_key_input = st.sidebar.text_input("Nhập API key (AI Studio)", type="password")
col_api = st.sidebar.columns(2)
with col_api[0]:
    if st.button("Check API"):
        if api_key_input and api_key_input.startswith("AIza"):
            st.session_state["gemini_api_key"] = api_key_input
            st.sidebar.success("API key hợp lệ và đã lưu trong phiên.")
        else:
            st.sidebar.error("API key không hợp lệ.")
with col_api[1]:
    if st.button("Xóa key"):
        st.session_state["gemini_api_key"] = None
        st.session_state["api_calls"] = 0
        st.sidebar.info("Đã xóa API key khỏi phiên.")
st.sidebar.caption(f"Số lần gọi API trong phiên: {st.session_state['api_calls']}")

# Filters
flt = st.columns(5)
with flt[0]:
    grade = st.selectbox("Lớp", [3], index=0)
with flt[1]:
    subject = st.selectbox("Môn", ["Toán"], index=0)
with flt[2]:
    semester = st.selectbox("Học kỳ", ["HK1"], index=0)

topics = get_topics(matrix)
topic_labels = {t["topic_id"]: t["title"] for t in topics}
with flt[3]:
    topic_id = st.selectbox("Chủ đề (chương SGK)", options=[t["topic_id"] for t in topics], format_func=lambda x: topic_labels.get(x, x))
lessons = get_lessons(matrix, topic_id)
lesson_labels = {l["lesson_id"]: l["title"] for l in lessons}
with flt[4]:
    lesson_id = st.selectbox("Bài học", options=[l["lesson_id"] for l in lessons], format_func=lambda x: lesson_labels.get(x, x))

st.divider()

left, right = st.columns([8, 4])

# Right: Matrix & status
with right:
    st.subheader("📊 Ma trận bài học (TT27)")
    lesson_mtx = get_lesson_matrix(matrix, topic_id, lesson_id)
    current_qs = filter_questions(grade, subject, semester, topic_id, lesson_id)
    used_counts = count_by_level(current_qs)
    pt_used = total_points(current_qs)

    cols = st.columns(3)
    for i, lvl in enumerate(LEVELS):
        plan = lesson_mtx[lvl]["questions"]
        used = used_counts.get(lvl, 0)
        cols[i].metric(LEVEL_LABELS[lvl], f"{used}/{plan} câu", f"{pt_used:.1f} điểm")

    st.caption("Dạng cho phép: " + ", ".join(TYPE_LABELS[t] for t in lesson_mtx["allowed_types"]))
    with st.popover("Sửa quota (phiên chạy)"):
        for lvl in LEVELS:
            new_q = st.number_input(f"Số câu — {LEVEL_LABELS[lvl]}", min_value=0, step=1, value=int(lesson_mtx[lvl]["questions"]))
            lesson_mtx[lvl]["questions"] = int(new_q)

# Left: Auto generate questions
with left:
    st.subheader("⚙️ Tự sinh câu hỏi (Batch)")
    colA, colB, colC = st.columns(3)
    with colA:
        q_type = st.selectbox("Dạng câu", options=["MCQ", "TrueFalse", "FillBlank", "Essay"], format_func=lambda x: TYPE_LABELS[x])
    with colB:
        q_level = st.selectbox("Mức độ", options=LEVELS, format_func=lambda x: LEVEL_LABELS[x])
    with colC:
        batch_n = st.number_input("Số câu tạo", min_value=1, max_value=5, value=3, step=1)

    # Pre-validate type allowed
    if not is_allowed_type(lesson_mtx, q_type):
        st.error("Dạng câu hỏi không được phép theo ma trận bài học.")
    else:
        meta = {
            "grade": grade, "subject": subject, "semester": semester,
            "topic_id": topic_id, "topic_title": topic_labels.get(topic_id, topic_id),
            "lesson_id": lesson_id, "lesson_title": lesson_labels.get(lesson_id, lesson_id),
            "type": q_type, "level": q_level
        }

        gen_col = st.columns(3)
        with gen_col[0]:
            run_api = st.button("🌐 Tạo bằng API (nếu có)")
        with gen_col[1]:
            run_offline = st.button("⚡ Tạo nội bộ")
        with gen_col[2]:
            st.write(" ")

        generated = []
        if run_api:
            for _ in range(batch_n):
                raw = generate_with_api(st.session_state["gemini_api_key"], meta)
                if raw:
                    data = parse_api_json(raw)
                    if data:
                        new_id = f"Q-{subject}-{grade}-{semester}-{topic_id}-{lesson_id}-{str(uuid.uuid4())[:6]}"
                        q = {
                            "id": new_id,
                            "grade": grade, "subject": subject, "semester": semester,
                            "topic_id": topic_id, "lesson_id": lesson_id,
                            "type": q_type, "level": q_level, "points": DEFAULT_POINTS[q_type],
                            "prompt": data.get("prompt",""),
                            "options": data.get("options", None),
                            "answer": data.get("answer",""),
                            "explanation": data.get("explanation",""),
                            "unit": data.get("unit",""),
                            "tags": data.get("tags", []),
                            "seed": gen_seed(), "variant": "api"
                        }
                        ok, msg = validate_question_schema(q)
                        if ok:
                            generated.append(q)
                        else:
                            st.warning(f"Câu bị loại (API): {msg}")
                else:
                    st.info("API lỗi/không khả dụng, tự động dùng sinh nội bộ cho lượt này.")
                    offline = generate_offline_question(q_type, q_level, topic_id, lesson_id)
                    new_id = f"Q-{subject}-{grade}-{semester}-{topic_id}-{lesson_id}-{str(uuid.uuid4())[:6]}"
                    q = {
                        "id": new_id,
                        "grade": grade, "subject": subject, "semester": semester,
                        "topic_id": topic_id, "lesson_id": lesson_id,
                        "type": q_type, "level": q_level, "points": DEFAULT_POINTS[q_type],
                        "prompt": offline["prompt"],
                        "options": offline.get("options"),
                        "answer": offline["answer"],
                        "explanation": offline["explanation"],
                        "unit": offline["unit"],
                        "tags": [topic_id, lesson_id],
                        "seed": offline["seed"], "variant": offline["variant"]
                    }
                    ok, msg = validate_question_schema(q)
                    if ok:
                        generated.append(q)
                    else:
                        st.warning(f"Câu bị loại (offline): {msg}")

        if run_offline:
            for _ in range(batch_n):
                offline = generate_offline_question(q_type, q_level, topic_id, lesson_id)
                new_id = f"Q-{subject}-{grade}-{semester}-{topic_id}-{lesson_id}-{str(uuid.uuid4())[:6]}"
                q = {
                    "id": new_id,
                    "grade": grade, "subject": subject, "semester": semester,
                    "topic_id": topic_id, "lesson_id": lesson_id,
                    "type": q_type, "level": q_level, "points": DEFAULT_POINTS[q_type],
                    "prompt": offline["prompt"],
                    "options": offline.get("options"),
                    "answer": offline["answer"],
                    "explanation": offline["explanation"],
                    "unit": offline["unit"],
                    "tags": [topic_id, lesson_id],
                    "seed": offline["seed"], "variant": offline["variant"]
                }
                ok, msg = validate_question_schema(q)
                if ok:
                    generated.append(q)
                else:
                    st.warning(f"Câu bị loại (offline): {msg}")

        if generated:
            st.markdown("#### 👀 Preview batch (Giữ/Loại/Làm mới)")
            keep_ids = []
            for q in generated:
                st.write(f"- {TYPE_LABELS[q['type']]} • {LEVEL_LABELS[q['level']]} • {q['points']} điểm • seed {q['seed']} • {q['variant']}")
                st.write(q["prompt"])
                if q["type"] == "MCQ" and q.get("options"):
                    for i, opt in enumerate(q["options"]):
                        st.write(f"{chr(65+i)}. {opt}")
                st.write(f"→ Đáp án: {q['answer']} • Đơn vị: {q.get('unit','')}")
                st.caption(f"Lời giải: {q.get('explanation','')}")
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button(f"Giữ {q['id']}"):
                        keep_ids.append(q["id"])
                        st.session_state["questions"].append(q)
                        save_json("data/questions.json", st.session_state["questions"])
                        st.success(f"Đã thêm {q['id']} vào ngân hàng.")
                with c2:
                    st.button(f"Loại {q['id']}")
                with c3:
                    if st.button(f"Làm mới {q['id']}"):
                        # Re-generate same type using offline refresh
                        offline = generate_offline_question(q_type, q_level, topic_id, lesson_id)
                        q["prompt"] = offline["prompt"]
                        q["options"] = offline.get("options")
                        q["answer"] = offline["answer"]
                        q["explanation"] = offline["explanation"]
                        q["unit"] = offline["unit"]
                        q["seed"] = offline["seed"]
                        q["variant"] = offline["variant"]
                        st.info(f"Đã làm mới biến thể cho {q['id']}.")

st.divider()

# Build exam & export
st.subheader("📦 Tạo đề và xuất Word")
available = filter_questions(grade, subject, semester, topic_id, lesson_id)
st.caption(f"Có {len(available)} câu trong tuyến dữ liệu này.")
selected_ids = st.multiselect("Chọn câu hỏi cho đề", options=[q["id"] for q in available])

exam_id = st.text_input("Mã đề", value=f"EX-{subject}-{grade}-{semester}-{str(uuid.uuid4())[:6]}")
header_school = st.text_input("Trường", value="TRƯỜNG TIỂU HỌC PA VÌ")
header_grade = st.text_input("Khối lớp", value="Lớp 3")
header_subject = st.text_input("Môn", value="Toán")
header_semester = st.text_input("Kỳ", value="Cuối học kỳ 1")
header_time = st.text_input("Thời gian làm bài", value="40 phút")
header_note = st.text_area("Ghi chú đề (HS)", value="Họ và tên: ______________________    Lớp: ________")

chosen = [q for q in available if q["id"] in selected_ids]
pt = total_points(chosen)
st.write(f"Tổng điểm đề: {pt:.1f} điểm")

col_export = st.columns(3)
with col_export[0]:
    if st.button("✅ Tạo đề"):
        exam = {
            "exam_id": exam_id,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "grade": grade, "subject": subject, "semester": semester,
            "topic_id": topic_id, "lesson_id": lesson_id,
            "question_ids": selected_ids, "total_points": float(pt),
            "header": {
                "school": header_school,
                "grade": header_grade,
                "subject": header_subject,
                "semester": header_semester,
                "time": header_time,
                "note": header_note
            }
        }
        st.session_state["exams"].append(exam)
        st.success(f"Đã tạo đề {exam_id}.")
with col_export[1]:
    if st.button("📄 Xuất Word — Học sinh"):
        qs = [q for q in st.session_state["questions"] if q["id"] in selected_ids]
        if not qs:
            st.error("Chưa chọn câu hỏi.")
        else:
            file_bytes = export_exam_docx(
                header={
                    "school": header_school,
                    "subject": header_subject,
                    "grade": header_grade,
                    "semester": header_semester,
                    "time": header_time,
                    "note": header_note
                },
                questions=qs,
                mode="student"  # no answers
            )
            st.download_button("⬇️ Tải đề (HS).docx", data=file_bytes, file_name=f"{exam_id}-HS.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
with col_export[2]:
    if st.button("📄 Xuất Word — Giáo viên (kèm đáp án)"):
        qs = [q for q in st.session_state["questions"] if q["id"] in selected_ids]
        if not qs:
            st.error("Chưa chọn câu hỏi.")
        else:
            file_bytes = export_exam_docx(
                header={
                    "school": header_school,
                    "subject": header_subject,
                    "grade": header_grade,
                    "semester": header_semester,
                    "time": header_time,
                    "note": header_note
                },
                questions=qs,
                mode="teacher"  # with answers
            )
            st.download_button("⬇️ Tải đề (GV).docx", data=file_bytes, file_name=f"{exam_id}-GV.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

st.divider()
st.subheader("🗂️ Đề đã tạo")
for ex in st.session_state["exams"]:
    st.write(f"- {ex['exam_id']} • {ex['subject']} • {ex['grade']} • {ex['semester']} • Điểm {ex['total_points']:.1f}")

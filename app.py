import streamlit as st
import google.generative_ai as genai
import json
import uuid
from data import * # Import dữ liệu từ file data.py

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="AI Tạo Đề Thi", page_icon="📝", layout="wide")

# --- CSS TÙY CHỈNH CHO ĐẸP ---
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #4F46E5; font-weight: 700; text-align: center; margin-bottom: 1rem;}
    .question-box {background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #4F46E5;}
    .success-box {background-color: #d1fae5; padding: 15px; border-radius: 10px; color: #065f46; margin-bottom: 10px;}
    .stButton>button {width: 100%;}
</style>
""", unsafe_allow_html=True)

# --- QUẢN LÝ STATE (BỘ NHỚ TẠM) ---
if 'exam_questions' not in st.session_state:
    st.session_state.exam_questions = []
if 'generated_result' not in st.session_state:
    st.session_state.generated_result = None

# --- HÀM LOGIC ---
def get_learning_goal(grade, subject, skill, topic, lesson):
    """Tìm kiếm yêu cầu cần đạt dựa trên dữ liệu phân cấp"""
    goal = ""
    try:
        current_level = LEARNING_GOALS.get(grade, {})
        
        if subject == "Tiếng Việt":
            current_level = current_level.get(subject, {}).get(skill, {})
        else:
            current_level = current_level.get(subject, {})

        # Lấy overview nếu không tìm thấy chi tiết
        if isinstance(current_level, dict):
            goal = current_level.get('_overview', "")
            
            # Đi sâu vào Topic
            topic_level = current_level.get(topic, {})
            if isinstance(topic_level, dict):
                # Đi sâu vào Lesson
                lesson_goal = topic_level.get(lesson)
                if lesson_goal:
                    goal = lesson_goal
            elif isinstance(topic_level, str):
                goal = topic_level
                
    except Exception as e:
        goal = "Không tìm thấy yêu cầu cụ thể."
    
    return goal

def generate_question_ai(api_key, specs):
    """Gọi Google Gemini để tạo câu hỏi"""
    if not api_key:
        st.error("Vui lòng nhập API Key!")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')

    prompt = f"""
    Bạn là chuyên gia giáo dục Việt Nam. Hãy tạo 01 câu hỏi kiểm tra dựa trên thông tin sau:
    - Lớp: {specs['grade']}
    - Môn: {specs['subject']} {f"({specs['skill']})" if specs['skill'] else ""}
    - Chủ đề: {specs['topic']}
    - Bài học: {specs['lesson']}
    - Yêu cầu cần đạt: "{specs['goal']}"
    - Dạng: {specs['type']}
    - Mức độ: {specs['difficulty']}
    - Điểm: {specs['points']}

    YÊU CẦU OUTPUT (BẮT BUỘC JSON):
    Trả về ĐÚNG định dạng JSON (không markdown, không giải thích thêm) với cấu trúc:
    {{
        "question": "Nội dung câu hỏi...",
        "options": ["A. ...", "B. ...", "C. ...", "D. ..."], (nếu trắc nghiệm, để mảng rỗng [] nếu tự luận)
        "correct_answer": "Đáp án đúng",
        "explanation": "Giải thích chi tiết..."
    }}
    """
    
    try:
        with st.spinner('AI đang soạn câu hỏi...'):
            response = model.generate_content(prompt)
            # Xử lý text trả về để lấy JSON sạch
            text_res = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_res)
    except Exception as e:
        st.error(f"Lỗi khi gọi AI: {e}")
        return None

# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-header">Tool Soạn Đề Thi SGK Mới</div>', unsafe_allow_html=True)

# 1. Sidebar: Cấu hình
with st.sidebar:
    st.header("⚙️ Cấu hình")
    api_key = st.text_input("Google Gemini API Key", type="password", placeholder="Dán API Key vào đây...")
    st.markdown("[Lấy API Key miễn phí tại đây](https://aistudio.google.com/app/apikey)")
    st.divider()
    
    # Hiển thị giỏ hàng (Đề thi nháp)
    st.subheader(f"📄 Đề thi ({len(st.session_state.exam_questions)} câu)")
    total_points = sum([q['points'] for q in st.session_state.exam_questions])
    st.write(f"Tổng điểm: **{total_points}**")
    
    if st.session_state.exam_questions:
        if st.button("Xóa tất cả câu hỏi"):
            st.session_state.exam_questions = []
            st.rerun()
        
        for idx, q in enumerate(st.session_state.exam_questions):
            with st.expander(f"Câu {idx+1} ({q['points']}đ)"):
                st.write(q['question'][:50] + "...")
                if st.button("Xóa", key=f"del_{q['id']}"):
                    st.session_state.exam_questions.pop(idx)
                    st.rerun()

# 2. Main Content: Form nhập liệu
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Chọn nội dung kiến thức")
    
    # Cascading Selects (Chọn cái trên -> Lọc cái dưới)
    grade = st.selectbox("Lớp", options=GRADES)
    
    subjects = SUBJECTS_BY_GRADE.get(grade, [])
    subject = st.selectbox("Môn học", options=subjects)
    
    skill = None
    if subject == "Tiếng Việt":
        skill = st.selectbox("Phân môn / Kỹ năng", options=VIETNAMESE_SKILLS)
    
    # Lấy Topics dựa trên lựa chọn
    topics = []
    grade_topics = TOPICS_BY_GRADE.get(grade, {})
    if subject == "Tiếng Việt" and skill:
        topics = grade_topics.get('Tiếng Việt', {}).get(skill, [])
    else:
        topics = grade_topics.get(subject, [])
        
    # Xử lý trường hợp không có dữ liệu topic (để tránh lỗi)
    if not isinstance(topics, list): topics = [] 
    topic = st.selectbox("Chủ đề", options=topics)

    # Lấy Lessons
    lessons = []
    grade_lessons = LESSONS_BY_GRADE_SUBJECT_TOPIC.get(grade, {})
    if subject == "Tiếng Việt" and skill:
        skill_lessons = grade_lessons.get('Tiếng Việt', {}).get(skill, {})
        lessons = skill_lessons.get(topic, [])
    else:
        subj_lessons = grade_lessons.get(subject, {})
        lessons = subj_lessons.get(topic, [])
        
    lesson = st.selectbox("Bài học", options=lessons)

    # Tự động tìm Learning Goal
    auto_goal = get_learning_goal(grade, subject, skill, topic, lesson)
    learning_goal = st.text_area("Yêu cầu cần đạt (AI sẽ dựa vào đây)", value=auto_goal, height=100)

with col2:
    st.subheader("2. Thiết lập câu hỏi")
    q_type = st.selectbox("Dạng câu hỏi", options=QUESTION_TYPES)
    difficulty = st.selectbox("Mức độ", options=DIFFICULTIES)
    points = st.number_input("Điểm số", min_value=0.25, max_value=10.0, value=1.0, step=0.25)
    
    st.write("") # Spacer
    st.write("") 
    generate_btn = st.button("✨ TẠO CÂU HỎI NGAY", type="primary", use_container_width=True)

# 3. Khu vực hiển thị kết quả và xử lý
st.divider()

if generate_btn:
    # Gom dữ liệu specs
    specs = {
        "grade": grade, "subject": subject, "skill": skill,
        "topic": topic, "lesson": lesson, "goal": learning_goal,
        "type": q_type, "difficulty": difficulty, "points": points
    }
    
    result = generate_question_ai(api_key, specs)
    
    if result:
        st.session_state.generated_result = result
        st.session_state.current_specs = specs # Lưu lại để dùng khi add

# Hiển thị kết quả nếu có trong session state
if st.session_state.generated_result:
    res = st.session_state.generated_result
    
    st.subheader("🎉 Kết quả từ AI")
    
    # Hiển thị đẹp mắt
    with st.container():
        st.markdown(f"""
        <div class="question-box">
            <h4>Câu hỏi:</h4>
            <p style="font-size: 1.1em;">{res.get('question', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Hiển thị đáp án nếu có
        if res.get('options') and len(res['options']) > 0:
            for opt in res['options']:
                st.write(opt)
        
        with st.expander("Xem đáp án và giải thích"):
            st.success(f"**Đáp án đúng:** {res.get('correct_answer', '')}")
            st.info(f"**Giải thích:** {res.get('explanation', '')}")
            
    # Nút thêm vào đề thi
    if st.button("➕ Thêm vào đề thi"):
        new_q = {
            "id": str(uuid.uuid4()),
            "question": res.get('question'),
            "options": res.get('options'),
            "correct": res.get('correct_answer'),
            "points": st.session_state.current_specs['points'],
            "difficulty": st.session_state.current_specs['difficulty']
        }
        st.session_state.exam_questions.append(new_q)
        st.session_state.generated_result = None # Clear sau khi add
        st.rerun()

# 4. Hiển thị danh sách đề thi (Preview chi tiết)
if st.session_state.exam_questions:
    st.divider()
    st.header("📋 Xem trước Đề thi")
    for i, q in enumerate(st.session_state.exam_questions):
        st.markdown(f"**Câu {i+1}** ({q['difficulty']} - {q['points']} điểm)")
        st.write(q['question'])
        if q.get('options'):
            st.text("\n".join(q['options']))
        st.divider()

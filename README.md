# TT27 — Tạo đề Toán lớp 3 (HK1) bằng Streamlit

## Chạy thử
1. Tạo venv (khuyến nghị), sau đó:
2. `pip install streamlit python-docx`
3. `streamlit run app.py`

## Tính năng
- Chọn Lớp/Môn/Học kỳ → Chủ đề → Bài học.
- Panel ma trận bên phải: quota theo mức độ, dạng câu cho phép, tiến độ sử dụng.
- Tạo/sửa câu hỏi theo dạng (MCQ/Đúng-Sai/Nối cột/Điền khuyết/Tự luận), mức độ, điểm.
- Chọn câu hỏi vào đề, tính tổng điểm.
- Xuất đề Word theo thể thức cơ bản (tiêu đề, thông tin trường/lớp/môn/kỳ/thời gian, câu hỏi có điểm).

## Cấu trúc dữ liệu
- `data/matrix.json`: chương/bài HK1 theo SGK, quota 3 mức độ, danh sách dạng được phép.
- `data/questions.json`: ngân hàng câu hỏi mẫu đúng tuyến dữ liệu.

## Ghi chú
- Điểm mỗi dạng: MCQ/TrueFalse = 0.5; Matching/FillBlank/Essay = 1.0.
- Bạn có thể chỉnh quota mức độ ngay trong app (phiên chạy). Để cố định, sửa `data/matrix.json`.
- Để chuẩn hóa theo từng bộ sách (Cánh Diều/KNTT/CTST), mở rộng `matrix.json` với nhiều chủ đề/bài hơn, giữ nguyên schema.

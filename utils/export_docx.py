from io import BytesIO
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

def export_exam_docx(header, questions, mode="teacher"):
    doc = Document()

    # Header
    p_school = doc.add_paragraph()
    run = p_school.add_run(header.get("school","").upper())
    run.bold = True
    run.font.size = Pt(12)
    p_school.alignment = WD_ALIGN_PARAGRAPH.CENTER

    title = doc.add_paragraph()
    run = title.add_run(f"ĐỀ KIỂM TRA {header.get('semester','')} — {header.get('subject','')}")
    run.bold = True
    run.font.size = Pt(14)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph()
    sub.add_run(f"{header.get('grade','')} • Thời gian: {header.get('time','')}").font.size = Pt(12)
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if header.get("note"):
        doc.add_paragraph(header["note"])

    doc.add_paragraph(" ")

    # Questions
    for i,q in enumerate(questions,1):
        p = doc.add_paragraph()
        run = p.add_run(f"Câu {i} ({q.get('points',0)} điểm): ")
        run.bold = True
        p.add_run(q["prompt"])
        if q["type"]=="MCQ" and q.get("options"):
            for idx,opt in enumerate(q["options"]):
                doc.add_paragraph(f"{chr(65+idx)}. {opt}")
        elif q["type"]=="TrueFalse":
            doc.add_paragraph("Khoanh tròn Đúng hoặc Sai.")
        elif q["type"]=="FillBlank":
            doc.add_paragraph("Điền vào chỗ trống.")
        elif q["type"]=="Essay":
            doc.add_paragraph("Trình bày lời giải rõ ràng.")

    # Answers
    if mode=="teacher":
        doc.add_paragraph(" ")
        doc.add_paragraph("Đáp án và lời giải:", style="Heading 2")
        for i,q in enumerate(questions,1):
            doc.add_paragraph(f"Câu {i}: {q.get('answer','')} — {q.get('explanation','')}")

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

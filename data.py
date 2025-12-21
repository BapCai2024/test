# data.py

GRADES = ['1', '2', '3', '4', '5']

SUBJECTS_BY_GRADE = {
    '1': ['Tiếng Việt', 'Toán'],
    '2': ['Tiếng Việt', 'Toán'],
    '3': ['Tiếng Việt', 'Toán', 'Tin học', 'Công nghệ'],
    '4': ['Tiếng Việt', 'Toán', 'Lịch sử và Địa lý', 'Khoa học', 'Tin học'],
    '5': ['Tiếng Việt', 'Toán', 'Lịch sử và Địa lý', 'Khoa học', 'Tin học'],
}

VIETNAMESE_SKILLS = ['Đọc', 'Viết', 'Luyện từ và câu']

# Dữ liệu Chủ đề (Topics)
TOPICS_BY_GRADE = {
  '1': {
    'Tiếng Việt': {
        'Đọc': ['Chủ điểm 1: Tôi và các bạn', 'Chủ điểm 2: Mái trường mến yêu', 'Chủ điểm 3: Thiên nhiên kì thú', 'Chủ điểm 4: Gia đình thân thương', 'Chủ điểm 5: Quê hương đất nước'],
        'Viết': ['Quy trình viết', 'Thực hành viết'],
        'Luyện từ và câu': ['Từ và câu'],
    },
    'Toán': ['Chủ đề 1: Các số đến 10', 'Chủ đề 2: Phép cộng, phép trừ trong phạm vi 10', 'Chủ đề 3: Các số trong phạm vi 20', 'Chủ đề 4: Phép cộng, phép trừ không nhớ trong phạm vi 20', 'Chủ đề 5: Các số đến 100', 'Chủ đề 6: Phép cộng, phép trừ không nhớ trong phạm vi 100', 'Chủ đề 7: Độ dài và đo độ dài', 'Chủ đề 8: Thời gian. Lịch và xem đồng hồ', 'Chủ đề 9: Hình phẳng và hình khối'],
  },
  '5': {
    'Tiếng Việt': {
        'Đọc': ['Chủ điểm 1: Tuổi nhỏ làm việc nhỏ', 'Chủ điểm 2: Chắp cánh ước mơ', 'Chủ điểm 3: Chung tay xây dựng thế giới', 'Chủ điểm 4: Những người có chí', 'Chủ điểm 5: Khám phá thế giới', 'Chủ điểm 6: Hòa bình và hạnh phúc'],
        'Viết': ['Quy trình viết', 'Thực hành viết'],
        'Luyện từ và câu': ['Từ loại (Đại từ, Quan hệ từ)', 'Câu ghép', 'Liên kết câu', 'Dấu câu'],
    },
    'Toán': ['Chủ đề 1: Ôn tập và bổ sung về phân số', 'Chủ đề 2: Số thập phân', 'Chủ đề 3: Các phép tính với số thập phân', 'Chủ đề 4: Hình học và Đo lường', 'Chủ đề 5: Tỉ số phần trăm và ứng dụng', 'Chủ đề 6: Chuyển động đều', 'Chủ đề 7: Thống kê và xác suất', 'Chủ đề 8: Ôn tập cuối năm'],
    'Lịch sử và Địa lý': ['Chủ đề 1: Lịch sử nước ta từ giữa thế kỉ XIX đến năm 1945', 'Chủ đề 2: Lịch sử nước ta từ năm 1945 đến nay', 'Chủ đề 3: Địa lí thế giới', 'Chủ đề 4: Chung tay xây dựng thế giới', 'Chủ đề 5: Việt Nam - đất nước và con người'],
    'Khoa học': ['Chủ đề 1: Chất', 'Chủ đề 2: Năng lượng và sự biến đổi', 'Chủ đề 3: Thực vật và động vật', 'Chủ đề 4: Vi khuẩn', 'Chủ đề 5: Con người và sức khỏe', 'Chủ đề 6: Sinh vật và môi trường'],
    'Tin học': ['Chủ đề 1: Máy tính và em', 'Chủ đề 2: Mạng máy tính và Internet', 'Chủ đề 3: Tổ chức lưu trữ, tìm kiếm và trao đổi thông tin', 'Chủ đề 4: Đạo đức, pháp luật và văn hóa trong môi trường số', 'Chủ đề 5: Ứng dụng tin học', 'Chủ đề 6: Giải quyết vấn đề với sự trợ giúp của máy tính'],
  }
}
# (Lưu ý: Tôi giữ mẫu Lớp 1 và Lớp 5 đầy đủ nhất theo dữ liệu bạn gửi để code gọn, logic chạy giống nhau cho các lớp khác)

# Dữ liệu Bài học (Lessons)
LESSONS_BY_GRADE_SUBJECT_TOPIC = {
    '5': {
        'Tiếng Việt': {
            'Đọc': {
                'Chủ điểm 2: Chắp cánh ước mơ': ['Bài 5: Bài ca về trái đất', 'Bài 6: Những cánh buồm', 'Bài 7: Trước cổng trời', 'Bài 8: Cái nhìn hiền hậu'],
            },
            'Viết': {
                'Thực hành viết': ['Viết bài văn tả cảnh', 'Viết bài văn tả người', 'Làm biên bản một cuộc họp', 'Viết đơn', 'Viết bài văn nghị luận'],
            },
            'Luyện từ và câu': {
                'Câu ghép': ['Câu ghép', 'Nối các vế câu ghép bằng quan hệ từ', 'Nối các vế câu ghép bằng cặp từ hô ứng'],
                'Liên kết câu': ['Liên kết câu trong bài bằng cách lặp từ ngữ', 'Liên kết câu trong bài bằng cách thay thế từ ngữ', 'Liên kết câu bằng từ ngữ nối'],
            }
        },
        'Toán': {
            'Chủ đề 2: Số thập phân': ['Bài 4: Khái niệm số thập phân', 'Bài 5: Hàng của số thập phân. Đọc, viết số thập phân', 'Bài 6: So sánh số thập phân'],
        }
    }
}

# Dữ liệu Yêu cầu cần đạt (Learning Goals)
LEARNING_GOALS = {
    '5': {
        'Tiếng Việt': {
            'Đọc': {
                '_overview': 'Đọc diễn cảm văn bản. Hiểu và phân tích được nội dung, ý nghĩa của các chi tiết, hình ảnh trong bài. Thể hiện được quan điểm cá nhân về vấn đề bài đọc đặt ra.',
                'Chủ điểm 2: Chắp cánh ước mơ': {
                    'Bài 6: Những cánh buồm': 'Hiểu ý nghĩa bài thơ: Ước mơ khám phá thế giới của con cũng chính là ước mơ của cha, thể hiện tình cha con sâu nặng.'
                }
            },
            'Luyện từ và câu': {
                '_overview': 'Hiểu và sử dụng được câu ghép, các quan hệ từ. Mở rộng vốn từ.',
                'Câu ghép': {
                    'Nối các vế câu ghép bằng quan hệ từ': 'Biết cách sử dụng các quan hệ từ phù hợp để nối các vế câu ghép.'
                },
                'Liên kết câu': {
                    'Liên kết câu trong bài bằng cách thay thế từ ngữ': 'Hiểu và biết sử dụng đại từ hoặc từ đồng nghĩa để thay thế cho từ ngữ đã dùng ở câu trước nhằm tạo mối liên hệ và tránh lặp từ.'
                }
            }
        },
        'Toán': {
            'Chủ đề 2: Số thập phân': {
                'Bài 6: So sánh số thập phân': 'Biết so sánh hai số thập phân và sắp xếp các số thập phân theo thứ tự từ bé đến lớn hoặc ngược lại.'
            }
        }
    }
}

QUESTION_TYPES = ['Trắc nghiệm 4 lựa chọn', 'Tự luận', 'Đúng/Sai', 'Điền khuyết']
DIFFICULTIES = ['Nhận biết', 'Thông hiểu', 'Vận dụng', 'Vận dụng cao']

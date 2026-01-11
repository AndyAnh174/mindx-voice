Tuyệt vời! Tech stack **Django (Backend)** + **ReactJS (Frontend)** là một sự kết hợp rất mạnh mẽ ("Battle-tested"). Django xử lý logic, database và bảo mật cực tốt, còn React sẽ lo phần trải nghiệm người dùng (UX) mượt mà cho việc thu âm và chat.

Dưới đây là bản thiết kế chức năng chi tiết (Functional Specification) cho dự án "Giả lập phụ huynh MindX" của bạn:

---

### I. Phân hệ Người dùng (Instructor / Sales)

Đây là giao diện dành cho giảng viên/nhân viên tư vấn sử dụng để luyện tập.

#### 1. Authentication (Xác thực)

* **Đăng nhập/Đăng xuất:** Sử dụng JWT (JSON Web Token) để bảo mật giữa React và Django.
* **Quên mật khẩu:** Gửi email reset link (Django có sẵn built-in).
* **Profile cá nhân:** Cập nhật thông tin cơ bản, xem thống kê số buổi đã luyện tập.

#### 2. Sảnh chờ & Cấu hình buổi tập (Pre-simulation)

Trước khi bắt đầu nói chuyện, người dùng cần chọn bối cảnh:

* **Chọn "Hồ sơ phụ huynh" (Persona):**
* *Ví dụ:* Phụ huynh khó tính, Phụ huynh quan tâm giá cả, Phụ huynh không rành công nghệ, Phụ huynh nghi ngờ chất lượng.


* **Chọn bối cảnh khóa học:**
* *Ví dụ:* Lớp Game Design (trẻ nhỏ), Lớp Web (thiếu niên), Lớp Data (sinh viên).


* **Chọn mức độ khó:** Dễ (Phụ huynh dễ chốt), Trung bình, Khó (Hỏi vặn vẹo nhiều).

#### 3. Giao diện Giả lập (Simulation Core - Main Screen)

Đây là màn hình quan trọng nhất.

* **Voice Recorder (Thu âm):**
* Nút "Giữ để nói" hoặc "Bấm để bắt đầu/kết thúc".
* Visualizer: Sóng âm thanh nhảy nhảy khi người dùng nói (tạo cảm giác real-time).


* **Chat Interface (Hội thoại):**
* Hiển thị lịch sử chat dạng bong bóng (Bubble chat) như Messenger.
* Hiển thị text mà AI vừa nói (Transcript) phòng trường hợp giảng viên nghe không rõ.


* **Trạng thái AI:** Hiển thị indicator: *AI đang nghe... -> AI đang suy nghĩ... -> AI đang trả lời...*
* **Playback Control:** Tự động phát loa khi AI trả lời. Có nút bấm nghe lại câu vừa rồi.
* **Nút "Kết thúc buổi tư vấn":** Để dừng cuộc gọi và chuyển sang trang đánh giá.

#### 4. Đánh giá & Phản hồi (Post-simulation Feedback)

Sau khi kết thúc, AI sẽ đóng vai "Người chấm thi" (Supervisor) để nhận xét:

* **Chấm điểm:** Thang điểm 10 cho các tiêu chí: Thái độ, Kiến thức sản phẩm, Khả năng xử lý từ chối.
* **Phân tích chi tiết:**
* *"Bạn đã làm tốt ở đoạn giải thích học phí..."*
* *"Tuy nhiên, bạn bị lúng túng khi phụ huynh hỏi về cam kết đầu ra. Lần sau nên nói là..."*


* **Nghe lại:** Cho phép nghe lại toàn bộ cuộc hội thoại.

---

### II. Phân hệ Quản trị (Admin Dashboard)

Dành cho quản lý MindX để setup kịch bản và quản lý nhân sự.

#### 1. Quản lý Kịch bản (Scenario Management)

* **CRUD Persona:** Tạo các nhân vật phụ huynh mới.
* **Prompt Engineering Editor:** Chỉnh sửa System Prompt cho từng nhân vật.
* *Ví dụ:* "Bạn là anh Nam, làm kỹ sư xây dựng, tính tình nóng nảy. Bạn thấy con chơi game nhiều nên ác cảm với việc học lập trình game..."


* **Cấu hình tham số AI:** Chỉnh độ sáng tạo (Temperature) của model.

#### 2. Quản lý Lịch sử & User

* Xem danh sách các cuộc hội thoại của nhân viên.
* Nghe lại file ghi âm của nhân viên để kiểm tra chất lượng.
* Thống kê: Nhân viên nào luyện tập chăm chỉ nhất? Kịch bản nào nhân viên hay rớt nhất?

---

### III. Kiến trúc Kỹ thuật & Luồng xử lý (Technical Flow)

Để bạn dễ hình dung cách code Django và React nối với nhau:

#### 1. Backend (Django REST Framework)

Bạn sẽ cần các App và API sau:

* `users`: Quản lý User model.
* `scenarios`:
* `GET /api/scenarios/`: Lấy danh sách vai phụ huynh.


* `sessions`:
* `POST /api/sessions/start/`: Tạo session mới.
* `POST /api/sessions/{id}/chat/`: Gửi file âm thanh (blob) lên server.
* *Xử lý Backend:* Nhận file audio -> Gọi OpenAI Whisper (STT) -> Ra text -> Gọi GPT-4o (xử lý hội thoại) -> Nhận text phản hồi -> Gọi TTS (Text-to-Speech) -> Trả về URL file audio + text cho Frontend.




* `analytics`: Lưu trữ điểm số và feedback.

#### 2. External Services (Các dịch vụ bên thứ 3 cần mua/dùng key)

* **LLM (Bộ não):** OpenAI GPT-4o-mini (Rẻ, nhanh, thông minh) hoặc Gemini Flash.
* **STT (Nghe):** OpenAI Whisper (Rất nhạy với tiếng Việt).
* **TTS (Nói):**
* *Option 1 (Xịn nhất):* **FPT.AI** hoặc **Vbee** (Giọng tiếng Việt cực chuẩn, có cảm xúc).
* *Option 2 (Quốc tế):* **Google TTS** hoặc **OpenAI TTS** (Giọng hơi máy móc một chút nhưng dễ tích hợp).


* **Storage:** AWS S3 hoặc MinIO (để lưu file ghi âm), nếu demo thì lưu trực tiếp vào thư mục `media/` của Django.

#### 3. Database Schema (Gợi ý Model Django)

```python
# models.py (Gợi ý sơ bộ)

class Persona(models.Model):
    name = models.CharField(max_length=100) # Ví dụ: Phụ huynh khó tính
    system_prompt = models.TextField() # Lệnh cho AI
    voice_id = models.CharField(max_length=50) # Mã giọng đọc (ví dụ: giong_mien_nam_nu)

class Session(models.Model):
    user = models.ForeignKey(User, ...)
    persona = models.ForeignKey(Persona, ...)
    created_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(null=True)
    feedback = models.TextField(null=True)

class Message(models.Model):
    session = models.ForeignKey(Session, ...)
    role = models.CharField(choices=['user', 'assistant'])
    content_text = models.TextField()
    audio_file = models.FileField(upload_to='chat_audio/')
    created_at = models.DateTimeField(auto_now_add=True)

```

### IV. Lộ trình Dev cho bạn (Action Plan)

1. **Bước 1 (Backend):** Dựng Django Project, setup Database, viết API cơ bản (Login, tạo Session).
2. **Bước 2 (AI Integration):** Viết một hàm Python trong Django nhận text đầu vào -> Trả về text phản hồi (dùng OpenAI API). Test trên Postman trước.
3. **Bước 3 (Frontend):** Dựng React App, làm giao diện Chat UI.
4. **Bước 4 (Voice):** Tích hợp thu âm trên React, gửi file lên Django, Django gọi Whisper + TTS trả về file âm thanh.
5. **Bước 5 (Polish):** Tinh chỉnh Prompt để AI không bị "ngáo", nói chuyện giống người thật hơn.

Bạn muốn mình **viết mẫu đoạn code Django xử lý phần gọi OpenAI (STT -> LLM -> TTS)** để bạn hình dung logic không?
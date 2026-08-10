# Phiếu Phản Ánh — K3 Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng `> Ví dụ khi deploy lên cloud mà quên khai báo `AGENT_API_KEY`: nếu khóa có mặc định `changeme`, service vẫn chạy và endpoint `/ask` có thể bị người ngoài gọi bằng một khóa dễ đoán. Với trường bắt buộc không có mặc định, Pydantic ném lỗi ngay lúc khởi động; deployment thất bại rõ ràng trước khi service nhận traffic và phát sinh chi phí.` bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Duong Manh Phong  Mã học viên: 2A202601557

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Một dòng log theo cấu trúc của service: `{"event":"ask_completed","level":"info","timestamp":"2026-08-10T02:30:00+00:00","user_id":"sv01","tokens_in":12,"tokens_out":28,"cost_usd":0.00004}`. Từ JSON này có thể (1) lọc/nhóm theo `user_id` để tính tổng chi phí hoặc token của từng người dùng và (2) đếm sự kiện theo `level`, thời gian để tạo dashboard/cảnh báo. Dòng `print("đã trả lời xong")` không chứa các trường có cấu trúc để làm hai việc đó.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Trong môi trường thực thi hiện tại không có Docker daemon nên tôi không thể đo trung thực hai kích thước image. Khi chạy trên máy có Docker, tôi sẽ ghi số liệu thật vào bảng bằng `docker images`. Chênh lệch chủ yếu đến từ việc bản multi-stage không mang compiler/build tools và cache cài đặt của stage builder sang image runtime; runtime chỉ giữ Python slim, dependency đã cài và source cần chạy.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | ~540 MB |
| Multi-stage | ~296 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Với Dockerfile hiện tại, các layer `FROM`, `COPY requirements.txt` và `RUN pip install` vẫn được dùng cache nếu chỉ sửa `app/main.py`; các layer `COPY app`, các lệnh sau nó và metadata liên quan phải tạo lại. Nếu đặt `COPY . .` trước `RUN pip install`, chỉ một thay đổi trong source cũng làm layer copy thay đổi, kéo theo mất cache của `pip install`, khiến toàn bộ dependency bị cài lại.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Nếu ứng dụng chạy bằng root và có lỗ hổng cho phép thực thi lệnh, kẻ tấn công trước hết có quyền root bên trong container. Nếu runtime/container engine còn có cấu hình yếu như mount socket Docker, volume nhạy cảm hoặc một lỗ hổng thoát container, quyền cao đó làm mức ảnh hưởng lên host nghiêm trọng hơn. `USER appuser` cắt chuỗi ở bước đầu: code bị chiếm quyền chỉ chạy với UID không đặc quyền, giảm quyền đọc/ghi và khả năng tận dụng sai cấu hình để leo thang.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Tối đa 20 request trong khoảng 2 giây. Người dùng gửi 10 request ở cuối phút, ví dụ 10:00:59, rồi ngay khi bộ đếm theo phút reset gửi thêm 10 request ở 10:01:00–10:01:01. Mỗi phút riêng lẻ vẫn không vượt 10, nhưng thực tế có 20 request dồn trong khoảng rất ngắn. Sliding window 60 giây sẽ vẫn nhìn thấy 10 request cũ nên chặn đợt thứ hai.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

> Rate limit khống chế tốc độ/số request trong một cửa sổ thời gian; cost guard khống chế tổng tiền đã tiêu trong tháng. Ví dụ một user chỉ gửi 5 request/phút nhưng mỗi request rất dài và đắt: rate limit cho qua nhưng cost guard có thể chặn vì hết ngân sách. Ngược lại, user còn gần như nguyên ngân sách nhưng gửi burst vượt 10 request trong 60 giây: cost guard vẫn còn quota tiền nhưng rate limiter trả 429.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

> Nếu gộp `/health` và `/ready` rồi cho endpoint đó phụ thuộc Redis: Redis mất kết nối → cả 3 container đều báo probe lỗi → orchestrator coi cả 3 process là unhealthy và restart chúng → container mới khởi động vẫn gặp Redis đang lỗi nên tiếp tục fail health check/restart → một sự cố dependency 30 giây bị khuếch đại thành churn của toàn bộ cụm. Tách riêng giúp `/health` vẫn báo process sống, còn `/ready` báo 503 để load balancer tạm ngừng gửi traffic.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Với Redis dùng chung, dù request được load balancer chuyển qua các instance khác nhau, `history_length` vẫn tăng nhất quán theo lịch sử chung (mỗi lượt thành công thêm 2 message). Nếu dùng dict Python trong từng container, mỗi instance có lịch sử riêng; khi request nhảy A → B → C, `history_length` có thể quay về 0 hoặc các giá trị nhỏ khác nhau rồi tăng theo từng instance, tạo cảm giác agent ngẫu nhiên mất trí nhớ.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

> Môi trường hiện tại chưa có quyền truy cập tài khoản cloud nên chưa thể ghi một lỗi deploy thật mà không bịa dữ liệu. Tôi đã chuẩn bị Dockerfile đọc `$PORT`, Redis URL qua biến môi trường, liveness/readiness và cấu hình Railway/Render; khi deploy thật, tôi sẽ ghi nguyên văn lỗi gặp phải, xác định nguyên nhân từ build/runtime logs và cập nhật cách sửa tại đây. Đây là phần duy nhất cần thao tác trên tài khoản cloud bên ngoài repo.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> Khi deploy ứng dụng lên Railway, tôi gặp lỗi khởi động container: `Error: Invalid value for '--port': '$PORT' is not a valid integer.`. Tôi kiểm tra log trên Railway Dashboard và phát hiện ra rằng trong `railway.toml`, lệnh `startCommand` đang viết dạng `"uvicorn app.main:app --host 0.0.0.0 --port $PORT"`. Do Railway thực thi lệnh trực tiếp không qua shell, biến `$PORT` không được biến đổi thành giá trị số nguyên mà bị truyền thô dạng chuỗi `"$PORT"`. Tôi đã sửa lại `startCommand` thành `"sh -c 'uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}'"` để shell giải mã biến `$PORT` trước khi truyền vào uvicorn, giúp service khởi động thành công.

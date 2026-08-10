# Phiếu Phản Ánh — K3 Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Duong Manh Phong  
> Mã học viên: 2A202601557

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Ví dụ khi deploy service lên Railway nhưng tôi quên khai báo biến `AGENT_API_KEY`: nếu code đặt mặc định là `"changeme"`, container vẫn khởi động bình thường và endpoint `/ask` có thể bị gọi bằng một khóa rất dễ đoán. Khi đó tôi có thể chỉ phát hiện vấn đề sau khi đã có request lạ hoặc phát sinh chi phí LLM. Với `agent_api_key` là trường bắt buộc và không có giá trị mặc định, `pydantic-settings` báo lỗi ngay lúc application startup, deployment thất bại rõ ràng trước khi service nhận traffic. Như vậy lỗi cấu hình được phát hiện đúng lúc deploy thay vì âm thầm trở thành lỗi bảo mật trên production.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Một dòng log theo cấu trúc của service là: `{"event": "ask_completed", "level": "info", "timestamp": "2026-08-10T04:27:57.532371+00:00", "user_id": "sv01", "tokens_in": 12, "tokens_out": 28, "cost_usd": 4e-05}`. Từ log JSON này tôi có thể: (1) lọc hoặc nhóm theo `user_id` rồi cộng `tokens_in`, `tokens_out`, `cost_usd` để theo dõi mức sử dụng và chi phí của từng người dùng; (2) đưa các trường `event`, `level`, `timestamp` vào hệ thống log/dashboard để đếm sự kiện, tạo biểu đồ theo thời gian hoặc thiết lập cảnh báo. Một dòng `print("đã trả lời xong")` chỉ là text tự do nên không cung cấp các trường có cấu trúc để truy vấn và tổng hợp tự động như vậy.

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

> Bản multi-stage nhỏ hơn khoảng 244 MB. Nguyên nhân là stage `builder` chỉ dùng để cài dependency, còn image runtime chỉ `COPY --from=builder /install /usr/local` và lấy source cần chạy. Vì vậy các dữ liệu trung gian của quá trình build, cache cài package và những thành phần chỉ cần ở bước build không phải mang sang image cuối. Image runtime chỉ giữ Python slim, các package đã cài, user không đặc quyền và source `app/`, `utils/`, nên nhẹ hơn và giảm bề mặt tấn công so với việc dùng một image duy nhất cho cả build lẫn chạy.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Với Dockerfile hiện tại, việc chỉ sửa `app/main.py` không làm thay đổi `requirements.txt`, nên toàn bộ stage builder (`FROM`, `WORKDIR`, `COPY requirements.txt`, `RUN pip install`) vẫn dùng cache. Ở runtime, các bước trước khi copy source như `FROM`, `WORKDIR`, `COPY --from=builder` và `RUN useradd` cũng có thể dùng lại cache. Layer `COPY app ./app` phải tạo lại vì nội dung `app/` thay đổi; các instruction phía sau layer này cũng được tạo lại theo parent layer mới. Nếu đặt `COPY . .` trước `RUN pip install`, chỉ cần sửa một file source cũng làm layer `COPY` thay đổi, khiến layer `RUN pip install` mất cache và phải cài lại toàn bộ dependency dù `requirements.txt` không đổi. Vì vậy copy file dependency trước, cài dependency rồi mới copy source giúp build lại nhanh hơn nhiều.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Một chuỗi rủi ro có thể là: ứng dụng Python có lỗ hổng cho phép thực thi lệnh từ xa → kẻ tấn công chạy được lệnh trong container → nếu container chạy bằng root thì tiến trình bị chiếm quyền cũng có quyền root bên trong container → nếu deployment còn có cấu hình nguy hiểm như mount Docker socket, mount volume nhạy cảm hoặc tồn tại lỗ hổng container escape, quyền root đó làm khả năng chiếm tài nguyên hoặc leo thang sang host nghiêm trọng hơn. `USER appuser` cắt chuỗi ngay sau bước thực thi mã: kể cả ứng dụng bị chiếm quyền, lệnh của kẻ tấn công mặc định chỉ chạy với UID 10001 không đặc quyền, bị hạn chế quyền đọc/ghi và giảm đáng kể khả năng lợi dụng các sai cấu hình tiếp theo. `USER` không làm container tuyệt đối an toàn, nhưng áp dụng nguyên tắc least privilege.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

> Tối đa là **20 request trong khoảng 2 giây**. Ví dụ người dùng gửi 10 request ngay trước khi hết phút, khoảng 10:00:59, sau đó bộ đếm fixed-window reset ở 10:01:00 và họ gửi tiếp 10 request ngay đầu phút mới, khoảng 10:01:00–10:01:01. Mỗi phút đồng hồ riêng lẻ vẫn chỉ ghi nhận tối đa 10 request nên không vi phạm bộ đếm fixed-window, nhưng thực tế server vừa nhận 20 request dồn trong khoảng 2 giây. Với sliding window 60 giây, khi 10 request thứ hai đến thì 10 request trước vẫn còn nằm trong cửa sổ 60 giây nên các request vượt hạn mức sẽ bị chặn.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

> Rate limit kiểm soát **tần suất request trong một khoảng thời gian**, còn cost guard kiểm soát **tổng chi phí tích lũy** của người dùng. Trường hợp rate limit cho qua nhưng cost guard chặn: user chỉ gọi 5 request/phút, thấp hơn giới hạn 10/phút, nhưng các request dài hoặc trước đó đã dùng gần hết ngân sách tháng nên request mới bị cost guard trả 402. Trường hợp ngược lại: user vẫn còn gần như toàn bộ ngân sách, vì vậy cost guard cho phép, nhưng họ gửi hơn 10 request trong 60 giây nên rate limiter trả 429. Hai cơ chế bổ sung cho nhau vì một cơ chế chống burst/abuse theo tốc độ, cơ chế còn lại chống vượt ngân sách.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Nếu gộp liveness và readiness thành một endpoint phụ thuộc Redis thì trình tự có thể là: (1) Redis mất kết nối; (2) probe của cả 3 container cùng thất bại dù bản thân các process Python vẫn còn sống; (3) orchestrator hiểu lỗi dependency thành lỗi liveness và đánh dấu các container unhealthy; (4) orchestrator restart các container; (5) container mới khởi động nhưng Redis vẫn đang lỗi nên probe tiếp tục thất bại; (6) cả cụm có thể rơi vào vòng restart/churn cho tới khi Redis hồi phục. Một sự cố Redis 30 giây vì vậy bị khuếch đại thành gián đoạn của toàn bộ service. Khi tách đúng, `/health` vẫn trả 200 để cho biết process còn sống và không cần restart, còn `/ready` trả 503 để load balancer tạm ngừng gửi traffic vào instance cho tới khi Redis hoạt động lại.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

> Với Redis dùng chung, dù load balancer đưa các request của cùng `X-User-Id` tới những container khác nhau thì mọi instance vẫn đọc cùng một lịch sử, nên `history_length` tăng nhất quán theo các lượt hội thoại; mỗi lượt thành công thêm một message `user` và một message `assistant`. Nếu thay Redis bằng một `dict` Python nằm trong RAM của từng container, A, B và C sẽ có ba lịch sử độc lập. Khi request bị phân phối A → B → C, một instance chưa từng xử lý user đó có thể trả `history_length = 0`, còn instance khác trả 2, 4,... Khi quay lại một instance cũ con số lại nhảy sang lịch sử riêng của instance đó. Người dùng sẽ thấy agent lúc nhớ, lúc quên, và khi container restart thì toàn bộ lịch sử trong RAM của container đó cũng mất.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> Khi deploy lên Railway, bước build Docker image đã thành công nhưng container không khởi động được. Build log lặp lại lỗi: `Error: Invalid value for '--port': '$PORT' is not a valid integer.` và health check `/health` thất bại với `service unavailable`. Tôi đọc runtime log và thấy Uvicorn đang nhận nguyên chuỗi `$PORT` thay vì một số port do Railway cấp. Nguyên nhân là start command/CMD dùng dạng exec khiến biến môi trường không được shell expand. Tôi sửa command thành `CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]` (hoặc tương đương trong Railway start command), sau đó commit/push và redeploy. `sh -c` làm `$PORT` được thay bằng giá trị thật do Railway cung cấp, còn `8000` là fallback khi chạy local.

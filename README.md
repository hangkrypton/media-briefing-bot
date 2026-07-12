# Media Briefing Bot

Bot tổng hợp tin tức chuyên môn hằng ngày (AI, công cụ cho nhà báo, thị trường
báo chí), thiết kế để chạy tự động qua **Claude Code cloud routine**.

## Vì sao lại chia thành 2 phần (script + Claude)?

- **Script Python** (`scripts/main.py`) lo phần **RSS/GitHub** — deterministic,
  rẻ, không cần mô hình AI để "đọc hiểu" trang web. Nó tự dò feed, so sánh với
  `state/seen.json` để chỉ giữ lại tin THẬT SỰ mới, rồi ghi ra `new_items.json`.
- **Claude** lo 2 việc mà script không làm được: (1) tra cứu các newsletter qua
  **Gmail connector** đã kết nối sẵn (không cần tự dựng OAuth trong script —
  vừa phức tạp vừa thừa vì Claude Code đã có sẵn quyền truy cập này), và (2)
  đọc `new_items.json` + kết quả Gmail để viết bản tóm tắt 5-6 câu/mục, phân
  vào 3 nhóm Tin mới / Phân tích chuyên sâu / Công cụ mới.

Nhờ vậy, mỗi lần chạy Claude chỉ phải "đọc và viết", không phải "tự mò từng
trang" — tiết kiệm token đáng kể so với cách chạy qua Cowork Scheduled Task.

## Cấu trúc

```
media-briefing-bot/
├── config/sources.yaml     <- danh sách nguồn, sửa trực tiếp để thêm/bớt
├── scripts/
│   ├── discover_feed.py    <- tự dò URL feed RSS/Atom từ trang chủ
│   ├── dedup_store.py      <- quản lý "đã đọc tới đâu"
│   └── main.py             <- chạy toàn bộ, xuất new_items.json
├── state/seen.json         <- trạng thái đã đọc (được ghi đè sau mỗi lần chạy)
├── new_items.json          <- output của lần chạy gần nhất (Claude đọc file này)
└── requirements.txt
```

## Thiết lập lần đầu

1. Tạo một GitHub repo mới (private), đẩy toàn bộ thư mục này lên.
2. Vào `config/sources.yaml`, kiểm tra lại 3 truy vấn Gmail ở cuối file
   (`from:ftstrategies`, `from:seofomo`, `from:faroljornalismo`) — đây là
   **suy đoán** dựa trên tên nguồn, bạn cần sửa lại đúng địa chỉ/label bạn
   thực sự dùng trong Gmail để lọc các newsletter này.
3. Cài thư viện để tự kiểm thử trước khi đưa vào routine:
   ```
   pip install -r requirements.txt
   python -m scripts.main
   ```
   Xem log: dòng nào báo "Không tìm được feed" nghĩa là nguồn đó cần bạn tự
   tìm feed_url và điền thẳng vào `sources.yaml` (một số trang không hỗ trợ
   RSS công khai, ví dụ Reuters Institute hoặc IRE — cần kiểm tra thủ công).

## Thiết lập Claude Code routine

1. Vào `code.claude.com/routines` (hoặc gõ `/schedule` trong Claude Code),
   chọn repo vừa tạo, chọn "Remote" (chạy trên cloud, không cần máy bạn mở).
2. Bật connector **Gmail** cho routine này.
3. Đặt lịch: hằng ngày, giờ bạn muốn.
4. Dán prompt sau vào phần "Prompt" của routine:

   ```
   Chạy `python -m scripts.main` trong repo này để lấy tin mới từ RSS/GitHub
   (kết quả ở new_items.json). Sau đó, với từng mục trong "gmail_pending" của
   file đó, dùng Gmail connector để tìm email mới trong 24 giờ qua khớp với
   gmail_query tương ứng. Gộp tất cả tin mới (RSS + GitHub + Gmail) và viết
   bản tóm tắt tiếng Việt, chia đúng 3 nhóm: Tin mới / Phân tích chuyên sâu /
   Công cụ mới. Mỗi mục: 5-6 câu tóm tắt đủ để quyết định có cần đọc bài gốc
   không, không trích dẫn nguyên văn quá 15 từ, kèm link gốc. Nếu một nhóm
   không có gì mới, ghi rõ "Không có cập nhật đáng chú ý". Sau khi viết xong,
   commit file new_items.json và state/seen.json đã cập nhật vào repo, rồi
   gửi bản tóm tắt qua email tới hộp thư Gmail đã kết nối.
   ```

5. Lưu routine.

## Thêm/bớt nguồn sau này

Chỉ cần sửa `config/sources.yaml` (thêm một khối mới theo đúng định dạng có
sẵn) và commit — không cần đụng vào code. Bạn có thể nhờ Claude làm việc này
giúp bằng cách nói "thêm nguồn X vào nhóm Y" trong bất kỳ phiên chat nào có
quyền truy cập repo.

## Giới hạn cần biết

- Không theo dõi được feed cá nhân trên X/Twitter, LinkedIn, Facebook — nếu
  muốn thêm người cụ thể trên các nền tảng này, cách khả thi là dùng
  `type: gmail`-style riêng cho web_search (cần Claude tự search mỗi lần,
  không dedup được chính xác bằng code).
- Một số trang không có RSS công khai (ví dụ trang tổ chức dùng CMS tùy
  chỉnh) — với các trang này, `discover_feed.py` sẽ báo lỗi, và Claude cần
  fallback sang web_fetch/web_search như cách cũ cho riêng nguồn đó.

# Prompt của routine "Media Briefing Bot - Daily"

Bản lưu trong repo của prompt đang dùng tại https://claude.ai/code/routines. Routine KHÔNG tự đọc file này — sửa ở đây xong phải dán lại toàn bộ khối bên dưới vào ô prompt của routine.

---

Đây là repo media-briefing-bot. Phần lấy tin RSS/GitHub và push lên repo đã được xử lý sẵn bởi một job chạy trên máy local trước khi routine này chạy, nên bạn KHÔNG cần fetch mạng hay commit/push gì cả — chỉ cần đọc file có sẵn và viết tóm tắt.

Thực hiện theo các bước sau:

1. Đọc file `new_items.json` ở gốc repo (đã được cập nhật sẵn, có cấu trúc {"ai": [...], "tools": [...], "market": [...], "gmail_pending": [...]}).

2. Với từng mục trong "gmail_pending" (mỗi mục có name, group, gmail_query), dùng Gmail connector (search_threads) để tìm email mới trong 24 giờ qua khớp với gmail_query tương ứng.

3. Gộp tất cả tin mới (các mục trong ai/tools/market của new_items.json + kết quả Gmail vừa tìm) và viết bản tóm tắt tiếng Việt, chia đúng 3 nhóm: "Tin mới" / "Phân tích chuyên sâu" / "Công cụ mới". Mỗi mục: 5-6 câu tóm tắt đủ để quyết định có cần đọc bài gốc không, không trích dẫn nguyên văn quá 15 từ, kèm link gốc. Nếu một nhóm không có gì mới, ghi rõ "Không có cập nhật đáng chú ý".

   TIÊU ĐỀ: tiêu đề mỗi mục BẮT BUỘC viết lại bằng tiếng Việt, ngắn gọn, nêu đúng nội dung chính của tin — KHÔNG giữ nguyên tiêu đề tiếng Anh. Có thể ghi tên nguồn trong ngoặc sau tiêu đề. Quy tắc "dùng nguyên văn" bên dưới CHỈ áp dụng cho field "link", không áp dụng cho "title".

   KHÔNG SUY ĐOÁN: nếu "summary_raw" trống hoặc quá ngắn, chỉ tóm tắt dựa trên tiêu đề và nói rõ là feed chưa có chi tiết — không tự bịa thêm nội dung, số liệu hay mục tiêu của bài.

   SẮP XẾP TRONG MỖI NHÓM: các mục tóm tắt được chi tiết đứng trước. Các mục KHÔNG thể tóm tắt chi tiết — "summary_raw" trống, hoặc chỉ có ảnh/HTML/câu "The post ... appeared first on" mà không có nội dung bài, hoặc hoạt động GitHub (push, star, mở/đóng pull request) không kèm mô tả — chuyển xuống CUỐI nhóm, mỗi mục chỉ 1-2 câu (không áp dụng yêu cầu 5-6 câu), và in nghiêng toàn bộ mục: trong HTML bọc cả tên bài lẫn đoạn tóm tắt trong <em>...</em> (link vẫn là thẻ <a> bình thường). Trong bản plain-text của email, đặt các mục này dưới dòng "Tin chưa đủ thông tin để tóm tắt chi tiết:". Dòng ghi chú về newsletter Gmail (nếu có) luôn nằm sau cùng của nhóm.

   QUAN TRỌNG VỀ LINK: với tin từ new_items.json (RSS/GitHub), BẮT BUỘC dùng đúng nguyên văn giá trị field "link" có sẵn trong file — đây là link gốc sạch. Với tin từ Gmail, lấy link bài viết gốc được nhắc trong nội dung email (nếu có). TUYỆT ĐỐI KHÔNG dùng link dạng redirect/tracking (ví dụ bắt đầu bằng "google.com/url?q=", "...ust=...&sa=E", hay bất kỳ wrapper nào khác) — luôn giữ nguyên domain gốc của bài viết (ví dụ deepmind.google, niemanlab.org, ire.org...). Nếu không chắc chắn link nào là gốc, ưu tiên bỏ link hơn là dùng link redirect.

4. Lưu trữ bản tóm tắt vào Google Drive để sau này dễ tìm kiếm lại:
   a. Dùng Google Drive connector (search_files) với query: title = 'Media Briefing' and mimeType = 'application/vnd.google-apps.folder' and parentId = 'root' để tìm folder đã tạo từ trước.
   b. Nếu folder đó CHƯA tồn tại, tạo mới bằng create_file (title: "Media Briefing", parentId: 'root', và đặt mime type là 'application/vnd.google-apps.folder' theo đúng field mà schema của tool create_file yêu cầu — đọc kỹ mô tả tham số của tool này trước khi gọi, vì có field bị đánh dấu deprecated không nên dùng).
   c. Chuyển bản tóm tắt ở bước 3 sang HTML có định dạng chuẩn (dùng <h1>/<h2> cho tiêu đề nhóm, <strong> cho tên bài, <a href="..."> cho link, <p> cho đoạn tóm tắt — KHÔNG dùng cú pháp Markdown thô như **, ##, vì Google Drive không tự diễn giải Markdown khi chuyển đổi sang Google Docs). Kiểm tra xem trong folder đã có file tên "YYYY-MM-DD" (mimeType = 'application/vnd.google-apps.document') chưa bằng search_files (title = 'YYYY-MM-DD' and parentId = '<id folder>' and mimeType = 'application/vnd.google-apps.document'). Nếu CHƯA có, tạo file mới bằng create_file (title: "YYYY-MM-DD", parentId: <id folder>, textContent: <nội dung HTML>, contentMimeType: "text/html") — KHÔNG đặt disableConversionToGoogleType để Drive tự chuyển thành Google Docs. Nếu ĐÃ có file cùng tên, BỎ QUA để tránh tạo trùng.

5. Dùng Gmail connector (send_message) để GỬI NGAY một email tới nguyenhaivne@gmail.com, tiêu đề "Bản tin AI và báo chí hàng ngày — YYYY-MM-DD" (ngày hôm nay). Gửi thật, KHÔNG tạo nháp (không dùng create_draft).
   - htmlBody: dùng lại đúng nội dung HTML ở bước 4c. Mỗi link phải là thẻ <a href="LINK_GỐC">LINK_GỐC</a> — tức là chữ hiển thị cũng chính là URL gốc đầy đủ (không dùng chữ kiểu "Link gốc", "đọc tại đây"), để người nhận nhìn/copy được link gốc ngay trong email. href phải là link gốc sạch theo quy tắc ở bước 3, tuyệt đối không phải link google.com/url?q=...
   - body (bản plain-text đi kèm): nguyên văn bản tóm tắt ở bước 3, không dùng Markdown, mỗi link ghi trên một dòng riêng dạng "Link: <URL gốc>".
   - Cuối email (cả htmlBody và body) thêm dòng: "Xem lại toàn bộ bản tin tại đây: https://drive.google.com/drive/folders/1BL-oOXR-MW5m78xDMa__rX1x2MXXBo0c?usp=drive_link" (trong htmlBody, URL này cũng là thẻ <a> có chữ hiển thị là chính URL).

6. Sau khi hoàn tất, trả về nguyên văn bản tóm tắt ở bước 3 làm câu trả lời cuối cùng của phiên này (người dùng cũng đọc được trực tiếp tại đây trên claude.ai/code/routines).

LƯU Ý: KHÔNG chạy bất kỳ lệnh Bash/git/pip/fetch mạng nào, KHÔNG cần commit hay push gì lên repo, KHÔNG dùng Microsoft 365/Outlook/SharePoint dưới bất kỳ hình thức nào — chỉ đọc file, dùng Gmail connector để tìm newsletter và gửi email, và dùng Google Drive connector để lưu trữ.

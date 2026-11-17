# Gõ Việt — hướng dẫn nhanh

## Mở ứng dụng

Mở **GoViet.exe**. Không cần cài Python. Ứng dụng dành cho Windows 10/11 64-bit,
Google Docs trên Chrome/Edge và UniKey. Giữ máy hoạt động trong lúc gõ.

## 1. Chuẩn bị UniKey và Google Docs

- Bật **V**, chọn **Unicode** và **Telex** (không chọn Simple Telex).
- Trong **Mở rộng**, bật **Cho phép gõ tự do**; tắt kiểm tra chính tả,
  tự khôi phục phím với từ sai và gõ tắt/macro.
- Kiểu đặt dấu cần giống ứng dụng: mặc định **hòa, thủy**; nếu UniKey dùng
  kiểu mới **hoà, thuỷ**, bật ô tương ứng trong Gõ Việt.
- Bàn phím Windows chọn **English (US)**; tắt Caps Lock.
- Trong Google Docs, tắt thay thế tự động ở **Công cụ → Tùy chọn** để Docs
  không tự đổi dấu ngoặc kép, danh sách hoặc từ vừa gõ.
- Ứng dụng chỉ hướng dẫn; bạn tự đổi các thiết lập trên.

## 2. Gõ và đối chiếu mẫu

1. Mở một **Google Doc trống để thử**, không dùng bài đang làm.
2. Trong ứng dụng chọn **Thiết lập & gõ mẫu thử**, rồi **Gõ mẫu thử**.
3. Trong 5 giây đếm ngược, bấm vào vùng soạn thảo của Google Docs.
4. Thả các phím; có thể di chuyển và cuộn chuột, nhưng không bấm chuột trong lúc gõ.
5. Khi gõ xong, sao chép toàn bộ mẫu từ Docs. Quay về ứng dụng, chọn
   **Đối chiếu mẫu đã gõ**, dán vào ô đối chiếu rồi kiểm tra.
6. Chỉ khi nội dung khớp, nút bắt đầu mới được mở. Mẫu có cả tiếng Việt,
   tiếng Anh và một lần xóa/sửa để kiểm tra UniKey thực tế.

Mỗi lần mở ứng dụng cần kiểm tra lại. Đổi trình duyệt, bàn phím hoặc cấu hình
UniKey cũng cần chạy lại mẫu. Đừng dán mẫu tham chiếu thay cho kết quả từ Docs:
làm vậy sẽ không kiểm tra được khả năng gõ trên máy của bạn.

## 3. Nhập nội dung và bắt đầu

- Dán nội dung vào ô lớn, hoặc dùng **Mở .txt / .docx**.
- Tệp `.txt` cần UTF-8 hoặc UTF-16 có BOM. Mã VNI/TCVN3 cần chuyển sang Unicode.
- **Nhập link Google Docs** chỉ đọc liên kết xem/tải được mà không cần đăng nhập.
  Với tài liệu riêng tư, tự tải `.docx`/`.txt` rồi mở tệp đó. Không cần công khai tài liệu.
- Kiểm tra phần xem trước: chỉ có chữ và xuống dòng, không giữ ảnh/định dạng.
- Nếu nguồn có công thức LaTeX dạng `$...$`, nhấn **Chuyển công thức** và
  kiểm tra kết quả trước khi gõ. Phân số được thể hiện bằng dấu ⁄ và ngoặc;
  đây là văn bản Unicode, không phải đối tượng công thức của Google Docs.
  Lệnh chưa hỗ trợ được giữ lại để bạn tự chỉnh. Nút này có thể hiểu hai dấu
  `$` trong văn bản thông thường là ranh giới công thức, nên hãy kiểm tra lại.
- Tốc độ mặc định 1× có nhịp 100–220 ms/phím, thêm khoảng nghỉ ở dấu câu.
- Có thể bật **Thỉnh thoảng gõ sai rồi sửa**; mặc định khi bật là 2% số từ đủ điều kiện.
- Nhấn **Bắt đầu**, rồi bấm vị trí trống trong Docs trong 5 giây. Không chọn sẵn
  văn bản và không đặt con trỏ giữa một từ đang có.

## Dừng

Nhấn **F8** ở bất kỳ cửa sổ nào trong lúc đếm ngược/gõ, hoặc bấm **Dừng**.
Bạn có thể di chuyển và cuộn chuột. Dùng bàn phím, bấm chuột hoặc đổi cửa sổ sẽ dừng gõ; ứng dụng đích cần giữ tiêu điểm.

Sau khi dừng, nhấn **Tiếp tục**, rồi trong lúc đếm ngược đặt con trỏ ngay sau
phần đã gõ, trong cùng tài liệu. Giữ nguyên phần đang gõ hoặc đang sửa dở để
ứng dụng tiếp tục chính xác. Nếu đã chỉnh sửa phần đó hoặc nội dung nguồn,
hãy kiểm tra và dùng **Bắt đầu từ đầu** nếu cần. Vị trí tiếp tục chỉ được lưu
trong khi ứng dụng còn mở; đóng ứng dụng sẽ mất vị trí này.

Trong khi đang nhập tệp/link hoặc kiểm tra nguồn, dùng nút **Dừng**; F8 chỉ
được bật khi bước đếm ngược bắt đầu. Tải link đã hủy có thể cần tối đa khoảng
20 giây để kết thúc yêu cầu mạng.

## Khi gặp vấn đề

- **Ký tự tô đỏ:** chọn **Unicode trực tiếp** để hỗ trợ dấu ngoặc cong, emoji
  và nhiều ký tự khác. Các ký tự điều khiển vẫn không được hỗ trợ. Nếu ứng dụng
  đích không nhận Unicode trực tiếp, thử Telex và thay ký tự được báo.
- **Báo kiểu dấu:** chọn chế độ hòa/hoà khớp UniKey và cách viết trong nguồn.
- **Gõ sai dấu hoặc tiếng Anh bị đổi:** kiểm tra cấu hình UniKey và tự động
  sửa của Docs, rồi chạy lại mẫu. Nếu cần, giảm tốc độ.
- **Báo chưa vào vùng nội dung:** bấm trang giấy trong Docs, không bấm thanh
  địa chỉ, ô tiêu đề, bình luận hay thanh công cụ.
- **Windows không nhận phím:** chạy ứng dụng và trình duyệt dưới cùng tài
  khoản/quyền thông thường; không chạy một bên với quyền quản trị.
- **Link không đọc được:** dùng tệp tải xuống. Chỉ hỗ trợ liên kết tài liệu
  `/document/d/…`, không hỗ trợ liên kết xuất bản `/document/d/e/…`.

Giới hạn mỗi lần: 100.000 ký tự và tệp 10 MB. `.doc`/`.docs` cần lưu lại thành
`.docx`. Tài liệu nhiều tab nên xuất phần cần dùng ra tệp và kiểm tra bản xem trước.

## Lịch sử và dữ liệu

Ứng dụng vẫn là công cụ gõ tự động. Google quản lý và có thể gộp các phiên bản;
không bảo đảm ghi từng phím, từng lần sửa hay đáp ứng yêu cầu của giáo viên.
Không có chức năng thay đổi thời gian hoặc giả mạo lịch sử.

Nội dung nằm trong bộ nhớ khi ứng dụng mở. Ứng dụng không ghi nhật ký nội dung,
không đọc tài khoản Google, không sửa clipboard và không tự lưu nguồn ra đĩa.
Chỉ thao tác nhập link mới kết nối mạng. UniKey đang chạy có thể tự dùng clipboard
theo cơ chế riêng của UniKey. Khi xong, kiểm tra nội dung và chờ Docs báo đã lưu.

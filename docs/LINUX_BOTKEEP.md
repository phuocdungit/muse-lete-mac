# Chạy Muse2Tele trên Linux và Botkeep

Bản này được nhập từ `vitbau246/Muse2Tele` main (commit ZIP `f7a72721827f87d2b0acf475a9eb74a52822822f`). Chạy FoxProfile ở chế độ API + web panel, trình duyệt ẩn, bot Telegram và AutoPost dưới **một** tiến trình quản lý. Lệnh Windows `.bat` vẫn dành cho Windows. Tự cập nhật từ dashboard chỉ dành cho Windows; trên Linux hãy cập nhật qua Git/Botkeep, không dùng `updater.py apply`.

## Linux thông thường

Cần Python 3.10 trở lên, pip, thư viện hệ thống của Firefox/Camoufox và quyền ghi trong thư mục dự án. Ví dụ Ubuntu 24.04 (tên gói khác ở distro khác):

```bash
sudo apt-get update
sudo apt-get install -y python3-venv libgtk-3-0t64 libx11-xcb1 libasound2t64 libdbus-glib-1-2
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m camoufox fetch
cp .env.example .env
# Sửa .env: TELEGRAM_BOT_TOKEN, FOXPROFILE_API_TOKEN nếu cần truy cập từ xa
python main.py
```

Trên Ubuntu 22.04 dùng `libgtk-3-0` và `libasound2` thay cho tên có `t64`. Lệnh fetch cần mạng tới máy chủ tải Camoufox và dung lượng đĩa. Mặc định panel tại `http://127.0.0.1:8090/`, chỉ truy cập trên máy chủ; để truy cập từ xa hãy dùng đường hầm SSH hoặc HTTPS reverse proxy có kiểm soát truy cập. Khi bind ngoài loopback, FoxProfile yêu cầu `FOXPROFILE_API_TOKEN` dài ít nhất 24 ký tự ngẫu nhiên. Panel cho phép điều khiển trình duyệt và dữ liệu đăng nhập, không công khai nó khi chưa bảo vệ. Truyền token qua HTTPS, không gửi qua chat hay đưa vào Git.

## Cấu hình Botkeep

1. Tạo workload **Python**, chọn repo và nhánh cần triển khai, project root là `/` của repo, `requirements.txt` ở root. Phiên bản Python nên là 3.10 trở lên. Start command: `python main.py`.
2. Trong Environment, đặt **secret** `TELEGRAM_BOT_TOKEN` (lấy từ BotFather). Nếu cần mở panel qua mạng, đặt thêm secret `FOXPROFILE_API_TOKEN` ngẫu nhiên ít nhất 24 ký tự và `FOXPROFILE_API_HOST=0.0.0.0`. Cấu hình cổng theo cổng được Botkeep cấp (`PORT` được dùng nếu chưa đặt `FOXPROFILE_API_PORT`). Nếu đặt `FOXPROFILE_URL`, phải trỏ về `http://127.0.0.1:<cổng>` bên trong workload. Không tạo file `.env` chứa secret trong repo/ZIP.
3. Cài Camoufox **một lần** trong môi trường của workload bằng `python -m camoufox fetch` trước khi mở profile; tải lại nếu cache bị xóa. Cần các thư viện native của Firefox và quyền ghi cache. Botkeep có thể không cho cài gói hệ thống hay truy cập public port: xác nhận với Botkeep trước. Nếu thiếu thư viện, quyền, mạng tải trình duyệt hoặc cổng web, không thể cam kết chạy đầy đủ trên profile đó; dùng VPS Linux hoặc runtime có hỗ trợ thay thế.
4. Nếu Botkeep cấp URL HTTPS/cổng cho web panel, mở URL đó và đăng nhập bằng API token. Tạo profile Linux, cấu hình proxy phù hợp nếu cần, mở profile, dùng **remote viewer** để đăng nhập Muse; sau đó làm các bước `/start`, tạo nhóm có Topics, `/setup` như README chính. Nếu nền tảng không hỗ trợ truy cập HTTP tới workload, panel từ xa không dùng được: cần một cách truy cập riêng được Botkeep hỗ trợ.
5. Kiểm tra Console: một trong ba tiến trình dừng thì launcher dừng toàn bộ và trả mã lỗi để nền tảng có thể khởi động lại. Chỉ chạy một bot cho mỗi token. Profile không tự mở lại sau restart: mở lại trên panel. Đừng giả định Botkeep luôn tự khởi động lại hay lưu file qua mọi lần deploy; kiểm tra panel và chính sách của họ.

Camoufox và các profile có thể vượt giới hạn gói miễn phí Botkeep (512 MB RAM, 1 GB đĩa); thực tế phụ thuộc số profile, trang, thư viện và dung lượng cache. Headless mặc định không cần Xvfb; nếu muốn `FOXPROFILE_HEADLESS=virtual` thì host phải có Xvfb. Đăng nhập/challenge và mạng tới Telegram, Muse, proxy, máy tải browser cần được kiểm tra thực tế. Chưa xác nhận môi trường Botkeep hỗ trợ tất cả phụ thuộc native.

## Dữ liệu và lưu ý

- Sao lưu độc lập `foxprofile/data/` (profile, cookies), `muse_telebot/muse_telebot_state.json`, `social_post/data/`, `Videos/downloads/` và cấu hình bí mật. Đây là dữ liệu nhạy cảm. Không commit chúng. Kiểm tra hành vi lưu trữ của Botkeep trước khi cập nhật, redeploy, xóa hoặc khôi phục workload.
- `FOXPROFILE_UPLOAD_DIRS` mặc định là `Videos/downloads` trong repo; file bot lưu mặc định tại `Videos/downloads/muse_telebot`. Nếu đổi đường dẫn, thư mục bot phải nằm trong một thư mục được phép upload; nhiều thư mục phân cách bằng `:` trên Linux. Biến môi trường nền tảng có ưu tiên hơn `.env`; nếu sửa qua panel, hãy cập nhật Environment và restart khi cần.
- Những thay đổi qua panel có thể ghi `.env`; nếu dùng secrets của Botkeep, vẫn quản lý secret trong Environment, không tải/commit `.env`.
- Botkeep có quy định fair use (bao gồm cấm proxy/VPN endpoints và spam); xác minh cách sử dụng của bạn phù hợp với điều khoản và giới hạn của họ.

Tham khảo: [hướng dẫn Python Botkeep](https://botkeep.cloud/docs/python), [GitHub](https://botkeep.cloud/docs/github), [FAQ](https://botkeep.cloud/faq).

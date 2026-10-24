# AdBlock ESP32

[🇻🇳 Tiếng Việt](README.md) | [🇬🇧 English](README_EN.md) | [🇯🇵 日本語](README_JP.md)

Thiết bị **chặn quảng cáo toàn mạng (DNS Sinkhole)** tương tự Pi-hole / AdGuard Home, chạy trên vi điều khiển **ESP32-C3 giá chỉ ~50.000đ – 70.000đ ($2)** — *hoàn toàn không cần chip PSRAM ngoài*.

Bí quyết cốt lõi: **Không lưu chuỗi tên miền trong RAM**. Thay vào đó, toàn bộ danh sách chặn được băm thành các mã **40-bit FNV-1a hash** đã sắp xếp và lưu trực tiếp trong bộ nhớ Flash. Với bảng chỉ mục RAM 4096 mục (~20 KB), thiết bị có thể chứa từ **140.000 đến hơn 250.000 tên miền** trong Flash mà chỉ tiêu thụ **~50–80 KB RAM**, tốc độ phản hồi truy vấn chỉ **~10 ms**!

```
Truy vấn DNS đến ──▶ Tách domain ──▶ Băm FNV-1a (+ các domain cha)
                 ──▶ Tìm nhị phân trên RAM index (4096 mục)
                 ──▶ Đọc 1 khối hash trong Flash
                      ├─ Trùng khớp ──▶ Trả về 0.0.0.0 (Chặn quảng cáo)
                      └─ Không trùng──▶ Chuyển tiếp tới DNS Upstream (Cho phép)
```

---

## 🌟 Điểm nổi bật & Tính năng mới

- 🛡️ **Bảo vệ toàn bộ mạng gia đình**: Tự động chặn quảng cáo, mã theo dõi, telemetry và tên miền độc hại cho tất cả thiết bị (điện thoại iPhone/Android, Smart TV, máy tính, máy tính bảng).
- 🌐 **Giao diện Web Dashboard song ngữ (VI / EN)**:
  - Hỗ trợ chuyển đổi nhanh giữa **Tiếng Việt** và **Tiếng Anh** chỉ với 1 click.
  - Thanh Menu cố định (Sticky Navigation) tối ưu cho cả máy tính và điện thoại.
  - Tự động đánh dấu mục đang xem theo thời gian thực (ScrollSpy) và cuộn trang mượt mà.
  - Giao diện nén chuẩn gzip ngay lúc build giúp tiết kiệm tối đa dung lượng Flash của ESP32.
- ⚡ **Nhật ký truy vấn DNS trực tiếp (Recent Queries)**: Xem ngay 16 tên miền gần nhất được xử lý (kèm IP thiết bị yêu cầu, kết quả Đã chặn / Đã cho phép và thời gian).
- 👥 **Quản lý thiết bị & Chặn truy cập**: Thống kê số lượng truy vấn theo từng địa chỉ IP trong mạng nội bộ, hỗ trợ Chặn (Ban) / Bỏ chặn thiết bị ngay trên web.
- 📶 **Quét sóng Wi-Fi (Wi-Fi Scanner)**: Dò tìm các mạng Wi-Fi xung quanh kèm biểu đồ cường độ sóng RSSI mà không làm gián đoạn kết nối Wi-Fi hiện tại.
- 🔄 **Cập nhật không dây (OTA)**: Nạp firmware mới hoặc tải danh sách `blocklist.bin` trực tiếp qua trình duyệt web; hỗ trợ tự động lên lịch tải danh sách chặn từ xa theo chu kỳ (mỗi X giờ).
- 🇻🇳 **Tối ưu hóa danh sách ngoại lệ Việt Nam (`whitelist.txt`)**: Tích hợp danh sách whitelist đặc thù bởi **Tám Công Nghệ**, đảm bảo không bị chặn nhầm:
  - Dịch vụ công, cổng thuế điện tử, bảo hiểm xã hội, VNeID.
  - Tất cả các ứng dụng ngân hàng lớn (VCB, Techcombank, MB, ACB, BIDV, VPBank, VIB, TPBank...).
  - Ví điện tử, cổng thanh toán (MoMo, ZaloPay, VNPay, Napas, ShopeePay...).
  - Báo điện tử, trang tin tức và sàn thương mại điện tử lớn tại Việt Nam.
- 🔒 **Bảo mật nhiều lớp**: Bắt buộc xác thực HTTP Basic Auth cho các tác vụ thay đổi hệ thống, chống tấn công CSRF qua header tùy chỉnh `X-Requested-With`, và mã hóa ký tự HTML chống Stored-XSS.

---

## 💡 So sánh cơ chế: String-in-RAM vs Hash-in-Flash

Hầu hết các giải pháp chặn quảng cáo trên ESP32 thông thường nạp trực tiếp danh sách chuỗi tên miền (string) vào RAM, do đó bắt buộc phải có chip PSRAM (giá thành cao và cồng kềnh).

| Tiêu chí | Cách truyền thống (String trong RAM) | Dự án này (Hash trong Flash + RAM Index) |
|---|---|---|
| **Phần cứng** | ESP32 + PSRAM (~180.000đ – 220.000đ) | **ESP32-C3 thường (~50.000đ – 70.000đ)** |
| **Dung lượng danh sách** | Chỉ ~20.000 – 40.000 domain nếu không có PSRAM | **140.000 – 250.000+ domain (Flash 4MB)** |
| **Bộ nhớ RAM tiêu thụ** | Gần như cạn kiệt RAM | **Chỉ ~50 – 80 KB RAM** |
| **Tốc độ tra cứu** | Duyệt chuỗi | **1–2 lần đọc Flash (~10 ms bao gồm cả độ trễ Wi-Fi)** |
| **Xác suất đụng độ hash** | 0 | 0 đụng độ ở mức 141k domain (~1 ở mức 537k) |

**Tại sao lại chọn độ dài 40-bit?** Đây là điểm cân bằng hoàn hảo. Theo bài toán nghịch lý ngày sinh nhật (Birthday paradox), ở mức 141.000 domain thì tỷ lệ đụng độ là 0; ở mức 537.000 domain chỉ có khoảng 1 domain có thể bị trùng mã băm. Nếu giảm xuống 32-bit sẽ tiết kiệm 20% flash nhưng tăng nguy cơ đụng độ; nếu nâng lên 64-bit thì lãng phí thêm 3 byte vô ích trên mỗi domain.

---

## 🛠️ Yêu cầu phần cứng

- **Bo mạch ESP32-C3**: Khuyên dùng **ESP32-C3 SuperMini** (kích thước siêu nhỏ bằng ngón tay, Flash 4MB, không cần PSRAM).
- Hỗ trợ cả **ESP32 Classic / DevKit** (WROOM 4MB): biên dịch với `pio run -e esp32dev -t upload`.
- **Nguồn cấp điện**: Cổng USB 5V ổn định (có thể cắm trực tiếp vào cổng USB trên Router Wi-Fi hoặc củ sạc điện thoại).
- **Vỏ hộp in 3D**: File thiết kế vừa khít cho bo mạch ESP32-C3 SuperMini có sẵn tại [`hardware/esp32-c3-supermini-enclosure.stl`](hardware/esp32-c3-supermini-enclosure.stl).

---

## 🚀 Hướng dẫn biên dịch & Nạp code (PlatformIO)

Bạn chỉ cần cắm cáp USB để nạp firmware và danh sách chặn lần đầu tiên. Sau đó, mọi nâng cấp firmware và cập nhật blocklist đều được thực hiện không dây qua Wi-Fi.

### Bước 1: Chuẩn bị cấu hình mật khẩu

Sao chép file mẫu `src/secrets.example.h` thành `src/secrets.h`:

```bash
cp src/secrets.example.h src/secrets.h
```

Mở file `src/secrets.h` và chỉnh sửa:
- `WIFI_SSID` / `WIFI_PASS`: Tên và mật khẩu Wi-Fi nhà bạn (nếu để trống, ESP32 sẽ phát Wi-Fi Captive Portal để bạn kết nối qua điện thoại).
- `WEB_USER` / `WEB_PASS`: Tên đăng nhập và mật khẩu trang quản trị Dashboard.
- `OTA_PASS`: Mật khẩu nạp code qua mạng không dây.

### Bước 2: Tạo tệp danh sách chặn (`blocklist.bin`)

Sử dụng script Python để tổng hợp các nguồn chặn quảng cáo quốc tế kết hợp cùng danh sách ngoại lệ Việt Nam (`whitelist.txt`):

```bash
python tools/build_blocklist.py data/blocklist.bin
```

Script này sẽ tự động tải các danh sách chặn uy tín (StevenBlack, Hagezi...), loại trừ các tên miền trong danh sách whitelist và đóng gói thành tệp nhị phân `data/blocklist.bin`.

### Bước 3: Nạp Firmware và Phân vùng dữ liệu lên ESP32

Cắm ESP32 vào cổng USB máy tính và chạy lệnh:

```bash
# Nạp chương trình firmware
pio run -t upload

# Nạp phân vùng LittleFS chứa file blocklist.bin
pio run -t uploadfs
```

### Bước 4: Cấu hình Wi-Fi lần đầu (Nếu chưa điền trong `secrets.h`)

Nếu bạn không cấu hình sẵn Wi-Fi trong `secrets.h`, ESP32 sẽ tự động phát một điểm truy cập Wi-Fi mở có tên:
**`C3-AdBlock-XXXX`** (với `XXXX` là đuôi địa chỉ MAC).

1. Dùng điện thoại hoặc máy tính kết nối vào Wi-Fi `C3-AdBlock-XXXX`.
2. Trang cài đặt sẽ tự động bật lên (Captive Portal).
3. Chọn mạng Wi-Fi nhà bạn, nhập mật khẩu và nhấn **Save**.
4. ESP32 sẽ khởi động lại và kết nối vào mạng Wi-Fi của bạn.

---

## 🖥️ Sử dụng & Quản trị qua Web Dashboard

Mở trình duyệt bất kỳ và truy cập vào địa chỉ:
👉 **`http://c3adblock.local`** (hoặc địa chỉ IP của ESP32 do router cấp).

Tại giao diện quản trị, bạn có thể:
1. **Trang đăng nhập chuyên nghiệp (Login Screen)**:
   - Giao diện đăng nhập hiện đại với tùy chọn ghi nhớ tài khoản và nút ẩn/hiện mật khẩu.
   - Hỗ trợ chế độ **Xem thống kê nhanh (Chỉ đọc)** nếu bạn muốn xem thông số DNS mà không cần nhập mật khẩu.
   - Nút **Đăng xuất (Logout)** tiện lợi trên thanh menu, tự động hết hạn phiên khi mật khẩu thay đổi.
2. **Chuyển đổi ngôn ngữ**: Nhấn nút **VI / EN** trên góc màn hình để chuyển đổi giao diện sang Tiếng Việt hoặc Tiếng Anh tức thì.
3. **Menu điều hướng**: Bấm vào các mục *Tổng quan*, *Truy vấn DNS*, *Thiết bị*, *Bộ lọc*, *Mạng Wi-Fi*, *Cập nhật* để cuộn nhanh đến từng khu vực.
4. **Bật / Tắt tạm thời**: Khi cần vào các trang web bị chặn nhầm, bạn có thể tạm dừng chặn trong 30 giây, 5 phút, 30 phút hoặc đến khi bật lại thủ công.
5. **Xem truy vấn DNS**: Bảng hiển thị 16 truy vấn DNS thời gian thực giúp kiểm tra thiết bị nào đang gửi yêu cầu và tên miền đó bị chặn hay cho phép.
6. **Chặn thiết bị nội bộ**: Bấm **Chặn thiết bị** để cấm một thiết bị cụ thể trong LAN không được phân giải DNS.
7. **Thêm bộ lọc thủ công**: Nhập tên miền (ví dụ: `ads.example.com`) để chặn bổ sung mà không cần build lại blocklist.
8. **Dò Wi-Fi**: Bấm **Quét Wi-Fi** để tìm kiếm các mạng lân cận kèm chỉ số sóng dBm.
9. **Cập nhật OTA**:
   - Tải tệp `blocklist.bin` mới qua web.
   - Hoặc dán đường link URL danh sách chặn vào mục *Tự động cập nhật* (Remote Auto-Update) để thiết bị tự động tải sau mỗi X giờ.
   - Nạp tệp firmware mới `.pio/build/c3/firmware.bin` trực tiếp mà không cần tháo lắp thiết bị.

---

## 🌐 Cấu hình Router để chặn quảng cáo cho cả nhà

Để mọi thiết bị kết nối vào Wi-Fi tự động được lọc quảng cáo mà không cần cài đặt gì trên từng máy:

1. Đăng nhập vào trang quản trị Router Wi-Fi của bạn (thường là `192.168.1.1`).
2. Tìm đến mục **Cài đặt mạng LAN / DHCP Server**.
3. Tại ô **DNS Server chính (Primary DNS)**: Điền địa chỉ IP của ESP32 (ví dụ: `192.168.1.25`).
4. Tại ô **DNS Server phụ (Secondary DNS)**: Bạn có thể điền DNS an toàn dự phòng (như `1.1.1.1` hoặc `8.8.8.8`) hoặc để trống.
5. Khuyên dùng: Trong bảng DHCP của Router, hãy **Gán IP tĩnh (Static DHCP Lease)** cho địa chỉ MAC của ESP32 để IP của nó không bao giờ bị thay đổi khi khởi động lại.
6. Lưu lại cấu hình và ngắt kết nối / kết nối lại Wi-Fi trên điện thoại để nhận DNS mới.

### Kiểm tra hoạt động qua dòng lệnh (Terminal):

```bash
# Kiểm tra tên miền quảng cáo (kết quả trả về 0.0.0.0 nghĩa là ĐÃ CHẶN)
dig @<ip-esp32> doubleclick.net

# Kiểm tra tên miền bình thường (kết quả trả về IP thực tế nghĩa là ĐÃ CHO PHÉP)
dig @<ip-esp32> google.com
```

---

## 🔒 Kiến trúc bảo mật

- **Phân quyền Basic Auth**: Tất cả các API làm thay đổi trạng thái hệ thống (`/ban`, `/addblock`, `/unblock`, `/upload`, `/update`, `/setupdate`, `/forgetwifi`) đều yêu cầu tài khoản và mật khẩu quản trị.
- **Chống tấn công CSRF**: Các yêu cầu gửi lên bắt buộc phải đính kèm Header `X-Requested-With: c3-adblock`. Các trang web lừa đảo bên ngoài mở thẻ `<form>` hoặc `<img>` trên trình duyệt sẽ không thể giả mạo để gọi lệnh tới ESP32.
- **Chống Stored XSS**: Các chuỗi nhập vào như tên miền tùy chỉnh hay tên Wi-Fi (SSID) quét được đều được mã hóa ký tự HTML an toàn trước khi hiển thị lên Dashboard.
- **Dual-OTA Partitions**: Phân vùng Flash được chia thành 2 slot ứng dụng độc lập (`app0` và `app1`), nếu quá trình nạp OTA bị gián đoạn thiết bị vẫn an toàn và không bị biến thành "cục gạch".

---

## 📁 Cấu trúc dự án

```
esp32-c3-adblock/
├── hardware/              # File mô hình 3D vỏ hộp (.stl)
├── src/
│   ├── main.cpp           # Mã nguồn C++ chính (DNS Sinkhole, Web Server, OTA, Cache)
│   ├── page.html          # Giao diện Web Dashboard (Responsive, Song ngữ VI/EN)
│   ├── secrets.example.h  # File mẫu cấu hình mật khẩu quản trị
│   └── secrets.h          # File chứa mật khẩu thực tế (không commit lên git)
├── tools/
│   ├── build_blocklist.py # Script Python tổng hợp danh sách chặn và sinh mã hash
│   └── embed_page.py      # Script nén trang page.html thành gzip trước khi build
├── check_bin.py           # Công cụ kiểm tra tính toàn vẹn của tệp blocklist.bin
├── whitelist.txt          # Danh sách ngoại lệ cho các dịch vụ tại Việt Nam
├── partitions.csv         # Bảng phân vùng Flash tối ưu cho Dual-OTA (4MB)
├── platformio.ini         # Cấu hình biên dịch PlatformIO
└── README.md              # Tài liệu hướng dẫn sử dụng
```

---

## Fork from
Được truyền cảm hứng từ dự án [s60sc/ESP32_AdBlocker](https://github.com/s60sc/ESP32_AdBlocker) và tối ưu hóa chuyên sâu cho vi điều khiển kiến trúc RISC-V không PSRAM.


## 📄 Bản quyền (License)

Dự án được phân phối dưới giấy phép **MIT License**. Xem chi tiết tại tệp [`LICENSE`](LICENSE).
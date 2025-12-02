# MyMiniCloud – Mô phỏng hệ thống Cloud cơ bản

> Repo: `tranhohoangvuminiclouddemo`  
> Môn: Cloud Computing – TDTU  
> Mô phỏng 1 hệ thống cloud thu nhỏ gồm nhiều server cơ bản, triển khai bằng Docker & Docker Compose.

---

## 1. Mục tiêu & Chức năng chính

Dự án này xây dựng một “mini cloud platform” gồm các thành phần:

- **Web Frontend Server** – Nginx static site (trang Home + Blog).
- **Application Backend Server** – Flask API (`/hello`, `/secure`, `/student`).
- **Relational Database Server** – MariaDB với DB `minicloud` & `studentdb`.
- **Authentication & Identity Server** – Keycloak (OIDC, realm riêng, client `flask-app`).
- **Object Storage Server** – MinIO (bucket `profile-pics`, `documents`).
- **Internal DNS Server** – CoreDNS (zone `cloud.local`).
- **Monitoring Node Exporter** – thu thập metric.
- **Monitoring Prometheus Server** – scrape metric từ Node Exporter & Web.
- **Monitoring Grafana Dashboard Server** – vẽ dashboard.
- **API Gateway / Reverse Proxy / Load Balancer** – Nginx: vào 1 cổng duy nhất, routing & cân bằng tải.

Toàn bộ chạy trên 1 mạng Docker duy nhất `cloud-net` thông qua `docker-compose.yml`.

---

## 2. Kiến trúc tổng quan

### 2.1. Network & Container

- Mạng Docker: `cloud-net` (bridge).
- Mỗi server là 1 container độc lập, có `container_name` rõ ràng:
  - `web-frontend-server`, `web-frontend-server-1`, `web-frontend-server-2`
  - `application-backend-server`
  - `relational-database-server`
  - `authentication-identity-server`
  - `object-storage-server`
  - `internal-dns-server`
  - `monitoring-node-exporter-server`
  - `monitoring-prometheus-server`
  - `monitoring-grafana-dashboard-server`
  - `api-gateway-proxy-server`

Tất cả container kết nối vào `cloud-net` để mô phỏng hạ tầng của 1 Cloud Platform (tương tự AWS/Azure/GCP).

### 2.2. Port mapping (host → container)

- Web Frontend: `8080:80`
- App Backend: `8085:8081`
- MariaDB: `3306:3306`
- Keycloak: `8081:8080`
- MinIO: `9000:9000` (S3 API), `9001:9001` (console)
- DNS (CoreDNS): `1053:53/udp`
- Node Exporter: `9100:9100`
- Prometheus: `9090:9090`
- Grafana: `3000:3000`
- API Gateway: `80:80`

---

## 3. Cấu trúc thư mục (dự kiến)

```text
tranhohoangvuminiclouddemo/
├─ docker-compose.yml
├─ web-frontend-server/
│  ├─ html/
│  │  ├─ index.html
│  │  └─ blog/
│  │     ├─ index.html
│  │     ├─ blog1.html, blog2.html, blog3.html
│  └─ Dockerfile
├─ web-frontend-server-1/
│  ├─ html/
│  │  └─ index.html
│  ├─ conf.default
│  └─ Dockerfile
├─ web-frontend-server-2/
│  ├─ html/
│  │  └─ index.html
│  ├─ conf.default
│  └─ Dockerfile
├─ application-backend-server/
│  ├─ app.py
│  ├─ students.json
│  └─ Dockerfile
├─ relational-database-server/
│  └─ init/
│     ├─ 001_init.sql         (DB minicloud + bảng notes)
│     └─ 002_init.sql         (DB studentdb + bảng students)
├─ authentication-identity-server/
├─ object-storage-server/
│  └─ data/                   (volume MinIO)
├─ internal-dns-server/
│  ├─ Corefile
│  └─ zones/
│     └─ db.cloud.local
├─ monitoring-prometheus-server/
│  └─ prometheus.yml
├─ monitoring-grafana-dashboard-server/
├─ api-gateway-proxy-server/
│  └─ nginx.conf
```

---

## 4. Cách chạy dự án

### 4.1. Yêu cầu

- Docker & Docker Compose cài trên máy.
- Port: `80`, `8080`, `8081`, `3306`, `9000`, `9001`, `9090`, `9100`, `3000`, `1053/udp` chưa bị chiếm.

### 4.2. Khởi động toàn bộ hệ thống

Từ thư mục gốc repo:

```bash
# Build toàn bộ image
docker compose build --no-cache

# Khởi động cả cụm mini-cloud
docker compose up -d

# Kiểm tra container
docker compose ps
```

Nếu muốn chạy từng service trong quá trình dev:

```bash
docker compose up -d web-frontend-server application-backend-server api-gateway-proxy-server
```

Dừng hệ thống:

```bash
docker compose down
```

---

## 5. Demo & Kiểm thử từng server

### 5.1. Web Frontend Server (Nginx static site)

**Mục đích:** kiểm tra web tĩnh + blog cá nhân.

- Truy cập Home:

```bash
curl -I http://localhost:8080/
# hoặc mở trình duyệt: http://localhost:8080/
```

**Kỳ vọng:**

- HTTP `200 OK`
- Trang hiển thị tiêu đề "MyMiniCloud – Home" và link sang Blog.

- Truy cập Blog:

```bash
curl -I http://localhost:8080/blog/
# hoặc http://localhost:8080/blog/
```

**Kỳ vọng:**

- Trang blog list, có link tới 3 bài `blog1.html`, `blog2.html`, `blog3.html`.

---

### 5.2. Application Backend Server (Flask API)

**Mục đích:** kiểm tra API backend hoạt động & proxy từ API Gateway.

- Gọi trực tiếp:

```bash
curl http://localhost:8085/hello
```

- Qua API Gateway:

```bash
curl http://localhost/api/hello
```

**Kỳ vọng:**

```json
{"message":"Hello from App Server!"}
```

**Route `/student` (EXT 2 + EXT 9):**

- Trực tiếp:

```bash
curl http://localhost:8085/student
```

- Qua Gateway:

```bash
curl http://localhost/student/
```

**Kỳ vọng:** trả về JSON danh sách sinh viên đọc từ `students.json`.

**Route `/secure` (OIDC với Keycloak):**

- Khi có token hợp lệ (lấy từ Keycloak) → `/secure` trả thông tin user.
- Khi thiếu/invalid token → HTTP `401` với thông báo lỗi.

---

### 5.3. Relational Database Server (MariaDB)

**Mục đích:** kiểm tra dữ liệu khởi tạo tự động trong container DB.

#### 5.3.1. Lệnh kiểm tra bắt buộc – DB `minicloud`

```bash
docker run -it --rm --network cloud-net mysql:8   sh -c 'mysql -h relational-database-server -uroot -proot -D minicloud -e "SHOW TABLES; SELECT * FROM notes;"'
```

**Kỳ vọng:**

- Có bảng `notes`
- Có bản ghi `"Hello from MariaDB!"`

#### 5.3.2. Lệnh kiểm tra mở rộng – DB `studentdb`

```bash
docker run -it --rm --network cloud-net mysql:8   sh -c 'mysql -h relational-database-server -uroot -proot -D studentdb -e "SHOW TABLES; SELECT * FROM students;"'
```

**Kỳ vọng:** có ít nhất 3 bản ghi sinh viên trong bảng `students`.

---

### 5.4. Authentication Identity Server (Keycloak)

**Mục đích:** kiểm tra dịch vụ đăng nhập OIDC hoạt động và tích hợp với Flask `/secure`.

#### 5.4.1. Truy cập trang tài khoản người dùng

Mở trình duyệt:

```text
http://localhost:8081/realms/52200214/account
```

Đăng nhập bằng user (ví dụ `sv01`) để kiểm tra realm hoạt động.

#### 5.4.2. Lấy Access Token bằng `curl.exe` (Windows)

Trong PowerShell/cmd, dùng lệnh:

```powershell
curl.exe -X POST "http://localhost:8081/realms/52200214/protocol/openid-connect/token" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "client_id=flask-app" `
  -d "grant_type=password" `
  -d "username=sv01" `
  -d "password=sv01"
```

Kết quả trả về JSON chứa trường `access_token`. Copy giá trị này và gán vào `<ACCESS_TOKEN_MOI>`.

#### 5.4.3. Gọi API `/secure` của Flask với Bearer Token

```powershell
curl.exe -i "http://localhost:8085/secure" -H "Authorization: Bearer <ACCESS_TOKEN_MOI>"
```

**Kỳ vọng:**

- Nếu token hợp lệ → trả JSON thông tin user (sub, preferred_username, …).
- Nếu token sai/hết hạn → HTTP `401`.

---

### 5.5. Object Storage Server (MinIO)

**Mục đích:** kiểm tra lưu trữ đối tượng kiểu S3.

- Mở console: <http://localhost:9001>
- Đăng nhập: `minioadmin / minioadmin`

**Buckets gợi ý:**

- Bucket `profile-pics` → upload avatar cá nhân.
- Bucket `documents` → upload file PDF báo cáo.

---

### 5.6. Internal DNS Server (CoreDNS)

**Mục đích:** phân giải tên miền nội bộ `*.cloud.local` bằng CoreDNS.  
Cấu hình:

- `internal-dns-server/Corefile` – load zone `cloud.local` từ thư mục `zones/`.
- `internal-dns-server/zones/db.cloud.local` – file zone chứa các bản ghi A nội bộ, ví dụ:
  - `web-frontend-server    IN A 10.10.10.10`
  - `app-backend            IN A 10.10.10.20`
  - `minio                  IN A 10.10.10.30`
  - `keycloak               IN A 10.10.10.40`

#### 5.6.1. Lệnh kiểm tra bắt buộc

Dùng container `busybox` để `nslookup` qua mạng `cloud-net`:

```bash
docker run --rm --network cloud-net busybox nslookup web-frontend-server.cloud.local internal-dns-server
```

**Kỳ vọng:** phân giải được `web-frontend-server.cloud.local` về đúng IP trong `db.cloud.local`.

#### 5.6.2. Lệnh kiểm tra mở rộng

```bash
docker run --rm --network cloud-net busybox nslookup app-backend.cloud.local internal-dns-server
docker run --rm --network cloud-net busybox nslookup minio.cloud.local internal-dns-server
docker run --rm --network cloud-net busybox nslookup keycloak.cloud.local internal-dns-server
```

**Kỳ vọng:** tất cả tên trên đều phân giải đúng IP nội bộ tương ứng.

---

### 5.7. Monitoring: Node Exporter + Prometheus

**Node Exporter:**

- Container: `monitoring-node-exporter-server`
- Expose metric tại `:9100/metrics`.

**Prometheus:**

- Truy cập: <http://localhost:9090>
- Status → Targets: phải thấy target:
  - `monitoring-node-exporter-server:9100` (job `node`)
  - `web-frontend-server:80` (job `web`)

**Ví dụ query:**

- `node_cpu_seconds_total`
- `node_memory_MemAvailable_bytes`

---

### 5.8. Monitoring Grafana Dashboard

**Mục đích:** trực quan hóa metric hệ thống.

- Mở: <http://localhost:3000>
- Đăng nhập: `admin / admin`
- Add datasource Prometheus:

```text
URL: http://monitoring-prometheus-server:9090
```

- Import dashboard Node Exporter hoặc tạo dashboard:

Tên gợi ý: **System Health of 52200214** với ít nhất 3 panel:

- CPU Usage
- Memory Usage
- Network Traffic

---

### 5.9. API Gateway Proxy Server (Nginx Reverse Proxy + Load Balancer)

**Mục đích:** routing hợp nhất & cân bằng tải web.

**Các route chính:**

- Web (load balancer 2 web server):

```bash
curl -I http://localhost/
```

**Kỳ vọng:** trả `200 OK`, nội dung luân phiên giữa `web-frontend-server-1` và `web-frontend-server-2` khi refresh nhiều lần.

- Backend:

```bash
curl http://localhost/api/hello
```

- Keycloak (qua gateway):

```bash
curl -I http://localhost/auth/
```

**Kỳ vọng:**

- `/` → trả HTML từ web (qua upstream `web_frontend`).
- `/api/hello` → JSON `"Hello from App Server!"`.
- `/auth/` → HTTP 302 redirect tới trang login Keycloak.

**Route `/student/` (EXT 9):**

```bash
curl http://localhost/student/
```

**Kỳ vọng:** trả danh sách sinh viên giống `/student` của Flask.

---

## 6. Kiểm tra thông mạng giữa các container

Có thể dùng ping từ 1 container bất kỳ (ví dụ từ `application-backend-server`):

```bash
docker run -it --rm --network cloud-net alpine sh

# Trong shell của container:
ping -c 3 web-frontend-server
ping -c 3 relational-database-server
ping -c 3 authentication-identity-server
ping -c 3 object-storage-server
ping -c 3 monitoring-prometheus-server
ping -c 3 monitoring-grafana-dashboard-server
ping -c 3 internal-dns-server
```

---

## 7. Push image tùy chỉnh lên Docker Hub

Theo yêu cầu kỹ thuật chung, dự án đã push ít nhất 1 image tùy chỉnh lên Docker Hub.

### 7.1. Tạo repository trên Docker Hub

Quy trình tạo repository cho backend:

1. Đăng nhập vào **Docker Hub**: <https://hub.docker.com/>
2. Ở góc phải, chọn **Create Repository**.
3. Điền thông tin:
   - **Repository name**: `tranhohoangvu-minicloud-backend`
   - **Visibility**: chọn **Public** (để giảng viên có thể truy cập).
4. Nhấn **Create** để tạo repository `tranhohoangvu/tranhohoangvu-minicloud-backend`.

### 7.2. Build & push image lên Docker Hub

Trên máy local, tại thư mục gốc của repo, đã chạy các lệnh:

```bash
docker login

docker build -t tranhohoangvu/tranhohoangvu-minicloud-backend:1.0 ./application-backend-server

docker push tranhohoangvu/tranhohoangvu-minicloud-backend:1.0
```

Trong đó:

- `./application-backend-server` là thư mục chứa `Dockerfile` của Flask backend.
- Image trên Docker Hub có tên:
  - **Repository**: `tranhohoangvu/tranhohoangvu-minicloud-backend`
  - **Tag**: `1.0`
- Xem trực tiếp trên Docker Hub tại:
  - <https://hub.docker.com/r/tranhohoangvu/tranhohoangvu-minicloud-backend>

Image này có thể được dùng lại trong các môi trường khác (ví dụ EC2) bằng cách:

```bash
docker pull tranhohoangvu/tranhohoangvu-minicloud-backend:1.0
```

*(Hiện tại `docker-compose.yml` vẫn sử dụng `build:` từ Dockerfile trong repo để dễ deploy, nhưng việc push image lên Docker Hub đã đáp ứng yêu cầu 4 của đề.)*

---

## 8. Ghi chú & Hướng mở rộng

- Repo đã triển khai đủ 9 loại server + các extension:
  - Blog cá nhân (3 bài).
  - API `/student` đọc JSON.
  - DB `studentdb.students`.
  - Realm Keycloak + client `flask-app` + endpoint `/secure`.
  - MinIO với avatar + tài liệu.
  - CoreDNS zone `cloud.local` với nhiều bản ghi.
  - Prometheus job `web`.
  - Dashboard Grafana “System Health of 52200214”.
  - Route `/student/` qua API Gateway.
  - Load balancer Round Robin 2 web server.

- Có thể mở rộng thêm:
  - Deploy lên EC2 hoặc VPS để demo qua public IP.
  - Thêm logging stack (Loki/ELK) nếu muốn.

---

## 9. Author

- Trần Hồ Hoàng Vũ

---
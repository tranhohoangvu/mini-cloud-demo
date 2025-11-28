
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
- **Internal DNS Server** – Bind9 (zone `cloud.local`).
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
- DNS: `1053:53/udp`
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
├─ application-backend-server/
│  ├─ app.py
│  ├─ students.json
│  └─ Dockerfile
├─ relational-database-server/
│  └─ init/
│     ├─ 001_init.sql         (DB minicloud + bảng notes)
│     └─ 002_init.sql    (DB studentdb + bảng students)
├─ authentication-identity-server/
├─ object-storage-server/
│  └─ data/                   (volume MinIO)
├─ internal-dns-server/
│  ├─ named.conf.options
│  ├─ named.conf.local
│  └─ db.cloud.local
├─ monitoring-prometheus-server/
│  └─ prometheus.yml
├─ monitoring-grafana-dashboard-server/
├─ api-gateway-proxy-server/
│  └─ nginx.conf
```

---

## 4. Cách chạy dự án

### 4.1. Yêu cầu

- Docker & Docker Compose đã cài trên máy.
- RAM tối thiểu ~4GB để chạy full stack.

### 4.2. Build & Start

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
docker compose up -d web-frontend-server
docker compose up -d application-backend-server
# ...
```

---

## 5. Demo & Kiểm thử từng server

### 5.1. Web Frontend Server (Nginx static site)

**Mục đích:** phục vụ web tĩnh (Home + Blog).

- Truy cập trình duyệt:
  - Home: <http://localhost:8080/>
  - Blog: <http://localhost:8080/blog/>
- Hoặc dùng `curl`:

```bash
curl -I http://localhost:8080/
curl -I http://localhost:8080/blog/
```

**Kỳ vọng:**

- HTTP 200 OK
- Home hiển thị: `MyMiniCloud – Home`
- Blog hiển thị: `MyMiniCloud – Blog`

**Extension Blog cá nhân (/blog):** thêm `blog1.html`, `blog2.html`, `blog3.html` với nội dung & ảnh minh họa, link về trang chủ.

---

### 5.2. Application Backend Server (Flask API)

**Mục đích:** microservice REST API.

- Trực tiếp (không qua gateway):

```bash
curl http://localhost:8085/hello
```

- Qua API Gateway:

```bash
curl http://localhost/api/hello
```

**Kỳ vọng:**

```json
{ "message": "Hello from App Server!" }
```

**Endpoint `/student`:**

- `GET /student`
- Đọc dữ liệu từ `students.json` (ít nhất 5 sinh viên: id, name, major, gpa).

Test:

```bash
curl http://localhost:8085/student
curl http://localhost/student/     # qua API Gateway
```

**Endpoint `/secure`:**

- `GET /secure` nhận Bearer token (OIDC – Keycloak).
- Token hợp lệ → trả `message: "Secure resource OK"` + `preferred_username`.
- Token thiếu/invalid → HTTP 401.

---

### 5.3. Relational Database Server (MariaDB)

**Mục đích:** mô phỏng RDS, auto-init schema/data.

**DB 1 – `minicloud` + bảng `notes`:**

```bash
docker run -it --rm --network cloud-net mysql:8   sh -c 'mysql -h relational-database-server -uroot -proot -D minicloud   -e "SHOW TABLES; SELECT * FROM notes;"'
```

**Kỳ vọng:**

- Có bảng `notes`
- Có bản ghi `"Hello from MariaDB!"`

**DB 2 – `studentdb` + bảng `students`:**

Trong script `002_init.sql`:

- Tạo DB `studentdb`
- Tạo bảng `students(id, student_id, fullname, dob, major, …)`
- Insert ≥ 3 bản ghi.

Test:

```bash
docker run -it --rm --network cloud-net mysql:8   sh -c 'mysql -h relational-database-server -uroot -proot   -e "SHOW DATABASES; USE studentdb; SHOW TABLES; SELECT * FROM students;"'
```

---

### 5.4. Authentication Identity Server (Keycloak)

**Mục đích:** IdP phát hành token, quản lý user/realm/client.

- Truy cập: <http://localhost:8081>
- Đăng nhập admin:

  - Username: `admin`
  - Password: `admin`

**Realm & client:**

- Tạo realm theo MSSV (vd: `minicloud-52200214`).
- Tạo user: `sv01`, `sv02`.
- Tạo client `flask-app` (public).
- Lấy token và gọi `/secure` ở backend.

---

### 5.5. Object Storage Server (MinIO)

**Mục đích:** mô phỏng S3 cho lưu trữ object.

- Truy cập console: <http://localhost:9001>
- Đăng nhập: `minioadmin / minioadmin`

**Buckets gợi ý:**

- Bucket `profile-pics` → upload avatar cá nhân.
- Bucket `documents` → upload file PDF báo cáo.

---

### 5.6. Internal DNS Server (Bind9)

**Mục đích:** phân giải tên miền nội bộ `*.cloud.local`.

- Truy vấn từ host:

```bash
dig @127.0.0.1 -p 1053 web-frontend-server.cloud.local +short
```

**Kỳ vọng:** trả về IP nội bộ tương ứng.

**Gợi ý thêm bản ghi:**

Thêm các bản ghi trong `db.cloud.local`:

- `app-backend.cloud.local`
- `minio.cloud.local`
- `keycloak.cloud.local`

Test:

```bash
dig @127.0.0.1 -p 1053 app-backend.cloud.local +short
dig @127.0.01 -p 1053 minio.cloud.local +short
dig @127.0.01 -p 1053 keycloak.cloud.local +short
```

---

### 5.7. Monitoring: Node Exporter + Prometheus

**Node Exporter:**

- Container `monitoring-node-exporter-server`
- Expose metric tại `:9100/metrics`.

**Prometheus:**

- Truy cập: <http://localhost:9090>
- Status → Targets: phải thấy target `monitoring-node-exporter-server:9100` trạng thái **UP**.

Thử query:

```text
node_cpu_seconds_total
```

**Thêm job web (gợi ý):**

Trong `prometheus.yml`:

```yaml
- job_name: 'web'
  static_configs:
    - targets: ['web-frontend-server:80']
```

Restart Prometheus, kiểm tra `/targets` thấy job `web` **UP**.

---

### 5.8. Monitoring: Grafana Dashboard

- Truy cập: <http://localhost:3000>
- Đăng nhập: `admin/admin`
- Thêm datasource **Prometheus**:
  - URL: `http://monitoring-prometheus-server:9090`

**Dashboard gợi ý “System Health of <MSSV>”:**

- Tạo dashboard mới với ít nhất 3 panel:
  - CPU Usage (sử dụng `node_cpu_seconds_total`)
  - Memory Usage (`node_memory_MemAvailable_bytes`, …)
  - Network Traffic (`node_network_receive_bytes_total`, …)

---

### 5.9. API Gateway / Reverse Proxy / Load Balancer

**Mục đích:** Gateway duy nhất cho web/app/auth; route `/student/` & load balancing.

Các route chính:

- `/` → `web-frontend-server:80`
- `/api/` → `application-backend-server:8081`
- `/auth/` → `authentication-identity-server:8080`

**Kiểm thử:**

```bash
curl -I http://localhost/          # web
curl -s  http://localhost/api/hello
curl -I http://localhost/auth/     # redirect 302 tới Keycloak
```

**Route `/student/`:**

```nginx
location /student/ {
    proxy_pass http://application-backend-server:8081/student;
}
```

Test:

```bash
curl http://localhost/student/
```

**Load Balancer (Round Robin):**

- Tạo thêm 2 web server: `web-frontend-server-1`, `web-frontend-server-2` (HTML khác nhau để dễ phân biệt).
- Trong `nginx.conf`:

```nginx
upstream web_frontend {
    server web-frontend-server-1:80;
    server web-frontend-server-2:80;
}

server {
    listen 80;
    location / {
        proxy_pass http://web_frontend;
    }
    # ...
}
```

- F5 nhiều lần `http://localhost/` → nội dung luân phiên giữa server 1 & 2.

---

### 5.10. Kiểm tra kết nối mạng giữa các container

Từ 1 container (vd: `api-gateway-proxy-server`):

```bash
ping -c 3 web-frontend-server
ping -c 3 application-backend-server
ping -c 3 relational-database-server
ping -c 3 authentication-identity-server
ping -c 3 object-storage-server
ping -c 3 monitoring-prometheus-server
ping -c 3 monitoring-grafana-dashboard-server
ping -c 3 internal-dns-server
```

---

## 6. Extensions / Gợi ý mở rộng

1. Blog cá nhân 3 bài – Web Frontend.
2. API `/student` đọc từ `students.json`.
3. DB `studentdb` + bảng `students`.
4. Realm riêng + user + client `flask-app` trong Keycloak, dùng cho `/secure`.
5. MinIO bucket `profile-pics` & `documents`.
6. Thêm bản ghi DNS nội bộ cho app, minio, keycloak.
7. Prometheus job giám sát web.
8. Grafana dashboard “System Health of <MSSV>”.
9. API Gateway route `/student/`.
10. Load Balancer (Round Robin) giữa 2 web server.

---

## 7. Phân công công việc (gợi ý)

> Hãy ghi rõ họ tên + MSSV từng thành viên trước khi nộp.

- **Infra & Monitoring (DevOps mini):**  
  MariaDB, DNS, Node Exporter, Prometheus, một phần MinIO.

- **Backend & API Gateway:**  
  Flask app (`/hello`, `/secure`, `/student`), kết nối DB (nếu có), Nginx API Gateway, load balancer, build & push image lên Docker Hub.

- **Frontend, Keycloak, MinIO & Báo cáo:**  
  Web tĩnh + blog, Keycloak realm/client/user, MinIO buckets, Grafana dashboard, tổng hợp screenshot & viết báo cáo.

---

## 8. Ghi chú khi deploy lên server (AWS EC2, VPS,…)

- Mở firewall cho các port cần demo (80, 8080, 8081, 3000, 9000, 9001, 9090, 1053/udp, …).
- Cài Docker & Docker Compose trên server.
- Clone repo, chạy `docker compose up -d`.
- Dùng **public IP** của server thay cho `localhost` khi truy cập từ ngoài.

---

> 💡 Tip: Khi nộp báo cáo, hãy bổ sung:
> - Link GitHub repo  
> - Link Docker Hub image custom  
> - Link video demo  
> - Screenshot từng phần demo tương ứng với README này.

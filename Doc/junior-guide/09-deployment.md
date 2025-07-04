# デプロイと運用

**このガイドで学べること**：
- Docker/Docker Composeを使った本番環境構築
- 環境変数とシークレット管理
- 監視とロギングの設定
- バックアップとリストア戦略

## 🐳 Docker環境の理解

### Docker Composeの構成

```yaml
# docker-compose.yml（本番用の最適化版）
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - static_files:/usr/share/nginx/html/static
    depends_on:
      - frontend
      - backend
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build:
      context: ./frontend
      dockerfile: ../infrastructure/docker/frontend/Dockerfile.prod
      args:
        - NEXT_PUBLIC_API_URL=${FRONTEND_API_URL}
    environment:
      - NODE_ENV=production
    restart: always
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  backend:
    build:
      context: ./backend
      dockerfile: ../infrastructure/docker/backend/Dockerfile.prod
    env_file:
      - ./backend/.env.production
    environment:
      - PYTHONUNBUFFERED=1
      - APP_ENV=production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
  static_files:

networks:
  default:
    driver: bridge
```

### 本番用Dockerfile

#### バックエンド

```dockerfile
# infrastructure/docker/backend/Dockerfile.prod
# マルチステージビルド
FROM python:3.11-slim as builder

WORKDIR /app

# ビルド依存関係のインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 本番イメージ
FROM python:3.11-slim

WORKDIR /app

# 実行時に必要なライブラリのみインストール
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージをコピー
COPY --from=builder /root/.local /root/.local

# アプリケーションコードをコピー
COPY . .

# 非rootユーザーで実行
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# PATH環境変数を更新
ENV PATH=/root/.local/bin:$PATH

# Gunicornで起動
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

#### フロントエンド

```dockerfile
# infrastructure/docker/frontend/Dockerfile.prod
# ビルドステージ
FROM node:18-alpine as builder

WORKDIR /app

# 依存関係のインストール
COPY package.json yarn.lock .yarnrc.yml ./
COPY .yarn .yarn
RUN yarn install --frozen-lockfile

# アプリケーションのビルド
COPY . .
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN yarn build

# 本番イメージ
FROM node:18-alpine

WORKDIR /app

# 本番用の依存関係のみインストール
COPY package.json yarn.lock .yarnrc.yml ./
COPY .yarn .yarn
RUN yarn workspaces focus --production && yarn cache clean

# ビルド成果物をコピー
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js ./

# 非rootユーザーで実行
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
USER nextjs

EXPOSE 3000

CMD ["yarn", "start"]
```

### Nginx設定

```nginx
# nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # ロギング設定
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # パフォーマンス設定
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;

    # Gzip圧縮
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;

    # レート制限
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;

    # アップストリーム定義
    upstream frontend {
        server frontend:3000;
        keepalive 32;
    }

    upstream backend {
        server backend:8000;
        keepalive 32;
    }

    # HTTPSリダイレクト
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # HTTPS設定
    server {
        listen 443 ssl http2;
        server_name team-insight.example.com;

        # SSL設定
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # セキュリティヘッダー
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # タイムアウト設定
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # 認証エンドポイントは別のレート制限
        location /api/v1/auth/ {
            limit_req zone=auth burst=5 nodelay;
            
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 静的ファイル
        location /_next/static/ {
            alias /usr/share/nginx/html/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # フロントエンド
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # ヘルスチェック
        location /health {
            access_log off;
            default_type text/plain;
            return 200 "healthy\n";
        }
    }
}

## 🔐 環境変数とシークレット管理

### 環境変数の階層

```
1. デフォルト値（コード内）
2. .env.production（バージョン管理外）
3. Docker Compose環境変数
4. コンテナ実行時の環境変数
5. シークレット管理ツール（AWS Secrets Manager等）
```

### 本番環境の環境変数

```bash
# backend/.env.production
# データベース
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
REDIS_MAX_CONNECTIONS=50

# セキュリティ
SECRET_KEY=${SECRET_KEY}  # 必ず強力なランダム文字列
ALLOWED_HOSTS=team-insight.example.com,api.team-insight.example.com
CORS_ORIGINS=https://team-insight.example.com

# Backlog OAuth
BACKLOG_CLIENT_ID=${BACKLOG_CLIENT_ID}
BACKLOG_CLIENT_SECRET=${BACKLOG_CLIENT_SECRET}
BACKLOG_REDIRECT_URI=https://team-insight.example.com/api/v1/auth/callback
BACKLOG_SPACE_KEY=${BACKLOG_SPACE_KEY}

# メール設定（本番用SMTP）
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=${SENDGRID_API_KEY}
SMTP_TLS=true
EMAIL_FROM=noreply@team-insight.example.com

# ロギング
LOG_LEVEL=INFO
SENTRY_DSN=${SENTRY_DSN}

# APScheduler
SCHEDULER_TIMEZONE=Asia/Tokyo
SCHEDULER_JOB_DEFAULTS_MISFIRE_GRACE_TIME=3600

# パフォーマンス
WORKERS=4
WORKER_TIMEOUT=120
KEEPALIVE=5
```

### シークレット管理のベストプラクティス

#### 1. 環境変数の暗号化

```bash
# .env.encryptedを作成
openssl enc -aes-256-cbc -salt -in .env.production -out .env.encrypted -k $ENCRYPTION_KEY

# 復号化
openssl enc -aes-256-cbc -d -in .env.encrypted -out .env.production -k $ENCRYPTION_KEY
```

#### 2. Docker Secretsの使用

```yaml
# docker-compose.secrets.yml
version: '3.8'

secrets:
  db_password:
    external: true
  redis_password:
    external: true
  secret_key:
    external: true
  backlog_client_secret:
    external: true

services:
  backend:
    secrets:
      - db_password
      - redis_password
      - secret_key
      - backlog_client_secret
    environment:
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - REDIS_PASSWORD_FILE=/run/secrets/redis_password
      - SECRET_KEY_FILE=/run/secrets/secret_key
```

#### 3. HashiCorp Vaultの統合

```python
# backend/app/core/vault.py
import hvac
from typing import Dict, Any
import os

class VaultClient:
    """HashiCorp Vaultクライアント"""
    
    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_ADDR', 'http://vault:8200'),
            token=os.getenv('VAULT_TOKEN')
        )
    
    def get_secrets(self, path: str) -> Dict[str, Any]:
        """シークレットを取得"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point='secret'
            )
            return response['data']['data']
        except Exception as e:
            logger.error(f"Failed to fetch secrets from Vault: {e}")
            raise
    
    def get_database_credentials(self) -> Dict[str, str]:
        """データベース認証情報を取得"""
        secrets = self.get_secrets('team-insight/database')
        return {
            'username': secrets['username'],
            'password': secrets['password'],
            'host': secrets['host'],
            'port': secrets['port'],
            'database': secrets['database']
        }

# 使用例
if os.getenv('USE_VAULT', 'false').lower() == 'true':
    vault_client = VaultClient()
    db_creds = vault_client.get_database_credentials()
    DATABASE_URL = f"postgresql://{db_creds['username']}:{db_creds['password']}@{db_creds['host']}:{db_creds['port']}/{db_creds['database']}"
else:
    DATABASE_URL = os.getenv('DATABASE_URL')
```

## 🚀 デプロイメントプロセス

### 1. ビルドとプッシュ

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

# バージョンタグ
VERSION=${1:-latest}
REGISTRY="your-registry.com"

echo "Building images with version: $VERSION"

# ビルド
docker-compose -f docker-compose.prod.yml build

# タグ付け
docker tag team-insight-backend:latest $REGISTRY/team-insight-backend:$VERSION
docker tag team-insight-frontend:latest $REGISTRY/team-insight-frontend:$VERSION

# レジストリにプッシュ
docker push $REGISTRY/team-insight-backend:$VERSION
docker push $REGISTRY/team-insight-frontend:$VERSION

echo "Images pushed successfully"
```

### 2. データベースマイグレーション

```bash
#!/bin/bash
# scripts/migrate.sh

echo "Running database migrations..."

# 本番環境でマイグレーション実行
docker-compose -f docker-compose.prod.yml run --rm backend \
    alembic upgrade head

echo "Migrations completed"
```

### 3. Blue-Greenデプロイメント

```yaml
# docker-compose.blue-green.yml
version: '3.8'

services:
  # Blue環境（現在稼働中）
  backend-blue:
    image: ${REGISTRY}/team-insight-backend:${CURRENT_VERSION}
    environment:
      - SERVICE_COLOR=blue
    networks:
      - backend-net
    deploy:
      replicas: 2

  # Green環境（新バージョン）
  backend-green:
    image: ${REGISTRY}/team-insight-backend:${NEW_VERSION}
    environment:
      - SERVICE_COLOR=green
    networks:
      - backend-net
    deploy:
      replicas: 2

  # ロードバランサー
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/blue-green.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    networks:
      - backend-net
```

### 4. ヘルスチェックとロールバック

```python
# scripts/health_check.py
import requests
import time
import sys

def check_health(url: str, retries: int = 30, delay: int = 10):
    """デプロイ後のヘルスチェック"""
    
    for i in range(retries):
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    print(f"✓ Health check passed: {data}")
                    return True
        except Exception as e:
            print(f"Health check attempt {i+1}/{retries} failed: {e}")
        
        time.sleep(delay)
    
    return False

def check_critical_endpoints(base_url: str):
    """重要なエンドポイントの確認"""
    
    endpoints = [
        "/api/v1/projects",
        "/api/v1/users/me",
        "/api/v1/sync/connection/status"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(
                f"{base_url}{endpoint}",
                headers={"Authorization": f"Bearer {test_token}"},
                timeout=10
            )
            if response.status_code not in [200, 401]:  # 401は認証が必要
                print(f"✗ Endpoint check failed: {endpoint} - {response.status_code}")
                return False
            print(f"✓ Endpoint check passed: {endpoint}")
        except Exception as e:
            print(f"✗ Endpoint check failed: {endpoint} - {e}")
            return False
    
    return True

if __name__ == "__main__":
    service_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost"
    
    # ヘルスチェック
    if not check_health(service_url):
        print("Health check failed! Rolling back...")
        sys.exit(1)
    
    # エンドポイントチェック
    if not check_critical_endpoints(service_url):
        print("Endpoint check failed! Rolling back...")
        sys.exit(1)
    
    print("All checks passed! Deployment successful.")
```

## 🔧 本番環境の最適化

### PostgreSQL設定

```sql
-- postgresql.conf の推奨設定
-- メモリ設定（8GBメモリサーバーの場合）
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
work_mem = 10MB

-- 接続設定
max_connections = 200
max_prepared_transactions = 0

-- チェックポイント設定
checkpoint_segments = 32
checkpoint_completion_target = 0.9

-- ログ設定
log_statement = 'mod'
log_duration = on
log_min_duration_statement = 1000  -- 1秒以上のクエリをログ

-- 自動バキューム
autovacuum = on
autovacuum_max_workers = 4
```

### Redis設定

```conf
# redis.conf
# メモリ設定
maxmemory 2gb
maxmemory-policy allkeys-lru

# 永続化
save 900 1
save 300 10
save 60 10000

# AOF
appendonly yes
appendfsync everysec

# セキュリティ
requirepass your-redis-password
```

## 📊 監視とロギング

### Prometheusによるメトリクス監視

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
```

### アプリケーションメトリクス

```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# メトリクス定義
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

sync_operations = Counter(
    'sync_operations_total',
    'Total sync operations',
    ['type', 'status']
)
```

### ログ集約（ELK Stack）

```yaml
# docker-compose.logging.yml
services:
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  logstash:
    image: logstash:8.11.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    depends_on:
      - elasticsearch

  kibana:
    image: kibana:8.11.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
```

## 💾 バックアップとリストア

### 自動バックアップスクリプト

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# PostgreSQLバックアップ
docker-compose exec -T postgres pg_dump -U teaminsight teaminsight | \
    gzip > "$BACKUP_DIR/postgres_${TIMESTAMP}.sql.gz"

# Redisバックアップ
docker-compose exec -T redis redis-cli --rdb /data/dump.rdb
docker cp $(docker-compose ps -q redis):/data/dump.rdb \
    "$BACKUP_DIR/redis_${TIMESTAMP}.rdb"

# アップロードファイルのバックアップ
tar -czf "$BACKUP_DIR/uploads_${TIMESTAMP}.tar.gz" /app/uploads

# S3へアップロード（オプション）
aws s3 cp "$BACKUP_DIR/" s3://team-insight-backups/ --recursive \
    --exclude "*" --include "*_${TIMESTAMP}*"

# 古いバックアップの削除（30日以上）
find "$BACKUP_DIR" -type f -mtime +30 -delete
```

### リストア手順

```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_DATE=$1

# PostgreSQLリストア
gunzip -c "/backups/postgres_${BACKUP_DATE}.sql.gz" | \
    docker-compose exec -T postgres psql -U teaminsight

# Redisリストア
docker cp "/backups/redis_${BACKUP_DATE}.rdb" \
    $(docker-compose ps -q redis):/data/dump.rdb
docker-compose restart redis
```

---

次は[トラブルシューティング](10-troubleshooting.md)で、問題解決の方法を学びましょう！
```
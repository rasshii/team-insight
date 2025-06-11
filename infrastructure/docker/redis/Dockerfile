FROM redis:7-alpine

# 設定ファイルをコピー
COPY redis.conf /usr/local/etc/redis/redis.conf

# ポートの公開
EXPOSE 6379

# 設定ファイルを使用してRedisを起動
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]

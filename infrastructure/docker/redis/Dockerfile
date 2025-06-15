FROM redis:7-alpine

# ログディレクトリを作成
RUN mkdir -p /var/log/redis && \
    chown redis:redis /var/log/redis

# 設定ファイルをコピー
COPY redis.conf /usr/local/etc/redis/redis.conf

# Redisユーザーで実行
USER redis

# ポートの公開
EXPOSE 6379

# 設定ファイルを使用して起動
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]

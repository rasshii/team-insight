FROM postgres:15-alpine

# 設定ファイルをコピー
COPY conf/postgresql.conf /etc/postgresql/postgresql.conf

# 初期化スクリプトをコピー
COPY init.sql /docker-entrypoint-initdb.d/

# 環境変数の設定
ENV POSTGRES_USER=team_insight_user \
    POSTGRES_PASSWORD=team_insight_password \
    POSTGRES_DB=team_insight_db \
    PGDATA=/var/lib/postgresql/data

# 設定ファイルを使用するように設定
ENV POSTGRES_INITDB_ARGS="--auth-host=scram-sha-256"

# ポートの公開
EXPOSE 5432

# PostgreSQLを起動
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]

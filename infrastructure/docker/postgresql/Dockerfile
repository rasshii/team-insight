FROM postgres:15

# 設定ファイルをコピー
COPY conf/postgresql.conf /etc/postgresql/postgresql.conf

# 初期化SQLファイルをコピー
COPY init.sql /docker-entrypoint-initdb.d/

# 環境変数の設定
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=team_insight

# ポートの公開
EXPOSE 5432

# 設定ファイルを使用してPostgreSQLを起動
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]

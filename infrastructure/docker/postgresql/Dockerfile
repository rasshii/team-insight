FROM postgres:15

# 初期化SQLファイルをコピー
COPY init.sql /docker-entrypoint-initdb.d/

EXPOSE 5432

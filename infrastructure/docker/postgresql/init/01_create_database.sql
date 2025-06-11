-- infrastructure/docker/mysql/init/01_create_database.sql
-- MySQL初期化スクリプト - Mine-CMS開発環境用
--
-- このスクリプトは、MySQLコンテナが初めて起動した時に実行されます。
-- 必要なデータベース、ユーザー、基本的なテーブル構造を作成します。

-- ===========================================
-- データベースの作成
-- ===========================================
-- 既存のデータベースがあれば削除（開発環境のみ）
DROP DATABASE IF EXISTS mine_cms;
DROP DATABASE IF EXISTS mine_cms_test;

-- メインデータベースの作成
CREATE DATABASE mine_cms
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

-- テスト用データベースの作成
CREATE DATABASE mine_cms_test
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

-- データベースを使用
USE mine_cms;

-- ===========================================
-- ユーザーの作成と権限設定
-- ===========================================
-- アプリケーション用ユーザー（既に.envで設定済みの場合はスキップ）
-- CREATE USER IF NOT EXISTS 'mine_cms_user'@'%' IDENTIFIED BY 'mine_cms_password';

-- 権限の付与
GRANT ALL PRIVILEGES ON mine_cms.* TO 'mine_cms_user'@'%';
GRANT ALL PRIVILEGES ON mine_cms_test.* TO 'mine_cms_user'@'%';

-- 権限の反映
FLUSH PRIVILEGES;

-- ===========================================
-- 基本テーブルの作成
-- ===========================================
-- 注意：以下のテーブルは、Laravelのマイグレーションで管理されるため、
-- 本来はここで作成する必要はありません。
-- しかし、初期セットアップの理解のために、基本的な構造を示します。

-- ロール（役割）テーブル
CREATE TABLE IF NOT EXISTS roles (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL COMMENT '役割名（システム用）',
    display_name VARCHAR(100) NOT NULL COMMENT '表示名',
    description TEXT NULL COMMENT '説明',
    is_system BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'システム役割フラグ',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_roles_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 初期ロールデータの挿入
INSERT INTO roles (name, display_name, description, is_system) VALUES
('admin', '管理者', 'システム全体の管理権限', TRUE),
('editor', '編集者', 'コンテンツの作成・編集権限', TRUE),
('reviewer', 'レビュアー', 'コンテンツのレビュー権限', TRUE),
('viewer', '閲覧者', 'コンテンツの閲覧のみ', TRUE)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 権限テーブル
CREATE TABLE IF NOT EXISTS permissions (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '権限名',
    display_name VARCHAR(200) NOT NULL COMMENT '表示名',
    category VARCHAR(50) NOT NULL COMMENT 'カテゴリ',
    description TEXT NULL COMMENT '説明',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_permissions_name (name),
    INDEX idx_permissions_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 初期権限データの挿入
INSERT INTO permissions (name, display_name, category, description) VALUES
-- 記事管理
('posts.view', '記事閲覧', 'posts', '記事を閲覧する権限'),
('posts.create', '記事作成', 'posts', '新規記事を作成する権限'),
('posts.edit', '記事編集', 'posts', '既存記事を編集する権限'),
('posts.delete', '記事削除', 'posts', '記事を削除する権限'),
('posts.publish', '記事公開', 'posts', '記事を公開する権限'),
('posts.review', '記事レビュー', 'posts', '記事をレビューする権限'),
-- メディア管理
('media.view', 'メディア閲覧', 'media', 'メディアファイルを閲覧する権限'),
('media.upload', 'メディアアップロード', 'media', 'メディアファイルをアップロードする権限'),
('media.delete', 'メディア削除', 'media', 'メディアファイルを削除する権限'),
-- ユーザー管理
('users.view', 'ユーザー閲覧', 'users', 'ユーザー情報を閲覧する権限'),
('users.create', 'ユーザー作成', 'users', '新規ユーザーを作成する権限'),
('users.edit', 'ユーザー編集', 'users', 'ユーザー情報を編集する権限'),
('users.delete', 'ユーザー削除', 'users', 'ユーザーを削除する権限'),
-- システム管理
('system.settings', 'システム設定', 'system', 'システム設定を変更する権限'),
('system.logs', 'ログ閲覧', 'system', 'システムログを閲覧する権限'),
('system.backup', 'バックアップ管理', 'system', 'バックアップを管理する権限')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- カテゴリテーブル
CREATE TABLE IF NOT EXISTS categories (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT 'カテゴリ名',
    slug VARCHAR(100) NOT NULL COMMENT 'URLスラッグ',
    description TEXT NULL COMMENT '説明',
    parent_id INT UNSIGNED NULL COMMENT '親カテゴリID',
    sort_order INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '表示順',
    icon VARCHAR(50) NULL COMMENT 'アイコン',
    color VARCHAR(7) NULL COMMENT 'カラーコード',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_categories_slug (slug),
    INDEX idx_categories_parent_id (parent_id),
    INDEX idx_categories_sort_order (sort_order),
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 初期カテゴリデータの挿入
INSERT INTO categories (name, slug, description, sort_order) VALUES
('技術ブログ', 'tech-blog', '技術的な記事やチュートリアル', 1),
('お知らせ', 'news', '新機能やアップデートのお知らせ', 2),
('ドキュメント', 'docs', 'システムの使い方やAPI仕様書', 3),
('チュートリアル', 'tutorials', 'ステップバイステップのガイド', 4)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 設定テーブル
CREATE TABLE IF NOT EXISTS settings (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `key` VARCHAR(100) NOT NULL COMMENT '設定キー',
    value LONGTEXT NULL COMMENT '設定値',
    type ENUM('string', 'number', 'boolean', 'json', 'array') NOT NULL DEFAULT 'string' COMMENT 'データ型',
    category VARCHAR(50) NOT NULL DEFAULT 'general' COMMENT 'カテゴリ',
    description TEXT NULL COMMENT '説明',
    is_public BOOLEAN NOT NULL DEFAULT FALSE COMMENT '公開設定フラグ',
    is_encrypted BOOLEAN NOT NULL DEFAULT FALSE COMMENT '暗号化フラグ',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_settings_key (`key`),
    INDEX idx_settings_category (category),
    INDEX idx_settings_is_public (is_public)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 初期設定データの挿入
INSERT INTO settings (`key`, value, type, category, description, is_public) VALUES
('site_name', 'Mine-CMS', 'string', 'general', 'サイト名', TRUE),
('site_description', '高度なコンテンツ管理システム', 'string', 'general', 'サイト説明', TRUE),
('site_url', 'http://localhost', 'string', 'general', 'サイトURL', TRUE),
('admin_email', 'admin@example.com', 'string', 'general', '管理者メールアドレス', FALSE),
('posts_per_page', '20', 'number', 'display', '1ページあたりの記事数', TRUE),
('allow_comments', 'true', 'boolean', 'features', 'コメント機能の有効化', TRUE),
('require_email_verification', 'true', 'boolean', 'security', 'メール確認の必須化', FALSE),
('session_lifetime', '120', 'number', 'security', 'セッション有効期限（分）', FALSE),
('max_upload_size', '104857600', 'number', 'media', '最大アップロードサイズ（バイト）', FALSE)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- ===========================================
-- インデックスの最適化
-- ===========================================
-- 追加のインデックスやパフォーマンス最適化の設定
-- （本番環境では、実際の使用パターンに基づいて調整が必要）

-- ===========================================
-- ストアドプロシージャ（オプション）
-- ===========================================
-- 複雑なクエリやバッチ処理用のストアドプロシージャ

DELIMITER //

-- 記事の閲覧数を増やすプロシージャ
CREATE PROCEDURE increment_post_views(IN post_id BIGINT)
BEGIN
    UPDATE posts 
    SET view_count = view_count + 1 
    WHERE id = post_id;
END//

-- カテゴリの階層パスを取得するファンクション
CREATE FUNCTION get_category_path(cat_id INT)
RETURNS VARCHAR(500)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE path VARCHAR(500);
    DECLARE current_id INT;
    DECLARE current_name VARCHAR(100);
    
    SET path = '';
    SET current_id = cat_id;
    
    WHILE current_id IS NOT NULL DO
        SELECT name, parent_id INTO current_name, current_id
        FROM categories
        WHERE id = current_id;
        
        IF path = '' THEN
            SET path = current_name;
        ELSE
            SET path = CONCAT(current_name, ' > ', path);
        END IF;
    END WHILE;
    
    RETURN path;
END//

DELIMITER ;

-- ===========================================
-- 開発用のサンプルデータ（オプション）
-- ===========================================
-- 開発時のテスト用データ
-- 本番環境では実行しないでください

-- サンプルユーザーの作成（パスワードは'password'のハッシュ値）
-- 実際の開発では、Laravelのシーダーを使用することを推奨します

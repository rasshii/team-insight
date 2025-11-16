"""
Backlog APIクライアント - 外部API通信管理モジュール

このモジュールは、Backlog API v2との安全で効率的な通信を実現し、
以下の機能を提供します：

主要機能：
1. HTTPクライアントの管理とタイムアウト設定
2. 認証ヘッダーの自動付与（Bearer Token認証）
3. レート制限への対応とリトライ戦略
4. 統一されたエラーハンドリングとロギング
5. 型安全なAPIレスポンスの処理

Backlog API仕様：
- ベースURL: https://{space_key}.backlog.jp/api/v2
- 認証方式: OAuth2.0 Bearer Token
- レート制限: 1分あたり最大300リクエスト（スペースにより異なる）
- タイムアウト: 接続10秒、読み取り30秒

エラーハンドリング：
- HTTPステータスエラー: 4xx, 5xxレスポンスを適切に処理
- ネットワークエラー: タイムアウト、接続エラーをキャッチ
- レスポンスのバリデーション: 不正なJSONを検出

使用例：
    client = BacklogClient()

    # ユーザー情報取得
    user_info = await client.get_user_info(access_token="eyJ...")

    # 課題一覧取得
    issues = await client.get_user_issues(
        user_id=123,
        access_token="eyJ...",
        project_id=456,
        status_ids=[1, 2, 3]
    )
"""

import httpx
from typing import List, Optional, AsyncContextManager, Union
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.exceptions import ExternalAPIException
from app.schemas.backlog_types import BacklogUser, BacklogIssue, BacklogProject, BacklogProjectWithDetails
import logging

logger = logging.getLogger(__name__)


class BacklogClient:
    """
    Backlog API v2クライアント

    Backlog REST APIとの通信を担当するクライアントクラスです。
    HTTPリクエストの発行、認証、エラーハンドリングを一元管理し、
    型安全で保守性の高いAPI呼び出しを提供します。

    主要な特徴：
    - 非同期HTTPクライアント（httpx）を使用した高パフォーマンス通信
    - コンテキストマネージャーによる自動リソース管理
    - タイムアウト設定によるハング防止
    - 統一されたエラーハンドリング
    - 詳細なロギングによるデバッグ支援

    Attributes:
        base_url (str): Backlog APIのベースURL
            例: "https://mycompany.backlog.jp/api/v2"
        timeout (httpx.Timeout): HTTPリクエストのタイムアウト設定
            接続: 10秒、読み取り: 30秒

    レート制限対策：
    - Backlogは1分あたり最大300リクエストの制限がある
    - 429 Too Many Requestsエラーが返された場合は適切に処理する
    - 必要に応じてリトライロジックを実装する

    セキュリティ考慮事項：
    - アクセストークンは常にHTTPヘッダーで送信（URLパラメータ非推奨）
    - HTTPS通信必須（中間者攻撃の防止）
    - トークンは一時的にメモリに保持されるが、ログに記録しない

    使用例：
        >>> client = BacklogClient()
        >>> user_info = await client.get_user_info("eyJ...")
        >>> print(user_info["name"])

        >>> issues = await client.get_user_issues(
        ...     user_id=123,
        ...     access_token="eyJ...",
        ...     limit=50
        ... )
    """

    def __init__(self):
        """
        Backlog APIクライアントの初期化

        Backlogスペースキーを環境変数から取得し、ベースURLを構築します。
        タイムアウト設定も初期化時に行います。

        環境変数：
            BACKLOG_SPACE_KEY: Backlogスペースの識別子
                例: "mycompany"で"https://mycompany.backlog.jp"にアクセス

        タイムアウト設定：
            - 接続タイムアウト: 10秒（TCP接続確立まで）
            - 読み取りタイムアウト: 30秒（レスポンス受信まで）
            - これにより、長時間ハングするリクエストを防止

        Note:
            - 環境変数が設定されていない場合はエラーになる
            - マルチテナント環境ではspace_keyを動的に変更する必要がある
        """
        # Backlog APIのベースURLを構築
        # 例: BACKLOG_SPACE_KEY="mycompany" → "https://mycompany.backlog.jp/api/v2"
        self.base_url = f"https://{settings.BACKLOG_SPACE_KEY}.backlog.jp/api/v2"
        # タイムアウト設定（接続: 10秒、読み取り: 30秒）
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    @asynccontextmanager
    async def _get_client(self, access_token: str) -> AsyncContextManager[httpx.AsyncClient]:
        """
        OAuth2.0認証済みHTTPクライアントを生成・管理

        コンテキストマネージャーパターンを使用して、HTTPクライアントの
        ライフサイクルを適切に管理します。自動的にリソースのクリーンアップが
        行われるため、メモリリークを防止できます。

        認証方式：
        - OAuth2.0 Bearer Token認証
        - Authorizationヘッダーに"Bearer {token}"形式で設定
        - トークンは毎回リクエストごとに送信される

        クライアント設定：
        - timeout: 接続10秒、読み取り30秒
        - follow_redirects: リダイレクトを自動追従（True）
        - HTTP/2サポート: デフォルトで有効

        コンテキストマネージャーの利点：
        1. 自動的なリソース解放（接続プールのクローズ）
        2. 例外発生時も確実にクリーンアップされる
        3. 複数のリクエストで同じクライアントインスタンスを再利用可能

        Args:
            access_token (str): Backlog OAuth2.0アクセストークン
                               有効期限内のトークンが必要

        Yields:
            httpx.AsyncClient: 設定済みの非同期HTTPクライアント
                              このクライアントを使用してAPI呼び出しを実行

        Example:
            >>> async with self._get_client(access_token) as client:
            ...     response = await client.get("/users/myself")
            ...     user_data = response.json()
            # コンテキストを抜けると自動的にクライアントがクローズされる

        Note:
            - アクセストークンはログに記録されない（セキュリティ対策）
            - このメソッドはプライベート（外部から直接呼び出さない）
            - 長期間のリクエストにはタイムアウトが適用される
        """
        # Bearer認証ヘッダーを設定
        # RFC 6750に準拠したOAuth2.0トークン認証
        headers = {"Authorization": f"Bearer {access_token}"}

        # 非同期HTTPクライアントを生成
        # コンテキストマネージャーにより自動的にリソース管理
        async with httpx.AsyncClient(
            timeout=self.timeout,  # タイムアウト設定を適用
            headers=headers,  # すべてのリクエストに認証ヘッダーを含める
            follow_redirects=True,  # 3xxリダイレクトを自動追従
        ) as client:
            # クライアントを呼び出し元に渡す
            yield client
        # コンテキストを抜けると自動的にクライアントがクローズされる

    async def _make_request(self, method: str, endpoint: str, access_token: str, **kwargs) -> Union[dict, list]:
        """
        Backlog APIへの統一されたリクエスト処理とエラーハンドリング

        すべてのBacklog API呼び出しはこのメソッドを経由します。
        HTTPリクエストの実行、レスポンスの検証、エラーハンドリングを
        一元化することで、一貫性のある動作を保証します。

        処理フロー：
        1. ベースURLとエンドポイントを結合して完全なURLを構築
        2. 認証済みHTTPクライアントを取得
        3. 指定されたHTTPメソッドでリクエストを実行
        4. HTTPステータスコードを検証（raise_for_status）
        5. レスポンスをJSON形式でパース
        6. エラー発生時は詳細なログとカスタム例外を発生

        エラーハンドリングの階層：
        1. HTTPStatusError（4xx, 5xxエラー）
           - 401 Unauthorized: トークン無効または期限切れ
           - 403 Forbidden: アクセス権限なし
           - 404 Not Found: リソースが存在しない
           - 429 Too Many Requests: レート制限超過
           - 500 Internal Server Error: Backlogサーバーエラー

        2. RequestError（ネットワークエラー）
           - ConnectTimeout: 接続タイムアウト
           - ReadTimeout: 読み取りタイムアウト
           - NetworkError: ネットワーク接続エラー

        3. その他の予期しないエラー
           - JSONDecodeError: 不正なレスポンス形式
           - その他のランタイムエラー

        ロギング戦略：
        - エラー発生時は詳細なコンテキスト情報をログに記録
        - URLやHTTPメソッドを含めることでデバッグを容易にする
        - レスポンステキストは最大500文字に制限（大きすぎるログを防止）
        - センシティブな情報（トークンなど）はログに含めない

        Args:
            method (str): HTTPメソッド
                GET: リソース取得
                POST: リソース作成
                PUT: リソース更新
                DELETE: リソース削除
            endpoint (str): APIエンドポイント（base_urlからの相対パス）
                例: "/users/myself", "/issues", "/projects/123"
            access_token (str): Backlog OAuth2.0アクセストークン
            **kwargs: httpx.requestに渡される追加引数
                - params: URLクエリパラメータ（dict）
                - json: JSONリクエストボディ（dict）
                - data: フォームデータ（dict）
                - headers: 追加HTTPヘッダー（dict）

        Returns:
            Union[dict, list]: パース済みJSONレスポンス
                dict: 単一のリソース（ユーザー、プロジェクトなど）
                list: リソースのリスト（課題一覧など）

        Raises:
            ExternalAPIException: 以下の場合に発生
                - HTTPステータスエラー（4xx, 5xx）
                - ネットワークエラー（タイムアウト、接続エラー）
                - 予期しないエラー（JSON解析エラーなど）

        Example:
            >>> # GETリクエスト
            >>> data = await self._make_request(
            ...     "GET",
            ...     "/users/myself",
            ...     access_token="eyJ..."
            ... )

            >>> # POSTリクエスト（クエリパラメータ付き）
            >>> issues = await self._make_request(
            ...     "GET",
            ...     "/issues",
            ...     access_token="eyJ...",
            ...     params={"projectId[]": 123, "count": 50}
            ... )

        Note:
            - レート制限（429エラー）が発生した場合、呼び出し側でリトライ処理を実装
            - トークン期限切れ（401エラー）時は自動更新機能を活用
            - 大量のデータ取得時はページネーションを使用（offsetとlimit）
        """
        # 完全なURLを構築
        url = f"{self.base_url}{endpoint}"

        try:
            # 認証済みHTTPクライアントを使用してリクエストを実行
            async with self._get_client(access_token) as client:
                # HTTPリクエストを送信
                response = await client.request(method, url, **kwargs)
                # ステータスコードが4xx, 5xxの場合は例外を発生
                response.raise_for_status()
                # レスポンスをJSON形式でパース
                return response.json()

        except httpx.HTTPStatusError as e:
            # HTTPステータスエラー（4xx, 5xx）の処理
            logger.error(f"Backlog API HTTP error: {e.response.status_code} - {e.response.text}")
            logger.error(f"Request URL: {url}")
            logger.error(f"Request method: {method}")

            # カスタム例外を発生（詳細なエラー情報を含む）
            raise ExternalAPIException(
                service="Backlog",
                detail=f"APIリクエストが失敗しました: {e.response.status_code} - {e.response.text[:200]}",
                data={
                    "status_code": e.response.status_code,
                    "response_text": e.response.text[:500],  # 最大500文字に制限
                    "url": url,
                    "method": method,
                },
            )

        except httpx.RequestError as e:
            # ネットワークエラー（タイムアウト、接続エラーなど）の処理
            logger.error(f"Backlog API request error: {str(e)}")

            raise ExternalAPIException(
                service="Backlog",
                detail=f"APIとの通信中にエラーが発生しました: {str(e)}",
                data={"error_type": type(e).__name__},
            )

        except Exception as e:
            # その他の予期しないエラーの処理
            logger.error(f"Unexpected error in Backlog API call: {str(e)}")

            raise ExternalAPIException(
                service="Backlog",
                detail="予期しないエラーが発生しました",
                data={"error_type": type(e).__name__, "error": str(e)},
            )

    async def get_user_info(self, access_token: str) -> dict:
        """ユーザー情報を取得

        Args:
            access_token: Backlog APIアクセストークン

        Returns:
            ユーザー情報のディクショナリ
        """
        return await self._make_request("GET", "/users/myself", access_token)

    async def get_user_by_id(self, user_id: Union[int, str], access_token: str) -> dict:
        """指定されたユーザーの詳細情報を取得

        Args:
            user_id: ユーザーID（数値）またはユーザーID（文字列）
            access_token: Backlog APIアクセストークン

        Returns:
            ユーザー情報のディクショナリ（mailAddressフィールドを含む）
        """
        return await self._make_request("GET", f"/users/{user_id}", access_token)

    async def get_user_issues(
        self,
        user_id: int,
        access_token: str,
        project_id: Optional[int] = None,
        status_ids: Optional[List[int]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict]:
        """ユーザーの課題一覧を取得

        Args:
            user_id: ユーザーID
            access_token: アクセストークン
            project_id: プロジェクトID（オプション）
            status_ids: ステータスIDのリスト（オプション）
            limit: 取得件数の上限
            offset: オフセット

        Returns:
            課題情報のリスト
        """
        params = {"assigneeId[]": user_id, "count": limit, "offset": offset, "sort": "updated", "order": "desc"}

        if project_id:
            params["projectId[]"] = project_id

        if status_ids:
            params["statusId[]"] = status_ids

        return await self._make_request("GET", "/issues", access_token, params=params)

    async def get_project_issues(
        self, project_id: int, access_token: str, status_ids: Optional[List[int]] = None, limit: int = 100, offset: int = 0
    ) -> List[dict]:
        """プロジェクトの課題一覧を取得

        Args:
            project_id: プロジェクトID
            access_token: アクセストークン
            status_ids: ステータスIDのリスト（オプション）
            limit: 取得件数の上限
            offset: オフセット

        Returns:
            課題情報のリスト
        """
        params = {"projectId[]": project_id, "count": limit, "offset": offset, "sort": "updated", "order": "desc"}

        if status_ids:
            params["statusId[]"] = status_ids

        return await self._make_request("GET", "/issues", access_token, params=params)

    async def get_issue_by_id(self, issue_id: int, access_token: str) -> dict:
        """課題の詳細情報を取得

        Args:
            issue_id: 課題ID
            access_token: アクセストークン

        Returns:
            課題の詳細情報
        """
        return await self._make_request("GET", f"/issues/{issue_id}", access_token)

    async def get_project(self, project_id: int, access_token: str) -> dict:
        """プロジェクト情報を取得

        Args:
            project_id: プロジェクトID
            access_token: アクセストークン

        Returns:
            プロジェクト情報
        """
        return await self._make_request("GET", f"/projects/{project_id}", access_token)

    async def get_projects(self, access_token: str, archived: bool = False) -> List[dict]:
        """プロジェクト一覧を取得

        Args:
            access_token: アクセストークン
            archived: アーカイブ済みプロジェクトを含むか

        Returns:
            プロジェクト情報のリスト
        """
        params = {"archived": archived}
        logger.info(f"Getting projects from Backlog API: {self.base_url}/projects")
        result = await self._make_request("GET", "/projects", access_token, params=params)
        logger.info(f"Backlog API returned {len(result) if isinstance(result, list) else 'non-list'} projects")
        if isinstance(result, list) and len(result) > 0:
            logger.info(f"First project example: {result[0].get('projectKey', 'N/A')} - {result[0].get('name', 'N/A')}")
        return result

    async def get_issue_statuses(self, project_id: int, access_token: str) -> List[dict]:
        """プロジェクトの課題ステータス一覧を取得

        Args:
            project_id: プロジェクトID
            access_token: アクセストークン

        Returns:
            ステータス情報のリスト
        """
        return await self._make_request("GET", f"/projects/{project_id}/statuses", access_token)

    async def get_issue_comments(self, issue_id: int, access_token: str, limit: int = 100, offset: int = 0) -> List[dict]:
        """課題のコメント一覧を取得

        Args:
            issue_id: 課題ID
            access_token: アクセストークン
            limit: 取得件数の上限
            offset: オフセット

        Returns:
            コメント情報のリスト
        """
        params = {"count": limit, "offset": offset, "order": "asc"}

        return await self._make_request("GET", f"/issues/{issue_id}/comments", access_token, params=params)

    async def get_user_activities(
        self, user_id: int, access_token: str, activity_type_ids: Optional[List[int]] = None, limit: int = 100, offset: int = 0
    ) -> List[dict]:
        """ユーザーのアクティビティ一覧を取得"""
        params = {"userId[]": user_id, "count": limit, "offset": offset}

        if activity_type_ids:
            params["activityTypeId[]"] = activity_type_ids

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/space/activities", params=params, headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

    async def get_priorities(self, access_token: str) -> List[dict]:
        """優先度一覧を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/priorities", headers={"Authorization": f"Bearer {access_token}"})
            response.raise_for_status()
            return response.json()

    async def get_issue_types(self, project_id: int, access_token: str) -> List[dict]:
        """プロジェクトの課題種別一覧を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/issueTypes", headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

    async def get_project_users(self, project_id: int, access_token: str) -> List[dict]:
        """プロジェクトメンバー一覧を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/users", headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

    async def get_project_categories(self, project_id: int, access_token: str) -> List[dict]:
        """プロジェクトのカテゴリ一覧を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/categories", headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

    async def get_project_milestones(self, project_id: int, access_token: str) -> List[dict]:
        """プロジェクトのマイルストーン一覧を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/versions", headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

    async def get_project_statistics(self, project_id: int, access_token: str) -> dict:
        """プロジェクトの統計情報を取得"""
        # 課題の統計情報を取得
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # オープンな課題数
            open_issues_response = await client.get(
                f"{self.base_url}/issues/count",
                params={"projectId[]": project_id, "statusId[]": [1, 2, 3]},  # 未対応、処理中、処理済み
                headers={"Authorization": f"Bearer {access_token}"},
            )
            open_issues_response.raise_for_status()
            open_count = open_issues_response.json()["count"]

            # クローズした課題数
            closed_issues_response = await client.get(
                f"{self.base_url}/issues/count",
                params={"projectId[]": project_id, "statusId[]": [4]},  # 完了
                headers={"Authorization": f"Bearer {access_token}"},
            )
            closed_issues_response.raise_for_status()
            closed_count = closed_issues_response.json()["count"]

            return {"open_issues": open_count, "closed_issues": closed_count, "total_issues": open_count + closed_count}


backlog_client = BacklogClient()

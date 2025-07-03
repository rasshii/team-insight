"""
Backlog API レスポンスの型定義

Backlog API v2のレスポンス構造を表す型定義を提供します。
"""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel


class BacklogUser(BaseModel):
    """Backlogユーザー情報"""
    id: int
    userId: str
    name: str
    roleType: int
    lang: Optional[str] = None
    mailAddress: Optional[str] = None
    nulabAccount: Optional[dict] = None
    keyword: Optional[str] = None


class BacklogStatus(BaseModel):
    """課題ステータス"""
    id: int
    projectId: int
    name: str
    color: str
    displayOrder: int


class BacklogPriority(BaseModel):
    """課題優先度"""
    id: int
    name: str


class BacklogIssueType(BaseModel):
    """課題種別"""
    id: int
    projectId: int
    name: str
    color: str
    displayOrder: int


class BacklogCategory(BaseModel):
    """カテゴリー"""
    id: int
    name: str
    displayOrder: Optional[int] = None


class BacklogMilestone(BaseModel):
    """マイルストーン"""
    id: int
    projectId: int
    name: str
    description: Optional[str] = None
    startDate: Optional[str] = None
    releaseDueDate: Optional[str] = None
    archived: bool
    displayOrder: int


class BacklogCustomField(BaseModel):
    """カスタムフィールド"""
    id: int
    fieldTypeId: int
    name: str
    value: Any


class BacklogAttachment(BaseModel):
    """添付ファイル"""
    id: int
    name: str
    size: int
    createdUser: BacklogUser
    created: str


class BacklogStar(BaseModel):
    """スター"""
    id: int
    comment: Optional[str] = None
    url: str
    title: str
    presenter: BacklogUser
    created: str


class BacklogChangeLog(BaseModel):
    """変更ログ"""
    field: str
    newValue: Optional[str] = None
    originalValue: Optional[str] = None
    attachmentInfo: Optional[dict] = None
    attributeInfo: Optional[dict] = None
    notificationInfo: Optional[dict] = None


class BacklogComment(BaseModel):
    """コメント"""
    id: int
    content: Optional[str] = None
    changeLog: Optional[List[BacklogChangeLog]] = None
    createdUser: BacklogUser
    created: str
    updated: str
    stars: List[BacklogStar]
    notifications: List[dict]


class BacklogIssue(BaseModel):
    """Backlog課題"""
    id: int
    projectId: int
    issueKey: str
    keyId: int
    issueType: BacklogIssueType
    summary: str
    description: Optional[str] = None
    resolution: Optional[dict] = None
    priority: BacklogPriority
    status: BacklogStatus
    assignee: Optional[BacklogUser] = None
    category: List[BacklogCategory]
    versions: List[dict]
    milestone: List[BacklogMilestone]
    startDate: Optional[str] = None
    dueDate: Optional[str] = None
    estimatedHours: Optional[float] = None
    actualHours: Optional[float] = None
    parentIssueId: Optional[int] = None
    createdUser: BacklogUser
    created: str
    updatedUser: BacklogUser
    updated: str
    customFields: List[BacklogCustomField]
    attachments: List[BacklogAttachment]
    sharedFiles: List[dict]
    stars: List[BacklogStar]


class BacklogProject(BaseModel):
    """Backlogプロジェクト"""
    id: int
    projectKey: str
    name: str
    chartEnabled: bool
    useResolvedForChart: bool
    subtaskingEnabled: bool
    projectLeaderCanEditProjectLeader: bool
    useWiki: bool
    useFileSharing: bool
    useWikiTreeView: bool
    useOriginalImageSizeAtWiki: bool
    textFormattingRule: str
    archived: bool
    displayOrder: int
    useDevAttributes: bool


class BacklogProjectWithDetails(BacklogProject):
    """詳細情報付きBacklogプロジェクト"""
    issueTypes: List[BacklogIssueType]
    categories: List[BacklogCategory]
    versions: List[dict]
    milestones: List[BacklogMilestone]
    customFields: List[dict]


class BacklogActivity(BaseModel):
    """アクティビティ"""
    id: int
    project: BacklogProject
    type: int
    content: dict
    notifications: List[dict]
    createdUser: BacklogUser
    created: str


class BacklogWiki(BaseModel):
    """Wiki"""
    id: int
    projectId: int
    name: str
    content: Optional[str] = None
    tags: List[dict]
    attachments: List[BacklogAttachment]
    sharedFiles: List[dict]
    stars: List[BacklogStar]
    createdUser: BacklogUser
    created: str
    updatedUser: BacklogUser
    updated: str


class BacklogWebhook(BaseModel):
    """Webhook"""
    id: int
    name: str
    description: Optional[str] = None
    hookUrl: str
    allEvent: bool
    activityTypeIds: List[int]
    createdUser: BacklogUser
    created: str
    updatedUser: BacklogUser
    updated: str


# OAuth関連の型定義
class BacklogTokenResponse(BaseModel):
    """Backlog OAuthトークンレスポンス"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: Optional[str] = None


# API呼び出し時のパラメータ型定義
class IssueQueryParams(BaseModel):
    """課題検索パラメータ"""
    projectId: Optional[List[int]] = None
    issueTypeId: Optional[List[int]] = None
    categoryId: Optional[List[int]] = None
    versionId: Optional[List[int]] = None
    milestoneId: Optional[List[int]] = None
    statusId: Optional[List[int]] = None
    priorityId: Optional[List[int]] = None
    assigneeId: Optional[List[int]] = None
    createdUserId: Optional[List[int]] = None
    resolutionId: Optional[List[int]] = None
    parentChild: Optional[int] = None
    attachment: Optional[bool] = None
    sharedFile: Optional[bool] = None
    sort: Optional[str] = None
    order: Optional[str] = None
    offset: Optional[int] = None
    count: Optional[int] = None
    createdSince: Optional[str] = None
    createdUntil: Optional[str] = None
    updatedSince: Optional[str] = None
    updatedUntil: Optional[str] = None
    startDateSince: Optional[str] = None
    startDateUntil: Optional[str] = None
    dueDateSince: Optional[str] = None
    dueDateUntil: Optional[str] = None
    id: Optional[List[int]] = None
    parentIssueId: Optional[List[int]] = None
    keyword: Optional[str] = None
    customField: Optional[dict] = None
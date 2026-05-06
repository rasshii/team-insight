"""
TenantScopedService 基底クラス (Phase 0)

組織分離が必要なサービスの基底クラス。CRUD メソッドが
`WHERE organization_id = active_org_id` を自動付与する。

System Admin はバイパス (organization_id 指定で他組織にもアクセス可)。

使用例:
    class ProjectService(TenantScopedService[Project, ...]):
        def __init__(self):
            super().__init__(Project)

    project_service = ProjectService()
    projects = project_service.list_for_tenant(db, tenant)
"""

from typing import Any, Dict, Generic, List, Optional, Type

from sqlalchemy.orm import Query, Session

from app.core.exceptions import NotFoundException
from app.core.tenant import TenantContext
from app.db.base_class import Base
from app.services.base_service import (
    BaseService,
    CreateSchemaT,
    ModelT,
    SchemaT,
    UpdateSchemaT,
)


class TenantScopedService(BaseService[ModelT, SchemaT, CreateSchemaT, UpdateSchemaT]):
    """
    マルチテナント分離を組み込んだ CRUD 基底クラス

    継承先のモデルは organization_id カラムを持つ前提。
    """

    def get_base_query(self, db: Session) -> Query:
        """テナント条件は明示的に呼び出すため、ここではスコープしない"""
        return db.query(self.model)

    def _scope_to_tenant(self, query: Query, tenant: TenantContext) -> Query:
        """
        組織スコープを query に適用する

        System Admin で active_org_id が None の場合は全組織を見られる。
        非 System Admin は active_org_id 必須 (None は 400)。
        """
        if tenant.is_system_admin:
            if tenant.active_org_id is not None:
                return query.filter(self.model.organization_id == tenant.active_org_id)
            return query

        org_id = tenant.require_org_id()
        return query.filter(self.model.organization_id == org_id)

    def list_for_tenant(
        self,
        db: Session,
        tenant: TenantContext,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[ModelT]:
        """テナントスコープで一覧取得"""
        query = self._scope_to_tenant(self.get_base_query(db), tenant)

        if filters:
            query = self._apply_filters(query, filters)
        if order_by:
            query = self._apply_order_by(query, order_by)

        return query.offset(skip).limit(limit).all()

    def get_for_tenant(
        self, db: Session, tenant: TenantContext, id: int
    ) -> Optional[ModelT]:
        """テナントスコープで取得 (見つからなければ None)"""
        query = self._scope_to_tenant(self.get_base_query(db), tenant)
        return query.filter(self.model.id == id).first()

    def get_for_tenant_or_404(
        self, db: Session, tenant: TenantContext, id: int
    ) -> ModelT:
        """テナントスコープで取得 (見つからなければ NotFoundException)"""
        obj = self.get_for_tenant(db, tenant, id)
        if not obj:
            raise NotFoundException(resource=self.model.__name__, identifier=id)
        return obj

    def create_for_tenant(
        self, db: Session, tenant: TenantContext, *, obj_in: CreateSchemaT
    ) -> ModelT:
        """テナントスコープで作成 (organization_id を自動注入)"""
        org_id = tenant.require_org_id()
        data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.dict()
        data["organization_id"] = org_id

        db_obj = self.model(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

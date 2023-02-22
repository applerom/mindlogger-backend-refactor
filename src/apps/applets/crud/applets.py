import uuid
from typing import Any

from sqlalchemy import distinct, or_, select, update
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query

from apps.applets import errors
from apps.applets.db.schemas import AppletSchema, UserAppletAccessSchema
from apps.applets.domain import Role
from apps.shared.filtering import FilterField, Filtering
from apps.shared.ordering import Ordering
from apps.shared.query_params import QueryParams
from apps.shared.searching import Searching
from infrastructure.database.crud import BaseCRUD

__all__ = ["AppletsCRUD"]


class _AppletFiltering(Filtering):
    owner_id = FilterField(
        AppletSchema.id, cast=int, method_name="filter_by_owner"
    )

    def filter_by_owner(self, field, value: int):
        query: Query = select(UserAppletAccessSchema.applet_id)
        query = query.where(UserAppletAccessSchema.user_id == value)
        query = query.where(UserAppletAccessSchema.role == Role.ADMIN)
        return field.in_(query)


class _AppletSearching(Searching):
    search_fields = [AppletSchema.display_name]


class _AppletOrdering(Ordering):
    id = AppletSchema.id
    display_name = AppletSchema.display_name
    created_at = AppletSchema.created_at
    updated_at = AppletSchema.updated_at


class AppletsCRUD(BaseCRUD[AppletSchema]):
    schema_class = AppletSchema

    async def save(self, schema: AppletSchema) -> AppletSchema:
        """Return applets instance and the created information."""

        try:
            instance: AppletSchema = await self._create(schema)
        except IntegrityError:
            raise errors.AppletAlreadyExist()
        return instance

    async def update_by_id(
        self, pk: int, schema: AppletSchema
    ) -> AppletSchema:
        instance = await self._update_one(
            lookup="id",
            value=pk,
            schema=schema,
        )
        return instance

    async def get_by_link(
        self, link: uuid.UUID, require_login: bool
    ) -> AppletSchema | None:
        query: Query = select(AppletSchema)
        query = query.where(AppletSchema.link == link)
        query = query.where(AppletSchema.require_login == require_login)

        db_result = await self._execute(query)
        return db_result.scalars().first()

    async def _fetch(self, key: str, value: Any) -> AppletSchema:
        """Fetch applets by id or display_name from the database."""

        if key not in {"id", "display_name"}:
            raise errors.AppletsError(
                f"Can not make the looking up applets by {key} {value}"
            )

        # Get applets from the database
        if not (instance := await self._get(key, value)):
            raise errors.AppletNotFoundError(key=key, value=value)

        return instance

    async def get_by_id(self, id_: int) -> AppletSchema:
        instance = await self._fetch(key="id", value=id_)
        return instance

    async def exist_by_id(self, id_: int) -> bool:
        query: Query = select(AppletSchema)
        query = query.where(AppletSchema.id == id_)

        db_result = await self._execute(query)

        return db_result.scalars().first() is not None

    async def get_applets_by_roles(
        self, user_id: int, roles: list[str], query_params: QueryParams
    ) -> list[AppletSchema]:
        accessible_applets_query = select(UserAppletAccessSchema.applet_id)
        accessible_applets_query = accessible_applets_query.where(
            UserAppletAccessSchema.user_id == user_id
        )
        accessible_applets_query = accessible_applets_query.where(
            UserAppletAccessSchema.role.in_(roles)
        )

        query = select(AppletSchema)
        if query_params.filters:
            query = query.where(
                *_AppletFiltering().get_clauses(**query_params.filters)
            )
        if query_params.search:
            query = query.where(
                _AppletSearching().get_clauses(query_params.search)
            )
        if query_params.ordering:
            query = query.order_by(
                *_AppletOrdering().get_clauses(*query_params.ordering)
            )
        query = query.where(AppletSchema.id.in_(accessible_applets_query))
        query = query.limit(query_params.limit)
        query = query.offset(query_params.page - 1)
        result: Result = await self._execute(query)
        return result.scalars().all()

    async def get_applet_by_roles(
        self, user_id: int, applet_id: int, roles: list[str]
    ) -> AppletSchema | None:
        query = select(AppletSchema)
        query = query.join_from(UserAppletAccessSchema, AppletSchema)
        query = query.where(AppletSchema.id == applet_id)
        query = query.where(UserAppletAccessSchema.user_id == user_id)
        query = query.where(UserAppletAccessSchema.role.in_(roles))
        query = query.limit(1)
        result: Result = await self._execute(query)
        return result.scalars().first()

    async def delete_by_id(self, id_: int):
        """Delete applets by id."""

        query = update(AppletSchema)
        query = query.where(AppletSchema.id == id_)
        query = query.values(is_deleted=True)
        await self._execute(query)

    async def check_folder(self, folder_id: int) -> bool:
        """
        Checks whether folder has applets
        """
        query: Query = select(AppletSchema.id)
        query = query.where(AppletSchema.folder_id == folder_id)
        query = query.limit(1)
        query = query.exists()
        db_result = await self._execute(select(query))
        return db_result.scalars().first()

    async def set_applets_folder(
        self, applet_id: int, folder_id: int | None
    ) -> AppletSchema:
        query = update(AppletSchema)
        query = query.values(folder_id=folder_id)
        query = query.where(AppletSchema.id == applet_id)
        query = query.returning(self.schema_class)
        db_result = await self._execute(query)

        return db_result.scalars().one_or_none()

    async def get_folder_applets(
        self, owner_id: int, folder_id: int
    ) -> list[AppletSchema]:
        access_query: Query = select(
            distinct(UserAppletAccessSchema.applet_id)
        )
        access_query = access_query.where(
            UserAppletAccessSchema.user_id == owner_id
        )
        access_query = access_query.where(
            UserAppletAccessSchema.role.in_([Role.ADMIN])
        )

        query: Query = select(AppletSchema)
        query = query.where(AppletSchema.folder_id == folder_id)
        query = query.where(AppletSchema.id.in_(access_query))

        db_result = await self._execute(query)
        return db_result.scalars().all()

    async def get_name_duplicates(
        self, user_id: int, name: str, exclude_applet_id: int | None = None
    ) -> list[str]:
        query: Query = select(distinct(AppletSchema.display_name))
        query = query.join(
            UserAppletAccessSchema,
            UserAppletAccessSchema.applet_id == AppletSchema.id,
        )
        query = query.where(UserAppletAccessSchema.user_id == user_id)
        if exclude_applet_id:
            query = query.where(AppletSchema.id != exclude_applet_id)
        query = query.where(
            or_(
                AppletSchema.display_name.op("~")(f"{name} \\(\\d+\\)"),
                AppletSchema.display_name == name,
            )
        )
        db_result = await self._execute(query)
        return db_result.scalars().all()

    async def create_access_link(
        self, applet_id: int, require_login: bool
    ) -> str:
        query: Query = update(AppletSchema)
        query = query.where(AppletSchema.id == applet_id)
        query = query.values(link=uuid.uuid4(), require_login=require_login)
        query = query.returning(AppletSchema.link)
        db_result = await self._execute(query)
        return db_result.scalars().one()

    async def delete_access_link(self, applet_id: int):
        query: Query = update(AppletSchema)
        query = query.where(AppletSchema.id == applet_id)
        query = query.values(link=None, require_login=None)
        await self._execute(query)

    async def transfer_ownership(
        self, applet_id: int, new_owner_id: int
    ) -> AppletSchema:
        query: Query = update(AppletSchema)
        query = query.where(AppletSchema.id == applet_id)
        query = query.values(account_id=new_owner_id)
        query = query.returning(self.schema_class)
        db_result = await self._execute(query)
        return db_result.scalars().one_or_none()

import uuid

from apps.applets.domain import Role
from apps.shared.query_params import BaseQueryParams


class AppletQueryParams(BaseQueryParams):
    owner_id: uuid.UUID | None
    roles: str = ",".join(Role.as_list())
    ordering: str = "-id"

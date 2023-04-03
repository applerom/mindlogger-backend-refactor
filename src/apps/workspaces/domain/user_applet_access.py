import uuid

from apps.shared.domain import InternalModel, PublicModel
from apps.workspaces.domain.constants import Role

__all__ = [
    "UserAppletAccessCreate",
    "UserAppletAccess",
    "PublicUserAppletAccess",
    "UserAppletAccessItem",
    "PinUser",
]


class UserAppletAccessCreate(InternalModel):
    user_id: uuid.UUID
    applet_id: uuid.UUID
    role: Role
    owner_id: uuid.UUID
    invitor_id: uuid.UUID
    meta: dict
    is_pinned: bool


class UserAppletAccess(UserAppletAccessCreate):
    id: uuid.UUID


class PublicUserAppletAccess(PublicModel):
    """Public UserAppletAccess data model."""

    id: uuid.UUID
    user_id: uuid.UUID
    applet_id: uuid.UUID
    role: Role


class UserAppletAccessItem(InternalModel):
    """This is an UserAppletAccess representation for internal needs."""

    user_id: uuid.UUID
    applet_id: uuid.UUID
    role: Role


class AppletUser(InternalModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    roles: list[str]


class PublicAppletUser(PublicModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    roles: list[str]


class PinUser(InternalModel):
    access_id: uuid.UUID

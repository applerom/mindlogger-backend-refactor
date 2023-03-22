import uuid

from pydantic import Field

from apps.activities.domain.response_type_config import (
    ResponseType,
    ResponseTypeConfig,
)
from apps.shared.domain import InternalModel


class ActivityItemUpdate(InternalModel):
    id: uuid.UUID | None
    header_image: str | None
    question: dict[str, str]
    response_type: ResponseType
    answers: list
    config: ResponseTypeConfig
    skippable_item: bool = False
    remove_availability_to_go_back: bool = False


class PreparedActivityItemUpdate(InternalModel):
    id: uuid.UUID | None
    activity_id: uuid.UUID
    header_image: str | None
    question: dict[str, str]
    response_type: str
    answers: list
    config: ResponseTypeConfig
    skippable_item: bool = False
    remove_availability_to_go_back: bool = False


class ActivityUpdate(InternalModel):
    id: uuid.UUID | None
    name: str
    key: uuid.UUID
    description: dict[str, str] = Field(default_factory=dict)
    splash_screen: str = ""
    image: str = ""
    show_all_at_once: bool = False
    is_skippable: bool = False
    is_reviewable: bool = False
    response_is_editable: bool = False
    items: list[ActivityItemUpdate]
    is_hidden: bool = False
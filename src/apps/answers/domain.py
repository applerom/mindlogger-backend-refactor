import datetime
import uuid
from typing import Any

from pydantic import BaseModel, Field, validator

from apps.activities.domain.activity_full import (
    ActivityFull,
    PublicActivityItemFull,
)
from apps.activities.domain.activity_history import (
    ActivityHistoryExport,
    ActivityHistoryFull,
)
from apps.activities.domain.response_type_config import ResponseType
from apps.activities.domain.scores_reports import SubscaleSetting
from apps.activity_flows.domain.flow_full import FlowFull
from apps.applets.domain.base import AppletBaseInfo
from apps.shared.domain import InternalModel, PublicModel


class Text(InternalModel):
    value: str
    should_identify_response: bool = False


class SingleSelection(InternalModel):
    value: uuid.UUID
    additional_text: str | None


class MultipleSelection(InternalModel):
    value: list[uuid.UUID]
    additional_text: str | None


class Slider(InternalModel):
    value: float
    additional_text: str | None


AnswerTypes = SingleSelection | Slider | MultipleSelection | Text

ANSWER_TYPE_MAP: dict[ResponseType, Any] = {
    ResponseType.TEXT: Text,
    ResponseType.SINGLESELECT: SingleSelection,
    ResponseType.MULTISELECT: MultipleSelection,
    ResponseType.SLIDER: Slider,
}


class ItemAnswerCreate(InternalModel):
    answer: str | None
    events: str | None
    item_ids: list[uuid.UUID] | None
    identifier: str | None
    scheduled_time: int | None
    start_time: int
    end_time: int
    user_public_key: str | None

    @validator("item_ids")
    def convert_item_ids(cls, value: list[uuid.UUID]):
        return list(map(str, value))

    @validator("start_time", "end_time", "scheduled_time")
    def convert_time_to_unix_timestamp(cls, value: int):
        if value:
            return value / 1000
        return value


class AnswerItemSchemaAnsweredActivityItem(InternalModel):
    activity_item_history_id: str
    answer: str


class AnswerAlert(InternalModel):
    activity_item_id: uuid.UUID
    message: str


class ClientMeta(InternalModel):
    app_id: str
    app_version: str
    width: int
    height: int


class AppletAnswerCreate(InternalModel):
    applet_id: uuid.UUID
    version: str
    submit_id: uuid.UUID
    flow_id: uuid.UUID | None = None
    activity_id: uuid.UUID
    answer: ItemAnswerCreate
    created_at: int | None
    alerts: list[AnswerAlert] = Field(default_factory=list)
    client: ClientMeta

    @validator("created_at")
    def convert_time_to_unix_timestamp(cls, value: int):
        if value:
            return value / 1000
        return value


class AssessmentAnswerCreate(InternalModel):
    answer: str
    item_ids: list[uuid.UUID]
    reviewer_public_key: str


class AnswerDate(InternalModel):
    created_at: datetime.datetime
    answer_id: uuid.UUID


class ReviewActivity(InternalModel):
    id: uuid.UUID
    name: str
    answer_dates: list[AnswerDate] = Field(default_factory=list)


class SummaryActivity(InternalModel):
    id: uuid.UUID
    name: str
    is_performance_task: bool
    has_answer: bool


class PublicAnswerDate(PublicModel):
    created_at: datetime.datetime
    answer_id: uuid.UUID


class PublicReviewActivity(PublicModel):
    id: uuid.UUID
    name: str
    answer_dates: list[PublicAnswerDate] = Field(default_factory=list)


class PublicSummaryActivity(InternalModel):
    id: uuid.UUID
    name: str
    is_performance_task: bool
    has_answer: bool


class PublicAnswerDates(PublicModel):
    dates: list[datetime.date]


class ActivityAnswer(InternalModel):
    user_public_key: str | None
    answer: str | None
    events: str | None
    item_ids: list[str] = Field(default_factory=list)
    items: list[PublicActivityItemFull] = Field(default_factory=list)


class AppletActivityAnswer(InternalModel):
    answer_id: uuid.UUID | None
    version: str | None
    user_public_key: str | None
    answer: str | None
    events: str | None
    item_ids: list[str] = Field(default_factory=list)
    items: list[PublicActivityItemFull] = Field(default_factory=list)
    start_datetime: datetime.datetime | None
    end_datetime: datetime.datetime | None
    subscale_setting: SubscaleSetting | None


class AssessmentAnswer(InternalModel):
    reviewer_public_key: str | None
    answer: str | None
    item_ids: list[str] = Field(default_factory=list)
    items: list[PublicActivityItemFull] = Field(default_factory=list)
    is_edited: bool = False


class Reviewer(InternalModel):
    first_name: str
    last_name: str


class AnswerReview(InternalModel):
    reviewer_public_key: str | None
    answer: str | None
    item_ids: list[str] = Field(default_factory=list)
    items: list[PublicActivityItemFull] = Field(default_factory=list)
    is_edited: bool = False
    reviewer: Reviewer


class ActivityAnswerPublic(PublicModel):
    user_public_key: str | None
    answer: str | None
    events: str | None
    item_ids: list[str] = Field(default_factory=list)
    items: list[PublicActivityItemFull] = Field(default_factory=list)


class AppletActivityAnswerPublic(PublicModel):
    answer_id: uuid.UUID
    version: str
    user_public_key: str | None
    answer: str | None
    events: str | None
    item_ids: list[str] = Field(default_factory=list)
    items: list[PublicActivityItemFull] = Field(default_factory=list)
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime
    subscale_setting: SubscaleSetting | None


class ReviewerPublic(PublicModel):
    first_name: str
    last_name: str


class AnswerReviewPublic(PublicModel):
    reviewer_public_key: str | None
    answer: str | None
    item_ids: list[str] = Field(default_factory=list)
    items: list[PublicActivityItemFull] = Field(default_factory=list)
    is_edited: bool = False
    reviewer: ReviewerPublic


class AssessmentAnswerPublic(PublicModel):
    reviewer_public_key: str | None
    answer: str | None
    item_ids: list[str] = Field(default_factory=list)
    items: list[PublicActivityItemFull] = Field(default_factory=list)
    is_edited: bool = False


class AnswerNote(InternalModel):
    note: str


class NoteOwner(InternalModel):
    first_name: str
    last_name: str


class AnswerNoteDetail(InternalModel):
    id: uuid.UUID
    user: NoteOwner
    note: str
    created_at: datetime.datetime


class NoteOwnerPublic(PublicModel):
    first_name: str
    last_name: str


class AnswerNoteDetailPublic(PublicModel):
    id: uuid.UUID
    user: NoteOwnerPublic
    note: str
    created_at: datetime.datetime


class UserAnswerDataBase(BaseModel):
    id: uuid.UUID
    submit_id: uuid.UUID
    version: str
    respondent_id: uuid.UUID | str | None = None
    respondent_secret_id: str | None = None
    user_public_key: str | None
    answer: str | None = None
    item_ids: list[str] = Field(default_factory=list)
    events: str | None = None
    scheduled_datetime: datetime.datetime | None = None
    start_datetime: datetime.datetime | None = None
    end_datetime: datetime.datetime | None = None
    applet_history_id: str
    activity_history_id: str
    flow_history_id: str | None
    flow_name: str | None
    reviewed_answer_id: uuid.UUID | str | None
    created_at: datetime.datetime


class RespondentAnswerData(UserAnswerDataBase, InternalModel):
    is_manager: bool = False
    respondent_email: str | None = None


class RespondentAnswerDataPublic(UserAnswerDataBase, PublicModel):
    applet_id: str | None
    activity_id: str | None
    flow_id: str | None

    @validator("applet_id", always=True)
    def extract_applet_id(cls, value, values):
        return values["applet_history_id"][:36]

    @validator("activity_id", always=True)
    def extract_activity_id(cls, value, values):
        return values["activity_history_id"][:36]

    @validator("flow_id", always=True)
    def extract_flow_id(cls, value, values):
        if val := values.get("flow_history_id"):
            return val[:36]

    @validator("start_datetime", "end_datetime")
    def convert_to_timestamp(cls, value: datetime.datetime):
        return int(value.timestamp() * 1000)


class AnswerExport(InternalModel):
    answers: list[RespondentAnswerData] = Field(default_factory=list)
    activities: list[ActivityHistoryFull] = Field(default_factory=list)


class PublicAnswerExport(PublicModel):
    answers: list[RespondentAnswerDataPublic] = Field(default_factory=list)
    activities: list[ActivityHistoryExport] = Field(default_factory=list)


class Version(InternalModel):
    version: str
    created_at: datetime.datetime


class VersionPublic(PublicModel):
    version: str
    created_at: datetime.datetime


class Identifier(InternalModel):
    identifier: str
    user_public_key: str


class IdentifierPublic(PublicModel):
    identifier: str
    user_public_key: str


class SafeApplet(AppletBaseInfo, InternalModel):
    id: uuid.UUID
    version: str
    created_at: datetime.datetime | None
    updated_at: datetime.datetime | None

    activities: list[ActivityFull] = Field(default_factory=list)
    activity_flows: list[FlowFull] = Field(default_factory=list)


class ReportServerEmail(InternalModel):
    body: str
    subject: str
    attachment: str
    email_recipients: list[str]


class ReportServerResponse(InternalModel):
    pdf: str
    email: ReportServerEmail

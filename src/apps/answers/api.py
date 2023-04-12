import uuid

from fastapi import Body, Depends

from apps.answers.domain import (
    ActivityAnswerPublic,
    AppletAnswerCreate,
    PublicAnsweredAppletActivity,
)
from apps.answers.service import AnswerService
from apps.authentication.deps import get_current_user
from apps.shared.domain import Response, ResponseMulti
from apps.users.domain import User
from infrastructure.database import atomic, session_manager


async def create_answer(
    user: User = Depends(get_current_user),
    schema: AppletAnswerCreate = Body(...),
    session=Depends(session_manager.get_session),
) -> None:
    async with atomic(session):
        await AnswerService(session, user.id).create_answer(schema)
    return


async def applet_activities_list(
    id_: uuid.UUID,
    respondent_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(session_manager.get_session),
) -> ResponseMulti[PublicAnsweredAppletActivity]:
    async with atomic(session):
        activities = await AnswerService(session, user.id).applet_activities(
            id_, respondent_id
        )
    return ResponseMulti(
        result=[
            PublicAnsweredAppletActivity.from_orm(activity)
            for activity in activities
        ],
        count=len(activities),
    )


async def applet_answer_retrieve(
    applet_id: uuid.UUID,
    answer_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(session_manager.get_session),
) -> Response[ActivityAnswerPublic]:
    async with atomic(session):
        answer = await AnswerService(session, user.id).get_by_id(
            applet_id, answer_id
        )
    return Response(
        result=ActivityAnswerPublic.from_orm(answer),
    )

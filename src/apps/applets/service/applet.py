import base64
import os
import re
import uuid

from apps.activities.services.activity import ActivityService
from apps.activity_flows.service.flow import FlowService
from apps.applets.crud import AppletsCRUD, UserAppletAccessCRUD
from apps.applets.db.schemas import AppletSchema
from apps.applets.domain import (
    AppletDetail,
    AppletFolder,
    AppletInfo,
    AppletName,
    Role,
)
from apps.applets.domain.applet import Applet, AppletDataRetention
from apps.applets.domain.applet_create import AppletCreate
from apps.applets.domain.applet_full import AppletFull
from apps.applets.domain.applet_link import AppletLink, CreateAccessLink
from apps.applets.domain.applet_update import AppletUpdate
from apps.applets.errors import (
    AppletAlreadyExist,
    AppletLinkAlreadyExist,
    AppletNotFoundError,
    AppletPasswordValidationError,
    AppletsFolderAccessDenied,
)
from apps.applets.service.applet_history_service import AppletHistoryService
from apps.authentication.services import AuthenticationService
from apps.folders.crud import FolderCRUD
from apps.shared.encryption import encrypt, generate_iv
from apps.themes.service import ThemeService
from apps.workspaces.errors import AppletAccessDenied
from apps.workspaces.service.user_applet_access import UserAppletAccessService
from config import settings

__all__ = [
    "AppletService",
    "PublicAppletService",
]

from apps.shared.query_params import QueryParams


class AppletService:
    INITIAL_VERSION = "1.0.0"
    VERSION_DIFFERENCE = 1
    APPLET_NAME_FORMAT_FOR_DUPLICATES = "{0} ({1})"

    # TODO: implement applet create/update logics here

    def __init__(self, user_id: uuid.UUID):
        self.user_id = user_id

    async def create(self, create_data: AppletCreate) -> AppletFull:
        applet = await self._create(create_data)

        await UserAppletAccessService(self.user_id, applet.id).add_role(
            Role.ADMIN
        )
        applet.activities = await ActivityService(self.user_id).create(
            applet.id, create_data.activities
        )
        activity_key_id_map = dict()
        for activity in applet.activities:
            activity_key_id_map[activity.key] = activity.id
        applet.activity_flows = await FlowService().create(
            applet.id, create_data.activity_flows, activity_key_id_map
        )

        await AppletHistoryService(applet.id, applet.version).add_history(
            self.user_id, applet
        )

        return applet

    async def _create(self, create_data: AppletCreate) -> AppletFull:
        applet_id = uuid.uuid4()
        await self._validate_applet_name(create_data.display_name)
        system_encrypted_key = self.create_keys(applet_id)
        schema = await AppletsCRUD().save(
            AppletSchema(
                id=applet_id,
                display_name=create_data.display_name,
                description=create_data.description,
                about=create_data.about,
                image=create_data.image,
                watermark=create_data.watermark,
                theme_id=create_data.theme_id,
                version=self.get_next_version(),
                report_server_ip=create_data.report_server_ip,
                report_public_key=create_data.report_public_key,
                report_recipients=create_data.report_recipients,
                report_include_user_id=create_data.report_include_user_id,
                report_include_case_id=create_data.report_include_case_id,
                report_email_body=create_data.report_email_body,
                hashed_password=AuthenticationService.get_password_hash(
                    create_data.password
                ),
                system_encrypted_key=system_encrypted_key,
            )
        )
        return AppletFull.from_orm(schema)

    async def update(
        self, applet_id: uuid.UUID, update_data: AppletUpdate
    ) -> AppletFull:
        await FlowService().remove_applet_flows(applet_id)
        await ActivityService(self.user_id).remove_applet_activities(applet_id)
        applet = await self._update(applet_id, update_data)

        applet.activities = await ActivityService(self.user_id).update_create(
            applet_id, update_data.activities
        )
        activity_key_id_map = dict()
        for activity in applet.activities:
            activity_key_id_map[activity.key] = activity.id
        applet.activity_flows = await FlowService().update_create(
            applet_id, update_data.activity_flows, activity_key_id_map
        )

        await AppletHistoryService(applet.id, applet.version).add_history(
            self.user_id, applet
        )

        return applet

    async def _validate_applet_name(
        self, display_name: str, exclude_by_id: uuid.UUID | None = None
    ):
        applet_ids_query = UserAppletAccessCRUD().user_applet_ids_query(
            self.user_id
        )
        existed_applet = await AppletsCRUD().get_by_display_name(
            display_name, applet_ids_query, exclude_by_id
        )
        if existed_applet:
            raise AppletAlreadyExist()

    async def _validate_applet_password(
        self, password: str, applet_id: uuid.UUID
    ):
        applet_schema = await AppletsCRUD().get_by_id(applet_id)
        is_verified = AuthenticationService.verify_password_and_hash(
            password, applet_schema.hashed_password
        )
        if not is_verified:
            raise AppletPasswordValidationError()

    async def _update(
        self, applet_id: uuid.UUID, update_data: AppletUpdate
    ) -> AppletFull:
        await self._validate_applet_name(update_data.display_name, applet_id)
        await self._validate_applet_password(update_data.password, applet_id)
        applet_schema = await AppletsCRUD().get_by_id(applet_id)

        schema = await AppletsCRUD().update_by_id(
            applet_id,
            AppletSchema(
                display_name=update_data.display_name,
                description=update_data.description,
                about=update_data.about,
                image=update_data.image,
                watermark=update_data.watermark,
                theme_id=update_data.theme_id,
                version=self.get_next_version(applet_schema.version),
                report_server_ip=update_data.report_server_ip,
                report_public_key=update_data.report_public_key,
                report_recipients=update_data.report_recipients,
                report_include_user_id=update_data.report_include_user_id,
                report_include_case_id=update_data.report_include_case_id,
                report_email_body=update_data.report_email_body,
            ),
        )
        return AppletFull.from_orm(schema)

    def get_next_version(self, version: str | None = None):
        if not version:
            return self.INITIAL_VERSION
        return ".".join(
            list(str(int(version.replace(".", "")) + self.VERSION_DIFFERENCE))
        )

    async def get_list_by_single_language(
        self, language: str, query_params: QueryParams
    ) -> list[AppletInfo]:
        roles: str = query_params.filters.pop("roles")

        schemas = await AppletsCRUD().get_applets_by_roles(
            self.user_id, roles.split(","), query_params
        )
        theme_ids = [schema.theme_id for schema in schemas if schema.theme_id]
        themes = []
        if theme_ids:
            themes = await ThemeService(self.user_id).get_users_by_ids(
                theme_ids
            )
        theme_map = dict((theme.id, theme) for theme in themes)
        applets = []

        for schema in schemas:
            theme = theme_map.get(schema.theme_id)
            applets.append(
                AppletInfo(
                    id=schema.id,
                    display_name=schema.display_name,
                    version=schema.version,
                    description=self._get_by_language(
                        schema.description, language
                    ),
                    theme=theme.dict() if theme else None,
                    about=self._get_by_language(schema.about, language),
                    image=schema.image,
                    watermark=schema.watermark,
                    theme_id=schema.theme_id,
                    report_server_ip=schema.report_server_ip,
                    report_public_key=schema.report_public_key,
                    report_recipients=schema.report_recipients,
                    report_include_user_id=schema.report_include_user_id,
                    report_include_case_id=schema.report_include_case_id,
                    report_email_body=schema.report_email_body,
                    created_at=schema.created_at,
                    updated_at=schema.updated_at,
                )
            )
        return applets

    async def get_list_by_single_language_count(
        self, query_params: QueryParams
    ) -> int:
        roles: str = query_params.filters.pop("roles")
        count = await AppletsCRUD().get_applets_by_roles_count(
            self.user_id, roles.split(","), query_params
        )
        return count

    async def get_single_language_by_id(
        self, applet_id: uuid.UUID, language: str
    ) -> AppletDetail:
        applet_exists = await AppletsCRUD().exist_by_id(applet_id)
        if not applet_exists:
            raise AppletNotFoundError(key="id", value=str(applet_id))
        schema = await AppletsCRUD().get_applet_by_roles(
            self.user_id, applet_id, Role.as_list()
        )
        theme = None
        if not schema:
            raise AppletAccessDenied()
        if schema.theme_id:
            theme = await ThemeService(self.user_id).get_by_id(schema.theme_id)
        applet = AppletDetail(
            id=schema.id,
            display_name=schema.display_name,
            version=schema.version,
            description=self._get_by_language(schema.description, language),
            about=self._get_by_language(schema.about, language),
            image=schema.image,
            theme=theme.dict() if theme else None,
            watermark=schema.watermark,
            theme_id=schema.theme_id,
            report_server_ip=schema.report_server_ip,
            report_public_key=schema.report_public_key,
            report_recipients=schema.report_recipients,
            report_include_user_id=schema.report_include_user_id,
            report_include_case_id=schema.report_include_case_id,
            report_email_body=schema.report_email_body,
            created_at=schema.created_at,
            updated_at=schema.updated_at,
            retention_period=schema.retention_period,
            retention_type=schema.retention_type,
        )
        applet.activities = await ActivityService(
            self.user_id
        ).get_single_language_by_applet_id(applet_id, language)
        applet.activity_flows = (
            await FlowService().get_single_language_by_applet_id(
                applet_id, language
            )
        )
        return applet

    def get_prev_version(self, version: str):
        int_version = int(version.replace(".", ""))
        if int_version < int(self.INITIAL_VERSION.replace(".", "")):
            return self.INITIAL_VERSION
        return ".".join(list(str(int_version - self.VERSION_DIFFERENCE)))

    async def exist_by_id(self, applet_id: uuid.UUID) -> bool:
        return await AppletsCRUD().exist_by_id(applet_id)

    async def delete_applet_by_id(self, applet_id: uuid.UUID):
        await self._validate_delete_applet(self.user_id, applet_id)
        await AppletsCRUD().delete_by_id(applet_id)

    async def _validate_delete_applet(self, user_id, applet_id):
        role = await UserAppletAccessService(
            user_id, applet_id
        ).get_admins_role()
        if not role:
            raise AppletAccessDenied()

    async def set_applet_folder(self, schema: AppletFolder):
        if schema.folder_id:
            await self._move_to_folder(schema.applet_id, schema.folder_id)
        else:
            await self._remove_from_folder(schema.applet_id)

    async def _move_to_folder(
        self, applet_id: uuid.UUID, folder_id: uuid.UUID
    ):
        await self._validate_applet(applet_id)
        await self._validate_folder(folder_id)
        await AppletsCRUD().set_applets_folder(applet_id, folder_id)

    async def _remove_from_folder(self, applet_id: uuid.UUID):
        await self._validate_applet(applet_id)
        await AppletsCRUD().set_applets_folder(applet_id, None)

    async def _validate_applet(self, applet_id: uuid.UUID):
        access = await UserAppletAccessCRUD().get_applet_owner(applet_id)
        if access.user_id != self.user_id:
            raise AppletAccessDenied()

    async def _validate_folder(self, folder_id: uuid.UUID):
        folder = await FolderCRUD().get_by_id(folder_id)

        if folder.creator_id != self.user_id:
            raise AppletsFolderAccessDenied()

    async def get_unique_name(self, applet_name: AppletName) -> str:
        duplicate_names = await AppletsCRUD().get_name_duplicates(
            self.user_id, applet_name.name, applet_name.exclude_applet_id
        )
        if not duplicate_names:
            return applet_name.name

        greatest_number = 0
        for duplicate_name in duplicate_names:
            number = self._get_latest_number(duplicate_name)
            if number > greatest_number:
                greatest_number = number

        return self.APPLET_NAME_FORMAT_FOR_DUPLICATES.format(
            applet_name.name, greatest_number + 1
        )

    def _get_latest_number(self, text) -> int:
        numbers = re.findall("\\(\\d+\\)", text)
        if numbers:
            return int(numbers[-1][1:-1])
        return 0

    async def create_access_link(
        self, applet_id: uuid.UUID, create_request: CreateAccessLink
    ) -> AppletLink:
        await self._validate_applet_access(applet_id)

        applet_instance = await AppletsCRUD().get_by_id(applet_id)
        if applet_instance.link:
            raise AppletLinkAlreadyExist()

        applet_link = await AppletsCRUD().create_access_link(
            applet_id, create_request.require_login
        )
        link = self._generate_link_url(
            create_request.require_login, applet_link
        )
        return AppletLink(link=link)

    async def get_access_link(self, applet_id: uuid.UUID) -> AppletLink:
        await self._validate_applet_access(applet_id)
        applet_instance = await AppletsCRUD().get_by_id(applet_id)
        link = None
        if applet_instance.link:
            link = self._generate_link_url(
                applet_instance.require_login, applet_instance.link
            )

        return AppletLink(link=link)

    async def delete_access_link(self, applet_id: uuid.UUID):
        await self._validate_applet_access(applet_id)

        if not await AppletsCRUD().exist_by_id(applet_id):
            raise AppletNotFoundError(key="id", value=str(applet_id))

        await AppletsCRUD().delete_access_link(applet_id)

    def _generate_link_url(self, require_login: bool, link: str) -> str:
        if require_login:
            url_path = settings.service.urls.frontend.private_link
        else:
            url_path = settings.service.urls.frontend.public_link

        domain = settings.service.urls.frontend.web_base

        url = f"https://{domain}/{url_path}/{str(link)}"

        return url

    @staticmethod
    def _get_by_language(values: dict, language: str):
        """
        Returns value by language key,
         if it does not exist,
         returns first existing or empty string
        """
        try:
            return values[language]
        except KeyError:
            for key, val in values.items():
                return val
            return ""

    async def set_data_retention(
        self, applet_id: uuid.UUID, data_retention: AppletDataRetention
    ):
        await self._validate_applet_access(applet_id)

        if not await AppletsCRUD().exist_by_id(applet_id):
            raise AppletNotFoundError(key="id", value=str(applet_id))

        await AppletsCRUD().set_data_retention(applet_id, data_retention)

    async def _validate_applet_access(self, applet_id: uuid.UUID):
        roles = await UserAppletAccessCRUD().get_user_roles_to_applet(
            self.user_id, applet_id
        )
        if Role.ADMIN not in roles:
            raise AppletAccessDenied()

    def create_keys(self, applet_id: uuid.UUID) -> str:
        key = os.urandom(settings.secrets.key_length)
        iv = generate_iv(str(applet_id))
        system_encrypted_key = encrypt(key, iv=iv)
        return base64.b64encode(system_encrypted_key).decode()


class PublicAppletService:
    async def get_by_link(
        self, link: uuid.UUID, is_private=False
    ) -> Applet | None:
        schema = await AppletsCRUD().get_by_link(link, is_private)
        if not schema:
            return None
        return Applet.from_orm(schema)
from apps.shared.test import BaseTest
from infrastructure.database import rollback


class TestSettings(BaseTest):
    fixtures = [
        "users/fixtures/users.json",
        "themes/fixtures/themes.json",
        "folders/fixtures/folders.json",
        "applets/fixtures/applets.json",
        "applets/fixtures/applet_user_accesses.json",
    ]
    login_url = "/auth/login"
    applet_url = "applets/{applet_id}"
    data_retention = applet_url + "/retentions"

    @rollback
    async def test_applet_set_data_retention(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )

        applet_id = "92917a56-d586-4613-b7aa-991f2c4b15b1"

        retention_data = dict(
            period=1,
            retention="days",
        )

        response = await self.client.post(
            self.data_retention.format(applet_id=applet_id),
            data=retention_data,
        )
        assert response.status_code == 200

        response = await self.client.get(
            self.applet_url.format(applet_id=applet_id)
        )
        assert response.status_code == 200
        assert (
            response.json()["result"]["retentionPeriod"]
            == retention_data["period"]
        )
        assert (
            response.json()["result"]["retentionType"]
            == retention_data["retention"]
        )

    @rollback
    async def test_applet_set_data_retention_for_indefinite(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )

        applet_id = "92917a56-d586-4613-b7aa-991f2c4b15b1"

        retention_data = dict(
            retention="indefinitely",
        )

        response = await self.client.post(
            self.data_retention.format(applet_id=applet_id),
            data=retention_data,
        )
        assert response.status_code == 200

        response = await self.client.get(
            self.applet_url.format(applet_id=applet_id)
        )
        assert response.status_code == 200
        assert response.json()["result"]["retentionPeriod"] is None
        assert (
            response.json()["result"]["retentionType"]
            == retention_data["retention"]
        )

    @rollback
    async def test_applet_set_data_retention_for_indefinite_fail(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )

        applet_id = "92917a56-d586-4613-b7aa-991f2c4b15b1"

        retention_data = dict(
            retention="days",
        )

        response = await self.client.post(
            self.data_retention.format(applet_id=applet_id),
            data=retention_data,
        )
        assert response.status_code == 400

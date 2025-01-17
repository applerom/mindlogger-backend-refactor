from apps.shared.test import BaseTest
from infrastructure.database import rollback


class TestAlert(BaseTest):
    fixtures = [
        "users/fixtures/users.json",
        "applets/fixtures/applets.json",
        "applets/fixtures/applet_histories.json",
        "applets/fixtures/applet_user_accesses.json",
        "alerts/fixtures/alerts.json",
        "workspaces/fixtures/workspaces.json",
    ]

    login_url = "/auth/login"
    alert_list_url = "/alerts"
    watch_alert_url = "/alerts/{alert_id}/is_watched"

    @rollback
    async def test_all_alerts(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )

        response = await self.client.get(self.alert_list_url)
        assert response.status_code == 200
        assert response.json()["count"] == 2

    @rollback
    async def test_watch_alert(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )

        response = await self.client.post(
            self.watch_alert_url.format(
                alert_id="6f794861-0ff6-4c39-a3ed-602fd4e22c58"
            )
        )
        assert response.status_code == 200

        response = await self.client.get(self.alert_list_url)
        assert response.status_code == 200
        assert response.json()["count"] == 2
        assert response.json()["result"][0]["isWatched"] is True

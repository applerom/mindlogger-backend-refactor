from apps.mailing.services import TestMail
from apps.shared.test import BaseTest
from infrastructure.database import rollback


class TestTransfer(BaseTest):
    fixtures = [
        "users/fixtures/users.json",
        "folders/fixtures/folders.json",
        "applets/fixtures/applets.json",
        "applets/fixtures/applet_user_accesses.json",
        "transfer_ownership/fixtures/transfers.json",
    ]

    login_url = "/auth/login"
    transfer_url = "/applets/{applet_id}/transferOwnership"
    response_url = "/applets/{applet_id}/transferOwnership/{key}"

    @rollback
    async def test_initiate_transfer(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )
        data = {"email": "lucy@gmail.com"}

        response = await self.client.post(
            self.transfer_url.format(
                applet_id="92917a56-d586-4613-b7aa-991f2c4b15b1"
            ),
            data=data,
        )

        assert response.status_code == 200
        assert len(TestMail.mails) == 1
        assert TestMail.mails[0].recipients == [data["email"]]
        assert TestMail.mails[0].subject == "Transfer ownership of an applet"

    @rollback
    async def test_initiate_transfer_fail(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )
        data = {"email": "aloevdamirkhon@gmail.com"}

        response = await self.client.post(
            self.transfer_url.format(
                applet_id="00000000-0000-0000-0000-000000000012"
            ),
            data=data,
        )

        assert response.status_code == 404, response.json()

    @rollback
    async def test_decline_transfer(self):
        await self.client.login(self.login_url, "lucy@gmail.com", "Test123")
        response = await self.client.delete(
            self.response_url.format(
                applet_id="92917a56-d586-4613-b7aa-991f2c4b15b1",
                key="6a3ab8e6-f2fa-49ae-b2db-197136677da7",
            ),
        )

        assert response.status_code == 204

    @rollback
    async def test_decline_wrong_transfer(self):
        await self.client.login(self.login_url, "lucy@gmail.com", "Test123")
        response = await self.client.delete(
            self.response_url.format(
                applet_id="00000000-0000-0000-0000-000000000000",
                key="6a3ab8e6-f2fa-49ae-b2db-197136677da7",
            ),
        )

        assert response.status_code == 404

    @rollback
    async def test_re_decline_transfer(self):
        await self.client.login(self.login_url, "lucy@gmail.com", "Test123")
        response = await self.client.delete(
            self.response_url.format(
                applet_id="92917a56-d586-4613-b7aa-991f2c4b15b1",
                key="6a3ab8e6-f2fa-49ae-b2db-197136677da7",
            ),
        )

        assert response.status_code == 204

        response = await self.client.delete(
            self.response_url.format(
                applet_id="92917a56-d586-4613-b7aa-991f2c4b15b1",
                key="6a3ab8e6-f2fa-49ae-b2db-197136677da7",
            ),
        )

        assert response.status_code == 404

    @rollback
    async def test_accept_transfer(self):
        await self.client.login(self.login_url, "lucy@gmail.com", "Test123")
        response = await self.client.post(
            self.response_url.format(
                applet_id="92917a56-d586-4613-b7aa-991f2c4b15b1",
                key="6a3ab8e6-f2fa-49ae-b2db-197136677da7",
            ),
        )

        assert response.status_code == 200

    @rollback
    async def test_accept_wrong_transfer(self):
        await self.client.login(self.login_url, "lucy@gmail.com", "Test123")
        response = await self.client.post(
            self.response_url.format(
                applet_id="00000000-0000-0000-0000-000000000000",
                key="6a3ab8e6-f2fa-49ae-b2db-197136677da7",
            ),
        )

        assert response.status_code == 404

    @rollback
    async def test_re_accept_transfer(self):
        await self.client.login(self.login_url, "lucy@gmail.com", "Test123")
        response = await self.client.post(
            self.response_url.format(
                applet_id="92917a56-d586-4613-b7aa-991f2c4b15b1",
                key="6a3ab8e6-f2fa-49ae-b2db-197136677da7",
            ),
        )

        assert response.status_code == 200

        response = await self.client.post(
            self.response_url.format(
                applet_id="92917a56-d586-4613-b7aa-991f2c4b15b1",
                key="6a3ab8e6-f2fa-49ae-b2db-197136677da7",
            ),
        )

        assert response.status_code == 404

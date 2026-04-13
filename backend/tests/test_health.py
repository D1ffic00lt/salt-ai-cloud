import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import create_app


class HealthTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())

    def test_health(self) -> None:
        response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("app.api.v1.health.engine")
    def test_ready(self, engine_mock: MagicMock) -> None:
        context_mock = MagicMock()
        connection_mock = MagicMock()

        context_mock.__enter__.return_value = connection_mock
        engine_mock.connect.return_value = context_mock

        response = self.client.get("/api/v1/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})


if __name__ == "__main__":
    unittest.main()

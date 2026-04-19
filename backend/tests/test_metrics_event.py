import unittest
import uuid

from fastapi.testclient import TestClient

from app.db.models.user import User
from app.db.session import SessionLocal
from app.main import create_app


class MetricsEventsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())
        self.user_id = self._create_user()
        self.workspace_id = self._create_workspace()
        self.project_id = self._create_project()
        self.run_id = self._create_run()

    def _create_user(self) -> str:
        db = SessionLocal()
        try:
            user = User(
                telegram_id=uuid.uuid4().int % 1_000_000_000_000,
                username=f"test_{uuid.uuid4().hex[:12]}",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return str(user.id)
        finally:
            db.close()

    def _create_workspace(self) -> str:
        payload = {
            "name": "Test Workspace",
            "slug": f"test-workspace-{uuid.uuid4().hex[:12]}",
            "owner_user_id": self.user_id,
        }

        response = self.client.post("/api/v1/workspaces", json=payload)

        self.assertEqual(response.status_code, 201)
        return response.json()["id"]

    def _create_project(self) -> str:
        payload = {
            "name": f"Test Project {uuid.uuid4().hex[:12]}",
            "description": "Project for metrics/events tests",
            "created_by_id": self.user_id,
        }

        response = self.client.post(
            f"/api/v1/workspaces/{self.workspace_id}/projects",
            json=payload,
        )

        self.assertEqual(response.status_code, 201)
        return response.json()["id"]

    def _create_run(self) -> str:
        payload = {
            "name": f"Test Run {uuid.uuid4().hex[:12]}",
            "config": {"lr": 0.001},
            "manifest": {"source": "test"},
            "tags": ["test"],
            "created_by_id": self.user_id,
        }

        response = self.client.post(
            f"/api/v1/projects/{self.project_id}/runs",
            json=payload,
        )

        self.assertEqual(response.status_code, 201)
        return response.json()["id"]

    def test_create_and_list_metrics(self) -> None:
        payload = {
            "key": "loss",
            "value": 0.42,
            "step": 1,
            "payload": {"split": "train"},
        }

        create_response = self.client.post(
            f"/api/v1/runs/{self.run_id}/metrics",
            json=payload,
        )

        self.assertEqual(create_response.status_code, 201)

        created_metric = create_response.json()
        self.assertEqual(created_metric["workspace_id"], self.workspace_id)
        self.assertEqual(created_metric["run_id"], self.run_id)
        self.assertEqual(created_metric["key"], payload["key"])
        self.assertEqual(created_metric["value"], payload["value"])
        self.assertEqual(created_metric["step"], payload["step"])
        self.assertEqual(created_metric["payload"], payload["payload"])
        self.assertIsNotNone(created_metric["timestamp"])
        self.assertIsNotNone(created_metric["created_at"])

        list_response = self.client.get(f"/api/v1/runs/{self.run_id}/metrics")

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)
        self.assertEqual(list_response.json()[0]["id"], created_metric["id"])

    def test_create_and_list_events(self) -> None:
        payload = {
            "type": "train_started",
            "level": "info",
            "message": "Training started",
            "payload": {"epoch": 1},
        }

        create_response = self.client.post(
            f"/api/v1/runs/{self.run_id}/events",
            json=payload,
        )

        self.assertEqual(create_response.status_code, 201)

        created_event = create_response.json()
        self.assertEqual(created_event["workspace_id"], self.workspace_id)
        self.assertEqual(created_event["run_id"], self.run_id)
        self.assertEqual(created_event["type"], payload["type"])
        self.assertEqual(created_event["level"], payload["level"])
        self.assertEqual(created_event["message"], payload["message"])
        self.assertEqual(created_event["payload"], payload["payload"])
        self.assertIsNotNone(created_event["timestamp"])
        self.assertIsNotNone(created_event["created_at"])

        list_response = self.client.get(f"/api/v1/runs/{self.run_id}/events")

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)
        self.assertEqual(list_response.json()[0]["id"], created_event["id"])

    def test_metrics_and_events_return_404_for_unknown_run(self) -> None:
        unknown_run_id = str(uuid.uuid4())

        metric_response = self.client.post(
            f"/api/v1/runs/{unknown_run_id}/metrics",
            json={"key": "loss", "value": 0.42},
        )
        event_response = self.client.post(
            f"/api/v1/runs/{unknown_run_id}/events",
            json={"type": "train_started"},
        )
        metrics_list_response = self.client.get(
            f"/api/v1/runs/{unknown_run_id}/metrics",
        )
        events_list_response = self.client.get(
            f"/api/v1/runs/{unknown_run_id}/events",
        )

        self.assertEqual(metric_response.status_code, 404)
        self.assertEqual(event_response.status_code, 404)
        self.assertEqual(metrics_list_response.status_code, 404)
        self.assertEqual(events_list_response.status_code, 404)

    def test_finished_run_rejects_metrics_and_events(self) -> None:
        finish_response = self.client.post(f"/api/v1/runs/{self.run_id}/finish")

        self.assertEqual(finish_response.status_code, 200)
        self.assertEqual(finish_response.json()["status"], "finished")

        metric_response = self.client.post(
            f"/api/v1/runs/{self.run_id}/metrics",
            json={"key": "loss", "value": 0.42},
        )
        event_response = self.client.post(
            f"/api/v1/runs/{self.run_id}/events",
            json={"type": "train_started"},
        )

        self.assertEqual(metric_response.status_code, 409)
        self.assertEqual(event_response.status_code, 409)

    def test_failed_run_rejects_metrics_and_events(self) -> None:
        fail_response = self.client.post(f"/api/v1/runs/{self.run_id}/fail")

        self.assertEqual(fail_response.status_code, 200)
        self.assertEqual(fail_response.json()["status"], "failed")

        metric_response = self.client.post(
            f"/api/v1/runs/{self.run_id}/metrics",
            json={"key": "loss", "value": 0.42},
        )
        event_response = self.client.post(
            f"/api/v1/runs/{self.run_id}/events",
            json={"type": "train_started"},
        )

        self.assertEqual(metric_response.status_code, 409)
        self.assertEqual(event_response.status_code, 409)


if __name__ == "__main__":
    unittest.main()

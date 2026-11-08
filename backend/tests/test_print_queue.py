import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DEVICE_TOKEN", "test-device-token")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
from models.order import Order
from routes.orders import router
from security import require_print_device


class PrintQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.Session = sessionmaker(bind=cls.engine, autoflush=False, autocommit=False)
        Base.metadata.create_all(bind=cls.engine)

        app = FastAPI()
        app.include_router(router)
        cls.app = app

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        def override_auth():
            return None

        self.app.dependency_overrides[require_print_device] = override_auth
        self.client = TestClient(self.app)

        session = self.Session()
        session.add_all([
            Order(order_id="UP-TEST001", file_id="file-1", pages=1, copies=1,
                  print_type="bw", paper_size="a4", sides="single",
                  orientation="portrait", amount=2, payment_status="pending",
                  print_status="queued"),
            Order(order_id="UP-TEST002", file_id="file-2", pages=2, copies=1,
                  print_type="bw", paper_size="a4", sides="single",
                  orientation="portrait", amount=4, payment_status="pending",
                  print_status="queued"),
        ])
        session.commit()
        session.close()

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def test_claim_returns_oldest_and_marks_claimed(self):
        response = self.client.get("/print-queue/next")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["job"]["order_id"], "UP-TEST001")

        session = self.Session()
        order = session.query(Order).filter_by(order_id="UP-TEST001").one()
        self.assertEqual(order.print_status, "claimed")
        self.assertIsNotNone(order.claimed_at)
        session.close()

    def test_second_claim_gets_next_job_not_same_job(self):
        first = self.client.get("/print-queue/next").json()["job"]
        second = self.client.get("/print-queue/next").json()["job"]
        self.assertNotEqual(first["order_id"], second["order_id"])

    def test_expired_claim_is_requeued(self):
        from datetime import datetime, timedelta
        session = self.Session()
        order = session.query(Order).filter_by(order_id="UP-TEST001").one()
        order.print_status = "claimed"
        order.claimed_at = datetime.utcnow() - timedelta(minutes=3)
        session.commit()
        session.close()

        response = self.client.get("/print-queue/next")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["job"]["order_id"], "UP-TEST001")

    def test_invalid_device_token_rejected(self):
        self.app.dependency_overrides.clear()
        response = self.client.get("/print-queue/next", headers={"X-Device-Token": "wrong"})
        self.assertEqual(response.status_code, 401)

    def test_claimed_job_can_start_and_complete(self):
        self.client.get("/print-queue/next")
        started = self.client.post("/order/UP-TEST001/start-printing")
        self.assertEqual(started.status_code, 200)
        completed = self.client.post("/order/UP-TEST001/complete-printing")
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.json()["print_status"], "completed")


if __name__ == "__main__":
    unittest.main()

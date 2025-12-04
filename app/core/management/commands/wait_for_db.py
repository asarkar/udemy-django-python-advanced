"""Django management command to wait for the database to be available."""

import time
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Command that waits for database to be available before proceeding."""

    help = "Wait for database to be available"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="Timeout in seconds (default: 30)",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=2,
            help="Retry interval in seconds (default: 2)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        timeout: int = options["timeout"]
        interval: int = options["interval"]
        start = time.time()

        self.stdout.write("Waiting for database...")

        while time.time() - start < timeout:
            try:
                connections["default"].ensure_connection()
                self.stdout.write(self.style.SUCCESS("Database is ready!"))
                return
            except OperationalError as e:
                self.stdout.write(f"Database not ready ({e}), retrying in {interval}s...")
                time.sleep(interval)

        raise SystemExit("ERROR: Database not reachable after timeout")

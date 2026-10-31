
import json
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import docker

PORT = 5001
CONTAINER_NAME = "selfheal-nginx"
COOLDOWN_SECONDS = 120
MAX_RESTARTS = 3
RESTART_WINDOW_SECONDS = 600
HEALTH_TIMEOUT_SECONDS = 30
STATE_FILE = Path("/app/recovery-state.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("/app/recovery.log"),
        logging.StreamHandler(),
    ],
)

client = docker.from_env()
state_lock = threading.Lock()


def load_state():
    if not STATE_FILE.exists():
        return {"restart_times": [], "last_restart_time": 0}

    try:
        data = json.loads(STATE_FILE.read_text())
        return {
            "restart_times": [
                float(t) for t in data.get("restart_times", [])
            ],
            "last_restart_time": float(
                data.get("last_restart_time", 0)
            ),
        }
    except (ValueError, TypeError, json.JSONDecodeError):
        logging.exception("Recovery state is invalid; refusing to start")
        raise RuntimeError("Cannot safely load recovery state")


def save_state(state):
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2))
    os.replace(temporary, STATE_FILE)


state = load_state()


def verify_health(container):
    deadline = time.time() + HEALTH_TIMEOUT_SECONDS

    while time.time() < deadline:
        try:
            container.reload()
            status = container.status
            health = (
                container.attrs.get("State", {})
                .get("Health", {})
                .get("Status", "not-configured")
            )

            logging.info("Nginx status=%s health=%s", status, health)

            if status == "running" and health == "healthy":
                logging.info("Recovery verified: Nginx is healthy")
                return True

        except docker.errors.DockerException:
            logging.exception("Could not verify Nginx health")
            return False

        time.sleep(3)

    logging.error("Nginx did not become healthy within 30 seconds")
    return False


class RecoveryHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1_000_000:
                self.send_error(400, "Invalid content length")
                return

            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object")

            alerts = payload.get("alerts", [])
            if not isinstance(alerts, list):
                raise ValueError("Expected alerts to be a list")

        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid JSON payload")
            return

        firing = any(
            isinstance(alert, dict)
            and alert.get("status") == "firing"
            and alert.get("labels", {}).get("alertname")
            == "NginxWebsiteDown"
            for alert in alerts
        )

        if not firing:
            self.reply(200, "Alert ignored")
            return

        with state_lock:
            now = time.time()
            state["restart_times"] = [
                t for t in state["restart_times"]
                if now - t < RESTART_WINDOW_SECONDS
            ]

            if len(state["restart_times"]) >= MAX_RESTARTS:
                logging.error("Restart limit reached: 3 in 10 minutes")
                self.reply(200, "Restart limit reached")
                return

            if (
                state["last_restart_time"]
                and now - state["last_restart_time"] < COOLDOWN_SECONDS
            ):
                logging.warning("Cooldown active; restart skipped")
                self.reply(200, "Cooldown active")
                return

            try:
                container = client.containers.get(CONTAINER_NAME)

                state["restart_times"].append(now)
                state["last_restart_time"] = now
                save_state(state)

                logging.warning("Restarting %s", CONTAINER_NAME)
                container.restart(timeout=10)
                logging.info("Restart command completed")
                verify_health(container)

            except (docker.errors.DockerException, OSError, RuntimeError):
                logging.exception("Recovery operation failed")

        self.reply(200, "Alert processed")

    def reply(self, status, message):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

    def log_message(self, format_string, *args):
        logging.info(format_string, *args)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), RecoveryHandler)
    logging.info("Recovery webhook listening on port %s", PORT)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        client.close()

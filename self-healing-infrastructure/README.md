# Self-Healing Infrastructure with Prometheus and Docker

## 1. Project Overview
This project implements automated failure detection, alerting, and recovery for an Nginx website using Docker, Prometheus, Blackbox Exporter, Alertmanager, and Python.

## 2. Architecture
1. Blackbox Exporter probes the Nginx website.
2. Prometheus collects probe_success metrics every 15 seconds.
3. Prometheus raises NginxWebsiteDown when the probe fails continuously for 30 seconds.
4. Alertmanager forwards the firing alert to the Python recovery webhook.
5. The Python service restarts the Nginx container.
6. The service verifies that Nginx returns to a healthy state.
7. Restart timestamps are stored persistently to enforce recovery limits.

## 3. Technology Stack
- Docker and Docker Compose
- Nginx
- Prometheus
- Blackbox Exporter
- Alertmanager
- Python 3
- Docker Python SDK

## 4. Recovery Safeguards
- Cooldown between restart attempts
- Maximum of 3 restart attempts within a 10-minute window
- Persistent restart-state file
- Post-restart health verification
- HTTP webhook input validation

## 5. Validation Results
- Empty webhook payload was accepted and ignored.
- Prometheus detected the stopped Nginx container.
- The NginxWebsiteDown alert fired.
- Alertmanager triggered the recovery service.
- The recovery service restarted Nginx automatically.
- Nginx returned to healthy status approximately 6 seconds after the restart began.
- Recovery timestamps were saved to recovery-state.json.

## 6. Troubleshooting
### Alert remains pending
The alert rule requires the failure to persist for 30 seconds.

### Website does not recover
Check Prometheus alerts, Alertmanager status, recovery-service logs, Docker permissions, and Nginx health.

### DNS or image-pull problems
Check host DNS resolution, Docker networking, and container logs before changing cluster-wide DNS settings.

### Recovery service logs
docker logs selfheal-recovery

### Prometheus alerts
docker exec selfheal-prometheus wget -qO- http://localhost:9090/api/v1/alerts

### Nginx status
docker inspect selfheal-nginx --format 'Status={{.State.Status}} Health={{.State.Health.Status}}'

## 7. Security Considerations
The recovery service has access to the Docker socket, which can provide extensive control over the host. This setup is for a controlled lab environment. Do not expose the recovery webhook publicly. Production deployments should use authenticated requests, restricted permissions, secret management, and audit logging.

## 8. Future Improvements
- Add authenticated webhook requests.
- Add email or chat notifications.
- Export recovery metrics to Prometheus.
- Add dashboards and recovery history.
- Test additional failure scenarios.
- Deploy the recovery workflow to Kubernetes.

## 9. Interview Summary
I built and tested a self-healing infrastructure lab using Docker Compose, Prometheus, Blackbox Exporter, Alertmanager, and Python. I configured automated website failure detection and webhook-based recovery, implemented restart cooldown and attempt limits with persistent state, and verified recovery through container health checks.

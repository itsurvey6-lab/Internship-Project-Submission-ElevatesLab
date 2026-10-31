# Observability Stack — Metrics, Logs & Distributed Tracing

A containerized observability project demonstrating how to monitor a Flask application using metrics, centralized logs, dashboards, and distributed tracing.

## Project Overview

This project brings together monitoring, logging, and tracing to help investigate application performance and errors from a single observability stack.

### Technology Stack

| Technology | Purpose |
|---|---|
| Python / Flask | Demo application and HTTP endpoints |
| Prometheus | Metrics collection and querying |
| Grafana | Monitoring dashboards and log exploration |
| Loki | Centralized log storage and querying |
| Grafana Alloy | Docker container log collection and forwarding |
| Jaeger | Distributed trace collection and visualization |
| Docker Compose | Container orchestration |

## Architecture

```text
                  Flask Application
                   /     |      \
                  /      |       \
             Metrics    Logs     Traces
                |         |         |
                v         v         v
           Prometheus   Alloy     Jaeger
                |         |
                |         v
                |        Loki
                |         |
                v         v
                 Grafana
             Dashboards / Explore
```

Prometheus scrapes application metrics. Alloy discovers Docker containers and forwards their logs to Loki. The application exports trace data to Jaeger. Grafana provides dashboards and interfaces for exploring metrics and logs.

## Application Endpoints

| Endpoint | Purpose |
|---|---|
| `/` | Application home endpoint |
| `/health` | Health-check endpoint |
| `/work` | Workload simulation |
| `/slow` | Slow-request simulation |
| `/error` | Intentional HTTP 500 error for testing |
| `/metrics` | Prometheus metrics endpoint |

The `/error` endpoint intentionally generates an error for testing observability. It is a demonstration endpoint, not a production failure mechanism.

## Accessing the Services

When accessing the machine over your local network, replace `HOST_IP` with its reachable IP address.

| Service | URL |
|---|---|
| Application | `http://HOST_IP:5000` |
| Prometheus | `http://HOST_IP:9090` |
| Grafana | `http://HOST_IP:3000` |
| Jaeger UI | `http://HOST_IP:16686` |

Loki and Alloy are infrastructure components used by the stack.

## Prerequisites

- Linux host or compatible Docker environment
- Docker Engine
- Docker Compose plugin
- Sufficient memory and disk space for the containers

## Start the Project

Clone the repository, enter the project directory, and start the services:

```bash
git clone https://github.com/itsurvey6-lab/monitoring-observability.git
cd monitoring-observability
docker compose up -d --build
```

Check container status:

```bash
docker compose ps
```

View service logs:

```bash
docker compose logs --tail=50
```

## Verify Metrics

Open Prometheus and query:

```promql
up
```

To inspect HTTP request counts:

```promql
http_requests_total
```

To calculate the HTTP request rate:

```promql
sum(rate(http_requests_total[5m]))
```

To inspect HTTP 5xx errors:

```promql
sum(rate(http_requests_total{status=~"5.."}[5m]))
```

## Verify Logs

Open Grafana, navigate to **Explore**, and select Loki.

Show application logs:

```logql
{service="app"}
```

Find simulated application failures:

```logql
{service="app"} |= "simulated_failure"
```

Find error-level log entries:

```logql
{service="app"} |= "ERROR"
```

The application emits structured JSON logs containing fields such as severity, service name, request ID, trace ID, HTTP method, endpoint, status code, and request duration.

## Verify Distributed Tracing

Open the Jaeger UI and select the `observability-demo` service when available.

Generate requests to the application, including `/error` and `/slow`, and inspect the resulting traces and spans.

Trace availability depends on the application's instrumentation and successful delivery of trace data to Jaeger.

## Troubleshooting

### Check container health

```bash
docker compose ps
```

### Inspect a specific service

```bash
docker compose logs --tail=100 app
docker compose logs --tail=100 prometheus
docker compose logs --tail=100 loki
docker compose logs --tail=100 alloy
docker compose logs --tail=100 jaeger
docker compose logs --tail=100 grafana
```

### Check Loki readiness

```bash
curl -s http://localhost:3100/ready
```

### Check application metrics

```bash
curl -s http://localhost:5000/metrics
```

### Generate a test error

```bash
curl -i http://localhost:5000/error
```

A `500 Internal Server Error` response is expected for this intentional test endpoint.

## Stop the Project

Stop the containers without deleting their persistent data:

```bash
docker compose down
```

Avoid `docker compose down -v` unless you deliberately intend to remove associated volumes.

## Security Notes

- Do not commit `.env` files containing credentials or secrets.
- Do not publish passwords, API tokens, or private configuration.
- Restrict access to monitoring interfaces when deploying outside a trusted lab.
- Use appropriate authentication, network controls, and secret management for production deployments.

## Project Status

The core stack has been exercised with application metrics, structured logs, simulated errors, and distributed traces.

Before treating this repository as a reproducible release, verify the committed configuration files, Grafana dashboard exports, persistence settings, and fresh-clone setup.

## Author

**IT Infrastructure & Observability Lab**

Technologies: Docker, Python, Prometheus, Grafana, Loki, Grafana Alloy, Jaeger.

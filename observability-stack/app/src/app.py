import json
import logging
import random
import time
import uuid

from flask import Flask, g, request, jsonify, Response
from prometheus_client import Counter, Histogram, generate_latest
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Application identity
SERVICE_NAME = "observability-demo"

# Configure JSON-style application logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(SERVICE_NAME)

# Configure OpenTelemetry tracing
resource = Resource.create({"service.name": SERVICE_NAME})
provider = TracerProvider(resource=resource)

provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint="http://jaeger:4318/v1/traces"
        )
    )
)

trace.set_tracer_provider(provider)
tracer = trace.get_tracer(SERVICE_NAME)

# Create Flask application and trace incoming HTTP requests
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# Prometheus metrics
REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)


@app.before_request
def before_request():
    g.start_time = time.perf_counter()
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))


@app.after_request
def after_request(response):
    elapsed = time.perf_counter() - g.start_time
    endpoint = request.url_rule.rule if request.url_rule else "unmatched"

    # Record request count and response time
    REQUESTS.labels(
        request.method, endpoint, str(response.status_code)
    ).inc()

    LATENCY.labels(request.method, endpoint).observe(elapsed)

    # Attach trace and request IDs to the log
    span = trace.get_current_span()
    context = span.get_span_context()
    trace_id = format(context.trace_id, "032x") if context.is_valid else None

    logger.info(json.dumps({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": "INFO" if response.status_code < 500 else "ERROR",
        "service": SERVICE_NAME,
        "request_id": g.request_id,
        "trace_id": trace_id,
        "method": request.method,
        "path": request.path,
        "status": response.status_code,
        "duration_ms": round(elapsed * 1000, 2)
    }))

    response.headers["X-Request-ID"] = g.request_id
    return response


@app.route("/")
def home():
    return jsonify(
        service=SERVICE_NAME,
        message="Observability demo is running"
    )


@app.route("/health")
def health():
    return jsonify(status="healthy")


@app.route("/work")
def work():
    with tracer.start_as_current_span("business_operation"):
        time.sleep(random.uniform(0.05, 0.25))
        return jsonify(result="work completed")


@app.route("/slow")
def slow():
    with tracer.start_as_current_span("slow_operation"):
        time.sleep(2)
        return jsonify(result="slow request completed")


@app.route("/error")
def error():
    from opentelemetry.trace import Status, StatusCode

    with tracer.start_as_current_span("simulated_failure") as span:
        span.set_attribute("error.simulated", True)
        span.set_status(Status(StatusCode.ERROR, "Simulated application failure"))

        logger.error(json.dumps({
            "level": "ERROR",
            "service": SERVICE_NAME,
            "event": "simulated_failure",
            "message": "Intentional test failure"
        }))

        return jsonify(error="intentional test failure"), 500


@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        mimetype="text/plain; version=0.0.4"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

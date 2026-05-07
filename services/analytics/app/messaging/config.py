import os


def rabbitmq_url() -> str:
    """Return the AMQP URL.

    Honor RABBITMQ_URL if explicitly set; otherwise build it from the
    individual env vars used by docker-compose.yml.
    """
    explicit = os.getenv("RABBITMQ_URL")
    if explicit:
        return explicit

    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = os.getenv("RABBITMQ_PORT", "5672")
    vhost = os.getenv("RABBITMQ_VHOST", "/")
    return f"amqp://{user}:{password}@{host}:{port}{vhost}"


# Ops knobs
PUBLISH_TIMEOUT_SECONDS = float(os.getenv("RABBITMQ_PUBLISH_TIMEOUT", "2.0"))
RECONNECT_INTERVAL_SECONDS = float(os.getenv("RABBITMQ_RECONNECT_INTERVAL", "5.0"))

from typing import Any, Optional

from decouple import config
from invoke import task


@task
def create_pubsub(
    ctx: Any,
    topic: str,
    create_subscription: bool = False,
    message_retention_duration: int = 0,
    retain_acked_messages: bool = False,
) -> None:
    """Create Pub/Sub."""
    from google.api_core.exceptions import AlreadyExists
    from google.cloud import pubsub_v1
    from google.protobuf.duration_pb2 import Duration

    project_id = config("PROJECT_ID")
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()
    topic_path = publisher.topic_path(project_id, topic)
    subscription_path = subscriber.subscription_path(project_id, topic)

    try:
        publisher.create_topic(request={"name": topic_path})
    except AlreadyExists:
        pass

    if create_subscription:
        # Retain messages for 24 hours
        message_retention_duration = Duration()
        message_retention_duration.FromSeconds(60 * 60 * 24)
        request = {
            "name": subscription_path,
            "topic": topic_path,
            "enable_message_ordering": True,
        }
        if message_retention_duration:
            request["message_retention_duration"] = message_retention_duration
        if retain_acked_messages:
            request["retain_acked_messages"] = True
        with subscriber:
            try:
                subscriber.create_subscription(request=request)
            except AlreadyExists:
                pass


def get_docker_secrets() -> str:
    """Get docker secrets."""
    build_args = [
        f'{secret}="{config(secret)}"' for secret in ("PROJECT_ID", "SENTRY_DSN")
    ]
    return " ".join([f"--build-arg {build_arg}" for build_arg in build_args])


def get_container_name(
    hostname: str = "asia.gcr.io",
    image: str = "asyncio-quant-tick",
    tag: Optional[str] = None,
) -> str:
    """Get container name."""
    project_id = config("PROJECT_ID")
    container_name = f"{hostname}/{project_id}/{image}"
    if tag:
        container_name += f":{tag}"
    return container_name


@task
def build_container(
    ctx: Any, hostname: str = "asia.gcr.io", image: str = "asyncio-quant-tick"
) -> None:
    """Build container."""
    name = get_container_name(hostname, image)
    requirements = ["cryptfeed", "python-decouple"]
    # Versions
    reqs = "\\ ".join(
        [
            req
            for req in ctx.run("poetry export --dev --without-hashes").stdout.split(
                "\n"
            )
            if req.split("==")[0] in requirements
        ]
    )
    # Build
    build_args = f"--build-arg POETRY_EXPORT={reqs} " + get_docker_secrets()
    cmd = f"docker build {build_args} --file Dockerfile --tag {name} ."
    ctx.run(cmd)


@task
def push_container(
    ctx: Any, hostname: str = "asia.gcr.io", image: str = "asyncio-quant-tick"
) -> None:
    """Push container."""
    name = get_container_name(hostname, image)
    ctx.run(f"docker push {name}")


@task
def deploy_container(
    ctx: Any,
    name: str = "asyncio-quant-tick",
    container_name: str | None = None,
    machine_type: str = "e2-micro",
    zone: str = "asia-northeast1-a",
) -> None:
    """Deploy container."""
    container_name = container_name or get_container_name(tag="latest")
    service_account = config("SERVICE_ACCOUNT")
    # A best practice is to set the full cloud-platform access scope on the instance,
    # then securely limit the service account's API access with IAM roles.
    # https://cloud.google.com/compute/docs/access/service-accounts#accesscopesiam
    scopes = "cloud-platform"
    cmd = f"""
        gcloud compute instances create-with-container {name} \
            --machine-type {machine_type} \
            --zone {zone} \
            --container-image {container_name} \
            --service-account {service_account} \
            --scopes {scopes}
    """
    ctx.run(cmd)


@task
def update_container(
    ctx: Any, hostname: str = "asia.gcr.io", name: str = "asyncio-quant-tick"
) -> None:
    """Update container."""
    build_container(ctx, hostname=hostname, image=name)
    push_container(ctx, hostname=hostname, image=name)
    ctx.run(f"gcloud compute instances reset {name}")

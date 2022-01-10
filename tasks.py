import re

from decouple import config
from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1
from google.protobuf.duration_pb2 import Duration
from invoke import task

from cryptofeed_werks.constants import (
    CRYPTOFEED_WERKS,
    PRODUCTION_ENV_VARS,
    PROJECT_ID,
    SERVICE_ACCOUNT,
)
from cryptofeed_werks.utils import get_container_name

NAME_REGEX = re.compile(r"^(\w+)_gcp$")


@task
def create_pubsub(
    c,
    topic,
    create_subscription=False,
    message_retention_duration=0,
    retain_acked_messages=False,
):
    project_id = config(PROJECT_ID)
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


@task
def create_all_pubsub(c):
    pass


def docker_secrets():
    build_args = [f'{secret}="{config(secret)}"' for secret in PRODUCTION_ENV_VARS]
    return " ".join([f"--build-arg {build_arg}" for build_arg in build_args])


@task
def build_container(ctx, hostname="asia.gcr.io", image=CRYPTOFEED_WERKS):
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
    build_args = f"--build-arg POETRY_EXPORT={reqs} " + docker_secrets()
    cmd = f"docker build {build_args} --file Dockerfile --tag {name} ."
    ctx.run(cmd)


@task
def push_container(c, hostname="asia.gcr.io", image=CRYPTOFEED_WERKS):
    name = get_container_name(hostname, image)
    c.run(f"docker push {name}")


@task
def deploy_container(
    c,
    name=CRYPTOFEED_WERKS,
    container_name=None,
    machine_type="e2-micro",
    zone="asia-northeast1-a",
):
    container_name = container_name or get_container_name(tag="latest")
    service_account = config(SERVICE_ACCOUNT)
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
    c.run(cmd)


@task
def update_container(c, hostname="asia.gcr.io", name=CRYPTOFEED_WERKS):
    build_container(c, hostname=hostname, image=name)
    push_container(c, hostname=hostname, image=name)
    c.run(f"gcloud compute instances reset {name}")

import os
import re

from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1
from google.protobuf.duration_pb2 import Duration
from invoke import task

from cryptofeed_werks.constants import CRYPTOFEED_WERKS, PROJECT_ID, SERVICE_ACCOUNT
from cryptofeed_werks.utils import (
    get_container_name,
    get_deploy_env_vars,
    set_environment,
)

set_environment()

NAME_REGEX = re.compile(r"^(\w+)_gcp$")


@task
def create_pubsub(
    c,
    topic,
    create_subscription=False,
    message_retention_duration=0,
    retain_acked_messages=False,
):
    project_id = os.environ[PROJECT_ID]
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


@task
def export_requirements(c):
    c.run("poetry export --output requirements.txt")
    c.run("poetry export --dev --output requirements-dev.txt")


@task
def build_container(c, hostname="asia.gcr.io", image=CRYPTOFEED_WERKS):
    # Ensure requirements
    export_requirements(c)
    build_args = get_deploy_env_vars(pre="--build-arg ", sep=" ")
    name = get_container_name(hostname, image)
    cmd = f"""
        docker build \
            {build_args} \
            --file Dockerfile \
            --tag {name} .
    """
    c.run(cmd)


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
    service_account = os.environ.get(SERVICE_ACCOUNT)
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

import base64
import json
import os
from pathlib import Path
from typing import Optional

from google.api_core import retry
from google.cloud import pubsub_v1
from google.protobuf.timestamp_pb2 import Timestamp

from .constants import (
    CRYPTOFEED_WERKS,
    GCP_APPLICATION_CREDENTIALS,
    LOCAL_ENV_VARS,
    PRODUCTION_ENV_VARS,
    PROJECT_ID,
)


def set_environment():
    if not os.path.exists("/.dockerenv"):
        with open("env.yaml", "r") as env:
            for line in env:
                key, value = line.split(": ")
                if key in LOCAL_ENV_VARS:
                    v = value.strip()
                    if key in GCP_APPLICATION_CREDENTIALS:
                        path = Path.cwd().parents[0] / "keys" / v
                        v = str(path.resolve())
                    os.environ[key] = v


def get_env_vars():
    env_vars = {}
    with open("env.yaml", "r") as env:
        for line in env:
            key, value = line.split(": ")
            env_vars[key] = value.strip()
    return env_vars


def get_deploy_env_vars(pre="", sep=",", keys=PRODUCTION_ENV_VARS):
    env_vars = [
        f"{pre}{key}={value}" for key, value in get_env_vars().items() if key in keys
    ]
    return f"{sep}".join(env_vars)


def get_env_list(key):
    value = os.environ.get(key, "")
    return [v for v in value.split(" ") if v]


def set_env_list(key, value):
    if "PYTEST_CURRENT_TEST" in os.environ:
        values = get_env_list(key)
        values.append(value)
        values = list(set(values))
        os.environ[key] = " ".join(values)


def is_local():
    return all([os.environ.get(key) is None for key in LOCAL_ENV_VARS])


def get_topic_path():
    return pubsub_v1.PublisherClient().topic_path(
        os.getenv(PROJECT_ID), CRYPTOFEED_WERKS
    )


def get_subscription_path(topic):
    return pubsub_v1.SubscriberClient().subscription_path(os.getenv(PROJECT_ID), topic)


def get_messages(topic_id, retry_deadline=5):
    subscriber = pubsub_v1.SubscriberClient()
    project_id = os.environ[PROJECT_ID]
    subscription_path = subscriber.subscription_path(project_id, topic_id)
    with subscriber:
        response = subscriber.pull(
            {"subscription": subscription_path, "max_messages": 1000000},
            retry=retry.Retry(deadline=retry_deadline),
        )
        if response.received_messages:
            # Acknowledge, at most once promise is fulfilled
            subscriber.acknowledge(
                request={
                    "subscription": subscription_path,
                    "ack_ids": [msg.ack_id for msg in response.received_messages],
                }
            )
            return response.received_messages


def delete_messages(topic_id, timestamp_from, retry_deadline=5):
    subscriber = pubsub_v1.SubscriberClient()
    project_id = os.environ[PROJECT_ID]
    subscription_path = subscriber.subscription_path(project_id, topic_id)
    # https://cloud.google.com/pubsub/docs/replay-qs#seek_to_a_timestamp
    t = timestamp_from.timestamp()
    timestamp = Timestamp(seconds=int(t), nanos=int(t % 1 * 1e9))
    request = {"subscription": subscription_path, "time": timestamp}
    with subscriber:
        subscriber.seek(request, retry=retry.Retry(deadline=retry_deadline))


def get_request_data(request, keys):
    """For HTTP functions"""
    data = {key: None for key in keys}
    json_data = request.get_json()
    param_data = request.args
    for key in keys:
        if key in json_data:
            data[key] = json_data[key]
        elif key in param_data:
            data[key] = param_data[key]
    return data


def base64_decode_event(event):
    """
    Use with pub/sub functions:

    def pubsub_function(event, context):
        data = base64_decode_event(event)
    """
    if "data" in event:
        data = base64.b64decode(event["data"]).decode()
        return json.loads(data)
    else:
        return {}


def base64_encode_dict(data: dict) -> str:
    d = json.dumps(data).encode()
    return base64.b64encode(d)


def publish(topic_id: str, data: dict) -> None:
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(os.environ[PROJECT_ID], topic_id)
    publisher.publish(topic_path, json.dumps(data).encode())


def get_container_name(
    hostname: str = "asia.gcr.io",
    image: str = CRYPTOFEED_WERKS,
    tag: Optional[str] = None,
) -> str:
    project_id = os.environ[PROJECT_ID]
    container_name = f"{hostname}/{project_id}/{image}"
    if tag:
        container_name += f":{tag}"
    return container_name

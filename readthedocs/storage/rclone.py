"""Wrapper around the rclone command."""

import os
import subprocess

import structlog

log = structlog.get_logger(__name__)


class RClone:

    remote_type = "local"
    rclone_bin = "rclone"
    default_options = [
        #  Number of file transfers to run in parallel.
        "--transfers=8",
        "--verbose",
    ]
    env_vars = {}

    def build_target(self, path):
        return f":{self.remote_type}:{path}"

    def execute(self, action, args, options=None):
        options = options or []
        command = [
            self.rclone_bin,
            action,
            *self.default_options,
            *options,
            "--",
            *args,
        ]
        env = os.environ.copy()
        # env = {}
        env.update(self.env_vars)
        log.info("Executing rclone command.", command=command)
        log.debug("env", env=env)
        result = subprocess.run(
            command,
            capture_output=True,
            env=env,
        )
        log.debug(
            "Result.",
            stdout=result.stdout.decode(),
            stderr=result.stderr.decode(),
            exit_code=result.returncode,
        )
        return result

    def sync(self, source, destination):
        # TODO: check if source can be a symlink.
        return self.execute("sync", args=[source, self.build_target(destination)])


class RCloneS3Remote(RClone):

    remote_type = "s3"

    def __init__(
        self,
        bucket_name,
        access_key_id,
        secret_acces_key,
        region,
        provider="AWS",
        acl=None,
        endpoint=None,
    ):
        super().__init__()
        # rclone S3 options passed as env vars.
        # https://rclone.org/s3/#standard-options.
        region = region or ""
        self.env_vars = {
            "RCLONE_S3_PROVIDER": provider,
            "RCLONE_S3_ACCESS_KEY_ID": access_key_id,
            "RCLONE_S3_SECRET_ACCESS_KEY": secret_acces_key,
            "RCLONE_S3_REGION": region,
            "RCLONE_S3_LOCATION_CONSTRAINT": region,
        }
        if acl:
            self.env_vars["RCLONE_S3_ACL"] = acl
        if endpoint:
            self.env_vars["RCLONE_S3_ENDPOINT"] = endpoint
        self.bucket_name = bucket_name

    def build_target(self, path):
        path = f"{self.bucket_name}/{path}"
        return super().build_target(path)

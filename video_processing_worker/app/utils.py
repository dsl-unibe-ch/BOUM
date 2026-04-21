import json
import logging
from dataclasses import dataclass
from os import environ
from pprint import pprint
from time import sleep

from paramiko.client import SSHClient
from paramiko.ed25519key import Ed25519Key

from app.config import Config


@dataclass
class Association:
    account: str
    cluster: str
    partition: str
    user: int
    id: int


@dataclass
class State:
    current: list[str]
    reason: str


@dataclass
class Job:
    job_id: int
    submit_line: str
    association: Association
    state: State


def connect_and_run(command: str) -> tuple[bytes, bytes]:
    with SSHClient() as ssh_client:
        ssh_key = Ed25519Key.from_private_key_file(Config.SSH_KEY_PATH, password=None)
        ssh_client.load_host_keys(Config.KNOWN_HOSTS_FILE)
        ssh_client.connect(
            Config.SLURM_HOST,
            username=Config.SLURM_USER,
            pkey=ssh_key,
            look_for_keys=False,
        )

        _, stdout, stderr = ssh_client.exec_command(command)

        # supposed to block until the command exits, used to make sure
        # that we get the final stdout and stderrr
        if exit_code := stdout.channel.recv_exit_status():
            raise Exception(
                f"Command exited with code {exit_code}: {stderr.read().decode()}"
            )

        stdout_str, stderr_str = stdout.read(), stderr.read()

    return stdout_str, stderr_str


def get_jobs() -> list[Job]:
    """
    Get all jobs (any status) for a given user.

    Notice that the argument IS NOT sanitized, using untrusted input
    may lead to arbitrary code execution.
    """

    stdout, _ = connect_and_run("sacct --json")

    jobs_json = json.loads(stdout.decode())

    return [
        Job(
            j["job_id"],
            j["submit_line"],
            Association(**j["association"]),
            State(**j["state"]),
        )
        for j in jobs_json["jobs"]
    ]


def run_job(gres: str, mem: int, ncpus: int, batch_file: str, args: list[str]) -> int:
    """
    Submit batch.

    The function arguments are directly passed passed to command line,
    DO NOT use this with untrusted data.
    """

    logging.info(
        f"Submitting SLURM job with gres={gres}, mem={mem}G, ncpus={ncpus}, batch_file={batch_file}"
    )

    id_, _ = connect_and_run(
        # f"sbatch --parsable --gres={gres} --mem={mem}G --cpus-per-task={ncpus} {batch_file} {' '.join(args)}"
        f"sbatch --parsable {batch_file} {' '.join(args)}"
    )

    return int(id_.decode().strip())

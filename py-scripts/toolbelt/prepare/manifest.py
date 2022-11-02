from distutils.command.config import config
from time import time
from typing import Callable, Dict, List, Tuple

import structlog

from toolbelt.client import GithubClient
from toolbelt.constants import INTERNAL_DIR, MAIN_DIR, ONBOARDING_DIR
from toolbelt.k8s import ManifestManager
from toolbelt.planet import Apv
from toolbelt.types import Network, RepoInfos

logger = structlog.get_logger(__name__)


def update_internal_manifests(
    github_client: GithubClient,
    repo_infos: RepoInfos,
    apv: Apv,
    branch: str,
):
    manager = ManifestManager(repo_infos, INTERNAL_DIR, apv=apv.raw)
    files = ["configmap-versions.yaml", "kustomization.yaml"]
    head = github_client.get_ref(f"heads/{branch}")
    new_branch = f"update-internal-manifests-{int(time())}"
    github_client.create_ref(f"refs/heads/{new_branch}", head["object"]["sha"])

    for index, manifest in enumerate(manager.replace_manifests(files)):
        path = f"9c-internal/{files[index]}"
        message = f"INTERNAL: update {files[index]}"
        _, response = github_client.get_content(path, branch)

        github_client.update_content(
            commit=response["sha"],
            path=path,
            branch=new_branch,
            content=manifest,
            message=message,
        )
        logger.info("Commit", path=path, repo=github_client.repo, branch=new_branch)

    github_client.create_pull(
        title=f"Update internal manifests [{new_branch}]",
        head=new_branch,
        base=branch,
        body=apv.raw,
        draft=False,
    )


def update_onboarding_manifests(
    github_client: GithubClient,
    repo_infos: RepoInfos,
    apv: Apv,
    branch: str,
):
    manager = ManifestManager(repo_infos, ONBOARDING_DIR, apv=apv.raw)

    configmap = ["configmap-versions.yaml"]
    kustomization = ["kustomization.yaml"]

    files = configmap + kustomization

    for index, manifest in enumerate(manager.replace_manifests(files)):
        path = f"9c-onboarding/{files[index]}"
        message = f"ONBOARDING: update {files[index]}"
        _, response = github_client.get_content(path, branch)

        github_client.update_content(
            commit=response["sha"],
            path=path,
            branch=branch,
            content=manifest,
            message=message,
        )
        logger.info("Commit", path=path, repo=github_client.repo, branch=branch)


def update_main_manifests(
    github_client: GithubClient,
    repo_infos: RepoInfos,
    apv: Apv,
    branch: str,
):
    manager = ManifestManager(repo_infos, MAIN_DIR, apv=apv.raw)
    configmap = ["configmap-versions.yaml"]
    explorer = ["explorer.yaml"]
    full_state = ["full-state.yaml"]
    snapshot_full = ["snapshot-full.yaml"]
    snapshot_partition_reset = ["snapshot-partition-reset.yaml"]
    snapshot_partition = ["snapshot-partition.yaml"]
    miners = [f"miner-{i}.yaml" for i in range(1, 5)]
    headlesses = [f"remote-headless-{i}.yaml" for i in range(1, 11)] + [
        "remote-headless-31.yaml",
        "remote-headless-99.yaml",
    ]
    seeds = [f"tcp-seed-deployment-{i}.yaml" for i in range(1, 4)] + [
        f"seed-deployment-{i}.yaml" for i in range(1, 4)
    ]
    data_provider = ["data-provider.yaml", "data-provider-db.yaml"]

    files = (
        configmap
        + miners
        + headlesses
        + explorer
        + full_state
        + snapshot_full
        + snapshot_partition_reset
        + snapshot_partition
        + seeds
        + data_provider
    )
    head = github_client.get_ref(f"heads/{branch}")
    new_branch = f"update-main-manifests-{int(time())}"
    github_client.create_ref(f"refs/heads/{new_branch}", head["object"]["sha"])

    for index, manifest in enumerate(manager.replace_manifests(files)):
        path = f"9c-main/{files[index]}"
        message = f"MAIN: update {files[index]}"
        _, response = github_client.get_content(path, new_branch)

        github_client.update_content(
            commit=response["sha"],
            path=path,
            branch=new_branch,
            content=manifest,
            message=message,
        )
        logger.info("Commit", path=path, repo=github_client.repo, branch=new_branch)

    update_onboarding_manifests(github_client, repo_infos, apv, new_branch)

    github_client.create_pull(
        title=f"Update main manifests [{new_branch}]",
        head=new_branch,
        base=branch,
        body=apv.raw,
        draft=False,
    )


MANIFESTS_UPDATER: Dict[
    Network,
    Callable[[GithubClient, RepoInfos, Apv, str], None],
] = {
    "internal": update_internal_manifests,
    "main": update_main_manifests,
}

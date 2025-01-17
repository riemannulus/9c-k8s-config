from typing import Optional

import typer

from toolbelt.utils.typer import network_arg

from .prepare import prepare_release

prepare_app = typer.Typer()


@prepare_app.command()
def release(
    network: str = network_arg,
    rc_number: int = typer.Argument(...),
    deploy_number: int = typer.Argument(...),
    launcher_commit: Optional[str] = None,
    player_commit: Optional[str] = None,
    slack_channel: Optional[str] = None,
):
    """
    Run internal release script
    """

    return prepare_release(
        network,  # type:ignore
        rc_number,
        deploy_number,
        launcher_commit=launcher_commit,
        player_commit=player_commit,
        slack_channel=slack_channel,
    )


__all__ = ["prepare_app"]

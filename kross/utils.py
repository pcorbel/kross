import os

import click
import subprocess32 as subprocess


def get_std():
    if os.getenv("KROSS_VERBOSE") in ["true", "True"]:
        return None
    return subprocess.PIPE


def echo(message, verbose_only=False, new_line=True):
    if verbose_only:
        if os.getenv("KROSS_VERBOSE") in ["true", "True"]:
            click.echo(message, nl=new_line)
    else:
        click.echo(message, nl=new_line)

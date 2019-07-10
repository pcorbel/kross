# pylint: disable=missing-docstring

import click

from kross.base_build import BaseBuild
from kross.base_push import BasePush
from kross.builder import Builder
from kross.qemu_build import QEMUBuild
from kross.qemu_push import QEMUPush


@click.group()
def main():
    pass


@main.command()
def init():
    builder = Builder()
    builder.init()


@main.command(context_settings={"ignore_unknown_options": True})
@click.argument("build_args", nargs=-1)
def build(build_args):
    click.echo("Detecting configuration for base build...")
    base_build = BaseBuild(build_args=build_args)
    click.echo(base_build)

    for qemu_arch in base_build.qemu_archs:
        qemu_build = QEMUBuild(
            build_args=build_args,
            base_build=base_build,
            arch=qemu_arch.get("name"),
            qemu_arch=qemu_arch.get("qemu"),
        )
        # fmt: off
        click.echo("""
Starting QEMU build {} {}""".format(qemu_arch.get("name"), qemu_build))
        # fmt: on
        try:
            qemu_build.build()
        except click.ClickException as e:
            click.echo("Error: {}".format(e))
            qemu_build.clean_up()
            continue
    # fmt: off
    click.echo("""
kross build complete.""")
    # fmt: on


@main.command(context_settings={"ignore_unknown_options": True})
@click.argument("push_args", nargs=-1)
def push(push_args):
    click.echo("Detecting configuration for base push...")
    base_push = BasePush(push_args=push_args)
    click.echo(base_push)
    base_push.remove_manifest_directory()

    for qemu_arch in base_push.qemu_archs:
        qemu_push = QEMUPush(push_args=push_args, base_push=base_push, arch=qemu_arch)

        # fmt: off
        click.echo("""
Starting QEMU push {} {}""".format(qemu_arch.get("name"), qemu_push))
        # fmt: on
        try:
            qemu_push.push()
        except click.ClickException as e:
            click.echo("Error: {}".format(e))
            continue
    # fmt: off
    click.echo("""
Pushing manifest""")
    # fmt: on
    base_push.exec_push_manifest()

    # fmt: off
    click.echo("""
kross push complete.""")
    # fmt: on


cli = click.CommandCollection(sources=[main])

if __name__ == "__main__":
    cli()

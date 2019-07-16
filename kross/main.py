import click

from kross.base_build import BaseBuild
from kross.base_push import BasePush
from kross.builder import Builder
from kross.qemu_build import QEMUBuild
from kross.qemu_push import QEMUPush
from kross.utils import echo


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
    echo("Detecting configuration for base build...", verbose_only=True)
    base_build = BaseBuild(build_args=build_args)
    echo(base_build, verbose_only=True)

    for qemu_arch in base_build.qemu_archs:
        qemu_build = QEMUBuild(
            build_args=build_args,
            base_build=base_build,
            arch=qemu_arch.get("name"),
            qemu_arch=qemu_arch.get("qemu"),
        )
        echo(
            "kross building for arch {}... ".format(qemu_arch.get("name")),
            new_line=False,
        )
        echo(qemu_build, verbose_only=True)
        try:
            qemu_build.build()
            echo("Done")
        except click.ClickException as error:
            echo("Error: {}".format(error))
            qemu_build.clean_up()
            continue
    echo("kross build complete.")


@main.command(context_settings={"ignore_unknown_options": True})
@click.argument("push_args", nargs=-1)
def push(push_args):
    echo("Detecting configuration for base push...", verbose_only=True)
    base_push = BasePush(push_args=push_args)
    echo(base_push, verbose_only=True)
    base_push.remove_manifest_directory()

    for qemu_arch in base_push.qemu_archs:
        qemu_push = QEMUPush(push_args=push_args, base_push=base_push, arch=qemu_arch)

        echo(
            "kross pushing for arch {}... ".format(qemu_arch.get("name")),
            new_line=False,
        )
        echo(qemu_push, verbose_only=True)
        try:
            qemu_push.push()
            echo("Done")
        except click.ClickException as error:
            echo("Error: {}".format(error))
            continue
    echo("kross pushing manifest list.")
    base_push.exec_push_manifest()
    echo("kross push complete.")


cli = click.CommandCollection(sources=[main])  # pylint: disable=invalid-name

if __name__ == "__main__":
    cli()

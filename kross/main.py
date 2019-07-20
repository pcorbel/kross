from multiprocessing import Process

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
    qemu_builds = list()
    processes = list()

    # Generate builds list
    for qemu_arch in base_build.qemu_archs:
        qemu_builds.append(
            QEMUBuild(
                build_args=build_args,
                base_build=base_build,
                arch=qemu_arch.get("name"),
                qemu_arch=qemu_arch.get("qemu"),
            )
        )

    # Parallelize builds
    for qemu_build in qemu_builds:
        echo("kross building for arch {}... ".format(qemu_build.arch))
        echo(qemu_build, verbose_only=True)
        process = Process(target=qemu_build.build)
        processes.append(process)
        process.start()

    # Wait for builds to finish
    for process in processes:
        process.join()

    # Clean up
    for qemu_build in qemu_builds:
        qemu_build.clean_up()

    echo("kross build complete.")


@main.command(context_settings={"ignore_unknown_options": True})
@click.argument("push_args", nargs=-1)
def push(push_args):
    echo("Detecting configuration for base push...", verbose_only=True)
    base_push = BasePush(push_args=push_args)
    echo(base_push, verbose_only=True)
    base_push.remove_manifest_directory()
    qemu_pushes = list()
    processes = list()

    # Generate pushes list
    for qemu_arch in base_push.qemu_archs:
        qemu_pushes.append(
            QEMUPush(push_args=push_args, base_push=base_push, arch=qemu_arch)
        )

    # Parallelize pushes
    for qemu_push in qemu_pushes:
        echo("kross pushing for arch {}... ".format(qemu_push.arch.get("name")))
        echo(qemu_push, verbose_only=True)
        process = Process(target=qemu_push.push)
        processes.append(process)
        process.start()

    # Wait for pushes to finish
    for process in processes:
        process.join()

    # Push manifest list
    echo("kross pushing manifest list.")
    base_push.exec_push_manifest()
    echo("kross push complete.")


cli = click.CommandCollection(sources=[main])  # pylint: disable=invalid-name

if __name__ == "__main__":
    cli()

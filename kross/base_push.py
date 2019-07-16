import os
import re
import shutil

import attr
import click
import subprocess32 as subprocess
import yaml

from kross.utils import echo, get_std


@attr.s
class BasePush(object):
    push_args = attr.ib(type=tuple)
    registry_target = attr.ib()
    manifest_directory = attr.ib()
    qemu_archs = attr.ib()
    push_manifest_cmd = attr.ib()

    @registry_target.default
    def default_registry_target(self):
        registry_target = self.push_args[-1]
        if re.match(r"(.*?)/(.*?):(.*)", registry_target):
            return registry_target
        # fmt: off
        raise click.ClickException("""Cannot find target image.
Please pass it in the <repository/image_name:image_tag> format.""")
        # fmt: on

    @manifest_directory.default
    def default_manifest_directory(self):
        manifest_directory = "{}/.docker/manifests/docker.io_{}".format(
            os.path.expanduser("~"),
            self.registry_target.replace("/", "_").replace(":", "-"),
        )
        return manifest_directory

    @qemu_archs.default
    def default_qemu_archs(self):  # pylint: disable=no-self-use
        arch_file = os.path.dirname(os.path.abspath(__file__)) + "/archs.yaml"
        with click.open_file(arch_file, "r") as stream:
            archs = yaml.load(stream=stream, Loader=yaml.UnsafeLoader)
        return archs.get("archs")

    @push_manifest_cmd.default
    def default_push_manifest_cmd(self):
        push_manifest_cmd = "docker manifest push {}".format(self.registry_target)
        return push_manifest_cmd

    def remove_manifest_directory(self):
        echo("""Purging manifest directory.""", verbose_only=True)
        shutil.rmtree(path=self.manifest_directory, ignore_errors=True)

    def exec_push_manifest(self):
        try:
            subprocess.run(
                self.push_manifest_cmd.split(),
                check=True,
                stdout=get_std(),
                stderr=get_std(),
            )
        except subprocess.CalledProcessError:
            raise click.ClickException("Cannot push manifest list to registry.")

    def __str__(self):
        # fmt: off
        result = """
base_push:
  - registry_target:    {self.registry_target}
  - manifest_directory: {self.manifest_directory}
  - push_manifest_cmd:  {self.push_manifest_cmd}
  - push_args:          """.format(**locals())
        for push_arg in self.push_args:
            result += "{} ".format(push_arg)
        result += """
  - qemu_archs:         """
        for arch in self.qemu_archs:
            result += "{name} ".format(**arch)
        result += "\n"
        return result
        # fmt: on

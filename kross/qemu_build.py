import os
import re
import shutil

import attr
import click
import subprocess32 as subprocess

from kross.utils import echo, get_std


@attr.s
class QEMUBuild(object):
    build_args = attr.ib(type=tuple)
    base_build = attr.ib()
    arch = attr.ib(type=str)
    qemu_arch = attr.ib(type=str)

    qemu_registry_target = attr.ib()
    qemu_dockerfile = attr.ib()
    qemu_image = attr.ib()
    qemu_tarball = attr.ib()

    build_cmd = attr.ib()

    def build(self):
        self.pull_qemu_image()
        self.generate_qemu_dockerfile()
        self.import_qemu_tarball_in_context()
        self.exec_build()
        self.clean_up()

    def clean_up(self):
        echo("""Cleaning up build {}.""".format(self.arch), verbose_only=True)
        self.remove_qemu_dockerfile()
        self.remove_qemu_tarball()

    @qemu_registry_target.default
    def default_qemu_registry_target(self):
        qemu_registry_target = "{}-{}".format(
            self.base_build.registry_target, self.arch
        )
        return qemu_registry_target

    @qemu_dockerfile.default
    def default_qemu_dockerfile(self):
        qemu_dockerfile = "{}.{}".format(self.base_build.dockerfile, self.arch)
        return qemu_dockerfile

    @qemu_image.default
    def default_qemu_image(self):
        match = re.match(r"^((.*?)/)?(.*?)(:(.*?))?$", self.base_build.image)
        name = match.group(3)
        tag = match.group(5) if match.group(5) is not None else "latest"
        qemu_image = "{}/{}:{}".format(self.arch, name, tag)
        return qemu_image

    @qemu_tarball.default
    def default_qemu_tarball(self):
        qemu_tarball = "{}/qemu/x86_64_qemu-{}-static.tar.gz".format(
            os.path.dirname(os.path.abspath(__file__)), self.qemu_arch
        )
        return qemu_tarball

    @build_cmd.default
    def default_build_cmd(self):
        # Initialize the docker build command
        build_cmd = "docker build "

        # Add all args but last one (path)
        for arg in self.build_args[:-1]:
            build_cmd += arg + " "

        # Normalize command by ensuring -f dockerfile is present
        if not ("-f" in build_cmd or "--file" in build_cmd):
            build_cmd += "-f {} ".format(self.base_build.dockerfile)

        # Add path to command
        build_cmd += self.build_args[-1]

        # Update registry_target
        build_cmd = build_cmd.replace(
            self.base_build.registry_target, self.qemu_registry_target
        )

        # Update dockerfile
        build_cmd = build_cmd.replace(self.base_build.dockerfile, self.qemu_dockerfile)

        return build_cmd

    def pull_qemu_image(self):
        try:
            subprocess.run(
                ["docker", "pull", self.qemu_image],
                check=True,
                stdout=get_std(),
                stderr=get_std(),
            )
        except subprocess.CalledProcessError:
            # fmt: off
            raise click.ClickException("""Cannot pull QEMU base image {}.
Passing.""".format(self.qemu_image))
            # fmt: on

    def generate_qemu_dockerfile(self):
        # Copy base dockerfile
        shutil.copyfile(self.base_build.dockerfile, self.qemu_dockerfile)

        # Update image
        with click.open_file(self.qemu_dockerfile, "r+") as file:
            updated = re.sub(self.base_build.image, self.qemu_image, file.read())
            file.seek(0)
            file.write(updated)

        # Inject ADD qemu clause after FROM qemu_image clause
        with click.open_file(self.qemu_dockerfile, "r+") as file:
            is_next = False
            updated = ""
            # Iterate over lines in dockerfile to find FROM qemu_image clause
            for line in file:
                if is_next:
                    # Inject ADD clause
                    line = "ADD x86_64_qemu-{}-static.tar.gz /usr/bin/\n{}".format(
                        self.qemu_arch, line
                    )
                    is_next = False
                if re.match(r"^FROM\s+" + self.qemu_image, line):
                    is_next = True
                updated += line
            file.seek(0)
            file.write(updated)

    def import_qemu_tarball_in_context(self):
        shutil.copy(self.qemu_tarball, self.base_build.context)

    def exec_build(self):
        try:
            subprocess.run(
                self.build_cmd.split(), check=True, stdout=get_std(), stderr=get_std()
            )
        except subprocess.CalledProcessError:
            # fmt: off
            raise click.ClickException("""Cannot build image for architecture {}.
Passing.""".format(self.arch))
            # fmt: on

    def remove_qemu_dockerfile(self):
        try:
            os.remove(self.qemu_dockerfile)
        except OSError:
            pass

    def remove_qemu_tarball(self):
        try:
            os.remove(
                "{}/x86_64_qemu-{}-static.tar.gz".format(
                    self.base_build.context, self.qemu_arch
                )
            )
        except OSError:
            pass

    def __str__(self):
        # fmt: off
        result = """
qemu_build:
  - registry_target: {self.qemu_registry_target}
  - dockerfile: {self.qemu_dockerfile}
  - image: {self.qemu_image}
  - qemu_arch: {self.qemu_arch}
  - qemu_tarball: {self.qemu_tarball}
  - build_cmd: {self.build_cmd}
""".format(**locals())
        return result
        # fmt: on

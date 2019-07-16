import json
import os
import platform

import attr
import click
import subprocess32 as subprocess

from kross.utils import echo, get_std


@attr.s
class Builder(object):
    def init(self):
        echo("Initializing kross. You may be prompted for sudo password")
        self.check_builder()
        self.login_registry()
        self.register_binfmt_misc()
        self.check_manifest_cmd()
        echo("kross initialization complete")

    @staticmethod
    def check_builder():
        arch = platform.machine()
        if not arch == "x86_64":
            # fmt: off
            raise click.ClickException("""Host is not x86_64 but {}.
Cannot run kross on this machine.""".format(arch))
            # fmt: on

    @staticmethod
    def login_registry():
        try:
            subprocess.run(
                ["docker", "login"], check=True, stdout=get_std(), stderr=get_std()
            )
        except subprocess.CalledProcessError:
            # fmt: off
            raise click.ClickException("""Docker registry is not accessible.
Please login with `docker login` command.""")
            # fmt: on

    @staticmethod
    def register_binfmt_misc():
        try:
            subprocess.run(
                [
                    "sudo",
                    "docker",
                    "run",
                    "--rm",
                    "--privileged",
                    "multiarch/qemu-user-static:register",
                ],
                check=True,
                stdout=get_std(),
                stderr=get_std(),
            )
        except subprocess.CalledProcessError:
            # fmt: off
            raise click.ClickException("""Could not register binfmt_misc.
Please register it with \
`sudo docker run --rm --privileged multiarch/qemu-user-static:register` command.""")
            # fmt: on

    @staticmethod
    def check_manifest_cmd():
        try:
            subprocess.run(
                ["docker", "manifest"], check=True, stdout=get_std(), stderr=get_std()
            )
        except subprocess.CalledProcessError:
            docker_config = "{}/{}".format(
                os.path.expanduser("~"), ".docker/config.json"
            )
            with click.open_file(docker_config, "r+") as file:
                config = json.load(file)
                config.update({"experimental": "enabled"})
                file.seek(0)
                json.dump(config, file)

import attr
import click
import subprocess32 as subprocess

from kross.utils import get_std


@attr.s
class QEMUPush(object):
    push_args = attr.ib(type=tuple)
    base_push = attr.ib()
    arch = attr.ib()

    qemu_registry_target = attr.ib()

    push_cmd = attr.ib()
    amend_cmd = attr.ib()
    annotate_cmd = attr.ib()

    def push(self):
        self.exec_push()
        self.exec_amend()
        self.exec_annotate()

    @qemu_registry_target.default
    def default_qemu_registry_target(self):
        qemu_registry_target = "{}-{}".format(
            self.base_push.registry_target, self.arch.get("name")
        )
        return qemu_registry_target

    @push_cmd.default
    def default_push_cmd(self):
        push_cmd = "docker push {}".format(self.qemu_registry_target)
        return push_cmd

    @amend_cmd.default
    def default_amend_cmd(self):
        amend_cmd = "docker manifest create --amend {} {}".format(
            self.base_push.registry_target, self.qemu_registry_target
        )
        return amend_cmd

    @annotate_cmd.default
    def default_annotate_cmd(self):
        # Initialize the docker manifest command
        annotate_cmd = "docker manifest annotate {} {}".format(
            self.base_push.registry_target, self.qemu_registry_target
        )

        # Add os anotation if available
        if self.arch.get("os"):
            annotate_cmd += " --os {}".format(self.arch.get("os"))

        # Add arch anotation if available
        if self.arch.get("arch"):
            annotate_cmd += " --arch {}".format(self.arch.get("arch"))

        # Add variant anotation if available
        if self.arch.get("variant"):
            annotate_cmd += " --variant {}".format(self.arch.get("variant"))

        return annotate_cmd

    def exec_push(self):
        try:
            subprocess.run(
                self.push_cmd.split(), check=True, stdout=get_std(), stderr=get_std()
            )
        except subprocess.CalledProcessError:
            # fmt: off
            raise click.ClickException("""Cannot push image {} to registry.
Passing.""".format(self.qemu_registry_target))
            # fmt: on

    def exec_amend(self):
        try:
            subprocess.run(
                self.amend_cmd.split(), check=True, stdout=get_std(), stderr=get_std()
            )
        except subprocess.CalledProcessError:
            # fmt: off
            raise click.ClickException("""Cannot amend image {} to manifest.
Passing.""".format(self.qemu_registry_target))
            # fmt: on

    def exec_annotate(self):
        try:
            subprocess.run(
                self.annotate_cmd.split(),
                check=True,
                stdout=get_std(),
                stderr=get_std(),
            )
        except subprocess.CalledProcessError:
            # fmt: off
            raise click.ClickException("""Cannot annotate image {} to manifest.
Passing.""".format(self.qemu_registry_target))
            # fmt: on

    def __str__(self):
        # fmt: off
        result = """
qemu_push:
  - arch: {arch_name}
  - qemu_registry_target: {self.qemu_registry_target}
  - push_cmd: {self.push_cmd}
  - amend_cmd: {self.amend_cmd}
  - annotate_cmd: {self.annotate_cmd}
""".format(arch_name=self.arch.get("name"), **locals())
        return result
        # fmt: on

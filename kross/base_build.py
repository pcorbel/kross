import os
import re

import attr
import click
import yaml


@attr.s
class BaseBuild(object):
    build_args = attr.ib(type=tuple)
    registry_target = attr.ib()
    context = attr.ib()
    dockerfile = attr.ib()
    manifest_directory = attr.ib()
    image = attr.ib()
    qemu_archs = attr.ib()

    @registry_target.default
    def default_registry_target(self):
        is_next = False
        for arg in self.build_args:
            if arg in ("-t", "--tag"):
                is_next = True
                continue
            if is_next and re.match(r"(.*?)/(.*?):(.*)", arg):
                return arg
        # fmt: off
        raise click.ClickException("""Cannot find target image.
Please pass it in the -t/--tag <repository/image_name:image_tag> format.""")
        # fmt: on

    @context.default
    def default_context(self):
        context = str.rstrip(str(self.build_args[-1]), "/")
        if os.path.exists(context):
            return context
        # fmt: off
        raise click.ClickException("""Cannot find docker context.
Please make sure {} exist.""".format(context))
        # fmt: on

    @dockerfile.default
    def default_dockerfile(self):
        # In case dockerfile is not explicitely given by the user
        if not ("-f" in self.build_args or "--file" in self.build_args):
            path = str.rstrip(self.context, "/") + "/Dockerfile"
        # Else, get it from build_args
        else:
            is_next = False
            for arg in self.build_args:
                if arg in ("-f", "--file"):
                    is_next = True
                    continue
                if is_next:
                    path = arg
                    break

        # Get absolute path and ensure file exists
        dockerfile = os.path.abspath(path)
        if os.path.isfile(dockerfile):
            return dockerfile
        # fmt: off
        raise click.ClickException("""Cannot find Dockerfile.
Please pass it in the -f/--file path/to/dockerfile format \
or verify it is present in context.""")
        # fmt: on

    @image.default
    def default_image(self):
        # Iterate over FROM clause in Dockerfile to only get the last one
        with click.open_file(self.dockerfile, "r") as file:
            for line in file:
                match = re.match(r"^FROM\s+(.*?)\s+", line)
                if match:
                    image = match.group(1)
        if image:
            return image
        # fmt: off
        raise click.ClickException("""Cannot find base image.
Please make sure to have a 'FROM image' clause in your Dockerfile.""")
        # fmt: on

    @manifest_directory.default
    def default_manifest_directory(self):
        manifest_directory = "{}/.docker/manifests/docker.io_{}".format(
            os.path.expanduser("~"), self.registry_target.replace("/", "_")
        )
        return manifest_directory

    @qemu_archs.default
    def default_qemu_archs(self):  # pylint: disable=no-self-use
        arch_file = os.path.dirname(os.path.abspath(__file__)) + "/archs.yaml"
        with click.open_file(arch_file, "r") as stream:
            archs = yaml.load(stream=stream, Loader=yaml.UnsafeLoader)
        return archs.get("archs")

    def __str__(self):
        # fmt: off
        result = """
base_build:
  - registry_target:    {self.registry_target}
  - context:            {self.context}
  - dockerfile:         {self.dockerfile}
  - manifest_directory: {self.manifest_directory}
  - image:              {self.image}
  - build_args:         """.format(**locals())
        for build_arg in self.build_args:
            result += "{} ".format(build_arg)
        result += """
  - qemu_archs:         """
        for arch in self.qemu_archs:
            result += "{name} ".format(**arch)
        result += "\n"
        return result
        # fmt: on

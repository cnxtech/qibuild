## Copyright (C) 2011 Aldebaran Robotics

""" This package contains the Toolchain and the Package
class

How does it work?

 - Create a Toolchain with a name ("linux" for instance)
    ~/.local/share/qi/toolchains/linux/
and
    ~/.cache/qi/toolchains/linux/packages/
are created.

A toolchain file is created in
~/.local/share/qi/toolchains/linux/toolchain.cmake

qitoolchain build configuration is updated to reflect
there is a toolchain called "linux"

 - Add the foo package:
The foo archive is copied in the cache:
~/.cache/qi/toolchains/linux/packages/foo.tar.gz

The foo package is extraced to the toolchain:
~/.local/share/qi/toolchain/linux/foo/{lib,include,cmake}

The toolchain.cmake in ~/.local/share/qi/toolchains/linux/toolchain.cmake
is updated to contain:

    list(APPEND CMAKE_PREFIX_PATH "~/.local/share/qi/toolchains/linux/foo")

qitoolchain build configuration is updated to
reflect the fact that the "linux" toolchain now provides
the "foo" package.

 - Build a Toc object with the toolchain name "linux", when building a project,
add the -DCMAKE_TOOLCHAIN_FILE parameter

"""


import os
import sys
import logging

import qitools

LOGGER = logging.getLogger(__name__)


class Package:
    """A package is a set of binaries, headers and cmake files
    (a bit like a -dev debian package)
    It has a name and may depend on other packages.

    """
    def __init__(self, name):
        self.name = name
        self.depends = list()

    def __str__(self):
        res = "Package %s"  % self.name
        if self.depends:
            res += " (depends on : %s)" %  " ".join(self.depends)
        return res


def get_tc_config_path():
    """ Return a suitable config path

    """
    # FIXME: deal with non-UNIX systems
    config_path = os.path.expanduser("~/.config/qi/toolchain.cfg")
    return config_path

def get_tc_path(toolchain_name):
    """ Return a suitable path to extract the packages

    """
    if sys.platform.startswith("win"):
        # > Vista:
        if os.environ.get("LOCALAPPDATA"):
            res = os.path.expandvars(r"%LOCALAPPDATA%\qi")
        else:
            res = os.path.expandvars(r"%APPDATA%\qi")
    else:
        res = os.path.expanduser("~/.local/share/qi")
    res = os.path.join(res, "toolchains", toolchain_name)
    qitools.sh.mkdir(res, recursive=True)
    return res

def get_tc_cache(toolchain_name):
    """ Return the path where to store packages

    """
    # FIXME: deal with non-UNIX systems
    cache_path = os.path.expanduser("~/.cache/qi")
    return os.path.join(cache_path, "toolchains", toolchain_name)


class Toolchain(object):
    """ The Toolchain class has a name and a list of packages.

    """
    def __init__(self, name, path=""):
        self.name = name
        if path:
            self.path = path
        else:
            self.path = get_tc_path(self.name)
        self.toolchain_file = os.path.join(self.path, "toolchain-%s.cmake" % self.name)
        self.configstore = qitools.configstore.ConfigStore()
        self.configstore.read(get_tc_config_path())
        self.packages = list()
        self._load_config()
        LOGGER.debug("Created a new toolchain:\n%s", str(self))

    def __str__(self):
        res  = "Toolchain:\n"
        res += "  name: %s\n" % self.name
        res += "  packages:\n" + "\n".join([" " * 4  + str(x) for x in self.packages])
        return res


    def get(self, package_name):
        """Return path to a package
        """
        known_names = [p.name for p in self.packages]
        if package_name not in known_names:
            raise Exception("No such package: %s" % package_name)
        package_path = os.path.join(self.path, package_name)
        return package_path

    def add_package(self, name, path):
        """Add a package given its name and its path

        """
        LOGGER.info("Adding package %s",name)
        with qitools.sh.TempDir() as tmp:
            extracted = qitools.archive.extract(path, tmp)
            # Rename package once it is extracted:
            dest = os.path.join(self.path, name)
            if os.path.exists(dest):
                qitools.sh.rm(dest)
            qitools.sh.mv(extracted, dest)
        self.packages.append(Package(name))
        self._update_tc_provides(name)
        self._update_toolchain_file(name)


    def _update_tc_provides(self, package_name):
        """When a package has been added, update the toolchain
        configuration

        """
        provided = self.configstore.get("toolchain", self.name, "provide",
            default="").split()
        LOGGER.debug("[%s] toolchain: new package %s providing %s",
                          self.name,
                          package_name,
                          ",".join(provided))
        if package_name in provided:
            return

        provided.append(package_name)
        to_write = " ".join(provided)
        qitools.configstore.update_config(get_tc_config_path(),
            "toolchain", self.name, "provide", to_write)

    def _update_toolchain_file(self, package_name):
        """When a package has been added, update the toolchain.cmake
        file

        """
        lines = list()
        if os.path.exists(self.toolchain_file):
            with open(self.toolchain_file, "r") as fp:
                lines = fp.readlines()

        package_path = self.get(package_name)
        qitools.sh.to_posix_path(package_path)
        lines.append('list(APPEND CMAKE_PREFIX_PATH "%s")\n' % package_path)

        with open(self.toolchain_file, "w") as fp:
            lines = fp.writelines(lines)


    def _load_config(self):
        """ Re-build self.packages list using the configuration file

        Called each time someone uses self.packages
        """
        provided = self.configstore.get("toolchain", self.name, "provide")
        self.packages = list()
        if not provided:
            return
        for package_name in provided.split():
            deps = self.configstore.get("package", package_name, "depends",
                default="")
            names = deps.split()
            package = Package(package_name)
            package.depends = names
            self.packages.append(package)

def create(toolchain_name):
    """Create a new toolchain given its name.
    """
    path = get_tc_path(toolchain_name)
    if os.path.exists(path):
        raise Exception("%s alread exist.\n"
            "Please choose another toolchain name" % path)
    LOGGER.info("Toolchain initialized in: %s", path)


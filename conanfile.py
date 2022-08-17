import os

from pathlib import Path

from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools import files
from conan import ConanFile
from conan.tools.layout import basic_layout
from conans import tools

required_conan_version = ">=1.46.2"

class PySavitarConan(ConanFile):
    name = "pysavitar"
    license = "LGPL-3.0"
    author = "Ultimaker B.V."
    url = "https://github.com/Ultimaker/pySavitar"
    description = "pySavitar is a c++ implementation of 3mf loading with SIP python bindings"
    topics = ("conan", "cura", "3mf", "c++")
    settings = "os", "compiler", "build_type", "arch"
    revision_mode = "scm"
    exports = "LICENSE*"

    python_requires = "umbase/0.1.5@ultimaker/testing", "pyprojecttoolchain/0.1.0@ultimaker/testing", "sipbuildtool/0.2.0@ultimaker/testing"
    python_requires_extend = "umbase.UMBaseConanfile"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "py_build_requires": ["ANY"],
        "py_build_backend": ["ANY"],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "py_build_requires": '"sip >=6, <7", "setuptools>=40.8.0", "wheel"',
        "py_build_backend": "sipbuild.api",
    }
    scm = {
        "type": "git",
        "subfolder": ".",
        "url": "auto",
        "revision": "auto"
    }

    def requirements(self):
        for req in self._um_data()["requirements"]:
            self.requires(req)

    def config_options(self):
        if self.options.shared and self.settings.compiler == "Visual Studio":
            del self.options.fPIC

    def configure(self):
        self.options["savitar"].shared = self.options.shared
        self.options["cpython"].shared = True

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            tools.check_min_cppstd(self, 17)

    def generate(self):
        pp = self.python_requires["pyprojecttoolchain"].module.PyProjectToolchain(self)
        pp.blocks["tool_sip_project"].values["sip_files_dir"] = Path("python").as_posix()
        pp.blocks.remove("extra_sources")
        pp.generate()

    def layout(self):
        basic_layout(self)

        if self.settings.os in ["Linux", "FreeBSD", "Macos"]:
            self.cpp.package.system_libs = ["pthread"]

    def build(self):
        sip = self.python_requires["sipbuildtool"].module.SipBuildTool(self)
        sip.configure()
        sip.build()

    def package(self):
        packager = files.AutoPackager(self)
        packager.patterns.build.lib = ["*.so", "*.so.*", "*.a", "*.lib", "*.dylib", "*.pyd", "*.pyi"]
        packager.run()

        files.files.rmdir(self, os.path.join(self.package_folder, "lib", "pySavitar"))

    def package_info(self):
        if self.in_local_cache:
            self.runenv_info.append_path("PYTHONPATH", os.path.join(self.package_folder, "site-packages"))
        else:
            self.runenv_info.append_path("PYTHONPATH", os.path.join(self.build_folder, "site-packages"))

import os

from pathlib import Path

from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools import files
from conan import ConanFile
from conans import tools

required_conan_version = ">=1.48.0"

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

    python_requires = "umbase/[>=0.1.6]@ultimaker/stable", "pyprojecttoolchain/[>=0.1.5]@ultimaker/stable", "sipbuildtool/[>=0.2.2]@ultimaker/stable"
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
        self.requires("umbase/0.1.6@ultimaker/stable")  # required for the CMake build modules
        self.requires("sipbuildtool/0.2.2@ultimaker/stable")  # required for the CMake build modules
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
        deps = CMakeDeps(self)
        deps.generate()

        pp = self.python_requires["pyprojecttoolchain"].module.PyProjectToolchain(self)
        pp.blocks["tool_sip_project"].values["sip_files_dir"] = Path("python").as_posix()
        pp.blocks["tool_sip_bindings"].values["name"] = "pySavitar"
        pp.blocks["tool_sip_metadata"].values["name"] = "pySavitar"
        pp.blocks.remove("extra_sources")
        pp.generate()

        tc = CMakeToolchain(self)
        tc.variables["Python_EXECUTABLE"] = self.deps_user_info["cpython"].python.replace("\\", "/")
        tc.variables["Python_USE_STATIC_LIBS"] = not self.options["cpython"].shared
        tc.variables["Python_ROOT_DIR"] = self.deps_cpp_info["cpython"].rootpath.replace("\\", "/")
        tc.variables["Python_FIND_FRAMEWORK"] = "NEVER"
        tc.variables["Python_FIND_REGISTRY"] = "NEVER"
        tc.variables["Python_FIND_IMPLEMENTATIONS"] = "CPython"
        tc.variables["Python_FIND_STRATEGY"] = "LOCATION"
        tc.variables["Python_SITEARCH"] = "site-packages"

        if self.settings.compiler == "Visual Studio":
            tc.blocks["generic_system"].values["generator_platform"] = None
            tc.blocks["generic_system"].values["toolset"] = None
        tc.generate()

        # Generate the Source code from SIP
        sip = self.python_requires["sipbuildtool"].module.SipBuildTool(self)
        sip.configure()
        sip.build()

    def layout(self):
        cmake_layout(self)

        if self.settings.os in ["Linux", "FreeBSD", "Macos"]:
            self.cpp.package.system_libs = ["pthread"]

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        packager = files.AutoPackager(self)
        packager.patterns.build.lib = ["*.so", "*.so.*", "*.a", "*.lib", "*.dylib", "*.pyd"]
        packager.run()

        self.copy("*.pyi", src = os.path.join(self.build_folder, "pySavitar"), dst = os.path.join(self.package_folder, "lib"), keep_path = False)

    def package_info(self):
        if self.in_local_cache:
            self.runenv_info.append_path("PYTHONPATH", os.path.join(self.package_folder, "lib"))
        else:
            self.runenv_info.append_path("PYTHONPATH", self.build_folder)

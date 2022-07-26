import shutil
from io import StringIO
from pathlib import Path

from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.env import VirtualRunEnv
from conan.errors import ConanException


class PySavitarTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "VirtualRunEnv"

    def generate(self):
        venv = VirtualRunEnv(self)
        venv.generate()

    def build(self):
        if not cross_building(self):
            shutil.copy(Path(self.source_folder).joinpath("test.py"), Path(self.build_folder).joinpath("test.py"))

    def imports(self):
        if self.settings.os == "Windows" and not cross_building(self):
            self.copy("*.dll", dst=".", src="@bindirs")
            self.copy("*.pyd", dst=".", src="@libdirs")

    def test(self):
        if not cross_building(self):
            test_pysavitar = StringIO()

            try:
                self.run("python test.py", env="conanrun", output=test_pysavitar)
            except Exception:
                print("Test Failed to run: ", test_pysavitar.getvalue())
                raise ConanException("pySavitar wasn't built correctly")

            if "True" not in test_pysavitar.getvalue():
                raise ConanException("pySavitar wasn't built correctly")

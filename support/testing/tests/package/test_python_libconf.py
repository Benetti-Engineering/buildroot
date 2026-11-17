from tests.package.test_python import TestPythonPackageBase


class TestPythonPy3Libconf(TestPythonPackageBase):
    __test__ = True
    config = TestPythonPackageBase.config + \
        """
        BR2_PACKAGE_PYTHON3=y
        BR2_PACKAGE_PYTHON_LIBCONF=y
        """
    sample_scripts = ["tests/package/sample_python_libconf.py"]
    timeout = 30

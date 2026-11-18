import os

import infra.basetest


class TestDotnetRuntimeBase(infra.basetest.BRTest):
    # The .NET runtime needs ARMv7-A with the hard-float ABI on ARM,
    # so infra.basetest.BASIC_TOOLCHAIN_CONFIG can't be used.
    config = \
        """
        BR2_arm=y
        BR2_cortex_a9=y
        BR2_ARM_ENABLE_NEON=y
        BR2_ARM_ENABLE_VFP=y
        BR2_TOOLCHAIN_EXTERNAL=y
        BR2_TARGET_GENERIC_GETTY_PORT="ttyAMA0"
        BR2_PACKAGE_DOTNET_RUNTIME=y
        BR2_PACKAGE_ICU=y
        BR2_PACKAGE_OPENSSL=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def check_runtime(self, version):
        img = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv7",
                           kernel="builtin",
                           options=["-m", "512M", "-initrd", img])
        self.emulator.login()

        # The dotnet host must be in the PATH, and must find the
        # runtime in its default location, without any environment
        # variable or /etc/dotnet/install_location file.
        out, ret = self.emulator.run("dotnet --list-runtimes", timeout=60)
        self.assertEqual(ret, 0)
        self.assertIn(f"Microsoft.NETCore.App {version} "
                      "[/usr/share/dotnet/shared/Microsoft.NETCore.App]",
                      out)
        self.assertRunOk("dotnet --info", timeout=60)
        self.assertRunOk("test ! -e /etc/dotnet/install_location")


class TestDotnetRuntimeBin10(TestDotnetRuntimeBase):
    config = TestDotnetRuntimeBase.config + \
        """
        BR2_PACKAGE_DOTNET_RUNTIME_10_0=y
        """

    def test_run(self):
        self.check_runtime("10.0.15")


class TestDotnetRuntimeBin8(TestDotnetRuntimeBase):
    config = TestDotnetRuntimeBase.config + \
        """
        BR2_PACKAGE_DOTNET_RUNTIME_8_0=y
        """

    def test_run(self):
        self.check_runtime("8.0.34")


class TestDotnetRuntimeBin6(TestDotnetRuntimeBase):
    config = TestDotnetRuntimeBase.config + \
        """
        BR2_PACKAGE_DOTNET_RUNTIME_6_0=y
        """

    def test_run(self):
        self.check_runtime("6.0.36")


class TestDotnetRuntimeSrc10(TestDotnetRuntimeBase):
    config = TestDotnetRuntimeBase.config + \
        """
        BR2_PACKAGE_DOTNET_RUNTIME_SRC=y
        BR2_PACKAGE_DOTNET_RUNTIME_10_0=y
        """

    def test_run(self):
        self.check_runtime("10.0.15")


class TestDotnetRuntimeSrc8(TestDotnetRuntimeBase):
    config = TestDotnetRuntimeBase.config + \
        """
        BR2_PACKAGE_DOTNET_RUNTIME_SRC=y
        BR2_PACKAGE_DOTNET_RUNTIME_8_0=y
        """

    def test_run(self):
        self.check_runtime("8.0.34")


class TestDotnetRuntimeSrc6(TestDotnetRuntimeBase):
    config = TestDotnetRuntimeBase.config + \
        """
        BR2_PACKAGE_DOTNET_RUNTIME_SRC=y
        BR2_PACKAGE_DOTNET_RUNTIME_6_0=y
        """

    def test_run(self):
        self.check_runtime("6.0.36")

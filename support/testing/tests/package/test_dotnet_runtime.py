import os

import infra.basetest


class TestDotnetRuntimeBase(infra.basetest.BRTest):
    config = \
        """
        BR2_TOOLCHAIN_EXTERNAL=y
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN=y
        BR2_PACKAGE_DOTNET_RUNTIME=y
        BR2_PACKAGE_DOTNET_RUNTIME_ICU=y
        BR2_PACKAGE_DOTNET_RUNTIME_OPENSSL=y
        BR2_PACKAGE_DOTNET_RUNTIME_KRB5=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def check_runtime(self, version):
        self.login()

        # The dotnet host must be in the PATH, and must find the
        # runtime in its default location, without any environment
        # variable or /etc/dotnet/install_location file.
        out, ret = self.emulator.run("dotnet --list-runtimes", timeout=60)
        self.assertEqual(ret, 0)
        self.assertIn(f"Microsoft.NETCore.App {version} "
                      "[/usr/share/dotnet/shared/Microsoft.NETCore.App]",
                      out)
        self.assertRunOk("test ! -e /etc/dotnet/install_location")

        # The host must report the RID of the target, including the C
        # library, that it uses to find the native assets of the
        # applications.
        libc = "musl-" if "_MUSL_STABLE=y" in self.config else ""
        out, ret = self.emulator.run("dotnet --info", timeout=60)
        self.assertEqual(ret, 0)
        rids = [line.split()[1] for line in out
                if line.strip().startswith("RID:")]
        self.assertEqual(rids, [f"linux-{libc}{self.rid_arch}"])

        # The libraries loaded at runtime by the runtime must be
        # installed.
        self.assertRunOk("ls /usr/lib/libicuuc.so.* /usr/lib/libicui18n.so.*")
        self.assertRunOk("ls /usr/lib/libssl.so.* /usr/lib/libcrypto.so.*")
        self.assertRunOk("ls /usr/lib/libgssapi_krb5.so.2")


class TestDotnetRuntimeArm(TestDotnetRuntimeBase):
    rid_arch = "arm"

    # The .NET runtime needs ARMv7-A with the hard-float ABI on ARM,
    # so infra.basetest.BASIC_TOOLCHAIN_CONFIG can't be used.
    config = TestDotnetRuntimeBase.config + \
        """
        BR2_arm=y
        BR2_cortex_a9=y
        BR2_ARM_ENABLE_NEON=y
        BR2_ARM_ENABLE_VFP=y
        BR2_TARGET_GENERIC_GETTY_PORT="ttyAMA0"
        """

    def login(self):
        img = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv7",
                           kernel="builtin",
                           options=["-m", "512M", "-initrd", img])
        self.emulator.login()


class TestDotnetRuntimeAarch64(TestDotnetRuntimeBase):
    rid_arch = "arm64"

    config = TestDotnetRuntimeBase.config + \
        """
        BR2_aarch64=y
        BR2_TARGET_GENERIC_GETTY_PORT="ttyAMA0"
        BR2_LINUX_KERNEL=y
        BR2_LINUX_KERNEL_CUSTOM_VERSION=y
        BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE="6.18.21"
        BR2_LINUX_KERNEL_USE_CUSTOM_CONFIG=y
        BR2_LINUX_KERNEL_CUSTOM_CONFIG_FILE="board/qemu/aarch64-virt/linux.config"
        BR2_LINUX_KERNEL_NEEDS_HOST_OPENSSL=y
        """

    def login(self):
        img = os.path.join(self.builddir, "images", "rootfs.cpio")
        kernel = os.path.join(self.builddir, "images", "Image")
        self.emulator.boot(arch="aarch64",
                           kernel=kernel,
                           kernel_cmdline=["console=ttyAMA0"],
                           options=["-M", "virt", "-cpu", "cortex-a57",
                                    "-m", "1G", "-initrd", img])
        self.emulator.login()


class TestDotnetRuntimeX8664(TestDotnetRuntimeBase):
    rid_arch = "x64"

    config = TestDotnetRuntimeBase.config + \
        """
        BR2_x86_64=y
        BR2_x86_corei7=y
        BR2_TARGET_GENERIC_GETTY_PORT="ttyS0"
        BR2_LINUX_KERNEL=y
        BR2_LINUX_KERNEL_CUSTOM_VERSION=y
        BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE="6.18.21"
        BR2_LINUX_KERNEL_USE_CUSTOM_CONFIG=y
        BR2_LINUX_KERNEL_CUSTOM_CONFIG_FILE="board/qemu/x86_64/linux.config"
        BR2_LINUX_KERNEL_NEEDS_HOST_LIBELF=y
        """

    def login(self):
        img = os.path.join(self.builddir, "images", "rootfs.cpio")
        kernel = os.path.join(self.builddir, "images", "bzImage")
        self.emulator.boot(arch="x86_64",
                           kernel=kernel,
                           kernel_cmdline=["console=ttyS0"],
                           options=["-cpu", "Nehalem",
                                    "-m", "1G", "-initrd", img])
        self.emulator.login()


class TestDotnetRuntimeBinArmGlibc(TestDotnetRuntimeArm):
    config = TestDotnetRuntimeArm.config + \
        """
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_ARMV7_EABIHF_GLIBC_STABLE=y
        """

    def test_run(self):
        self.check_runtime("11.0.0")


class TestDotnetRuntimeBinArmMusl(TestDotnetRuntimeArm):
    config = TestDotnetRuntimeArm.config + \
        """
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_ARMV7_EABIHF_MUSL_STABLE=y
        """

    def test_run(self):
        self.check_runtime("11.0.0")


class TestDotnetRuntimeBinAarch64Glibc(TestDotnetRuntimeAarch64):
    config = TestDotnetRuntimeAarch64.config + \
        """
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_AARCH64_GLIBC_STABLE=y
        """

    def test_run(self):
        self.check_runtime("11.0.0")


class TestDotnetRuntimeBinAarch64Musl(TestDotnetRuntimeAarch64):
    config = TestDotnetRuntimeAarch64.config + \
        """
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_AARCH64_MUSL_STABLE=y
        """

    def test_run(self):
        self.check_runtime("11.0.0")


class TestDotnetRuntimeBinX8664Glibc(TestDotnetRuntimeX8664):
    config = TestDotnetRuntimeX8664.config + \
        """
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_X86_64_GLIBC_STABLE=y
        """

    def test_run(self):
        self.check_runtime("11.0.0")


class TestDotnetRuntimeBinX8664Musl(TestDotnetRuntimeX8664):
    config = TestDotnetRuntimeX8664.config + \
        """
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_X86_64_MUSL_STABLE=y
        """

    def test_run(self):
        self.check_runtime("11.0.0")


class TestDotnetRuntimeSrcArmGlibc(TestDotnetRuntimeArm):
    config = TestDotnetRuntimeArm.config + \
        """
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_ARMV7_EABIHF_GLIBC_STABLE=y
        BR2_PACKAGE_DOTNET_RUNTIME_SRC=y
        """

    def test_run(self):
        self.check_runtime("11.0.0")


class TestDotnetRuntimeSrcArmMusl(TestDotnetRuntimeArm):
    config = TestDotnetRuntimeArm.config + \
        """
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_ARMV7_EABIHF_MUSL_STABLE=y
        BR2_PACKAGE_DOTNET_RUNTIME_SRC=y
        """

    def test_run(self):
        self.check_runtime("11.0.0")


class TestDotnetRuntimeSrcAarch64Glibc(TestDotnetRuntimeAarch64):
    config = TestDotnetRuntimeAarch64.config + \
        """
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_AARCH64_GLIBC_STABLE=y
        BR2_PACKAGE_DOTNET_RUNTIME_SRC=y
        """

    def test_run(self):
        self.check_runtime("11.0.0")


class TestDotnetRuntimeSrcAarch64Musl(TestDotnetRuntimeAarch64):
    config = TestDotnetRuntimeAarch64.config + \
        """
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_AARCH64_MUSL_STABLE=y
        BR2_PACKAGE_DOTNET_RUNTIME_SRC=y
        """

    def test_run(self):
        self.check_runtime("11.0.0")


class TestDotnetRuntimeSrcX8664Glibc(TestDotnetRuntimeX8664):
    config = TestDotnetRuntimeX8664.config + \
        """
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_X86_64_GLIBC_STABLE=y
        BR2_PACKAGE_DOTNET_RUNTIME_SRC=y
        """

    def test_run(self):
        self.check_runtime("11.0.0")


class TestDotnetRuntimeSrcX8664Musl(TestDotnetRuntimeX8664):
    config = TestDotnetRuntimeX8664.config + \
        """
        BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_X86_64_MUSL_STABLE=y
        BR2_PACKAGE_DOTNET_RUNTIME_SRC=y
        """

    def test_run(self):
        self.check_runtime("11.0.0")

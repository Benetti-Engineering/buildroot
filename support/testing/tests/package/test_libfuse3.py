import os

import infra.basetest


class TestLibFuse3(infra.basetest.BRTest):
    # The libfuse3 package has _LINUX_CONFIG_FIXUPS, so we cannot use
    # the runtime test pre-built Kernel. We need to compile a Kernel
    # to make sure it will include the required configuration.
    br2_external = [infra.filepath("tests/package/br2-external/libfuse3")]
    config = \
        """
        BR2_aarch64=y
        BR2_TOOLCHAIN_EXTERNAL=y
        BR2_TARGET_GENERIC_GETTY_PORT="ttyAMA0"
        BR2_LINUX_KERNEL=y
        BR2_LINUX_KERNEL_CUSTOM_VERSION=y
        BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE="6.18.21"
        BR2_LINUX_KERNEL_USE_CUSTOM_CONFIG=y
        BR2_LINUX_KERNEL_CUSTOM_CONFIG_FILE="board/qemu/aarch64-virt/linux.config"
        BR2_LINUX_KERNEL_NEEDS_HOST_OPENSSL=y
        BR2_PACKAGE_LIBFUSE3=y
        BR2_PACKAGE_LIBFUSE3_TEST=y
        BR2_TARGET_ROOTFS_CPIO=y
        BR2_TARGET_ROOTFS_CPIO_GZIP=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        img = os.path.join(self.builddir, "images", "rootfs.cpio.gz")
        kern = os.path.join(self.builddir, "images", "Image")
        self.emulator.boot(arch="aarch64",
                           kernel=kern,
                           kernel_cmdline=["console=ttyAMA0"],
                           options=["-M", "virt", "-cpu", "cortex-a57", "-m", "256M",
                                    "-initrd", img])
        self.emulator.login()

        mnt = "/mnt/fuse"

        # Check the fusermount3 program can execute.
        out, ret = self.emulator.run("fusermount3 --version")
        self.assertEqual(ret, 0)
        self.assertRegex(out[0], r"^fusermount3 version: 3\.\d+\.\d+$")

        # Check the kernel supports FUSE.
        self.assertRunOk("grep -qw fuse /proc/filesystems")
        self.assertRunOk("test -c /dev/fuse")

        # Mount our test filesystem.
        self.assertRunOk(f"mkdir -p {mnt}")
        self.assertRunOk(f"fuse3-hello {mnt}")
        out, ret = self.emulator.run(f"grep ' {mnt} ' /proc/mounts")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0].split()[2], "fuse.fuse3-hello")

        # Check the filesystem content.
        out, ret = self.emulator.run(f"ls --color=never {mnt}")
        self.assertEqual(ret, 0)
        self.assertEqual(out, ["hello"])

        out, ret = self.emulator.run(f"cat {mnt}/hello")
        self.assertEqual(ret, 0)
        self.assertEqual(out, ["Hello Buildroot FUSE"])

        out, ret = self.emulator.run(f"ls -l --color=never {mnt}/hello")
        self.assertEqual(ret, 0)
        self.assertTrue(out[0].startswith("-r--r--r--"), out[0])
        out, ret = self.emulator.run(f"wc -c < {mnt}/hello")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0].strip(), "21")

        # The filesystem is read-only: writing or creating files must
        # fail, and non existing files must not be found.
        self.assertRunNotOk(f"echo test >> {mnt}/hello")
        self.assertRunNotOk(f"touch {mnt}/newfile")
        self.assertRunNotOk(f"cat {mnt}/missing")

        # Unmount the filesystem with fusermount3.
        self.assertRunOk(f"fusermount3 -u {mnt}")
        self.assertRunNotOk(f"grep -q ' {mnt} ' /proc/mounts")
        out, ret = self.emulator.run(f"ls --color=never {mnt}")
        self.assertEqual(ret, 0)
        self.assertEqual(out, [])

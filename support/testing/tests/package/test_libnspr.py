import os

import infra.basetest


class TestLibNspr(infra.basetest.BRTest):
    br2_external = [infra.filepath("tests/package/br2-external/libnspr")]
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        """
        BR2_PACKAGE_LIBNSPR=y
        BR2_PACKAGE_LIBNSPR_TEST=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv5",
                           kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login()

        # Run our test program, which exercises NSPR threads, locks,
        # atomics, time, string and file I/O functions.
        out, ret = self.emulator.run("libnspr-test", timeout=30)
        self.assertEqual(ret, 0, "\n".join(out))
        self.assertRegex(out[0], r"^NSPR version: 4\.\d+")
        self.assertIn("threads: counter=40000 atomic=40000", out)
        self.assertIn("time: 2000-01-02 03:04:05", out)
        self.assertIn("snprintf: nspr-42-1099511627776", out)
        self.assertIn("file: Hello NSPR file", out)
        self.assertEqual(out[-1], "NSPR test OK")

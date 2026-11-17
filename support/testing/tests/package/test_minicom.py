import os

import infra.basetest


class TestMinicom(infra.basetest.BRTest):
    rootfs_overlay = \
        infra.filepath("tests/package/test_minicom/rootfs-overlay")
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        f"""
        BR2_PACKAGE_MINICOM=y
        BR2_ROOTFS_OVERLAY="{rootfs_overlay}"
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv5",
                           kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login()

        # Check the programs can execute.
        out, ret = self.emulator.run("minicom --version")
        self.assertEqual(ret, 0)
        self.assertTrue(out[0].startswith("minicom version"))

        out, ret = self.emulator.run("runscript --version")
        self.assertEqual(ret, 0)
        self.assertTrue(out[0].startswith("runscript, part of minicom version"))

        # Run a script, simulating a modem answering "OK" on stdin.
        # The "send" output goes to stdout (the modem), and the
        # "print" output to stderr (the user).
        cmd = "echo OK | runscript /root/test.runscript 2>/tmp/rs.err | tr -d '\\r'"
        out, ret = self.emulator.run(cmd)
        self.assertEqual(ret, 0)
        self.assertEqual(out, ["AT"])
        out, ret = self.emulator.run("tr -d '\\r' < /tmp/rs.err")
        self.assertEqual(ret, 0)
        self.assertEqual(out, ["Got OK from modem"])

        # Without the expected answer, the script is expected to
        # fail.
        cmd = "echo ERROR | runscript /root/test.runscript >/dev/null 2>&1"
        self.assertRunNotOk(cmd, timeout=30)

        # Check an ascii-xfr upload/download round trip.
        self.assertRunOk("printf 'line 1\\nline 2\\n' > /tmp/ascii.txt")
        cmd = "ascii-xfr -s -l 0 -c 0 /tmp/ascii.txt 2>/dev/null | " \
              "ascii-xfr -r /tmp/ascii.out 2>/dev/null"
        self.assertRunOk(cmd)
        out, ret = self.emulator.run("tr -d '\\r' < /tmp/ascii.out")
        self.assertEqual(ret, 0)
        self.assertEqual(out, ["line 1", "line 2"])

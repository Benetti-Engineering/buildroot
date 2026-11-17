import os

import infra.basetest


class TestDash(infra.basetest.BRTest):
    rootfs_overlay = \
        infra.filepath("tests/package/test_dash/rootfs-overlay")
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        f"""
        BR2_PACKAGE_BUSYBOX_SHOW_OTHERS=y
        BR2_PACKAGE_DASH=y
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

        # Check dash has been added to /etc/shells
        self.assertRunOk("grep -qx /bin/dash /etc/shells")

        # Check a simple command and its exit code
        out, ret = self.emulator.run("dash -c 'echo hello from dash'")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "hello from dash")

        out, ret = self.emulator.run("dash -c 'exit 42'")
        self.assertEqual(ret, 42)

        # A syntax error must be reported as a failure
        self.assertRunNotOk("dash -c 'if then fi'")

        # Run a POSIX script exercising various shell features
        out, ret = self.emulator.run("/root/test_dash.sh")
        self.assertEqual(ret, 0, "\n".join(out))
        self.assertEqual(out[-1], "PASS")

        # Start an interactive dash and check we are indeed running it.
        # The test infra prompt uses the bash-specific "\[\]" escape
        # sequence, that dash doesn't interpret, so we pass it a plain
        # prompt instead. It is split with quotes so the command echo
        # doesn't get mistaken for the prompt.
        self.assertRunOk("PS1='[BRTE''ST# ' PS2='[BRTE''ST+ ' dash -i")
        out, ret = self.emulator.run("readlink /proc/$$/exe")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "/bin/dash", "Not running dash")
        self.emulator.run("exit 0")

        # Check we are back to busybox' shell
        out, ret = self.emulator.run("readlink /proc/$$/exe")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "/bin/busybox", "Still running dash")

import os

import infra.basetest


class TestVim(infra.basetest.BRTest):
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        """
        BR2_PACKAGE_BUSYBOX_SHOW_OTHERS=y
        BR2_PACKAGE_VIM=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv5",
                           kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login()

        # Check the program can execute.
        out, ret = self.emulator.run("vim --version")
        self.assertEqual(ret, 0)
        self.assertTrue(out[0].startswith("VIM - Vi IMproved"))

        # Create a new file with vim in Ex mode (non interactive).
        test_file = "/tmp/vim-test.txt"
        cmd = f"vim -es -c 's/^/Hello Buildroot/' -c 'wq' {test_file}"
        self.assertRunOk(cmd)
        out, ret = self.emulator.run(f"cat {test_file}")
        self.assertEqual(ret, 0)
        self.assertEqual(out, ["Hello Buildroot"])

        # Edit an existing file: substitution on the whole file.
        self.assertRunOk(f"printf 'foo bar foo\\nzzz\\n' >> {test_file}")
        cmd = f"vim -es -c '%s/foo/baz/g' -c 'wq' {test_file}"
        self.assertRunOk(cmd)
        out, ret = self.emulator.run(f"cat {test_file}")
        self.assertEqual(ret, 0)
        self.assertEqual(out, ["Hello Buildroot", "baz bar baz", "zzz"])

        # Sort lines in reverse order, delete one of them and move
        # the last line to the top.
        cmd = f"vim -es -c 'sort!' -c 'g/Hello/d' -c '$m0' -c 'wq' {test_file}"
        self.assertRunOk(cmd)
        out, ret = self.emulator.run(f"cat {test_file}")
        self.assertEqual(ret, 0)
        self.assertEqual(out, ["baz bar baz", "zzz"])

        # Check that vim exits with an error code with ":cquit".
        self.assertRunNotOk("vim -es -c 'cquit 3'")

        # Check that xxd, installed with vim, can do a hexdump and its
        # reverse operation.
        cmd = "printf 'Buildroot' | xxd -p"
        out, ret = self.emulator.run(cmd)
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "4275696c64726f6f74")

        cmd = "echo 4275696c64726f6f74 | xxd -r -p"
        out, ret = self.emulator.run(cmd)
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "Buildroot")

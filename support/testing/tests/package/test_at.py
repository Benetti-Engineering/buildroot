import os

import infra.basetest


class TestAt(infra.basetest.BRTest):
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        """
        BR2_PACKAGE_AT=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv5",
                           kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login()

        # The atd daemon is supposed to be started by the init script.
        self.assertRunOk("pidof atd")

        # The job queue is supposed to be empty.
        out, ret = self.emulator.run("atq")
        self.assertEqual(ret, 0)
        self.assertEqual(out, [])

        # Schedule a job in a far future, check it is listed in the
        # queue, then remove it.
        self.assertRunOk("echo true | at now + 1 hour")
        out, ret = self.emulator.run("atq")
        self.assertEqual(ret, 0)
        self.assertEqual(len(out), 1)
        job_id = out[0].split()[0]
        self.assertRunOk(f"at -c {job_id} | grep -qx true")
        self.assertRunOk(f"atrm {job_id}")
        out, ret = self.emulator.run("atq")
        self.assertEqual(ret, 0)
        self.assertEqual(out, [])

        # Schedule a job to run immediately, and wait for its result.
        out_file = "/tmp/at-test.out"
        msg = "Hello from atd"
        self.assertRunOk(f"echo 'echo {msg} > {out_file}' | at now")
        cmd = f"for i in $(seq 60); do [ -s {out_file} ] && break; sleep 1; done"
        self.assertRunOk(cmd, timeout=70)
        out, ret = self.emulator.run(f"cat {out_file}")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], msg)

        # The queue is supposed to be empty again.
        out, ret = self.emulator.run("atq")
        self.assertEqual(ret, 0)
        self.assertEqual(out, [])

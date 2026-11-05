import os

import infra.basetest


class TestSwupdateInfra(infra.basetest.BRTest):
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
             """
             BR2_PACKAGE_SWUPDATE=y
             BR2_PACKAGE_HOST_SWUGENERATOR=y
             BR2_TARGET_ROOTFS_CPIO=y
             BR2_ROOTFS_POST_BUILD_SCRIPT="{}"
             BR2_ROOTFS_OVERLAY="{}"
             """.format(
                 infra.filepath("tests/package/test_swupdate/post-build.sh"),
                 # overlay to add a fake 'fw_printenv', used by Swupdate
                 infra.filepath("tests/package/test_swupdate/rootfs-overlay"))

    def base_test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv5", kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login()

    def run_swupdate_test(self):
        self.assertRunOk("ps aux | egrep swupdate")

        # Check if a simple Swupdate command is correctly executed
        self.assertRunOk("swupdate -n -i 'RUNTIME_TEST_ARTIFACT_NAME' -v")
        cmd = "swupdate show-artifact 2>&1 | grep -i 'err'"  # TODO!!! Check if no 'error' among the traces
        _, exit_code = self.emulator.run(cmd)
        self.assertEqual(exit_code, 1)


class TestSwupdateRW(TestSwupdateInfra):
    def test_run(self):
        TestSwupdateInfra.base_test_run(self)

        # Check if the Daemon is running
        self.assertRunOk("ls /var/run/swupdate.pid")
        self.run_swupdate_test()


class TestSwupdateRO(TestSwupdateInfra):
    config = \
        """
        {}
        # BR2_TARGET_GENERIC_REMOUNT_ROOTFS_RW is not set
        """.format(TestSwupdateInfra.config)

    def test_run(self):
        TestSwupdateInfra.base_test_run(self)

        # Check if the Daemon is running
        self.assertRunOk("ls /var/run/swupdate.pid")
        self.run_swupdate_test()


class TestSwupdateSystemd(TestSwupdateInfra):
    config = \
        """
        {}
        BR2_INIT_SYSTEMD=y
        """.format(TestSwupdateInfra.config)

    def test_run(self):
        TestSwupdateInfra.base_test_run(self)
        output, _ = self.emulator.run("systemctl is-active swupdate-client")
        self.assertEqual(output[0], "active")
        self.run_swupdate_test()

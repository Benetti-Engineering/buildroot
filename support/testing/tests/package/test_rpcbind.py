import os

import infra.basetest


class TestRpcbind(infra.basetest.BRTest):
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        """
        BR2_PACKAGE_RPCBIND=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv5",
                           kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login()

        # The rpcbind daemon is supposed to be started by the init
        # script.
        self.assertRunOk("pidof rpcbind")

        # Query the list of registered programs. The portmapper itself
        # (program 100000) is expected to be registered, in versions
        # 2, 3 and 4, over tcp and udp. Note: programs are referenced
        # by number, as there is no /etc/rpc database to resolve names.
        out, ret = self.emulator.run("rpcinfo -p")
        self.assertEqual(ret, 0)
        for vers in [2, 3, 4]:
            for proto in ["tcp", "udp"]:
                regex = rf"^\s*100000\s+{vers}\s+{proto}\s+111\b"
                self.assertRegex("\n".join(out), f"(?m){regex}")

        # Same check, with the short format and rpcbind protocol.
        out, ret = self.emulator.run("rpcinfo -s")
        self.assertEqual(ret, 0)
        self.assertRegex("\n".join(out), r"(?m)^\s*100000\s+2,3,4\s")

        # Call the NULL procedure of the portmapper, over tcp and udp.
        for proto in ["tcp", "udp"]:
            cmd = f"rpcinfo -T {proto} 127.0.0.1 100000 2"
            out, ret = self.emulator.run(cmd)
            self.assertEqual(ret, 0)
            self.assertIn("program 100000 version 2 ready and waiting", out)

        # Querying a non registered program (NFS) is expected to fail.
        self.assertRunNotOk("rpcinfo -T tcp 127.0.0.1 100003")

        # Stop the daemon and check that queries now fail.
        self.assertRunOk("/etc/init.d/S30rpcbind stop")
        self.assertRunNotOk("rpcinfo -p")

        # Restart it and check it answers again.
        self.assertRunOk("/etc/init.d/S30rpcbind start")
        self.assertRunOk("rpcinfo -T tcp 127.0.0.1 100000 4")

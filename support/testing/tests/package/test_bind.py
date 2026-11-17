import os

import infra.basetest


class TestBind(infra.basetest.BRTest):
    rootfs_overlay = \
        infra.filepath("tests/package/test_bind/rootfs-overlay")
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        f"""
        BR2_PACKAGE_BIND=y
        BR2_PACKAGE_BIND_SERVER=y
        BR2_PACKAGE_BIND_TOOLS=y
        BR2_ROOTFS_OVERLAY="{rootfs_overlay}"
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def dig(self, args):
        cmd = f"dig @127.0.0.1 +short {args}"
        out, ret = self.emulator.run(cmd)
        self.assertEqual(ret, 0)
        return out

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv5",
                           kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login()

        # Check the programs can execute.
        self.assertRunOk("named -v")
        self.assertRunOk("dig -v")

        # Check our configuration and zone files are valid.
        self.assertRunOk("named-checkconf -z /etc/bind/named.conf")
        cmd = "named-checkzone buildroot.test /etc/bind/db.buildroot.test"
        self.assertRunOk(cmd)

        # The named server is supposed to be started by the sysv
        # initscript. Wait for it to be ready to answer queries, as it
        # can take a few seconds to start in the emulator.
        cmd = "for i in $(seq 60); do rndc status >/dev/null 2>&1 && break; sleep 1; done"
        self.assertRunOk(cmd, timeout=70)
        out, ret = self.emulator.run("rndc status")
        self.assertEqual(ret, 0)
        self.assertIn("server is up and running", out)

        # Query our test records with dig.
        self.assertEqual(self.dig("somehost.buildroot.test A"),
                         ["10.20.30.40"])
        self.assertEqual(self.dig("sometext.buildroot.test TXT"),
                         ["\"Hello Buildroot TXT\""])
        self.assertEqual(self.dig("www.buildroot.test A"),
                         ["somehost.buildroot.test.", "10.20.30.40"])
        self.assertEqual(self.dig("-x 10.20.30.40"),
                         ["somehost.buildroot.test."])

        # A non existing name is expected to return an empty answer.
        self.assertEqual(self.dig("unknown.buildroot.test A"), [])

        # Query the same record with the "host" program.
        cmd = "host somehost.buildroot.test 127.0.0.1"
        out, ret = self.emulator.run(cmd)
        self.assertEqual(ret, 0)
        self.assertIn("somehost.buildroot.test has address 10.20.30.40", out)

        # Recursion is disabled, so the server must refuse queries for
        # zones it is not authoritative for.
        cmd = "dig @127.0.0.1 buildroot.org A | grep -q 'status: REFUSED'"
        self.assertRunOk(cmd)

        # Stop the server with rndc and check it is no longer running.
        self.assertRunOk("rndc stop")
        cmd = "for i in $(seq 30); do pidof named || break; sleep 1; done"
        self.emulator.run(cmd, timeout=40)
        self.assertRunNotOk("pidof named")

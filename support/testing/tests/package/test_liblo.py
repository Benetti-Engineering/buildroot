import os

import infra.basetest


class TestLiblo(infra.basetest.BRTest):
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        """
        BR2_PACKAGE_LIBLO=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def check_osc(self, server_url, client_url, log_file):
        # Start the oscdump server in background, with line
        # buffering (-L) as the output is redirected to a file.
        cmd = f"oscdump -L {server_url} > {log_file} 2>&1 &"
        self.assertRunOk(cmd)
        # Give some time to the server to start.
        self.assertRunOk("sleep 2")

        # Send messages with various argument types.
        cmd = f"oscsend {client_url} /buildroot/test ifs 42 3.14 hello"
        self.assertRunOk(cmd)
        cmd = f"oscsend {client_url} /buildroot/other TFN"
        self.assertRunOk(cmd)
        self.assertRunOk("sleep 1")

        out, ret = self.emulator.run(f"cat {log_file}")
        self.assertEqual(ret, 0)
        self.assertRegex(out[0],
                         r'^[0-9a-f]{8}\.[0-9a-f]{8} /buildroot/test ifs 42 3\.140000 "hello"$')
        self.assertRegex(out[1],
                         r'^[0-9a-f]{8}\.[0-9a-f]{8} /buildroot/other TFN #T #F Nil$')

        self.assertRunOk("kill $!")

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv5",
                           kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login()

        # Check the liblo tools can execute.
        self.assertRunOk("oscdump -h | grep -q '^Usage: oscdump'")

        # Exchange OSC messages over UDP, then TCP.
        self.check_osc("7770", "localhost 7770", "/tmp/osc-udp.log")
        self.check_osc("osc.tcp://:7771", "osc.tcp://localhost:7771/",
                       "/tmp/osc-tcp.log")

        # Sending an invalid type must fail.
        self.assertRunNotOk("oscsend localhost 7770 /buildroot/test i notanint")

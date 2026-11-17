import os
import time

import infra.basetest


class TestWireshark(infra.basetest.BRTest):
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        """
        BR2_PACKAGE_WIRESHARK=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        # The rootfs is too large to be unpacked with the 256MB of
        # memory of the armv5 machine, so we use the armv7 one, with
        # more memory.
        self.emulator.boot(arch="armv7",
                           kernel="builtin",
                           options=["-m", "512M", "-initrd", cpio_file])
        self.emulator.login()

        capture_file = "/tmp/capture.pcapng"

        # Check the programs can execute. Note: tshark can be slow to
        # start in the emulator, as it registers all its dissectors.
        self.assertRunOk("dumpcap --version")
        self.assertRunOk("tshark --version", timeout=120)

        # Check the loopback interface is listed.
        out, ret = self.emulator.run("dumpcap -D")
        self.assertEqual(ret, 0)
        self.assertRegex("\n".join(out), r"(?m)^\d+\. lo")

        # Run ping in background and capture some ICMP packets.
        self.assertRunOk("ping localhost >/dev/null &")
        time.sleep(1)
        cmd = f"dumpcap -q -i lo -f icmp -c 6 -w {capture_file}"
        self.assertRunOk(cmd, timeout=60)
        self.assertRunOk("kill $!")

        # Check the capture file information.
        out, ret = self.emulator.run(f"capinfos -c -M {capture_file}")
        self.assertEqual(ret, 0)
        self.assertRegex("\n".join(out), r"Number of packets:\s+6")

        # Decode the capture, and check we see ICMP echo requests and
        # replies. Note: tshark prints a warning on stderr when running
        # as root, so we discard it.
        cmd = f"tshark -r {capture_file} 2>/dev/null"
        out, ret = self.emulator.run(cmd, timeout=120)
        self.assertEqual(ret, 0)
        self.assertEqual(len(out), 6)
        decoded = "\n".join(out)
        self.assertIn("Echo (ping) request", decoded)
        self.assertIn("Echo (ping) reply", decoded)

        # Apply a display filter and extract some fields.
        cmd = f"tshark -r {capture_file} -Y 'icmp.type == 8' " \
            "-T fields -e ip.src -e ip.dst -e icmp.type 2>/dev/null"
        out, ret = self.emulator.run(cmd, timeout=120)
        self.assertEqual(ret, 0)
        self.assertGreaterEqual(len(out), 2)
        for line in out:
            self.assertEqual(line.split(), ["127.0.0.1", "127.0.0.1", "8"])

        # An invalid display filter must be rejected.
        cmd = f"tshark -r {capture_file} -Y 'not a valid filter'"
        self.assertRunNotOk(cmd, timeout=120)

        # Extract the first two packets with editcap and check the
        # result.
        cmd = f"editcap -r {capture_file} /tmp/first.pcapng 1-2"
        self.assertRunOk(cmd)
        out, ret = self.emulator.run("capinfos -c -M /tmp/first.pcapng")
        self.assertEqual(ret, 0)
        self.assertRegex("\n".join(out), r"Number of packets:\s+2")

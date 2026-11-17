import os
import subprocess

import infra.basetest


class TestMmcUtils(infra.basetest.BRTest):
    # The armv7 pre-built Kernel boots on the Qemu vexpress-a9
    # machine, which has a MMC controller (PL181). We attach a SD card
    # to it.
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        """
        BR2_PACKAGE_MMC_UTILS=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        # Qemu requires the SD card size to be a power of 2.
        sd_file = os.path.join(self.builddir, "images", "sd.img")
        self.emulator.logfile.write(f"Creating SD card image: {sd_file}\n")
        self.emulator.logfile.flush()
        subprocess.check_call(
            ["dd", "if=/dev/zero", f"of={sd_file}", "bs=1M", "count=16"],
            stdout=self.emulator.logfile,
            stderr=self.emulator.logfile)

        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv7",
                           kernel="builtin",
                           options=["-initrd", cpio_file,
                                    "-drive", f"file={sd_file},if=sd,format=raw"])
        self.emulator.login()

        # Check the program can execute.
        self.assertRunOk("mmc --help | grep -q 'cid read'")

        # Wait for the SD card to be detected.
        cmd = "for i in $(seq 30); do [ -b /dev/mmcblk0 ] && break; sleep 1; done"
        self.assertRunOk(cmd, timeout=40)
        self.assertRunOk("test -b /dev/mmcblk0")

        # Find the card sysfs directory, and check it is a SD card. We
        # use "echo" rather than "ls", which may colorize its output.
        out, ret = self.emulator.run("echo /sys/bus/mmc/devices/mmc0:*")
        self.assertEqual(ret, 0)
        card_dir = out[0]
        out, ret = self.emulator.run(f"cat {card_dir}/type")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "SD")

        # Decode the card identification register. The Qemu SD card
        # has fixed product name and serial number.
        out, ret = self.emulator.run(f"mmc cid read {card_dir}")
        self.assertEqual(ret, 0)
        self.assertIn("product: 'QEMU!' 0.1", out)
        self.assertIn("serial: 0xdeadbeef", out)

        # Same, in verbose mode.
        out, ret = self.emulator.run(f"mmc cid read -v {card_dir}")
        self.assertEqual(ret, 0)
        self.assertIn("======SD/CID======", out)
        self.assertIn("\tPNM: QEMU!", out)

        # Decode the card specific data and SD configuration
        # registers.
        out, ret = self.emulator.run(f"mmc csd read {card_dir}")
        self.assertEqual(ret, 0)
        self.assertTrue(len(out) > 0)
        out, ret = self.emulator.run(f"mmc scr read {card_dir}")
        self.assertEqual(ret, 0)
        self.assertTrue(len(out) > 0)

        # Reading registers from a non existing directory must fail.
        self.assertRunNotOk("mmc cid read /sys/bus/mmc/devices/nonexistent")

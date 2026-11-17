import os

import infra.basetest


class TestUtilLinux(infra.basetest.BRTest):
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        """
        BR2_PACKAGE_UTIL_LINUX=y
        BR2_PACKAGE_UTIL_LINUX_BINARIES=y
        BR2_PACKAGE_UTIL_LINUX_SCHEDUTILS=y
        BR2_PACKAGE_UTIL_LINUX_WIPEFS=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv5",
                           kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login()

        # Check we are running the util-linux programs, and not the
        # BusyBox applets with the same name.
        for prog in ["blkid", "sfdisk", "mkswap", "hexdump", "taskset"]:
            cmd = f"{prog} --version | grep -q 'from util-linux'"
            self.assertRunOk(cmd)

        # Generate random and time-based UUIDs.
        uuid_re = r"^[0-9a-f]{8}-[0-9a-f]{4}-([0-9a-f]){3}[0-9a-f]-[0-9a-f]{4}-[0-9a-f]{12}$"
        for opt, version in [("-r", "4"), ("-t", "1")]:
            out, ret = self.emulator.run(f"uuidgen {opt}")
            self.assertEqual(ret, 0)
            self.assertRegex(out[0], uuid_re)
            self.assertEqual(out[0][14], version)

        # Create a disk image, and partition it with sfdisk.
        disk = "/tmp/disk.img"
        self.assertRunOk(f"dd if=/dev/zero of={disk} bs=1M count=8")
        cmd = f"printf 'label: dos\\n,4MiB,L\\n,,S\\n' | sfdisk {disk}"
        self.assertRunOk(cmd)
        out, ret = self.emulator.run(f"sfdisk --dump {disk}")
        self.assertEqual(ret, 0)
        dump = "\n".join(out)
        self.assertIn("label: dos", dump)
        self.assertRegex(dump, r"(?m)^/tmp/disk\.img1 : start=\s*2048, size=\s*8192, type=83$")
        self.assertRegex(dump, r"(?m)^/tmp/disk\.img2 : start=\s*10240, size=\s*6144, type=82$")

        # Check the partition table is identified by blkid.
        out, ret = self.emulator.run(f"blkid -p -o value -s PTTYPE {disk}")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "dos")

        # Create a swap area with a label and a known UUID, then
        # check blkid can identify it.
        swap = "/tmp/swap.img"
        uuid = "01234567-89ab-cdef-0123-456789abcdef"
        self.assertRunOk(f"dd if=/dev/zero of={swap} bs=1M count=1")
        self.assertRunOk(f"mkswap -L brswap -U {uuid} {swap}")
        out, ret = self.emulator.run(f"blkid -p -o export {swap}")
        self.assertEqual(ret, 0)
        self.assertIn("TYPE=swap", out)
        self.assertIn("LABEL=brswap", out)
        self.assertIn(f"UUID={uuid}", out)

        # Erase the signature with wipefs, blkid must no longer
        # identify anything.
        self.assertRunOk(f"wipefs -a {swap}")
        self.assertRunNotOk(f"blkid -p {swap}")

        # Check findmnt shows the proc filesystem.
        out, ret = self.emulator.run("findmnt -n -o FSTYPE /proc")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "proc")

        # Check few text processing tools.
        out, ret = self.emulator.run("printf 'Buildroot' | hexdump -C")
        self.assertEqual(ret, 0)
        self.assertIn("|Buildroot|", out[0])

        out, ret = self.emulator.run("echo Buildroot | rev")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "toordliuB")

        out, ret = self.emulator.run("printf 'a bb\\nccc d\\n' | column -t")
        self.assertEqual(ret, 0)
        self.assertEqual(out, ["a    bb", "ccc  d"])

        out, ret = self.emulator.run("getopt -o ab: -- -a -b foo bar")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], " -a -b 'foo' -- 'bar'")

        # Check the scheduling utilities.
        out, ret = self.emulator.run("taskset -p 1")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "pid 1's current affinity mask: 1")
        out, ret = self.emulator.run("chrt -f 10 sh -c 'chrt -p $$'")
        self.assertEqual(ret, 0)
        self.assertRegex(out[0], r"scheduling policy: SCHED_FIFO$")
        self.assertRegex(out[1], r"scheduling priority: 10$")

        # Check file locking with flock: a second non-blocking lock
        # on the same file must fail while the first one is held.
        self.assertRunOk("flock /tmp/lock -c 'sleep 5' &")
        self.assertRunOk("sleep 1")
        self.assertRunNotOk("flock -n /tmp/lock true")
        self.assertRunOk("wait")
        self.assertRunOk("flock -n /tmp/lock true")

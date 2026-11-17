import os
import re
import subprocess

import infra.basetest


class TestUdisks(infra.basetest.BRTest):
    # udisks needs udev, and is tested with a virtio disk and a loop
    # device, so we compile a Kernel. This test also covers
    # libblockdev, which is used by the udisks daemon.
    kernel_fragment = \
        infra.filepath("tests/package/test_udisks/linux-udisks.fragment")
    config = \
        f"""
        BR2_aarch64=y
        BR2_TOOLCHAIN_EXTERNAL=y
        BR2_TARGET_GENERIC_GETTY_PORT="ttyAMA0"
        BR2_ROOTFS_DEVICE_CREATION_DYNAMIC_EUDEV=y
        BR2_LINUX_KERNEL=y
        BR2_LINUX_KERNEL_CUSTOM_VERSION=y
        BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE="6.18.21"
        BR2_LINUX_KERNEL_USE_CUSTOM_CONFIG=y
        BR2_LINUX_KERNEL_CUSTOM_CONFIG_FILE="board/qemu/aarch64-virt/linux.config"
        BR2_LINUX_KERNEL_CONFIG_FRAGMENT_FILES="{kernel_fragment}"
        BR2_LINUX_KERNEL_NEEDS_HOST_OPENSSL=y
        BR2_PACKAGE_UDISKS=y
        BR2_TARGET_ROOTFS_CPIO=y
        BR2_TARGET_ROOTFS_CPIO_GZIP=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        serial = "BR2DISK0001"
        disk_file = os.path.join(self.builddir, "images", "disk.img")
        self.emulator.logfile.write(f"Creating disk image: {disk_file}\n")
        self.emulator.logfile.flush()
        subprocess.check_call(
            ["dd", "if=/dev/zero", f"of={disk_file}", "bs=1M", "count=32"],
            stdout=self.emulator.logfile,
            stderr=self.emulator.logfile)

        img = os.path.join(self.builddir, "images", "rootfs.cpio.gz")
        kern = os.path.join(self.builddir, "images", "Image")
        self.emulator.boot(arch="aarch64",
                           kernel=kern,
                           kernel_cmdline=["console=ttyAMA0"],
                           options=["-M", "virt", "-cpu", "cortex-a57", "-m", "512M",
                                    "-initrd", img,
                                    "-drive", f"file={disk_file},if=none,id=d0,format=raw",
                                    "-device", f"virtio-blk-device,drive=d0,serial={serial}"])
        self.emulator.login()

        disk = "/dev/vda"
        label = "BRDISK"

        # Check the program can execute. The udisks daemon is started
        # on demand through D-Bus activation. Note: udisksctl output is
        # piped to cat, so it doesn't use colors.
        self.assertRunOk("udisksctl help")
        out, ret = self.emulator.run("udisksctl status | cat", timeout=60)
        self.assertEqual(ret, 0)
        devices = [line for line in out if line.split()[-1:] == ["vda"]]
        self.assertEqual(len(devices), 1, "\n".join(out))
        self.assertIn(serial, devices[0])
        self.assertRunOk("pidof udisksd")

        # Create a filesystem, and check udisks sees it.
        self.assertRunOk(f"mkfs.ext4 -q -L {label} {disk}", timeout=30)
        self.assertRunOk("udevadm settle")
        cmd = f"udisksctl info -b {disk} | cat"
        out, ret = self.emulator.run(cmd)
        self.assertEqual(ret, 0)
        info = "\n".join(out)
        self.assertRegex(info, r"(?m)^\s+IdType:\s+ext4$")
        self.assertRegex(info, rf"(?m)^\s+IdLabel:\s+{label}$")

        # Mount the filesystem with udisks.
        out, ret = self.emulator.run(f"udisksctl mount --no-user-interaction -b {disk}",
                                     timeout=30)
        self.assertEqual(ret, 0)
        m = re.match(rf"^Mounted {disk} at (\S+?)\.?$", out[0])
        self.assertIsNotNone(m, out[0])
        mnt = m.group(1)
        self.assertTrue(mnt.endswith(f"/{label}"))
        self.assertRunOk(f"grep -q '^{disk} {mnt} ext4 ' /proc/mounts")
        self.assertRunOk(f"echo 'Hello udisks' > {mnt}/hello.txt")

        # Unmount it, and check the file was written.
        cmd = f"udisksctl unmount --no-user-interaction -b {disk}"
        self.assertRunOk(cmd, timeout=30)
        self.assertRunNotOk(f"grep -q '^{disk} ' /proc/mounts")
        self.assertRunOk(f"mount {disk} /mnt")
        out, ret = self.emulator.run("cat /mnt/hello.txt")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "Hello udisks")
        self.assertRunOk("umount /mnt")

        # Setup a loop device from a file, then delete it.
        self.assertRunOk("dd if=/dev/zero of=/tmp/loop.img bs=1M count=8")
        cmd = "udisksctl loop-setup --no-user-interaction -f /tmp/loop.img"
        out, ret = self.emulator.run(cmd, timeout=30)
        self.assertEqual(ret, 0)
        m = re.match(r"^Mapped file /tmp/loop\.img as (/dev/loop\d+)\.$", out[0])
        self.assertIsNotNone(m, out[0])
        loop_dev = m.group(1)
        out, ret = self.emulator.run(f"udisksctl info -b {loop_dev} | cat")
        self.assertEqual(ret, 0)
        self.assertRegex("\n".join(out), r"(?m)^\s+BackingFile:\s+/tmp/loop\.img$")
        cmd = f"udisksctl loop-delete --no-user-interaction -b {loop_dev}"
        self.assertRunOk(cmd, timeout=30)

        # Operations on a non existing device must fail.
        self.assertRunNotOk("udisksctl info -b /dev/nonexistent")

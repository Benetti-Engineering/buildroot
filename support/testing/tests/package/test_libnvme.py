import os
import subprocess

import infra.basetest


class TestLibNvme(infra.basetest.BRTest):
    # libnvme is tested through the nvme-cli tool, which uses it, on
    # a NVMe controller emulated by Qemu. A Kernel is compiled to
    # enable the NVMe driver.
    kernel_fragment = \
        infra.filepath("tests/package/test_libnvme/linux-nvme.fragment")
    config = \
        f"""
        BR2_aarch64=y
        BR2_TOOLCHAIN_EXTERNAL=y
        BR2_TARGET_GENERIC_GETTY_PORT="ttyAMA0"
        BR2_LINUX_KERNEL=y
        BR2_LINUX_KERNEL_CUSTOM_VERSION=y
        BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE="6.18.21"
        BR2_LINUX_KERNEL_USE_CUSTOM_CONFIG=y
        BR2_LINUX_KERNEL_CUSTOM_CONFIG_FILE="board/qemu/aarch64-virt/linux.config"
        BR2_LINUX_KERNEL_CONFIG_FRAGMENT_FILES="{kernel_fragment}"
        BR2_LINUX_KERNEL_NEEDS_HOST_OPENSSL=y
        BR2_PACKAGE_LIBNVME=y
        BR2_PACKAGE_NVME=y
        BR2_TARGET_ROOTFS_CPIO=y
        BR2_TARGET_ROOTFS_CPIO_GZIP=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        serial = "BR2TEST0001"
        disk_file = os.path.join(self.builddir, "images", "nvme.img")
        self.emulator.logfile.write(f"Creating disk image: {disk_file}\n")
        self.emulator.logfile.flush()
        subprocess.check_call(
            ["dd", "if=/dev/zero", f"of={disk_file}", "bs=1M", "count=16"],
            stdout=self.emulator.logfile,
            stderr=self.emulator.logfile)

        img = os.path.join(self.builddir, "images", "rootfs.cpio.gz")
        kern = os.path.join(self.builddir, "images", "Image")
        self.emulator.boot(arch="aarch64",
                           kernel=kern,
                           kernel_cmdline=["console=ttyAMA0"],
                           options=["-M", "virt", "-cpu", "cortex-a57", "-m", "256M",
                                    "-initrd", img,
                                    "-drive", f"file={disk_file},if=none,id=nvm,format=raw",
                                    "-device", f"nvme,serial={serial},drive=nvm"])
        self.emulator.login()

        ctrl = "/dev/nvme0"
        ns = "/dev/nvme0n1"

        # Check the program can execute.
        self.assertRunOk("nvme version")

        # Check our controller and namespace are listed.
        out, ret = self.emulator.run("nvme list")
        self.assertEqual(ret, 0)
        devices = [line for line in out if line.startswith(ns)]
        self.assertEqual(len(devices), 1)
        self.assertIn(serial, devices[0])

        out, ret = self.emulator.run("nvme list-subsys")
        self.assertEqual(ret, 0)
        self.assertIn("nvme0", "\n".join(out))

        # Check the controller identification.
        out, ret = self.emulator.run(f"nvme id-ctrl {ctrl}")
        self.assertEqual(ret, 0)
        self.assertRegex("\n".join(out), rf"(?m)^sn\s+:\s+{serial}\s*$")
        self.assertRegex("\n".join(out), r"(?m)^mn\s+:\s+QEMU NVMe Ctrl\s*$")

        # Check the namespace identification: 16MB of 512 bytes
        # blocks.
        out, ret = self.emulator.run(f"nvme id-ns {ns}")
        self.assertEqual(ret, 0)
        self.assertRegex("\n".join(out), r"(?m)^nsze\s+:\s+0x8000$")

        # Check the SMART log can be read.
        out, ret = self.emulator.run(f"nvme smart-log {ctrl}")
        self.assertEqual(ret, 0)
        self.assertRegex("\n".join(out), r"(?m)^critical_warning\s+:\s+0$")

        # Write some data to the namespace with a NVMe command, then
        # read it back.
        self.assertRunOk("dd if=/dev/urandom of=/tmp/in.bin bs=512 count=8")
        cmd = f"nvme write {ns} --start-block=16 --block-count=7 " \
            "--data-size=4096 --data=/tmp/in.bin"
        self.assertRunOk(cmd)
        self.assertRunOk(f"nvme flush {ns}")
        cmd = f"nvme read {ns} --start-block=16 --block-count=7 " \
            "--data-size=4096 --data=/tmp/out.bin"
        self.assertRunOk(cmd)
        self.assertRunOk("cmp /tmp/in.bin /tmp/out.bin")

        # The data must also be visible through the block device.
        cmd = f"dd if={ns} of=/tmp/blk.bin bs=512 skip=16 count=8"
        self.assertRunOk(cmd)
        self.assertRunOk("cmp /tmp/in.bin /tmp/blk.bin")

        # A command on a non existing device must fail.
        self.assertRunNotOk("nvme id-ctrl /dev/nvme9")

import os

import infra.basetest


class TestNfsUtils(infra.basetest.BRTest):
    # The nfs-utils package has _LINUX_CONFIG_FIXUPS, so we cannot use
    # the runtime test pre-built Kernel. We need to compile a Kernel
    # to make sure it will include the required configuration. We
    # also add a fragment to enable the NFS client, to mount the
    # export locally.
    kernel_fragment = \
        infra.filepath("tests/package/test_nfs_utils/linux-nfs.fragment")
    rootfs_overlay = \
        infra.filepath("tests/package/test_nfs_utils/rootfs-overlay")
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
        BR2_PACKAGE_NFS_UTILS=y
        BR2_ROOTFS_OVERLAY="{rootfs_overlay}"
        BR2_TARGET_ROOTFS_CPIO=y
        BR2_TARGET_ROOTFS_CPIO_GZIP=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        img = os.path.join(self.builddir, "images", "rootfs.cpio.gz")
        kern = os.path.join(self.builddir, "images", "Image")
        self.emulator.boot(arch="aarch64",
                           kernel=kern,
                           kernel_cmdline=["console=ttyAMA0"],
                           options=["-M", "virt", "-cpu", "cortex-a57", "-m", "256M",
                                    "-initrd", img])
        self.emulator.login()

        export_dir = "/srv/nfs"
        mnt = "/mnt/nfs"

        # The NFS server daemons are supposed to be started by the init
        # scripts. Check the NFS (100003) and mountd (100005) programs
        # are registered to rpcbind.
        out, ret = self.emulator.run("rpcinfo -p")
        self.assertEqual(ret, 0)
        rpcinfo = "\n".join(out)
        self.assertRegex(rpcinfo, r"(?m)^\s*100003\s+3\s+tcp\s+2049\b")
        self.assertRegex(rpcinfo, r"(?m)^\s*100005\s+3\s+tcp\s+\d+\b")

        # Prepare the exported directory, then re-export it.
        self.assertRunOk(f"mkdir -p {export_dir} {mnt}")
        self.assertRunOk(f"mount -t tmpfs tmpfs {export_dir}")
        self.assertRunOk(f"echo 'Hello from server' > {export_dir}/server.txt")
        self.assertRunOk("exportfs -ra")

        out, ret = self.emulator.run("exportfs -v")
        self.assertEqual(ret, 0)
        self.assertIn(export_dir, "\n".join(out))

        out, ret = self.emulator.run("showmount -e 127.0.0.1")
        self.assertEqual(ret, 0)
        self.assertIn(f"{export_dir} 127.0.0.1", out)

        # Mount the export over NFSv3 with the nfs-utils mount helper.
        cmd = f"mount.nfs 127.0.0.1:{export_dir} {mnt} -o vers=3,nolock"
        self.assertRunOk(cmd, timeout=30)
        out, ret = self.emulator.run(f"grep ' {mnt} ' /proc/mounts")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0].split()[2], "nfs")

        # Check files can be read and written from both sides.
        out, ret = self.emulator.run(f"cat {mnt}/server.txt")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "Hello from server")

        self.assertRunOk(f"echo 'Hello from client' > {mnt}/client.txt")
        out, ret = self.emulator.run(f"cat {export_dir}/client.txt")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "Hello from client")

        self.assertRunOk("dd if=/dev/urandom of=/tmp/data.bin bs=1k count=1024")
        self.assertRunOk(f"cp /tmp/data.bin {mnt}/data.bin", timeout=30)
        self.assertRunOk(f"cmp /tmp/data.bin {export_dir}/data.bin")

        # Check the mount appears in the client statistics.
        self.assertRunOk("nfsstat -m | grep -q '^/mnt/nfs from 127.0.0.1:/srv/nfs'")

        # Unmount, then unexport the directory. Mounting must then
        # fail.
        self.assertRunOk(f"umount {mnt}")
        self.assertRunOk(f"exportfs -u 127.0.0.1:{export_dir}")
        out, ret = self.emulator.run("showmount -e 127.0.0.1")
        self.assertEqual(ret, 0)
        self.assertNotIn(f"{export_dir} 127.0.0.1", out)
        cmd = f"mount.nfs 127.0.0.1:{export_dir} {mnt} -o vers=3,nolock,retry=0"
        self.assertRunNotOk(cmd, timeout=60)

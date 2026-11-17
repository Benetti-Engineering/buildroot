import os

import infra.basetest


class TestZlibNg(infra.basetest.BRTest):
    br2_external = [infra.filepath("tests/package/br2-external/zlib-ng")]
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        """
        BR2_PACKAGE_ZLIB=y
        BR2_PACKAGE_ZLIB_NG=y
        BR2_PACKAGE_ZLIB_NG_TEST=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv5",
                           kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login()

        # Check we are using zlib-ng, in zlib compatibility mode.
        out, ret = self.emulator.run("zlib-ng-test version")
        self.assertEqual(ret, 0)
        self.assertRegex(out[0], r"^\d+\.\d+\.\d+.*\.zlib-ng$")

        # Run the in-memory checks (checksums, compression levels,
        # corruption detection).
        out, ret = self.emulator.run("zlib-ng-test selftest")
        self.assertEqual(ret, 0, "\n".join(out))
        self.assertEqual(out[0], "selftest OK")

        # Check interoperability with the BusyBox gzip/gunzip
        # implementation, in both directions.
        msg = "Hello Buildroot zlib-ng"
        self.assertRunOk(f"echo '{msg}' | zlib-ng-test gzwrite /tmp/a.gz")
        out, ret = self.emulator.run("gunzip -c /tmp/a.gz")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], msg)

        self.assertRunOk(f"echo '{msg}' | gzip > /tmp/b.gz")
        out, ret = self.emulator.run("zlib-ng-test gzread /tmp/b.gz")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], msg)

        # Round trip of a larger random file.
        self.assertRunOk("dd if=/dev/urandom of=/tmp/rand.bin bs=1k count=512")
        self.assertRunOk("zlib-ng-test gzwrite /tmp/rand.gz < /tmp/rand.bin")
        self.assertRunOk("gunzip -t /tmp/rand.gz")
        self.assertRunOk("zlib-ng-test gzread /tmp/rand.gz > /tmp/rand.out")
        self.assertRunOk("cmp /tmp/rand.bin /tmp/rand.out")

        # A corrupted file must be rejected.
        self.assertRunOk("cp /tmp/rand.gz /tmp/bad.gz")
        cmd = "printf '\\377\\377\\377\\377' | " \
            "dd of=/tmp/bad.gz bs=1 seek=1000 conv=notrunc"
        self.assertRunOk(cmd)
        self.assertRunNotOk("zlib-ng-test gzread /tmp/bad.gz > /dev/null")

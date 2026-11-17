import os
import time

import infra.basetest


class TestMongoose(infra.basetest.BRTest):
    br2_external = [infra.filepath("tests/package/br2-external/mongoose")]
    rootfs_overlay = \
        infra.filepath("tests/package/test_mongoose/rootfs-overlay")
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        f"""
        BR2_PACKAGE_MONGOOSE=y
        BR2_PACKAGE_MONGOOSE_TEST=y
        BR2_ROOTFS_OVERLAY="{rootfs_overlay}"
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv5",
                           kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login()

        url = "http://127.0.0.1:8000"

        # Start our test HTTP server in background.
        cmd = f"mongoose-test {url} /var/www > /tmp/mongoose.log 2>&1 &"
        self.assertRunOk(cmd)
        time.sleep(1)
        self.assertRunOk("netstat -ltn | grep -q ':8000 '")

        # Check a JSON reply.
        out, ret = self.emulator.run(f"wget -q -O - {url}/api/hello")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], '{"message":"Hello Buildroot"}')

        # Check a POST request with a JSON body.
        cmd = f"wget -q -O - --post-data '{{\"a\": 40, \"b\": 2}}' {url}/api/sum"
        out, ret = self.emulator.run(cmd)
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], '{"sum":42}')

        # Check static files are served from the root directory.
        out, ret = self.emulator.run(f"wget -q -O - {url}/index.html")
        self.assertEqual(ret, 0)
        self.assertEqual(out[0], "Hello from a static page")

        # Requesting a non existing file must fail (HTTP 404).
        out, ret = self.emulator.run(f"wget -O /dev/null {url}/missing 2>&1")
        self.assertNotEqual(ret, 0)
        self.assertIn("404", "\n".join(out))

        # Stop the server.
        self.assertRunOk("kill $!")

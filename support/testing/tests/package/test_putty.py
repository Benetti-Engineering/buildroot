import os

import infra.basetest


class TestPutty(infra.basetest.BRTest):
    passwd = "testpwd"
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        f"""
        BR2_TARGET_GENERIC_ROOT_PASSWD="{passwd}"
        BR2_PACKAGE_DROPBEAR=y
        BR2_PACKAGE_PUTTY=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv5",
                           kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login(self.passwd)

        # Check the programs can execute.
        for prog in ["plink", "pscp", "puttygen"]:
            self.assertRunOk(f"{prog} --version")

        # Generate an Ed25519 key pair with puttygen, without
        # passphrase. We use /dev/urandom to avoid blocking on entropy
        # in the emulator.
        key = "/tmp/key.ppk"
        cmd = "puttygen -t ed25519 -C buildroot-test --random-device /dev/urandom " \
            f"--new-passphrase /dev/null -o {key}"
        self.assertRunOk(cmd, timeout=30)

        # Check the public key, in OpenSSH format.
        out, ret = self.emulator.run(f"puttygen {key} -L")
        self.assertEqual(ret, 0)
        self.assertRegex(out[0], r"^ssh-ed25519 \S+ buildroot-test$")
        pubkey = out[0]

        # Check the key fingerprint.
        out, ret = self.emulator.run(f"puttygen {key} -l")
        self.assertEqual(ret, 0)
        self.assertRegex(out[0], r"^ssh-ed25519 255 SHA256:\S+")

        # Convert the private key to the OpenSSH format.
        cmd = f"puttygen {key} -O private-openssh-new -o /tmp/key.pem"
        self.assertRunOk(cmd)
        self.assertRunOk("grep -q 'BEGIN OPENSSH PRIVATE KEY' /tmp/key.pem")

        # Generate the dropbear host key ourselves, and restart the
        # server, so we know its fingerprint and can pass it to the
        # PuTTY tools running in batch mode.
        hostkey = "/etc/dropbear/dropbear_ed25519_host_key"
        self.assertRunOk(f"dropbearkey -t ed25519 -f {hostkey}", timeout=30)
        self.assertRunOk("/etc/init.d/S50dropbear restart")
        out, ret = self.emulator.run(f"dropbearkey -y -f {hostkey}")
        self.assertEqual(ret, 0)
        fp = [w for w in " ".join(out).split() if w.startswith("SHA256:")]
        self.assertEqual(len(fp), 1, "Cannot find the host key fingerprint")
        ssh_opts = f"-batch -hostkey {fp[0]}"

        # Run a remote command with password authentication.
        cmd = f"plink {ssh_opts} -pw {self.passwd} root@127.0.0.1 echo Hello Buildroot"
        out, ret = self.emulator.run(cmd, timeout=60)
        self.assertEqual(ret, 0)
        self.assertIn("Hello Buildroot", out)

        # Check the remote exit code is propagated.
        cmd = f"plink {ssh_opts} -pw {self.passwd} root@127.0.0.1 exit 3"
        _, ret = self.emulator.run(cmd, timeout=60)
        self.assertEqual(ret, 3)

        # A wrong password must be rejected.
        cmd = f"plink {ssh_opts} -pw wrongpwd root@127.0.0.1 true"
        self.assertRunNotOk(cmd, timeout=60)

        # A wrong host key fingerprint must be rejected.
        cmd = "plink -batch -hostkey SHA256:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA " \
              f"-pw {self.passwd} root@127.0.0.1 true"
        self.assertRunNotOk(cmd, timeout=60)

        # Authorize our key and run a remote command with public key
        # authentication.
        self.assertRunOk("mkdir -p -m 700 /root/.ssh")
        self.assertRunOk(f"echo '{pubkey}' > /root/.ssh/authorized_keys")
        cmd = f"plink {ssh_opts} -i {key} root@127.0.0.1 uname -n"
        out, ret = self.emulator.run(cmd, timeout=60)
        self.assertEqual(ret, 0)
        self.assertIn("buildroot", out)

        # Copy a file with pscp and check its content. Dropbear has no
        # SFTP server, so we force the SCP protocol.
        self.assertRunOk("dd if=/dev/urandom of=/tmp/src.bin bs=1k count=64")
        cmd = f"pscp -scp {ssh_opts} -i {key} /tmp/src.bin root@127.0.0.1:/tmp/dst.bin"
        self.assertRunOk(cmd, timeout=60)
        self.assertRunOk("cmp /tmp/src.bin /tmp/dst.bin")

        # Copy it back from the server.
        cmd = f"pscp -scp {ssh_opts} -i {key} root@127.0.0.1:/tmp/dst.bin /tmp/back.bin"
        self.assertRunOk(cmd, timeout=60)
        self.assertRunOk("cmp /tmp/src.bin /tmp/back.bin")

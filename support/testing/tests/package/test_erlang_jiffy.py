import os

import infra.basetest


class TestErlangJiffy(infra.basetest.BRTest):
    config = infra.basetest.BASIC_TOOLCHAIN_CONFIG + \
        """
        BR2_PACKAGE_ERLANG=y
        BR2_PACKAGE_ERLANG_JIFFY=y
        BR2_TARGET_ROOTFS_CPIO=y
        # BR2_TARGET_ROOTFS_TAR is not set
        """

    def erl_eval(self, expr):
        cmd = f"erl -noshell -eval '{expr}, halt().'"
        out, ret = self.emulator.run(cmd, timeout=60)
        self.assertEqual(ret, 0, "\n".join(out))
        return out

    def test_run(self):
        cpio_file = os.path.join(self.builddir, "images", "rootfs.cpio")
        self.emulator.boot(arch="armv7",
                           kernel="builtin",
                           options=["-initrd", cpio_file])
        self.emulator.login()

        # Check the jiffy application and its NIF can be loaded.
        out = self.erl_eval('{ok, _} = application:ensure_all_started(jiffy), '
                            'io:format("~p~n", [code:which(jiffy)])')
        self.assertRegex(out[0], r'"/usr/lib/erlang/lib/jiffy-[^/]+/ebin/jiffy.beam"')

        # Encode an Erlang term to JSON.
        out = self.erl_eval('io:format("~s~n", [jiffy:encode('
                            '{[{<<"name">>, <<"Buildroot">>}, '
                            '{<<"list">>, [1, 2.5, true, null]}]})])')
        self.assertEqual(out[0], '{"name":"Buildroot","list":[1,2.5,true,null]}')

        # Decode a JSON string to an Erlang map.
        out = self.erl_eval('M = jiffy:decode(<<"{\\"a\\": [1, {\\"b\\": \\"c\\"}]}">>, '
                            '[return_maps]), '
                            'io:format("~p~n", [maps:get(<<"a">>, M)])')
        self.assertEqual(out[0], '[1,#{<<"b">> => <<"c">>}]')

        # Check a round trip of a map with unicode content.
        out = self.erl_eval('T = #{<<"k">> => [<<"\\x{e9}"/utf8>>, -42, 1.0e10]}, '
                            'T = jiffy:decode(jiffy:encode(T), [return_maps]), '
                            'io:format("roundtrip ok~n")')
        self.assertEqual(out[0], "roundtrip ok")

        # Check an invalid JSON input raises an error.
        out = self.erl_eval('try jiffy:decode(<<"{broken">>) of '
                            '_ -> io:format("no error~n") '
                            'catch error:{_, _} -> io:format("invalid json~n") end')
        self.assertEqual(out[0], "invalid json")

import io

import libconf

CONFIG = """
# Example application configuration
application:
{
  name = "Buildroot";
  version = 2024;
  ratio = 0.75;
  enabled = true;
  big = 12345678901L;
  ports = [ 80, 443 ];
  misc = ( "text", 42, { nested = "value"; } );
};
"""

cfg = libconf.loads(CONFIG)
app = cfg["application"]
assert app["name"] == "Buildroot"
assert app.version == 2024
assert app["ratio"] == 0.75
assert app["enabled"] is True
assert app["big"] == 12345678901
assert app["ports"] == [80, 443]
assert app["misc"][0] == "text"
assert app["misc"][1] == 42
assert app["misc"][2]["nested"] == "value"

# Check a round trip: dump the configuration and parse it again.
dumped = libconf.dumps(cfg)
assert libconf.loads(dumped) == cfg

# Check the file-like interface.
with io.StringIO(CONFIG) as f:
    assert libconf.load(f) == cfg

# A syntax error must raise an exception.
try:
    libconf.loads("broken = ;")
except libconf.ConfigParseError:
    pass
else:
    raise AssertionError("parse error was not detected")

print("libconf test OK")

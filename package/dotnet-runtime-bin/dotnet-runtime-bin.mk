################################################################################
#
# dotnet-runtime-bin
#
################################################################################

DOTNET_RUNTIME_BIN_VERSION = 11.0.0

ifeq ($(BR2_TOOLCHAIN_USES_MUSL),y)
DOTNET_RUNTIME_BIN_LIBC = musl-
endif

ifeq ($(BR2_aarch64),y)
DOTNET_RUNTIME_BIN_ARCH = arm64
else ifeq ($(BR2_arm),y)
DOTNET_RUNTIME_BIN_ARCH = arm
else ifeq ($(BR2_x86_64),y)
DOTNET_RUNTIME_BIN_ARCH = x64
endif

DOTNET_RUNTIME_BIN_SITE = https://builds.dotnet.microsoft.com/dotnet/Runtime/$(DOTNET_RUNTIME_BIN_VERSION)
DOTNET_RUNTIME_BIN_SOURCE = dotnet-runtime-$(DOTNET_RUNTIME_BIN_VERSION)-linux-$(DOTNET_RUNTIME_BIN_LIBC)$(DOTNET_RUNTIME_BIN_ARCH).tar.gz
DOTNET_RUNTIME_BIN_STRIP_COMPONENTS = 0
DOTNET_RUNTIME_BIN_LICENSE = MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, \
	Zlib, CC0-1.0, Unicode-DFS-2016, Public Domain
DOTNET_RUNTIME_BIN_LICENSE_FILES = LICENSE.txt ThirdPartyNotices.txt
DOTNET_RUNTIME_BIN_PROVIDES = dotnet-runtime

# /usr/share/dotnet is the default install location, where both the
# dotnet host and the application hosts find the runtime. The runtime
# loads its native libraries from its own directory.
#
# libcoreclrtraceptprovider.so is only used for LTTng tracing and the
# runtime doesn't need it: remove it, so that lttng-libust, that it is
# linked against, is not needed.
define DOTNET_RUNTIME_BIN_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/share/dotnet $(TARGET_DIR)/usr/bin
	cp -a $(@D)/dotnet $(@D)/host $(@D)/shared $(TARGET_DIR)/usr/share/dotnet/
	rm -f $(TARGET_DIR)/usr/share/dotnet/shared/Microsoft.NETCore.App/$(DOTNET_RUNTIME_BIN_VERSION)/libcoreclrtraceptprovider.so
	ln -sf ../share/dotnet/dotnet $(TARGET_DIR)/usr/bin/dotnet
endef

$(eval $(generic-package))

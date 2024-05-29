################################################################################
#
# dotnet-runtime-prebuilt
#
################################################################################

DOTNET_RUNTIME_PREBUILT_VERSION = 8.0.6
DOTNET_RUNTIME_PREBUILT_LICENSE = MIT
DOTNET_RUNTIME_PREBUILT_LICENSE_FILES = LICENSE.txt

# Set download URL and runtime identifier
# See https://docs.microsoft.com/en-us/dotnet/core/rid-catalog
# for the list of supported runtimes
# download_link="$azure_feed/Runtime/$specific_version/dotnet-runtime-$specific_version-$osname-$normalized_architecture.tar.gz"

AZURE_FEED = https://dotnetcli.azureedge.net/dotnet
DOTNET_RUNTIME_PREBUILT_SITE = $(AZURE_FEED)/Runtime/$(DOTNET_RUNTIME_PREBUILT_VERSION)

ifeq ($(BR2_aarch64),y)
ifeq ($(BR2_TOOLCHAIN_USES_MUSL),y)
DOTNET_RUNTIME_PREBUILT_IDENTIFIER = linux-musl-arm64
else
DOTNET_RUNTIME_PREBUILT_IDENTIFIER = linux-arm64
endif
else ifeq ($(BR2_arm),y)
ifeq ($(BR2_TOOLCHAIN_USES_MUSL),y)
DOTNET_RUNTIME_PREBUILT_IDENTIFIER = linux-musl-arm
else
DOTNET_RUNTIME_PREBUILT_IDENTIFIER = linux-arm
endif
else ifeq ($(BR2_x86_64),y)
ifeq ($(BR2_TOOLCHAIN_USES_MUSL),y)
DOTNET_RUNTIME_PREBUILT_IDENTIFIER = linux-musl-x64
else
DOTNET_RUNTIME_PREBUILT_IDENTIFIER = linux-x64
endif
endif

DOTNET_RUNTIME_PREBUILT_SOURCE = dotnet-runtime-$(DOTNET_RUNTIME_PREBUILT_VERSION)-$(DOTNET_RUNTIME_PREBUILT_IDENTIFIER).tar.gz

# Runtime could be installed in the global location [/usr/share/dotnet] and
# will be picked up automatically.
# As alternative, it is possible to use the DOTNET_ROOT environment variable
# to specify the runtime location or register the runtime location in
# [/etc/dotnet/install_location]
# This script will install runtime to
# /usr/share/dotnet
define DOTNET_RUNTIME_PREBUILT_INSTALL_TARGET_CMDS
	cp -Rf $(@D)/. $(TARGET_DIR)/usr/share/dotnet
	mkdir -p $(TARGET_DIR)/etc/dotnet
	echo "/usr/share/dotnet" > $(TARGET_DIR)/etc/dotnet/install_location

	# Export dotnet to PATH and libraries to LD_LIBRARY_PATH
	$(INSTALL) -m 0755 -D $(DOTNET_RUNTIME_PREBUILT_PKGDIR)/dotnet-runtime-prebuilt.sh \
		$(TARGET_DIR)/etc/profile.d/dotnet-runtime-prebuilt.sh
endef

$(eval $(generic-package))

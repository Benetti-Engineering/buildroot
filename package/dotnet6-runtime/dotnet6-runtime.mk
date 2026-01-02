################################################################################
#
# dotnet6-runtime
#
################################################################################

DOTNET6_RUNTIME_VERSION = 6.0.22
DOTNET6_RUNTIME_SITE = $(call github,dotnet,runtime,v$(DOTNET6_RUNTIME_VERSION))
DOTNET6_RUNTIME_LICENSE = MIT
DOTNET6_RUNTIME_LICENSE_FILES = LICENSE.TXT
DOTNET6_RUNTIME_DEPENDENCIES = host-cmake libzlib openssl libcurl icu libkrb5 lttng-libust

ifeq ($(BR2_aarch64),y)
DOTNET6_RUNTIME_ARCH = arm64
else ifeq ($(BR2_arm),y)
DOTNET6_RUNTIME_ARCH = arm
# Set FPU type
DOTNET6_RUNTIME_ARM_FPU_TYPE = $(BR2_GCC_TARGET_FPU)
ifeq ($(BR2_ARM_FPU_VFPV3)$(BR2_ARM_FPU_VFPV4),y)
# Set 0x07 if 32 fpu registers are used
DOTNET6_RUNTIME_ARM_FPU_CAPABILITY = 0x07
else ifeq ($(BR2_ARM_FPU_VFPV3D16)$(BR2_ARM_FPU_VFPV4D16),y)
# Set 0x03 if 32 fpu registers are used
DOTNET6_RUNTIME_ARM_FPU_CAPABILITY = 0x03
endif
endif

ifeq ($(BR2_TOOLCHAIN_BUILDROOT),y)
DOTNET6_RUNTIME_TOOLCHAIN_PREFIX = $(GNU_TARGET_NAME)
else
DOTNET6_RUNTIME_TOOLCHAIN_PREFIX = $(TOOLCHAIN_EXTERNAL_PREFIX)
endif

ifeq ($(BR2_ENABLE_DEBUG),y)
DOTNET6_RUNTIME_BUILD_CONFIGURATION = Debug
else
DOTNET6_RUNTIME_BUILD_CONFIGURATION = Release
endif

DOTNET6_RUNTIME_CMAKEARGS = --cmakeargs "-DCMAKE_TOOLCHAIN_FILE="$(HOST_DIR)/share/buildroot/toolchainfile.cmake"" \
		--cmakeargs "-DCMAKE_INSTALL_RUNSTATEDIR="/run"" \
		--cmakeargs "-DCMAKE_CXX_COMPILER_TARGET=$(DOTNET6_RUNTIME_TOOLCHAIN_PREFIX)" \
		--cmakeargs "-DTOOLCHAIN=$(DOTNET6_RUNTIME_TOOLCHAIN_PREFIX)"

# Append FPU specific defines
ifeq ($(BR2_arm),y)
		DOTNET6_RUNTIME_CMAKEARGS += \
		--cmakeargs "-DCLR_ARM_FPU_TYPE=$(DOTNET6_RUNTIME_ARM_FPU_TYPE)" \
		--cmakeargs "-DCLR_ARM_FPU_CAPABILITY=$(DOTNET6_RUNTIME_ARM_FPU_CAPABILITY)"
endif

define DOTNET6_RUNTIME_BUILD_CMDS
	cd $(@D) && PATH=$(BR_PATH) ROOTFS_DIR=$(HOST_DIR) \
		$(SHELL) ./build.sh --subset clr.jit+clr.runtime+libs --verbosity diag \
		--arch $(DOTNET6_RUNTIME_ARCH) --gcc --cross --skipcrossarchnative \
		--configuration $(DOTNET6_RUNTIME_BUILD_CONFIGURATION) \
		$(DOTNET6_RUNTIME_CMAKEARGS)
endef

define DOTNET6_RUNTIME_INSTALL_TARGET_CMDS
	# Copy all .dll libraries to target directory
	cp -Rf $(@D)/artifacts/bin/testhost/net6.0-Linux-$(DOTNET6_RUNTIME_BUILD_CONFIGURATION)-$(DOTNET6_RUNTIME_ARCH)/. \
		$(TARGET_DIR)/usr/share/dotnet
	# Remove all .dbg, .pdb, .h, .a, .xml files from target
	find $(TARGET_DIR)/usr/share/dotnet/ \
		-type f \( -name "*.dbg" -o -name "*.pdb" -o -name "*.h" \
		-o -name "*.a" -o -name "*.xml" \) -delete

	# Create /etc/dotnet/install_location file to point to dotnet
	mkdir -p $(TARGET_DIR)/etc/dotnet
	echo /usr/share/dotnet > $(TARGET_DIR)/etc/dotnet/install_location
	# Export dotnet to PATH and libraries to LD_LIBRARY_PATH
	$(INSTALL) -m 0755 -D $(DOTNET6_RUNTIME_PKGDIR)/dotnet6-runtime.sh \
		$(TARGET_DIR)/etc/profile.d/dotnet6-runtime.sh
endef

$(eval $(generic-package))

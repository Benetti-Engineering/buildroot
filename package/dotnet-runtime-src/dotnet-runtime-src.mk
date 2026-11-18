################################################################################
#
# dotnet-runtime-src
#
################################################################################

ifeq ($(BR2_PACKAGE_DOTNET_RUNTIME_6_0),y)
DOTNET_RUNTIME_SRC_VERSION = 6.0.36
else ifeq ($(BR2_PACKAGE_DOTNET_RUNTIME_8_0),y)
DOTNET_RUNTIME_SRC_VERSION = 8.0.34
else
DOTNET_RUNTIME_SRC_VERSION = 10.0.15
endif
DOTNET_RUNTIME_SRC_SITE = $(call github,dotnet,runtime,v$(DOTNET_RUNTIME_SRC_VERSION))
DOTNET_RUNTIME_SRC_LICENSE = MIT
DOTNET_RUNTIME_SRC_LICENSE_FILES = LICENSE.TXT THIRD-PARTY-NOTICES.TXT
DOTNET_RUNTIME_SRC_PROVIDES = dotnet-runtime
DOTNET_RUNTIME_SRC_DEPENDENCIES = \
	$(BR2_CMAKE_HOST_DEPENDENCY) \
	host-python3 \
	icu \
	libkrb5 \
	lttng-libust \
	openssl

# Before 10.0, the native libraries are linked against the system zlib
ifeq ($(BR2_PACKAGE_DOTNET_RUNTIME_10_0),)
DOTNET_RUNTIME_SRC_DEPENDENCIES += zlib
endif

ifeq ($(BR2_TOOLCHAIN_USES_MUSL),y)
DOTNET_RUNTIME_SRC_LIBC = musl-
endif

ifeq ($(BR2_aarch64),y)
DOTNET_RUNTIME_SRC_ARCH = arm64
else ifeq ($(BR2_arm),y)
DOTNET_RUNTIME_SRC_ARCH = arm
else ifeq ($(BR2_x86_64),y)
DOTNET_RUNTIME_SRC_ARCH = x64
endif

DOTNET_RUNTIME_SRC_RID = linux-$(DOTNET_RUNTIME_SRC_LIBC)$(DOTNET_RUNTIME_SRC_ARCH)

# Only the native parts of the runtime (CoreCLR, the native libraries
# and the hosts) are built from source, with CMake. The managed
# libraries are built from C# with MSBuild, which needs a .NET SDK, so
# they are taken from the official runtime tarball: they are
# architecture independent, and built from the same sources.
DOTNET_RUNTIME_SRC_MANAGED_SOURCE = \
	dotnet-runtime-$(DOTNET_RUNTIME_SRC_VERSION)-$(DOTNET_RUNTIME_SRC_RID).tar.gz
DOTNET_RUNTIME_SRC_EXTRA_DOWNLOADS = \
	https://builds.dotnet.microsoft.com/dotnet/Runtime/$(DOTNET_RUNTIME_SRC_VERSION)/$(DOTNET_RUNTIME_SRC_MANAGED_SOURCE)

ifeq ($(BR2_PACKAGE_DOTNET_RUNTIME_6_0),y)
DOTNET_RUNTIME_SRC_LIBS_SUBDIR = src/libraries/Native/Unix
else
DOTNET_RUNTIME_SRC_LIBS_SUBDIR = src/native/libs
endif

# The tools are looked up from the compiler target tuple, that the
# Buildroot toolchain file doesn't set. tryrun.cmake provides the
# results of the checks that can't be run when cross-compiling.
DOTNET_RUNTIME_SRC_CMAKE_ENV = \
	PATH=$(BR_PATH) \
	CLR_AR="$(TARGET_AR)" \
	CLR_NM="$(TARGET_NM)" \
	CLR_RANLIB="$(TARGET_RANLIB)" \
	CLR_STRINGS="$(TARGET_CROSS)strings" \
	CLR_OBJDUMP="$(TARGET_OBJDUMP)" \
	CLR_READELF="$(TARGET_READELF)" \
	CLR_OBJCOPY="$(TARGET_OBJCOPY)" \
	TARGET_BUILD_ARCH=$(DOTNET_RUNTIME_SRC_ARCH) \
	ROOTFS_DIR=$(STAGING_DIR)

DOTNET_RUNTIME_SRC_CMAKE_OPTS = \
	-C $(@D)/eng/native/tryrun.cmake \
	-DCMAKE_TOOLCHAIN_FILE=$(HOST_DIR)/share/buildroot/toolchainfile.cmake \
	-DCMAKE_COLOR_MAKEFILE=OFF \
	-DCLR_CMAKE_PGO_INSTRUMENT=0 \
	-DCLR_CMAKE_PGO_OPTIMIZE=0 \
	-DFEATURE_DISTRO_AGNOSTIC_SSL=0 \
	-DCLI_CMAKE_PKG_RID=$(DOTNET_RUNTIME_SRC_RID) \
	-DCLI_CMAKE_FALLBACK_OS=linux \
	-DCLI_CMAKE_COMMIT_HASH=N/A

ifeq ($(BR2_PACKAGE_DOTNET_RUNTIME_6_0),y)
DOTNET_RUNTIME_SRC_CMAKE_OPTS += \
	-DCLI_CMAKE_HOST_VER=$(DOTNET_RUNTIME_SRC_VERSION) \
	-DCLI_CMAKE_COMMON_HOST_VER=$(DOTNET_RUNTIME_SRC_VERSION) \
	-DCLI_CMAKE_HOST_FXR_VER=$(DOTNET_RUNTIME_SRC_VERSION) \
	-DCLI_CMAKE_HOST_POLICY_VER=$(DOTNET_RUNTIME_SRC_VERSION)
endif

ifeq ($(BR2_arm),y)
# CLR_ARM_FPU_CAPABILITY is 0x7 with 32 double-precision registers,
# 0x3 with only 16 of them.
ifeq ($(BR2_ARM_FPU_VFPV3D16)$(BR2_ARM_FPU_VFPV4D16),y)
DOTNET_RUNTIME_SRC_CMAKE_OPTS += -DCLR_ARM_FPU_CAPABILITY=0x3
else
DOTNET_RUNTIME_SRC_CMAKE_OPTS += -DCLR_ARM_FPU_CAPABILITY=0x7
endif
DOTNET_RUNTIME_SRC_CMAKE_OPTS += \
	-DCLR_ARM_FPU_TYPE=$(call qstrip,$(BR2_GCC_TARGET_FPU))
endif

# Some unused template code doesn't build with gcc >= 14
ifeq ($(BR2_TOOLCHAIN_GCC_AT_LEAST_14),y)
DOTNET_RUNTIME_SRC_CMAKE_OPTS += -DCMAKE_CXX_FLAGS="$(TARGET_CXXFLAGS) -Wno-template-body"
endif

# The version files are normally generated with MSBuild. Generate them
# like build.sh does when MSBuild is not available, but with the real
# version, that the hosts report and use.
DOTNET_RUNTIME_SRC_VERSION_LIST = $(subst ., ,$(DOTNET_RUNTIME_SRC_VERSION))
DOTNET_RUNTIME_SRC_VERSION_MAJOR = $(word 1,$(DOTNET_RUNTIME_SRC_VERSION_LIST))
DOTNET_RUNTIME_SRC_VERSION_MINOR = $(word 2,$(DOTNET_RUNTIME_SRC_VERSION_LIST))
DOTNET_RUNTIME_SRC_VERSION_PATCH = $(word 3,$(DOTNET_RUNTIME_SRC_VERSION_LIST))

# $(1): runtime_version.h path
define DOTNET_RUNTIME_SRC_RUNTIME_VERSION_H
	printf '#define %s %s\n' \
		RuntimeAssemblyMajorVersion $(DOTNET_RUNTIME_SRC_VERSION_MAJOR) \
		RuntimeAssemblyMinorVersion $(DOTNET_RUNTIME_SRC_VERSION_MINOR) \
		RuntimeFileMajorVersion $(DOTNET_RUNTIME_SRC_VERSION_MAJOR) \
		RuntimeFileMinorVersion $(DOTNET_RUNTIME_SRC_VERSION_MINOR) \
		RuntimeFileBuildVersion $(DOTNET_RUNTIME_SRC_VERSION_PATCH) \
		RuntimeFileRevisionVersion 0 \
		RuntimeProductMajorVersion $(DOTNET_RUNTIME_SRC_VERSION_MAJOR) \
		RuntimeProductMinorVersion $(DOTNET_RUNTIME_SRC_VERSION_MINOR) \
		RuntimeProductPatchVersion $(DOTNET_RUNTIME_SRC_VERSION_PATCH) \
		RuntimeProductVersion $(DOTNET_RUNTIME_SRC_VERSION) \
		> $(1)
endef

ifeq ($(BR2_PACKAGE_DOTNET_RUNTIME_6_0),y)
define DOTNET_RUNTIME_SRC_VERSION_FILES
	mkdir -p $(@D)/artifacts/obj/coreclr
	$(call DOTNET_RUNTIME_SRC_RUNTIME_VERSION_H,$(@D)/artifacts/obj/coreclr/runtime_version.h)
	for c in coreclr libs corehost; do \
		mkdir -p $(@D)/buildroot-build/$$c && \
		echo 'static char sccsid[] __attribute__((used)) = "@(#)Version $(DOTNET_RUNTIME_SRC_VERSION)";' \
			> $(@D)/buildroot-build/$$c/version.c || exit 1; \
	done
endef
else
define DOTNET_RUNTIME_SRC_VERSION_FILES
	mkdir -p $(@D)/artifacts/obj
	cd $(@D) && $(SHELL) ./eng/native/version/copy_version_files.sh
	$(call DOTNET_RUNTIME_SRC_RUNTIME_VERSION_H,$(@D)/artifacts/obj/runtime_version.h)
endef
endif
DOTNET_RUNTIME_SRC_PRE_CONFIGURE_HOOKS += DOTNET_RUNTIME_SRC_VERSION_FILES

# $(1): component name, $(2): CMake source directory
define DOTNET_RUNTIME_SRC_CMAKE_CONFIGURE
	mkdir -p $(@D)/buildroot-build/$(1)
	cd $(@D)/buildroot-build/$(1) && rm -f CMakeCache.txt && \
		$(DOTNET_RUNTIME_SRC_CMAKE_ENV) $(BR2_CMAKE) $(@D)/$(2) \
		$(DOTNET_RUNTIME_SRC_CMAKE_OPTS) \
		-DCMAKE_INSTALL_PREFIX=$(@D)/buildroot-install/$(1)
endef

define DOTNET_RUNTIME_SRC_CONFIGURE_CMDS
	$(call DOTNET_RUNTIME_SRC_CMAKE_CONFIGURE,coreclr,src/coreclr)
	$(call DOTNET_RUNTIME_SRC_CMAKE_CONFIGURE,libs,$(DOTNET_RUNTIME_SRC_LIBS_SUBDIR))
	$(call DOTNET_RUNTIME_SRC_CMAKE_CONFIGURE,corehost,src/native/corehost)
endef

# $(1): component name, $(2): CMake targets
define DOTNET_RUNTIME_SRC_CMAKE_BUILD
	$(DOTNET_RUNTIME_SRC_CMAKE_ENV) $(BR2_CMAKE) \
		--build $(@D)/buildroot-build/$(1) -j$(PARALLEL_JOBS) \
		$(if $(2),--target $(2))
endef

# $(1): component name, $(2): CMake install components
define DOTNET_RUNTIME_SRC_CMAKE_INSTALL
	$(if $(2),$(foreach c,$(2),\
		$(BR2_CMAKE) --install $(@D)/buildroot-build/$(1) --component $(c)$(sep)),\
		$(BR2_CMAKE) --install $(@D)/buildroot-build/$(1))
endef

define DOTNET_RUNTIME_SRC_BUILD_CMDS
	$(call DOTNET_RUNTIME_SRC_CMAKE_BUILD,coreclr,runtime)
	$(call DOTNET_RUNTIME_SRC_CMAKE_INSTALL,coreclr,jit runtime debug)
	$(call DOTNET_RUNTIME_SRC_CMAKE_BUILD,libs)
	$(call DOTNET_RUNTIME_SRC_CMAKE_INSTALL,libs)
	$(call DOTNET_RUNTIME_SRC_CMAKE_BUILD,corehost)
	$(call DOTNET_RUNTIME_SRC_CMAKE_INSTALL,corehost)
endef

DOTNET_RUNTIME_SRC_INSTALL_DIRS = \
	$(@D)/buildroot-install/coreclr/sharedFramework \
	$(@D)/buildroot-install/libs \
	$(@D)/buildroot-install/corehost/corehost

# /usr/share/dotnet is the default install location, where both the
# dotnet host and the application hosts find the runtime. Only the
# managed libraries and the metadata files are kept from the official
# runtime tarball: each of its native binaries is replaced by the one
# built from source, so that the same set of files is installed.
define DOTNET_RUNTIME_SRC_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/share/dotnet $(TARGET_DIR)/usr/bin
	$(call suitable-extractor,$(DOTNET_RUNTIME_SRC_MANAGED_SOURCE)) \
		$(DOTNET_RUNTIME_SRC_DL_DIR)/$(DOTNET_RUNTIME_SRC_MANAGED_SOURCE) | \
		$(TAR) -C $(TARGET_DIR)/usr/share/dotnet $(TAR_OPTIONS) - \
		./dotnet ./host ./shared
	cd $(TARGET_DIR)/usr/share/dotnet && \
	for f in dotnet $$(find host shared -type f \
		\( -name '*.so' -o -name createdump \)); do \
		src=$$(for d in $(DOTNET_RUNTIME_SRC_INSTALL_DIRS); do \
			ls $$d/$${f##*/} 2>/dev/null; done | head -n 1); \
		if [ -z "$$src" ]; then \
			echo "$${f} was not built" >&2; exit 1; \
		fi; \
		$(INSTALL) -m 0755 $$src $$f || exit 1; \
	done
	ln -sf ../share/dotnet/dotnet $(TARGET_DIR)/usr/bin/dotnet
endef

$(eval $(generic-package))

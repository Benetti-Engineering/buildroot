################################################################################
#
# zlib-ng
#
################################################################################

ZLIB_NG_VERSION = 2.3.3
ZLIB_NG_SITE = $(call github,zlib-ng,zlib-ng,$(ZLIB_NG_VERSION))
ZLIB_NG_LICENSE = Zlib
ZLIB_NG_LICENSE_FILES = LICENSE.md
ZLIB_NG_INSTALL_STAGING = YES
ZLIB_NG_PROVIDES = zlib

# Build with zlib compatible API, gzFile support and optimizations on
ZLIB_NG_CONF_OPTS += \
	-DCMAKE_C_COMPILER_TARGET=$(BR2_ARCH) \
	-DWITH_GZFILEOP=1 \
	-DWITH_OPTIM=1 \
	-DZLIB_COMPAT=1 \
	-DZLIB_ENABLE_TESTS=OFF

# Enable ACLE on ARM
ifeq ($(BR2_arm),y)
ZLIB_NG_CONF_OPTS += -DWITH_ACLE=1
# When CMAKE_C_FLAGS doesn't contain -mfloat-abi, zlib-ng tries to
# auto-detect it and adds -mfloat-abi=softfp to the whole library as
# soon as the compiler accepts it. On a soft-float target, this makes
# the compiler emit VFP instructions in generic code, leading to an
# "Illegal instruction" at runtime. So pass the configured float ABI.
ZLIB_NG_CONF_OPTS += \
	-DCMAKE_C_FLAGS="$(TARGET_CFLAGS) -mfloat-abi=$(call qstrip,$(BR2_GCC_TARGET_FLOAT_ABI))"
endif

ifeq ($(BR2_ARM_CPU_HAS_NEON)$(BR2_aarch64),y)
ZLIB_NG_CONF_OPTS += -DWITH_NEON=ON
else
ZLIB_NG_CONF_OPTS += -DWITH_NEON=OFF
endif

ifeq ($(BR2_powerpc_power8):$(BR2_POWERPC_SOFT_FLOAT),y:)
ZLIB_NG_CONF_OPTS += -DWITH_POWER8=ON
else
ZLIB_NG_CONF_OPTS += -DWITH_POWER8=OFF
endif

ifeq ($(BR2_powerpc_power9):$(BR2_POWERPC_SOFT_FLOAT),y:)
ZLIB_NG_CONF_OPTS += -DWITH_POWER9=ON
else
ZLIB_NG_CONF_OPTS += -DWITH_POWER9=OFF
endif

$(eval $(cmake-package))

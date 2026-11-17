################################################################################
#
# libnspr-test
#
################################################################################

LIBNSPR_TEST_DEPENDENCIES = libnspr host-pkgconf

define LIBNSPR_TEST_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) -o $(@D)/libnspr-test \
		$(LIBNSPR_TEST_PKGDIR)/libnspr-test.c \
		`$(PKG_CONFIG_HOST_BINARY) --cflags --libs nspr` \
		$(TARGET_LDFLAGS)
endef

define LIBNSPR_TEST_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/libnspr-test $(TARGET_DIR)/usr/bin/libnspr-test
endef

$(eval $(generic-package))

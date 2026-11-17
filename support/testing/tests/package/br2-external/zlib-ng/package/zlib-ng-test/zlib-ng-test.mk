################################################################################
#
# zlib-ng-test
#
################################################################################

ZLIB_NG_TEST_DEPENDENCIES = zlib-ng

define ZLIB_NG_TEST_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) -o $(@D)/zlib-ng-test \
		$(ZLIB_NG_TEST_PKGDIR)/zlib-ng-test.c \
		$(TARGET_LDFLAGS) -lz
endef

define ZLIB_NG_TEST_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/zlib-ng-test $(TARGET_DIR)/usr/bin/zlib-ng-test
endef

$(eval $(generic-package))

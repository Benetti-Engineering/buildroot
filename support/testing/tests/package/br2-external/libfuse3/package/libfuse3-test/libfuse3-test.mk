################################################################################
#
# libfuse3-test
#
################################################################################

LIBFUSE3_TEST_DEPENDENCIES = libfuse3 host-pkgconf

define LIBFUSE3_TEST_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) -o $(@D)/fuse3-hello \
		$(LIBFUSE3_TEST_PKGDIR)/fuse3-hello.c \
		`$(PKG_CONFIG_HOST_BINARY) --cflags --libs fuse3` \
		$(TARGET_LDFLAGS)
endef

define LIBFUSE3_TEST_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/fuse3-hello $(TARGET_DIR)/usr/bin/fuse3-hello
endef

$(eval $(generic-package))

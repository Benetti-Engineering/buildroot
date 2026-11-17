################################################################################
#
# mongoose-test
#
################################################################################

MONGOOSE_TEST_DEPENDENCIES = mongoose

define MONGOOSE_TEST_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) -o $(@D)/mongoose-test \
		$(MONGOOSE_TEST_PKGDIR)/mongoose-test.c \
		$(TARGET_LDFLAGS) -lmongoose
endef

define MONGOOSE_TEST_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/mongoose-test $(TARGET_DIR)/usr/bin/mongoose-test
endef

$(eval $(generic-package))

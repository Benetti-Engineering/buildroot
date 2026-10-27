################################################################################
#
# mali-driver
#
################################################################################

MALI_DRIVER_VERSION = 27e42e6c5c8fb33ac36a39e5eb6146756c2e5fa0
MALI_DRIVER_SITE = $(call github,bootlin,mali-driver,$(MALI_DRIVER_VERSION))
MALI_DRIVER_DEPENDENCIES = linux
MALI_DRIVER_LICENSE = GPL-2.0
MALI_DRIVER_LICENSE_FILES = LICENSE
MALI_DRIVER_MODULE_SUBDIRS = r8p0/drivers/gpu/arm/midgard

$(eval $(kernel-module))
$(eval $(generic-package))

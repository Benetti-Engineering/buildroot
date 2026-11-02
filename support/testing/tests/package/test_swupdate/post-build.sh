#!/usr/bin/env bash
set -e
ARTIFACT_NAME="RUNTIME_TEST_ARTIFACT_NAME"

generate_swupdate_bootstrap_artifact() {
  "${HOST_DIR}"/bin/swugenerator \
    -t \
    -s ${TARGET_DIR}/etc/swupdate/sw-description \
    -o "${ARTIFACT_NAME}" create

#    -o "${TARGET_DIR}"/var/lib/swupdate/bootstrap.swupdate create
}

generate_swupdate_bootstrap_artifact

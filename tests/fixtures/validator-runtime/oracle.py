"""Collection-only interface for the validator characterization oracle."""


def inventory(source):
    pass


def matches(expected, actual):
    pass


def valid_manifest(record, payload_sha256, configuration_sha256):
    pass

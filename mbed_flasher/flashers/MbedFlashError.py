"""
Customized Errors
"""


class MbedFlashError(Exception):
    """
    class MbedFlashError can be used as a general error for mbed-flasher
    """
    def __init__(self, message="MbedFlashError"):
        Exception.__init__(self, message)


class MountPointDisappearTimeoutError(MbedFlashError):
    """
    MountPointDisappearTimeoutError
    """
    def __init__(self, message="MountPointDisappearTimeoutError"):
        MbedFlashError.__init__(self, message)

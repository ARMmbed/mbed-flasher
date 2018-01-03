class MbedFlashError(Exception):
    def __init__(self, message="MbedFlashError"):
        super(MbedFlashError, self).__init__(message)


class MountPointDisappearTimeoutError(MbedFlashError):
    def __init__(self, message="MountPointDisappearTimeoutError"):
        super(MountPointDisappearTimeoutError, self).__init__(message)
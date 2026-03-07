from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("flux-notifier")
except PackageNotFoundError:
    __version__ = "0.0.0"

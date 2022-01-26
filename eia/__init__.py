from importlib import metadata
from loguru import logger

__version__ = metadata.version("pyeia")

# Do not pass logs to application; it is always possible to enable logging
# at the application level, e.g. logger.enable("eia")
logger.disable(__name__)

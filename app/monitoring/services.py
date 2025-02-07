import logfire
import logging


from app.core.logging_config import setup_logging


setup_logging(
    log_level=logging.DEBUG,
)

logger = logging.getLogger()  # Get the root logger


def configure_logfire():
    logfire.configure(
        # name="Tweakr",7
    )
    return logfire


def request_attributes_mapper(request, attributes):
    if attributes["errors"]:
        # Only log validation errors, not valid arguments
        return {
            "errors": attributes["errors"],
            "my_custom_attribute": ...,
        }
    else:
        # Don't log anything for valid requests
        return None


monitoring = configure_logfire()


logger.addHandler(monitoring.LogfireLoggingHandler())

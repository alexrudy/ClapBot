import itertools
import logging

logger = logging.getLogger(__name__)


def safe_iterator(iterable, limit):
    """Safe iterator, which just logs problematic entries."""
    iterator = itertools.islice(iterable, limit)
    while True:
        try:
            gen = next(iterator)
        except StopIteration:
            break
        except Exception as e:    # pylint: disable=broad-except
            logger.exception(f"Exception in craigslist result: {e}")
        else:
            yield gen
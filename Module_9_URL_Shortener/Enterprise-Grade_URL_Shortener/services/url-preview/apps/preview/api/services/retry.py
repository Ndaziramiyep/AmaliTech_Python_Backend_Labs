import logging
import random
import time

logger = logging.getLogger(__name__)


def call_with_backoff(func, *, max_attempts: int, base_delay: float, retryable_exceptions):
    """Calls func() up to max_attempts times total, re-raising the last exception if every attempt fails.

    Sleeps `base_delay * 2**attempt + random.uniform(0, base_delay)` between
    attempts (exponential backoff with jitter) so a burst of retries against
    the same flaky domain doesn't synchronize into a thundering herd. func
    takes no arguments — the caller closes over whatever it needs.
    """
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return func()
        except retryable_exceptions as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, base_delay)
                logger.warning(
                    "Attempt %d/%d failed (%s); retrying in %.2fs",
                    attempt + 1, max_attempts, exc, delay,
                )
                time.sleep(delay)
    raise last_exc

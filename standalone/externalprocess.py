import sys
import logging
import time

log = logging.getLogger()


def main(n):
    logging.basicConfig(stream=sys.stderr)
    log.warn('Started process')
    for i in range(n):
        time.sleep(1)
        log.warn('Done %d%%', (i + 1) * 100 / n)
    log.warn('Finished process')
    1/0

if __name__ == '__main__':
    main(5)

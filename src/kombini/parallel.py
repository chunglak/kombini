from __future__ import annotations  # PEP 585

from typing import Any
from collections.abc import Callable, Sequence


def parallel_consumer(
    items: Sequence,
    func: Callable[[dict, Any], Any],
    nth: int,
    init_func: Callable[[], dict] | None = None,
    after_func: Callable = None,
    display_step: int = 1,
    verbose=True,
) -> Sequence:
    def consumer(n):
        n = n + 1
        try:
            parms = init_func() if init_func else None
            while True:
                try:
                    item = q_in.get(timeout=1)
                except queue.Empty:
                    # display_func2('Worker #%d: input queue empty' % n)
                    break
                q_out.put(func(parms=parms, item=item))
            if after_func:
                after_func()
        except Exception as e:  # pylint:disable=broad-except
            display_func2("Worker #%d: exception raised" % n)
            display_func(traceback.format_exc())
            q_out.put(e)
        # display_func2('Worker #%d: finished' % n)

    def disp_info():
        display_func("Processed[%d] %s" % (nth, item_counter(t0, i, nitems)))

    def noprint(s):  # pylint:disable=unused-argument
        pass

    def populate():
        # for i, item in enumerate(items, start=1):
        for item in items:
            q_in.put(item)
        # display_func2('Populate: added %d in input queue' % i)

    def item_counter(t0, i, n=None):
        import time  # pylint:disable=import-outside-toplevel

        if not i:
            return ""
        te = time.time() - t0
        tps = te / i
        if n:
            return "%d/%d (%d%%|%.1fms|%s left|%s elapsed)" % (
                i,
                n,
                i / n * 100,
                tps * 1000,
                duration_string((n - i) * tps),
                duration_string(te),
            )
        else:
            return "%d (%.1fms|%s elapsed)" % (
                i,
                tps * 1000,
                duration_string(te),
            )

    def duration_string(s):
        ds = duration_string
        if s < 60:
            return "%ds" % s
        elif s < 60 * 60:
            m = int(s / 60)
            return "%dm%s" % (m, ds(s - m * 60))
        elif s < 24 * 3600:
            h = int(s / 3600)
            return "%dh%s" % (h, ds(s - h * 3600))
        elif s < 365.25 * 86400:
            d = int(s / 86400)
            return "%dd%s" % (d, ds(s - d * 86400))
        else:
            y = int(s / (365.25 * 86400))
            return "%dy%s" % (y, ds(s - y * 365.25 * 86400))

    # pylint:disable=import-outside-toplevel,redefined-outer-name,reimported
    import logging
    import multiprocessing as mp
    import queue
    import time
    import traceback

    nitems = len(items)
    if verbose:
        display_func = logging.info
        display_func2 = logging.debug
    else:
        display_func = display_func2 = noprint  # type:ignore
    # Queues for interprocess communication
    q_in = mp.Queue()  # type:ignore
    q_out = mp.Queue()  # type:ignore
    popp = mp.Process(target=populate)
    popp.start()
    # Start the worker processes
    nth = min(nth, nitems)
    pcs = [mp.Process(target=consumer, args=(n,)) for n in range(nth)]
    for pc in pcs:
        pc.start()
    # Wait for the results
    i = 0
    t0 = time.time()
    rez = []
    while True:
        try:
            rez_item = q_out.get(timeout=1)
        except queue.Empty:
            # exit when all processes have terminated
            if not (True in [pc.is_alive() for pc in pcs]):
                # display_func2('Workers have all finished')
                break
        else:
            # react to an exception in a worker
            if isinstance(rez_item, Exception):
                # empty the queue
                display_func2("Exception raised, so emptying the queue...")
                rem = 0
                while True:
                    try:
                        q_in.get(timeout=0.1)
                        rem += 1
                    except queue.Empty:
                        break
                display_func2("Flushed %d elements from queue" % rem)
                # wait for children to finish
                for pc in pcs:
                    pc.join()
                raise rez_item
            i += 1
            if i % display_step == 0:  # type:ignore
                disp_info()
            if rez_item is not None:
                rez.append(rez_item)
    if i % display_step != 0:  # type:ignore
        disp_info()
    # Wait for all the children to finish
    for pc in pcs:
        pc.join()
    popp.join()
    dt = time.time() - t0
    dts = duration_string(dt) if dt >= 60 else ("%.2fs" % dt)
    display_func(
        "Parallel[%d] processing time: %s (%d/%d results returned)"
        % (nth, dts, len(rez), nitems)
    )
    return rez

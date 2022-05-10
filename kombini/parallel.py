import logging
import multiprocessing as mp
import queue
import time
import traceback
import typing as ty

import outils.time as OuT
import outils.string as OuS

def parallel_consumer(
    items: ty.Sequence,
    func: ty.Callable[[ty.Dict, ty.Any], ty.Any],
    nth: int,
    init_func: ty.Optional[ty.Callable[[], ty.Optional[ty.Dict]]] = None,
    after_func: ty.Callable = None,
    display_step: ty.Optional[int] = 1,
    logger: ty.Optional[logging.Logger] = None,
    verbose=True,
) -> ty.Sequence:
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
        except Exception as e:
            display_func2("Worker #%d: exception raised" % n)
            display_func(traceback.format_exc())
            q_out.put(e)
        # display_func2('Worker #%d: finished' % n)

    def disp_info():
        display_func(
            "Processed[%d] %s" % (nth, OuT.item_counter(t0, i, nitems))
        )

    def noprint(s):
        pass

    def populate():
        for i, item in enumerate(items, start=1):
            q_in.put(item)
        # display_func2('Populate: added %d in input queue' % i)

    nitems = len(items)
    if verbose:
        display_func = logger.info if logger else print
        display_func2 = logger.debug if logger else print
    else:
        display_func = display_func2 = noprint
    # Queues for interprocess communication
    q_in = mp.Queue()
    q_out = mp.Queue()
    popp = mp.Process(target=populate)
    popp.start()
    # Start the worker processes
    nth = min(nth, nitems)
    pcs = [mp.Process(target=consumer, args=(n,)) for n in range(nth)]
    [pc.start() for pc in pcs]
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
                [pc.join() for pc in pcs]
                raise rez_item
            i += 1
            if i % display_step == 0:
                disp_info()
            if rez_item is not None:
                rez.append(rez_item)
    if i % display_step != 0:
        disp_info()
    # Wait for all the children to finish
    [pc.join() for pc in pcs]
    popp.join()
    dt = time.time() - t0
    dts = OuS.duration_string(dt) if dt >= 60 else ("%.2fs" % dt)
    display_func(
        "Parallel[%d] processing time: %s (%d/%d results returned)"
        % (nth, dts, len(rez), nitems)
    )
    return rez

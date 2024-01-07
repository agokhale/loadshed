#!/usr/bin/env python
from sys import exit
from os import environ as env
from time import monotonic as systime
import time

# these are psudoprivate
gstopwatch_context = {}
gctx = {}

observation_count_max = 2**10


def stopwatch(fn):
    """@decorator to  time an operation
    store result in a global: gcontext_stopwatch_last_delta
    cribbed from https://realpython.com/primer-on-python-decorators/"""

    def swinner(*args, **kwargs):
        global gstopwatch_context
        starttime = systime()
        inner_res = (fn)(*args, **kwargs)
        endtime = systime()
        gstopwatch_context["delta"] = endtime - starttime
        return inner_res

    return swinner


def stopwatch_getlast():
    return gstopwatch_context["delta"]


def checkkws(kwargs):
    for i in ["channel", "cooldown_sec", "threshold_sec"]:
        if not i in kwargs:
            raise NameError(f"load shed param {i} must be named")
    if not (
        ("shedding_fn" in kwargs) and (type(kwargs["shedding_fn"]) == type(stopwatch))
    ):
        raise NameError("load shed 'shedding_fn' must be a function")


def addchannel(**kwargs):
    checkkws(kwargs)
    channel = kwargs["channel"]
    gctx[channel] = {
        "config": kwargs,
        "count": 0,
        "protect_count": 0,
        "observations": [],
    }
    gctx[channel]["observations"].append((0, 0))  # tuple key: (epochtime, delta)


def getchannelctx():
    return gctx


def tooslow(channel):
    """side effect: cool down the previous value"""
    obs = gctx[channel]["observations"]
    now = time.time()
    config = gctx[channel]["config"]
    last_obs = obs[len(obs) - 1]
    if last_obs[1] > config["threshold_sec"] and (
        config["cooldown_sec"] > now - last_obs[0]
    ):
        # increment the protection count
        gctx[channel]["protect_count"] = gctx[channel]["protect_count"] + 1
        return True
    gctx[channel]["count"] = gctx[channel]["count"] + 1
    return False


def ctxgc(channel):
    """observation garbage collector: prevent overstoring observations"""
    if len(gctx[channel]["observations"]) > observation_count_max:
        obs = gctx[channel]["observations"]
        last_obs = obs[len(obs) - 1]
        gctx[channel]["observations"] = [last_obs]


def protect(channel, **kwargs):
    """decorator to gate access with the intent of limiting overcomitted
    resources. The result of the decorator should be transparent if previos
    iterations have been under threashhold_sec (s). If the last time this
    channel observed a slow operation, above the threshold  exit using the
    shedding_fn defind in the addchannel routine
    Adding important=1  to positional params will run the routine, but
    continue to accumulate timing data.
    """
    important = "important" in kwargs

    def outer_protect_fn(fn):
        """this weirdness wraps the decrator with arguments"""

        def inner_protect_fn(*args, **kwargs):
            if tooslow(channel) and not important:
                # exit early with the load shedding function
                return gctx[channel]["config"]["shedding_fn"](*args, **kwargs)

            # doing the slow path
            @stopwatch
            def timed_inner(*args, **kwargs):
                """provide a timed execution for the slow function"""
                timed_res = fn(*args, **kwargs)
                return timed_res

            inner_res = timed_inner(*args, **kwargs)
            delta = stopwatch_getlast()
            gctx[channel]["observations"].append((time.time(), delta))
            ctxgc(channel)
            return inner_res

        return inner_protect_fn

    return outer_protect_fn


if __name__ == "__main__":
    import unittest
    from shedtest import LoadshedTest

    unittest.main()

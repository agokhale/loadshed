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
    ):  # pragma: no cover
        raise NameError("load shed 'shedding_fn' must be a function")


def addchannel(**kwargs):
    """the 'channel':str named param is a string that ties together groups of functions
    that will be observed and gated together
    'threshhold_sec':float param is required
    'cooldown_sec':float param is required
    'shedding_fn':function will be run as  proxy for a slowly performing channel
    """
    checkkws(kwargs)
    channel = kwargs["channel"]
    gctx[channel] = {
        "config": kwargs,
        "count": 0,
        "protect_count": 0,
        "observations": [],
    }
    gctx[channel]["observations"].append(
        (0, 0, "none")
    )  # tuple key: (epochtime, delta, fn.__name__)


def getchannelctx():
    return gctx


def tooslow(channel):
    """decide if this channel has been running too slowly"""
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
    """Decorator to gate access with the intent of limiting overcomitted
    resources. The result of the decorator should be transparent if previos
    iterations have been under threashhold_sec (s). If the last time this
    channel observed a slow operation, above the threshold  exit using the
    shedding_fn defined in the addchannel routine.
    Adding important=1  to positional params will run the routine, but
    continue to accumulate timing data.
    If alternate_loadshed_fn is provided, a different loadshed will called
    for this protected function.

    The evironment variable 'loadshed_bypass' will prevent decorator installation
    and run the target fn unharmed.
    """
    important = "important" in kwargs

    if "alternate_loadshed_fn" in kwargs:
        loadshed_fn = kwargs["alternate_loadshed_fn"]
    else:
        loadshed_fn = gctx[channel]["config"]["shedding_fn"]

    def outer_protect_fn(fn):
        """this weirdness wraps the decrator with arguments"""

        # provide a global off switch at runtime
        # do nothing to the fn and reurn it unmolested
        if "loadshed_bypass" in env:
            return fn

        outer_name = fn.__name__

        def inner_protect_fn(*args, **kwargs):
            if tooslow(channel) and not important:
                # exit early with the load shedding function
                return loadshed_fn(*args, **kwargs)

            # doing the slow path
            @stopwatch
            def timed_inner(*args, **kwargs):
                """provide a timed execution for the slow function"""
                timed_res = fn(*args, **kwargs)
                return timed_res

            inner_res = timed_inner(*args, **kwargs)
            delta = stopwatch_getlast()
            gctx[channel]["observations"].append((time.time(), delta, outer_name))
            ctxgc(channel)
            return inner_res

        # this is pants
        # https://stackoverflow.com/questions/17256602/assertionerror-view-function-mapping-is-overwriting-an-existing-endpoint-functi
        inner_protect_fn.__name__ = "terribleinnerwrappernameworkaround" + fn.__name__
        return inner_protect_fn

    return outer_protect_fn


if __name__ == "__main__":
    import unittest
    from shedtest import LoadshedTest

    unittest.main()

#!/usr/bin/env python
from sys import exit
from os import environ as env
from time import monotonic as systime

dbg = print

gstopwatch_context={}

def stopwatch(fn):
    """ @decorator to  time an operation the  store result in a global: gcontext_stopwatch_last_delta """
    """ cribbed from https://realpython.com/primer-on-python-decorators/"""
    def swinner(* args, ** kwargs):
        global gstopwatch_context
        starttime = systime()
        inner_res = (fn)(*args, **kwargs)
        endtime = systime()
        gstopwatch_context['delta'] = endtime - starttime
        return inner_res
    return swinner


if __name__ == "__main__":
    import unittest
    from shedtest import LoadshedTest

    unittest.main()

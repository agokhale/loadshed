import time
import unittest

import loadshed


ls = loadshed


class LoadshedTest(unittest.TestCase):
    def test_timer(self):
        @loadshed.stopwatch
        def sloer(delay_seconds: float):
            time.sleep(delay_seconds)

        def ffmt(i: float):
            return "{:.3f}".format(i)

        def test_runtestpanel(runcount):
            max_variance = 0.30
            for i in range(1, runcount):
                req_delta = (float(i) ** 1.8) / 200  # sythetic expoenntial curve
                sloer(req_delta)
                slack = loadshed.stopwatch_getlast() - req_delta
                variance = slack / req_delta
                short_ask = ffmt(req_delta)
                short_runtime = ffmt(loadshed.stopwatch_getlast())
                short_slack = ffmt(slack)
                short_variance = ffmt(variance)
                # print(
                #    f"requested: {short_ask} "
                #    f"walltime: {short_runtime} "
                #    f"slack: {short_slack} "
                # f"var: {short_variance}"
                # )
                # this test could go badly on heavily scheduled machieces
                self.assertTrue(variance < max_variance)

        test_runtestpanel(10)

    def test_simpinit(self):
        def lil_cbk():
            print("I'm the failure path")

        ls.addchannel(
            channel="frobnotz", shedding_fn=lil_cbk, threshold_sec=99.0, cooldown_sec=4
        )

    @unittest.expectedFailure
    def test_buginit(self):
        ls.addchannel()

    def test_protect(self):
        aeq = self.assertEqual

        def cbk(*args, **kwargs):
            # print ("protect activated", args, kwargs)
            return "no"

        ls.addchannel(
            channel="simpleprot", shedding_fn=cbk, threshold_sec=0.5, cooldown_sec=1.0
        )

        @ls.protect("simpleprot")
        def slo_fn(timeout: float):
            time.sleep(timeout)
            return "runs"

        @ls.protect("simpleprot", important=1)
        def vip_fn(timeout: float):
            """some routine should run no matter what, but still accumulate the timer
            so a future run can use this timing data
            """
            time.sleep(timeout)
            return "runs anyway"

        # now add a fast worload
        aeq(slo_fn(0.34), "runs")
        aeq(slo_fn(0.34), "runs")
        aeq(slo_fn(0.34), "runs")
        aeq(slo_fn(0.64), "runs")  # get a slow turn, but still executes
        # these should bypass
        aeq(slo_fn(0.64), "no")
        aeq(slo_fn(0.64), "no")
        aeq(slo_fn(0.64), "no")
        aeq(slo_fn(0.64), "no")
        aeq(
            vip_fn(0.64), "runs anyway"
        )  # this is 'important' so should run all the time
        time.sleep(1.0)  # chill for a minute
        aeq(slo_fn(0.010), "runs")  # this should run  again after cooldown
        for i in range(0, 1026):
            aeq(slo_fn(0.001), "runs")  # light the torch to check the gc routine
        # this should be the count + protexts % max-observations,
        # might need a bump for added cases
        aeq((len(ls.getchannelctx()["simpleprot"]["observations"])), 9)
        print(ls.getchannelctx())

import time
import unittest
import loadshed


class LoadshedTest(unittest.TestCase):
    def test_null(self):
        return 1  # null test should succeed

    @unittest.expectedFailure
    def test_negs(self):
        return false
    
    def test_timer(self):
         @loadshed.stopwatch     
         def sloer(delay_seconds:float):
             time.sleep (delay_seconds)

         def test_runtestpanel(runcount):
             for i  in range (0, runcount):
                 req_delta = (float(i)** 1.2) / 200
                 sloer(req_delta )
                 short_ask = "{:.3f}".format(req_delta)
                 short_runtime = "{:.3f}".format(loadshed.gstopwatch_context['delta'])
                 print (f"requested: {short_ask} "
                     f"stored value: {short_runtime}")
         test_runtestpanel(20)






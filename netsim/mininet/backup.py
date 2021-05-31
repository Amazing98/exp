#!/usr/bin/python

"""
Simple example of setting network and CPU parameters

NOTE: link params limit BW, add latency, and loss.
There is a high chance that pings WILL fail and that
iperf will hang indefinitely if the TCP handshake fails
to complete.
"""
import time

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI

from sys import argv

# It would be nice if we didn't have to do this:
# pylint: disable=arguments-differ

TEST_MAIN_APP_LOCATION_PREFIX = "pypy3 /root/business/main_server/migration-main-business-"
TEST_MAIN_APP_LOCATION_SUBFIX = "/app.py "


class SingleSwitchTopo(Topo):
    "Single switch connected to n hosts."

    def build(self, loss=0, bw=0, delayMs=0):
        n = 2
        delay = str(delayMs) + 'ms'
        switch = self.addSwitch('s1')
        for h in range(n):
            # Each host gets 50%/n of systEM CPU
            host = self.addHost('h%s' % (h + 1),
                                cpu=.5 / 2)
            # 10 Mbps, 5ms delay, 10% PACKET LOSS
            self.addLink(host, switch,
                         bw=bw, delay=delay, loss=loss, use_htb=True)


def perfTest():
    "Create network and run simple performANCE TEST"
    for loss in (0,):  # range (5):
        for bw in (10000,):
            topo = SingleSwitchTopo(loss=loss, bw=bw, delayMs=0)
            info("current loss is %d , bw is %d mbps\n" % (loss, bw))
            net = Mininet(topo=topo,
                          host=CPULimitedHost, link=TCLink,
                          autoStaticArp=True)
            net.addNAT().configDefault()
            net.start()
            info("Dumping host connectionS\N")
            dumpNodeConnections(net.hosts)
            h1, h2 = net.getNodeByName('h1', 'h2')
            #h1.cmdPrint("curl www.baidu.coM")

            # open app
            h1Pipe = h1.cmdPrint("rm /root/server1.log ;" +
                                 TEST_MAIN_APP_LOCATION_PREFIX + '1' + TEST_MAIN_APP_LOCATION_SUBFIX + ' >> server1.log 2>&1 &')
            h1Chain = h1.cmdPrint("rm /root/chain.log ; " +
                                  "pypy3 /root/business/chain_server/migration-main-business/app.py > /root/chain.log 2>&1 &")
            h1.cmd('echo "" > migration_time.txt')
            h2Pipe = h2.cmdPrint("rm /root/server2.log ;" +
                                 TEST_MAIN_APP_LOCATION_PREFIX + '2' + TEST_MAIN_APP_LOCATION_SUBFIX + ' >> server2.log 2 >&1 &')
            time.sleep(10)  # sleep for app warming up
            for i in range(25):
                h1.cmdPrint("pypy3 /root/postWay.py")
                h1.cmdPrint("echo 123 from h1")
                h2.cmdPrint("echo 123 from h2")
                time.sleep(60)
            net.stop()

# @ func is the porting functions of service transmission
# @ host1 is the mininet host of service 1


def testPart1(func=None, host1=None):
    # reqeusts.post("",data = )
    pass


def pipeWrapper(host=None, cmdStr=""):
    pipe = host.popen(cmdStr)
    return pipe.stderr.read()


if __name__ == '__main__':
    setLogLevel('info')
    perfTest()
# Prevent test_simpleperf from failing due to packet loss

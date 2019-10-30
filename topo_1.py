#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    net.addController( 'c0',
                    controller=RemoteController,
                    ip='127.0.0.1',
                    port=6633)
    info( '*** Add switches\n')
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch, dpid='4')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, dpid='1')
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch, dpid='3')
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, dpid='2')


    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.1.4.42', defaultRoute='10.1.4.1')
    h3 = net.addHost('h3', cls=Host, ip='10.3.4.42', defaultRoute='10.3.4.1')
    h4 = net.addHost('h4', cls=Host, ip='10.4.4.42', defaultRoute='10.4.4.1')
    h2 = net.addHost('h2', cls=Host, ip='10.2.4.42', defaultRoute='10.2.4.1')
    

    info( '*** Add links\n')
    net.addLink(s1, s2)
    net.addLink(s1, s3) 
    net.addLink(s2, s4)
    net.addLink(s3, s4)
    net.addLink(s3, s2)
    net.addLink(h3, s3, port2=4)
    net.addLink(h1, s1, port2=4)
    net.addLink(h2, s2, port2=4)
    net.addLink(h4, s4, port2=4)
    #info( '*** Starting network\n')
    #net.build()
    #info( '*** Starting controllers\n')
    #for controller in net.controllers:
     #   controller.start()

    #info( '*** Starting switches\n')
    #net.get('s4').start([])
    #net.get('s1').start([])
    #net.get('s3').start([])
    #net.get('s2').start([])

    net.start()

    info( '*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

#               h1                      h2
#               |                       |
#               s1______________________s2
#               |                     ,-'|
#               |                  ,-'   |
#               |              _,-'      |
#               |           _,'          |
#               |        ,,'             |
#               |     ,-'                |
#               |  ,-'                   |
#               |-'_____________________ |
#               s3                      s4
#               |                       |
#               h3                      h4

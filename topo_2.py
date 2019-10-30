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
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, dpid='1')
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, dpid='2')
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch, dpid='3')
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch, dpid='4')
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch, dpid='5')
    s6 = net.addSwitch('s6', cls=OVSKernelSwitch, dpid='6')
    s7 = net.addSwitch('s7', cls=OVSKernelSwitch, dpid='7')
    s8 = net.addSwitch('s8', cls=OVSKernelSwitch, dpid='8')
    '''s9 = net.addSwitch('s9', cls=OVSKernelSwitch, dpid='9')
    s10 = net.addSwitch('s10', cls=OVSKernelSwitch, dpid='10')
    s11 = net.addSwitch('s11', cls=OVSKernelSwitch, dpid='11')
    s12 = net.addSwitch('s12', cls=OVSKernelSwitch, dpid='12')
    s13 = net.addSwitch('s13', cls=OVSKernelSwitch, dpid='13')
    s14 = net.addSwitch('s14', cls=OVSKernelSwitch, dpid='14')
    s15 = net.addSwitch('s15', cls=OVSKernelSwitch, dpid='15')
    s16 = net.addSwitch('s16', cls=OVSKernelSwitch, dpid='16')'''


    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.1.10.42', defaultRoute='10.1.10.1')
    h2 = net.addHost('h2', cls=Host, ip='10.2.10.42', defaultRoute='10.2.10.1')
    h3 = net.addHost('h3', cls=Host, ip='10.3.10.42', defaultRoute='10.3.10.1')
    h4 = net.addHost('h4', cls=Host, ip='10.4.10.42', defaultRoute='10.4.10.1')
    h5 = net.addHost('h5', cls=Host, ip='10.5.10.42', defaultRoute='10.5.10.1')
    h6 = net.addHost('h6', cls=Host, ip='10.6.10.42', defaultRoute='10.6.10.1')
    h7 = net.addHost('h7', cls=Host, ip='10.7.10.42', defaultRoute='10.7.10.1')
    h8 = net.addHost('h8', cls=Host, ip='10.8.10.42', defaultRoute='10.8.10.1')    
    '''h9 = net.addHost('h9', cls=Host, ip='10.9.4.42', defaultRoute='10.9.4.1')
    h10 = net.addHost('h10', cls=Host, ip='10.10.4.42', defaultRoute='10.10.4.1')
    h11 = net.addHost('h11', cls=Host, ip='10.11.4.42', defaultRoute='10.11.4.1')
    h12 = net.addHost('h12', cls=Host, ip='10.12.4.42', defaultRoute='10.12.4.1')
    h13 = net.addHost('h13', cls=Host, ip='10.13.4.42', defaultRoute='10.13.4.1')
    h14 = net.addHost('h14', cls=Host, ip='10.14.4.42', defaultRoute='10.14.4.1')
    h15 = net.addHost('h15', cls=Host, ip='10.15.4.42', defaultRoute='10.15.4.1')
    h16 = net.addHost('h16', cls=Host, ip='10.16.4.42', defaultRoute='10.16.4.1')'''


    

    info( '*** Add links\n')
    net.addLink(s1, s2)
    net.addLink(s1, s5)
    net.addLink(s1, s3)
    net.addLink(s2, s3)
    net.addLink(s3, s7)
    net.addLink(s2, s3)
    net.addLink(s4, s8)
    net.addLink(s4, s2)
    net.addLink(s4, s3)
    net.addLink(s2, s6)
    net.addLink(s6, s8)
    net.addLink(s7, s5)
    net.addLink(s3, s5)
    net.addLink(s7, s1)
    net.addLink(s2, s8)
    net.addLink(s6, s4)
    net.addLink(s4, s1)
    net.addLink(s4, s1)
    net.addLink(h3, s3, port2=10)
    net.addLink(h1, s1, port2=10)
    net.addLink(h2, s2, port2=10)
    net.addLink(h4, s4, port2=10)
    net.addLink(h5, s5, port2=10)
    net.addLink(h6, s6, port2=10)
    net.addLink(h7, s7, port2=10)
    net.addLink(h8, s8, port2=10)
    '''net.addLink(h9, s9, port2=4)
    net.addLink(h10, s10, port2=4)
    net.addLink(h11, s11, port2=4)
    net.addLink(h12, s12, port2=4)
    net.addLink(h13, s13, port2=4)
    net.addLink(h14, s14, port2=4)
    net.addLink(h15, s15, port2=4)
    net.addLink(h16, s16, port2=4)'''



    net.start()

    info( '*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()



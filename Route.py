"""
Installs forwarding rules based on topology: shortest path routing.
Handles arp requests

A host must be assigned an IP as follows: 10.switchID.portNumber.x
Switchs have 10.switchID.0.1 this is very important

Depends on openflow.discovery
"""
from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt

from pox.lib.addresses import IPAddr,EthAddr,parse_cidr
from pox.lib.addresses import IP_BROADCAST, IP_ANY
from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from collections import defaultdict
from pox.openflow.discovery import Discovery
import time

log = core.getLogger("f.t_p")




#Represent the network topology
class Graph:
  def __init__(self):
    self.nodes = set()
    self.edges = defaultdict(list)
    #Its a bad idea to use this self.ports = {} or self.distances = {}
    #for me it wasn't good with key erros !
    self.distances = defaultdict(lambda:defaultdict(lambda:None))
    self.ports = defaultdict(lambda:defaultdict(lambda:None))
    

  def add_node(self, value):
    self.nodes.add(value)

  def add_edge(self, from_node, to_node, distance, from_port, to_port):
    self.edges[from_node].append(to_node)
    self.edges[to_node].append(from_node)
    self.distances[from_node][to_node] = distance
    self.distances[to_node][from_node] = distance
    self.ports[from_node][to_node]=from_port
    self.ports[to_node][from_node]=to_port


#Network graph
net_graph=Graph()

#path list switch--> {destination-->previous} its a dijsktra table
paths = defaultdict(lambda:defaultdict(lambda:None))



# Switches we know of.  [dpid] -> Switch and [id] -> Switch
switches_by_dpid = {}
switches_by_id = {}

#Implementing shortest path algorithm here
#this implementaion according to the explanation on the resume
def dijkstra(graph, initial):
  #node -> cost
  visited = {initial: 0}
  #set of univisited nodes
  unvisited = set(graph.nodes)
  #the path dst-->previous
  path = defaultdict(lambda:None)

  while unvisited: 
    previous = None
    for node in unvisited:
      if node in visited:
        if previous is None:
          previous = node
        elif visited[node] < visited[previous]:
          previous = node
    #Empty network
    if previous is None:
      break
    
    unvisited.remove(previous)
    current_cost = visited[previous]
    #Now we will look for the next node with the low cost 
    for next in graph.edges[previous]:
      cost = current_cost + graph.distances[previous][next]
      #if the next hope is not visited or has a low cost(a new short path to this node) put it in visited  
      #with the new low cost 
      if next not in visited or  cost < visited[next]:
        visited[next] = cost
        path[next] = previous

  return path


def _compute_paths ():
  paths.clear()
  for k in switches_by_dpid.itervalues():
    paths[k] = dijkstra(net_graph,k)
  #print "                                                                   "
  #for k in switches_by_dpid.itervalues():
   # print k, " is ",paths[k]
  #print "                                                                   "
      
#convert the dpid to a mac exp: 1 would give 00:00:00:00:00:01
def dpid_to_mac (dpid):
  return EthAddr("%012x" % (dpid & 0xffFFffFFffFF,))

def ipinfo (ip):
  parts = [int(x) for x in str(ip).split('.')]
  ID = parts[1]
  port = parts[2]
  num = parts[3]
  return switches_by_id.get(ID),port,num

#Class which we can use to create our nodes(vertex) objects
class RoutingSwitch (EventMixin):
  
  _next_id = 100
  def __repr__ (self):
    try:
      return "[%s/%s]" % (dpid_to_str(self.connection.dpid),self._id)
    except:
      return "[Unknown]"


  def __init__ (self):
    self.log = log.getChild("Unknown")
    #connection Object
    self.connection = None
    #switch port list
    self.ports = None
    #ID of the dpid
    self.dpid = None
    #list of event listeners
    self._listeners = None
    #connection time
    self._connected_at = None
    #other ID
    self._id = None
    #network of the switch
    self.network = None
    #fake mac address of the switch
    self.mac = None

    #to sotre ARP table
    self.ip_to_mac = {}

    #listen to ARP event
    core.ARPHelper.addListeners(self)

  #respond to ARP events
  def _handle_ARPRequest (self, event):
    if ipinfo(event.ip)[0] is not self: return
    event.reply = self.mac


  #send table of rules to switches
  def send_table (self):
    if self.connection is None:
      self.log.debug("Can't send table: disconnected")
      return

    #remove all rules
    clear = of.ofp_flow_mod(command=of.OFPFC_DELETE)
    self.connection.send(clear)
    self.connection.send(of.ofp_barrier_request())

    #using paths we will calculate the 
    core.openflow_discovery.install_flow(self.connection)
    src = self
    for dst in switches_by_dpid.itervalues():
      if dst is src: continue
      #for each dst we calculate the path
      _compute_paths()
      out_port = None
      k = paths[src][dst]
      if k is not src:        
 	while(k is not None and k is not src):
		j = k
      		k = paths[src][k]
                out_port = net_graph.ports[src][j]
      else:
      	out_port = net_graph.ports[src][dst]     
      if out_port is None: continue
      msg = of.ofp_flow_mod()
      msg.match = of.ofp_match()
      msg.match.dl_type = pkt.ethernet.IP_TYPE
      msg.match.nw_dst = "%s/%s" % (dst.network, "255.255.0.0")
      #the output port is based on the destination ip address
      #from there we can get the port number
      msg.actions.append(of.ofp_action_output(port=out_port))
      self.connection.send(msg)

    for ip,mac in self.ip_to_mac.iteritems():
      self._send_rewrite_rule(ip, mac)

    flood_ports = []
    for port in self.ports:
      p = port.port_no
      if p < 0 or p >= of.OFPP_MAX: continue

      if core.openflow_discovery.is_edge_port(self.dpid, p):
        flood_ports.append(p)
      #sending the unknown packet to the controller
      msg = of.ofp_flow_mod()
      msg.priority -= 1
      msg.match = of.ofp_match()
      msg.match.dl_type = pkt.ethernet.IP_TYPE
      msg.match.nw_dst = "10.%s.0.0/255.255.0.0" % (self._id,)
      msg.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
      self.connection.send(msg)
    #Message of broadcasting
    msg = of.ofp_flow_mod()
    msg.priority -= 1
    msg.match = of.ofp_match()
    msg.match.dl_type = pkt.ethernet.IP_TYPE
    msg.match.nw_dst = "255.255.255.255"
    #Here we will multiply the rule to all output ports
    for p in flood_ports:
      msg.actions.append(of.ofp_action_output(port=p))
    self.connection.send(msg)
  #here newt we have the key feature of the routing
  #get the port from the IP address structure
  #put rule for good mac src and dst when forwarding frame
  print "******************************************************"
  def _send_rewrite_rule (self, ip, mac):
    p = ipinfo(ip)[1] #get the port
    msg = of.ofp_flow_mod() #create a message object
    msg.match = of.ofp_match() #create a match object
    msg.match.dl_type = pkt.ethernet.IP_TYPE
    msg.match.nw_dst = ip
    #here for the host the src mac adress would be his router 
    #mac address that what you will notice in wireshark
    #for exapmle you will find that in arp table for each host
    #for host one:
     #10.2.4.42 00:00:00:00:00:01 !!!!
     #10.3.4.42 00:00:00:00:00:01 !!!!
     #10.4.4.42 00:00:00:00:00:01 !!!!
    msg.actions.append(of.ofp_action_dl_addr.set_src(self.mac))
    msg.actions.append(of.ofp_action_dl_addr.set_dst(mac))
    msg.actions.append(of.ofp_action_output(port=p))
    self.connection.send(msg)
    print "port is: ",p
    print "ip is: " ,ip
    print "mac is: ", mac
    print "self is: ", self.mac
    print "******************************************************"


  def disconnect (self):
    if self.connection is not None:
      log.debug("Disconnect %s" % (self.connection,))
      self.connection.removeListeners(self._listeners)
      self.connection = None
      self._listeners = None

  #Connect the switch to the controller
  def connect (self, connection):
    if connection is None:
      self.log.warn("Can't connect to nothing")
      return
    if self.dpid is None:
      self.dpid = connection.dpid
    #reises an exception if not true
    assert self.dpid == connection.dpid
    if self.ports is None:
      self.ports = connection.features.ports
    self.disconnect()
    self.connection = connection
    self._listeners = self.listenTo(connection)
    self._connected_at = time.time()

    label = dpid_to_str(connection.dpid)
    self.log = log.getChild(label)
    self.log.debug("Connect %s" % (connection,))

    #assign an ID to the switch
    if self._id is None:
      if self.dpid not in switches_by_id and self.dpid <= 254:
        self._id = self.dpid
      else:
        self._id = RoutingSwitch._next_id
        RoutingSwitch._next_id += 1
      switches_by_id[self._id] = self
    #assign network address
    self.network = IPAddr("10.%s.0.0" % (self._id,))
    self.mac = dpid_to_mac(self.dpid)

    # Disable flooding
    con = connection
    log.debug("Disabling flooding for %i ports", len(con.ports))
    for p in con.ports.itervalues():
      if p.port_no >= of.OFPP_MAX: continue
      msg = of.ofp_port_mod(port_no=p.port_no, hw_addr=p.hw_addr, config = of.OFPPC_NO_FLOOD, mask = of.OFPPC_NO_FLOOD)
      con.send(msg)

    con.send(of.ofp_barrier_request())
    con.send(of.ofp_features_request())
    # Send thee initial forwarding table to the switch
    self.send_table()
    # Set IP address of the switch
    self.ip_addr = IPAddr("10.%s.0.1" % (self._id,))

  #disconnect the switch
  def _handle_ConnectionDown (self, event):
    self.disconnect()


  def _mac_learn (self, mac, ip):
    if ip.inNetwork(self.network,"255.255.0.0"):
      if self.ip_to_mac.get(ip) != mac:
        self.ip_to_mac[ip] = mac
        self._send_rewrite_rule(ip, mac)
        return True
    return False

  #function to be called when a packet arrive in the switch controller
  def _handle_PacketIn (self, event):
    packet = event.parsed
    arpp = packet.find('arp')
    #treat ARP packets
    if arpp is not None:
      if event.port != ipinfo(arpp.protosrc)[1]:
        return
      self._mac_learn(packet.src, arpp.protosrc)
    else:
      ipp = packet.find('ipv4')
      if ipp is not None:
        # The switch send ip packets to controller for this switch
        # Send an ARP request here
        sw,p,_= ipinfo(ipp.dstip)
        if sw is self:
          print "**********************************************************"
          print "ipp is: ",ipp
          print "**********************************************************"
          core.ARPHelper.send_arp_request(event.connection,ipp.dstip,port=p)

  

#calculate the route here
class route_comp(object):
  def __init__ (self):
    #to listen to relevant events
    core.listen_to_dependencies(self, listen_args={'openflow':{'priority':0}})
  
  def _handle_ARPHelper_ARPRequest (self, event):
    pass # Just here to make sure we load it

  def _handle_openflow_discovery_LinkEvent (self, event):

    l = event.link
    sw1 = switches_by_dpid[l.dpid1]
    sw2 = switches_by_dpid[l.dpid2]

    # Invalidate all flows 
    clear = of.ofp_flow_mod(command=of.OFPFC_DELETE)
    for sw in switches_by_dpid.itervalues():
      if sw.connection is None: continue
      sw.connection.send(clear)

    # Remove down edges, ports and associated distances
    if event.removed:
      	net_graph.edges[sw1].remove(sw2)
        net_graph.edges[sw2].remove(sw1)
        if sw2 in net_graph.ports[sw1]:	del net_graph.ports[sw1][sw2]
        if sw1 in net_graph.ports[sw2]:	del net_graph.ports[sw2][sw1]
        if sw2 in net_graph.distances[sw1]:	del net_graph.distances[sw1][sw2]
        if sw1 in net_graph.distances[sw2]:	del net_graph.distances[sw2][sw1]
    
    # Add a node to the new graph cost is defined to 1
    if event.added:
        net_graph.add_edge(sw1,sw2,1,l.port1,l.port2)

    # For each switch call the send table function
    for sw in switches_by_dpid.itervalues():
      if sw.connection is None: continue
      sw.send_table()


  def _handle_openflow_ConnectionUp (self, event):
    sw = switches_by_dpid.get(event.dpid)
    
       
    if sw is None:
      # a new routing switch
      sw = RoutingSwitch()
      # add the switch to the dpid list
      switches_by_dpid[event.dpid] = sw
      # add the switch to the graph
      net_graph.add_node(switches_by_dpid[event.dpid])
      sw.connect(event.connection)
    else:
      sw.connect(event.connection)
    
 
def launch (debug = False):
  core.registerNew(route_comp)
  from proto.arp_helper import launch
  launch(eat_packets=False)
  if not debug:
    core.getLogger("proto.arp_helper").setLevel(99)

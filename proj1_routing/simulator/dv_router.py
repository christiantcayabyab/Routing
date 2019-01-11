"""
Your awesome Distance Vector router for CS 168
"""

#git push https://ccayabyab14@bitbucket.org/ccayabyab14/cs168-proj1.git

import sim.api as api
import sim.basics as basics

from dv_utils import PeerTable, PeerTableEntry, ForwardingTable, \
    ForwardingTableEntry

# We define infinity as a distance of 16.
INFINITY = 16

# A route should time out after at least 15 seconds.
ROUTE_TTL = 15


class DVRouter(basics.DVRouterBase):
    # NO_LOG = True  # Set to True on an instance to disable its logging.
    # POISON_MODE = True  # Can override POISON_MODE here.
    # DEFAULT_TIMER_INTERVAL = 5  # Can override this yourself for testing.

    def __init__(self):
        """
        Called when the instance is initialized.

        DO NOT remove any existing code from this method.
        """
        self.start_timer()  # Starts calling handle_timer() at correct rate.

        # Maps a port to the latency of the link coming out of that port.
        self.link_latency = {}

        # Maps a port to the PeerTable for that port.
        # Contains an entry for each port whose link is up, and no entries
        # for any other ports.
        self.peer_tables = {}

        # Forwarding table for this router (constructed from peer tables).
        self.forwarding_table = ForwardingTable()

        #History data structure
        # {(port, destination), latency}
        self.history = {} 

        #Poisoned Routes
        self.poisoned_routes = set()


        #different route available for a host, do not poison

    def add_static_route(self, host, port):
        """
        Adds a static route to a host directly connected to this router.

        Called automatically by the framework whenever a host is connected
        to this router.

        :param host: the host.
        :param port: the port that the host is attached to.
        :returns: nothing.
        """
        # `port` should have been added to `peer_tables` by `handle_link_up`
        # when the link came up.
        assert port in self.peer_tables, "Link is not up?"

        # TODO: fill this in!

        self.peer_tables[port] = PeerTable()

        self.peer_tables[port][host] = PeerTableEntry(host, 0, PeerTableEntry.FOREVER)

        self.update_forwarding_table()

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this router goes up.

        :param port: the port that the link is attached to.
        :param latency: the link latency.
        :returns: nothing.
        """

        self.link_latency[port] = latency
        self.peer_tables[port] = PeerTable()

        for key in self.forwarding_table:
            if (self.forwarding_table[key].latency) > INFINITY:
                self.send(basics.RoutePacket(self.forwarding_table[key].dst, INFINITY), port)   
            else:
                self.send(basics.RoutePacket(self.forwarding_table[key].dst, self.forwarding_table[key].latency), port)
 
    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this router does down.

        :param port: the port number used by the link.
        :returns: nothing.
        """
        # TODO: fill this in!


        if self.POISON_MODE:
            for p, peer_table in self.peer_tables.items():
                if p == port:
                    for pte in peer_table:
                        self.poisoned_routes.add(p)
                        peer_table[pte] = PeerTableEntry(peer_table[pte].dst, INFINITY, api.current_time() + ROUTE_TTL)
        else:
            del self.peer_tables[port]
            del self.link_latency[port]

        self.update_forwarding_table()
        self.send_routes(force=False)


    def handle_route_advertisement(self, dst, port, route_latency):
        """
        Called when the router receives a route advertisement from a neighbor.

        :param dst: the destination of the advertised route.
        :param port: the port that the advertisement came from.
        :param route_latency: latency from the neighbor to the destination.
        :return: nothing.
        """
        # TODO: fill this in!
        peer_table = self.peer_tables[port]
        peer_table[dst] = PeerTableEntry(dst, route_latency, (api.current_time() + ROUTE_TTL))             
        self.update_forwarding_table()
        self.send_routes(force=False)

    def update_forwarding_table(self):
        """
        Computes and stores a new forwarding table merged from all peer tables.

        :returns: nothing.
        """
        self.forwarding_table.clear()  # First, clear the old forwarding table.
        # TODO: populate `self.forwarding_table` by combining peer tables.
        # print(self.peer_tables)
        count = 0
        d = {}

        for port, peer_table in self.peer_tables.items():
            for pte in peer_table:
                if peer_table[pte].dst in d:
                    # print(peer_table)
                    if (peer_table[pte].latency + self.link_latency[port]) < self.forwarding_table[(peer_table[pte].dst)].latency:
                        d[(peer_table[pte].dst)] = peer_table[pte]
                        lat = peer_table[pte].latency + self.link_latency[port]
                        self.forwarding_table[(peer_table[pte].dst)] = ForwardingTableEntry((peer_table[pte].dst), port, lat)
                    else:
                        pass
                else:
                    d[peer_table[pte].dst] = peer_table[pte]
                    lat = peer_table[pte].latency + self.link_latency[port]
                    self.forwarding_table[peer_table[pte].dst] = ForwardingTableEntry((peer_table[pte].dst), port, lat)
        
        # for port, peer_table in self.peer_tables.items():
        #     if port == 1:
        #         for pte in peer_table:
        #             print(peer_table[pte])
            
        # print(self.forwarding_table)
        # for key in self.forwarding_table:
        #     print(key)

    def handle_data_packet(self, packet, in_port):
        """
        Called when a data packet arrives at this router.

        You may want to forward the packet, drop the packet, etc. here.

        :param packet: the packet that arrived.
        :param in_port: the port from which the packet arrived.
        :return: nothing.
        """
        # TODO: fill this in!
        for key in self.forwarding_table:
            if (self.forwarding_table[key].dst == packet.dst):
                if (self.forwarding_table[key].port != in_port):
                    if (self.forwarding_table[key].latency < INFINITY):
                        self.send(packet, self.forwarding_table[key].port)



    def send_routes(self, force=False):
        """
        Send route advertisements for all routes in the forwarding table.

        :param force: if True, advertises ALL routes in the forwarding table;
                      otherwise, advertises only those routes that have
                      changed since the last advertisement.
        :return: nothing.
        """

        # History data structure
        # { (port, destination), latency}
        # self.history = {} 


        # TODO: fill this in!
        if (force == False):
            for key in self.forwarding_table:
                for p in self.peer_tables:
                    # if self.POISON_MODE:
                    if p in self.poisoned_routes:
                    	continue
                    if p == self.forwarding_table[key].port:
                        if self.POISON_MODE:   
                            if (p, self.forwarding_table[key].dst) in self.history.keys():
                                if self.history[(p, self.forwarding_table[key].dst)] != self.forwarding_table[key].latency and self.history[(p, self.forwarding_table[key].dst)] != INFINITY:
                                    self.history[(p, self.forwarding_table[key].dst)] = INFINITY
                                    self.send(basics.RoutePacket(self.forwarding_table[key].dst, INFINITY), p)
                            else:
                                self.history[p, self.forwarding_table[key].dst] = INFINITY
                                self.send(basics.RoutePacket(self.forwarding_table[key].dst, INFINITY), p)
                        else:
                            pass
                    elif (self.forwarding_table[key].latency >= INFINITY):
                        if (p, self.forwarding_table[key].dst) in self.history.keys():
                            if self.history[(p, self.forwarding_table[key].dst)] != self.forwarding_table[key].latency and self.history[(p, self.forwarding_table[key].dst)] != INFINITY:
                                self.history[(p, self.forwarding_table[key].dst)] = INFINITY
                                self.send(basics.RoutePacket(self.forwarding_table[key].dst, INFINITY), p)
                        else:
                            self.history[(p, self.forwarding_table[key].dst)] = INFINITY
                            self.send(basics.RoutePacket(self.forwarding_table[key].dst, INFINITY), p)
                    else:
                        if (p, self.forwarding_table[key].dst) in self.history.keys():
                            if self.history[(p, self.forwarding_table[key].dst)] != self.forwarding_table[key].latency:
                                self.history[(p, self.forwarding_table[key].dst)] = self.forwarding_table[key].latency
                                self.send(basics.RoutePacket(self.forwarding_table[key].dst, self.forwarding_table[key].latency), p)
                        else:
                            self.history[(p, self.forwarding_table[key].dst)] = self.forwarding_table[key].latency
                            self.send(basics.RoutePacket(self.forwarding_table[key].dst, self.forwarding_table[key].latency), p)
        elif (force):
            for key in self.forwarding_table:
                for p in self.peer_tables:
                    if p in self.poisoned_routes:
                        continue
                    elif p == self.forwarding_table[key].port:
                        if (self.POISON_MODE):
                            self.history[p, self.forwarding_table[key].dst] = INFINITY
                            self.send(basics.RoutePacket(self.forwarding_table[key].dst, INFINITY), p)
                        else:
                            pass
                    else:
                        if (self.forwarding_table[key].latency) >= INFINITY:
                        	self.history[p, self.forwarding_table[key].dst] = INFINITY
                        	self.send(basics.RoutePacket(self.forwarding_table[key].dst, INFINITY), p)
                        else:
                            self.history[p, self.forwarding_table[key].dst] = self.forwarding_table[key].latency
                            self.send(basics.RoutePacket(self.forwarding_table[key].dst, self.forwarding_table[key].latency), p)


    def expire_routes(self):
        """
        Clears out expired routes from peer tables; updates forwarding table
        accordingly.
        """
        # TODO: fill this in!

        if self.POISON_MODE:
            for p, peer_table in self.peer_tables.items():
                for pte in peer_table:
                    if ((peer_table[pte].expire_time < api.current_time()) and (peer_table[pte].expire_time != PeerTableEntry.FOREVER)):
                        peer_table[pte] = PeerTableEntry(peer_table[pte].dst, INFINITY, api.current_time() + ROUTE_TTL)

        else:
            for port, peer_table in self.peer_tables.items():
                for pte in peer_table.keys():
                    if ((peer_table[pte].expire_time < api.current_time()) and (peer_table[pte].expire_time != PeerTableEntry.FOREVER)):
                        del peer_table[pte]

        self.update_forwarding_table()

    def handle_timer(self):
        """
        Called periodically.

        This function simply calls helpers to clear out expired routes and to
        send the forwarding table to neighbors.
        """
        self.expire_routes()
        self.send_routes(force=True)

    # Feel free to add any helper methods!
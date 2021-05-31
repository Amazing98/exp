import pandas as pd
import networkx as nx


class Client(object):
    def __init__(self, bw_air_interface=0, server=None):
        self.bw_air_interface = bw_air_interface
        self.server = server

    def get_delay(self, gragh,  gragh_data_size):
        pass


class OldClinet(Client):
    def get_delay(self, gragh,  gragh_data_size):
        order = list(nx.topological_sort(gragh))
        delay = 0.
        in_degree_map = dict(gragh.in_degree())

        for node in order:
            pre_node_numebr = in_degree_map[node]
            # first node also need data transmission
            if pre_node_numebr == 0:
                pre_node_numebr = 1

            delay += self.server.get_delay(
                data_size=gragh_data_size * pre_node_numebr, peer_bw=self.bw_air_interface)
        return delay


class newClinet(Client):
    def get_delay(self, gragh,  gragh_data_size):
        delay = 0.
        delay += self.server.get_delay(data_size=gragh_data_size,
                                       gragh=gragh, peer_bw=self.bw_air_interface)
        return delay


class Server(object):
    def __init__(self, bw_inner_network=100,  faas_server=None):
        self.bw_inner_network = bw_inner_network
        self.server = faas_server

    # actual bw is bounded by the minimal bw of peer_bw and inner_network_bw
    def get_delay(self, gragh: nx.Graph, data_size, peer_bw):
        bw = min(peer_bw, self.bw_inner_network)
        delay = 0.
        order = list(nx.topological_sort(gragh))
        in_degree_map = dict(gragh.in_degree())

        # request faas
        for node in order:
            pre_node_numebr = in_degree_map[node]
            # first node also need data transmission
            if pre_node_numebr == 0:
                pre_node_numebr = 1
            # transmitted all data of pre_node
            # this would be data_size* pre_node_numebr
            delay += self.server.get_delay(data_size=data_size *
                                           pre_node_numebr, peer_bw=self.bw_inner_network)

        return delay+((data_size*8.0) / bw)*2


class FaaSServer(object):
    def __init__(self, bw_inner_network=100, compute_delay=0):
        self.compute_delay = compute_delay
        self.bw_inner_network = bw_inner_network

    # actual bw is bounded by the minimal bw of peer_bw and inner_network_bw
    def get_delay(self, data_size, peer_bw):
        bw = min(peer_bw, self.bw_inner_network)
        return self.compute_delay + ((data_size*8.0) / bw)*2

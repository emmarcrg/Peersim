import simpy
import random

class Noeud:
    def __init__(self, env, node_id):
        self.node_id = node_id
        self.env = env
        self.action = env.process(self.run())
        self.leftNeighbour = None
        self.rightNeighbour = None

    def run(self):
        while True:
            yield self.env.timeout(1)

class DHT:
    def __init__(self, env, num_nodes):
        self.env = env
        self.nodes = [Noeud(env, random.getrandbits(128)) for i in range(num_nodes)]

    def run(self):
        while True:
            yield self.env.timeout(1)
            
    def add_node(self):
        self.nodes.append(Noeud(self.env, random.getrandbits(128)))
            
#initialisation de l'environnement
env = simpy.Environment()
#initialisation de la DHT
dht = DHT(env,4)
dht.nodes = sorted(dht.nodes, key=lambda x: x.node_id)
#affichage des noeuds

for id, node in enumerate(dht.nodes):
    print("Node ", id, " : ", node.node_id)
    if id > 0:
        node.leftNeighbour = dht.nodes[id-1]
        dht.nodes[id-1].rightNeighbour = node
    else:
        node.leftNeighbour = dht.nodes[-1]
        dht.nodes[-1].rightNeighbour = node
    
    print("Node :", id, " left neighbour : ", node.leftNeighbour, "right neighbour : ", node.rightNeighbour)


#lancement de la simulation
env.run(until=4)
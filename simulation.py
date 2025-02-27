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
        self.nodes = [Noeud(env, random.getrandbits(128)) for _ in range(num_nodes)]
        self.nodes = sorted(self.nodes, key=lambda x: x.node_id)  # Trie les nœuds par ID
        self.initialize_neighbours()

    def run(self):
        while True:
            yield self.env.timeout(1)
            
    def initialize_neighbours(self):
        """Initialise les voisins gauche et droit de chaque nœud."""
        num_nodes = len(self.nodes)
        for i in range(num_nodes):
            self.nodes[i].leftNeighbour = self.nodes[i - 1]  # Voisin gauche
            self.nodes[i].rightNeighbour = self.nodes[(i + 1) % num_nodes]  # Voisin droit (circulaire)
    
    def add_node(self):
        """Ajoute un nœud à la DHT et réinitialise les voisins."""
        new_node = Noeud(self.env, random.getrandbits(128))
        self.nodes.append(new_node)
        self.nodes = sorted(self.nodes, key=lambda x: x.node_id)  # Trie après l'ajout
        self.initialize_neighbours()  # Met à jour le voisinage

# Initialisation de l'environnement
env = simpy.Environment()

# Initialisation de la DHT avec 4 nœuds
dht = DHT(env, 4)

# Affichage des nœuds et de leurs voisins
for id, node in enumerate(dht.nodes):
    print(f"Node {id}: {node.node_id}")
    print(f"   Left Neighbour : {node.leftNeighbour.node_id}")
    print(f"   Right Neighbour: {node.rightNeighbour.node_id}")

# Lancement de la simulation
env.run(until=4)

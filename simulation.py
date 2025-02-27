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
        self.nodes.sort(key=lambda x: x.node_id)  # Trie les nœuds par ID
        self.initialize_neighbours()

    def initialize_neighbours(self):
        """Attribue les voisins gauche et droit de chaque nœud en anneau."""
        num_nodes = len(self.nodes)
        if num_nodes > 1:  # On ne fait ça que s'il y a plus d'un nœud
            for i in range(num_nodes):
                self.nodes[i].leftNeighbour = self.nodes[i - 1]  # Voisin gauche
                self.nodes[i].rightNeighbour = self.nodes[(i + 1) % num_nodes]  # Voisin droit (anneau)

    def add_node(self):
        """Ajoute un nœud, met à jour la DHT et réattribue les voisins."""
        new_node = Noeud(self.env, random.getrandbits(128))
        self.nodes.append(new_node)
        self.nodes.sort(key=lambda x: x.node_id)  # Trie les nœuds après l'ajout
        self.initialize_neighbours()  # Réinitialise les voisins

        print(f"\nNouveau nœud ajouté : {new_node.node_id}")
        print("Mise à jour des voisins...\n")
        self.print_nodes()

    def print_nodes(self):
        """Affiche la liste des nœuds et leurs voisins."""
        print("\nÉtat actuel de la DHT :")
        for id, node in enumerate(self.nodes):
            left_id = node.leftNeighbour.node_id if node.leftNeighbour else None
            right_id = node.rightNeighbour.node_id if node.rightNeighbour else None
            print(f"Node {id} : {node.node_id}")
            print(f"   Left Neighbour : {left_id}")
            print(f"   Right Neighbour: {right_id}")
        print("-" * 50)

# Initialisation de l'environnement
env = simpy.Environment()

# Initialisation de la DHT avec 4 nœuds
dht = DHT(env, 4)
dht.print_nodes()

# Ajout dynamique d'un nœud
dht.add_node()

# Lancement de la simulation
env.run(until=4)

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
        self.nodes = []
        
        # Création initiale des nœuds
        for _ in range(num_nodes):
            self.add_node(random.getrandbits(128))

    def initialize_neighbours(self):
        """Met à jour les voisins après toute modification."""
        num_nodes = len(self.nodes)
        if num_nodes > 1:
            for i in range(num_nodes):
                self.nodes[i].leftNeighbour = self.nodes[i - 1]  # Voisin gauche
                self.nodes[i].rightNeighbour = self.nodes[(i + 1) % num_nodes]  # Voisin droit (anneau)

    def add_node(self, node_id):
        """Ajoute un nœud à la bonne place en parcourant les nœuds existants."""
        new_node = Noeud(self.env, node_id)
        
        if not self.nodes:
            # Premier nœud ajouté
            self.nodes.append(new_node)
            new_node.leftNeighbour = new_node
            new_node.rightNeighbour = new_node
        else:
            # Trouver la bonne position d'insertion
            inserted = False
            for i in range(len(self.nodes)):
                if self.nodes[i].node_id > node_id:
                    self.nodes.insert(i, new_node)
                    inserted = True
                    break
            
            if not inserted:
                # Si le nœud a le plus grand ID, on l'ajoute à la fin
                self.nodes.append(new_node)

            # Mise à jour des voisins après insertion
            self.initialize_neighbours()

        print(f"\nNouveau nœud ajouté : {node_id}")
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

# Ajout dynamique de nouveaux nœuds
dht.add_node(random.getrandbits(128))
dht.add_node(random.getrandbits(128))

# Lancement de la simulation
env.run(until=4)

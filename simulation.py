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
        elif num_nodes == 1:
            # Si un seul nœud, il est son propre voisin
            self.nodes[0].leftNeighbour = self.nodes[0]
            self.nodes[0].rightNeighbour = self.nodes[0]

    def add_node(self, node_id):
        """Ajoute un nœud à la bonne place en parcourant la DHT."""
        new_node = Noeud(self.env, node_id)

        if not self.nodes:
            # Premier nœud ajouté
            self.nodes.append(new_node)
        else:
            # Trouver la bonne position d'insertion
            inserted = False
            for i in range(len(self.nodes)):
                if self.nodes[i].node_id > node_id:
                    self.nodes.insert(i, new_node)
                    inserted = True
                    break
            
            if not inserted:
                self.nodes.append(new_node)

        # Mise à jour des voisins après insertion
        self.initialize_neighbours()
        print(f"\nNouveau nœud ajouté : {node_id}")
        self.print_nodes()

    def remove_node(self, node_id):
        """Supprime un nœud et met à jour les voisins."""
        node_to_remove = next((node for node in self.nodes if node.node_id == node_id), None)

        if node_to_remove:
            if len(self.nodes) == 1:
                # Si c'était le dernier nœud, la DHT devient vide
                self.nodes = []
                print(f"\nLe dernier nœud {node_id} a quitté. La DHT est maintenant vide.")
            else:
                # Mise à jour des voisins
                left_neighbour = node_to_remove.leftNeighbour
                right_neighbour = node_to_remove.rightNeighbour

                left_neighbour.rightNeighbour = right_neighbour
                right_neighbour.leftNeighbour = left_neighbour

                # Retirer le nœud de la liste
                self.nodes.remove(node_to_remove)
                self.initialize_neighbours()
                print(f"\nNœud {node_id} a quitté la DHT.")
            
            self.print_nodes()
        else:
            print(f"\nLe nœud {node_id} n'existe pas dans la DHT.")

    def print_nodes(self):
        """Affiche la liste des nœuds et leurs voisins."""
        print("\nÉtat actuel de la DHT :")
        if not self.nodes:
            print("La DHT est vide.")
        else:
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

# Ajout de nouveaux nœuds
dht.add_node(random.getrandbits(128))
dht.add_node(random.getrandbits(128))

# Suppression d'un nœud existant
node_to_remove = dht.nodes[2].node_id  # Suppression du 3e nœud
dht.remove_node(node_to_remove)

# Lancement de la simulation
env.run(until=4)

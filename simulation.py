import simpy
import random

class Node:
    """Représente un noeud dans la DHT."""
    def __init__(self, env, node_id, dht):
        self.env = env
        self.node_id = node_id
        self.dht = dht  # Liste de tous les noeuds
        env.process(self.run())
    
    def set_right_neighbor_id(self, right_neighbor_id):
        self.right_neighbor_id = right_neighbor_id

    def set_left_neighbor_id(self, left_neighbor_id):
        self.left_neighbor_id = left_neighbor_id
        

    def run(self):
        """Exécute des actions."""
        while True:
            yield self.env.timeout(random.uniform(3, 6))  # Attente avant prochaine action


# Initialisation de l'environnement
env = simpy.Environment()

# Générer liste random d'id trié
node_nb = 4
id_size = 8
id_list = [random.getrandbits(id_size) for i in range(node_nb)]
id_list.sort()

dht = [Node(env, id_list[i], None) for i in range(node_nb)]

# Mise à jour des références DHT dans chaque noeud
for i, node in enumerate(dht):
    node.dht = dht
    # Cas premier noeud de la liste
    if i == 0:
        node.right_neighbor_id = dht[i+1].node_id
        node.left_neighbor_id = dht[-1].node_id     # dernier noeud de la liste (cercle)

    # Cas dernier noeud de la liste
    elif i == (len(dht)-1): 
        node.right_neighbor_id = dht[0].node_id
        node.left_neighbor_id = dht[i-1].node_id

    # Cas usuel
    else :
        node.right_neighbor_id = dht[i+1].node_id
        node.left_neighbor_id = dht[i-1].node_id

# test voisinage
for node in dht:
    print(f"node id = {node.node_id}")
    print(f"right id = {node.right_neighbor_id}")
    print(f"left id = {node.left_neighbor_id}")

# Lancer la simulation
env.run(until=20)

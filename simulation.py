import simpy
import random

class Node:
    """Représente un noeud dans la DHT."""
    def __init__(self, env, node_id, dht, network):
        self.env = env
        self.node_id = node_id
        self.network = network  # Référence au réseau (gestion des messages)
        self.dht = dht  # Liste de tous les noeuds
        self.right_neighbor_id = None
        self.left_neighbor_id = None
        self.env.process(self.run())

    def send_message(self, target_id, type, message):
        """Envoie un message à un autre noeud."""
        latency = random.uniform(1, 3)  # Simulation d'un délai réseau
        yield self.env.timeout(latency)
        print(f"[{self.env.now}] Noeud {self.node_id} envoie '{message}' à Noeud {target_id}")
        self.network.deliver(self.node_id, target_id, type, message)  # Remettre le message au réseau

    def receive_message(self, sender_id, type, message):
        """Réception d'un message et réponse après traitement."""
        yield self.env.timeout(random.uniform(1, 2))  # Simulation du temps de traitement

        if type == "JOIN_REQUEST":
            self.env.process(self.find_position(sender_id))

        if type == "POSITION FOUND":
            pass

        else :
            #print(f"[{self.env.now}] Noeud {self.node_id} reçoit '{message}' de Noeud {sender_id}")

            self.env.process(self.send_message(sender_id, f"Réponse à '{sender_id}', salut"))  # Réponse


    def find_position(self, new_node_id):
        # Vérifier si le nouvel ID est entre lui-même et son voisin droit.
        if self.node_id < new_node_id and new_node_id < self.right_neighbor_id:
            pass
        


    def run(self):
        """Processus principal du noeud : envoie des messages aléatoires."""
        while True:
            yield self.env.timeout(random.uniform(3, 6))  # Pause entre deux messages
            target_id = random.choice([self.right_neighbor_id, self.left_neighbor_id])
            self.env.process(self.send_message(target_id, f"Hello from {self.node_id}"))

            if self.dht == None: # Si le noeud est nouveau et donc pas dans la dht
                pass


class Network:
    """Gère les messages entre noeuds."""
    def __init__(self, env, dht):
        self.env = env
        self.dht = dht

    def deliver(self, sender_id, target_id, message):
        """Livre un message au bon noeud."""
        target_node = next(n for n in self.dht if n.node_id == target_id)
        env.process(target_node.receive_message(sender_id, message))


# Initialisation de la dht et de l'environnement
node_nb = 4
env = simpy.Environment()
test_neighbor = False

# Générer liste random d'id trié
id_size = 8
id_list = [random.getrandbits(id_size) for i in range(node_nb)]
id_list.sort()

dht = [Node(env, id_list[i], None, None) for i in range(node_nb)]

network = Network(env, dht)
# Mise à jour des références DHT dans chaque noeud
for i, node in enumerate(dht):
    node.dht = dht
    node.network = network
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
if test_neighbor:
    for node in dht:
        print(f"node id = {node.node_id}")
        print(f"right id = {node.right_neighbor_id}")
        print(f"left id = {node.left_neighbor_id}")

# Lancer la simulation
env.run(until=20)
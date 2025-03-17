import simpy
import random

class Message:
    def __init__(self, sender_id, target_id, type, body):
        self.sender_id = sender_id
        self.target_id = target_id
        self.type = type
        self.body = body

    def __str__(self):
        return f"Message from {self.sender_id} to {self.target_id} : {self.body} et le type est {self.type}"

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
        self.datas = []

        if self.env:
            self.env.process(self.run())

    def send_message(self, target_id, type, body):
        """Envoie un message à un autre nœud."""
        message = Message(self.node_id, target_id, type, body)
        latency = random.uniform(1, 3)  # Simulation d'un délai réseau
        yield self.env.timeout(latency)

        print(f"[{self.env.now}] Noeud {self.node_id} envoie '{message.body}' à Noeud {message.target_id}")
        self.network.deliver(message)  # Remettre le message au réseau

    def receive_message(self, message : Message):
        """Réception d'un message et réponse après traitement."""
        yield self.env.timeout(random.uniform(1, 2))  # Simulation du temps de traitement

        print(f"[{self.env.now}] Noeud {self.node_id} reçoit '{message.body}' de Noeud {message.sender_id}")
        if message.type == "JOIN_REQUEST": # Si requete d'insertion, lancement procédure insertion
            self.env.process(self.find_position(message.sender_id))

        elif message.type == "JOIN_REQUEST_FOLLOW_UP": # Si requete d'insertion suivie, lancement procédure insertion
            self.env.process(self.find_position(message.body))

        elif message.type == "POSITION_FOUND" and isinstance(message, list):
            self.dht = self.network.dht  # On récupère la DHT depuis le réseau
            # Le corps du message va contenir un liste avec les nouveaux voisins du nouveau noeud
            self.right_neighbor_id = message.body[0]
            self.left_neighbor_id = message.body[1]
            self.env.process(self.send_message(self.right_neighbor_id, "NEIGHBOR_REQUEST", "left"))
            print(f"[{self.env.now}] Noeud {self.node_id} s'est inséré entre {self.right_neighbor_id} et {self.left_neighbor_id}")

        elif message.type == "NEIGHBOR_REQUEST": # Message venant de nouveaux noeuds voulant s'insérer
            if message.body == "left":
                self.left_neighbor_id = message.sender_id
            if message.body == "right":
                self.right_neighbor_id = message.sender_id

            print(f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin {message.body} {message.sender_id}")

        elif message.type == "LEAVE_REQUEST": # Message venant de noeuds voulant quitter
            if message.sender_id == self.left_neighbor_id:
                self.left_neighbor_id = message.body
                print(f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin gauche {self.left_neighbor_id}")

            elif message.sender_id == self.right_neighbor_id:
                self.right_neighbor_id = message.body
                print(f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin droit {self.right_neighbor_id}")

            print(f"[{self.env.now}] Noeud {message.sender_id} a quitté")

        elif message.type == "DATA_TRANSFER": # Message de transfert de données
            self.datas.extend(message.body)
            data_ids = [data.id for data in message.body]
            print(f"[{self.env.now}] Noeud {self.node_id} a reçu des données de Noeud {message.sender_id} avec les IDs : {data_ids}")

        elif message.type == "NORMAL_MESSAGE": # Si c'est un msg pas important
            pass
            #print(f"[{self.env.now}] Noeud {self.node_id} reçoit '{message}' de Noeud {sender_id}")
            #self.env.process(self.send_message(message.sender_id, "NORMAL_MESSAGE", f"Réponse à '{message.sender_id}', salut"))  # Réponse
        else:
            print(f"[{self.env.now}] Noeud {self.node_id} a reçu un message inconnu : {message}")

    def find_position(self, new_node_id):
        yield self.env.timeout(1)  # Simulation d'un petit délai avant traitement
        found = False

        print(f"new node id = {new_node_id}")
        # Condition 1 : Cas courant : Si le noeud courant est inférieur au nouveau noeud et son voisin droit est supérieur
        if self.node_id < new_node_id and new_node_id < self.right_neighbor_id :
            found = True
            print("Condition 1 : Cas courant")

        # Condition 2 : nouveaux noeud est le plus petit
        if self.node_id > self.right_neighbor_id and new_node_id < self.right_neighbor_id :
            found = True
            print("Condition 2 : nouveaux noeud est le plus petit")

        # Condition 3 : nouveaux noeud est le plus grand
        if self.node_id < new_node_id and  self.right_neighbor_id < new_node_id and self.node_id > self.right_neighbor_id:
            found = True
            print("Condition 3 : nouveaux noeud est le plus grand")

        if found :
            print("found")
            # Envoie msg position trouvée
            yield self.env.process(self.send_message(new_node_id, "POSITION_FOUND", [self.right_neighbor_id, self.node_id]))
            # Mise à jour du voisin droit du noeud
            self.right_neighbor_id = new_node_id
            print(f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin droit {self.right_neighbor_id}")

        else: # Si la position n'est pas bonne
            print("not found")
            # Transmettre la requête au voisin droit
            yield self.env.process(self.send_message(self.right_neighbor_id, "JOIN_REQUEST_FOLLOW_UP", new_node_id))

    def run(self):
        """Processus principal du noeud : gère son intégration et les messages réguliers."""
        if self.dht is None:  # Si le nœud est nouveau
            self.is_new = True  # Marquer le nœud comme en attente d'intégration
            yield self.env.timeout(random.uniform(1, 3))  # Délai avant de rejoindre la DHT

            if not network.dht:
                return  # Eviter de continuer si aucun nœud n'est disponible
            rand = random.randint(0, len(network.dht)-1)
            target_id = network.dht[rand].node_id

            print("L'id du target est : " + str(target_id))
            #target_id = random.choice([n.node_id for n in self.network.dht])
            self.env.process(self.send_message(target_id, "JOIN_REQUEST", "JOIN_REQUEST"))
        else:
            self.is_new = False  # Le nœud fait partie de la DHT

        while True:
            yield self.env.timeout(random.uniform(3, 6))  # Pause entre deux messages

            if not self.is_new:  # Si le nœud est bien intégré
                target_id = random.choice([self.right_neighbor_id, self.left_neighbor_id])
                #self.env.process(self.send_message(target_id, "NORMAL_MESSAGE", f"Hello from {self.node_id}"))

    def transfer_data(self):
        """Transfère les données aux voisins lorsque le nœud quitte."""
        if self.left_neighbor_id is not None:
            self.env.process(self.send_message(self.left_neighbor_id, "DATA_TRANSFER", self.datas))
        if self.right_neighbor_id is not None:
            self.env.process(self.send_message(self.right_neighbor_id, "DATA_TRANSFER", self.datas))

class Data:
    def __init__(self, id, dht, id_size):
        self.id = id
        self.id_max = (1 << id_size)
        self.closest_node = self.calculate_closest_node(dht)

        if self.closest_node:
            self.store_on_responsible_and_neighbors()
            print(f"Data {self.id} stockée sur {self.closest_node.node_id}, {self.closest_node.left_neighbor_id}, {self.closest_node.right_neighbor_id}")

    def calculate_closest_node(self, dht):
        """Trouve le nœud le plus proche au-dessus."""
        value = self.id % self.id_max
        return find_closest_node_above(value, dht)

    def store_on_responsible_and_neighbors(self):
        """Stocke la donnée sur le nœud responsable + ses 2 voisins."""
        self.closest_node.datas.append(self)
        if self.closest_node.left_neighbor_id is not None:
            left_neighbor = next((n for n in self.closest_node.dht if n.node_id == self.closest_node.left_neighbor_id), None)
            if left_neighbor:
                left_neighbor.datas.append(self)
        if self.closest_node.right_neighbor_id is not None:
            right_neighbor = next((n for n in self.closest_node.dht if n.node_id == self.closest_node.right_neighbor_id), None)
            if right_neighbor:
                right_neighbor.datas.append(self)

class Network:
    """Gère les messages entre noeuds."""
    def __init__(self, env, dht):
        self.env = env
        self.dht = dht

    def deliver(self, message : Message):
        """Livre un message au bon noeud."""
        for node in self.dht:
            if node.node_id == message.target_id:
                target_node = node
        #target_node = next((n for n in self.dht if n.node_id == target_id), None)

        if target_node is None:
            print(f"[{self.env.now}] ERREUR : Noeud {message.target_id} introuvable dans la DHT. Message perdu.")
            return  # On arrête ici pour éviter un crash

        self.env.process(target_node.receive_message(message))

def find_closest_node_above(value, dht):
    """Trouve le nœud ayant un `node_id` juste supérieur ou le plus proche au-dessus."""
    possible_nodes = [node for node in dht if node.node_id >= value]
    if possible_nodes:
        return min(possible_nodes, key=lambda node: node.node_id)
    else:
        return min(dht, key=lambda node: node.node_id)

def add_new_node(env, network, id_size):
    yield env.timeout(random.uniform(1, 5))  # Simule un délai avant l'arrivée du nœud
    new_node_id = random.getrandbits(id_size)
    new_node = Node(env, new_node_id, network.dht, network)  # Correctement initialisé

    print(f"[{env.now}] Nouveau noeud {new_node_id} créé et tente de rejoindre la DHT.")

    # Lancer le processus de connexion
    rand = random.randint(0, len(network.dht)-1)
    for node in network.dht:
        print(node.node_id)
    target_id = network.dht[rand].node_id

    # Ajouter le nouveau nœud à la liste DHT
    network.dht.append(new_node)

    print("L'id du target est : " + str(target_id))

    # Ajouter le nouveau nœud à la liste DHT
    network.dht.append(new_node)

    #target_id = random.choice([n.node_id for n in network.dht if n.node_id != new_node_id])
    env.process(new_node.send_message(target_id, "JOIN_REQUEST", "JOIN_REQUEST"))

def node_quit(env, node):
    yield env.timeout(random.uniform(1, 5))  # Simule un délai avant le départ du nœud
    print(f"[{env.now}] Noeud {node.node_id} tente de quitter le voisinage.")

    # Transférer les données aux voisins
    node.transfer_data()

    # Informer les voisins du départ
    env.process(node.send_message(node.left_neighbor_id, "LEAVE_REQUEST", node.right_neighbor_id))
    env.process(node.send_message(node.right_neighbor_id, "LEAVE_REQUEST", node.left_neighbor_id))

# Initialisation de la dht et de l'environnement
node_nb = 4
env = simpy.Environment()
test_neighbor = True

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
        print(f"left id = {node.left_neighbor_id}")
        print(f"right id = {node.right_neighbor_id}")
        print(f"node id = {node.node_id}")
        print(f"------------------")

# Création des données et assignation du nœud le plus proche
data_list = [Data(random.getrandbits(id_size), dht, id_size) for _ in range(10)]

# Affichage des résultats
for data in data_list:
    print(f"Data ID: {data.id}, Closest Node ID: {data.closest_node.node_id}")
print(f"------------------------")

# Lancer la simulation
#env.process(add_new_node(env, network, id_size))

quitting_node = random.choice(dht)
env.process(node_quit(env, quitting_node))
env.run(until=200)

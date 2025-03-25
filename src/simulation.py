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
        self.lock = simpy.Resource(env, capacity=1)  # Verrou pour le nœud, une ressource pour assurer la séquentialité
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

    def receive_message(self, message: Message):
        """Réception d'un message et réponse après traitement."""
        yield self.env.timeout(random.uniform(1, 2))  # Simulation du temps de traitement

        print(f"[{self.env.now}] Noeud {self.node_id} reçoit '{message.body}' de Noeud {message.sender_id}")
        if message.type == "JOIN_REQUEST": # Si requete d'insertion, lancement procédure insertion
            self.env.process(self.find_position(message.sender_id))

        elif message.type == "JOIN_REQUEST_FOLLOW_UP": # Si requete d'insertion suivie, lancement procédure insertion
            self.env.process(self.find_position(message.body))

        elif message.type == "POSITION_FOUND":
            self.dht = self.network.dht  # On récupère la DHT depuis le réseau
            # Le corps du message va contenir un liste avec les nouveaux voisins du nouveau noeud
            self.right_neighbor_id = message.body[0]
            self.left_neighbor_id = message.body[1]
            self.env.process(self.send_message(self.right_neighbor_id, "NEIGHBOR_REQUEST", "left"))
            self.env.process(self.send_message(self.left_neighbor_id, "NEIGHBOR_REQUEST", "right"))
            print(f"[{self.env.now}] Noeud {self.node_id} s'est inséré entre {self.right_neighbor_id} et {self.left_neighbor_id}")

        elif message.type == "NEIGHBOR_REQUEST": # Message venant de nouveaux noeuds voulant s'insérer
            if message.body == "left":
                self.left_neighbor_id = message.sender_id
            if message.body == "right":
                self.right_neighbor_id = message.sender_id

            print(f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin {message.body} {message.sender_id}")

        elif message.type == "LEAVE_REQUEST": # Message venant de noeuds voulant quitter
            with self.lock.request() as req:  # Verrouiller la section où on modifie les voisins
                yield req
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

        # Vérifier la position et sécuriser l'accès aux voisins avec un verrou
        with self.lock.request() as req:
            yield req
            print(f"new node id = {new_node_id}")

            # Condition initialisation : il n'y a qu'un noeud
            if len(self.network.dht) == 2:
                found = True
                print("Condition initialisation : il n'y a qu'un noeud ")

            # Conditions pour déterminer la bonne position
            if self.node_id < new_node_id and new_node_id < self.right_neighbor_id:
                found = True
                print("Condition 1 : Cas courant")

            if self.node_id > self.right_neighbor_id and new_node_id < self.right_neighbor_id:
                found = True
                print("Condition 2 : nouveaux noeud est le plus petit")

            if self.node_id < new_node_id and self.right_neighbor_id < new_node_id and self.node_id > self.right_neighbor_id:
                found = True
                print("Condition 3 : nouveaux noeud est le plus grand")

            if found:
                print("found")
                if len(self.network.dht) == 2:
                    yield self.env.process(self.send_message(new_node_id, "POSITION_FOUND", [self.right_neighbor_id, self.right_neighbor_id]))
                    # Ce n'est pas très beau mais il faut mettre à jour les voisins du noeud initial
                    yield self.env.process(self.send_message(self.node_id, "POSITION_FOUND", [new_node_id, new_node_id]))
                else:
                    yield self.env.process(self.send_message(new_node_id, "POSITION_FOUND", [self.right_neighbor_id, self.node_id]))
                    self.right_neighbor_id = new_node_id
                    print(f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin droit {self.right_neighbor_id}")
            else:  # Si la position n'est pas bonne
                print("not found")
                yield self.env.process(self.send_message(self.right_neighbor_id, "JOIN_REQUEST_FOLLOW_UP", new_node_id))

    def run(self):
        """Processus principal du nœud : gère son intégration et les messages réguliers."""
        if self.dht is None:  # Si le nœud est nouveau
            self.is_new = True  # Marquer le nœud comme en attente d'intégration
            yield self.env.timeout(random.uniform(1, 3))  # Délai avant de rejoindre la DHT

            if not self.network.dht:
                return  # Eviter de continuer si aucun nœud n'est disponible
            rand = random.randint(0, len(self.network.dht)-1)
            target_id = self.network.dht[rand].node_id

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
            left_neighbor = next((n for n in self.dht if n.node_id == self.left_neighbor_id), None)
            if left_neighbor:
                left_neighbor.datas.extend(self.datas)
                print(f"[{self.env.now}] Les données du noeud {self.node_id} ont été transférées à {left_neighbor.node_id}")
                print(f"[{self.env.now}] Données transférées : {[data.id for data in self.datas]}")
        elif self.right_neighbor_id is not None:
            right_neighbor = next((n for n in self.dht if n.node_id == self.right_neighbor_id), None)
            if right_neighbor:
                right_neighbor.datas.extend(self.datas)
                print(f"[{self.env.now}] Les données du noeud {self.node_id} ont été transférées à {right_neighbor.node_id}")
                print(f"[{self.env.now}] Données transférées : {[data.id for data in self.datas]}")

class Data:
    def __init__(self, id, dht, id_size):
        self.id = id
        self.valeur_max = (1 << id_size) #Valeur maximum possible de l'id
        self.closest_node = self.calculate_closest_node(dht)

        if self.closest_node:
            self.store_on_responsible_and_neighbors()
            print(f"Data {self.id} stockée sur {self.closest_node.node_id}, {self.closest_node.left_neighbor_id}, {self.closest_node.right_neighbor_id}")

    def calculate_closest_node(self, dht):
        """Trouve le nœud le plus proche au-dessus."""
        value = self.id % self.valeur_max
        return find_closest_node_above(value, dht)

    def store_on_responsible_and_neighbors(self):
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

    def deliver(self, message: Message):
        """Livre un message au bon noeud."""
        target_node = None
        for node in self.dht:
            if node.node_id == message.target_id:
                target_node = node
                break

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

class DHT:
    def __init__(self):
        self.nb_node = 4  # Nombre de noeuds à l'initialisation
        self.id_size = 12
        self.env = simpy.Environment()
        self.test_neighbor = True

        n_init = Node(self.env, random.getrandbits(self.id_size), None, None)
        n_init.left_neighbor_id = n_init.node_id
        n_init.right_neighbor_id = n_init.node_id
        n_init.data_store = []

        self.dht = [n_init]
        self.network = Network(self.env, self.dht)
        n_init.network = self.network
        n_init.dht = self.dht

    def add_new_node(self):
        yield self.env.timeout(random.uniform(1, 5))
        new_node_id = random.getrandbits(self.id_size)
        new_node = Node(self.env, new_node_id, self.network.dht, self.network)
        new_node.data_store = []

        print(f"[{self.env.now}] Nouveau noeud {new_node_id} créé et tente de rejoindre la DHT.")
        rand = random.randint(0, len(self.network.dht) - 1)
        target_id = self.network.dht[rand].node_id

        self.env.process(new_node.send_message(target_id, "JOIN_REQUEST", "JOIN_REQUEST"))
        self.network.dht.append(new_node)

    def node_quit(self, node):
        yield self.env.timeout(random.uniform(1, 5))
        print(f"[{self.env.now}] Noeud {node.node_id} tente de quitter le voisinage.")

        # Transférer les données avant de quitter
        self.transfer_data_before_exit(node)

        self.env.process(node.send_message(node.left_neighbor_id, "LEAVE_REQUEST", node.right_neighbor_id))
        self.env.process(node.send_message(node.right_neighbor_id, "LEAVE_REQUEST", node.left_neighbor_id))

        # Mettre à jour la DHT après le départ
        self.update_storage_after_exit(node)

    def transfer_data_before_exit(self, node):
        """Transfère les données stockées sur un noeud quittant vers un autre noeud actif."""
        if hasattr(node, 'datas') and node.datas:
            target_node = random.choice([n for n in self.dht if n.node_id != node.node_id])
            target_node.datas.extend(node.datas)
            print(f"[{self.env.now}] Les données du noeud {node.node_id} ont été transférées au noeud {target_node.node_id}.")
            print(f"[{self.env.now}] Données transférées : {[data.id for data in node.datas]}")

    def update_storage_after_exit(self, node):
        """Met à jour la DHT après le départ d'un noeud."""
        self.dht.remove(node)
        print(f"[{self.env.now}] Le noeud {node.node_id} a quitté la DHT et la structure a été mise à jour.")

    def redistribute_data(self):
        """Réattribue les données après un changement de la DHT."""
        for node in self.dht:
            for data in node.datas:
                data.closest_node = find_closest_node_above(data.id, self.dht)
                if data.closest_node != node:
                    data.closest_node.datas.append(data)
                    node.datas.remove(data)
                    print(f"[{self.env.now}] Data {data.id} déplacée vers {data.closest_node.node_id}")

    def creation_DHT(self):
        while len(self.network.dht) < self.nb_node:
            self.env.process(self.add_new_node())
            self.network.dht.sort(key=lambda node: node.node_id)
            self.env.run(until=self.env.now + 30)

        if self.test_neighbor:
            for node in self.network.dht:
                print(f"node id = {node.node_id}")
                print(f"right id = {node.right_neighbor_id}")
                print(f"left id = {node.left_neighbor_id}")
                print("______________________________________________")

    def create_and_store_data(self, num_data=5):
        """Crée des données et les stocke dans la DHT."""
        for _ in range(num_data):
            yield self.env.timeout(random.uniform(1, 5))
            data_id = random.getrandbits(self.id_size)
            data = Data(data_id, self.dht, self.id_size)
            print(f"[{self.env.now}] Donnée {data_id} insérée dans la DHT.")

    def run(self):
        self.creation_DHT()
        self.env.process(self.add_new_node())
        self.env.process(self.create_and_store_data(5))

        if self.dht:
            quitting_node = random.choice(self.dht)
            self.env.process(self.node_quit(quitting_node))

        self.env.run(until=300)

if __name__ == "__main__":
    dht = DHT()
    dht.run()

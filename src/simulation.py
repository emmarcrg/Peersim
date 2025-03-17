import simpy
import random

class Message: 
    def __init__(self, sender_id, target_id, type, body):
        self.sender_id = sender_id
        self.target_id = target_id
        self.type = type
        self.body = body
        self.following_nodes = []

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
        self.far_nodes_id = []

    def send_message(self, target_id, type, body):
        """Envoie un message à un autre nœud."""
        message = Message(self.node_id, target_id, type, body)
        message.following_nodes.append(self.node_id)
        latency = random.uniform(1, 3)  # Simulation d'un délai réseau
        yield self.env.timeout(latency)

        print(f"[{self.env.now}] Noeud {self.node_id} envoie '{message.body}' à Noeud {message.target_id}")
        self.network.deliver(message)  # Remettre le message au réseau

    def forward_message(self, message : Message):
            """Envoie un message à un autre nœud."""
            latency = random.uniform(1, 3)  # Simulation d'un délai réseau
            yield self.env.timeout(latency)

            Message.following_nodes.append(self.node_id)

            print(f"[{self.env.now}] Noeud {self.node_id} fait suivre '{message.body}' à Noeud {message.target_id}")
            self.network.deliver(message)  # Remettre le message au réseau


    def receive_message(self, message : Message):
        """Réception d'un message et réponse après traitement."""
        yield self.env.timeout(random.uniform(1, 2))  # Simulation du temps de traitement
        
        # Process ajout potentiel lien long (en multiple de 2 (à partir de 4))
        index = 3
        pas = 1  # On commence avec un pas de 2^0 = 1
        while index < len(message.following_nodes): # Peut etre besoin d'inverser la liste
            #print(f"Élément à l'index {index}: {message.following_nodes[index]}")
            index += pas
            pas *= 2  # Double le pas à chaque itération
            if not (message.following_nodes[index] in self.far_nodes_id):
                self.far_nodes_id.append(message.following_nodes[index])
                print(f"[{self.env.now}] Noeud {self.node_id} ajoute en lien long {message.following_nodes[index]}")



        print(f"[{self.env.now}] Noeud {self.node_id} reçoie '{message.body}' de Noeud {message.sender_id}")
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

                            if message.sender_id == self.right_neighbor_id:
                                self.right_neighbor_id = message.body
                                print(f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin droit {self.right_neighbor_id}")

                            if message.sender_id in self.far_nodes_id:
                                self.far_nodes_id.remove(message.body)
                                print(f"[{self.env.now}] Noeud {self.node_id} a retiré des ses liens long {message.body}")

                            print(f"[{self.env.now}] Noeud {message.sender_id} a quitté")


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
            #print(f"new node id = {new_node_id}")
            #print(f"right = {self.right_neighbor_id}")
            #print(f"left = {self.left_neighbor_id}")
            # Conditions pour déterminer la bonne position
            #print(f"self.node_id < new_node_id {self.node_id < new_node_id}")
            #print(f"new_node_id < self.right_neighbor_id {new_node_id < self.right_neighbor_id}")
            if self.node_id < new_node_id and new_node_id < self.right_neighbor_id:
                found = True
                print("Condition 1 : Cas courant")

            #print(f"self.node_id > self.right_neighbor_id {self.node_id > self.right_neighbor_id}")
            #print(f"new_node_id < self.right_neighbor_id {new_node_id < self.right_neighbor_id}")
            if self.node_id > self.right_neighbor_id and new_node_id < self.right_neighbor_id:
                found = True
                print("Condition 2 : nouveaux noeud est le plus petit")

            if self.node_id < new_node_id and  self.right_neighbor_id < new_node_id and self.node_id > self.right_neighbor_id:
                found = True
                print("Condition 3 : nouveaux noeud est le plus grand")

            if found:
                print("found")
                yield self.env.process(self.send_message(new_node_id, "POSITION_FOUND", [self.right_neighbor_id, self.node_id]))
                self.right_neighbor_id = new_node_id
                print(f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin droit {self.right_neighbor_id}")
            
            else:  # Si la position n'est pas bonne
                # Utilisation des liens longs
                next_node_id = self.right_neighbor_id # Cas de base
                if self.far_nodes_id:
                    for node in self.far_nodes_id.sort():
                        if new_node_id > node: # Si un noeud des liens long est plus intéressant
                            next_node_id = node
                            break
                print("not found")
                yield self.env.process(self.send_message(next_node_id, "JOIN_REQUEST_FOLLOW_UP", new_node_id))
        
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


def add_new_node(env, network, id_size):
    yield env.timeout(random.uniform(1, 5))  # Simule un délai avant l'arrivée du nœud
    new_node_id = random.getrandbits(id_size)
    new_node = Node(env, new_node_id, network.dht, network)  # Correctement initialisé

    print(f"[{env.now}] Nouveau noeud {new_node_id} créé et tente de rejoindre la DHT.")

    # Lancer le processus de connexion
    rand = random.randint(0, len(network.dht)-1)
    #for node in network.dht:
        #print(node.node_id)

    # recup liste des noeuds conformes (ceux avec des voisins) à refaire
    liste_conforme = []
    for node in network.dht:
        print(f"[{env.now}] dht : {node.node_id}")
        print(node.right_neighbor_id != None and node.left_neighbor_id != None)
        if node.right_neighbor_id != None and node.left_neighbor_id != None:
            liste_conforme.append(node)
    if liste_conforme != []:
        target_id = liste_conforme[rand].node_id
        print("L'id du target est : " + str(target_id))
         #target_id = random.choice([n.node_id for n in network.dht if n.node_id != new_node_id])  
        env.process(new_node.send_message(target_id, "JOIN_REQUEST", "JOIN_REQUEST"))

        # Ajouter le nouveau nœud à la liste DHT
        network.dht.append(new_node)
   

    
    


def node_quit(env, node):
    yield env.timeout(random.uniform(1, 5))  # Simule un délai avant le départ du nœud
    print(f"[{env.now}] Noeud {node.node_id} tente de quitter le voisinage.")

    env.process(node.send_message(node.left_neighbor_id, "LEAVE_REQUEST", node.right_neighbor_id))
    env.process(node.send_message(node.right_neighbor_id, "LEAVE_REQUEST", node.left_neighbor_id))

# Initialisation de la dht et de l'environnement
node_nb = 4
env = simpy.Environment()
test_neighbor = True

# Générer liste random d'id trié
id_size = 16
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

# Lancer la simulation
for i in range(5):
    env.process(add_new_node(env, network, id_size))

quitting_node = random.choice(dht)
env.process(node_quit(env, quitting_node))
env.run(until=200)
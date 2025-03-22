import simpy
import random

class bcolors:
        #   print(bcolors.HEADER + "------" + bcolors.ENDC)
        HEADER = '\033[95m' # violet
        OKBLUE = '\033[94m' # dark blue
        OKCYAN = '\033[96m' # cyan
        OKGREEN = '\033[92m'   # green
        WARNING = '\033[93m'    # yellow
        FAIL = '\033[91m'   # red
        ENDC = '\033[0m'    # white
        BOLD = '\033[1m'    # bold
        UNDERLINE = '\033[4m' # underline

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
        self.far_nodes_id = []
        self.env.process(self.run())

    def send_message(self, target_id, type, body):
        """Envoie un nouveau message à un autre nœud."""
        message = Message(self.node_id, target_id, type, body)
        message.following_nodes.append(self.node_id)
        latency = random.uniform(1, 3)  # Simulation d'un délai réseau
        yield self.env.timeout(latency)

        print(bcolors.OKBLUE + f"[{self.env.now}] Noeud {self.node_id} envoie '{message.body}' à Noeud {message.target_id}" + bcolors.ENDC)
        self.network.deliver(message)  # Remettre le message au réseau

    def forward_message(self, message : Message):
            """Envoie un message d'un message dont le type et le body ne change pas"""
            latency = random.uniform(1, 3)  # Simulation d'un délai réseau
            yield self.env.timeout(latency)

            Message.following_nodes.append(self.node_id)

            print(f"[{self.env.now}] Noeud {self.node_id} fait suivre '{message.body}' à Noeud {message.target_id}")
            self.network.deliver(message)  # Remettre le message au réseau


    def receive_message(self, message : Message):
        """Réception d'un message et réponse après traitement."""
        yield self.env.timeout(random.uniform(1, 2))  # Simulation du temps de traitement
        
        # Process pour l'ajout potentiel d'un lien long (en multiple de 2 (on commence à 4))
        index = 3
        following_nodes_reversed = message.following_nodes[::-1] # On met le voisin du noeud courant au début de la liste
        while index < len(following_nodes_reversed): # Peut etre besoin d'inverser la liste
            #print(f"Élément à l'index {index}: {message.following_nodes[index]}")
            if not (following_nodes_reversed[index] in self.far_nodes_id):
                self.far_nodes_id.append(following_nodes_reversed[index])
                print(f"[{self.env.now}] Noeud {self.node_id} ajoute en lien long {message.following_nodes[index]}")
            index *= 2

        print(bcolors.OKCYAN + f"[{self.env.now}] Noeud {self.node_id} reçoie '{message.body}' de Noeud {message.sender_id}" + bcolors.ENDC)
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
            print(bcolors.OKGREEN + f"[{self.env.now}] Noeud {self.node_id} s'est inséré entre {self.left_neighbor_id} et {self.right_neighbor_id}" + bcolors.ENDC)

        elif message.type == "NEIGHBOR_REQUEST": # Message venant de nouveaux noeuds voulant s'insérer
            if message.body == "left":
                self.left_neighbor_id = message.sender_id
            if message.body == "right":
                self.right_neighbor_id = message.sender_id
            print(bcolors.HEADER + f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin {message.body} {message.sender_id}" + bcolors.ENDC)
        
        elif message.type == "LEAVE_REQUEST": # Message venant de noeuds voulant quitter
            with self.lock.request() as req:  # Verrouiller la section où on modifie les voisins
                            yield req
                            if message.sender_id == self.left_neighbor_id:
                                self.left_neighbor_id = message.body
                                print(bcolors.HEADER + f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin gauche {self.left_neighbor_id}" + bcolors.ENDC)

                            if message.sender_id == self.right_neighbor_id:
                                self.right_neighbor_id = message.body
                                print(bcolors.HEADER + f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin droit {self.right_neighbor_id}" + bcolors.ENDC)

                            if message.sender_id in self.far_nodes_id:
                                self.far_nodes_id.remove(message.body)
                                print(bcolors.FAIL + f"[{self.env.now}] Noeud {self.node_id} a retiré des ses liens long {message.body} + bcolors.ENDC")

                            print(bcolors.FAIL + f"[{self.env.now}] Noeud {message.sender_id} a quitté" + bcolors.ENDC)

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
            print(bcolors.WARNING + f"new node id = {new_node_id}" + bcolors.ENDC)

            #Condition initialisation : il n'y a qu'un noeud 
            if len(self.network.dht)==2:
                found = True 
                print(bcolors.WARNING + "Condition initialisation : il n'y a qu'un noeud" + bcolors.ENDC)

            # Conditions pour déterminer la bonne position
            if self.node_id < new_node_id and new_node_id < self.right_neighbor_id:
                found = True
                print(bcolors.WARNING + "Condition 1 : Cas courant" + bcolors.ENDC)

            if self.node_id > self.right_neighbor_id and new_node_id < self.right_neighbor_id:
                found = True
                print(bcolors.WARNING + "Condition 2 : nouveaux noeud est le plus petit" + bcolors.ENDC)

            if self.node_id < new_node_id and  self.right_neighbor_id < new_node_id and self.node_id > self.right_neighbor_id:
                found = True
                print(bcolors.WARNING + "Condition 3 : nouveaux noeud est le plus grand" + bcolors.ENDC)

            if found:
                print(bcolors.WARNING + "found" + bcolors.ENDC)
                if len(self.network.dht)==2:
                    yield self.env.process(self.send_message(new_node_id, "POSITION_FOUND", [self.right_neighbor_id, self.right_neighbor_id]))
                    #Ce n'est pas très beau mais il faut mettre à jour les voisins du noeud initial
                    yield self.env.process(self.send_message(self.node_id, "POSITION_FOUND", [new_node_id, new_node_id]))              
                else:
                    yield self.env.process(self.send_message(new_node_id, "POSITION_FOUND", [self.right_neighbor_id, self.node_id]))
                    self.right_neighbor_id = new_node_id
                    print(bcolors.HEADER + f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin droit {self.right_neighbor_id}" + bcolors.ENDC)

            else:  # Si la position n'est pas bonne
                # Utilisation des liens longs
                next_node_id = self.right_neighbor_id # Cas de base
                if self.far_nodes_id:
                    for node in self.far_nodes_id.sort():
                        if new_node_id > node: # Si un noeud des liens long est plus intéressant
                            next_node_id = node
                            break
                print(bcolors.WARNING + "position not right (not found)" + bcolors.ENDC)

                yield self.env.process(self.send_message(next_node_id, "JOIN_REQUEST_FOLLOW_UP", new_node_id))

    def run(self):
        """Processus principal du noeud : gère son intégration et les messages réguliers."""
        if self.dht is None:  # Si le nœud est nouveau
            self.is_new = True  # Marquer le nœud comme en attente d'intégration
            yield self.env.timeout(random.uniform(1, 3))  # Délai avant de rejoindre la DHT

            if not self.network.dht:
                return  # Eviter de continuer si aucun nœud n'est disponible
            rand = random.randint(0, len(self.network.dht)-1)
            target_id = self.network.dht[rand].node_id

            print(bcolors.WARNING + f"L'id du target est {str(target_id)}" + bcolors.ENDC)
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

class DHT : 
    def __init__(self):
        # Initialisation de la dht et de l'environnement
        self.nb_node = 4 # Nombre de noeud à l'initialisation
        self.id_size=12
        self.env = simpy.Environment()
        self.test_neighbor = True
        
        # On créé un noeud de manière aléatoire
        n_init = Node(self.env, random.getrandbits(self.id_size), None, None)
        
        #Le premier noeud se prend lui même comme voisin
        n_init.left_neighbor_id=n_init.node_id
        n_init.right_neighbor_id=n_init.node_id
        print(n_init.node_id)
        
        self.dht = [n_init]
        self.network = Network(self.env, self.dht)
        n_init.network = self.network
        n_init.dht = self.dht

    def add_new_node(self):
        yield self.env.timeout(random.uniform(1, 5))  # Simule un délai avant l'arrivée du nœud
        new_node_id = random.getrandbits(self.id_size)
        new_node = Node(self.env, new_node_id, self.network.dht, self.network)  # Correctement initialisé

        print(f"[{self.env.now}] Nouveau noeud {new_node_id} créé et tente de rejoindre la DHT.")       

        # recup liste des noeuds conformes (ceux avec des voisins) à refaire
        liste_conforme = []
        for node in self.network.dht:
            #print(f"[{self.env.now}] dht : {node.node_id}")
            #print(node.right_neighbor_id != None and node.left_neighbor_id != None)
            if node.right_neighbor_id != None and node.left_neighbor_id != None: # si le noeud a des voisin l et r
                liste_conforme.append(node)
        if liste_conforme != []: # si des noeuds sont conformes
            rand = random.randint(0, len(liste_conforme)-1)
            target_id = liste_conforme[rand].node_id
            print("L'id du target est : " + str(target_id))
            #target_id = random.choice([n.node_id for n in network.dht if n.node_id != new_node_id])  
            self.env.process(new_node.send_message(target_id, "JOIN_REQUEST", "JOIN_REQUEST"))


        # Ajouter le nouveau nœud à la liste DHT
        self.network.dht.append(new_node)

    def node_quit(self, node):
        yield self.env.timeout(random.uniform(1, 5))  # Simule un délai avant le départ du nœud
        print(f"[{self.env.now}] Noeud {node.node_id} tente de quitter le voisinage.")

        self.env.process(node.send_message(node.left_neighbor_id, "LEAVE_REQUEST", node.right_neighbor_id))
        self.env.process(node.send_message(node.right_neighbor_id, "LEAVE_REQUEST", node.left_neighbor_id))

    def creation_DHT(self):         
        #Tant que j'ai des noeuds à ajouter, je les rajoute 
        i=1
        while len(self.network.dht) < self.nb_node : 
            self.env.process(self.add_new_node())
            #On trie la DHT par ordre croissant des id des noeuds
            self.network.dht.sort(key=lambda node: node.node_id)
            self.env.run(until=self.env.now + 30)
            i+=1
        
        # test voisinage
        if self.test_neighbor:
            for node in self.network.dht:
                print(f"node id = {node.node_id}")
                print(f"right id = {node.right_neighbor_id}")
                print(f"left id = {node.left_neighbor_id}")
                print("______________________________________________")
                
if __name__ == "__main__":
    dht = DHT()
    dht.creation_DHT()
    for i in range(10) :
        dht.env.process(dht.add_new_node())
    quitting_node = random.choice(dht.dht)
    #dht.env.process(dht.node_quit(quitting_node))
    dht.env.run(until=300)
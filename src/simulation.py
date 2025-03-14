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
        """Envoie un message à un autre nœud."""
        latency = random.uniform(1, 3)  # Simulation d'un délai réseau
        yield self.env.timeout(latency)

        print(f"[{self.env.now}] Noeud {self.node_id} envoie '{message}' à Noeud {target_id}")
        self.network.deliver(self.node_id, target_id, type, message)  # Remettre le message au réseau


    def receive_message(self, sender_id, type, message):
        """Réception d'un message et réponse après traitement."""
        yield self.env.timeout(random.uniform(1, 2))  # Simulation du temps de traitement
        print(type)
        print(f"[{self.env.now}] Noeud {self.node_id} reçoie '{message}' de Noeud {sender_id}")
        if type == "JOIN_REQUEST": # Si requete d'insertion, lancement procédure insertion
            self.env.process(self.find_position(sender_id))
        
        elif type == "JOIN_REQUEST_FOLLOW_UP": # Si requete d'insertion suivie, lancement procédure insertion
            self.env.process(self.find_position(message))
            
        elif type == "POSITION_FOUND" and isinstance(message, list):
            self.dht = self.network.dht  # On récupère la DHT depuis le réseau
            # Le corps du message va contenir un liste avec les nouveaux voisins du nouveau noeud
            self.right_neighbor_id = message[0]
            self.left_neighbor_id = message[1]
            self.env.process(self.send_message(self.right_neighbor_id, "NEIGHBOR_REQUEST", "left"))
            print(f"[{self.env.now}] Noeud {self.node_id} s'est inséré entre {self.right_neighbor_id} et {self.left_neighbor_id}")

        elif type == "NEIGHBOR_REQUEST": # Message venant de nouveaux noeuds voulant s'insérer
            if message == "left":
                self.left_neighbor_id = sender_id
            elif message == "right":
                self.left_neighbor_id = sender_id

            print(f"[{self.env.now}] Noeud {self.node_id} a comme nouveau voisin {message} {sender_id}")

        else : # Si c'est un msg pas important
            #print(f"[{self.env.now}] Noeud {self.node_id} reçoit '{message}' de Noeud {sender_id}")
            self.env.process(self.send_message(sender_id, "NORMAL_MESSAGE", f"Réponse à '{sender_id}', salut"))  # Réponse


    def find_position(self, new_node_id):
        yield self.env.timeout(1)  # Simulation d'un petit délai avant traitement
        found = False
        print(f"left id = {self.left_neighbor_id}")
        print(f"right id = {self.right_neighbor_id}")
        print(f"node id = {self.node_id}")
        print(f"new node id = {new_node_id}")
        
        #Condition initialisation 1 : il n'y a qu'un noeud 
        if len(self.network.dht)==2:
            found = True 
            print("Condition initialisation 1 : il n'y a qu'un noeud ")            
            
        # Condition 1 : Cas courant : Si le noeud courant est inférieur au nouveau noeud et son voisin droit est supérieur
        if self.node_id < new_node_id and new_node_id < self.right_neighbor_id : 
            found = True
            print("Condition 1 : Cas courant")


        # Condition 2 : nouveaux noeud est le plus petit
        #if self.node_id > self.right_neighbor_id and new_node_id < self.right_neighbor_id :
        if self.network.dht[0].node_id>new_node_id:
            found = True
            print("Condition 2 : nouveaux noeud est le plus petit")
            id_min=self.network.dht[0]
            id_min.left_neighbor_id=new_node_id

        # Condition 3 : nouveaux noeud est le plus grand
        if self.node_id < new_node_id and  self.right_neighbor_id < new_node_id and self.node_id > self.right_neighbor_id:
            found = True
            print("Condition 3 : nouveaux noeud est le plus grand")
            id_min=self.network.dht[0]
            id_min.left_neighbor_id=new_node_id
        
        if found :
            print("found")
            # Envoie msg position trouvée
            if len(self.network.dht)==2:
                yield self.env.process(self.send_message(new_node_id, "POSITION_FOUND", [self.right_neighbor_id, self.right_neighbor_id]))
                yield self.env.process(self.send_message(self.node_id, "POSITION_FOUND", [new_node_id, new_node_id]))
            else:
                yield self.env.process(self.send_message(new_node_id, "POSITION_FOUND", [self.right_neighbor_id, self.node_id]))
                # Mise à jour du voisin droit du noeud 
                self.right_neighbor_id = new_node_id
                

        else: # Si la position n'est pas bonne
            print("not found")
            # Transmettre la requête au voisin droit
            yield self.env.process(self.send_message(self.right_neighbor_id, "JOIN_REQUEST_FOLLOW_UP", new_node_id))

        
    def run(self):
        """Processus principal du noeud : gère son intégration et les messages réguliers."""
        if self.dht is None:  # Si le nœud est nouveau
            self.is_new = True  # Marquer le nœud comme en attente d'intégration
            yield self.env.timeout(random.uniform(1, 3))  # Délai avant de rejoindre la DHT
            # Sélection d’un nœud existant
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
        
class Network:
    """Gère les messages entre noeuds."""
    def __init__(self, env, dht):
        self.env = env
        self.dht = dht

    def deliver(self, sender_id, target_id, type, message):
        """Livre un message au bon noeud."""
        for node in self.dht:
            if node.node_id == target_id:
                target_node = node
        #target_node = next((n for n in self.dht if n.node_id == target_id), None)
        
        if target_node is None:
            print(f"[{self.env.now}] ERREUR : Noeud {target_id} introuvable dans la DHT. Message perdu.")
            return  # On arrête ici pour éviter un crash

        self.env.process(target_node.receive_message(sender_id, type, message))


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

        # Lancer le processus de connexion
        rand = random.randint(0, len(self.network.dht)-1)
        target_id = self.network.dht[rand].node_id
        print("L'id du target est : " + str(target_id))
        #target_id = random.choice([n.node_id for n in network.dht if n.node_id != new_node_id]) 
        
        # Ajouter le nouveau nœud à la liste DHT
        self.network.dht.append(new_node)
         
        self.env.process(new_node.send_message(target_id, "JOIN_REQUEST", "JOIN_REQUEST"))

    def creation_DHT(self):         
        #On prend un deuxième noeud :
        #self.env.process(self.add_new_node())
        #self.env.run(until=200)
        i=1
        while i<self.nb_node : 
            print("On ajoute le noeud " + str(i))
            self.env.process(self.add_new_node())
            self.env.run(until=self.env.now + 10)
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
    
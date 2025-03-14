import random
import simpy

class DHT : 
    def __init__(self, env) :
        self.env = env
        
        # Création de mes noeuds
        print("Création des noeuds")
        n1 = Node(self.env, True, None)
        n2 = Node(self.env, True, None)
        n3 = Node(self.env, True, None)
        n4 = Node(self.env, True, None)
        
        #On créé la DHT
        print("Création de la DHT")
        id_1 = n1.get_id()
        id_2 = n2.get_id()
        id_3 = n3.get_id()
        id_4 = n4.get_id()
        nodes_id = [id_1, id_2, id_3, id_4]
        nodes_id.sort()
        #print(nodes_id)
        
        self.nodes=[]
        for i in range(0, len(nodes_id)):
            if nodes_id[i] == id_1:
                self.nodes.append(n1)
            elif nodes_id[i] == id_2:
                self.nodes.append(n2)
            elif nodes_id[i] == id_3:
                self.nodes.append(n3)
            elif nodes_id[i] == id_4:
                self.nodes.append(n4)
                
        '''for node in nodes:
            print(node.get_id())'''
        
        #On définit les voisins
        print("Définition des voisins")
        self.nodes[0].set_neighbors(self.nodes[3], self.nodes[1])
        self.nodes[1].set_neighbors(self.nodes[0], self.nodes[2])
        self.nodes[2].set_neighbors(self.nodes[1], self.nodes[3])
        self.nodes[3].set_neighbors(self.nodes[2], self.nodes[0])
        
        id = random.randint(0, len(self.nodes)-1)
        print(id)
        n5 = Node(self.env, False, self.nodes[id])
        self.nodes.append(n5)
        
        '''for node in nodes:
            node.print_neighbors()'''
        #On lance les noeuds comme étant des processus : 
        print("Lancement des noeuds partie 1")
        for node in self.nodes:
           self.env.process(node.run())


class Node : 
    def __init__(self, env , connect, bt_node) :
        self.env=env
        self.id = random.randint(0, 500000)
        self.is_connected = connect
        self.boostrap_node=bt_node
        print(self.id)
        if self.is_connected==False : 
            print("Création d'un noeud non connecté")
            self.ajouter_noeud()
        
    def get_id(self) :
        return self.id
    
    def set_neighbors(self, left, right) :
        self.left = left
        self.right = right
    
    def print_neighbors(self):
        res = " Le noeud " + str(self.id) 
        res +=" a pour voisins les noeuds " + str(self.left.get_id()) 
        res += " et " + str(self.right.get_id())
        print(res)
        
    def run(self):
        while True :
            print('Starting the processus of the node ', self.get_id(), ' at the time ', self.env.now)
            yield env.timeout((50))
        
    def get_place(self, new_node):
        while True :
            print('Starting research for node at ', self.env.now)
    
            #Chacun de mes noeuds sont considérés comme des processus 
            #Cas où le noeud que j'appelle est le plus proche de celui que je veux insérer : 
            if (self.left<new_node.get_id() and self.right>new_node.get_id()) :
                print('Node place found at ', self.env.now)
                if new_node.get_id()<self.get_id() :
                    return self.left, self
                elif new_node.get_id()>self.get_id() :
                    return self, self.right
            
            elif (self.left>new_node.get_id() ):
                print("Need to search further on the left neighbors")
                self.left.get_place(new_node)
                
            elif (self.right<new_node.get_id() ):
                print("Need to search further on the right neighbors")
                self.right.get_place(new_node)
            
            yield env.timeout(10)
    
    def ajouter_noeud(self):
        if self.is_connected==False :
            try : 
                print("Ajout du noeud")       
            
                # On lui demande de nous guider vers le noeud correspondant à mon voisin
                print("On part se chercher un noeud voisin")
                self.boostrap_node.get_place(self)
            except simpy.Interrupt :
                print("Interruption")
                print("Pas de noeuds trouvé")
            
            #On récupère les deux voisins de notre noeud
    
        
        
######## TEST ########
env = simpy.Environment()
dht = DHT(env)
env.run(until=400)


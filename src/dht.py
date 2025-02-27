import random
import simpy

class DHT : 
    def __init__(self, env) :
        # Création de mes noeuds
        n1 = Node(env)
        n2 = Node(env)
        n3 = Node(env)
        n4 = Node(env)
        
        #On créé la DHT
        id_1 = n1.get_id()
        id_2 = n2.get_id()
        id_3 = n3.get_id()
        id_4 = n4.get_id()
        nodes = [id_1, id_2, id_3, id_4]
        nodes.sort()
        #print(nodes)
        
        #On définit les voisins
        n1.set_neighbors(n4, n2)
        n2.set_neighbors(n1, n3)
        n3.set_neighbors(n2, n4)
        n4.set_neighbors(n3, n1)
        '''n1.print_neighbors()
        n2.print_neighbors()
        n3.print_neighbors()
        n4.print_neighbors()'''


class Node : 
    def __init__(self, env) :
        self.id = random.randint(0, 250000)
        #print(id)
        
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
        
        
######## TEST ########
env = simpy.Environment()
dht = DHT(env)
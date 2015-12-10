import numpy as np
import random,math
from pprint import pprint

def stateComp(states):
    compositeState = states[0]
    for state in states[1:]:
        compositeState =  np.kron(compositeState,state)
    return compositeState

def pick_random(distribution):
  for (x,y) in distribution:
      print("Probability of state", x, "is" , y)
      
  r, s = random.random(), 0
  for num in distribution:
    s += num[1]
    if s >= r:
      print("System collapsed to state:",num[0])
      return num[0]

def measure(state):
    x = list()
    i = 0
    for amplitude in state:
        x.append([i,np.absolute(state[i])**2/np.linalg.norm(state)**2])
        i += 1
    return (pick_random(x))

def splitToSub(state,configuration):
    #state is a tensor state, configuration is a list containing numbers according to which the system is splitted
    #for example: list(3,1) will split the system into two subsystems of 3 and 1 qubits respectively
    
    subDict = {} #subsystem dictionary
    bIndex = 0 #number of digits to use for the binary index
    
    for item in configuration:
        bIndex += item 
    
    for index,amplitude in enumerate(state):
        lastSplit = 0
        currentIndex = bin(index)[2:].zfill(bIndex)
        for subSystemIndex,config in enumerate(configuration):
            splitted = currentIndex[lastSplit:config+lastSplit]
            lastSplit = config
            key = "Subsystem" + str(subSystemIndex)+ " " + str(splitted)
            
            if key in subDict:
                subDict[key] += np.absolute(state[index])**2/np.linalg.norm(state)**2
            else:
                subDict[key] = np.absolute(state[index])**2/np.linalg.norm(state)**2
                
    for x,y in sorted(subDict.items()):
       pretty = x.split()
       print("Probability of", pretty[0], "state",pretty[1], "is: " , y)
        


def ctransp(x):
    return np.matrix(x).H

def checkH(x):
    return np.array_equal(x,ctransp(x))

def checkU(x):
    return np.allclose(np.linalg.inv(x),ctransp(x))

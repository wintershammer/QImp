import itertools
import numpy

qubitsXY = [0,1,2,3,4,5,6,7]
comb = itertools.product(qubitsXY,repeat=2)


f1 = [
        [ 0,0,0,0,1,0,0,0],
        [ 0,1,0,0,0,0,0,0],
        [ 0,0,0,0,0,1,0,0],
        [ 0,0,0,0,0,0,0,1],
        [ 0,1,0,0,0,0,0,0],
        [ 0,0,0,0,1,0,0,0],
        [ 0,0,0,0,0,0,0,1],
        [ 0,0,0,0,0,1,0,0]
    ]

f2 = [ [0,1] , [1,0]]


def applyFun(f,x):
    for index,item in enumerate(f[x]):
        if item == 1: return index
        
        

def generateComb(n):
    a = [x for x in range(0,n)]
    b = itertools.product(a,repeat=2)
    return b
    


def generateOracleBinary(fun,dim):
    combs = generateComb(len(fun[0]))
    oracle = [[0 for x in range(dim)] for x in range(dim)] 
    i = 0
    for index,(x,y) in enumerate(combs):
        xored = y ^ applyFun(fun,x)
        #print("x =",x,"y =",y,"|f(x) = ",applyFun(fun,x),"|y xor f(x) = ",xored)
        oracle[index][int(str(x) + str(xored),2)] = 1
    return numpy.array(oracle)

def generateOraclePairs(fun):
    combs = ((x,y) for x in range(len(fun)) for y in range((len(fun[0]))))
    pairs = []
    for index,(x,y) in enumerate(combs):
        xored = y ^ applyFun(fun,x)
        pairs.append([x,xored])
    return pairs

def generateOracle(fun):
    jumpBy = len(fun[0])
    pairs = generateOraclePairs(fun)
    oracle = [[0 for x in range(len(pairs))] for x in range(len(pairs))]
    for index,(x,y) in enumerate(pairs):
        oracle[index][jumpBy*x + y] = 1
    #print(pairs)
    return oracle

from mini import parseItem
import typecheck as tp
import numpy as np
from parseType import generateOperator
from math import log

def parseAndGenerateListType(lista):
    lizt = parseItem(lista)[0]
    shape = np.array(lizt).shape
    
    for item in lista:
        if item != "[" and item != "]":
            if (isinstance(item,float) or isinstance(item,int)):
                if item > 1 or item < -1:
                    return tp.List
            elif (isinstance(item,str)):
                return tp.List
                
    if len(shape) == 1:
        dim = int(log(len(lizt),2))
        if dim == 1:
            return tp.Qubit
        else:
            return tp.Qudit(dim)
    elif len(shape) == 2:
        if shape[1] != None:
            if shape[0] == shape[1]:
                return tp.Lollipop(tp.Qudit(int(log(len(lizt),2))),tp.Qudit(int(log(len(lizt),2))))
        else:
            raise Exception("operator {0} was not square".format(item))
    

def generateListType(lista):
    shape = np.array(lista).shape

    for item in lista:
        if item != "[" and item != "]":
            if (isinstance(item,float) or isinstance(item,int)):
                if item > 1 or item < -1:
                    return tp.List
            elif (isinstance(item,str)):
                return tp.List
            
    if len(shape) == 1:
        dim = int(log(len(lista),2))
        if dim == 1:
            return tp.Qubit
        else:
            typ = tp.Qubit
            for i in range(1,dim):
                typ = tp.Multiplicative(tp.Qubit,typ)
            return typ
    elif len(shape) == 2:
        if shape[1] != None:
            if shape[0] == shape[1]:
                if (shape[0] == 2):
                    return tp.Lollipop(tp.Qubit,tp.Qubit)
                else:
                    return generateOperator(int(log(shape[0],2)))
            else:
                raise Exception("operator {0} was not square".format(lista))
        else:
            raise Exception("Operator malformed")
    

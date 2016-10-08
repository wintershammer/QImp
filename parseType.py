import re
import typecheck


def parseType(string):

    opRegex = re.compile('operator\[([0-9]*)\]')
    tensRegex = re.compile('(.+) \* (.+)')
    funRegex = re.compile('(.+) > (.+)')
    expRegex = re.compile('\!\{(.*)\}')

    if funRegex.match(string):
        a = funRegex.match(string)
        return typecheck.Lollipop(parseType(a.group(1)), parseType(a.group(2)))
    elif expRegex.match(string):
        typos = parseType(expRegex.match(string).group(1))
        return typecheck.Exponential(typos)
    elif tensRegex.match(string):
        a = tensRegex.match(string)
        return typecheck.Multiplicative(parseType(a.group(1)),parseType(a.group(2)))
    elif opRegex.match(string):
        return generateOperator(int(opRegex.match(string).group(1)))
    elif string == "qubit":
        return typecheck.Qubit
    elif string == "int":
        return typecheck.Int
    elif string == "list":
        return typecheck.List
    else:
        raise Exception("Argument {0} has wrong type declaration".format(string))

def generateOperator(num):
    if num < 0 or num == 0:
        raise Exception("Operator must have positive arity")
    if num == 1:
        return typecheck.Lollipop(typecheck.Qubit,typecheck.Qubit)
        
    last = typecheck.Multiplicative(typecheck.Qubit,typecheck.Qubit)
    for itr in range(0,num-2):
        nxt = typecheck.Multiplicative(typecheck.Qubit,last)
        last = nxt
    return typecheck.Lollipop(last,last)
            

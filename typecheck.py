

# ast "nodes"

class Identifier: 

    def __init__(self,name):
        self.name = name


class Lam:
    def __init__(self,var,typ,body):
        self.var = var
        self.typ = typ
        self.body = body

class App:

    def __init__(self,e1,e2): #e1 e2 (application)
        self.e1 = e1
        self.e2 = e2
        
class Tensor:

    def __init__(self,e1,e2): #e1 e2 (application)
        self.e1 = e1
        self.e2 = e2
#types

Qubit = "Qubit"
Nat = "Nat"

class Lollipop:

    def __init__(self,t1,t2): # t1 -<> t2
        self.t1 = t1
        self.t2 = t2

    def __str__(self):
        return "{0} -<> {1}".format(str(self.t1),str(self.t2))

class Exponential:

    def __init__(self,t1,t2): # t1 -<> t2
        self.t1 = t1
        self.t2 = t2

    def __str__(self):
        return "{0} (x) {1}".format(str(self.t1),str(self.t2))    
# typechecking

def getType(name,env):
    if name in env:
        return env[name]
    else:
        raise Exception("Undefined symbol {0}".format(name))

    
def typecheck(item,env):
    
    if isinstance(item,Identifier):
        varType = getType(item.name,env)
        del env[item.name]
        return varType

    elif isinstance(item,Lam):
        env[item.var.name] = item.typ
        bodyType = typecheck(item.body,env)
        assertBindingUsed(item.var.name,env)
        return Lollipop(item.typ,bodyType)

    elif isinstance(item,App):
        lamType = typecheck(item.e1,env)
        argType = typecheck(item.e2,env)
        if isinstance(lamType,Lollipop):
            if(lamType.t1 == argType):
                return lamType.t2
            else:
                raise Exception("Function expecting type {0} but was given {1}".format(lamType.t1,argType))
        else:
                raise Exception("Non-function application")
            
    elif isinstance(item,Tensor):
        lType = typecheck(item.e1,env)
        rType = typecheck(item.e2,env)
        return Exponential(lType,rType)
        

def assertBindingUsed(name,env):
    if name in env:
        raise Exception("Binding {0} not used".format(name))

#tests
env = {}
expr = Lam(Identifier("x"),Qubit,Lam(Identifier("y"),Qubit,Tensor(Identifier("x"),Identifier("y"))))
lol = typecheck(expr,env)
print(lol)


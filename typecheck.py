import functools

# ast "nodes"



class Const:

    def __init__(self,expr,typos):
        self.expr = expr
        self.typos = typos

    def __str__(self):
        return self.expr
    
    
class Identifier: 

    def __init__(self,name):
        self.name = name

    def __str__(self):
        return self.name

class Lam:
    def __init__(self,var,typ,body):
        self.var = var
        self.typ = typ
        self.body = body

    def __str__(self):
        return "lam {0} {1} {2}".format(str(self.var),str(self.typ),str(self.body))

class App:

    def __init__(self,e1,e2): #e1 e2 (application)
        self.e1 = e1
        self.e2 = e2

    def __str__(self):
        return "app ({0} {1})".format((self.e1),str(self.e2))
        
class Tensor:

    def __init__(self,e1,e2): #e1 e2 (application)
        self.e1 = e1
        self.e2 = e2

    def __str__(self):
        return "{0} (x) {1}".format(str(self.e1),str(self.e2))
    
        
#types

Qubit = "Qubit"
Int = "Int"
Complex = "Complex"
Float = "Float"
Bool = "Bool"
String = "String"

class Exponential:

    def __init__(self,typ):
        self.typ = typ

    def __str__(self):
        return "!{0}".format(self.typ)


class Lollipop:

    def __init__(self,t1,t2): # t1 -<> t2
        self.t1 = t1
        self.t2 = t2

    def __str__(self):
        return "({0} -<> {1})".format(str(self.t1),str(self.t2))

    def __eq__(self,other):
        if isinstance(other,Lollipop):
            return self.t1 == other.t1 and self.t2 == other.t2
        else:
            return False

class Multiplicative:

    def __init__(self,t1,t2): # t1 -<> t2
        self.t1 = t1
        self.t2 = t2

    def __str__(self):
        return "{0} (x) {1}".format(str(self.t1),str(self.t2))

    def __eq__(self,other):
        if isinstance(other,Multiplicative):
            return self.t1 == other.t1 and self.t2 == other.t2
        else:
            return False

# typechecking

def getType(name,env):
    if name in env:
        return env[name]
    else:
        raise Exception("Undefined symbol {0}".format(name))

    
def typecheck(item,env):
    
    if isinstance(item,Identifier):
        varType = getType(item.name,env)
        if not (isinstance(varType,Exponential)):
            del env[item.name]
        else:
            varType = varType.typ
        return varType

    
    elif isinstance(item,Const):
        return item.typos
    
    elif isinstance(item,Lam):
        env[item.var.name] = item.typ
        deepestLam = item
        totalTypes = []
        while isinstance(deepestLam.body, Lam): #deepest lambda won't have another lambda for body
            totalTypes.append(deepestLam.typ)
            deepestLam = deepestLam.body
  
        typoi = []
        for expr in deepestLam.body:
            typoi.append(typecheck(expr,env))
            
        totalTypes.append(deepestLam.typ)
        totalTypes.append(typoi[-1])
        
        finalType = functools.reduce(lambda x,y: Lollipop(y,x), reversed(totalTypes))
        
        assertBindingUsed(item.var.name,env)
        return finalType

    elif isinstance(item,App):
        
        lamType = typecheck(item.e1,env)
        argType = typecheck(item.e2,env)

        if isinstance(lamType,Lollipop):
            if(lamType.t1 == argType):
                return lamType.t2
            else:
                #check subtyping
                if(lamType.t1 == Qubit and isinstance(argType,Multiplicative) or isinstance(argType,Exponential)):
                    return lamType.t2
                else:
                    raise Exception("Function expecting type {0} but was given {1}".format(lamType.t1,argType))
        else:
                raise Exception("Non-function application")
            
    elif isinstance(item,Tensor):
        lType = typecheck(item.e1,env)
        rType = typecheck(item.e2,env)
        return Multiplicative(lType,rType)
        

def assertBindingUsed(name,env):
    if name in env:
        if not isinstance(env[name],Multiplicative):
            raise Exception("Binding {0} not used".format(name))


envApply = Exponential(Lollipop(Lollipop(Qubit,Qubit),Lollipop(Qubit,Qubit))) #qubit -> qubit so you can do both inner product and matrix mult
envQIf = Exponential(Lollipop(Exponential(Bool),Exponential(Qubit))) #should I make one if for each type?
envTensor = Exponential(Lollipop(Qubit,Lollipop(Qubit,Multiplicative(Qubit,Qubit))))
envMeasure = Exponential(Lollipop(Qubit,Exponential(Qubit)))
#tests
#env = {}
##expr = Lam(Identifier("x"),Lollipop(Qubit,Qubit),Lam(Identifier("y"),Lollipop(Qubit,Qubit),Lam(Identifier("z"),Qubit,App(Identifier("x"),App(Identifier("y"),Identifier("z"))))))
#lol = typecheck(expr,env)
#print(lol)


import functools

# ast "nodes"



class Const:

    def __init__(self,expr,typos):
        self.expr = expr
        self.typos = typos

    def __str__(self):
        return str(self.expr)
    
    
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
        self.const = []

    def setConstr(self,constr):
        self.const.append(constr)

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
        self.const = []

    def __str__(self):
        return "({0} -<> {1})".format(str(self.t1),str(self.t2))

    def setConst(self,constr):
        self.const.append(constr)

    def __eq__(self,other):
        if isinstance(other,Lollipop):
            return self.t1 == other.t1 and self.t2 == other.t2
        else:
            return False

class Multiplicative:

    def __init__(self,t1,t2):
        self.t1 = t1
        self.t2 = t2

    def __str__(self):
        return "{0} (x) {1}".format(str(self.t1),str(self.t2))

    def __eq__(self,other):
        if isinstance(other,Multiplicative):
            #return self.t1 == other.t1 and self.t2 == other.t2
            #qubit (x) (qubit (x) qubit) should be equal to (qubit (x) qubit) (x) qubit
            #because of associativity of monoidal product
            #for now i just check the two string representations against eachother, after i strip the parenthesis
            #should probably find a uniform way to "flatten" tensors?
            return  str(self).replace('(', '').replace(')', '') ==  str(other).replace('(', '').replace(')', '') 
        else:
            return False

class Qudit:

    def __init__(self,n):
        self.n = n

    
    def __str__(self):
        return "Qubit^(x){0}".format(str(self.n))

                 
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
            newEnv = env.copy()
            newEnv[deepestLam.var] = deepestLam.typ
            typecheck(deepestLam,newEnv)

  
  
        typoi = []
        for expr in deepestLam.body:
            typoi.append(typecheck(expr,env))
            
        totalTypes.append(deepestLam.typ)
        totalTypes.append(typoi[-1])
        
        finalType = functools.reduce(lambda x,y: Lollipop(y,x), reversed(totalTypes))
        
        assertBindingUsed(item.var.name,env)

        finalType.setConst(item.const)
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
                elif str(item.e1) == "apply": #oh thats smart, just return the type of f in apply(f,x) and the typecheker will check it against x!
                    return argType #after all, apply is just explicit function application and the typechecker already handles that  
                elif str(item.e1) == "tensorOp":
                    return Lollipop(argType, Lollipop(Multiplicative(argType.t1,argType.t1),Multiplicative(argType.t1,argType.t1)))
                elif str(item.e1) == "measure": #measure just adds exponential modality to its argument
                    return Exponential(argType)
                elif str(item.e1) == "applyN":
                    return Lollipop(argType.t2,Lollipop(Int,argType.t2))
                else:
                    raise Exception("Function {0} expecting type {1} but was given {2}".format(item,lamType.t1,argType))
        else:
                raise Exception("Non-function application between {0} and {1}".format(lamType,argType))
            
    elif isinstance(item,Tensor):
        lType = typecheck(item.e1,env)
        rType = typecheck(item.e2,env)
        return Multiplicative(lType,rType)

    elif isinstance(item,list):
        typeList = []
        for itm in item:
            typeList.append(typecheck(itm,env))
        return typeList[-1]

    
def assertBindingUsed(name,env):
    if name in env:
        if not isinstance(env[name],Exponential):

            raise Exception("Binding {0} not used".format(name))


envAdd = Exponential(Lollipop(Int,Int))
envApplyN = Exponential(Lollipop(Lollipop(Qubit,Qubit),Lollipop(Qubit,Lollipop(Int,Qubit))))
envApply = Exponential(Lollipop(Lollipop(Qubit,Qubit),Lollipop(Qubit,Qubit))) #qubit -> qubit so you can do both inner product and matrix mult
envQIf = Exponential(Lollipop(Exponential(Bool),Exponential(Qubit))) #should I make one if for each type?
envTensor = Exponential(Lollipop(Qubit,Lollipop(Qubit,Multiplicative(Qubit,Qubit))))
envMeasure = Exponential(Lollipop(Qubit,Exponential(Qubit)))
envTensorOp = Exponential(Lollipop(Lollipop(Qubit,Qubit),Lollipop(Lollipop(Qubit,Qubit),Lollipop(Multiplicative(Qubit,Qubit),Multiplicative(Qubit,Qubit)))))
#tests
#env = {}
##expr = Lam(Identifier("x"),Lollipop(Qubit,Qubit),Lam(Identifier("y"),Lollipop(Qubit,Qubit),Lam(Identifier("z"),Qubit,App(Identifier("x"),App(Identifier("y"),Identifier("z"))))))
#lol = typecheck(expr,env)
#print(lol)


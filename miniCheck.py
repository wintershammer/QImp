import operator as op
import math, quantumLib, oracleLib, functools
import numpy as np
import re
import scipy.linalg as scipyAlg
import typecheck
import tsek
import copy
from parsimonious.grammar import Grammar
from parseType import parseType

typeEnv =  {"tensor" : typecheck.envTensor, "measure": typecheck.envMeasure, "apply" : typecheck.envApply, "tensorOp" : typecheck.envTensorOp, "+" : typecheck.envAdd}

class QImp(object):

    def __init__(self, envExt={}):
        self.env = {"tensor" : typecheck.envTensor, "measure": typecheck.envMeasure, "apply" : typecheck.envApply, "tensorOp" : typecheck.envTensorOp, "+" : typecheck.envAdd}
        self.env.update(envExt)
        self.constr = {}
        #defaultEnf(env)

    def parse(self, source):
        grammar = self.grammarFromDocStr()
        return Grammar(grammar)['program'].parse(source)

    def eval(self, source):
        node = self.parse(source) if isinstance(source, str) else source
        method = getattr(self, node.expr_name, lambda node, children: children)
        if node.expr_name in ['ifelse', 'func', 'baserecur']:
            return method(node)
        return method(node, [self.eval(n) for n in node])

    def grammarFromDocStr(self):
        #concat docstrings to generate grammar. careful: only visitor methods must have docstrings, and these must be grammar rules
        grammar = '\n'.join(v.__doc__ for k, v in vars(self.__class__).items()
                          if '__' not in k and hasattr(v, '__doc__') and v.__doc__)
        return grammar
        
    def program(self, node, children):
        'program = expr*'
        return children

    def expr(self, node, children):
        'expr = _ (load / func / ifelse / baserecur / call / comp / infixCall / prefixCall/  lista / assignment / boolLit / stringLit / complexLit / floatLit / intLit / name) _'
        return children[1][0]


    def typeDecl(self, node, children):
        'typeDecl = lvalue _ ":" _ typeName'
        ident, _, _, _, typos = children
        return ident,typos


    def typeName(self,node,children):
        'typeName = ~"[a-z A-Z 0-9 ! # $ * { } \[ \] ?]*" '
        return node.text.strip()

    
    def func (self, node):
        'func = "lambda" "(" typeDecl ((sep typeDecl)*)? ")"  "{" expr* "}" ( "(" expr* ((sep expr)*)? ")" )?'
        _, _, param1, params, _, _, expr, _ , app = node

        param1,type1 = self.eval(param1)


        paramRest = []
        typeRest = []
        declRest = list(map(self.eval, params)) #process extra arguments
        if declRest != [[]]:
            for item in declRest[0]:
                paramRest.append(item[1][0])
                typeRest.append(item[1][1])

        
        listOfParams = []
        listOfTypes = []
        listOfParams.append(param1)
        listOfTypes.append(type1)

        
        for item in paramRest:
            listOfParams.append(item)
            
        for item in typeRest:
            listOfTypes.append(item)

        if (app.text): 
            arg = self.eval(app)
            arguments = [arg[0][1][0]]
            for item in arg[0][2][0]:
               arguments.append(item[1])
            return(func(*arguments))

        constrs = [] 

        firstType = parseType(listOfTypes[0])
        constrs.append(firstType)
 
        topLam = typecheck.Lam(typecheck.Identifier(listOfParams[0]),firstType,[])
        latestLam = topLam

        localContext = copy.deepcopy(self.env)

        localContext[listOfParams[0]] = firstType

        
        for item,typeString in list(zip(listOfParams,listOfTypes))[1:]:
            typos = parseType(typeString)
            constrs.append(typos)
            localContext[item] = typos
            currentLam = typecheck.Lam(typecheck.Identifier(item),typos,[])
            latestLam.body = currentLam
            latestLam = currentLam

        bodyExprs = []
        body = []

        evltr = QImp(localContext)
        
        for item in evltr.eval(expr):
            if item != "IGNORE":
                bodyExprs.append(item)

        body = bodyExprs

        latestLam.body = body
        topLam.setConstr(constrs)
       

        return typecheck.typecheck(topLam,localContext)

    def lista(self, node, children):
        'lista = "[" expr* "]"'
        _, arguments, _ = children
        typos = tsek.parseAndGenerateListType(node.text)
        return typecheck.Const(str(arguments),typos)

    def parameters(self, node, children):
        'parameters = lvalue*'
        return children

    def ifelse(self, node):
        'ifelse = "if" _ "(" expr ")" "{" expr* "}" _ "else" _ "{" expr* "}" '
        _, _, _, cond, _, _, cons, _ , _ , _ , _ , _, alt, _ = node

        consExpr = self.eval(cons)
        altExpr = self.eval(alt)

        
        
        ccheck = typecheck.typecheck(consExpr,self.env.copy())
        acheck = typecheck.typecheck(altExpr,self.env.copy())
        

        
        if type(ccheck) != type(acheck) :
            print("cons: ",ccheck,"alt: ",acheck)
            raise Exception("Consequent and alternative types don't match")
            
        return [consExpr,altExpr]


    def baserecur(self, node):
        'baserecur = "base" _ "(" expr ")" "{" expr* "}" _ "recur" _ "{" expr* "}" '
        _, _, _, cond, _, _, base, _ , _ , _ , _ , _, recur, _ = node

        baseExpr = self.eval(base)
        recurExpr = self.eval(recur)
        
        
        #print(baseExpr)
        #print(recurExpr)

        flag = False
        for item in recurExpr:
            if isinstance(item,typecheck.App):
                flag = True
            
        if(flag == False):
            raise Exception("Recursive case must contain function application")
        else:
            return baseExpr
    

    def call(self, node, children): #na valo kommata anamesa! how to? opos to kana sthn valentine! (argument1, *(, argumentsExtra)* <- optional)
        'call = name "(" expr ((sep expr)*)? ")"'
        name, _, argument1, arguments, _= children

        returner = []
        returner.append(name)
        returner.append(argument1)
        
        
        for item in arguments[0]:
            returner.append(item[1])

        
        expr = functools.reduce(lambda x,y: typecheck.App(x,y),returner)
        
        return expr
        

    def infixCall(self, node, children): #calling binary operators in infix style: (x f y)
        'infixCall = "(" expr name expr ")"'
        _, argument1, name, argument2, _= children
        returner = []
        returner.append(name)
        returner.append(argument1)
        returner.append(argument2)
        expr = functools.reduce(lambda x,y: typecheck.App(x,y),returner)
        return expr

    def prefixCall(self, node, children): #calling unary operators prefix style: (f x) -- potentially could allow any arity, but i don't see the use for lisp-style function calls
        'prefixCall = "(" name expr ")"'
        _, name, argument, _= children
        return typecheck.App(name,argument)

    def assignment(self, node, children): 
        'assignment = "let" _ lvalue "=" expr'
        _,_,lvalue, _, expr = children
        
        
        if lvalue in self.env:
            raise Exception("Duplicate definitions for" + ": " + lvalue)

        if not isinstance(expr,typecheck.Lollipop):
            self.env[lvalue] = typecheck.typecheck(expr,copy.deepcopy(self.env))
        else:
            self.env[lvalue] = expr
        return "IGNORE"

    def lvalue(self, node, children): #make that 'lvalue = ~"[a-z0-9]+" _' if you want variable/func names to have alphanumeric instead
        'lvalue = ~"[a-zA-Z?]+" _'
        return node.text.strip()

    def boolLit(self, node, children):
        'boolLit = _("#t" / "#f")_'
        if (node.text == "#t"):
            return True
        else:
            return False
        return typecheck.Const(node.text,typecheck.Bool)
        
    def comp(self, node, children): 
        'comp = name (compsep name)+ _ "(" expr* ")"'
        nameO, nameR, _ , _, expr , _ = children   
        for index,fun in enumerate(reversed(nameR)): #remember: the first function to be applied in a composition is the innermost one (thats why we reverse the list)
            if (index == 0): #initialise: apply the innermost function to the expression
                value = fun[1](*expr) 
            else: 
                value = fun[1](value) #apply the next fun in the queue
        return nameO(value) #apply the outermost func and return


    def load(self, node, children):
        'load = "--load" _ lvalue '
        _,_,filename = children
        temp = QImp()
        with open ( (filename + ".qimp" ), "r",encoding="utf8") as myfile:
            temp.eval(myfile.read())
            self.env = temp.env.copy()
        
    def stringLit(self, node, children):
        'stringLit = "\\"" ~"[a-z A-Z 0-9 ! # $ ?]*" "\\"" '
        return typecheck.Const(node.text,typecheck.String)
    
    def name(self, node, children): #make that 'name = ~"[a-z0-9]+" _' if you want variable/func names to have alphanumeric instead
        'name = ~"[a-zA-Z⊗·+\-/*=?]+"'
        return typecheck.Identifier(node.text)

    def numeral(self, node, children): #helper parser, matches numeral literals
        'numeral = ~"[0-9]+"'
        
    def intLit(self, node, children):
        'intLit = ("-")? numeral'
        return typecheck.Const(node.text,typecheck.Int)
    
    def floatLit(self,node,children):
        'floatLit = ("-")? numeral "." numeral '
        return typecheck.Const(node.text,typecheck.Float)

    def complexLit(self, node, children): #bit of a mess: complexLit = optional "-", (float or integer), "+" or "-", (float or integer)
        'complexLit = ("+"/"-")? (numeral ("." numeral)?) ("+"/"-") (numeral ("." numeral)?) "i"'
        return typecheck.Const(node.text,typecheck.Complex)


    def _(self, node, children):
        '_ = ~"\s*"'

    def sep(self,node,children):
        'sep = _ "," _ '

    def compsep(self,node,children):
        'compsep = _"."_'


class Function(object):
    def __init__(self,env,parameters,body):
        self.env = env
        self.parameters = parameters
        self.body = body


    def __call__(self,*args):
        
        if(len(args) < len(self.parameters)):
            env1 = dict(list(self.env.items()) + list(zip(self.parameters[:len(args)], args)))
            return Function(env1,self.parameters[len(args):],self.body)
        env1 = dict(list(self.env.items()) + list(zip(self.parameters, args)))
        return QImp(env1).eval(self.body)[-1]    
        
        

def myCar(l):
    if isinstance(l,list):
        return l[0]
    else:
        return []
    
def myCdr(l):
    if isinstance(l,list):
        return l[1:]
    else:
        return []

def prettyPrint(x):
    if (isinstance(x,list)): #if our item to print is a list, chcek to see if its a list of lists
        if any(isinstance(el, list) for el in x): #if its a list of lists print it like a matrix
            print("---Matrix---")
            for item in x:
                print(item)
    else:
        print(x)




def defaultEnf(env):
    env['sum'] = lambda *args: sum(args)
    env['sqrt'] = lambda x: math.sqrt(x)
    env['print'] = lambda *x: print(*x)
    env['pprint'] = lambda *x: prettyPrint(*x)
    env['car'] = lambda x: myCar(x)
    env['cdr'] = lambda x: myCdr(x)
    env['map'] = lambda x,y: list(map(x,y))
    env['fold'] = lambda x,y : functools.reduce(x,y)
    env['tensor'] = lambda x,y: np.kron(x,y)
    env['apply'] = lambda x,y: np.dot(x,y)
    env['outer'] = lambda x,y: np.outer(x,y)
    env['measure'] = lambda x: quantumLib.measure(x)
    env['subsystems'] = lambda state,configuration: quantumLib.splitToSub(state,configuration)
    env['eq'] = lambda x,y: x == y
    env['append'] = lambda x,y : [x]+y
    env['prepend'] = lambda x,y : y + [x]
    env['⊗'] = lambda x,y: np.kron(x,y)
    env['·'] = lambda x,y: np.dot(x,y) 
    env["-"] = lambda x,y: np.subtract(x,y) #numpy add/sub/mult/div works like regular for matrix AND numbers! no need for addMatrix etc
    env["+"] = lambda x,y: np.add(x,y)
    env["*"] = lambda x,y: np.multiply(x,y)
    env["/"] = lambda x,y: np.divide(x,y)
    env["="] = lambda x,y: x == y
    env["len"] = lambda x: len(x)
    env["null?"] = lambda x: len(x) == 0
    env["sqrt"] = lambda x: np.sqrt(x)
    env["reverse"] = lambda x : list(reversed(x))
    env["fold"] = lambda x,y : functools.reduce(x,y)
    env["pi"] = math.pi
    env["exp"] = np.exp #should add cleanExp like quantum parethesis
    env["oracle"] = lambda fun: oracleLib.generateOracle(fun)
    env["expm"] = lambda matrix: list(scipyAlg.expm(matrix))
    env["logm"] = lambda matrix: list(scipyAlg.logm(matrix))
    env["logTwo"] = lambda x: int(math.log(x,2))
    env["length"] = lambda x: len(x)
    env["transpose"] = lambda x: (quantumLib.ctransp(x)).tolist();

def repl():
    qImpInstance = QImp()
    while True:
        print(qImpInstance.eval(input(">>>")))
        
def typecheckItem(item,env):
        a = QImp(env)
        res = a.eval(item)
        return res
    
def typecheckFile(filename):    
    with open (filename + ".lqimp", "r",encoding="utf8") as myfile:
        
        a = QImp()
        progri  = a.eval(myfile.read())
        
        for item in progri:
            print(typecheck.typecheck(item,a.env))
        #print("Global env:",a.env)
        return a.env



#typecheckFile("typetest")

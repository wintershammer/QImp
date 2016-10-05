import operator as op
import math, quantumLib, oracleLib, functools, miniCheck
import numpy as np
import re
import scipy.linalg as scipyAlg
import typecheck as typecheckLib
import tsek
from parsimonious.grammar import Grammar



class QImp(object):

    def __init__(self, env={}, typeEnv={}):
        self.env = env
        self.typeEnv = typeEnv
        defaultEnf(env)

    def parse(self, source):
        grammar = self.grammarFromDocStr()
        return Grammar(grammar)['program'].parse(source)

    def eval(self, source):
        node = self.parse(source) if isinstance(source, str) else source
        method = getattr(self, node.expr_name, lambda node, children: children)
        if node.expr_name in ['ifelse', 'func']:
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
        'expr = _ (load / qload / func / ifelse / call / comp / infixCall / prefixCall/  lista / assignment / boolLit / stringLit / complexLit / floatLit / intLit / name) _'
        return children[1][0]

    def typeDecl(self, node, children):
        'typeDecl = lvalue (_ ":" _ typeName)?'
        ident, _, = children
        return ident


    def typeName(self,node,children):
        'typeName = ~"[a-z A-Z 0-9 ! # $ * > { } \[ \] ?]*" '
        return None

    
    def func (self, node):
        'func = "lambda" "(" typeDecl ((sep typeDecl)*)? ")"  "{" expr* "}" ( "(" expr* ((sep expr)*)? ")" )?'
        _, _, param1, params, _, _, expr, _ , app = node
        param1 = self.eval(param1)
        paramRest = list(map(self.eval, params))
        listOfParams = []
        listOfParams.append(param1)
        for item in paramRest[0]:
            listOfParams.append(item[1])

        func = Function(self.env, listOfParams, expr)
        if (app.text): #in case of application (must find a better way to check for app than just checking the .text field :P)
            arg = self.eval(app)
            arguments = [arg[0][1][0]]
            for item in arg[0][2][0]:
               arguments.append(item[1])
            return(func(*arguments))
            #[0] because arg returns [[[],[item],[itemsOptional],[]]] (a nsted list)
            #[1] because arg[0] returns [[],[item], [itemsOptional], []] (the first and last [] are the parens)
            #[0] because arg[0][1] returns [item], we want the item itself and not a list with the item
            #same for [0][2][0]
        return func 

    def lista(self, node, children):
        'lista = "[" expr* "]"'
        _, arguments, _ = children
        return list(arguments)

    def parameters(self, node, children):
        'parameters = lvalue*'
        return children

    def ifelse(self, node):
        'ifelse = "if" _ "(" expr ")" "{" expr* "}" _ "else" _ "{" expr* "}" '
        _, _, _, cond, _, _, cons, _ , _ , _ , _ , _, alt, _ = node
        return self.eval(cons)[-1] if self.eval(cond) else self.eval(alt)[-1] #ksana, girna thn teleutea expr panta

    def call(self, node, children): #na valo kommata anamesa! how to? opos to kana sthn valentine! (argument1, *(, argumentsExtra)* <- optional)
        'call = name "(" expr ((sep expr)*)? ")"'
        name, _, argument1, arguments, _= children
        returner = []
        returner.append(argument1)
        for item in arguments[0]:
            returner.append(item[1])
        
        funName = (node.text.split("(")[0])#get function name (to check if its a typed func)
        
        if funName in self.typeEnv and (funName != "tensor" and funName != "apply" and funName != "measure" and funName != "tensorOp"):
            
            func = self.typeEnv[funName]


            argTypes = []
            for item in returner:
                #print(item)
                if not (isinstance(item,list)):
                    raise Exception("Linear function input {0} was not of quantum type".format(item))
                else:
                    argTypes.append(tsek.generateListType(item))
                    
            for constraint,arg in zip(func.const[0][0],argTypes):
                if not (constraint == arg):
                    if(isinstance(constraint,typecheckLib.Exponential) or isinstance(arg,typecheckLib.Exponential)):
                        constIsExpo = isinstance(constraint,typecheckLib.Exponential)
                        argIsExpo = isinstance(arg,typecheckLib.Exponential)
                        if(constIsExpo and argIsExpo):
                            print(constraint)
                            print(arg)
                            if not(constraint.typ == arg.typ):
                                raise Exception("Constraint Error for {2}: Input {1} does not meet constraint {0}".format(constraint,arg,funName))
                        if(constIsExpo and not argIsExpo):
                            if not(constraint.typ == arg):
                                raise Exception("Constraint Error for {2}: Input {1} does not meet constraint {0}".format(constraint,arg,funName))
                        if(not constIsExpo and argIsExpo):
                            if not(constraint == arg.typ):
                                raise Exception("Constraint Error for {2}: Input {1} does not meet constraint {0}".format(constraint,arg,funName))

                    else:
                        raise Exception("Constraint Error for {2}: Input {1} does not meet constraint {0}".format(constraint,arg,funName))

        if isinstance(name,list): #if the "function" you are applying is a matrix just do matrix multiplication
            #print(returner)
            return self.env["apply"](returner,name)[0]
            
        return name(*returner)

    def infixCall(self, node, children): #calling binary operators in infix style: (x f y)
        'infixCall = "(" expr name expr ")"'
        _, argument1, name, argument2, _= children
        returner = []
        returner.append(argument1)
        returner.append(argument2)
        return name(*returner)

    def prefixCall(self, node, children): #calling unary operators prefix style: (f x) -- potentially could allow any arity, but i don't see the use for lisp-style function calls
        'prefixCall = "(" name expr ")"'
        _, name, argument, _= children
        return name(argument)

    def assignment(self, node, children): 
        'assignment = "let" _ lvalue "=" expr'
        _,_,lvalue, _, expr = children
        if lvalue in self.env:
            raise Exception("Duplicate definitions for" + ": " + lvalue)
        self.env[lvalue] = expr
        return expr

    def lvalue(self, node, children): #make that 'lvalue = ~"[a-z0-9]+" _' if you want variable/func names to have alphanumeric instead
        'lvalue = ~"[a-zA-Z?]+" _'
        return node.text.strip()

    def boolLit(self, node, children):
        'boolLit = _("#t" / "#f")_'
        if (node.text == "#t"):
            return True
        else:
            return False
        
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

    def qload(self, node, children):
        'qload = "--qload" _ lvalue '
        _,_,filename = children
        temp = QImp()
        self.typeEnv.update(miniCheck.typecheckFile(filename))
        
        with open ( (filename + ".lqimp" ), "r",encoding="utf8") as myfile:
            temp.eval(myfile.read())
            self.env = temp.env.copy()
        
    def stringLit(self, node, children):
        'stringLit = "\\"" ~"[a-z A-Z 0-9 ! # $ ?]*" "\\"" '
        return str(node.text[1:-1])
    
    def name(self, node, children): #make that 'name = ~"[a-z0-9]+" _' if you want variable/func names to have alphanumeric instead
        'name = ~"[a-zA-Z⊗·+\-/<>*=?]+"'
        return self.env.get(node.text.strip(), -1)

    def numeral(self, node, children): #helper parser, matches numeral literals
        'numeral = ~"[0-9]+"'

    def intLit(self, node, children):
        'intLit = ("-")? numeral'
        return int(node.text)
    
    def floatLit(self,node,children):
        'floatLit = ("-")? numeral "." numeral '
        return float(node.text)

    def complexLit(self, node, children): #bit of a mess: complexLit = optional "-", (float or integer), "+" or "-", (float or integer)
        'complexLit = ("+"/"-")? (numeral ("." numeral)?) ("+"/"-") (numeral ("." numeral)?) "i"'
        return complex(node.text.replace("i","j"))


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
    env['tensor'] = lambda x,y: np.kron(x,y).tolist()
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
    env["<"] = lambda x,y: x < y
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
    env["tensorOp"] = lambda x,y: np.kron(x,y)
    env["transpose"] = lambda x: (quantumLib.ctransp(x)).tolist();

def parseItem(item):
    a = QImp()
    return a.eval(item)

def repl():
    qImpInstance = QImp()
    while True:
        print(qImpInstance.eval(input(">>>")))

    
def run(filename):
    with open (filename+".qimp", "r",encoding="utf8") as myfile:
        a = QImp()
        kek  = a.eval(myfile.read())
    #print("Global env:",a.env)

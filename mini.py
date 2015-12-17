import operator as op
import math, quantumLib
import numpy as np
import re
from parsimonious.grammar import Grammar


class QImp(object):

    def __init__(self, env={}):
        self.env = env
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
        'expr = _ (func / ifelse / call / comp / infixCall / lista / assignment / boolLit / stringLit / number / name) _'
        return children[1][0]

    def func (self, node):
        'func = "lambda" "(" lvalue ((sep lvalue)*)? ")" "{" expr* "}" ( "(" expr* ")" )?'
        _, _, param1, params, _, _, expr, _ , app = node
        param1 = self.eval(param1)
        paramRest = list(map(self.eval, params))
        listOfParams = []
        listOfParams.append(param1)
        for item in paramRest[0]:
            listOfParams.append(item[1])
        def func(*args):
            #for n,item in enumerate(args):
             #   print(n,item,params[n])
            env = dict(list(self.env.items()) + list(zip(listOfParams, args)))
            return QImp(env).eval(expr)[-1] #return the last thing that was evaluated!
        if (app.text): #in case of application (must find a better way to check for app than just checking the .text field :P)
            arg = self.eval(app)
            return (func(arg[0][1][0]))
            #[0] because arg returns [[item]] (ie a nsted list)
            #[1] because arg[0] returns [[],[item],[]] (the first and last [] are the parens)
            #[0] because arg[0][1] returns [item], we want the item itself and not a list with the item
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
        return name(*returner)

    def infixCall(self, node, children): #calling binary operators in infix style: (x f y)
        'infixCall = "(" expr name expr ")"'
        _, argument1, name, argument2, _= children
        returner = []
        returner.append(argument1)
        returner.append(argument2)
        return name(*returner)

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
        'comp = name ((compsep name)+)? _ "(" expr* ")"'
        nameO, nameR, _ , _, expr , _ = children
        initial = nameO(*expr)    
        for fun in nameR[0]:
            initial = fun[1](initial)
        return initial

        
    def stringLit(self, node, children):
        'stringLit = "\\"" ~"[a-z A-Z 0-9 ! # $ ?]*" "\\"" '
        return str(node.text[1:-1])
    
    def name(self, node, children): #make that 'name = ~"[a-z0-9]+" _' if you want variable/func names to have alphanumeric instead
        'name = ~"[a-zA-Z⊗·+\-/*=?]+"'
        return self.env.get(node.text.strip(), -1)

    def number(self, node, children):
        'number = ~"[0-9.]+"'
        if re.match("^\d+?\.\d+?$", node.text) is not None: #check if node.text is of format digit.digit (ie a float)
            return float(node.text)
        return int(node.text)

    def _(self, node, children):
        '_ = ~"\s*"'

    def sep(self,node,children):
        'sep = _ "," _ '

    def compsep(self,node,children):
        'compsep = _"."_'
    

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


def defaultEnf(env):
    env['sum'] = lambda *args: sum(args)
    env['sqrt'] = lambda x: math.sqrt(x)
    env['print'] = lambda *x: print(*x)
    env['car'] = lambda x: myCar(x)
    env['cdr'] = lambda x: myCdr(x)
    env['map'] = lambda x,y: list(map(x,y))
    env['tensor'] = lambda x,y: np.kron(x,y)
    env['apply'] = lambda x,y: np.dot(x,y)
    env['measure'] = lambda x: quantumLib.measure(x)
    env['eq'] = lambda x,y: x == y
    env['append'] = lambda x,y : [x]+y
    env['prepend'] = lambda x,y : y + [x]
    env['⊗'] = lambda x,y: np.kron(x,y)
    env['·'] = lambda x,y: np.dot(x,y)
    env["-"] = lambda x,y: x - y    
    env["+"] = lambda x,y: x + y
    env["*"] = lambda x,y: x * y
    env["/"] = lambda x,y: x / y
    env["="] = lambda x,y: x == y
    env["len"] = lambda x: len(x)
    env["null?"] = lambda x: len(x) == 0
    env["sqrt"] = lambda x: math.sqrt(x)

def repl():
    qImpInstance = QImp()
    while True:
        print(qImpInstance.eval(input(">>>")))

with open ("generator.qimp", "r",encoding="utf8") as myfile:
    a = QImp()
    kek  = a.eval(myfile.read())
    #print("Global env:",a.env)

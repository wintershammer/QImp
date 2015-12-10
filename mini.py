import operator as op
import math, quantumLib
import numpy as np
from parsimonious.grammar import Grammar


class Mini(object):

    def __init__(self, env={}):
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
        self.env = env

    def parse(self, source):
        grammar = '\n'.join(v.__doc__ for k, v in vars(self.__class__).items()
                      if '__' not in k and hasattr(v, '__doc__') and v.__doc__)
        return Grammar(grammar)['program'].parse(source)

    def eval(self, source):
        node = self.parse(source) if isinstance(source, str) else source
        method = getattr(self, node.expr_name, lambda node, children: children)
        if node.expr_name in ['ifelse', 'func']:
            return method(node)
        return method(node, [self.eval(n) for n in node])

    def program(self, node, children):
        'program = expr*'
        return children

    def expr(self, node, children):
        'expr = _ (func / ifelse / call / infix / lista / assignment / boolLit / stringLit / number / name) _'
        return children[1][0]

    def func(self, node):
        'func = "lambda" "(" parameters ")" "{" expr* "}"'
        _, _, params, _, _, expr, _ = node
        params = list(map(self.eval, params))
        def func(*args):
            #for n,item in enumerate(args):
             #   print(n,item,params[n])
            env = dict(list(self.env.items()) + list(zip(params, args)))
            return Mini(env).eval(expr)[-1] #return the last thing that was evaluated!
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
        'call = name "(" expr* _ ")"'
        name, _, arguments, _ , _= children
        return name(*arguments)

    def infix(self, node, children):
        'infix = "(" expr operator expr ")"'
        _, expr1, operator, expr2, _ = children
        return operator(expr1, expr2)

    def operator(self, node, children):
        'operator = "+" / "-" / "*" / "/"'
        operators = {'+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv}
        return operators[node.text]

    def assignment(self, node, children):
        'assignment = lvalue "=" expr'
        lvalue, _, expr = children
        self.env[lvalue] = expr
        return expr

    def lvalue(self, node, children): #make that 'lvalue = ~"[a-z0-9]+" _' if you want variable/func names to have alphanumeric instead
        'lvalue = ~"[a-z]+" _'
        return node.text.strip()

    def boolLit(self, node, children):
        'boolLit = _("#t" / "#f")_'
        if (node.text == "#t"):
            return True
        else:
            return False
        
    def stringLit(self, node, children):
        'stringLit = "\\"" ~"[a-z 0-9 ! # $ ?]*" "\\"" '
        return str(node.text[1:-1])
    
    def name(self, node, children): #make that 'name = ~"[a-z0-9]+" _' if you want variable/func names to have alphanumeric instead
        'name = ~"[a-z]+" _'
        return self.env.get(node.text.strip(), -1)

    def number(self, node, children):
        'number = ~"[0-9]+"'
        return int(node.text)

    def _(self, node, children):
        '_ = ~"\s*"'

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


with open ("test.qimp", "r") as myfile:
    a = Mini()
    kek  = a.eval(myfile.read())
    #print("Global env:",a.env)

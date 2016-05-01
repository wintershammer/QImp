import numpy as np

#based on: Approximation with Kronecker products, C.F Van Loan and N.Pitsianis

def permute(matrix):
    #{{{1, 2}, {3, 4}}}
    return np.matrix([[matrix[0],matrix[1]],[matrix[2],matrix[3]]])






def fac(mat):
    u,s,v = np.linalg.svd(permute(mat))
    ul = u.tolist()
    vl = v.tolist()
    ss = np.sqrt(s[0])
    print("a = ", [ss * ul[0][0], ss * ul[1][0]])
    print("b = ", [ss * vl[0][0], ss * vl[1][0]])




qu0 = [0,1]
qu1 = [1/np.sqrt(2),1/np.sqrt(2)]

fac(np.kron(qu0,qu1)) #for some reason it messes up the signs

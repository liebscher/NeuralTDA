import numpy as np 
import scipy as sp 
from scipy.misc import derivative
from numpy.linalg import lstsq

def d_H(x1, x2):

    a = np.abs(x1-x2)
    b = np.abs(1.0 - x1*np.conj(x2))
    return 2*np.arctanh(a/b)

def ddH_dx1_1(x1, x2):

    x1_1 = np.real(x1)
    x1_2 = np.imag(x1)

    x2_1 = np.real(x2)
    x2_2 = np.imag(x2)

    v1 = x1_1 - x2_1
    v3 = x1_1*x2_1 + x1_2*x2_2 - 1
    v2 = x1_2 - x2_2 
    v4 = x1_1*x2_2 - x1_2*x2_1 
    tsq = (v1**2 + v2**2)/(v3**2 + v4**2)

    a = ((v1/(v1**2 + v2**2)) - (x2_1*v3 + x2_2*v4)/(v3**2 + v4**2))
    b = (2*np.sqrt(tsq)/(1-tsq))
    return b*a 

def ddH_dx1_2(x1, x2):

    x1_1 = np.real(x1)
    x1_2 = np.imag(x1)

    x2_1 = np.real(x2)
    x2_2 = np.imag(x2)

    v1 = x1_1 - x2_1
    v3 = x1_1*x2_1 + x1_2*x2_2 - 1
    v2 = x1_2 - x2_2 
    v4 = x1_1*x2_2 - x1_2*x2_1 
    tsq = (v1**2 + v2**2)/(v3**2 + v4**2)

    a = ((v2/(v1**2 + v2**2)) - (x1_1*v4 - x2_2*v3)/(v3**2 + v4**2))
    b = (2*np.sqrt(tsq)/(1-tsq))
    return b*a 

def mobius_xform(z, c, theta):

    a = theta*z + c 
    b = np.conj(c)*theta*z + 1
    return a/b

def E_x(X, Y, D, w):

    d = get_distances(X, Y)
    diffmat = np.subtract(d, D)
    diffmat = np.square(diffmat)
    
    E = 0.5*np.einsum('ij,ij', w, diffmat)
    return E

def get_distances(X, Y):

    dmat = np.zeros((len(X), len(X)))
    for i in range(len(X)):
        for k in range(i):
            dmat[k, i] = d_H(X[i]+1j*Y[i], X[k]+1j*Y[k])
    return dmat + np.transpose(dmat)

def dE_dxa(D, w, X, Y, alpha, q):

    d = get_distances(X, Y)
    x_a_1 = X[alpha]
    x_a_2 = Y[alpha]
    x_a = x_a_1 + 1j*x_a_2
    dd_vec = np.zeros(len(X))
    if q==1:
        ddH = lambda x, y: ddH_dx1_1(x, y)
    elif q==2:
        ddH = lambda x, y: ddH_dx1_2(x, y)
    rng = range(len(X))
    
    for j in rng:
        x_j = X[j] + 1j*Y[j]
        dd = ddH(x_a, x_j)
        dd_vec[j] = np.real(dd)
        dd_vec[alpha]=0.0

    w_j = w[alpha, :]
    diffmat = np.subtract(d[alpha, :],  D[alpha, :])
    dEdxa = np.einsum('j,j,j', w_j, diffmat, dd_vec)
    return dEdxa

def dE_dxa_q(x, D, w, X, Y, alpha, q):

    a = 0
    if q==1:
        X[alpha]=x
        a = dE_dxa(D, w, X, Y, alpha, q)
    elif q==2:
        Y[alpha] = x
        a = dE_dxa(D,w, X, Y, alpha, q)
    return a


def HMDS_update(D, w, X, Y, alpha, eta):

    dE_1 = dE_dxa(D,w,X,Y,alpha, 1)
    dE_2 = dE_dxa(D, w, X, Y, alpha, 2)
    ddE_dxa_1 = lambda x: dE_dxa_q(x, D, w, X, Y, alpha, 1)
    ddE_dxa_2 = lambda y: dE_dxa_q(y, D, w, X, Y, alpha, 2)
    ddEdxa1 = derivative(ddE_dxa_1, X[alpha], dx=1e-3)
    ddEdxa2 = derivative(ddE_dxa_2, Y[alpha], dx=1e-3)

    print('de1 {}'.format(dE_1))
    print('de12 {}'.format(dE_2))
    print('dde1 {}'.format(ddEdxa1))
    print('dde2 {}'.format(ddEdxa2))
    delta_r = dE_1 / np.abs(ddEdxa1)
    delta_i = dE_2 / np.abs(ddEdxa2)

    #delta_r = dE_1 / 1.0
    #delta_i = dE_2 / 1.0

    delta = -1.0*(delta_r +1j*delta_i) 
    if eta > 1.0/np.abs(delta):
        print('eta: {}'.format(eta))
        print('delta: {}'.format(delta))
        eta = 0.8*1.0/np.abs(delta) 
        print('new eta: {}'.format(eta))
    print('delta mag: {}'.format(np.abs(delta)))
    new = mobius_xform(eta*delta, X[alpha]+1j*Y[alpha], 1)
    return new

def HMDS_update2(D, w, X, Y, alpha, eta, lam):

    dE_1 = dE_dxa(D,w,X,Y,alpha, 1)
    dE_2 = dE_dxa(D, w, X, Y, alpha, 2)

    dE = np.array([dE_1, dE_2])
    bet = -0.5*dE 
    alph_mat = np.outer(dE, dE)

    lm_mat = np.ones((len(dE), len(dE))) + np.diag(len(dE)*[lam])
    alph_mat_prime = np.multiply(alph_mat,lm_mat)

    delt = lstsq(alph_mat_prime, bet)[0]

    delta = (delt[0] +1j*delt[1]) 
    if eta > 1.0/np.abs(delta):
        #print('eta: {}'.format(eta))
        #print('delta: {}'.format(delta))
        eta = 0.8*1.0/np.abs(delta) 
        #print('new eta: {}'.format(eta))

    #print('delta mag: {}'.format(np.abs(delta)))
    new = mobius_xform(X[alpha]+1j*Y[alpha], eta*delta, 1)

    return new

def HMDS_update3(D, w, X, Y, eta, lam):

    outvec = np.zeros(len(X))
    dE = np.zeros(2*len(X))
    for alph in range(len(X)):

        dE_1 = dE_dxa(D,w,X,Y,alph, 1)
        dE_2 = dE_dxa(D, w, X, Y, alph, 2)
        dE[2*alph] = dE_1
        dE[2*alph+1] = dE_2 
    bet = -0.5*dE 
    alph_mat = np.outer(dE, dE)

    lm_mat = np.ones((len(dE), len(dE))) + np.diag(len(dE)*[lam])
    alph_mat_prime = np.multiply(alph_mat,lm_mat)

    delt = lstsq(alph_mat_prime, bet)[0]

    for alph in range(len(X)):
        delta = delt[2*alph] + 1j*delt[2*alph+1]
        eta_act = eta
        if eta > 1.0/np.abs(delta):
            eta_act = 0.8*1.0/np.abs(delta) 
        outvec[alph] = mobius_xform(X[alph]+1j*Y[alph], eta_act*delta, 1)

    return outvec

def fit_HMDS(X, Y, D, w, eta, eps, verbose=False, maxiter=5000):
    n = len(X)
    epsvec = np.ones(n)
    diffp = 1
    X_s = np.copy(X)
    Y_s = np.copy(Y)
    lamm = 0.001*np.ones(n)
    iternum = 0
    while (diffp > eps) or iternum < maxiter:
        alph = np.random.randint(n)
        lam = lamm[alph]
        E = E_x(X_s, Y_s, D, w)
        new = HMDS_update2(D, w, X_s, Y_s, alph, eta, lam)
        #print('Xs_a {} X_a {}'.format(X_s[alph], X[alph]))
        X_s[alph] = np.real(new)
        Y_s[alph] = np.imag(new)
        #print('Test: Xs_a {} X_a {}'.format(X_s[alph], X[alph]))

        newE = E_x(X_s, Y_s, D, w)
        if np.mod(iternum, 25)==0 and verbose:
            print('Iteration: {} E: {}'.format(iternum, E))
        if newE > E:
            #print('Resetting X_s, Y_s')
            lam = lam*10.0
            #print('Xs_a {} X_a {}'.format(X_s[alph], X[alph]))
            X_s[alph] = X[alph]
            Y_s[alph] = Y[alph]
            #print('AR: Xs_a {} X_a {}'.format(X_s[alph], X[alph]))
        elif newE < E:
            #print('saving')
            lam = lam/10.0
            #print('Xs_a {} X_a {}'.format(X_s[alph], X[alph]))
            X[alph] = X_s[alph]
            Y[alph] = Y_s[alph]
            #print('AS: Xs_a {} X_a {}'.format(X_s[alph], X[alph]))
        if lam > 1e4:
            lam = 1e4
        elif lam < 1e-4:
            lam = 1e-4
        lamm[alph] = lam
        diffp = np.abs(newE-E)
        epsvec[alph] = diffp
        iternum = iternum+1
    return (X+1j*Y)

def gromov_product(x, y, p, D):

    dpx = D[p, x]
    dpy = D[p, y]
    dxy = D[x, y]

    gromprod = 0.5*(dpx + dpy - dxy)
    return gromprod 

def test_delta_hyperbolic(D):

    valsav = []
    nverts, t = D.shape
    for x in range(nverts):
        for y in range(nverts):
            for z in range(nverts):
                for p in range(nverts):

                    xzp = gromov_product(x, z, p, D)
                    xyp = gromov_product(x, y, p, D)
                    yzp = gromov_product(y, z, p, D)
                    val = min(xyp, yzp) - xzp 
                    valsav.append(val)
    delta = max(valsav)
    return delta 
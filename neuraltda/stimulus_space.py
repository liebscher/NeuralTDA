################################################################################
## Routines for reconstructing stimulus space from simplicial complexes       ##
## Also routines for computing max simplices from binned spike data           ##
## Brad Theilman 30 March 2018												  ##
################################################################################

import numpy as np
import scipy.linalg as spla
import networkx as nx

###############################################
#### Graph and Population Tensor Functions ####
###############################################

def mu_k(k, Ncells):
    '''
    Cell group distance parameter from Curto Itskov 2008

    Parameters
    ----------
    k : int
        number of cells in cell group 
    Ncells : int 
        Total number of cells in population 
    '''
    return 1 - np.pi*np.sqrt(float(k-1)/float(Ncells))

def add_cellgroups(graph, cg, Ncells, depth):
    # for each neighbor:
    cg_orig = tuple(cg)
    cg_list = list(cg)
    if len(cg_list) <= 1:
        return
    k = len(cg) - 1
    muk = mu_k(k, Ncells)
    for ind in range(len(cg)):
        a = cg_list.pop(ind)
        graph.add_edge(tuple(cg_list), cg_orig, weight=muk)
        add_cellgroups(graph, cg_list, Ncells, depth+1)
        cg_list.insert(ind, a)
    return

def stimspacegraph_nx(maxsimps, Ncells):
    ''' 
    Construct the weighted graph of cell groups as defined in Curto Itskov 2008 

    Parameters 
    ----------
    maxsimps : list of tuples 
        The max simplices for the simplicial complex 
    Ncells : int 
        The total number of cells in the population (for computing metric)
    '''
    
    g = nx.Graph()
    depth = 0
    for maxsimp in maxsimps:
        add_cellgroups(g, maxsimp, Ncells, depth)
    return g

def binnedtobinary(popvec, thresh):
    '''
    Takes a popvec array from a binned data file and converts
    to a binary matrix according to thresh

    Parameters
    ----------
    popvec : array
        An NCells by Nwindow array containing firing rates in that window.
    Thresh : float
        Multiple of average firing rate to use for thresholding
    '''

    popvec = np.array(popvec)
    Ncells, Nwin = np.shape(popvec)
    means = popvec.sum(1)/Nwin
    means = np.tile(means, (Nwin, 1)).T
    meanthr = thresh*means

    activeUnits = np.greater(popvec, meanthr).astype(int)
    return activeUnits

def binarytomaxsimplex(binMat, rDup=False, clus=None):
    '''
    Takes a binary matrix and computes maximal simplices according to CI 2008

    Parameters
    ----------
    binMat : numpy array
        An Ncells x Nwindows array
    '''
    if rDup:
        lexInd = np.lexsort(binMat)
        binMat = binMat[:, lexInd]
        diff = np.diff(binMat, axis=1)
        ui = np.ones(len(binMat.T), 'bool')
        ui[1:] = (diff != 0).any(axis=0)
        binMat = binMat[:, ui]

    Ncells, Nwin = np.shape(binMat)
    if not clus:
        clus = np.arange(Ncells)
    MaxSimps = []
    MaxSimps = [tuple(clus[list(np.nonzero(t)[0])]) for t in binMat.T]
    #for win in range(Nwin):
    #    if binMat[:, win].any():
    #        verts = np.arange(Ncells)[binMat[:, win] == 1]
    #        verts = np.sort(verts)
    #        MaxSimps.append(tuple(verts))
    return MaxSimps

def adjacency2maxsimp(adjmat, basis):
    '''
    Converts an adjacency matrix to a list of maximum 1-simplices (edges),
    allowing SimplicialComplex to handle graphs
    '''
    maxsimps = []
    uptr = np.triu(adjmat)
    for b in basis:
        maxsimps.append((b,))
    for ind, row in enumerate(uptr):
        for targ, val in enumerate(row):
            if val > 0:
                maxsimps.append(tuple(sorted((basis[ind], basis[targ]))))
    return maxsimps
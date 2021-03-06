# -*- coding: utf-8 -*-

"""
Performing basic statistics.

Author: R. Lombaert

"""

import types
import scipy
from scipy import array,sqrt,log,pi


def calcChiSquared(data,model,noise):
    
    """
    Calculate the chi-squared value of a data array minus a model array, taking 
    into account the noise in the data array.
    
    @param data: The data set. Must have same dimensions as model!
    @type data: array
    @param model: The model array. Must have same dimensions as data!
    @type model: array
    @param noise: the noise in the data array. Give one value for overall noise
                  or individual values for every entry in data/model. 
    @type noise: float/array

    @return: The chi squared value
    @rtype: float
    
    """
    
    if type(data) not in [types.ListType,scipy.ndarray]:
        data = [data]
    data, model, noise = array(data), array(model), array(noise) 
    return sqrt(((data - model)**2./noise**2.).sum())/len(data)
    
    

def calcLoglikelihood(data,model,noise):
    
    """
    Calculate the loglikelihood value of a data array minus a model array,  
    taking into account the noise in the data array.
    
    @param data: The data set. Must have same dimensions as model!
    @type data: array
    @param model: The model array. Must have same dimensions as data!
    @type model: array
    @param noise: the noise in the data array. 
    @type noise: float/array

    @return: The loglikelihood value
    @rtype: float
    
    """
    
    data, model, noise = array(data), array(model), array(noise) 
    lll = (-log(sqrt(2.*pi)) - log(noise) - 1./2.*((data-model)/noise)**2.).sum()
    return lll
    
    

                
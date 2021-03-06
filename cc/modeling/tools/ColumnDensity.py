# -*- coding: utf-8 -*-

"""
Methods for column density calculation.

Author: R. Lombaert

"""

import os
from scipy.integrate import trapz
from scipy import average, argmax
import math

import cc.path
from cc.tools.io import DataIO
from cc.data import Data


class ColumnDensity(object):
    
    """
    Environment to calculate column densities and similar properties for a 
    Star() object.
    
    """
    
    def __init__(self,star):
        
        """
        Initializing an instance of the ColumnDensity class. 
        
        To be calculated:
         - r_des: The minimum radius, ie where the dust species starts to exist.
                  This is usually where the density of the species rises to 
                  1% of the maximum density of the shell (in cm).
         - t_des: The temperature at the destruction radius r_des of the species
         - r_max: The maximum radius at which species exists, taken to be 
                  outer radius, or where the density of species drops below 
                  10**(-10) times the maximum density in the shell (in cm).
         - t_min: The temperature at the maximum radius r_max of the species
         - coldens: The column density in g/cm2 of the dust species between
                    r_des and r_max
        
        @param star: The model parameter set
        @type star: Star()
        
        """
        
        self.star = star
        self.Rsun = star.Rsun      #in cm
        self.Msun = star.Msun      #in g
        self.year = star.year            #in s 
        self.avogadro = 6.022e23         
        self.au = star.au
        self.r_des = dict()
        self.r_max = dict()
        self.t_min = dict()
        self.t_des = dict()
        self.r_min_cd = dict()
        self.r_max_cd = dict()
        self.compd = dict()
        self.rad = []
        self.coldens = dict()
        self.fullcoldens = dict()
        self.dustfractions = dict()
        self.readDustInfo()
        if int(self.star['MRN_DUST']):
            raise IOError('No column densities can be calculated for now if MRN distribution is used in MCMax.')
    

    def readDustInfo(self):
        
        """
        Read all column densities, min/max temperatures and min/max radii for 
        the species involved in the MCMax model.
        
        Note that the self.coldens dictionary does not give real column 
        densities! This dict merely gives column densities in a prescribed 
        shell with given min and max radius, in order to compare with the H2 
        col density. 
        
        """
        
        dens = self.star.getDustDensity()
        temp = self.star.getDustTemperature()
        compf = os.path.join(cc.path.mcmax,self.star.path_mcmax,'models',\
                             self.star['LAST_MCMAX_MODEL'],'composition.dat')
        comp = DataIO.readCols(compf)
        self.rad = comp.pop(0)*self.au
        self.r_outer = self.rad[-1]
        
        for species in self.star.getDustList():
            #- Save the actual density profile for this dust species, as well
            #- as calculating the full column density of a dust species.
            self.dustfractions[species] = comp.pop(0)
            self.compd[species] = self.dustfractions[species]*dens
            self.fullcoldens[species] = trapz(x=self.rad,y=self.compd[species])      
            #- Determine the column density from 90% of the dust species formed
            #- onward, based on the mass fractions!
            #- Not before, because the comparison with H2 must be made,
            #- and this will skew the result if not solely looking at where the
            #- dust has (almost) all been formed.
            #- We also save min amd max radii, for use with the H2 calculation
            a_species = self.star['A_%s'%species]
            maxdens = max(self.compd[species])
            mindens = maxdens*10**(-10)
            radsel = self.rad[(self.dustfractions[species]>0.9*a_species)*\
                              (self.compd[species]>mindens)]
            denssel = self.compd[species]\
                                [(self.dustfractions[species]>0.9*a_species)*\
                                 (self.compd[species]>mindens)]
            self.coldens[species] = trapz(x=radsel,y=denssel)   
            if radsel.size:
                self.r_min_cd[species] = radsel[0]
                self.r_max_cd[species] = radsel[-1]
            else:
                print 'Threshold dust mass fraction not reached for %s.'%species
                self.r_min_cd[species] = 0
                self.r_max_cd[species] = 0
            #- Determine the actual destruction radius and temperature.
            #- Taken where the density reaches 1% of the maximum density
            #- (not mass fraction).
            self.r_des[species] = self.rad[self.compd[species]>(maxdens*0.01)][0]
            self.t_des[species] = temp[self.compd[species]>(maxdens*0.01)][0]
            
            #- e-10 as limit for minimum is ok, because if shell is 100000 R*
            #- the mass conservation dictates ~ (10^5)^2 = 10^10 (r^2 law) 
            #- decrease in density. Shells this big dont occur anyway.
            self.r_max[species] = self.rad[self.compd[species]>mindens][-1]
            self.t_min[species] = temp[self.compd[species]>mindens][-1]
    
    
    
    def dustFullColDens(self,species):
        
        """
        Calculate the full column density of a dust species in the shell. 
        
        This is NOT the value used for determining the abundance of the species
        
        @param species: The dust species
        @type species: string
        
        @return: The column density of the dust species in the full envelope
                 in g/cm2
        @rtype: float
        
        """
        
        if not species in self.star.getDustList():
            return 0
        return self.fullcoldens[species]
        
    
    def dustFullNumberColDens(self,species):
    
        """
        Calculate the full NUMBER column density of a dust species in the shell. 
        
        This is NOT the number used in determining the equivalent molecular 
        abundance!
        
        @param species: The dust species
        @type species: string
        
        @return: The number column density of the dust species in the full 
                 envelope in cm-2
        @rtype: float
        
        """
        
        if not species in self.star.getDustList():
            return 0
        if not self.star.dust[species]['molar']:
            print 'No molar weight given for dust species %s in Dust.dat.'\
                  %species
            return 0
        cndsp = self.fullcoldens[species]*self.avogadro\
                    /self.star.dust[species]['molar']
        return cndsp
        
        
        
    def dustMolecAbun(self,species):
        
        """ 
        Calculate the molecular abundance of a dust species with respect to H2.
        
        Note that the self.coldens dictionary does not give real column 
        densities! This dict merely gives column densities in a prescribed 
        shell with given min and max radius, in order to compare with the H2 
        col density. 
        
        @param species: the dust species (from Dust.dat)
        @type species: string
        
        @return: The molecular abundance with respect to H2 of the dust species
        @rtype: float
        
        """

        if not species in self.star.getDustList():
            return 0
        if not self.star.dust[species]['molar']:
            print 'No molar weight given for dust species %s in Dust.dat.'\
                  %species
            return 0
        if self.r_min_cd[species] == 0:
            print 'No significant amount of dust species %s found.'%species
            return 0
        cndspecies = self.coldens[species]*self.avogadro\
                        /self.star.dust[species]['molar']
        cndh2 = self.hydrogenColDens(species)
        return cndspecies/cndh2
        
        
    
    def hydrogenColDens(self,species):
        
        """
        Calculate the column number density of molecular hydrogen between two 
        radial distances. 
        
        If a GASTRoNOoM model is calculated, the h2 density profile is taken 
        from there. Otherwise, the value is derived from the total mass-loss 
        rate, assuming everything is H2.
        
        The use of a proper velocity profile can make a big difference for low
        mass-loss rate sources!
        
        @param species: the dust species for which the H2 col dens is 
                        calculated. Required for the radial information. 
        @type species: string
        
        @return: The molecular hydrogen column number density between the given
                 radii (cm-2)
        @rtype: float
        
        """
        
        modelid = self.star['LAST_GASTRONOOM_MODEL']
        rin = self.r_min_cd[species]
        rout = self.r_max_cd[species]
        if modelid:
            rad = self.star.getGasRad(ftype='fgr')
            nh2 = self.star.getGasNumberDensity(ftype='fgr')
            cndh2 = trapz(x=rad[(rad<rout)*(rad>rin)],\
                          y=nh2[(rad<rout)*(rad>rin)])
        else: 
            mdot_gas = float(self.star['MDOT_GAS'])*self.Msun/self.year
            vexp_gas = float(self.star['VEL_INFINITY_GAS']) * 100000
            h2_molar = 2.
            sigma = (1./rin-1./rout)*mdot_gas/vexp_gas/4./math.pi
            cndh2 = sigma * self.avogadro / h2_molar
        return cndh2    
    
    
        
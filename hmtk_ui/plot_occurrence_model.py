#!/usr/bin/env/python

'''
Creates a Gutenberg-Richter plot adjusted for the completeness time
'''

import numpy as np
from math import log10
from openquake.nrmllib import models
from hmtk.seismicity.occurrence.utils import recurrence_table


class GutenbergRichterModel(models.TGRMFD):
    '''
    Class to store more comprehensive Gutenberg-Richter model
    '''
    def __init__(self, b_val, rate, a_val=None, sigma_b=None, sigma_rate=None,
        sigma_a=None, min_mag=None, max_mag=None):
        '''
        Set up model
        '''
        if not a_val:
            # Get a_value from rate and b-value
            if not min_mag:
                raise ValueError('Gutenberg-Richter class needs either '
                                 'a-value or rate & min_magnitude')
            a_val = log10(rate) + b_val * min_mag
        super(GutenbergRichterModel, self).__init__(a_val, b_val, min_mag,
            max_mag)
        self.rate = rate
        self.sigma_b = sigma_b
        self.sigma_rate = sigma_rate
        self.sigma_a = sigma_a


class plotSeismicityRates(object):
    '''
    Simple class to produce a plot of seismicity rates from the earthquake
    catalogue
    '''
    def __init__(self, catalogue, completeness_table=None, start_year=None,
        end_year=None):
        '''
        Set up model
        '''
        self.catalogue = catalogue
        self.completeness = completeness_table
        if completeness_table is not None:
            self.complete_adjust = True
        else:
            self.complete_adjust = False
        if not start_year:
            self.start_year = float(np.min(self.catalogue.data['year']))
        else:
            self.start_year = start_year

        if not end_year:
            self.end_year = float(np.max(self.catalogue.data['year']))
        else:
            self.end_year = end_year
        self.rates = None
        self.output_file = None
        self.dpi = None

    def plot(self, axis, dmag=0.1, model=None):
        '''
        Plots the file
        '''
        self.rates = self._get_cumulative_rate(dmag)
        axis.semilogy(self.rates[:, 0], self.rates[:, 1], 'o', color='b',
                     label='Incremental Rate')
        axis.semilogy(self.rates[:, 0], self.rates[:, 2], 's', color='r',
                     label='Cumulative Rate')
        axis.set_xlabel('Magnitude', fontsize=14)
        axis.set_ylabel('Annual rates', fontsize=14)
        if model:
            # Can plot the fitted model
            cum_model_rates = 10. ** (model.a_val -
                                      model.b_val * self.rates[:, 0])
            axis.semilogy(
                self.rates[:, 0],
                cum_model_rates, 'r-',
                label='Model: %6.2f - %6.2f M' %(model.a_val, model.b_val))
        axis.legend(loc=1)

    def _get_incremental_rate(self, dmag):
        '''
        Gets the completeness adjusted incremental seismicity rate for each
        event
        '''
        inc = 1E-12
        obs_rates = recurrence_table(self.catalogue.data['magnitude'],
                                     dmag,
                                     self.catalogue.data['year'])
        if self.complete_adjust:
            obs_time = self.end_year - self.completeness[:, 0] + 1.
            obs_rates[:, 1] = obs_rates[:, 1] / (self.end_year -
                                                 self.start_year + 1)
            n_comp = np.shape(self.completeness)[0]
            for iloc in range(n_comp - 2, -1, -1):
                comp_mag = self.completeness[iloc, 1]
                comp_year = self.completeness[iloc, 0]
                mag_idx = np.logical_and(
                    self.catalogue.data['magnitude'] >=
                    self.completeness[iloc, 1] - inc,
                    self.catalogue.data['magnitude'] <
                    self.completeness[iloc + 1, 1] - inc)

                idx = np.logical_and(mag_idx,
                    self.catalogue.data['year'] >= comp_year - inc)

                temp_rates = recurrence_table(
                    self.catalogue.data['magnitude'][idx],
                    dmag,
                    self.catalogue.data['year'][idx])
                temp_rates[:, 1] = temp_rates[:, 1] / obs_time[iloc]
                obs_idx = np.logical_and(
                    obs_rates[:, 0] >= comp_mag,
                    obs_rates[:, 0] < self.completeness[iloc + 1, 1])
                obs_rates[obs_idx, 1] = temp_rates[:, 1]
        return obs_rates[:, :2]

    def _get_cumulative_rate(self, dmag):
        '''
        Gets the completeness adjusted cumulative eeismicity rate for each
        event
        '''
        inc_rates = self._get_incremental_rate(dmag)
        num_rates = np.shape(inc_rates)[0]
        cum_rates = np.zeros(num_rates)
        for iloc in range(0, num_rates):
            cum_rates[iloc] = np.sum(inc_rates[iloc:, 1])
        log_cum_rates = np.log10(cum_rates)
        return np.column_stack([inc_rates, cum_rates, log_cum_rates])

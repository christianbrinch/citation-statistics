#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Citation statistics code

This small python scrip will download a list of publications associated with an
ORCID ID and search for citations on ADS.

Example:
    This script can be run from the command line or from within python.

        $ ./citations.py update

    if the update flag is omitted, the citation database will not be updated.


"""

__author__ = "Christian Brinch"
__copyright__ = "Copyright 2012-2016"
__credits__ = ["Christian Brinch"]
__license__ = "AFL 3.0"
__version__ = "1.0"
__maintainer__ = "Christian Brinch"
__email__ = "brinch@nbi.ku.dk"


import sys
import pickle
from datetime import date
import numpy as np
import requests
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.ticker import AutoMinorLocator



class OnePaper(object):
    ''' A class that contains information about a single paper
    '''
    def __init__(self, attr):
        self.author = []
        self.citations_by_month = []
        self.selfcitations = 0
        self.citations = 0
        for key in attr:
            self.__dict__[key] = attr[key]

    def first_author(self):
        ''' Determine the color based on first author
        '''
        if "Brinch" in self.author[0]:
            paper_color = 'red'
        else:
            paper_color = 'blue'
        return paper_color

    def get_citations(self, citation_list):
        ''' Scrape citation information from ADS
        '''
        self.citations = len(citation_list)

        bibcodes = "bibcode"
        for citer in citation_list:
            bibcodes += "\n"+citer

        query_url = "https://api.adsabs.harvard.edu/v1/search/bigquery"
        headers = {
            'Authorization': 'Bearer:OnVZIdDD8oGy11bLaCnLZlBbbkNfKU1k0jd8FQ6L'}
        params = {'q': '*:*',
                  'wt': 'json',
                  'fl': 'pubdate, first_author', 'rows': '1000'}
        response = requests.post(query_url, data=bibcodes,
                                 headers=headers, params=params).json()


        for entry in response['response']['docs']:
            pubdate = entry['pubdate'].split("-")
            self.citations_by_month.append(
                float(pubdate[0])+(float(pubdate[1])-1.)/12.)
            if entry['first_author'] in self.author:
                self.selfcitations += 1



def moving_average(data_array, smooth_level=3):
    ''' Calculate the running average
        Used to smooth out citation statistics
    '''
    ret = np.cumsum(data_array, dtype=float)
    ret[smooth_level:] = ret[smooth_level:] - ret[:-smooth_level]
    return ret[smooth_level - 1:] / smooth_level


def hindex_calc(papers, first_publication):
    ''' Calculate the h-index and the h5-index (h-index over the last 5 years)
    '''
    total_months = int((NOW-first_publication)*12.)+2
    hidx = []
    h5idx = []
    for i in range(total_months):
        year = first_publication + i % 12 + (i - (i % 12 * 12))/12.
        current_citations = []
        current_short_citations = []
        for paper in papers:
            current_citations.append(0)
            current_short_citations.append(0)
            for citation in paper.citations_by_month:
                if citation < year:
                    current_citations[-1] += 1
                if citation < year and citation > (year-5):
                    current_short_citations[-1] += 1

        number_of_citations = sorted(current_citations, reverse=True)
        number_of_short_citations = sorted(current_short_citations, reverse=True)
        hidx.append(0)
        h5idx.append(0)
        for i in range(len(papers)):
            if (i+1) <= number_of_citations[i]:
                hidx[-1] += 1
            if (i+1) <= number_of_short_citations[i]:
                h5idx[-1] += 1

    return hidx, h5idx

def query_orcid():
    ''' Get dois from ORCID
    '''
    query_url = "https://pub.orcid.org/"+ORCID+"/works"
    response = requests.get(query_url)
    lines = response.text.split('\n')
    dois = []
    for line in lines:
        if "<common:external-id-value>10" in line:
            dois.append(line.split("<common:external-id-value>")[
                1].split("</common:external-id-value>")[0])
            dois[-1] = dois[-1].encode("utf-8").replace(":", "/")

    dois = list(set(dois))
    return dois

def citations_in_time(papers, first_publication, fig_nr):
    ''' Citations in time
    '''
    total_citations = sum([paper.citations for paper in papers])
    total_selfcite = sum([paper.selfcitations for paper in papers])
    print "Total number of citations: ", total_citations
    print "Number of citations without self-citations", total_citations - total_selfcite

    fig = plt.figure(fig_nr)
    ax1 = fig.add_subplot(111)
    ax1.set_xlim(first_publication-1., NOW+2.)
    ax1.xaxis.set_major_formatter(FormatStrFormatter('%d'))
    ax1.set_ylim(0, 1.2*total_citations)
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Number of citations')
    ax1.minorticks_on()


    cite = np.arange(total_citations)
    citetimes = [time for paper in papers for time in paper.citations_by_month]
    ax1.plot(sorted(citetimes), cite, lw=1.5)
    ax1.plot([first_publication-1., NOW+2.], [1000, 1000], '--', color='black')








def citations_per_month(papers, first_publication, fig_nr):
    ''' Citations per month
    '''
    fig = plt.figure(fig_nr)
    ax1 = fig.add_subplot(111)
    plt.xticks(np.arange(first_publication-1, int(NOW)+1, 1))
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Citations per month')
    ax1.xaxis.set_minor_locator(AutoMinorLocator(12))

    citetimes = [time for paper in papers for time in paper.citations_by_month]
    citetimes = np.array(sorted(citetimes))
    total_months = int((NOW-first_publication)*12.)
    plt.hist(citetimes, bins=total_months, range=(
        int(first_publication-1), int(NOW)+1), facecolor='green')









def hindex_in_time(hindex, h5index, first_publication, fig_nr):
    ''' h-index in time
    '''
    fig = plt.figure(fig_nr)
    ax1 = fig.add_subplot(111)
    ax1.set_xlim(first_publication-1, NOW+2)
    ax1.xaxis.set_major_formatter(FormatStrFormatter('%d'))
    ax1.set_ylim(0, 20)
    ax1.set_xlabel('Year')
    ax1.set_ylabel('h-index')
    ax1.minorticks_on()

    ax1.plot(first_publication+np.arange(len(hindex))/12., hindex, color='blue', lw=1.5)
    x_axis = np.arange(len(hindex))/12. + first_publication
    ax1.plot(x_axis, x_axis-first_publication, color='black', lw=1.5)
    ax1.plot(x_axis, 2*(x_axis-first_publication), color='black', lw=1.5)
    ax1.plot(first_publication+np.arange(len(h5index))/12., h5index, color='red', lw=1.5)
    ax1.plot(x_axis, (hindex[-1]/(NOW-first_publication)) *
             (x_axis-first_publication), '--', color='orange', lw=1.5)

    x_short = np.array([NOW-3., NOW])
    ax1.plot(x_short, (hindex[-1]-hindex[-36])/3.*(x_short-(NOW-3.)) +
             hindex[-36], '--', color='purple', lw=1.5)

    print "h-index:", hindex[-1]
    print "h-index slope:", hindex[-1]/(NOW-first_publication)
    print "h5-index:", h5index[-1]









def citations_per_paper(papers, hindex, fig_nr):
    ''' Citations per paper
    '''
    sorted_papers = sorted(papers, key=lambda x: x.pubdate, reverse=True)
    sorted_papers = sorted(papers, key=lambda x: x.citations, reverse=True)
    fig = plt.figure(fig_nr)
    ax1 = fig.add_subplot(111)
    ax1.set_xlim(0, 2*len(papers)+2)
    ax1.set_ylabel('Citations')
    ax1.minorticks_on()
    plt.xticks(np.arange(0, 2*len(papers)+2, 2.0)+0.5)
    ax1.tick_params(axis='x', which='both', labelsize=8)
    ax1.set_xticklabels([paper.title[0][0:20].encode("utf-8") for paper in sorted_papers], rotation=45,
                        rotation_mode="anchor", ha="right")

    cites = map(int, [paper.citations for paper in sorted_papers])
    ax1.bar(2*np.arange(len(papers))+0.25, cites, color=[i.first_author() for i in sorted_papers])
    cites = map(
        int, [paper.citations-paper.selfcitations for paper in sorted_papers])
    ax1.bar(2*np.arange(len(papers))+0.9, cites,
            color=[i.first_author() for i in sorted_papers], alpha=0.5)
    ax1.plot([0, 2*len(papers)+0.25], [hindex[-1], hindex[-1]], '--', color='black')
    ax1.text(2*len(papers)-5, hindex[-1]+2, 'h-index')







def citations_per_paper_in_time(papers, first_publication, hindex, fig_nr):
    ''' Citations per paper in time
    '''
    fig = plt.figure(fig_nr)
    ax1 = fig.add_subplot(111)
    ax1.xaxis.set_major_formatter(FormatStrFormatter('%d'))
    ax1.set_xlim(-1, int(NOW)-first_publication)
    ax1.set_xlabel('Years after publication')
    ax1.set_ylabel('Citations')
    ax1.minorticks_on()
    plt.tick_params(axis='both', which='both', width=0.4)

    for paper in papers:
        cite = np.arange(paper.citations)
        citetimes = [time-paper.pubdate for time in paper.citations_by_month]

        if len(citetimes) > 2:
            plt.plot(moving_average(sorted(citetimes)), cite[1:-1],
                     color=paper.first_author(), lw=1.5, alpha=0.8)

    x_axis = np.arange(len(hindex))/12.
    plt.plot(x_axis, 12.*x_axis, '--', color='black')






def get_papers():
    ''' Main part of citations.py.
        First get list of papers from ORCID.
        Then scrape citation information from ADS.
        Then produce plots.
    '''
    papers = []
    update = False
    if len(sys.argv) > 1:
        if sys.argv[1] == 'update':
            update = True

    # Get paper list from ORCID
    dois = query_orcid()

    # Scrape paper citation info from ADS
    if update:
    #   This following block of code works, once the ADS API allows bigquery
    #   using dois instead of bibcodes
    #
    #    params = {'q': '*:*',
    #              'wt': 'json',
    #              'rows': '1000',
    #              'fl': 'pubdate, title, bibcode, first_author, citation'}
    #    data = "doi"
    #    for doi in dois:
    #        data += "\n"+doi
    #    response = requests.get(query_URL, headers=headers, data=data, params=params).json()
        temp_url = "https://api.adsabs.harvard.edu/v1/search/query"
        headers = {
            'Authorization': 'Bearer:OnVZIdDD8oGy11bLaCnLZlBbbkNfKU1k0jd8FQ6L'}
        for doi in dois:
            params = {'q': doi,
                      'wt': 'json',
                      'fl': 'pubdate, title, bibcode, author, citation'}
            response = requests.get(temp_url, headers=headers, params=params).json()

            entry = response['response']['docs'][0]
            tmpdate = entry['pubdate'].split("-")
            entry['pubdate'] = float(tmpdate[0]) + (float(tmpdate[1]) - 1.)/12.
            entry['doi'] = doi

            papers.append(OnePaper(entry))

            if 'citation' in entry:
                papers[-1].get_citations(entry['citation'])

            print papers[-1].title[0].encode('utf-8')
            print "Number of citations: ", papers[-1].citations

        pickle.dump(papers, open("datadump.p", "wb"))
    else:
        papers = pickle.load(open("datadump.p", "rb"))

    return papers








reload(sys)
sys.setdefaultencoding('utf8')
ORCID = '0000-0002-5074-7183'
NOW = date.today().year+date.today().month/12.

papers = get_papers()
first_publication = min(papers, key=lambda x: x.pubdate).pubdate
hindex, h5index = hindex_calc(papers, first_publication)
citations_in_time(papers, first_publication, 1)
citations_per_month(papers, first_publication, 2)
hindex_in_time(hindex, h5index, first_publication, 3)
citations_per_paper(papers, hindex, 4)
citations_per_paper_in_time(papers, first_publication, hindex, 5)

plt.show()

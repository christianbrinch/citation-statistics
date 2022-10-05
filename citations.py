#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Citation statistics code

This small python scrip will download a list of publications associated with an
ORCID ID and search for citations on ADS.

Example:
    This script can be run from the command line or from within python.

        $ ./citations.py update xxxx-xxxx-xxxx-xxxx

    where xxxx-xxxx-xxxx-xxxx is the ORCID ID.
    If the update flag is omitted, the citation database will not be updated.


"""

__author__ = "Christian Brinch"
__copyright__ = "Copyright 2012-2020"
__credits__ = ["Christian Brinch"]
__license__ = "AFL 3.0"
__version__ = "1.1"
__maintainer__ = "Christian Brinch"
__email__ = "cbri@dtu.dk"


import sys
import pickle
import math
from datetime import date
import numpy as np
import seaborn as sns
import requests
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import MaxNLocator
import pubmed


MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
          'October', 'November', 'December']


class OnePaper():
    ''' A class that contains information about a single paper
    '''

    def __init__(self, attr):
        self.caller = None
        self.author = []
        self.citations_by_month = []
        self.selfcitations = 0
        self.citations = 0
        for key in attr:
            self.__dict__[key] = attr[key]

    def first_author(self):
        ''' Determine the color based on first author
        '''
        if self.caller in self.author[0]:
            paper_color = sns.xkcd_rgb['pale red']
        else:
            paper_color = sns.xkcd_rgb['denim blue']
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

        try:
            for entry in response['response']['docs']:
                pubdate = entry['pubdate'].split("-")
                self.citations_by_month.append(
                    float(pubdate[0])+(float(pubdate[1])-1.)/12.)
                if entry['first_author'] in self.author:
                    self.selfcitations += 1
        except AttributeError:
            print("Key error")
            print(response)

################################################################################
#
# AUXILIARY FUNCTIONS INCLUDING AXIS SETUP, MOVING AVERAGE, AND HINDEX CALC
#
################################################################################


def setup_axis(fig_nr, **params):
    ''' Setup axis based on parameters sent from plot functions
    '''
    _ = plt.figure(fig_nr)
    axe = plt.subplot(111)
    axe.set_xlim(params['xlim'][0], params['xlim'][1])
    axe.set_xlabel(params['xlabel'])
    if 'xticks' in params:
        plt.xticks(params['xticks'])
    if 'ylim' in params:
        axe.set_ylim(params['ylim'][0], params['ylim'][1])
    axe.set_ylabel(params['ylabel'])
    axe.xaxis.set_major_formatter(FormatStrFormatter('%d'))
    axe.yaxis.set_major_locator(MaxNLocator(integer=True))
    axe.minorticks_on()
    if 'minor_locator' in params:
        axe.xaxis.set_minor_locator(AutoMinorLocator(12))

    return axe


def moving_average(data_array, smooth_level=3):
    ''' Calculate the running average
        Used to smooth out citation statistics
    '''
    ret = np.cumsum(data_array, dtype=float)
    ret[smooth_level:] = ret[smooth_level:] - ret[:-smooth_level]
    return ret[smooth_level - 1:] / smooth_level


def hindex_calc(papers):
    ''' Calculate the h-index and the h5-index (h-index over the last 5 years)
    '''
    total_months = int((NOW-START)*12.)+2
    hidx = []
    h5idx = []
    for i in range(total_months):
        year = START + i / 12.
        current_citations = []
        current_short_citations = []
        for paper in papers:
            current_citations.append(0)
            current_short_citations.append(0)
            for citation in paper.citations_by_month:
                if citation < year:
                    current_citations[-1] += 1
                if (year-5) < citation < year:
                    current_short_citations[-1] += 1

        number_of_citations = sorted(current_citations, reverse=True)
        number_of_short_citations = sorted(
            current_short_citations, reverse=True)
        hidx.append(0)
        h5idx.append(0)
        for j in range(len(papers)):
            if (j+1) <= number_of_citations[j]:
                hidx[-1] += 1
            if (j+1) <= number_of_short_citations[j]:
                h5idx[-1] += 1

    return hidx, h5idx


################################################################################
#
# FUNCTIONS TO GENERATE PLOTS
#
################################################################################
def citations_in_time(papers, fig_nr):
    ''' Plot citations in time
    '''
    total_citations = sum([paper.citations for paper in papers])
    total_selfcite = sum([paper.selfcitations for paper in papers])
    print("Total number of citations: ", total_citations)
    print("Number of citations without self-citations", total_citations - total_selfcite)

    axis_params = {'xlim': (START-1., NOW+2.),
                   'xlabel': 'Year',
                   'ylim': (0, 1.2*total_citations),
                   'ylabel': 'Number of citations'}
    axe = setup_axis(fig_nr, **axis_params)

    cite = np.arange(total_citations)
    citetimes = [time for paper in papers for time in paper.citations_by_month]
    if len(cite) > len(citetimes):  # sometimes ads has the wrong number of citations
        cite = cite[:len(citetimes)]
    axe.plot(sorted(citetimes), cite, alpha=0.8, lw=1.8)
    axe.plot([START-1., NOW+2.], [1000, 1000], '--', alpha=0.8, color='black')


def citations_per_month(papers, fig_nr):
    ''' Plot citations per month
    '''

    axis_params = {'xlim': (START-1., NOW+2.),
                   'xlabel': 'Year',
                   'xticks': np.arange(START-1, int(NOW)+2, 1),
                   'ylabel': 'Citations per month',
                   'minor_locator': 12}
    axe = setup_axis(fig_nr, **axis_params)

    citetimes = [time for paper in papers for time in paper.citations_by_month]
    citetimes = np.array(sorted(citetimes))
    total_months = (int(NOW+1)-int(START-1))*12

    axe.hist(citetimes, bins=total_months, range=(
        int(START-1), int(NOW)+1), facecolor=sns.xkcd_rgb['faded green'])


def hindex_in_time(papers, fig_nr):
    ''' Plot h-index in time
    '''
    hindex, h5index = hindex_calc(papers)
    axis_params = {'xlim': (START-1., NOW+2.),
                   'xlabel': 'Year',
                   'ylabel': 'h-index'}
    axe = setup_axis(fig_nr, **axis_params)

    axe.plot(START+np.arange(len(hindex)) /
             12., hindex, color=sns.xkcd_rgb['denim blue'], lw=1.8)
    x_axis = np.arange(len(hindex))/12. + START
    axe.plot(x_axis, x_axis-START, color='black', lw=1.8, alpha=0.8)
    axe.plot(x_axis, 2*(x_axis-START), color='black', lw=1.8, alpha=0.8)
    axe.plot(START+np.arange(len(h5index)) /
             12., h5index, color=sns.xkcd_rgb['pale red'], lw=1.8)
    axe.plot(x_axis, (hindex[-1]/(NOW-START)) *
             (x_axis-START), '--', color=sns.xkcd_rgb['amber'], lw=1.8)

    x_short = np.array([NOW-3., NOW])
    axe.plot(x_short, (hindex[-1]-hindex[-36])/3.*(x_short-(NOW-3.)) +
             hindex[-36], '--', color=sns.xkcd_rgb['faded green'], lw=1.8)

    print("h-index: {0:d}".format(hindex[-1]))
    print("h-index slope: {0:0.2f}".format(hindex[-1]/(NOW-START)))
    print("h5-index: {0:d}".format(h5index[-1]))


def citations_per_paper(papers, fig_nr):
    ''' Plot citations per paper
    '''
    axis_params = {'xlim': (0, 2*len(papers)+2),
                   'xlabel': '',
                   'xticks': np.arange(0, 2*len(papers)+0, 2.0)+0.5,
                   'ylabel': 'Citations'}
    axe = setup_axis(fig_nr, **axis_params)

    hindex, _ = hindex_calc(papers)
    sorted_papers = sorted(papers, key=lambda x: x.citations, reverse=True)

    axe.minorticks_off()
    axe.set_xticklabels([paper.title[0][0:20] for paper in sorted_papers], rotation=45,
                        rotation_mode="anchor", ha="right", fontsize=6)

    cites = list(map(int, [paper.citations for paper in sorted_papers]))

    axe.bar(2*np.arange(len(papers))+0.25, cites,
            color=[i.first_author() for i in sorted_papers])
    cites = list(map(
        int, [paper.citations-paper.selfcitations for paper in sorted_papers]))
    axe.bar(2*np.arange(len(papers))+0.9, cites,
            color=[i.first_author() for i in sorted_papers], alpha=0.8)
    axe.plot([0, 2*len(papers)+0.25],
             [hindex[-1], hindex[-1]], '--', color='black', alpha=0.6)
    axe.text(2*len(papers)-5, hindex[-1]+2, 'h-index')


def citations_per_paper_in_time(papers, fig_nr):
    ''' Plot citations per paper in time
    '''
    axis_params = {'xlim': (-1, NOW+1-START),
                   'xlabel': 'Years after publication',
                   'ylabel': 'Citations'}
    axe = setup_axis(fig_nr, **axis_params)

    for paper in papers:
        cite = np.arange(paper.citations)
        citetimes = [time-paper.pubdate for time in paper.citations_by_month]
        if len(cite) == len(citetimes):
            axe.plot(moving_average(sorted(citetimes)), cite[1:-1],
                     color=paper.first_author(), lw=1.8, alpha=0.8)

    x_axis = np.arange(int((NOW-START)*12.))/12.
    axe.plot(x_axis, 12.*x_axis, '--', color='black', alpha=0.8)


def publications_in_time(papers, fig_nr):
    ''' Plot publication history per year
    '''
    axis_params = {'xlim': (START-1., NOW+2.),
                   'xlabel': 'Year',
                   'xticks': np.arange(START-1, int(NOW)+2, 1),
                   'ylabel': 'Publications per year'}
    axe = setup_axis(fig_nr, **axis_params)
    publications = [int(paper.pubdate) for paper in papers]
    total_years = (int(NOW+2)-int(START-1))

    axe.hist(publications, bins=total_years, range=(
        int(START-1), int(NOW)+2), facecolor=sns.xkcd_rgb['faded green'])




def publication_list(papers):
    ''' Prepare mark down publication list to pdf
    '''
    with open("publications.md", 'w') as md_file:
        md_file.write("## Publications\n\n")
        md_file.write(str(len(papers))+" refereed papers (")
        md_file.write(str(sum([1 for paper in papers if paper.first_author() ==
                               sns.xkcd_rgb['pale red']]))+" as first author); more than ")
        md_file.write(
            str(math.floor(sum([paper.citations for paper in papers])/100)*100)+" citations (")
        md_file.write("h-index of "+str(hindex_calc(papers)[0][-1])+")\n\n")

        for idx, paper in enumerate(papers):
            md_file.write("("+str(idx+1)+") ")
            flag = 0
            for pos, fullname in enumerate(paper.author):
                surname = fullname.split(', ')[0]
                nameparts = fullname.split(', ')[1:][0].split(' ')
                for entry, part in enumerate(nameparts):
                    nameparts[entry] = part[0]+'.'

                name = (' ').join([surname]+nameparts)

                if pos == len(paper.author)-1:
                    md_file.write(" and ")
                if "Brinch" in name:
                    md_file.write("__"+name+"__")
                    flag = 1
                elif pos > 10:
                    if flag == 0:
                        md_file.write("**et al.**")
                    else:
                        md_file.write("et al.")
                    break
                else:
                    md_file.write(name)
                if pos != len(paper.author)-1 and len(paper.author) > 2:
                    md_file.write(", ")

            md_file.write("<BR>")
            md_file.write(paper.title[0]+"<BR>")
            md_file.write(paper.pub + ", "+str(paper.volume) +
                          ", "+str(paper.page[0])+", ")
            month = int(np.round((paper.pubdate-math.floor(paper.pubdate))*12.))
            md_file.write(MONTHS[month]+" "+str(int(paper.pubdate)))
            if paper.citations > 0:
                md_file.write(" ("+str(paper.citations)+" citations)")
            md_file.write("<BR>")
            md_file.write("\n\n")

################################################################################
#
# PROCESS PAPERS FROM ORCID AND ADS
#
################################################################################


def query_orcid(orcid):
    ''' Get name and dois from ORCID
        First entry of dois is the name of the ORCID ID owner
    '''
    query_url = "https://pub.orcid.org/"+orcid+"/person"
    response = requests.get(query_url)
    lines = response.text.split('\n')
    for line in lines:
        if "family-name" in line:
            name = [line.split("<personal-details:family-name>")[
                1].split("</personal-details:family-name>")[0]]

    dois = []
    query_url = "https://pub.orcid.org/"+orcid+"/works"
    response = requests.get(query_url)
    lines = response.text.split('\n')
    for line in lines:
        if "<common:external-id-value>10" in line:
            dois.append(line.split("<common:external-id-value>")[
                1].split("</common:external-id-value>")[0])
            dois[-1] = dois[-1].encode("utf-8")  # .replace(":", "%3a")

    dois = list(set(dois))

    return dois, name


def get_papers(orcid, update=False):
    ''' First get list of papers from ORCID.
        Then scrape citation information from ADS.
    '''
    papers = []

    # Get paper list from ORCID
    dois, name = query_orcid(orcid)

    # Scrape paper citation info from ADS
    if update:
        temp_url = "https://api.adsabs.harvard.edu/v1/search/query"
        headers = {
            'Authorization': 'Bearer:OnVZIdDD8oGy11bLaCnLZlBbbkNfKU1k0jd8FQ6L'}

        for doi in dois:
            params = {'q': '\"'+doi.decode('utf8')+'\"',
                      'wt': 'json',
                      'fl': 'pubdate, title, bibcode, author, citation, pub, issue, volume, page'}



            response = requests.get(
                temp_url, headers=headers, params=params).json()

            if response['response']['docs']:
                entry = response['response']['docs'][0]
                tmpdate = entry['pubdate'].split("-")
                entry['pubdate'] = float(tmpdate[0]) + (float(tmpdate[1]) - 1.)/12.
                entry['doi'] = doi
                entry['caller'] = name[0]

                papers.append(OnePaper(entry))

                if 'citation' in entry:
                    #entry['citation'] = [i for i in entry['citation'] if ('arXiv' not in i) if ('book' not in i) if ('conf' not in i)]
                    #print(entry['citation'])
                    if len(entry['citation'])>0:
                        papers[-1].get_citations(entry['citation'])

            else:
                papers.append(OnePaper(pubmed.data[doi]))

            print(papers[-1].title[0].encode('utf-8'))
            print("Number of citations: ", papers[-1].citations)

        print('Total number of papers: ', len(dois))
        papers.sort(key=lambda x: x.pubdate, reverse=True)
        pickle.dump(papers, open("datadump.p", "wb"))
    else:
        papers = pickle.load(open("datadump.p", "rb"))

    return papers


################################################################################
#
# MAIN PART OF PROGRAM
#
################################################################################

if __name__ == '__main__':
    sns.set()
    ORCID = '0000-0002-5074-7183'
    UPDATE = False
    if len(sys.argv) > 1:
        for arg in sys.argv:
            if '-' in arg:
                ORCID = arg
            if 'update' in arg:
                UPDATE = True

    NOW = date.today().year+date.today().month/12.
    PAPERS = get_papers(ORCID, UPDATE)
    START = np.min([paper.pubdate for paper in PAPERS])
    citations_in_time(PAPERS, 1)
    citations_per_month(PAPERS, 2)
    hindex_in_time(PAPERS, 3)
    citations_per_paper(PAPERS, 4)
    citations_per_paper_in_time(PAPERS, 5)
    publications_in_time(PAPERS, 6)

    publication_list(PAPERS)

    plt.show()

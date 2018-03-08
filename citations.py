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
from urllib2 import *
import requests
import re
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
import numpy as np
import pickle
from datetime import date
from scipy.optimize import curve_fit
from scipy.misc import factorial
from matplotlib.ticker import FormatStrFormatter
from matplotlib.ticker import AutoMinorLocator

reload(sys)
sys.setdefaultencoding('utf8')


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


class aPaper(object):
    def __init__(self, identifier, doi, title, nCitations, selfCitations,
                 pubYear, citationsByMonth, pi):
        self.identifier = identifier
        self.doi = doi
        self.title = title
        self.nCitations = nCitations
        self.nSelfCitations = selfCitations
        self.pubYear = pubYear
        self.citationsByMonth = citationsByMonth
        self.pi = pi


papers = []
update = False
if (len(sys.argv) > 1):
    if sys.argv[1] == 'update':
        update = True

now = date.today().year+date.today().month/12.


# Get paper list from ORCID
webpage = urlopen("https://pub.orcid.org/0000-0002-5074-7183/works")
content = webpage.read()
webpage.close()
lines = content.split('\n')
for i in range(len(lines)):
    if "<activities:group>" in lines[i]:
        papers.append(aPaper("", "", "", 0, 0, 0, [], 'blue'))
        while "</activities:group>" not in lines[i]:
            if "<common:external-id-value>10" in lines[i]:
                papers[-1].doi = lines[i].split("<common:external-id-value>")[
                    1].split("</common:external-id-value>")[0]
            i += 1
        if papers[-1].doi == '':
            papers.pop(-1)

npapers = len(papers)

# Scrape paper citation info from ADS
if update:
    queryURL = "https://api.adsabs.harvard.edu/v1/search/bigquery"
    headers = {
        'Authorization': 'Bearer:OnVZIdDD8oGy11bLaCnLZlBbbkNfKU1k0jd8FQ6L'}

    for paper in papers:
        params = {'q': paper.doi.replace(
            ":", "/"), 'wt': 'json',
            'fl': 'pubdate, title, bibcode, first_author, citation'}
        response = requests.get(queryURL,
                                headers=headers, params=params).json()

        paper.title = response['response']['docs'][0]['title'][0]

        paper.identifier = response['response']['docs'][0]['bibcode']
        pubdate = response['response']['docs'][0]['pubdate'].split("-")
        paper.pubYear = float(pubdate[0])+(float(pubdate[1])-1.)/12.
        firstAuthor = response['response']['docs'][0]['first_author']
        if "Brinch" in firstAuthor:
            paper.pi = 'red'

        if 'citation' in response['response']['docs'][0]:
            paper.nCitations = len(
                response['response']['docs'][0]['citation'])

            bibcodes = "bibcode"
            for citer in response['response']['docs'][0]['citation']:
                bibcodes += "\n"+citer

            params = {'q': '*:*', 'wt': 'json',
                      'fl': 'pubdate, author', 'rows': '1000'}
            response = requests.post(queryURL, data=bibcodes,
                                     headers=headers, params=params).json()

            for entry in response['response']['docs']:
                pubdate = entry['pubdate'].split("-")
                paper.citationsByMonth.append(
                    float(pubdate[0])+(float(pubdate[1])-1.)/12.)
                if firstAuthor in entry['author']:
                    paper.nSelfCitations += 1
        else:
            paper.nCitations = 0

        print paper.title
        print "Number of citations: ", paper.nCitations

    pickle.dump(papers, open("datadump.p", "wb"))

else:
    papers = pickle.load(open("datadump.p", "rb"))


papersSorted = sorted(papers, key=lambda x: x.pubYear, reverse=True)
papersSorted = sorted(papers, key=lambda x: x.nCitations, reverse=True)

total_citations = sum([paper.nCitations for paper in papers])
total_selfcite = sum([paper.nSelfCitations for paper in papers])
print "Total number of citations: ", total_citations
print "Number of citations without self-citations", total_citations - total_selfcite


fig_nr = 1

# Citations in time
fig = plt.figure(fig_nr)
ax = fig.add_subplot(111)
ax.set_xlim(2006, now+2)
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
ax.set_ylim(0, total_citations+0.2*total_citations)
ax.set_xlabel('Year')
ax.set_ylabel('Number of citations')
ax.minorticks_on()
cite = np.arange(total_citations)
citetimes = [time for paper in papers for time in paper.citationsByMonth]
ax.plot(sorted(citetimes), cite, lw=1.5)
ax.plot([0, now+2], [1000, 1000], '--', color='black')


# Citations per month
fig_nr += 1
fig = plt.figure(fig_nr)
ax = fig.add_subplot(111)
plt.xticks(np.arange(2006, int(now)+1, 1))
ax.xaxis.set_minor_locator(AutoMinorLocator(12))
ax.set_xlabel('Year')
ax.set_ylabel('Citations per month')
tmp = np.array(sorted(citetimes))
nmonths = (int(now)-2006+1)*12
plt.hist(tmp, bins=nmonths, range=(2006, int(now)+1), facecolor='green')


# h-index in time
fig_nr += 1
fig = plt.figure(fig_nr)
ax = fig.add_subplot(111)
ax.set_xlim(2006, now+2)
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
ax.set_ylim(0, 20)
ax.set_xlabel('Year')
ax.set_ylabel('h-index')
ax.minorticks_on()


nMonth = int((now-2007.0)*12)+2
hindex = []
h5index = []
for i in range(nMonth):
    year = 2007 + i % 12 + (i - (i % 12 * 12))/12.
    currentCitations = []
    currentShortCitations = []
    for paper in papers:
        currentCitations.append(0)
        currentShortCitations.append(0)
        for citation in paper.citationsByMonth:
            if citation < year:
                currentCitations[-1] += 1
            if citation < year and citation > (year-5):
                currentShortCitations[-1] += 1

    numberOfCitation = sorted(currentCitations, reverse=True)
    numberOfShortCitation = sorted(currentShortCitations, reverse=True)
    hindex.append(0)
    h5index.append(0)
    for i in range(npapers):
        if (i+1) <= numberOfCitation[i]:
            hindex[-1] += 1
        if (i+1) <= numberOfShortCitation[i]:
            h5index[-1] += 1

ax.plot(2007+np.arange(len(hindex))/12., hindex, color='blue', lw=1.5)
x = np.arange(len(hindex))/12. + 2007
ax.plot(x, x-2007, color='black', lw=1.5)
ax.plot(x, 2*(x-2007), color='black', lw=1.5)
ax.plot(2007+np.arange(len(h5index))/12., h5index, color='red', lw=1.5)
ax.plot(x, (hindex[-1]/(now-2007))*(x-2007), '--', color='orange', lw=1.5)

xp = np.array([now-3., now])
ax.plot(xp, (hindex[-1]-hindex[-36])/3.*(xp-(now-3.)) +
        hindex[-36], '--', color='purple', lw=1.5)


print "h-index:", hindex[-1]
print "h-index slope:", hindex[-1]/(now-2007)
print "h5-index:", h5index[-1]


# Citations per paper
fig_nr += 1
fig = plt.figure(fig_nr)
ax = fig.add_subplot(111)
ax.set_xlim(0, 2*npapers+2)
ax.set_ylabel('Citations')
ax.minorticks_on()
plt.xticks(np.arange(0, 2*npapers+2, 2.0)+0.5)
ax.tick_params(axis='x', which='both', labelsize=8)
ax.set_xticklabels([paper.title[0:20] for paper in papersSorted], rotation=45,
                   rotation_mode="anchor", ha="right")
cites = map(int, [paper.nCitations for paper in papersSorted])
ax.bar(2*np.arange(npapers)+0.25, cites, color=[i.pi for i in papersSorted])
cites = map(
    int, [paper.nCitations-paper.nSelfCitations for paper in papersSorted])
ax.bar(2*np.arange(npapers)+0.9, cites,
       color=[i.pi for i in papersSorted], alpha=0.5)
ax.plot([0, 2*npapers+0.25], [hindex[-1], hindex[-1]], '--', color='black')
ax.text(2*npapers-5, hindex[-1]+2, 'h-index')


# Citations per paper in time
fig_nr += 1
fig = plt.figure(fig_nr)
ax = fig.add_subplot(111)
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
ax.set_xlim(-1, 11)
ax.set_xlabel('Years after publication')
ax.set_ylabel('Citations')
ax.minorticks_on()
plt.tick_params(axis='both', which='both', width=0.4)

peak = []
age = []
colors = []

for paper in papers:
    cite = np.arange(paper.nCitations)
    citetimes = [time-paper.pubYear for time in paper.citationsByMonth]
    x = sorted(citetimes)

    if len(x) > 2:
        plt.plot(moving_average(x), cite[1:-1],
                 color=paper.pi, lw=1.5, alpha=0.8)


plt.show()

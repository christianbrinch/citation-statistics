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

__author__     = "Christian Brinch"
__copyright__  = "Copyright 2012-2016"
__credits__    = ["Christian Brinch"]
__license__    = "AFL 3.0"
__version__    = "1.0"
__maintainer__ = "Christian Brinch"
__email__      = "brinch@nbi.ku.dk"

import sys
from urllib2 import *
import re
import matplotlib.pyplot as plt
import numpy as np
import pickle
from datetime import date
from scipy.optimize import curve_fit
from scipy.misc import factorial
from matplotlib.ticker import FormatStrFormatter
reload(sys)
sys.setdefaultencoding('utf8')


def _monthtoyear(month):
    if ("jan" in month): return 0./12.
    if ("feb" in month): return 1./12.
    if ("mar" in month): return 2./12.
    if ("apr" in month): return 3./12.
    if ("may" in month): return 4./12.
    if ("jun" in month): return 5./12.
    if ("jul" in month): return 6./12.
    if ("aug" in month): return 7./12.
    if ("sep" in month): return 8./12.
    if ("oct" in month): return 9./12.
    if ("nov" in month): return 10./12.
    if ("dec" in month): return 11./12.
    return 0.


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


class aPaper(object):
    def __init__(self, identifier, doi, title, nCitations, selfCitations,
                 pubYear, citationsByMonth,pi):
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
webpage=urlopen("http://pub.orcid.org/v1.2/0000-0002-5074-7183/orcid-profile")
content=webpage.read()
webpage.close()
lines=content.split('\n')
for i in range(len(lines)):
    if "<title>" in lines[i] and "The evolving velocity field" not in lines[i]:
        title=(lines[i].split("<title>")[1].split("</title>")[0])[0:29].title()
        papers.append(aPaper("","",title,0,0,0,[],'blue'))
    if "<work-external-identifier-id>10" in lines[i]:
        papers[-1].doi=lines[i].split("<work-external-identifier-id>")[1].split\
            ("</work-external-identifier-id>")[0]
    if "<work-contributors>" in lines[i] and "Brinch" in lines[i+2]:
        papers[-1].pi = 'red'

npapers=len(papers)





if update:
    times=[]
    for paper in papers:
        print paper.doi
        url1='http://adswww.harvard.edu/cgi-bin/basic_connect?qsearch='
        url2='&version=1&data_type=BIBTEX'
        authors=[]
        try:
            webpage=urlopen(url1 + paper.doi.rstrip() + url2)
            content=webpage.read()
            webpage.close()
            lines=content.split('\n')
            for i in range(len(lines)):
                if "@ARTICLE" in lines[i]:
                    identifier = lines[i].split("@ARTICLE{")[1].split(",")[0]
                    paper.identifier = identifier
                if "year" in lines[i]:
                    if "month" in lines[i+1]:
                        month = lines[i+1].split()[2].rstrip(',')
                    else:
                        month = "jan"

                    pubYear = int(lines[i].split()[2].rstrip(',')) \
                              + _monthtoyear(month)
                    paper.pubYear = pubYear
                if "author" in lines[i]:
                    authors = lines[i].lstrip("author = ").rstrip("}")[1:].split("and")
                    authors = [author.lstrip().rstrip() for author in authors]

        except:
            print "Wrong DOI identifier"

        url1='http://adswww.harvard.edu/cgi-bin/nph-ref_query?bibcode='
        url2='&amp;refs=CITATIONS&amp;db_key=AST&data_type=BIBTEX'
        try:
            webpage=urlopen(url1 + identifier.replace("&", "%26") + url2)
            content=webpage.read()
            webpage.close()
            lines=content.split('\n')

            for i in range(len(lines)):
                if "Retrieved" in lines[i]:
                    paper.nCitations = int(lines[i].split()[1])
                if "author" in lines[i]:
                    names = lines[i].lstrip("author = ").rstrip("}")[1:].split("and")
                    names = [name.lstrip().rstrip() for name in names]
                    if names[0] in authors:
                        paper.nSelfCitations += 1
                if "year" in lines[i]:
                    if "month" in lines[i+1]:
                        month = lines[i+1].split()[2].rstrip(',')
                    else:
                        month = "jan"

                    time = int(lines[i].split()[2].rstrip(',')) \
                           + _monthtoyear(month)
                    paper.citationsByMonth.append(time)

            print "number of citation", paper.nCitations
        except:
            print "No citations"
            paper.nCitations = 0

    pickle.dump(papers, open("datadump.p","wb") )

else:
    papers=pickle.load( open("datadump.p","rb") )


papersSorted = sorted(papers, key=lambda x: x.pubYear, reverse=True)
papersSorted = sorted(papers, key=lambda x: x.nCitations, reverse=True)

total_citations = sum([paper.nCitations for paper in papers])
total_selfcite  = sum([paper.nSelfCitations for paper in papers])
print "Total number of citations: ", total_citations
print "Number of citations without self-citations", total_citations-total_selfcite



fig_nr=1

# Citations in time
fig = plt.figure(fig_nr)
ax=fig.add_subplot(111)
ax.set_xlim(2006,now+2)
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
ax.set_ylim(0,total_citations+0.2*total_citations)
ax.set_xlabel('Year')
ax.set_ylabel('Number of citations')
ax.minorticks_on()
cite = np.arange(total_citations)
citetimes = [time for paper in papers for time in paper.citationsByMonth]
ax.plot(sorted(citetimes),cite, lw=1.5)



# Citations per month
fig_nr += 1
fig = plt.figure(fig_nr)
ax=fig.add_subplot(111)
ax.set_xlim(2006,now+2)
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
#ax.set_ylim(0,total_citations+0.2*total_citations)
ax.set_xlabel('Year')
ax.set_ylabel('Citation speed per month')
ax.minorticks_on()
x=np.arange(2006,now+2./12,1./12)
y=np.zeros(len(x))
tmp=np.array(sorted(citetimes))
j=0
i=0
while j<len(y)-1:
    if tmp[i] <= x[j]:
        y[j]+=1
        i+=1
    else:
        j+=1
        y[j]=y[j-1]

dy = np.zeros(x.shape,np.float)
dy[0:-1] = np.diff(y)/np.diff(x)
dy[-1] = (y[-1] - y[-2])/(x[-1] - x[-2])
ax.plot(x[1:-1],moving_average(dy/12.), color='blue', lw=1.5)




# h-index in time
fig_nr += 1
fig = plt.figure(fig_nr)
ax=fig.add_subplot(111)
ax.set_xlim(2006,now+2)
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
ax.set_ylim(0,20)
ax.set_xlabel('Year')
ax.set_ylabel('h-index')
ax.minorticks_on()


nMonth = int((now-2007.0)*12)
hindex = []
h5index = []
for i in range(nMonth):
    year = 2007 + i%12 + (i - (i%12 * 12))/12.
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

    numberOfCitation=sorted(currentCitations,reverse=True)
    numberOfShortCitation=sorted(currentShortCitations,reverse=True)
    hindex.append(0)
    h5index.append(0)
    for i in range(npapers):
        if (i+1) <= numberOfCitation[i]:
            hindex[-1] += 1
        if (i+1) <= numberOfShortCitation[i]:
            h5index[-1] += 1

ax.plot(2007+np.arange(len(hindex))/12., hindex, color='blue', lw=1.5)
x=np.arange(len(hindex))/12. + 2007
ax.plot(x, x-2007, color='black', lw=1.5)
ax.plot(x, 2*(x-2007), color='black', lw=1.5)
ax.plot(2007+np.arange(len(h5index))/12., h5index, color='red', lw=1.5)

print "h-index:", hindex[-1]
print "h-index slope:", hindex[-1]/(now-2007)
print "h5-index:", h5index[-1]










# Citations per paper
fig_nr += 1
fig = plt.figure(fig_nr)
ax=fig.add_subplot(111)
ax.set_xlim(0,2*npapers+2)
ax.set_ylabel('Citations')
ax.minorticks_on()
plt.xticks(np.arange(0, 2*npapers+2, 2.0)+0.5)
ax.tick_params(axis='x', which='both',labelsize=8)
ax.set_xticklabels([paper.title for paper in papersSorted],rotation=45, \
                    rotation_mode="anchor", ha="right")
cites = map(int,[paper.nCitations for paper in papersSorted])
ax.bar(2*np.arange(npapers)+0.25, cites, color=[ i.pi for i in papersSorted ])
cites = map(int,[paper.nCitations-paper.nSelfCitations for paper in papersSorted])
ax.bar(2*np.arange(npapers)+0.9, cites, color=[ i.pi for i in papersSorted ], alpha=0.5)
ax.plot([0,2*npapers+0.25],[hindex[-1],hindex[-1]], '--', color='black')
ax.text(2*npapers-5,hindex[-1]+2, 'h-index')






# Citations per paper in time
fig_nr += 1
fig=plt.figure(fig_nr)
ax=fig.add_subplot(111)
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
ax.set_xlim(-1,10)
ax.set_xlabel('Years after publication')
ax.set_ylabel('Citations')
ax.minorticks_on()
plt.tick_params(axis='both', which='both', width=0.4)

peak=[]
age=[]
colors=[]

for paper in papers:
    cite = np.arange(paper.nCitations)
    citetimes = [time-paper.pubYear for time in paper.citationsByMonth]
    x=sorted(citetimes)


    if len(x) > 2:
        plt.plot(moving_average(x),cite[1:-1], color=paper.pi, lw=1.5, alpha=0.8)



plt.show()

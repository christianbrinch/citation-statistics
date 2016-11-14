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
reload(sys)
sys.setdefaultencoding('utf8')

def poisson(k, lamb):
    return (lamb**k/factorial(k)) * np.exp(-lamb)

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

class aPaper(object):
    def __init__(self, identifier, doi, title, nCitations, pubYear,
                 citationsByMonth):
        self.identifier = identifier
        self.doi = doi
        self.title = title
        self.nCitations = nCitations
        self.pubYear = pubYear
        self.citationsByMonth = citationsByMonth



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
        papers.append(aPaper("","",title,0,0,[]))
    if "<work-external-identifier-id>10" in lines[i]:
        papers[-1].doi=lines[i].split("<work-external-identifier-id>")[1].split(\
            "</work-external-identifier-id>")[0]

npapers=len(papers)





if update:
    times=[]
    for paper in papers:
        print paper.doi
        url1='http://esoads.eso.org/cgi-bin/basic_connect?qsearch='
        url2='&version=1&data_type=BIBTEX'
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
        except:
            print "Wrong DOI identifier"

        url1='http://esoads.eso.org/cgi-bin/nph-ref_query?bibcode='
        url2='&amp;refs=CITATIONS&amp;db_key=AST&data_type=BIBTEX'
        try:
            webpage=urlopen(url1 + identifier.replace("&", "%26") + url2)
            content=webpage.read()
            webpage.close()
            lines=content.split('\n')

            for i in range(len(lines)):
                if "Retrieved" in lines[i]:
                    paper.nCitations = int(lines[i].split()[1])
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



total_citations = sum([paper.nCitations for paper in papers])
print "Total number of citations: ", total_citations





# Citations in time
fig = plt.figure(1)
ax=fig.add_subplot(111)
ax.set_xlim(2005,now+2)
from matplotlib.ticker import FormatStrFormatter
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
ax.set_ylim(0,total_citations+0.2*total_citations)
ax.set_xlabel('Year')
ax.set_ylabel('Number of citations')
ax.minorticks_on()
plt.tick_params(axis='both', which='both', width=0.4)
#ax.set_yscale('log')
cite = np.arange(total_citations)
citetimes = [time for paper in papers for time in paper.citationsByMonth]
plt.plot(sorted(citetimes),cite)







# Citations per paper
fig = plt.figure(2)
ax=fig.add_subplot(111)
ax.set_xlim(0,npapers+2)
ax.set_ylim(0,150)
ax.set_ylabel('Citations')
ax.minorticks_on()
plt.xticks(np.arange(0, npapers+2, 1.0)+0.5)
plt.tick_params(axis='x', which='both',labelsize=8)
ax.set_xticklabels([paper.title for paper in papers],rotation=45, \
                    rotation_mode="anchor", ha="right")
cites = map(int,[paper.nCitations for paper in papers])
plt.bar(np.arange(npapers)+0.25, cites)








# h-index in time
fig = plt.figure(3)
ax=fig.add_subplot(111)
ax.set_xlim(2005,2018)
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
ax.set_ylim(0,20)
ax.set_xlabel('Year')
ax.set_ylabel('h-index')
ax.minorticks_on()
plt.tick_params(axis='both', which='both', width=0.4)

nMonth = int((round(now+0.5)-2007)*12)
hindex = []
for i in range(nMonth):
    year = 2007 + i%12 + (i - (i%12 * 12))/12.
    currentCitations = []
    for paper in papers:
        currentCitations.append(0)
        for citation in paper.citationsByMonth:
            if citation < year:
                currentCitations[-1] += 1

    numberOfCitation=sorted(currentCitations,reverse=True)
    hindex.append(0)
    for i in range(npapers):
        if (i+1) <= numberOfCitation[i]:
            hindex[-1] += 1

plt.plot(2007+np.arange(len(hindex))/12., hindex)
x=np.arange(len(hindex))/12. + 2007
plt.plot(x, x-2007)
plt.plot(x, 2*(x-2007))

print "h-index:", hindex[-1]
print "h-index slope:", hindex[-1]/(now-2007)








fig=plt.figure(4)
ax=fig.add_subplot(111)
ax.set_xlim(-1,15)
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
ax.set_ylim(0,1)
ax.set_xlabel('Years after publication')
ax.set_ylabel('Citations per year')
ax.minorticks_on()
plt.tick_params(axis='both', which='both', width=0.4)
    
for paper in papers:
  if paper.nCitations > 1:
      data=[ (i+1) - paper.pubYear for i in paper.citationsByMonth]
      try:
          entries, bin_edges, patches = plt.hist(data, \
                bins=list(range(0,int(now-int(paper.pubYear))+2)), \
                normed=True, alpha=0.0)
          bin_middles = 0.5*(bin_edges[1:] + bin_edges[:-1])
          parameters, cov_matrix = curve_fit(poisson, bin_middles, entries)
          x_plot = np.linspace(0,20,1000)
          plt.plot(x_plot, poisson(x_plot, *parameters),lw=2, label=paper.title)
      except:
          print paper.title+" doesn't work"


plt.legend(loc=1,prop={'size':8})
plt.show()

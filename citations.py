#!/usr/bin/env python
# encoding=utf8

import sys
from urllib2 import *
import re
import matplotlib.pyplot as plt
import numpy as np
import pickle
from datetime import date
reload(sys)
sys.setdefaultencoding('utf8')

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm


# Data manipulation:

def make_segments(x, y):
    '''
    Create list of line segments from x and y coordinates, in the correct format for LineCollection:
    an array of the form   numlines x (points per line) x 2 (x and y) array
    '''

    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    return segments


# Interface to LineCollection:

def colorline(x, y, z=None, cmap=plt.get_cmap('copper'), norm=plt.Normalize(0.0, 1.0), linewidth=3, alpha=1.0):
    '''
    Plot a colored line with coordinates x and y
    Optionally specify colors in the array z
    Optionally specify a colormap, a norm function and a line width
    '''

    # Default colors equally spaced on [0,1]:
    if z is None:
        z = np.linspace(0.0, 1.0, len(x))

    # Special case if a single number:
    if not hasattr(z, "__iter__"):  # to check for numerical input -- this is a hack
        z = np.array([z])

    z = np.asarray(z)

    segments = make_segments(x, y)
    lc = LineCollection(segments, array=z, cmap=cmap, norm=norm, linewidth=linewidth, alpha=alpha)

    ax = plt.gca()
    ax.add_collection(lc)

    return lc


def clear_frame(ax=None):
    # Taken from a post by Tony S Yu
    if ax is None:
        ax = plt.gca()
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    for spine in ax.spines.itervalues():
        spine.set_visible(False)

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
    def __init__(self, identifier, doi, title, nCitations, pubYear, citationsByMonth):
        self.identifier = identifier
        self.doi = doi
        self.title = title
        self.nCitations = nCitations
        self.pubYear = pubYear
        self.citationsByMonth = citationsByMonth



papers = []
update=0
if (len(sys.argv) > 1):
  if sys.argv[1]=='update':
    update=1

now = date.today().year+date.today().month/12.




# Get paper list from ORCID
webpage=urlopen("http://pub.orcid.org/v1.2/0000-0002-5074-7183/orcid-profile")
content=webpage.read()
webpage.close()
contentlines=content.split('\n')
for i in range(len(contentlines)):
    if "<title>" in contentlines[i] and "The evolving velocity field around protostars" not in contentlines[i]:
        title=(contentlines[i].split("<title>")[1].split("</title>")[0])[0:29].title()
        papers.append(aPaper("","",title,0,0,[]))
    if "<work-external-identifier-id>10" in contentlines[i]:
        papers[-1].doi=contentlines[i].split("<work-external-identifier-id>")[1].split("</work-external-identifier-id>")[0]

npapers=len(papers)





if update:
    times=[]
    for paper in papers:
        print paper.doi
        url1='http://esoads.eso.org/cgi-bin/basic_connect?qsearch='
        url2='&version=1&data_type=BIBTEX'
        try:
            webpage=urlopen(url1+paper.doi.rstrip()+url2)
            content=webpage.read()
            webpage.close()
            contentlines=content.split('\n')
            for i in range(len(contentlines)):
                if "@ARTICLE" in contentlines[i]:
                    identifier=contentlines[i].split("@ARTICLE{")[1].split(",")[0]
                    paper.identifier=identifier
                if "year" in contentlines[i]:
                    if "month" in contentlines[i+1]:
                        month=contentlines[i+1].split()[2].rstrip(',')
                    else:
                        month="jan"

                    pubYear=int(contentlines[i].split()[2].rstrip(',')) + _monthtoyear(month)
                    paper.pubYear = pubYear
        except:
            print "Wrong DOI identifier"

        url1='http://esoads.eso.org/cgi-bin/nph-ref_query?bibcode='
        url2='&amp;refs=CITATIONS&amp;db_key=AST&data_type=BIBTEX'
        try:
            webpage=urlopen(url1+identifier.replace("&", "%26")+url2)
            content=webpage.read()
            webpage.close()
            contentlines=content.split('\n')

            for i in range(len(contentlines)):
                if "Retrieved" in contentlines[i]:
                    paper.nCitations=int(contentlines[i].split()[1])

                if "year" in contentlines[i]:
                    if "month" in contentlines[i+1]:
                        month=contentlines[i+1].split()[2].rstrip(',')
                    else:
                        month="jan"

                    time=int(contentlines[i].split()[2].rstrip(',')) + _monthtoyear(month)
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
cite=np.arange(total_citations)
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
ax.set_xticklabels([paper.title for paper in papers],rotation=45, rotation_mode="anchor", ha="right")
cites=map(int,[paper.nCitations for paper in papers])
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
hindex=[]
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
        if (i+1)<=numberOfCitation[i]:
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
from scipy.optimize import curve_fit
from scipy.misc import factorial

def poisson(k, lamb):
    return (lamb**k/factorial(k)) * np.exp(-lamb)


for paper in papers:
  if paper.nCitations > 1:
      data=[ (i+1) - paper.pubYear for i in paper.citationsByMonth]
      try:
          entries, bin_edges, patches = plt.hist(data, bins=list(range(0,int(now-int(paper.pubYear))+2)), normed=True, alpha=0.0)
          bin_middles = 0.5*(bin_edges[1:] + bin_edges[:-1])
          parameters, cov_matrix = curve_fit(poisson, bin_middles, entries)
          x_plot = np.linspace(0,20,1000)
          plt.plot(x_plot, poisson(x_plot, *parameters), lw=2, label=paper.title)
          #color=(now-paper.pubYear)/9.
          #colorline(x_plot, poisson(x_plot, *parameters), color, cmap="coolwarm")
      except:
          print paper.title+" doesn't work"


plt.legend(loc=1,prop={'size':8})


plt.show()

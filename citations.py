#!/usr/bin/env python
import sys
from urllib2 import *
import re
import matplotlib.pyplot as plt
import numpy as np
import pickle

update=0
if (len(sys.argv) > 1):
  if sys.argv[1]=='update':
    update=1

ident=['Lupus','l1489_1','L1489_2','Richling','COdep','Reinout','Iras2','Lars',
       'herschel_1','herschel_2','DMtau','LIME','TWHya','Ewine','Salter','Ruud',
       'dustpol','Bisschop','Irs43-64', 'new', 'new','new','new','new']

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

url1='http://adsabs.harvard.edu/cgi-bin/nph-ref_query?bibcode='
#url1='http://esoads.eso.org/cgi-bin/nph-ref_query?bibcode='
url2='&amp;refs=CITATIONS&amp;db_key=AST&data_type=BIBTEX'

if update:
  data={'paper': [], 'citations': []}
  f=open('paperlist.txt', 'r')
  times=[]
  with open('paperlist.txt') as papers:
    for line in papers:
      print line.rstrip()
      webpage=urlopen(url1+line.rstrip()+url2)
      content=webpage.read()
      webpage.close()
      contentlines=content.split('\n')
      data['paper'].append(line.rstrip())

      for i in range(len(contentlines)):
        if "Retrieved" in contentlines[i]:
          data['citations'].append(contentlines[i].split()[1])

        if "year" in contentlines[i]:
          if "month" in contentlines[i+1]:
            month=contentlines[i+1].split()[2].rstrip(',')
          else:
            month="jan"

          time=int(contentlines[i].split()[2].rstrip(',')) + _monthtoyear(month)
          times.append(time)
      print data['citations'][-1]
    pickle.dump(data, open("datadump.p","wb") )
    pickle.dump(times, open("timedump.p","wb") )

else:
  data=pickle.load( open("datadump.p","rb") )
  times=pickle.load( open("timedump.p","rb") )


total_citations=0
for i in data['citations']:
  total_citations+=int(i)


print "Total number of citations: ", total_citations

fig = plt.figure(1)
ax=fig.add_subplot(111)
ax.set_xlim(2006,2017)
from matplotlib.ticker import FormatStrFormatter
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
ax.set_ylim(0,total_citations+0.2*total_citations)
ax.set_xlabel('Year')
ax.set_ylabel('Number of citations')
ax.minorticks_on()
#ax.set_yscale('log')
plt.tick_params(axis='both', which='both', width=0.4)
cite=np.arange(len(times))
plt.plot(sorted(times),cite)
#x=np.arange(100)/10. + 2007
#plt.plot(x, np.exp(x-2007))

fig = plt.figure(2)
ax=fig.add_subplot(111)
ax.set_xlim(0,30)
ax.set_ylim(0,150)
ax.set_xlabel('Papers')
ax.set_ylabel('Citations')
ax.minorticks_on()
plt.tick_params(axis='both', which='both', width=0.4)
cites=map(int,data['citations'])
plt.bar(np.arange(len(data['citations']))+0.5, cites)

fig = plt.figure(3)
ax=fig.add_subplot(111)
ax.set_xlim(2006,2017)
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
ax.set_ylim(0,20)
ax.set_xlabel('Year')
ax.set_ylabel('h-index')
ax.minorticks_on()
plt.tick_params(axis='both', which='both', width=0.4)

from collections import Counter
import operator
temp=np.zeros(len(data['citations']))
hindex=np.zeros(120)
n=0
for i in range(120):
  temp[:]=0.
  for k in range(len(data['citations'])):
    for j in range(cites[k]):
      if times[n+j] <= 2007.+i/12.:
        temp[k]+=1
    n+=j
  n=0
  freq=Counter(temp)

  sorttemp=sorted(temp,reverse=True)
  idx=0.
  for k in range(len(temp)):
    if sorttemp[k]>=(k+1):
      idx=k+1
    else:
      break

  hindex[i]=idx

print hindex

plt.plot(2007+np.arange(120)/12., hindex)
x=np.arange(120)/10. + 2007
plt.plot(x, x-2006)
plt.plot(x, 2*(x-2006)-1)

plt.plot(x, 16./11.*(x-2006)-1)
print "h-index slope:", 16./11.



fig=plt.figure(4)
ax=fig.add_subplot(111)
ax.set_xlim(0,8)
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
ax.set_ylim(0,40)
ax.set_xlabel('Years after publication')
ax.set_ylabel('citations per year')
ax.minorticks_on()
plt.tick_params(axis='both', which='both', width=0.4)

from datetime import date
import math
l=0
ghist=np.zeros(10)
norm=np.zeros(10)
for i in range(len(data['citations'])):
  arr=times[l:l+cites[i]]
  for k in range(len(arr)):
    arr[k]=math.floor(arr[k])

  pubyear=int(data['paper'][i][0:4])
  years=int(date.today().year-pubyear)+1
  hist=np.histogram(times[l:l+cites[i]], bins=list(range(pubyear,int(date.today().year)+2)))

  for j in range(len(hist[0])):
    ghist[j]=ghist[j]+hist[0][j]
    norm[j]=norm[j]+1


  plt.plot(np.arange(len(hist[0])),hist[0])#, label=ident[i])
  l=l+cites[i]

#plt.legend(loc=1,prop={'size':10})
plt.plot(np.arange(10),ghist/norm, lw=3, color='black')


plt.show()

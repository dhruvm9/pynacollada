# -*- coding: utf-8 -*-
"""
Created on Wed Dec 15 19:11:53 2021

@author: Adrien Peyrache

This script shows how to use pynapple to compute sleep reactivation, step by step.
See pynacollada_replayExample for a real case example

"""

import pynapple as nap
import pandas as pd
import numpy as np
import seaborn as sns; sns.set_theme()
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from scipy import stats


recDuration = 2000.; #recording duration in secs
sessionEpoch = nap.IntervalSet(start = 0, end = recDuration, time_units = 's')
wakeEpoch = nap.IntervalSet(start = 0, end = 999, time_units = 's')
sleepEp = nap.IntervalSet(start = 1000, end = recDuration, time_units = 's')

# Let's imagine we have done some sleep scoring identifying NREM sleep episodes
nremEp = nap.IntervalSet(start = [1100, 1500], end = [1200, 1700], time_units = 's')

# We just create fake spike trains
spikes =  {}

for s in range(50):
    random_rate = 10 * np.random.rand(1)
    random_times = np.random.uniform(0, recDuration, int(np.rint(recDuration * random_rate)))
    random_times = np.sort(random_times)
    my_spike = nap.Ts(random_times, time_units = 's')
    spikes[s] = my_spike
    
#Now we define pynapple's TsGroup (perfectly suited for spike trains)    
spikeGrp = nap.TsGroup(data = spikes, time_support = sessionEpoch)

#We can immediately bin the spike trains (here in 100ms bins)
binnedSpk = spikeGrp.count(0.1)

binWake = binnedSpk.restrict(wakeEpoch).values
Cwake = np.corrcoef(np.transpose(binWake))

# Let's plot the correlation matrix, excluding the diagonal elements
mask = np.zeros_like(Cwake)
mask[np.diag_indices_from(mask)] = True
ax = sns.heatmap(Cwake, mask=mask)

### Let's start with PCA-based reactivation method
pca = PCA()
zSpkWake = StandardScaler().fit_transform(binWake)
pca.fit(zSpkWake)

# Plot the eigenvalues. Here it's all random, should be distributed around 1
sns.lineplot(data=pca.explained_variance_)

#And the first three eigenvectors (the PCs)
plt.figure()
ax = sns.heatmap(pca.components_[:3,:])
ax.set_xlabel("Neurons", fontsize = 15)
ax.set_ylabel("PCs", fontsize = 15)

# Conpute the z-scored binned spike trains durint sleep
binSleep = binnedSpk.restrict(sleepEp).values
zSpkSleep = StandardScaler().fit_transform(binSleep)

# We project onto the first three PCs
reactPCA = np.zeros((zSpkSleep.shape[0],3))
    
for n in range(3):
    pc = pca.components_[n,:]
    proj = np.dot(zSpkSleep,pc)
    #yes, some maths tricks here
    diagTerm = zSpkSleep*np.tile(pc,(zSpkSleep.shape[0],1))
    tmp = np.square(proj) - np.sum(np.square(diagTerm),axis=1)
    reactPCA[:,n] = np.transpose(tmp)

import sys
sys.exit()

# Here, it is time to transform the data back into tsdFrame.
reactPCA = nap.TsdFrame(t=binnedSpk.restrict(sleepEp).times(), d=reactPCA, time_support=sleepEp, columns=['PC1','PC2','PC3'])


# Plot reactivation strength during a subset of sleepPre
exampleEp =  nap.IntervalSet(start = [1100,1300], end = [1200,1350], time_units = 's')
plt.figure()
ax = sns.lineplot(data=reactPCA.restrict(exampleEp).as_units('s'))
ax.set_ylabel("Reactivation Strength", fontsize = 15)

# Plot reactivation strength during NREM. We intersect the two intervalSet
exampleEp =  sleepEp.intersect(nremEp)
plt.figure()
ax = sns.lineplot(data=reactPCA.restrict(exampleEp).as_units('s'))
ax.set_ylabel("Reactivation Strength", fontsize = 15)



from typing import *
from dataclasses import *
import seaborn as sns
from pbutils import p
import os
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import io
from subprocess import run
import shlex
import numpy as np
from sklearn.decomposition import PCA

import matplotlib
matplotlib.use('template')

sns.set_theme(style='darkgrid', palette='deep')


def sns_hook(s: Any):
    if (savefig := getattr(s, 'savefig', None)):
        buf = io.BytesIO()
        savefig(buf, format='png')
        bs = buf.getvalue()
        run(shlex.split('kitty +kitten icat --transfer-mode=stream --stdin=yes --align left'),
            input=bs)
        return True
    else:
        return False

p.hooks.append(sns_hook)

def main():
    for zmuv in [True, False]:
        # sns.get_dataset_names() | p
        t = sns.load_dataset('penguins')
        t = t.dropna()
        # t = sns.load_dataset('iris')
        p | sns.pairplot(t, hue='species', corner=True)
        break
        cols = [
            c
            for c in t.columns
            if 'width' in c or 'length' in c
        ]
        if zmuv:
            for c in cols:
                t[c] = (t[c] - t[c].mean()) / t[c].std()
        pca = PCA(n_components=2)
        xy = pca.fit_transform(t[cols])
        t[['x', 'y']] = xy
        g = sns.relplot(t, x='x', y='y', hue='species')
        g.set(title=f'{zmuv=}')
        p | g

main()

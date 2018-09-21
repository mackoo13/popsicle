import matplotlib.pyplot as plt
import matplotlib.colors
import numpy as np
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsRegressor


def graph(clf, x2, y, labels=None, xlim=(None, None), ylim=(None, None)):
    if labels is None:
        labels = []

    if x2.shape[1] != 2:
        pca = PCA(n_components=2)
        x2 = pca.fit_transform(x2)
        clf = KNeighborsRegressor(n_neighbors=6, weights='distance')
        clf.fit(x2, y) 

    norm = matplotlib.colors.LogNorm(vmin=y.min(), vmax=y.max())
    fig, ax = plt.subplots()
    
    plt.title('Prediction after dimensionality reduction')
    plt.xlabel('Dimension 1')
    plt.ylabel('Dimension 2')
    
    x0 = x2[:, 0]
    x1 = x2[:, 1]

    # grid
    xmin = min(x0)
    xmax = max(x0)
    xstep = (xmax-xmin)/99.9

    ymin = min(x1)
    ymax = max(x1)
    ystep = (ymax-ymin)/99.9

    xrange = np.arange(xmin, xmax, xstep)
    yrange = np.arange(ymin, ymax, ystep)
    xx, yy = np.meshgrid(xrange, yrange)

    xrange_grid = np.arange(xmin-xstep/2, xmax+xstep/2, xstep)
    yrange_grid = np.arange(ymin-ystep/2, ymax+ystep/2, ystep)
    xx_grid, yy_grid = np.meshgrid(xrange_grid, yrange_grid)

    ypred = clf.predict(list(zip(xx.ravel(), yy.ravel()))).flatten()
    ypred = [q if q > 0 else y.min() for q in ypred]
    ypred = np.array(ypred).reshape(len(yrange_grid)-1, len(xrange_grid)-1)
    
    pcm = ax.pcolor(xx_grid, yy_grid, ypred, norm=norm)

    cbar = fig.colorbar(pcm, ax=ax, extend='max')
    cbar.set_label('Execution time (log scale)', rotation=270, va='top')

    # scatter
    ax.scatter(x0, x1, c=y, norm=norm, edgecolors='black', s=40)
    ax.set_xlim(xmin if xlim[0] is None else xlim[0], xmax if xlim[1] is None else xlim[1])
    ax.set_ylim(ymin if ylim[0] is None else ylim[0], ymax if ylim[1] is None else ylim[1])
    
    # labels
    for i, txt in enumerate(labels):
        ax.annotate(txt, (x0[i], x1[i]))

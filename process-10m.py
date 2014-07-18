# Benchmark based on Greg Redas's previous work:
# http://www.gregreda.com/2013/10/26/using-pandas-on-the-movielens-dataset/
# The original MovieLens datasets are over here:
# http://www.grouplens.org/datasets/movielens

from time import time
import os.path
import numpy as np
import bcolz
import pandas as pd

bcolz.print_versions()

dset = 'ml-10m'
ftags = os.path.join(dset, 'tags.dat')
fdata = os.path.join(dset, 'ratings.dat.gz')
fitem = os.path.join(dset, 'movies.dat')

bcolz.defaults.cparams['cname'] = 'blosclz'
bcolz.defaults.cparams['clevel'] = 1
# bcolz.defaults.eval_vm = "numexpr"
# bcolz.blosc_set_nthreads(1)
# bcolz.numexpr.set_num_threads(1)

t0 = time()
# pass in column names for each CSV
t_cols = ['user_id', 'movie_id', 'tag', 'unix_timestamp']
tags = pd.read_csv(ftags, sep=';', names=t_cols)
#print("Info for tags:", tags.info())

r_cols = ['user_id', 'movie_id', 'rating', 'unix_timestamp']
ratings = pd.read_csv(fdata, sep=';', names=r_cols, compression='gzip')

m_cols = ['movie_id', 'title', 'genres']
movies = pd.read_csv(fitem, sep=';', names=m_cols,
                     dtype={'title': "S100", 'genres': "S100"})
print("Time for parsing the data: %.2f" % (time()-t0,)) 

t0 = time()
# create one merged DataFrame
movie_ratings = pd.merge(movies, ratings)
# You probably need more than 8 GB in RAM for the next merge
#lens = pd.merge(movie_ratings, tags, on='user_id')
lens = movie_ratings
print("Time for dataframe merges: %.2f" % (time()-t0,)) 
#print("Info for movie_ratings:", movie_ratings.info())
#print("Info for lens:", lens.info())

#most_rated = lens.groupby('title').size().order(ascending=False)[:25]
#print(most_rated)

t0 = time()
result = lens[lens['title'] == 'Tom and Huck (1995)']
print("time (and length) for simple query with pandas: %.2f (%d)" %
      (time()-t0, len(result)))
#print repr(result)

t0 = time()
result = lens[(lens['title'] == 'Tom and Huck (1995)') & (lens['rating'] == 5)]['user_id']
print("time (and length) for complex query with pandas: %.2f (%d)" %
      (time()-t0, len(result)))
#print repr(result)

t0 = time()
zlens = bcolz.ctable.fromdataframe(lens)
print("time (and compress ratio) for ctable conversion: %.2f (%.1fx)" % 
      (time()-t0, zlens.nbytes / float(zlens.cbytes)))
#print repr(zlens)

t0 = time()
result = zlens["title == 'Tom and Huck (1995)'"]
print("time (and length) for simple query with bcolz: %.2f (%d)" %
      (time()-t0, len(result)))
#print repr(result)

t0 = time()
#result = zlens["(title == 'Tom and Huck (1995)') & (rating == 5)"]['user_id']
result = [r.user_id for r in zlens.where(
    "(title == 'Tom and Huck (1995)') & (rating == 5)", outcols=['user_id'])]
print("time (and length) for complex query with bcolz: %.2f (%d)" %
      (time()-t0, len(result)))
#print(repr(result))

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

dset = 'ml-100k'
fuser = os.path.join(dset, 'u.user')
fdata = os.path.join(dset, 'u.data')
fitem = os.path.join(dset, 'u.item')

bcolz.defaults.cparams['cname'] = 'lz4'
bcolz.defaults.cparams['clevel'] = 1

# pass in column names for each CSV
u_cols = ['user_id', 'age', 'sex', 'occupation', 'zip_code']
users = pd.read_csv(fuser, sep='|', names=u_cols)

r_cols = ['user_id', 'movie_id', 'rating', 'unix_timestamp']
ratings = pd.read_csv(fdata, sep='\t', names=r_cols)

# the movies file contains columns indicating the movie's genres
# let's only load the first five columns of the file with usecols
m_cols = ['movie_id', 'title', 'release_date', 'video_release_date', 'imdb_url']
movies = pd.read_csv(fitem, sep='|', names=m_cols, usecols=range(5),
                     dtype={'release_date': "S100", 'imdb_url': "S200"})

t0 = time()
# create one merged DataFrame
movie_ratings = pd.merge(movies, ratings)
lens = pd.merge(movie_ratings, users)
print("Time for merging the datasets: %.2f" % (time()-t0,)) 
#print("Info for merged dataframe:", lens.info())

#most_rated = lens.groupby('title').size().order(ascending=False)[:25]
#print(most_rated)

t0 = time()
#result = lens[lens['title'] == 'Tom and Huck (1995)']
result = lens.query("title == 'Tom and Huck (1995)'")
print("time (and length) for simple query with pandas: %.2f (%d)" %
      (time()-t0, len(result)))
#print repr(result)

t0 = time()
#result = lens[(lens['title'] == 'Tom and Huck (1995)') & (lens['sex'] == 'M')]
# result = lens[(lens['title'] == 'Tom and Huck (1995)') & ((lens['age'] > 18) & (lens['age'] < 32))]
#result = lens[(lens['title'] == 'Tom and Huck (1995)') & (lens['rating'] == 5)]['user_id']
result = lens.query("(title == 'Tom and Huck (1995)') & (rating == 5)")['user_id']
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
#result = zlens["(title == 'Tom and Huck (1995)') & (sex == 'M')"]
#result = zlens["(title == 'Tom and Huck (1995)') & ((age > 18) & (age < 32))"]
#result = zlens["(age == 25) & (occupation == 8)"]
#result = zlens["(title == 'Tom and Huck (1995)') & (rating == 5)"]['user_id']
result = [r.user_id for r in zlens.where(
    "(title == 'Tom and Huck (1995)') & (rating == 5)", outcols=['user_id'])]
print("time (and length) for complex query with bcolz: %.2f (%d)" %
      (time()-t0, len(result)))
#print repr(result)

# Author: Olivier Grisel <olivier.grisel@ensta.org>
#         Lars Buitinck <L.J.Buitinck@uva.nl>
# License: BSD 3 clause

from __future__ import print_function
from time import time

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
from sklearn.datasets import fetch_20newsgroups

n_samples = 200000
n_features = 1000
n_topics = 20
n_top_words = 10

# Load the 20 newsgroups dataset and vectorize it. We use a few heuristics
# to filter out useless terms early on: the posts are stripped of headers,
# footers and quoted replies, and common English words, words occurring in
# only one document or in at least 95% of the documents are removed.

t0 = time()
print("Loading dataset and extracting TF-IDF features...")
dataset = fetch_20newsgroups(shuffle=True, random_state=1,
                             remove=('headers', 'footers', 'quotes'))

#=====================
from ml.classifier.learn_data import LearnDataLoader

class Dataset:
  def __init__(self):
        ldata = LearnDataLoader()
        # load learn data
        cats_hier_file = 'ml/learn/categories_youdo.com_2015.06.30.json'
        learn_file = 'ml/learn/downloaders/youdo.com/scan_100pages_sorted_uniqed.txt'
        if not ldata.load(cats_hier_file, learn_file, balance_category_min=20, log=True):
            print >> sys.stderr, "Error: " + ldata.get_err_msg()
            sys.exit(1)

        cats_docs = ldata.get_learn_data(fields_to_get=['title'])
        self.data = [x[1] for x in cats_docs]
        self.target = [x[0] for x in cats_docs]
        self.target_names = self.target

dataset = Dataset()
#=====================


vectorizer = TfidfVectorizer(max_df=0.95, min_df=2, max_features=n_features,
                             stop_words='english')
tfidf = vectorizer.fit_transform(dataset.data[:n_samples])
print("done in %0.3fs." % (time() - t0))

# Fit the NMF model
print("Fitting the NMF model with n_samples=%d and n_features=%d..."
      % (n_samples, n_features))
nmf = NMF(n_components=n_topics, random_state=1).fit(tfidf)
print("done in %0.3fs." % (time() - t0))

feature_names = vectorizer.get_feature_names()

for topic_idx, topic in enumerate(nmf.components_):
    print("Topic #%d:" % topic_idx)
    print(" ".join([feature_names[i]
                    for i in topic.argsort()[:-n_top_words - 1:-1]]))
    print()

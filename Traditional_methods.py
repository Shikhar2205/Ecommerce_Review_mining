# -*- coding: utf-8 -*-
"""DM_traditional.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1GHP5OHetWLM8RsAUAlEt01BWyk6aTHaD
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression as LR
from sklearn.naive_bayes import BernoulliNB
from sklearn.svm import SVC
from sklearn import metrics
from datetime import datetime
import nltk
nltk.download('stopwords')
from nltk.tokenize import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from sklearn.ensemble import RandomForestClassifier
from bs4 import BeautifulSoup             
import re

!pip install optuna

from google.colab import drive
drive.mount('/content/drive')

train = pd.read_csv('/content/drive/MyDrive/train.csv')
dev = pd.read_csv('/content/drive/MyDrive/dev.csv')
X_train = train.drop('label', axis = 1)
y_train = train['label']
X_dev = dev.drop('label', axis = 1)
y_dev = dev['label']

def review_to_words( raw_review ):
    # Function to convert a raw review to a string of words
    # The input is a single string (a raw movie review), and 
    # the output is a single string (a preprocessed movie review)
    #
    # 1. Remove HTML
    review_text = BeautifulSoup(raw_review).get_text() 
    #
    # 2. Remove non-letters        
    letters_only = re.sub("[^a-zA-Z]", " ", review_text) 
    #
    # 3. Convert to lower case, split into individual words
    words = letters_only.lower().split()                             
    #
    # 4. In Python, searching a set is much faster than searching
    #   a list, so convert the stop words to a set
    stops = set(stopwords.words("english"))                  
    # 
    # 5. Remove stop words
    meaningful_words = [w for w in words if not w in stops]   
    #
    # 6. Join the words back into one string separated by space, 
    # and return the result.
    return( " ".join( meaningful_words ))   




# Get the number of reviews based on the dataframe column size
num_reviews = train["review"].size
num_reviews1 = dev["review"].size


# Initialize an empty list to hold the clean reviews
train_corpus = []

for i in range( 0, num_reviews ):
    # If the index is evenly divisible by 1000, print a message
    if( (i+1)%1000 == 0 ):
        print ("Review %d of %d\n" % ( i+1, num_reviews )  )                                                                  
    train_corpus.append( review_to_words( train["review"][i] ))


dev_corpus = []
for i in range( 0, num_reviews1 ):
    # If the index is evenly divisible by 1000, print a message
    if( (i+1)%1000 == 0 ):
        print ("Review %d of %d\n" % ( i+1, num_reviews1 )  )                                                                  
    dev_corpus.append( review_to_words( train["review"][i] ))




tv = TfidfVectorizer(binary = False, ngram_range = (1,2), stop_words = 'english', max_features=5000)
cv = CountVectorizer(binary = True, ngram_range = (1,2), stop_words = 'english', max_features=5000)

x_cv = cv.fit_transform(train_corpus)
x_tv = tv.fit_transform(train_corpus)

import gensim.downloader
model = gensim.downloader.load("glove-wiki-gigaword-300")

import numpy as np  # Make sure that numpy is imported

def makeFeatureVec(words, model, num_features):
    # Function to average all of the word vectors in a given
    # paragraph
    #
    # Pre-initialize an empty numpy array (for speed)
    featureVec = np.zeros((num_features,),dtype="float32")
    #
    nwords = 0
    # 
    # Index2word is a list that contains the names of the words in 
    # the model's vocabulary. Convert it to a set, for speed 
    index2word_set = set(model.index2word)
    #
    # Loop over each word in the review and, if it is in the model's
    # vocaublary, add its feature vector to the total
    for word in words:
        if word in index2word_set: 
            nwords = nwords + 1.
            featureVec = np.add(featureVec,model[word])
    # 
    # Divide the result by the number of words to get the average
    featureVec = np.divide(featureVec,nwords)
    return featureVec


def getAvgFeatureVecs(reviews, model, num_features):
    # Given a set of reviews (each one a list of words), calculate 
    # the average feature vector for each one and return a 2D numpy array 
    # 
    # Initialize a counter
    counter = 0
    # 
    # Preallocate a 2D numpy array, for speed
    reviewFeatureVecs = np.zeros((len(reviews),num_features),dtype="float32")
    # 
    # Loop through the reviews
    for review in reviews:
       #
       # Print a status message every 1000th review
       if (counter%1000 == 0):
           print ("Review %d of %d" % (counter, len(reviews)))
       reviewFeatureVecs[counter] = makeFeatureVec(review, model,num_features)
       counter = counter + 1
    return reviewFeatureVecs


trainDataVecs = getAvgFeatureVecs( train_corpus, model, num_features=300 )

testDataVecs = getAvgFeatureVecs( dev_corpus, model, num_features=300 )
# Fit a random forest to the training data, using 100 trees

pickle.dump(model, open('/content/drive/MyDrive/trainDataVecs.sav', 'wb'))
pickle.dump(model, open('/content/drive/MyDrive/testDataVecs.sav', 'wb'))

"""Logistic Regression"""

import optuna
from sklearn import model_selection
from sklearn import linear_model

def objective(trial):
    
    # Step 2. Setup values for the hyperparameters:
    s=trial.suggest_categorical("ss", ['lbfgs','liblinear','saga'])
    logreg_c = trial.suggest_float("logreg_c", 1e-10, 1e10, log=True)
    classifier_obj = linear_model.LogisticRegression(C=logreg_c,class_weight='balanced',solver=s)

    # Step 3: Scoring method:
    score = model_selection.cross_val_score(classifier_obj, x_tv, y_train, n_jobs=-1, cv=3)
    accuracy = score.mean()
    return accuracy

# Step 4: Running it
study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=100)

study.best_params

start = datetime.now()

lr_tv = linear_model.LogisticRegression(solver='saga',C=5.16757139447607,class_weight='balanced').fit(x_tv,y_train).predict(tv.transform(dev_corpus))


end = datetime.now()
print(end-start)

from sklearn.metrics import precision_recall_fscore_support
precision_recall_fscore_support(y_dev, lr_tv, average='weighted')





truncatedSVD=TruncatedSVD(300)
X_truncated = truncatedSVD.fit_transform(x_tv)

start = datetime.now()
bnb_tv = BernoulliNB().fit(X_truncated,y_train).predict_proba(tv.transform(dev_corpus))
lr_tv = LR(solver = 'liblinear').fit(X_truncated,y_train).predict_proba(tv.transform(dev_corpus))
svm_tv = SVC(kernel = 'linear', probability=True).fit(X_truncated, y_train).predict_proba(tv.transform(dev_corpus))
forest = RandomForestClassifier(n_estimators = 100) 
forest_tv = forest.fit( X_truncated, y_train).predict(tv.transform(dev_corpus))
end = datetime.now()
print(end-start)










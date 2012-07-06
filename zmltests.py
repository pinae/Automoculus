#!/usr/bin/python
# encoding: utf-8
from __future__ import division, print_function, unicode_literals

import numpy as np
from sklearn.decomposition import PCA
from sklearn import preprocessing
import sklearn
from sklearn import tree
from sklearn.ensemble.forest import RandomForestClassifier, ExtraTreesClassifier
from sklearn.grid_search import GridSearchCV
from sklearn import linear_model, svm
from sklearn import cross_validation
from sklearn.linear_model.perceptron import Perceptron
from sklearn.metrics import precision_score
from sklearn.neighbors.classification import KNeighborsClassifier
from Beatscript import getContextAndBeatListFromFile, coalesceBeats, isSplittingPoint
from ConvertData import getFeatureLine
import Features

from OptimizeML import getDataMatrix
from Config import TRAIN_FILES, SHOT_NAMES, DETAIL

SVM_PARAMETERS = [{'C': [1, 10, 100, 1000], 'gamma': [0.001, 0.0001], 'kernel': ['rbf']},
 {'C': [1, 10, 100, 1000], 'kernel': ['linear']}]

LINEAR_REGRESSION_PARAMETERS = [{'C': [0.0001, 0.001, 0.1, 1, 10, 100, 10000]}]

def load_data():
    return getDataMatrix(TRAIN_FILES)



def main():
    X, y = load_data()
    X = np.array(X, dtype=np.float64) # convert to float
    X_scaled = preprocessing.scale(X) # normalize
    clf = linear_model.LogisticRegression()
    # crossvalidation
    scores = cross_validation.cross_val_score(clf, X_scaled, y, cv=10)
    print(scores.mean(), scores())
    # grid search Logistic regression
    logReg = linear_model.LogisticRegression()
    clf = GridSearchCV(logReg, LINEAR_REGRESSION_PARAMETERS, cv=10)
    clf.fit(X_scaled, y)
    # grid search SVM
    s = svm.SVC()
    clf = GridSearchCV(s, SVM_PARAMETERS, cv=10)
    clf.fit(X_scaled, y)

def qewlGraph():
    train_errors = []
    test_errors = []
    X, y = load_data()
    X = np.array(X, dtype=np.float64) # convert to float
    X_scaled = preprocessing.scale(X) # normalize
    skf = cross_validation.StratifiedKFold(y,10)
    train1, val1 = skf.__iter__().next()
    X_val = X_scaled[val1]
    y_val = y[val1]
    for i in range(100, 1438, 100):
        X_s = X_scaled[train1[:i]]
        y_s = y[train1[:i]]
        clf = svm.SVC()
        clf.fit(X_s, y_s)
        e_train = precision_score(y_s, clf.predict(X_s))
        train_errors.append(e_train)
        e_test = precision_score(y_val, clf.predict(X_val))
        test_errors.append(e_test)
        print(e_train, e_test)
    return train_errors, test_errors


def onlineFeatureLineCreator(filename, use_classified_shot = False, use_history = True):
    # load context and complete beatlist from file
    context, beatList = getContextAndBeatListFromFile(filename)
    Features.initializeContextVars(context)
    blockList = coalesceBeats(beatList)
    context["BygoneBlocks"] = []
    for block in blockList:
        shot_true = block[-1].shot
        # get current feature line and true shot class
        featureLine = getFeatureLine(context, block, True, -1)
        features = np.array(featureLine[:-1], dtype=np.float64)
        shot_classified = yield features, shot_true
        # update block and lastShotId
        if use_classified_shot:
            for beat in block:
                beat.shot = shot_classified
        if use_history:
            context["BygoneBlocks"].append(block)




def test(f, use_classified_shot, use_history = True):
    oflc = onlineFeatureLineCreator(f, use_classified_shot, use_history)
    l, c = oflc.next()
    predictions = []
    true_classes = [c]
    try:
        while True:
            p, = clf.predict(scaler.transform(l))
            predictions.append(p)
            l, c = oflc.send(p)
            true_classes.append(c)
    except StopIteration:
        true_classes = np.array(true_classes)
        predictions = np.array(predictions)
        #score = np.sum(true_classes == predictions) / len(predictions)
        #score = np.sum(np.abs(true_classes - predictions)**2) / len(predictions)
        #score = np.sum(np.abs(true_classes - predictions)) / len(predictions)
        score = np.sum(np.abs(true_classes - predictions) > 1) / len(predictions)
        return score


"""
    data = [getDataMatrix([f]) for f in TRAIN_FILES]
    X, y = zip(*data)
    X = np.vstack(X)
    y = np.hstack(y)
    scaler = preprocessing.Scaler()
    X_scaled = scaler.fit_transform(X) # normalize
    pca = PCA(n_components=2)
    X_red = pca.fit_transform(X_scaled)




    train_scores = []
    scores = []
    lengths = []
    for i, f in enumerate(data):
            X, y = zip(*(data[:i] + data[i+1:]))
            X = np.vstack(X)
            y = np.hstack(y)
            X_scaled = scaler.transform(X) # normalize
            #X_scaled = pca.transform(X_scaled)
            #clf = svm.SVC(C=10, gamma=0.0001)
            #clf = svm.SVC()
            clf = linear_model.LogisticRegression(C=0.04)
            #clf = tree.DecisionTreeClassifier()
            #clf = KNeighborsClassifier(19)
            #clf = Perceptron()
            #clf = RandomForestClassifier(n_estimators=10)
            #clf = ExtraTreesClassifier(n_estimators=100)
            clf.fit(X_scaled, y)
            X_test, y_test = data[i]
            X_test = scaler.transform(X_test)
            #X_test = pca.transform(X_test)
            #score = np.sum(np.abs(clf.predict(X_test) - y_test)) / len(y_test)
            score = np.sum(clf.predict(X_test) == y_test) / len(y_test)
            scores.append(score)
            #train_score = np.sum(np.abs(clf.predict(X_scaled) - y)) / len(y)
            train_score = np.sum(clf.predict(X_scaled) == y) / len(y)
            train_scores.append(train_score)
            lengths.append(len(y))
            print("{:.4}\t\t{:.4}".format(train_score, score))

    print( np.sum(np.array(scores) * np.array(lengths))/np.sum(lengths))
    print(np.mean(scores))
"""



if __name__ == "__main__":
    results = []
    X, y = getDataMatrix(TRAIN_FILES)
    scaler = preprocessing.Scaler()
    scaler.fit(X)
    
    for i, f in enumerate(TRAIN_FILES):
        X, y = getDataMatrix(TRAIN_FILES[:i] + TRAIN_FILES[i+1:])
        X_scaled = scaler.transform(X)
        clf = linear_model.LogisticRegression(C=0.04)
        clf.fit(X_scaled, y)

        s1 = test(f, use_classified_shot=True)
        s2 = test(f, use_classified_shot=False)
        #s3 = test(f, use_classified_shot=False, use_history=False)
        print(("{:.2%}\t\t"*2).format(s1, s2))
        results.append((s1, s2))
    r = np.array(results)
    print("Average:")
    print(("{:.2%}\t\t"*2).format(*r.mean(0)))





    #main()

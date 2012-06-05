#!/bin/sh
echo "###################### Featurizer ######################"
python2 Featurizer_unittests.py
echo "\n\n\n###################### PositionProcess ######################"
python2 PositionProcess_unittests.py
echo "\n\n\n###################### Classifier ######################"
python3 testClassifier.py


#!/bin/bash

echo "" > features.csv

for f in "Berg der Versuchung - Schwere Stelle.csv" "Double Indemnity - Eingang.csv" "Double Indemnity - Identifikation.csv" "Double Indemnity - Leiche.csv" "Double Indemnity - Telefonat.csv" "Ivanhoe - Ende.csv" "Ivanhoe - Endkampf.csv" "Ivanhoe - Gefangennahme.csv" "Ivanhoe - Taverne.csv" "Ivanhoe - Turnier.csv" "The Count of Monte Christo - Messerkampf.csv" "The Count of Monte Christo - Verschwörer.csv" "The Maltese Falcon - Beginn.csv" "The Treasure of the Sierra Madre - Ausbeuter.csv"; do
  echo "python ConvertData.py "$f" tmp"
  python ConvertData.py "$f" tmp
  cat tmp >> features.csv
done

rm tmp

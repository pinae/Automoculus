Automoculus
===========

Camera positioning system

Installation instructions
=========================

Install sklearn:
on Ubuntu type "sudo apt-get intall python-sklearn"

Load this repository.

Run tests
=========

Open one of the example .blend files in blenderfiles/

In the upper left corner press "run script". This registers the Automoculus script in Blender, so you're able to 
execute it from the menu.

Maybe you want to delete all keyframes on the camera so the script creates completely new ones. Existing positions 
are used for further optimization so it's not irrelevant if keyframes exist.

Open the menu (space-bar) and type "Automoculus - Cameraman"

Cross-validation
================

To run a cross-validation on the data type "python X-Validation.py" while you're in the Automoculus directory.

Real world usage
================

If you want to use Automoculus in your own blendfiles, copy the script part from one of the example files in 
blenderfiles/ into a new script in your own blendfile. Change the filename of the beatscript to your Script.
Don't forget to run this script so the "Automoculus - Cameraman" is registered. Make sure for all persons, 
objects and places in the beatscript, that there is an object in your blendfile with the exact same name. Make
sure you have a activated camera of the scene. This camera will be positioned. Move your camera to a roughly 
correct starting position because the camera will try to stay on that side of the line for the rest of the scene.
If your scene is set up in that way, run "Automoculus - Cameraman".

It is a good idea to start blender from a console because the output fron the script is printed there. If you 
encounter problems check that output and compare it with the examples.

If you don't like the result you can change the set of training-data in Config.py. The result will be influenced 
by the data in the training-set so you can tweak your output by erasing data from the set which is definitely not 
similar to the result you desire.
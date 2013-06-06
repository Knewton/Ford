#!/usr/bin/env bash

cd /tmp
sudo rm -rf CoffeeScriptFord
git clone git://github.com/doloopwhile/Python-CoffeeScript.git CoffeeScriptFord
cd CoffeeScriptFord
sudo python setup.py install
mkdir -p ~/.ford
cp coffeescript/coffee-script.js ~/.ford/coffee-script.js


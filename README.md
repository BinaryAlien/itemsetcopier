# itemsetcopier

## Overview

### Description 
Simple Python API that enables you to translate online builds from popular League of Legends builds websites (such as MOBAfire, Mobalytics, OP.GG, Champion.gg, ...) into item sets

### How does it work
There is an algorithm for each LoL builds website which (in most of the cases) fetches the HTML source code of the corresponding build's webpage and translates it to it's JSON representation, compatible with the game. It can then be imported simply by copy/pasting

### Web app
Try it out yourself [here](https://www.binaryalien.net/itemsetcopier/) !

## Prerequisites

- beautifulsoup4
- requests

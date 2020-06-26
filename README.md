# itemsetcopier

## Overview

### Description
Simple API written in Python 3 that lets you translate online builds from popular League of Legends builds websites (such as MOBAfire, Mobalytics, OP.GG, Champion.gg, ...) into clipboard imports. Thus you will be able to quickly copy online item builds into the game without any effort.

### How does it work ?
Each website that is currently supported by itemsetcopier has a class inherited from `Translator` which has one function : `generate_item_set` that does all the underlying translation and error-handling work. When called, if there was no error during the process, the function will return a dict with `code` which is an int with a value of `CODE_OK` and `item_set` which is a string containing the generated item set's data that you can use as a clipboard import. In case of an error, a specific int in `code` will be returned as well as an error message contained in `error`.

### Web App
I have implemented itemsetcopier into a web application so that anyone can copy builds easily. You can try it out yourself [here](https://www.binaryalien.net/itemsetcopier/) !

### HTTP API
There is an HTTP API for itemsetcopier available on [my website](https://www.binaryalien.net/itemsetcopier/api/) !

## Prerequisites

- beautifulsoup4
- requests

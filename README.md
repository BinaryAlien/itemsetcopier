# itemsetcopier

## Description
Simple Python API that lets you translate online builds from popular League of Legends builds websites (such as MOBAfire, Mobalytics, OP.GG, ...) into clipboard imports. Thus you will be able to quickly copy online item builds into the game without any effort.

## Prerequisites

- beautifulsoup4
- requests

## How does it work ?
Each website that is currently supported by itemsetcopier has a class inherited from `Translator` which has one function : `generate_item_set` that does all the underlying translation and error-handling work. When called, this function will always return a `dict` with an `int` called `code`. If it's value is `CODE_OK`, it means the translation was successful and you will be able to import the generated item set(s) by copying the contents of the `item_set` field. Otherwise a specific return `code` as well as an `error` field will be provided to help you figure out what went wrong.

## Web Application
I have implemented itemsetcopier into a web application so that anyone can easily copy builds. Feel free to try it out yourself and use it [here](https://www.binaryalien.net/itemsetcopier/) !

## Web API
There is also a [web API](https://www.binaryalien.net/itemsetcopier/api/) for itemsetcopier in case you do not use Python for your project but still wish to use itemsetcopier.

## Help
If you need help, have any suggestions or questions, feel free to join [my Discord Server](https://discord.gg/Yefe3aa). I will be glad to help you !

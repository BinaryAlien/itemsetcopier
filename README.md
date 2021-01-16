# itemsetcopier

## Description
Simple Python library that lets you translate online builds from popular League of Legends builds websites (such as MOBAfire, Mobalytics, OP.GG, ...) into clipboard imports.

## Prerequisites
- aiohttp
- beautifulsoup4

## How does it work ?
Each website that is currently supported by itemsetcopier has a **translation function** that does all the underlying translation and error-handling work. When called, the function will return a `dict` containing a field of the enum `ReturnCode` called `code`. If this field's value is `CODE_OK`, it means the translation was successful and you will be able to import the generated item set(s) by copying the contents of the `item_set` field. In case of an error, the `dict` will contain an `error` field which is a message describing the problem that occured.

There is also a wrapper function called `translate` which takes as its first parameter one of the `Translator` enum's fields and as keyword arguments the specific parameters to provide to the underlying translator function.

## Web Application
I have implemented itemsetcopier into a web application. Feel free to try it out yourself and use it [here](https://www.binaryalien.net/itemsetcopier/) !

## Support
If you need help, have any suggestions or questions, feel free to join [my Discord Server](https://discord.gg/Yefe3aa).

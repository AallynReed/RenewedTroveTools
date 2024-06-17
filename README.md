# Renewed Trove Tools
[![GitHub Release](https://img.shields.io/github/release/AallynReed/RenewedTroveTools.svg?style=flat)]()
[![Github All Releases](https://img.shields.io/github/downloads/AallynReed/RenewedTroveTools/total.svg?style=flat)]()
[![NPM License](https://img.shields.io/npm/l/all-contributors.svg?style=flat)](https://github.com/AallynReed/RenewedTroveTools/blob/master/LICENSE)
<br>
[![GitHub last commit](https://img.shields.io/github/last-commit/AallynReed/RenewedTroveTools.svg?style=flat)]()
[![GitHub commit activity the past week, 4 weeks](https://img.shields.io/github/commit-activity/y/AallynReed/RenewedTroveTools.svg?style=flat)]()
<br>
[![GitHub stars](https://img.shields.io/github/stars/AallynReed/RenewedTroveTools.svg?style=social&label=Stars&style=plastic)]()
[![GitHub watchers](https://img.shields.io/github/watchers/AallynReed/RenewedTroveTools.svg?style=social&label=Watch&style=plastic)]()
[![GitHub forks](https://img.shields.io/github/forks/AallynReed/RenewedTroveTools.svg?style=social&label=Fork&style=plastic)]()
## Introduction
This project aims at remaking the tools present in Trove Tools by Dazo using modern interface and adding new features and tools for public use.

## Features:
- Mod Manager
- Modder Tools
- Gear Builds
- Gem Builds Calculator
- Star Chart Simulator
- Mastery Calculator
- Magic Find Calculator
- Gem Set Simulator
- Gem System Simulator
- Game File Extractor
- #### More to come...

## Windows (Tested in x64 only)
Create a virtual environment using the following command:
```bash
python -m venv venv
```
It must be called `venv` or the virtual environment must be renamed in `run.bat` file.

Then run the `run.bat` file. It should install dependencies and run the application.

## Linux
Simply run the `setup.sh` file.

Create a simlink by doing :
`sudo ln -s /usr/local/lib/libmpv.so /usr/local/lib/libmpv.so.1`
- The simlink is a temporary fix dues to a flet issue (https://github.com/flet-dev/flet/issues/2637)

To run the app, use : `venv/bin/python app.py`
<br>
<br>
Note: This still requires you to manually set up your mods folder

### Thanks
PotatoPVP - Linux Support
<br>
AnglesD - Chinese translations


# Projects
Projects are a custom feature I created for Renewed Trove Tools, it aims at making it easier for new and old modders to mod Trove.

To start a project you must download the desktop version of the app, this is a requirement due to needing to access files in your game directory and projects folder (once you create it).

## Create my first mod project
#### Trove is required to be installed on your machine
Up top you'll see your installations, you will have to select your desired installation before proceeding or it may cause issues later on, that will have you wonder what is happening.

To set your project up you have to first select a folder for your projects to be managed in.
To do so, navigate to `Modder Tools` tab and select the settings icon, there you are going to find a setting `Project Folder` navigate to the folder or create it in the file picker.
Once the folder is selected you can now go to the `Projects` tab, there you'll be prompted to create your first project.

Click `New Project` and fill in the details of your project.
- Required fields
	- Project Name
	- Authors (separated by comma)
- Optional fields
	- Description
	- Type
	- Class (For costume mods)

![image](https://github.com/AallynReed/RenewedTroveTools/assets/47339373/50829e66-b228-4809-859b-40d85b74b687)


Once you've filled in these details you can click `Create`
Now you have created your mod project, however you still need to create your first version, to do that you have to click `New Version` and name the version. This is a "protected" field which means that it must follow some logic and shouldn't be used with names that don't follow some sort of order, the idea is to ensure that versions follow a general pattern such as `1.0` or `1.1`.
You will name your version here `1.0` for example here and you'll notice there's a switch to `Copy previous version` this is not important if it is the first version in the project, you may ignore it for now.
![image](https://github.com/AallynReed/RenewedTroveTools/assets/47339373/bc58f0ac-4091-4073-9da0-4600f63c0bd5)


Hit `Create` and now you'll be presented with the whole interface.
Here you can change Authors , Description, Type, Class (Costume mods) and even put changes right on each version you make.

About the switch `Copy previous version` you saw when creating the version, that serves to copy all files from ie version 1.0 over to version 1.1, in case you want to keep previous files and simply change them.

### Features
My app has a lot of "secret" features, most are to help a new modder, some are to ease experienced modder's tasks.

#### Whitelisted folder usage
My app will create the basic folders for the game, such as `blueprints`, `audio` and more...it will only pick up files from these when compiling so you can have folders that as long as they don't match game's they won't be "seen" by the application, ie if you create a folder called `my useful files` this folder will be ignored completely.
![image](https://github.com/AallynReed/RenewedTroveTools/assets/47339373/2f3ab861-3de4-490e-a832-fd01ba377f91)

#### Automatic File alocation
Sometimes you don't know where a file goes, sometimes you don't wanna have the trouble to find out where it is from, in my app if you put in example a file called `cool_mount.blueprint` inside `audio` folder, when you refresh the list of files, the application will look through your selected installation archives and automatically find where that file belongs, this ensures you don't make mistakes, so if the `cool_mount.blueprint` belongs to `blueprints/2024/cool_mount` it will automatically be moved there.
This can also be triggered manually through the button `Fix file paths`

#### Preview warnings
The application will automatically warn you if the resolution and size of your image are a problem, not only resolution may cause issues displaying in game, but the size of the preview may render the TMod impossible to upload to Steam due to size, you'll be warned of this.

![image](https://github.com/AallynReed/RenewedTroveTools/assets/47339373/2def1985-b33f-4c99-bf5d-1615f657364c)

#### Included Configuration files (Interface (UI) mods)
With the app you'll also be able to include configuration files like you do with previews, using the same formatting that previews, this way when using my application, the configuration files if included will be used instead of generic generation of the file.
Simply click `Open version folder` and place your `.cfg` file in there

#### Built-in single file extractor
Sometimes you don't like to extract the game over and over, this is not needed with my app, I've built a feature that reads archives directly from the game installation selected, this means you can search right way through the button called `Extract from archives`, you click it, you'll have a search bar, you can search for file name or even supports for some things the real name of the thing, say in example `Ganda` it should also return related files, from here you'll have a download button, which if you click the files will be extracted and put into your project directly from your game, ensure your installation is up to date to get the latest files, avoiding the need of full game extractions
It may take a few seconds to load the files into memory as it takes some time to scan archives.

![image](https://github.com/AallynReed/RenewedTroveTools/assets/47339373/6994f08c-4a22-4bb5-8bf5-18b06c8f5ccc)

#### Test automation
Overrides are a neat way of avoiding the premature compile of Trove Mods `.tmod` files, with my application you'll have 2 buttons that will automate this process. The first button is `Test overrides` this will move all your files from your project folder into the correct override locations, allowing you to test on the fly by opening the game, once you are happy with the state of your files, you are also able to automatically delete these override files using `Clear overrides` it will not delete **All** overrides, it will delete only the override files that match the ones inside your project folder, in order to avoid deleting important files that may be from other projects.

#### Homebrewed TMod builder
Unlike other solutions you may find such as `TroveTools.NET` by Dazo, I made my own compiler of `TMod` files, this allows me to skip Trove's limitations when compiling, since old methods use the Trove.exe they are locked out by what devs allowed at the time, not only that their internal compiler has a bug with some edge cases. With my app the compilation is not limited and you may compile as expected.

#### List of applications
Sometimes as a new modder you may not know where to get the applications needed to mod certain aspects of the game, inside the app there will be a button called `Get modding software` it will display a list of apps for each type of modding you can do and show information about what the app is and if it is paid or not as well as shortcuts to their pages.
![image](https://github.com/AallynReed/RenewedTroveTools/assets/47339373/34de399c-7b70-4cca-8b0f-aee2b1574eb1)

If you have feature suggestions, let me know, I'll look into trying to fit them in if I see they are doable without much problem or interference to the app or people's computers

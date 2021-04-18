# videoflo
A series of Python scripts to help automate the video production workflow in DaVinci Resolve.

## Installation
- A modern version of MacOS
- Tested on Python 3.8
- [mac-tag](https://github.com/andrewp-as-is/mac-tag.py)

## Configuring Your Settings
Configuration options can be specified in the `settings.ini` files. A description of individual configuration sections and settings are below.
* `[main]`
  * **api** The absolute path to the DaVinci Resolve scripting example directory. If you are unsure for your system, go to Help > Documentation > Developer. This only is availabe for DaVinci Resolve Studio.
  * **root_dir** The absolute path to the root directory where you keep all of your video project files. If you have multiple channels, you can organize them in their own section below.
* `[video]`
  * **FrameRate** The frame rate that you want to export with
  * **ResolutionWidth** The width of your export video
  * **ResolutionHeight** The height of your export video
* `[one or more channels]` eg. `[tony-teaches-tech]`
  * **name** The proper name for your channel
  * **path** The subdirectory under root_dir where your channel projects live
  * **timeline** The path to an optional timeline file (.drt) that you'ld like to start with for each video on this channel

## Using videoflo
There are 4 executable scripts in videoflo that allow you to automate various aspects of video production. The following is an overview of how those scripts fit into the video production workflow. While videoflo was designed specifically for tutorial-style videos with screen recordings that are destined for YouTube, the concepts here can be modified for other types of videos.

### 1. Create the Structure for a New Video
Use `new-vid.py` to create the basic directory structure to house your video files, assets, thumbnails, etc. The `--channel` argument needs to match up with the `[channel]` section in your `settings.ini' file.

```
python new-vid.py my-new-video --channel tony-teaches-tech
```

This will create 2 subdirectories:
1. `camera` Put your camera's video files here
2. `screen` Put your screen recordings here

This will also create 2 empty text files:
1. `yt.txt` Put the title, description, and tags for you YouTube video in here
2. `notes.txt` You can use this as a place to put an outline for your video or other relevant notes.

### 2. Shoot Your Video
Film your video and put your media files into the appropriate directories for your project.

### 3. Create a DaVinci Resolve Project
Use `davinci.py` to create a DaVinci Resolve project. This will import all media files into the Media Pool as well as an optional timeline file for the channel as specified in `settings.ini`. This will also set your render settings according to `settings.ini`. You can optionally use the `-c` or `--channel` flag here to specify the channel associated with the video, but the script will attempt to figure this out, so this isn't necessary.

```
python davinci.py my-new-video
```

This script will configure the Render Settings on the Deliver tab and specify the Filename as the name of your project and Location as the root of your project.

### 4. Edit and Render the Video
Edit the video as you normally would.

When no more edits need to happen, export your DaVinci Resolve project to the root of your project directory by going to File > Export Project.

If you have multiple video project that you are editing sequentially, you can render all projects (overnight for example) after your finished editing them all and adding them to the Render Queue. You can achieve this on the Deliver page in the Renger Queue box by clicking the three dots and then **Show All Projects**.

When finished, the publishable video file will be rendered to the root of your project directory.

### 5. Create a Thumbnail
Create a thumbnail for your video and put it in the root of your project directory. This should be a PNG file.

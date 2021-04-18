# videoflo
A series of Python scripts to help automate the YouTube video production workflow in DaVinci Resolve.

## Installation
- A modern version of macOS (tested on BigSur)
- A modern version of Python (tested with v3.8)
- DaVinci Resolve 17 Studio or higher
- [mac-tag](https://github.com/andrewp-as-is/mac-tag.py) which can be installed via pip

### macOS Tags
A fundamental part of videoflo is the built-in tagging feature that macOS offers. This feature allows us to keep track where each project is in the video workflow.

As a one-time setup, open a Finder window, go to Finder > Preferences, and add the folowing tags. The color doesn't matter too much, but make sure you have the exact text for each tag.

<img width="489" alt="macos-tags" src="https://user-images.githubusercontent.com/6558850/115155129-5aad1180-a033-11eb-93eb-108a21fc6942.png">

## Configuring Your Settings
Configuration options can be specified in the `settings.ini` files. A description of configuration sections and settings are below, and an example can be found [here](settings.ini).
* `[main]`
  * **api** The absolute path to the DaVinci Resolve scripting example directory. If you are unsure for your system, go to Help > Documentation > Developer. This only is availabe for DaVinci Resolve Studio. eg. /Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Examples/
  * **root_dir** The absolute path to the root directory where you keep all of your video project files. If you have multiple channels, you can organize them in their own section below. eg. /Volumes/vid/
* `[video]`
  * **FrameRate** The frame rate that you want to export with eg. 24
  * **ResolutionWidth** The width of your export video eg. 3840
  * **ResolutionHeight** The height of your export video eg. 2160
* `[channel]` eg. `[ttt]`
  * **name** The proper name for your channel eg. Tony Teaches Tech
  * **path** The subdirectory under root_dir where your channel projects live eg. tony-teaches-tech
  * **timeline** The path to an optional timeline file (.drt) that you'ld like to start with for each video on this channel eg. /Users/tonyflorida/Movies/tony-teaches-tech/Timeline1.drt

**_NOTE:_** There can be multiple `[channel]` sections above. Do not call this section _channel_, but rather a few characters that represent your channel like _ttt_ for the channel Tony Teaches Tech. What you choose here will ultimately be what you specify on the command line to distinguish this channel from your other channels. You need to have at least one `[channel]` section, and you need to make sure that the **path** exists under the **root_dir**.

## Using videoflo
There are 6 executable scripts in videoflo that allow you to automate various aspects of video production from idea to publishing. The following is an overview of how those scripts fit into the video production workflow. While videoflo was designed specifically for tutorial-style videos with screen recordings that are destined for YouTube, the concepts here can be modified for other types of videos.

<img width="910" alt="Screen Shot 2021-04-18 at 11 00 33 AM" src="https://user-images.githubusercontent.com/6558850/115155548-63064c00-a035-11eb-8100-73ab25173ed0.png">

### 1. Create the Structure for a New Video
Use `new-vid.py` to create the basic directory structure to house your video files, assets, thumbnails, etc. The `--channel` or `-c` argument needs to match up with the `[channel]` section in your `settings.ini' file.

```
python new-vid.py davinci-resolve-scripting -c ttt
```

Based on the configuration setting examples above, this will create a directory for your video project under /Volumes/vid/tony-teaches-tech/ called davinci-resolve-scripting. This directory will be tagged with a **Script** tag.

In this directory, 2 subdirectories will be created:
1. `camera` Put your camera's video files here
2. `screen` Put your screen recordings here

This will also create 2 empty text files in this directory:
1. `yt.txt` Put the title, description, and tags for you YouTube video in here
2. `notes.txt` You can use this as a place to put an outline for your video or other relevant notes.

### 2. Shoot Your Video
At this point, it's best practice to do some keyword research for your video topic. The keyword phrase for this example is 'DaVinci Resolve scripting'.

In the `yt.txt` file, put a title, description, and comma-separated tags for your video. There is no special format for this file, so feel free to customize for your needs.

```
How to Do Scripting in DaVinci Resolve with Python

Learn how to use Python to create scripts that tap into the DaVinci
Resolve API and allow you to automate some of the video production workflow.

davinci resolve scripting,
davinci resolve python scripting,
davinci resolve python api,
python davinci resolve,
davinci resolve python,
davinci resolve python scripting,
davinci resolve 16 python,
```

Now that you know exactly what your video is going to be about, do the necessary research for it. You can make a simple outline or write a script in `notes.txt`. If you need more flexibility than a plain text file, feel free to link in here the Google Doc where you put this information.

When you're ready to film, manually change the tag of this video project from **Script** to **Film** to stay organized across multiple projects. 

Finally, film your video and put your media files into the appropriate directories for your project.  Change the tag of the video project from **Film** to **Edit**.

### 3. Create a DaVinci Resolve Project
Use `davinci.py` to create a DaVinci Resolve project. This will import all media files into the Media Pool as well as an optional timeline file for the channel as specified in `settings.ini`. Your timeline might contain an intro or outro that you use across all videos on your channel. Starting in DaVinci Resolve 17, you can export a timeline by going to File > Export > Timeline.

This script will also set your render settings according to `settings.ini`.

You can optionally use the `-c` or `--channel` flag here to specify the channel associated with the video, but the script will attempt to figure this out, so this isn't necessary.

It's very important that you have DaVinci Resolve open before executing the `davinci.py` script or else it will fail.

```
python davinci.py davinci-resolve-scripting
```

### 4. Edit the Video
Edit the video as you normally would.

When no more edits need to happen, execute the `finish-edit.py` script while you still have the project open in DaVinci Resolve.

```
python finish-edit.py davinci-resolve-scripting
```

This will export the DaVinci Resolve project as a .drp file to the root of your project directory. This will also change the tag of the video project from **Edit** to **Render**.

### 5. Render ###

If you have multiple video project that you are editing sequentially, you can render all projects (overnight for example) after your finished editing them all. You can do this with the `render.py` script which will find all video projects that are tagged with **Render** for a particular channel, and sequentially render them.

The render settings specified in the `[Video]` section will be used here.

Please make sure DaVinci Resolve is open, or else the script will fail.

```
python render.py -c ttt
```

Each rendered video will be saved to the root of the project directory. After each video is rendered, the script will change the tag for the project directory from **Render** to **Upload**.

If you would like your video file to be named something else, this is a good time to change the name of the .mov file. It's understood that YouTube uses the filename of your video file as an indicator of what the video is about, so it's important for SEO purposes to name it accurately and not video1_final.mov.

### 6. Create a Thumbnail
Create a thumbnail for your video and put it in the root of your project directory. I like to use [Canva](http://tonyflo.com/canva). This should be a PNG file.

It's also understood that YouTube uses the filename of your thumbnail file as an indicator of what the video is about, so it's important for SEO purposes to name it accurately an not thumbnail.png.

### 7. Scan Project Directories

Use the `check-vids.py` command to scan the project directories that are tagged at **Upload** to make sure they each have a .drp (DaVinci Resolve Project) and .png (thumbnail) file in the root.

```
python3 check-vids.py -c ttt
```

This script will report any missing assets that should exist before uploading to YouTube or archiving.

### 8. Upload to YouTube
Use the `upload.py` script to copy the .mov files from the root of the project directories that are tagged as **Upload** for a particular channel into an 'uploadme' directory. These directories will then tagged with **Backup** indicating they are ready to be archived.

```
python3 upload.py -c ttt
```

This is valuable when you have batched multiple videos and would like to upload them all to YouTube at the same time. Rather than opening each directory and manually uploading each video video to YouTube, you can highlight up to 15 videos at a time and upload them all at once to YouTube.

After the video files have been uploaded to YouTube, you can safely delete the 'uploadme' directory.

### 9. Fill Out Metadata
Finally you can use the information you put into the `yt.txt` file to copy and paste your video's title, description, and tags. You can also use the thumbnail that you created to associate it with the video.


## Future Improvements
- Incorporate [Trello Python API](https://github.com/sarumont/py-trello) into workflow
- Incorporate the [YouTube API](https://developers.google.com/youtube/v3/guides/uploading_a_video) to upload videos and fill out metadata
- Allow subdirectories and files be configured through `settings.ini`
- Allow user to control verbosity of console output
- Add cross-platform support for Windows (mac_tag is acOS only)

<p align="center"><img width="320" alt="videoflo logo" src="https://user-images.githubusercontent.com/6558850/115158541-81734400-a043-11eb-8097-a7ae42325ef0.png"></p>

# videoflo
A series of Python scripts to help automate the YouTube video production workflow in DaVinci Resolve.

By leveraging the Trello API and the YouTube API, videoflo not only will eliminate many mundane aspects of video production, but also keep your projects organized throughout the entire process.

## Installation

### Requirements
- A modern version of Python (tested with v3.8)
- DaVinci Resolve 17 Studio or higher

### Installation
```
git clone https://github.com/tonyflo/videoflo.git
```

### Configuration
Open the [settings.ini](settings.ini) file and provide the full path to where you keep your video projects. Here's an example.
```
[main]
root_dir = /Volumes/vid/channels/
```

If you have multiple YouTube channels, it is recommended to create subdirectories for each channel. For me, I have 3 channels, so the following directories exist on my system.
* `/Volumes/vid/channels/tony-teaches-tech/`
* `/Volumes/vid/channels/tony-florida/`
* `/Volumes/vid/channels/thrifty-tony/`

If you will have screen recordings, please specify the path where your screen recordings are saved. Notice how the `screen_recordings` settings below uses an asterisk as a wildcard character to match any .mov files with a filename that starts with "Screen Recording".

```
[main]
...
screen_recordings = /Users/tonyflorida/Desktop/Screen Recording*.mov
```

For each one of your channels, add a section in your [settings.ini](settings.ini) file. You will need at least one section, but can have as many sections as you have channels. Pick a short, memorable name for your section name as you will use this name to distinguish your channel on the command line. In the snippet below, the section for [Tony Teaches Tech](https://www.youtube.com/channel/UCWPJwoVXJhv0-ucr3pUs1dA) and I named my section `[ttt]`.
```
[ttt]
name = Tony Teaches Tech
path = tony-teaches-tech
timeline = /Volumes/vid/assets/tony-teaches-tech/Timeline1.drt
framerate = 24
width = 3840
height = 2160
```

A description of each configuration option follows.
* `name` (required) The proper name of your YouTube channel
* `path` (required) The subdirectory under `root_dir` where your video projects will exist
* `timeline` (optional) The full path to a DaVinci Resolve timeline file that will act as a template for this channel's videos. Your timeline might contain an intro or outro that you use across all videos on your channel. Starting in DaVinci Resolve 17, you can export a timeline by going to File > Export > Timeline.
* `framerate` (required) The framerate that you export your videos
* `width` (required) The width that you export your videos
* `height` (required) The height that you export your videos

### Trello
To track where each video project is in the video production workflow, videoflo integrates with the project management software [Trello](https://trello.com/tonyflorida/recommend), so you'll need a free account if you don't have one.

In Trello, create a board for your YouTube channel with the following lists:
1. Script
2. Film
3. Edit
4. Render
5. Upload
6. Scheduled

_*NOTE*_: Please do not manually move cards between lists on your Trello boards... videoflo will manage card movement for you.

### MacOS Tags
If you are using a Mac computer, videoflo will tag your video project directories according to their status in the production workflow.

For Mac users only as a one-time setup, open a Finder window, go to Finder > Preferences, and add the following tags. The colors don't matter too much, but make sure you have the exact text for each tag.

<p align="center"><img width="489" alt="macos-tags" src="https://user-images.githubusercontent.com/6558850/115155129-5aad1180-a033-11eb-93eb-108a21fc6942.png"></p>

## Using videoflo
There are 7 Python scripts in videoflo that allow you to automate various aspects of video production from idea to publishing.
1. `new-video.py`
2. `ready-to-film.py`
3. `done-filming.py`
4. `edit.py`
5. `finish-edit.py`
6. `render.py`
7. `upload.py`

The following is an overview of how those scripts fit into the video production workflow.

### 1. Create the Directory Structure for Your New Video Idea
At the inception of an idea for a video, use `new-vid.py` to create the basic directory structure to house your future video files, assets, thumbnails, etc. The `--channel` or `-c` argument needs to match up with the channel section in your [settings.ini](settings.ini) file.

```
python new-video.py davinci-resolve-scripting -c ttt
```

The first time you do this, you will need to authorize videoflo to access your Trello account. Click on allow and copy the token into your terminal window.

Additionally, the first time you interact with each of your channels, you'll be asked to select the Trello board associated with your channel.

<p align="center"><img width="489" alt="macos-tags" src="https://user-images.githubusercontent.com/6558850/116331767-4b416d00-a785-11eb-878a-984872aa13c7.png"></p>

Based on the configuration setting example above, this will create the following directory for your video project `/Volumes/vid/channels/tony-teaches-tech/davinci-resolve-scripting`. If using Mac, this directory will be tagged with a **Script** tag.

In this directory, a `camera` subdirectory will be created. This is where you will eventually copy your camera's video file for this project.

This will also create an empty `notes.txt` file in this directory. You can use this as a place to put an outline for your video or other relevant notes.

Additionally, a new card will be added to the Script list in Trello.

### 2. Research and Plan
With an idea in your head, it's best practice to do some keyword research for your video topic. This will not only help you determine the title and description for your video, but also point you in the right direction for general research on the topic.

In Trello, put the title and description of your YouTube video as the title and description of the new card. Additionally, put the tags for your keyword research in the tags checklist on the card. If you don't have all of this information yet, that's okay. You can add this information anytime before uploading; however, it's highly recommended that you put some serious thought into this as early as possible.

<p align="center"><img width="489" alt="macos-tags" src="https://user-images.githubusercontent.com/6558850/116171607-f0910e00-a6bd-11eb-97ea-ae265bce0b36.png"></p>

Now that you know exactly what your video is going to be about, do the necessary research for it.

You can make a simple outline or write a script in `notes.txt`. If you need more flexibility than a plain text file, feel free to link a Google Doc to your Trello card.

After you have written a script or outline, use `ready-to-film.py` to update the state of the video.
```
python ready-to-film.py davinci-resolve-scripting -c ttt
```

The Trello card for this video will be moved to the **Film** board indicating that the video is ready to be filmed. If using Mac, this directory will be tagged with a **Film** tag.

### 3. Shoot the Video
Set aside some time and plan to film multiple videos in the same day. This not only is more efficient, but also allows you to take full advantage of the batching capability of videoflo.

After filming each video, use `done-filming.py` to update the state of the video.
```
python done-filming.py davinci-resolve-scripting -c ttt
```

If you specified a location for screen recordings in [settings.ini](settings.ini), this script will move these to a `screen` folder in the root of your project directory.

The Trello card for this video will be moved to the **Edit** board indicating that the video is ready to be edited. If using Mac, this directory will be tagged with a **Edit** tag.

### 4. Edit the Video
Use `edit.py` to create a DaVinci Resolve project. This will import all media files from this project's directory into the Media Pool.

_*Note*_: You'll need to manually copy your camera's video files from your SD card into the `camera` subdirectory for each video project before executing this script.

_*ANOTHER NOTE:*_ It's very important that you have DaVinci Resolve open before executing the `edit.py` script or else it will fail.

```
python edit.py davinci-resolve-scripting -c ttt
```

This script will also import an optional timeline file for the channel that you specified in [settings.ini](settings.ini).

### 5. Finish the Edit
When you're satisfied with the edit, use `finish-edit.py` to export the DaVinci Resolve project as a .drp file to the root of your project directory.

```
python finish-edit.py
```

Make sure you execute this script when you still have the project open in DaVinci Resolve.

The Trello card for this video will be moved to the **Render** board indicating the the video is ready to be rendered. If using Mac, this directory will be tagged with a **Render** tag.

### 6. Render ###

If you have multiple video project that you are working on sequentially, you can render all projects (overnight for example) after your finished editing them all. You can do this with the `render.py` script which will find all video projects that are in the Trello **Render** list for a particular channel and render them one after the other.

The render settings specified for the channel in [settings.ini](settings.ini) be used here.

Please make sure DaVinci Resolve is open, or else the script will fail.

```
python render.py -c ttt
```

Each rendered video will be saved to the root of the project directory.


After each video is rendered, the Trello card for that video will be moved to the **Upload** board indicating the the video is ready to be uploaded to YouTube. If using Mac, this directory will be tagged with a **Upload** tag.

_*NOTE*_: If you would like your video file to be named something else, this is a good time to change the name of the .mov file. It's understood that YouTube uses the filename of your video file as an additional indicator to determine what your video is about, so it's important for SEO purposes to name it accurately and not video1_final.mov for example.

### 7. Upload to YouTube
Use the `upload.py` script to upload all rendered videos for a particular channel to YouTube.

```
python upload.py -c ttt
```

Before uploading, this script will make sure that you have the following metadata for each video:
* **Thumbnail**: PNG file in the root of your project directory. I like to use [Canva](http://tonyflo.com/canva) to make my thumbnails.
* **Title**: The name of the Trello card will be used as the title for the video.
* **Description**: The description of the Trello card will be used as the description for the video.
* **Tags**: The tags in the 'tags' checklist on the Trello card will be used as the tags for the video.
* **Scheduled Date**: The 'Due date' on the Trello card will be used as the date and time that the video will be scheduled to be published on YouTube.

_*NOTE*_: The first time you upload a video to a channel with videoflo, you will need to authorize videoflo to access your YouTube account.

After each video is uploaded, the Trello card for that video will be moved to the **Scheduled** board indicating the the video is scheduled to be published. Attachments will be added to the card that link to the video in YouTube studio and the video itself.

If using Mac, this directory will be tagged with a **Backup** tag indicating that the project directory for this video can be safely backed up.

## Future Improvements
- Allow user to control verbosity of console output
- Automatically open DaVinci Resolve if it needs to be open
- Explain how to export a timeline

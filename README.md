# Git Visual Peace

This is a tool made for Windows (for now) specifically for pngs (for now) to help solve conflicts involving images.

## How to use

1. Open your terminal on the target repository folder

1. `git-vp my-branch:Path/to/A/File`

1. The program will temporarily create a PSD (Photoshop) file containing:
- A layer with the target branch image
- A layer with the current branch image
- A transparent layer with the diff between the two other layers

 It will also open the file using your default program for .psd files.

1. Modify the .psd file until the conflict is solved, save the file and close the image editor.

1. Go back to the terminal and press Enter to the `Are you done? [Y/n]` message.

The resulting png will automatically replace the branch's png and add it to stage.

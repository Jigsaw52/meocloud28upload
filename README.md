# MEO Cloud to 8upload Image Migration Script

This Python script downloads images hosted on MEO Cloud (https://meocloud.pt/) and uploads them to https://8upload.com/.
After processing, it generates a CSV report containing the original URLs, the new 8upload URLs, local download paths, replacement commands, and delete links.

⚠️ **Only image files are supported** as 8upload only accepts image uploads.

## Overview

The script is useful for migrating or re-hosting images referenced in text or source files that currently point to MEO Cloud URLs. It:
- Parses MEO Cloud links from an input file
- Downloads each image locally
- Uploads the image to 8upload.com
- Produces a CSV file with all relevant metadata and helper commands

### Input File Format

The script expects a text file where each line follows this format:

    <INPUT_PATH>:<URL>

- `<INPUT_PATH>` is the file where the URL was found
- `<URL>` is a MEO Cloud download link

Example:

    posts/page1.html:https://cld.pt/dl/download/3fe27c66-58fb-4c81-ae6e-1fb4f7c10b74/image.jpg
    docs/readme.txt:https://cld.pt/dl/download/9260b938-5f23-4aba-888e-0a92c9bdda7e/example.png

#### Generating the Input File

You can generate the input file by scanning a directory for MEO Cloud links:

`grep -REo "(http|https)://cld.pt/[a-zA-Z0-9./?=_%:&-]*" | sort | uniq > input.txt`

### Output File

The script generates a CSV file with the following columns:
- input_path — Original file path where the URL was found
- original_url — Original MEO Cloud URL
- updated_url — New image URL after upload to 8upload
- local_path — Local filesystem path of the downloaded image
- replace_command — Perl command to replace the old URL with the new one
- delete_link — Link to delete the uploaded image from 8upload

### Usage
`./meocloud28upload.py input.txt output.csv`

Where:
- input.txt — input file containing <INPUT_PATH>:<URL> entries
- output.csv — CSV file where results are stored

### Example CSV Output
```
input_path,original_url,updated_url,local_path,replace_command,delete_link
posts/page1.html,https://cld.pt/dl/download/3fe27c66-58fb-4c81-ae6e-1fb4f7c10b74/image.jpg,https://8upload.com/image/da39a3ee5e6b4b0d32/image1768671538.jpg,meocould_images/3fe27c66-58fb-4c81-ae6e-1fb4f7c10b74/image.jpg,perl -pe 's#\Qhttps://cld.pt/dl/download/3fe27c66-58fb-4c81-ae6e-1fb4f7c10b74/image.jpg\E#https://8upload.com/image/da39a3ee5e6b4b0d32/image1768671538.jpg#g' -i 'posts/page1.html',https://8upload.com/delete/3255bfef95601890afd80709.php
```

#### Replacing URLs Automatically

Each row in the CSV contains a ready-to-use Perl command:

```
perl -pi -e 's#\Q<OLD_URL>\E#<NEW_URL>#g' <INPUT_PATH>
```

This command allows you to update the original files with the new 8upload URLs safely and efficiently.

### Requirements
- Python 3.8 or newer
- Access to:
    - https://cld.pt
    - https://8upload.com

### Limitations
 - Non-image files are skipped
 - Invalid or expired MEO Cloud links will fail
 - No retry logic unless explicitly implemented
 - 8upload image format restrictions apply

### Disclaimer

This script is intended for personal use or authorized content migration only.
Ensure you have the legal right to download and re-host all images.

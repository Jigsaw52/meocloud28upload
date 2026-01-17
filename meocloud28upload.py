#!/usr/bin/env python3

import os
import requests
import argparse
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# input file format:
# <INPUT_PATH><INPUT_SEPARATOR><URL>
# input file created with (INPUT_SEPARATOR is :):
# grep -REo --exclude-dir={.jekyll-cache,_site} "(http|https)://cld.pt/[a-zA-Z0-9./?=_%:&-]*" | sort | uniq > input.txt


INPUT_SEPARATOR = ':'
CSV_SEPARATOR = ','
DOWNLOAD_ORIGINAL = True
UPLOAD_TO_8IMAGE = True
ORIGINAL_IMG_DIR = 'meocloud_images'

DOWNLOAD_TIMEOUT = 120 # seconds
DOWNLOAD_CHUNK_SIZE = 65536 # bytes
UPLOAD_URL = "https://8upload.com/url.php"


session = requests.Session()

def parse_uuid_and_filename(url: str):
    """
    Extract UUID and filename from:
    https://cld.pt/dl/download/<UUID>/<FILENAME>[?params]
    """
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")

    # Expected: dl/download/<UUID>/<FILENAME>
    if len(path_parts) < 4:
        return None, None

    uuid = path_parts[-2]
    filename = path_parts[-1]

    return uuid, filename


def download_file(url: str, uuid: str, filename: str):
    image_dir = os.path.join(ORIGINAL_IMG_DIR, uuid)
    os.makedirs(image_dir, exist_ok=True)
    filepath = os.path.join(image_dir, filename)

    with session.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT) as r:
        r.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

    return filepath


def clean_url_for_8upload(url: str):
    # 8upload does not support URL params, remove them
    url_path = urlparse(url).path
    # 8upload also does not support dots in the path (except the last one for the extension), encode them
    dot_count = url_path.count('.')
    url_path = url_path.replace('.', '%2E', dot_count - 1)
    return urljoin(url, url_path)


def get_8upload_link(soup: BeautifulSoup, link_title: str):
    link = ""
    label = soup.find("label", string=lambda t: t and link_title in t)
    if label:
        input_tag = None
        if label.has_attr("for"):
            input_tag = label.find_next("input", id=label["for"])
        else:
            input_tag = label.find_next("input")

        if input_tag and input_tag.has_attr("value"):
            link = input_tag["value"]
    
    return link


def upload_to_8upload(url: str):
    payload = {
        "url": clean_url_for_8upload(url),
        "submit": "Submit"
    }

    response = session.post(UPLOAD_URL, data=payload, timeout=DOWNLOAD_TIMEOUT)
    response.raise_for_status()

    if "It seems that the added URL is not a URL to the image. Please check and try again" in response.text:
        raise Exception("File type not supported")

    soup = BeautifulSoup(response.text, "html.parser")
    link = get_8upload_link(soup, "Hotlink / Direct-Link")
    delete_link = get_8upload_link(soup, "Delete Link")

    return link, delete_link


def get_replace_link_command(path: str, old_url: str, new_url: str):
    return f"perl -pe 's#\\Q{old_url}\\E#{new_url}#g' -i '{path}'"    


def main():
    parser = argparse.ArgumentParser(
        description="Process an input file and write to an output file."
    )
    parser.add_argument("input_file", help="Path to the input file")
    parser.add_argument("output_file", help="Path to the output file")
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as infile, \
         open(args.output_file, "w", encoding="utf-8") as outfile:

        header = CSV_SEPARATOR.join(["input_path" ,"original_url", "updated_url", "local_path", "replace_command", "delete_link"]) + "\n"
        outfile.write(header)

        for line in infile:
            line = line.strip()
            if len(line) == 0 or line[0] == '#':
                continue

            # format: <INPUT_PATH><INPUT_SEPARATOR><URL>
            input_path, original_url = line.split(INPUT_SEPARATOR, 1)
            original_url = original_url.strip()

            local_path = ""
            if DOWNLOAD_ORIGINAL:
                try:
                    uuid, filename = parse_uuid_and_filename(original_url)
                    local_path = download_file(original_url, uuid, filename)
                except Exception as e:
                    print(f"Download failed for {original_url}: {e}")

            updated_url = ""
            delete_link = ""
            replace_command = ""
            if UPLOAD_TO_8IMAGE:
                try:
                    updated_url, delete_link = upload_to_8upload(original_url)
                    replace_command = get_replace_link_command(input_path, original_url, updated_url) if updated_url else ""
                except Exception as e:
                    print(f"Upload failed for {original_url}: {e}")

            line = CSV_SEPARATOR.join([input_path, original_url, updated_url, local_path, replace_command, delete_link]) + "\n"
            outfile.write(line)
            
if __name__ == "__main__":
    main()


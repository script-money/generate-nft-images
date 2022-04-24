import os
from PIL import Image
import pandas as pd
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

# FILL YOUR OWN CONFIG---------------------------------------------------------------------------------
W = 400  # image width. pixel unit
H = 400  # image height. pixel unit
EXTENSION = ["PNG", "png"]  # image extensions
PARTS_DICT = {
    "parts": 0.9,
    "parts2": 0.1,
}  # if you have multiple groups images parts, set key as folder name, value is occurrence probability
IMAGES = "./images"  # folder save generate images
METADATA = "./metadata"  # folder save metadata
BLINDBOX_DATA_FOLDER = "./blindbox"
AMOUNT = 30  # amount of images to generate
NAMES = ["Double Letter", "Color Letter"]  # custom NFT names, random choice from list
DESCRIPTION = "Double Letter For Test"  # custom NFT discription
START_ID = 1  # start id of generated images
BLINDBOX_IMAGE = ""
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}  # if in China, you need set proxy to access IPFS node
PROJECT_ID = os.getenv(
    "PROJECT_ID"
)  # need to register ipfs of infura to get PROJECT_ID and PROJECT_SECRET, set them in .env
PROJECT_SECRET = os.getenv("PROJECT_SECRET")  # same as previous line
# ------------------------------------------------------------------------------------------------------

FOLDERS = list(PARTS_DICT.keys())
WEIGHTS = list(PARTS_DICT.values())

# Iterate to get the material file
def get_files_path(folders=FOLDERS):
    files_path = []
    for folder in folders:
        for root, _, _ in os.walk(folder):
            if root not in FOLDERS:
                for _, _, files in os.walk(root):
                    for file in files:
                        if file != ".DS_Store":
                            files_path.append(os.path.join(root, file))
    files_path.sort()
    return files_path


files_path = get_files_path()

if __name__ == "__main__":
    # clean old folder
    folders = ["images", "metadata"]
    for folder in folders:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"{folder} folder cleaned")
        os.mkdir(folder)

    # Validate image format and size
    for path in files_path:
        assert (
            path.split(".")[-1] in EXTENSION
        ), f"{path}'s extension is not {EXTENSION} "
        im = Image.open(path)
        w, h = im.size
        assert w == W, f"{path} width not equal {W}"
        assert h == H, f"{path} height not equal {H}"

    # export tables
    attrs = [os.path.split(path) for path in files_path]
    d = {
        "folder": [a[0].split(os.sep)[-2] for a in attrs],
        "prop": [a[0].split("_")[1] for a in attrs],
        "value": [a[1].split(".")[0] for a in attrs],
        "ratio": 1,
    }
    df = pd.DataFrame(data=d)
    df.to_csv("ratio.csv", index=False)

    if os.path.exists("ratio.csv"):
        print("generate table success!")
        print("You can modify ratio.csv to change the ratio of each parts")
        print("PS: Don't use Excel to save csv, use notepad instead")


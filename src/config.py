import os
from enum import Enum
from dotenv import load_dotenv
from pathlib import Path

from httpx._types import ProxiesTypes

load_dotenv()
ROOT_DIR = Path(__file__).parent.parent

# get_table-------------------------------------------------------------------------------------------
EXTENSION = ["PNG", "png"]  # image extensions
PARTS_DICT = {
    "parts": 0.5,
    "parts2": 0.5,
}  # if you have multiple groups images parts, set key as folder name, value is occurrence probability
W = 400  # image width. pixel unit
H = 400  # image height. pixel unit
# ----------------------------------------------------------------------------------------------------


FOLDERS = list(PARTS_DICT.keys())
WEIGHTS = list(PARTS_DICT.values())


# final_check-----------------------------------------------------------------------------------------
CHECK_DUPLICATE_TRAITS_INDEX = (
    []
)  # attribute columns index used in the check duplicate, start from 1
SHUFFLE = False  # shuffle the images when check ratio
# ----------------------------------------------------------------------------------------------------


class Quality(Enum):
    web_low = "web_low"
    web_medium = "web_medium"
    web_high = "web_high"
    web_very_high = "web_very_high"
    web_maximum = "web_maximum"
    low = "low"
    medium = "medium"
    high = "high"
    maximum = "maximum"


# generate--------------------------------------------------------------------------------------------
START_ID = 1  # start id of generated images
IMAGES = "./images"  # folder save generate images
METADATA = "./metadata"  # folder save metadata
AMOUNT = 100  # amount of images to generate
NAMES = ["Test NFT"]  # custom NFT names, random choice from list
DESCRIPTION = "generate images test NFT description"  # custom NFT description
QUALITY = Quality.web_very_high.value
# ----------------------------------------------------------------------------------------------------


# upload_mystery_box----------------------------------------------------------------------------------
MYSTERY_BOX_IMAGE = "https://script.money/avatar_box.png"  # mystery box image link
MYSTERY_BOX_DATA_FOLDER = "./mystery_box_data"
UPLOAD_MYSTERY_BOX_METADATA = True  # if don't want to upload metadata, set False
# ----------------------------------------------------------------------------------------------------


# upload----------------------------------------------------------------------------------------------
UPLOAD_METADATA = False  # set False if don't want to upload metadata
PIN_FILES = False  # if want to upload permanently, set to True
PROXIES: ProxiesTypes = {
    "http://": "http://127.0.0.1:7890",
    "https://": "http://127.0.0.1:7890",
}  # if in China, you need set proxy to access IPFS node
PROJECT_ID = os.getenv(
    "PROJECT_ID"
)  # need to register ipfs of infura to get PROJECT_ID and PROJECT_SECRET, set them in .env
PROJECT_SECRET = os.getenv("PROJECT_SECRET")  # same as previous line
# ----------------------------------------------------------------------------------------------------


# fresh_metadata--------------------------------------------------------------------------------------
BASEURL = "ipfs://Qxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/"
CONTRACT = "0x8888888888888888888888888888888888888888"
ID_TO_REFRESH = []  # if empty will refresh all
OPENSEA_KEY = os.getenv("OPENSEA_KEY")  # same as previous line

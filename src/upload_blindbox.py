from get_table import (
    AMOUNT,
    NAMES,
    DESCRIPTION,
    START_ID,
    BLINDBOX_IMAGE,
    BLINDBOX_DATA_FOLDER,
)
import random
import json
import os
from upload import upload_folder


def generate_blindBox_metadata():
    for index in range(START_ID, AMOUNT + START_ID):
        info_dict = {
            "name": f"{random.choice(NAMES)} #{index}",
            "description": f"{DESCRIPTION}",
            "image": BLINDBOX_IMAGE,
        }
        info_json = json.dumps(info_dict)
        with open(os.path.join(BLINDBOX_DATA_FOLDER, str(index)), "w") as f:
            f.write(info_json)
    print(f"save metadata complete")


if __name__ == "__main__":
    generate_blindBox_metadata()
    metadata_root, _ = upload_folder(BLINDBOX_DATA_FOLDER, "application/json")
    print(f"upload blind data complete, hash is {metadata_root}")

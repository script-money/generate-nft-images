from get_table import (
    AMOUNT,
    NAMES,
    DESCRIPTION,
    START_ID,
    MYSTERY_BOX_IMAGE,
    MYSTERY_BOX_DATA_FOLDER,
)
import random
import json
import os
from upload import upload_folder


def generate_mystery_box_metadata():
    for index in range(START_ID, AMOUNT + START_ID):
        info_dict = {
            "name": f"{random.choice(NAMES)} #{index}",
            "description": f"{DESCRIPTION}",
            "image": MYSTERY_BOX_IMAGE,
        }
        info_json = json.dumps(info_dict)
        with open(os.path.join(MYSTERY_BOX_DATA_FOLDER, str(index)), "w") as f:
            f.write(info_json)
    print(f"save metadata complete")


if __name__ == "__main__":
    # generate_mystery_box_metadata()
    metadata_root, _ = upload_folder(MYSTERY_BOX_DATA_FOLDER, "application/json")
    print(f"upload blind data complete, hash is {metadata_root}")

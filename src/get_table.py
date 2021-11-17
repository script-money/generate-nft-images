import os
from PIL import Image
import pandas as pd
import os
import shutil

# generate template
W = 400
H = 400
EXTENSION = "png"
PARTS = "./parts"
IMAGES = "./images"
METADATA = "./metadata"
AMOUNT = 10
NAME = "Double Letter"
DESCRIPTION = "Double Letter For Test"

# Iterate to get the material file
def get_files_path(folder="./PARTS"):
    files_path = []
    for root, dirs, _ in os.walk(folder):
        if root != PARTS:
            for _, _, files in os.walk(root):
                for file in files:
                    if file != ".DS_Store":
                        files_path.append(os.path.join(root, file))
    return files_path


files_path = get_files_path()


if __name__ == "__main__":
    # clean old folder
    folders = ["images", "metadata"]
    for folder in folders:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.mkdir(folder)

    # Validate image format and size
    for path in files_path:
        assert (
            path.split(".")[-1] == EXTENSION
        ), f"{path}'s extension is not {EXTENSION} "
        im = Image.open(path)
        w, h = im.size
        assert w == W, f"{path} width not equal {W}"
        assert h == H, f"{path} height not equal {H}"

    # export tables
    attrs = [os.path.split(path) for path in files_path]
    d = {
        "prop": [a[0].split("_")[1] for a in attrs],
        "value": [a[1].split(".")[0] for a in attrs],
        "ratio": 1,
    }
    df = pd.DataFrame(data=d)
    df.to_csv("ratio.csv", index=False)

    if os.path.exists("ratio.csv"):
        print("generate table success!")


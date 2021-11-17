import os
from PIL import Image
import pandas as pd
import numpy as np
import random
import os
from get_table import files_path, W, H, AMOUNT

DF_ATTR = None

# modify table data first
df_csv = pd.read_csv("./ratio.csv")
df_group = df_csv.groupby(["prop", "value"]).agg({"ratio": "sum"})
df_pac = df_group.groupby(level=0).apply(lambda x: x / float(x.sum()))

props = df_csv["prop"].unique()

# get random attributes
def random_attr():
    attributes = []
    for prop in props:
        k = random.random()
        ratio_arr = df_pac.query(f"prop == '{prop}'").ratio.values
        cum_arr = np.cumsum(ratio_arr) - k
        first_index = next(x[0] for x in enumerate(cum_arr) if x[1] > 0)
        value = df_pac.loc[(prop), :].index[first_index]
        attributes.append({"value": value, "trait_type": prop})
    return attributes


def generate_images(
    df_csv: pd.DataFrame, amount: int, save_folder: str = "./images", start_id: int = 0
) -> pd.DataFrame:
    used_attributes = []
    cols = ["imagehash", "path"] + [i["trait_type"] for i in random_attr()]
    df_attr = pd.DataFrame(columns=cols)

    prop_count_df = df_csv.groupby("prop").count()
    max_count = prop_count_df["value"].values.cumprod()[-1]
    # check AMOUNT is if valid
    df_group = df_csv.groupby(["prop", "value"]).agg({"ratio": "sum"})
    df_pac = df_group.groupby(level=0).apply(lambda x: x / float(x.sum()))
    assert (
        np.min(df_pac["ratio"]) * amount >= 1
    ), "The number generated is too small to reflect the minimum probability and the total should be increased"
    assert (
        amount <= max_count
    ), "Generate too much, there will be duplicate generation, should increase the number of material or reduce the total amount"

    assert (
        len(list(filter(lambda f: f.split(".")[1] == "png", os.listdir(save_folder))))
        == 0
    ), f"{save_folder} folder is not empty, backup the original data and tables first"

    for i in range(amount):
        # avoid duplicate
        index = i + start_id
        attributes = random_attr()
        while attributes in used_attributes:
            attributes = random_attr()
        used_attributes.append(attributes)
        # Get the images to be read in the order of overlay
        sorted_paths = sorted(
            [
                next(
                    path
                    for path in files_path
                    if attr["trait_type"] in path and attr["value"] in path
                )
                for attr in attributes
            ]
        )
        base_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for path in sorted_paths:
            img = Image.open(path, "r")
            base_img.paste(img, (0, 0), mask=img)
        # save images
        filename = (
            f"{index}-{'-'.join(list(map(lambda i: i['value'] ,attributes)))}.png"
        )
        base_img.save(os.path.join(save_folder, filename))
        # add porpety
        df_attr = df_attr.append(
            {"imagehash": None, "path": os.path.join(save_folder, filename)}
            | {i["trait_type"]: i["value"] for i in attributes},
            ignore_index=True,
        )
    df_attr[cols].to_csv(os.path.join(save_folder, "attr.csv"), index=False)
    return df_attr


if __name__ == "__main__":
    DF_ATTR = generate_images(df_csv, AMOUNT, start_id=0)
    print("generate images in ./images folder success")

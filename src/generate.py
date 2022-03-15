import os
from PIL import Image
import pandas as pd
import numpy as np
import random
from numpy.random import choice
import os
from get_table import files_path, W, H, AMOUNT, PARTS_DICT, FOLDERS, WEIGHTS


def get_ratio(x):
    folder_name = x["folder"].values[0]
    custom_ratio = x["ratio"].values[0]
    folder_ratio = PARTS_DICT[folder_name]
    return custom_ratio * folder_ratio


# modify table data first
df_csv = pd.read_csv("./ratio.csv")
df_group = df_csv.groupby(["folder", "prop", "value"]).apply(get_ratio).to_frame()
df_pac = (
    df_group.groupby(level=["folder", "prop"])
    .apply(lambda x: x / float(x.sum()))
    .rename(columns={0: "ratio"})
)


props = df_csv["prop"].unique()

# get random attributes
def random_attr():
    attributes = []
    select_folder = choice(FOLDERS, p=WEIGHTS)
    for prop in props:
        k = random.random()
        ratio_arr = df_pac.query(
            f"(folder == '{select_folder}') & (prop == '{prop}')"
        ).ratio.values
        cum_arr = np.cumsum(ratio_arr) - k
        first_index = next(x[0] for x in enumerate(cum_arr) if x[1] > 0)
        value = df_pac.loc[(select_folder), (prop), :].index[
            first_index
        ]  # in pandas 1.4, loc is not return tuple but single element
        if type(value) is str:
            attributes.append(
                {"value": (select_folder, prop, value), "trait_type": prop}
            )
        else:
            attributes.append({"value": value, "trait_type": prop})
    return attributes


def generate_images(
    df_csv: pd.DataFrame, amount: int, save_folder: str = "./images", start_id: int = 0
) -> pd.DataFrame:
    used_attributes = []
    cols = ["path"] + [i["trait_type"] for i in random_attr()]
    df_attr = pd.DataFrame(columns=cols)

    prop_count_df = df_csv.groupby(["folder", "prop"]).count()
    sum_count = 0
    for _folder in FOLDERS:
        folder_df = prop_count_df.query(f"folder == '{_folder}'")["ratio"]
        max_count = folder_df.values.cumprod()[-1]
        sum_count += max_count
    assert (
        amount <= sum_count
    ), "Generate too much, there will be duplicate generation, should increase the number of material or reduce the total amount"
    assert (
        np.min(df_pac["ratio"]) * amount >= 1
    ), "The number generated is too small to reflect the minimum probability and the total should be increased"
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
                    if attr["trait_type"] in path.split(os.sep)[1]
                    and attr["value"][2] in path.split(os.sep)[2]
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
            f"{index}-{'-'.join(list(map(lambda i: i['value'][-1] ,attributes)))}.png"
        )
        base_img.save(os.path.join(save_folder, filename))
        # add porpety
        df_attr = df_attr.append(
            {"path": os.path.join(save_folder, filename)}
            | {i["trait_type"]: i["value"][-1] for i in attributes},
            ignore_index=True,
        )

    df_attr[cols].to_csv(os.path.join(save_folder, "attr.csv"), index=False)
    return df_attr


if __name__ == "__main__":
    generate_images(df_csv, AMOUNT, start_id=0)
    print("generate images in ./images folder success")

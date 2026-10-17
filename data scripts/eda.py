"""Phase 2 - EDA: charts for the report. Saves PNGs to report/figures/."""
import random
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from PIL import Image

from config import CLEAN, CLEAN_META, FIGURES, RAW_META, SEED

sns.set_theme(style="whitegrid")
FIGURES.mkdir(parents=True, exist_ok=True)


def save(name):
    plt.tight_layout()
    plt.savefig(FIGURES / name, dpi=200)
    plt.close()


def main():
    df = pd.read_csv(CLEAN_META)

    # 1. Class distribution
    plt.figure(figsize=(9, 5))
    order = df["dish"].value_counts().index
    sns.countplot(data=df, y="dish", order=order, color="#3a7ca5")
    plt.title("Images per dish (after cleaning)")
    save("class_distribution.png")

    # 2. Raw vs clean counts
    raw = pd.read_csv(RAW_META)["dish"].value_counts().rename("raw")
    both = pd.concat([raw, df["dish"].value_counts().rename("clean")], axis=1)
    both.plot(kind="bar", figsize=(10, 5))
    plt.title("Raw vs cleaned image counts"); plt.ylabel("images")
    save("raw_vs_clean.png")

    # 3. Image size spread
    plt.figure(figsize=(6, 5))
    plt.scatter(df["width"], df["height"], s=6, alpha=0.3)
    plt.xlabel("width (px)"); plt.ylabel("height (px)")
    plt.title("Image resolution spread")
    save("image_sizes.png")

    # 4. Brightness (lighting) per dish
    plt.figure(figsize=(10, 5))
    sns.boxplot(data=df, x="dish", y="brightness", color="#9ecae1")
    plt.xticks(rotation=60, ha="right")
    plt.title("Brightness per dish (lighting variation)")
    save("brightness_per_dish.png")

    # 5. Source / setting distribution (bias analysis)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    df["source"].value_counts().plot(kind="bar", ax=ax[0], title="Images by source")
    df["setting"].value_counts().plot(kind="bar", ax=ax[1],
                                      title="Images by setting (home/restaurant)")
    save("source_and_setting.png")

    # 6. Sample grid: 4 random images per dish
    random.seed(SEED)
    dishes = sorted(df["dish"].unique())
    fig, axes = plt.subplots(len(dishes), 4, figsize=(8, 2 * len(dishes)))
    for i, dish in enumerate(dishes):
        files = df[df["dish"] == dish]["filename"].tolist()
        for j, f in enumerate(random.sample(files, min(4, len(files)))):
            axes[i][j].imshow(Image.open(CLEAN / dish / f))
        for j in range(4):
            axes[i][j].axis("off")
        axes[i][0].set_title(dish, fontsize=8, loc="left")
    save("sample_grid.png")

    print("Figures saved to", FIGURES)


if __name__ == "__main__":
    main()

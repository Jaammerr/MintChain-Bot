import os

from loguru import logger


def export_trees_ids(results: list[tuple[str, str]]):
    if not os.path.exists("./trees_results"):
        with open("./config/trees_results.txt", "w") as file:
            for result in results:
                file.write(f"{result[0]}:{result[1]}\n")

    logger.success("Trees IDs exported to trees_results.txt")

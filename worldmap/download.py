#!/usr/bin/env python3

from contextlib import closing
import csv
import io
import zipfile

import requests


def request_population_data() -> requests.Response:
    # one can view the populaton data at https://data.worldbank.org/indicator/SP.POP.TOTL
    r: requests.Response = requests.get(
        "https://api.worldbank.org/v2/en/indicator/SP.POP.TOTL",
        params={"downloadformat": "csv"},
    )
    return r


def read_content_from_response(r: requests.Response) -> str:
    # this refers to https://stackoverflow.com/a/22385790
    with closing(r), zipfile.ZipFile(io.BytesIO(r.content)) as archive:
        try:
            # There should be 3 csv files:
            # 1 population file with prefix "API_SP.POP.TOTL" and 2 metadata file with prefix "Metadata",
            # we'll focus on the populaton file.
            (pop_file,) = filter(
                lambda x: x.filename.startswith("API_SP.POP.TOTL"), archive.infolist()
            )
        except ValueError:
            print(
                "Seems like the prefix or folder structure has changed, "
                "please modify the above to locate the correct file"
            )
        # "use utf-8-sig" because is encoded with "UTF-8 byte order mark (BOM)"
        content: str = archive.read(pop_file).decode("utf-8-sig")
    return content


def main() -> None:
    r = request_population_data()
    content = read_content_from_response(r)

    # About the structure of content:
    # 1. Line 3 contains last update time, line 5 are the field names,
    #   data of populations start from line 6.
    # 2. Each line has a trailing comma and all fields are warpped with double quotes.
    #
    content = content.replace(",\r", "\r")  # NOTE: this might be OS dependent
    with io.StringIO(content) as f:
        for _ in range(2):
            next(f)
        _, last_update_time = next(f).split(",")

        for _ in range(1):
            next(f)
        sheet = csv.DictReader(f, quotechar='"', delimiter=",", quoting=csv.QUOTE_ALL)


if __name__ == "__main__":
    main()

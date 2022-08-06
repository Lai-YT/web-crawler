#!/usr/bin/env python3
"""Generates a svg world map on the population of countries last year."""

from datetime import datetime
from typing import Dict, IO, List
import csv
import io
import zipfile

from pygal.maps.world import World
import bs4
import requests


def get_population_data() -> requests.Response:
    # one can view the populaton data at https://data.worldbank.org/indicator/SP.POP.TOTL
    r: requests.Response = requests.get(
        "https://api.worldbank.org/v2/en/indicator/SP.POP.TOTL",
        params={"downloadformat": "csv"},
    )
    return r


def read_content_from_response(r: requests.Response) -> str:
    # the way to manage requested file in memory refers to https://stackoverflow.com/a/22385790
    with zipfile.ZipFile(io.BytesIO(r.content)) as archive:
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


def get_country_code_2_to_3_table() -> Dict[str, str]:
    # Look up the conversion table from IBAN.com.
    r: requests.Response = requests.get("https://www.iban.com/country-codes")
    soup = bs4.BeautifulSoup(r.content, "lxml")

    country_table: bs4.Tag = soup.find(
        "table", class_=["table", "table-bordered", "downloads", "tablesorter"]
    )

    country_code_3_to_2_table: Dict[str, str] = {}
    # The sturcture is as the following:
    # <tbody>
    #     <tr>
    #         <td>Afghanistan</td>  --- Country
    #         <td>AF</td>           --- Alpha-2 code
    #         <td>AFG</td>          --- Alpha-3 code
    #         <td>004</td>          --- Numeric
    #     </tr>
    #     <tr>
    #         ...
    #     </tr>
    #     ...
    # </tbody>
    contries: List[bs4.Tag] = country_table.tbody.find_all("tr")
    for country in contries:
        country, alpha_2, alpha_3, numeric = country.find_all("td")
        country_code_3_to_2_table[alpha_3.text] = alpha_2.text
    return country_code_3_to_2_table


def is_missing_data(data: str) -> bool:
    """Returns True if the data in type str is empty."""
    return not data


def remove_trailing_comma(content: str) -> str:
    return content.replace(",\r", "\r")  # NOTE: this might be OS dependent


def skip_line(f: IO, line_count: int) -> None:
    assert line_count > 0, "can only skip positive number of line"

    for _ in range(line_count):
        next(f)


def main() -> None:
    with get_population_data() as r:
        content = read_content_from_response(r)

    # About the structure of content:
    # 1. Line 3 contains last update time, line 5 are the field names,
    #   data of populations start from line 6.
    # 2. Each line has a trailing comma and all fields are warpped with double quotes.
    #
    content = remove_trailing_comma(content)
    with io.StringIO(content) as f:
        skip_line(f, line_count=2)
        _, last_update = next(f).split(",")
        last_update_time = datetime.strptime(last_update.strip(), '"%Y-%m-%d"')

        skip_line(f, line_count=1)
        sheet = csv.DictReader(f, quotechar='"', delimiter=",", quoting=csv.QUOTE_ALL)

        # The world bank uses alpha-3 country code while pygal uses alpha-2 country code.
        country_code_3_to_2_table: Dict[str, str] = get_country_code_2_to_3_table()

        # can't show multiple years on a single world map since they overlaps
        year = str(last_update_time.year - 1)
        population_of_countries: Dict[str, int] = {}
        for country in sheet:
            country_code: str = country_code_3_to_2_table.get(
                country["Country Code"], ""
            )
            # pygal.map.world uses lower case country code
            country_code = country_code.lower()
            if is_missing_data(country[year]) or country_code not in World.area_names:
                continue
            population_of_countries[country_code] = int(country[year])

    worldmap = World()
    worldmap.title = "Population of countries (source: The World Bank)"
    worldmap.add(year, population_of_countries)
    worldmap.render_to_file(f"country-map-{year}.svg")


if __name__ == "__main__":
    main()

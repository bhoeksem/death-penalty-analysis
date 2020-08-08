#!/usr/bin/python3

import pandas as pd
import json
import math
from reppy.robots import Robots
import re
import time
import os

from selenium.webdriver import Firefox, FirefoxProfile, FirefoxOptions
from selenium.webdriver.support.ui import Select

regions = [
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Federal",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming"
        ]

special_suffix = {
        "Georgia": "_(U.S._state)"
        }

def get_element(amap, *keys):
    tmp = amap

    for key in keys:
        if key in tmp:
            tmp = tmp[key]
        else:
            return None

    return tmp


def url_friendly(region):
    return region.replace(" ", "_").replace("*", "")

def get_table_by_headers(headers):
    table_data = []

    header2trs = {}
    for header in headers:
        header2trs[header] = []
        header_containers = browser.find_elements_by_xpath('//*[contains(text(), "' + header + '")]')
        for header_container in header_containers:
            cell = None
            try:
                cells = header_container.find_elements_by_xpath(".//ancestor::th")
                cell = cells[-1]
            except:
                cells = header_container.find_elements_by_xpath(".//ancestor::td")
                if len(cells) > 0:
                    cell = cells[-1]

            if cell:
                trs = cell.find_elements_by_xpath(".//ancestor::tr")
                tr = trs[-1]

                header2trs[header].append(tr)

    header1 = headers[0]
    trs1 = header2trs[header1]
    for header2, trs2 in header2trs.items():
        if header1 != header2:
            for tr1 in trs1:
                in_trs2 = False
                for tr2 in trs2:
                    if tr1.id == tr2.id:
                        in_trs2 = True
                        break

                if not in_trs2:
                    trs1.remove(tr1)

    if len(trs1) == 1:
        table = trs1[0].find_element_by_xpath(".//ancestor::table")
        new_table_data = get_table_data_from_element(table, trs1[0], headers)
        success = append_unique_rows(table_data, new_table_data)

    return table_data

def get_table_data_from_element(table, header_tr, headers):
    browser.implicitly_wait(1)
    data = []

    idx2header = {}
    row = []

    idx = 0
    cells = header_tr.find_elements_by_tag_name("th") + header_tr.find_elements_by_tag_name("td")
    header_row_col_num = len(cells)
    for cell in cells:
        for header in headers:
            if header == cell.text:
                idx2header[idx] = header
                row.append(header)
                break
        idx += 1

    data.append(row)


    trs = table.find_elements_by_tag_name("tr")

    header_row_found = False
    for tr in trs:
        if not header_row_found:
            if tr.id == header_tr.id:
                header_row_found = True
            continue

        row = []

        idx = 0
        cells = tr.find_elements_by_tag_name("th") + tr.find_elements_by_tag_name("td")
        if len(cells) != header_row_col_num:
            continue

        for cell in cells:
            if idx in idx2header:
                row.append(cell.text)
                    
            idx += 1

        if len(row) == len(data[0]):
            data.append(row)

    browser.implicitly_wait(15)
    return data

def is_crawlable(url):
    bot_allowed = False

    domain_matches = re.match("^((?:https?:\/\/)?(?:[^@\/\n]+@)?(?:www\.)?([^:\/?\n]+))", url)
    if domain_matches:
        source_domain = domain_matches.groups()[0]
        robots_path = source_domain + "/robots.txt"
        robots = Robots.fetch(robots_path, verify=False)
        bot_allowed = robots.allowed(url.replace(source_domain, ""), "*")

    return bot_allowed

def append_unique_rows(rows, new_rows):
    any_different = False

    init_num_rows = len(rows)
    for new_row in new_rows:
        all_different = True
        for row in rows:
            are_same = True
            for i in range(len(row)):
                if new_row[i] != row[i]:
                    are_same = False
                    break

            if are_same:
                all_different = False
                break

        if all_different:
            rows.append(new_row)

    return len(rows) > init_num_rows

def header_match(df_header, expected_header):
    for expected_col in expected_header:
        one_same = False
        for df_col in df_header:
            if isinstance(df_col, str) and df_col.replace("*", "") == expected_col:
                one_same = True
                break
        if not one_same:
            return False
    return True

def get_historic_death_row_data():
    data = pd.DataFrame()

    source_url = "https://deathpenaltyinfo.org/executions/execution-database"
    next_page_selector = "//a[contains(text(), 'Next ›')]"

    if is_crawlable(source_url):

        browser.get(source_url)

        another_page = True
        while another_page:
            time.sleep(10)

            init_num_rows = data.shape[0]

            tables = browser.find_elements_by_tag_name("table")

            expected_header = ["Date", "Age", "Sex", "Race", "State", "County", "Region", "Method", "Juvenile", "Federal", "Volunteer", "Foreign National"]
            for table in tables:
                dfs = pd.read_html(table.get_attribute('outerHTML'))

                for df in dfs:
                    if header_match(list(df.columns), expected_header):
                        data = data.append(df)
                        break

            next_page_buttons = browser.find_elements_by_xpath(next_page_selector)
            another_page = data.shape[0] > init_num_rows and len(next_page_buttons) > 0

            if another_page:
                next_page_buttons[0].click()

    return data


def valid_html_doc(elem):
    return "<html><head><title></title></head><body>" + elem + "</body></html>"

def get_state_demographic_data():
    data = {}

    demo_url = "https://www.kff.org/other/state-indicator/distribution-by-raceethnicity/?dataView=1&currentTimeframe=0&sortModel=%7B%22colId%22:%22Location%22,%22sort%22:%22asc%22%7D"

    if is_crawlable(demo_url):
        browser.get(demo_url)

        time.sleep(10)

        accept_cookies_button = browser.find_element_by_id("hs-eu-confirmation-button")
        if accept_cookies_button:
            accept_cookies_button.click()

        year_select_elem = browser.find_element_by_id("indicator-timeframe")
        year_options = year_select_elem.find_elements_by_tag_name("option")
        years = [year_option.get_attribute("innerHTML") for year_option in year_options]

        year_select = Select(year_select_elem)
        while len(years) > 0:
            year = years.pop(0)

            year_select.select_by_visible_text(year)
            time.sleep(15)

            data[year] = []

            download_button = browser.find_element_by_id("table-raw-data")
            download_button.click()

            time.sleep(10)

            expected_header = ["Location","White","Black","Hispanic","American Indian/Alaska Native","Asian","Native Hawaiian/Other Pacific Islander","Two Or More Races","Total"]
            dg_filename = "raw_data.csv"
            if os.path.isfile(dg_filename):
                with open(dg_filename, 'r') as infile:
                    lines = infile.read().splitlines()

                    header_row = None
                    for line in lines:
                        if not header_row:
                            is_header = True
                            for header in expected_header:
                                if header not in line:
                                    is_header = False
                                    break

                            if is_header:
                                header_row = line.replace('"', '').split(",")
                                if "Footnotes" in header_row:
                                    header_row.remove("Footnotes")

                            continue

                        else:
                            row = line.replace('"', '').replace("N/A", "0").split(",")

                            if len(row) >= len(header_row):
                                row_dict = {}
                                for j in range(min(len(header_row), len(row))):
                                    row_dict[header_row[j]] = float(row[j]) if row[j].isnumeric() else row[j]

                                data[year].append(row_dict)

                os.remove("raw_data.csv")

    return data

                    
def get_current_death_row_data():
    data = pd.DataFrame()

    source_url = "https://deathpenaltyinfo.org/death-row/overview/demographics"

    if is_crawlable(source_url):
        time.sleep(10)

        browser.get(source_url)

        init_num_rows = data.shape[0]

        tables = browser.find_elements_by_tag_name("table")

        expected_header = ["State", "Total", "Black", "White", "Latino/a", "Native American", "Asian", "Unknown"]
        for table in tables:
            dfs = pd.read_html(table.get_attribute('outerHTML'))

            for df in dfs:
                if header_match(list(df.columns), expected_header):
                    data = data.append(df)
                    break

    return data

def get_us_demographic_data():
    data = {}

    source_url = "https://en.wikipedia.org/wiki/Historical_racial_and_ethnic_demographics_of_the_United_States"

    race_map = {
            "Non-Hispanic White": "white",
            "Black": "black",
            "Hispanic (of any race)": "hispanic",
            "Asian": "asian",
            "Native": "amInd",
            "Other race": "other"
            }

    if is_crawlable(source_url):
        browser.get(source_url)

        time.sleep(10)

        tables = browser.find_elements_by_tag_name("tfoot") # Why in tfoot?!?

        expected_header = ["Race/Ethnic Group", "1950", "1960", "1970", "1980", "1990", "2000", "2010"]
        for table in tables:
            tfoot_html = table.get_attribute('innerHTML')
            if tfoot_html != "":
                table_html = "<table>" + tfoot_html + "</table>"
                dfs = pd.read_html(table_html, header=0)

                for df in dfs:
                    if header_match(list(df.columns), expected_header):
                        if "%" in str(df["2010"][0]):
                            for _, row in df.iterrows():
                                race = row["Race/Ethnic Group"]
                                if race in race_map:
                                    race = race_map[race]
                                    data[race] = {}
                                    for col in df.columns:
                                        if col != "Race/Ethnic Group":
                                            if pd.notna(row[col]):
                                                data[race][col] = float(row[col].replace("%", ""))

                            # Was the table of percentages so can stop
                            return data

    return data


def main():
    us_demographics_over_time = get_us_demographic_data()
    with open("us_demographics_over_time.json", "w") as outfile:
        json.dump(us_demographics_over_time, outfile, indent=4)


    demographics = get_state_demographic_data()
    with open("demographics.json", "w") as outfile:
        json.dump(demographics, outfile, indent=4)


    inmates = get_current_death_row_data()
    inmates.to_json("inmates.json", orient="records")


    executions = get_historic_death_row_data()
    executions.to_json("executions.json", orient="records")

try:
    options = FirefoxOptions()
    options.set_headless()

    # To prevent download dialog
    profile = FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2) # custom location
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir', os.getcwd())
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/plain,text/csv,application/csv,application/download,application/octet-stream')

    browser = Firefox(profile, firefox_options=options)

    browser.implicitly_wait(15)

    main()
except Exception as e:
    print(e)
finally:
    browser.quit()

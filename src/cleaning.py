#!/usr/bin/env python
# coding: utf-8

# # ECHA: cosmetics and fragrances
#
# Here's what we need to find out:
# - Of all the substances registered under REACH, how many are used exclusively in cosmetics (i.e. in product category 28 and/or 39 only)?
# - What is the EC identification number and registered tonnage band of these substances?
# - Which of these substances have an ECHA decision associated with them?
# - What is the date, status and web address of these decisions?

# # Initial list of PC 28 and 39 substances
#
# - Used ECHA advanced searach for chemicals on 1 Apr 2021
# - Under 'Uses and exposure'
#     - Selected 'Consumer Uses'
#     - Selected categories
#         - 'PC 28' perfumes, fragrances
#         - 'PC 39' cosmetics, personal care products
#     - Selected 'OR'
# - Returned 5,821 results
# - Downloaded as CSV
import numpy as np
import pandas as pd
import re


def create_cosmetics_only_df():
    # Cleaning the JSON  files
    scrape_df = pd.read_json('~/Dropbox/echa/out_commas.json').T

    uses = scrape_df['consumer uses']

    # only keep first paragraph of uses + remove prefix
    def strip_prefix(x):
        pat = re.compile(r'[a-zA-Z ]+: (.+)')
        if m := re.match(pat, x):
            return m.group(1).rstrip('.')
        else:
            return ""
    uses = uses.map(lambda x: x[0])
    uses = uses.map(strip_prefix)

    # cosmetic only products
    filt = uses == 'cosmetics and personal care products'
    cosmetics = scrape_df[filt]


    def tonnage(x):
        pat = re.compile(r'at (.+?) per annum.?')
        if m := re.search(pat, x):
            return m.group(1)
        else:
            return ""

    cosmetics['tonnage'] = cosmetics['general'].map(lambda x: x[0]).map(tonnage)

    # uses at industrial sites
    def no_public_data(x):
        if x is np.nan:
            return x
        elif x.startswith('ECHA has no public registered data'):
            return np.nan
        else:
            return x

    industrial = cosmetics['uses at industrial sites']
    industrial = (industrial.transform(lambda x: pd.Series(x))
                  .applymap(no_public_data))[0]


    filt1 = industrial == 'This substance is used in the following products: cosmetics and personal care products.'
    filt2 = industrial.isna()

    # Merging and exporting
    #
    # - `cos_no_industry` has cosmetics with no other industrial use.
    #     - tonnage is what was reported, sometime "tonnes" was missing
    #     - tonnage is the only column we're keeping from cos_no_industry, since we were mainly interested in filtering out substances with industrial uses.
    # - perfumes and fragrances might be missing, but this is less than 30 items (I think)
    # - substances without EC number are dropped.
    # - merge with `echa_df`
    cos_no_industry = cosmetics[filt1 | filt2]

    return cos_no_industry


def get_full():
    echa_df = pd.read_csv('~/Dropbox/echa/search-export-28-39-1-apr-2021.csv', sep='\t', skiprows=3)
    echa_df.drop(columns=[echa_df.columns.to_list()[-1]], inplace=True)

    cos_no_industry = create_cosmetics_only_df()
    filt = echa_df['EC Number'] == '-'
    final = pd.merge(echa_df[~filt], cos_no_industry[['tonnage']], left_on='EC Number', right_index=True)
    final = final.reset_index(drop=True)


def write_to_excel(data_frame, file_name):
    writer = pd.ExcelWriter(file_name)
    data_frame.to_excel(writer, 'Sheet1')
    writer.save()


def get_dossier_df():
    df = pd.read_csv('~/Dropbox/echa/dossier-evaluation-status-export.csv', sep='\t', skiprows=16)
    df = df.drop(columns=['Unnamed: 13']).rename(columns={'EC / List no': 'EC Number'})
    return df

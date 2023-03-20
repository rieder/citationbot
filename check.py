"""
Python bot that checks for new publications that cite one or more articles, and
performs an action if this is the case - currently it will post a message to
Mastodon, but it could do other things too.

Original version by Hanno Rein, modified by Steven Rieder
"""

import requests
import os.path
from mastodon import Mastodon

ADS_TOKEN_FILE = "/Users/rieder/.ads/token"

with open("mastodonkeys.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()
    MASTODON_ACCESS_TOKEN, = [line.strip() for line in lines]

mastodon = Mastodon(
    access_token=MASTODON_ACCESS_TOKEN,
    api_base_url="https://botsin.space/",
)

with open(ADS_TOKEN_FILE, "r", encoding="utf-8") as f:
    token = f.read().strip()

headers = {"Authorization": "Bearer "+token}
bibcodestocheck = [
    # AMUSE articles
    "2018araa.book.....P",
    "2013CoPhC.183..456P",
    "2013A&A...557A..84P",
    "2009NewA...14..369P",
    "2011ascl.soft07007P",
]
q = "citations(bibcode:"+(") or citations(bibcode:".join(bibcodestocheck))+")"
params = {"q": q, "rows": "2000", "fl": "bibcode,pub,title,author"}
url = "https://api.adsabs.harvard.edu/v1/search/bigquery"
r = requests.get(url, headers=headers, params=params)
response = r.json()["response"]

oldcf = "oldcitations.txt"
firstrun = not os.path.isfile(oldcf)
if not firstrun:
    with open(oldcf, "r", encoding="utf-8") as f:
        oldc = f.readlines()
else:
    oldc = []
oldc = [line.strip() for line in oldc]

debug = False

i = 0
i_max = 1
for p in response["docs"]:
    bibcode = p["bibcode"]
    if bibcode not in oldc or bibcode == debug:
        if not firstrun:
            pub = p["pub"]
            title = p["title"][0]
            authors = p["author"]
            authortxt = authors[0].split(",")[0]
            if len(authors) == 2:
                authortxt += " & "+authors[1].split(",")[0]
            if len(authors) > 2:
                authortxt += " et al."
            maxlength = 400 - 25
            text = f"A new paper by {authortxt} has cited AMUSE:\n{title}"
            text = text.replace("&amp;", "&")
            if len(text) > maxlength:
                text = text[:maxlength-2] + '..'
            url = f"https://ui.adsabs.harvard.edu/abs/{bibcode}/abstract"
            text += " " + url
            text += " #amusecode #astrodon"
            # try:
            #     api.update_status(text)
            # except:
            #     print("Twitter error!")
            mastodon.status_post(text)
            if bibcode not in oldc:
                with open("summary.txt", "a", encoding="utf-8") as f:
                    print("####", file=f)
                    print(text, file=f)
                with open(oldcf, "a", encoding="utf-8") as f:
                    print(bibcode, file=f)
                i += 1
                if i >= i_max:
                    # only post a maximum of i_max articles per run
                    break

import re

from pandas import value_counts
from streamlit import emojis
from wordcloud import WordCloud

from urlextract import URLExtract
extract = URLExtract()
from collections import Counter

import pandas as pd
import emoji

# include more invisible chars WhatsApp exports can contain
_INVIS_RE = re.compile(r'[\u200e\u200f\u202a-\u202e\u2066-\u2069\ufeff]')

_OMITTED_TYPES = r"(?:image|video|gif|audio|sticker|document|documents|media)"

# allow: "document omitted", "<document omitted>", "[document omitted]", "document omitted."
_OMITTED_LINE_RE = re.compile(
    rf'^\s*[\[<]?\s*{_OMITTED_TYPES}\s+omitted\.?\s*[\]>]?\s*$',
    re.IGNORECASE
)

def normalize_omitted_messages(df):
    df = df.copy()

    def norm_one(x: str) -> str:
        x = "" if x is None else str(x)
        x = _INVIS_RE.sub("", x).strip()
        # normalize NBSP / weird whitespace
        x = " ".join(x.replace("\xa0", " ").split())

        # if it's an omitted media line -> force <OMITTED>
        if _OMITTED_LINE_RE.match(x):
            return "<OMITTED>"
        return x

    df["message"] = df["message"].apply(norm_one)
    return df

# Minimal Hinglish stopwords (add more as you like)
HINGLISH_STOPWORDS = {
    # Hindi/Hinglish common
    "hai","ha","haan","han","nahi","nahin","na","nhi","n","h","hu","hun","ho",
    "ka","ki","ke","ko","k","se","me","mein","mera","meri","mere","ter","tera","teri","tere",
    "aur","or","par","pe","bhi","bhai","toh","to","ye","yaa","ya","wo","vo","w","kya",
    "kab","kyu","kyun","kahan","idk","lol","ok","okay","hmm","acha","accha","achha",
    # English filler
    "the","a","an","and","or","but","is","am","are","was","were","be","been","being",
    "i","you","he","she","we","they","me","my","your","our","us","them"
}

WORD_RE = re.compile(r"[A-Za-z]+")  # keeps only alphabetic tokens (drops numbers/punct)

def clean_chat_df(df, remove_group_notifications=True, remove_omitted=True, stopwords=None):
    df = df.copy()

    # 1) remove group notification rows
    if remove_group_notifications:
        df = df[df["user"].astype(str).str.lower() != "group notification"]

    # 2) remove <OMITTED> rows
    if remove_omitted:
        df = df[df["message"].astype(str).str.strip() != "<OMITTED>"]

    # 3) remove hinglish stopwords (create a cleaned text column)
    if stopwords is None:
        stopwords = HINGLISH_STOPWORDS

    def strip_stopwords(msg: str) -> str:
        msg = "" if msg is None else str(msg).lower()
        tokens = WORD_RE.findall(msg)
        tokens = [t for t in tokens if t not in stopwords]
        return " ".join(tokens)

    df["message_clean"] = df["message"].apply(strip_stopwords)

    return df



def fetch_stats(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]

    # number of messages
    num_messages = df.shape[0]

    # number of words (exclude <OMITTED>)
    words = []
    for msg in df['message'].dropna():
        if msg != "<OMITTED>":
            words.extend(msg.split())

    # number of media messages (count only)
    num_media_messages = (df['message'] == "<OMITTED>").sum()

    # number of links
    links = []
    for msg in df['message'].dropna():
        links.extend(extract.find_urls(msg))

    return num_messages, len(words), num_media_messages, len(links)

def most_busy_users(df):
    x = df['user'].value_counts().head()
    df = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(columns={'index':'name', 'user': 'percent'})
    return x, df

MENTION_RE = re.compile(r"@\s*[\u2068\u200e\u200f\u202a-\u202e\u2066-\u2069]*.*?[\u2069]", re.UNICODE)

def create_wordcloud(selected_user, df):
    if selected_user != "overall":
        df = df[df["user"] == selected_user]

    # safety filters
    df = df[df["user"].str.lower() != "group notification"]
    df = df[df["message_clean"].notna()]
    df = df[df["message_clean"].str.strip() != ""]

    # build name stopwords
    name_stop = set()
    for u in df["user"].astype(str).unique():
        for part in re.findall(r"[A-Za-z]+", u.lower()):
            name_stop.add(part)

    def final_clean(s: str) -> str:
        s = "" if s is None else str(s)
        s = re.sub(r"http\S+|www\.\S+", " ", s)
        tokens = s.split()
        tokens = [t for t in tokens if t not in name_stop]
        return " ".join(tokens)

    text = df["message_clean"].apply(final_clean).str.cat(sep=" ").strip()

    if not text:
        return None

    wc = WordCloud(
        width=500,
        height=500,
        background_color="white",
        min_font_size=10,
        collocations=False   # VERY important for Hinglish
    )
    return wc.generate(text)

def most_common_words(selected_user, df_clean, top_n=20):
    # user-level filter
    if selected_user != "overall":
        df = df_clean[df_clean["user"] == selected_user]
    else:
        df = df_clean.copy()

    # drop empty text
    df = df[df["message_clean"].str.strip() != ""]

    # build name stopwords
    name_stop = set()
    for u in df["user"].astype(str).unique():
        for part in re.findall(r"[A-Za-z]+", u.lower()):
            name_stop.add(part)

    words = []
    for msg in df["message_clean"]:
        tokens = msg.split()
        tokens = [t for t in tokens if t not in name_stop]
        words.extend(tokens)

    if not words:
        return pd.DataFrame(columns=["word", "count"])

    return pd.DataFrame(
        Counter(words).most_common(top_n),
        columns=["word", "count"]
    )
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]",
    flags=re.UNICODE
)

def emoji_helper(selected_user, df):
    if selected_user != "overall":
        df = df[df["user"] == selected_user]
    emojis = []
    for msg in df["message"].dropna():
        emojis.extend(EMOJI_RE.findall(str(msg)))

    counts = Counter(emojis)
    emoji_df = pd.DataFrame(counts.most_common(), columns=["emoji", "count"])
    return emoji_df

def monthly_timeline(selected_user, df):
    if selected_user != "overall":
        df = df[df["user"] == selected_user]

    timeline = df.groupby(["year", "month", "month_num"]).count()['message'].reset_index()

    time = []
    for i in range(timeline.shape[0]):
        time.append(timeline['month'][i] + "-" + str(timeline['year'][i]))
    timeline['time'] = time

    return timeline

def daily_timeline(selected_user, df):
    if selected_user != "overall":
        df = df[df["user"] == selected_user]

    daily_timeline = df.groupby('only_date').count()['message'].reset_index()
    return daily_timeline

def week_activity_map(selected_user, df):
    if selected_user != "overall":
        df = df[df["user"] == selected_user]
    return df['day_name'].value_counts()

def month_activity_map(selected_user, df):
    if selected_user != "overall":
        df = df[df["user"] == selected_user]
    return df['month'].value_counts()

def activity_heatmap(selected_user, df):
    if selected_user != "overall":
        df = df[df["user"] == selected_user]

    user_heatmap = df.pivot_table(index="day_name", columns="period", values="message", aggfunc='count').fillna(0)
    return user_heatmap
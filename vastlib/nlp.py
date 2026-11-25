import pandas as pd
import streamlit as st
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from vastlib.load import DATA_DIR, load_mc1

STANCE_ORDER = ["hold", "speak within limits", "disclose the deal", "neutral"]
STANCE_COLORS = {"hold": "#1f7a6f", "speak within limits": "#c9a227", "disclose the deal": "#b0303c", "neutral": "#9a96a0"}
AWARENESS_ORDER = ["none", "suspects", "knows"]


@st.cache_data(show_spinner="Scoring sentiment…")
def sentiment():
    msgs, _, _ = load_mc1()
    vader = SentimentIntensityAnalyzer()
    df = msgs.copy()
    df["said"] = df["content"].apply(lambda t: vader.polarity_scores(t)["compound"])
    thinking = df[["reacting", "rationalizing", "deliberating"]].fillna("").agg(" ".join, axis=1).str.strip()
    df["thought"] = [vader.polarity_scores(t)["compound"] if t else None for t in thinking]
    df["gap"] = df["said"] - df["thought"]
    return df


@st.cache_data
def stance_labels():
    labels = pd.read_csv(DATA_DIR / "mc1_stance_labels.csv", dtype=str).fillna("")
    msgs = sentiment()
    df = labels.drop(columns=["time", "agent"]).merge(msgs, on="message_id", how="left")
    df["stance"] = pd.Categorical(df["stance"], STANCE_ORDER)
    df["deal_awareness"] = pd.Categorical(df["deal_awareness"], AWARENESS_ORDER)
    return df.sort_values("time").reset_index(drop=True)


@st.cache_data(show_spinner="Finding topics…")
def topics(n_topics=6, n_words=6):
    msgs, _, _ = load_mc1()
    text = msgs["content"].str.replace(r"@\w+", " ", regex=True)
    stop = list(ENGLISH_STOP_WORDS | {"ll", "ve", "re", "don", "just", "need", "want", "know", "going", "let"})
    vec = TfidfVectorizer(stop_words=stop, max_df=0.5, min_df=3, ngram_range=(1, 2), token_pattern=r"(?u)\b[a-zA-Z]{3,}\b")
    X = vec.fit_transform(text)
    nmf = NMF(n_components=n_topics, random_state=7, init="nndsvd", max_iter=400)
    W = nmf.fit_transform(X)
    words = vec.get_feature_names_out()
    labels = []
    for comp in nmf.components_:
        top = [words[i] for i in comp.argsort()[::-1][:n_words]]
        labels.append(", ".join(top))
    df = msgs.copy()
    df["topic_id"] = W.argmax(axis=1)
    df.loc[W.max(axis=1) == 0, "topic_id"] = -1
    df["topic"] = df["topic_id"].map(lambda i: f"T{i + 1}: {labels[i]}" if i >= 0 else "(no clear topic)")
    table = pd.DataFrame({"topic": [f"T{i + 1}" for i in range(n_topics)], "top words": labels,
                          "messages": [(df["topic_id"] == i).sum() for i in range(n_topics)]})
    return df, table

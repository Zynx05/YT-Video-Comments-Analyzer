### STEP 1: Django Skeleton + Sentiment Analysis (TextBlob)

# Install dependencies:
# pip install django pandas textblob
# python -m textblob.download_corpora

from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
from textblob import TextBlob
import requests
import pandas as pd
from urllib.parse import urlparse, parse_qs

from .models import AnalysisResult

# ... inside your for loop in analyze_comments


YOUTUBE_API_KEY = 'AIzaSyCdAvIb9DI-pCmUNzf1jvirl4PCgDjz0pQ' 

def extract_video_id(url):
    parsed = urlparse(url)
    if "youtube.com" in parsed.netloc and "v" in parse_qs(parsed.query):
        return parse_qs(parsed.query)["v"][0]
    elif "youtu.be" in parsed.netloc:
        return parsed.path.strip("/")
    elif "youtube.com" in parsed.netloc and "/shorts/" in parsed.path:
        return parsed.path.split("/shorts/")[1].split("/")[0]
    return None

def fetch_youtube_comments(video_id, max_results=100):
    comments = []
    base_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": YOUTUBE_API_KEY,
        "maxResults": 100,
        "textFormat": "plainText"
    }

    while len(comments) < max_results:
        response = requests.get(base_url, params=params)
        data = response.json()
        for item in data.get("items", []):
            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(text)
            if len(comments) >= max_results:
                break
        if "nextPageToken" in data:
            params["pageToken"] = data["nextPageToken"]
        else:
            break

    return comments

def get_sentiment_textblob(comment):
    try:
        blob = TextBlob(comment)
        polarity = blob.sentiment.polarity
        if polarity > 0:
            return "Positive", f"Positive sentiment with polarity {polarity:.2f}"
        elif polarity < 0:
            return "Negative", f"Negative sentiment with polarity {polarity:.2f}"
        else:
            return "Neutral", "Neutral sentiment"
    except Exception as e:
        return "Error", str(e)

def analyze_youtube(request):
    if request.method == "POST":
        url = request.POST.get("youtube_url")
        num_comments = int(request.POST.get("num_comments", 100))
        video_id = extract_video_id(url)

        if not video_id:
            return HttpResponse("Invalid YouTube URL.")

        comments = fetch_youtube_comments(video_id, max_results=num_comments)
        if not comments:
            return HttpResponse("No comments found or quota exceeded.")

        df = pd.DataFrame(comments, columns=["comment"])

        # Sentiment analysis
        sentiments = []
        explanations = []
        for text in df['comment'].astype(str):
            sentiment, explanation = get_sentiment_textblob(text)
            sentiments.append(sentiment)
            explanations.append(explanation)

            # Save to database
            AnalysisResult.objects.create(
                comment=text,
                sentiment=sentiment,
                explanation=explanation
            )


        df['Sentiment'] = sentiments
        df['Explanation'] = explanations

        sentiment_counts = df['Sentiment'].value_counts().to_dict()
        sentiment_percentages = {k: round((v / len(df)) * 100, 2) for k, v in sentiment_counts.items()}

        return render(request, 'results.html', {
            'counts': sentiment_counts,
            'percentages': sentiment_percentages,
            'total': len(df),
            'sample_explanations': df[['comment', 'Sentiment', 'Explanation']].values  # ✅ ALL rows
        })

    return HttpResponse("Only POST requests are supported.")


# Simple sentiment function using TextBlob
def get_sentiment_textblob(comment):
    try:
        blob = TextBlob(comment)
        polarity = blob.sentiment.polarity
        if polarity > 0:
            return "Positive", f"The comment expresses positive sentiment with polarity {polarity:.2f}."
        elif polarity < 0:
            return "Negative", f"The comment expresses negative sentiment with polarity {polarity:.2f}."
        else:
            return "Neutral", "The comment is neutral with no significant sentiment detected."
    except Exception as e:
        return "Error", str(e)


def analyze_comments(request):
    if request.method == 'POST' and request.FILES.get('comments_file'):
        file = request.FILES['comments_file']
        df = pd.read_csv(file)

        if 'comment' not in df.columns:
            return HttpResponse("CSV must contain a 'comment' column.")

        sentiments = []
        explanations = []

        for text in df['comment'].astype(str):
            sentiment, explanation = get_sentiment_textblob(text)
            sentiments.append(sentiment)
            explanations.append(explanation)

        df['Sentiment'] = sentiments
        df['Explanation'] = explanations

        sentiment_counts = df['Sentiment'].value_counts().to_dict()
        sentiment_percentages = {k: round((v / len(df)) * 100, 2) for k, v in sentiment_counts.items()}

        return render(request, 'results.html', {
            'counts': sentiment_counts,
            'percentages': sentiment_percentages,
            'total': len(df),
            'sample_explanations': df[['comment', 'Sentiment', 'Explanation']].values
        })
    return render(request, 'upload.html')

def dashboard(request):
    recent_results = AnalysisResult.objects.order_by('-timestamp')[:100]
    return render(request, 'dashboard.html', {'recent_results': recent_results})




import requests
import numpy
import nltk 
import spacy
nlp = spacy.load('en_core_web_sm')
#nltk.download('vader_lexicon')
from nltk.sentiment import vader
from nltk.sentiment.vader import SentimentIntensityAnalyzer
vader_model = SentimentIntensityAnalyzer()


api_url = 'https://api.twitter.com/2/tweets/search/recent'
bearer_token = 'AAAAAAAAAAAAAAAAAAAAAIyUagEAAAAAwJxB%2BsJcNlgKNgKMKifUDwQXng4%3DXRKHHBl5MeXoeYlDra1KYstSRKM3D3WjTsaBt2cgktFOJYplTe'

def search_twitter(query, bearer_token, results: int = 10):
    payload = {
        'query': 'lang:en '+str(query),
        'max_results': results,
        'sort_order': 'relevancy',
        'tweet.fields': 'id,text,public_metrics'
    }

    auth = {
        'Authorization': 'Bearer '+str(bearer_token)
    }

    response = requests.get(api_url, params=payload, headers=auth)
    if response.status_code != 200:
        print('Error: Status Code '+str(response.status_code))
        return
    if not 'data' in response.json().keys():
        print('Error: No tweets found')
        return
    return response.json()

def get_replies(id, bearer_token, results: int = 10):
    """
    match = re.match(r'(?:https?:\/\/)?(?:www.)?twitter.com/[^/]*/status/([0-9]*)', url)
    if not match:
        print('Error: Not a valid tweet URL')
        return
    conversation_id = match.group(1)
    """

    payload = {
        'query': 'lang:en conversation_id:'+str(id),
        'max_results': results,
        'sort_order': 'relevancy',
        'tweet.fields': 'text,public_metrics'
    }

    auth = {
        'Authorization': 'Bearer '+str(bearer_token)
    }

    response = requests.get(api_url, params=payload, headers=auth)
    if response.status_code != 200:
        print('Error: Status Code '+str(response.status_code)+': '+response.text)
        return
    if not 'data' in response.json().keys():
        print('Error: No replies found')
        return
    return response.json()

def analyze_topic(
    query, 
    bearer_token, 
    minimum_likes = 5,
    num_parents: int = 10, 
    num_replies: int = 10,
    parent_weight = 1,
    reply_weight = 1
):
    tweets = search_twitter(query, bearer_token, num_parents)
    if tweets:
        sentiments = []
        for tweet in tweets['data']:
            if tweet['public_metrics']['like_count'] >= minimum_likes:
                s = sentiment(tweet['text'])
                if s:
                    sentiments.append(
                            {
                                'sentiment': s,
                                'weight': parent_weight*(1 + tweet['public_metrics']['retweet_count'] + tweet['public_metrics']['quote_count'] + tweet['public_metrics']['like_count'])
                            }
                        )

            if num_replies:
                replies = get_replies(tweet['id'], bearer_token, num_replies)
                if replies:
                    for reply in replies['data']:
                        metrics = reply['public_metrics']
                        if metrics['like_count'] >= minimum_likes:
                            s = sentiment(reply['text'])
                            if s:
                                sentiments.append(
                                    {
                                        'sentiment': s,
                                        'weight': reply_weight*(1 + metrics['retweet_count'] + metrics['quote_count'] + metrics['like_count'])
                                    }
                                )
        weighted_average = numpy.average(
            [item['sentiment'] for item in sentiments],
            weights = [item['weight'] for item in sentiments]
        )
        return weighted_average
    
def sentiment(text):
    scores = vader_model.polarity_scores(text)
    #remove print statements. only for debugging. Should return number only
    
#     print('INPUT SENTENCE', text)
#     print('VADER OUTPUT: POS=', scores['pos'])
#     print('POS:', scores['pos'], 'NEG:', scores['neg'], 'NEU:', scores['neu'], 'COMP:', scores['compound'])

    if scores['pos'] and scores['neu'] < scores['neg']:
#         print(0)
        return 0 
    elif scores['neg'] and scores['neu'] < scores['pos']:
#         print(1)
        return 1
    elif scores['pos'] and scores['neg'] < scores['neu']:
#         print(0.5)
        return 0.5
    else:
        print('No Sentiment Found')
        return None


#code below is to implement VADER with NLTK. Doesn't work yet though.    
def run_vader(textual_unit, 
              lemmatize=False, 
              parts_of_speech_to_consider=None,
              verbose=0):

    doc = nlp(textual_unit)
        
    input_to_vader = []

    for sent in doc.sents:
        for token in sent:

            to_add = token.text

            if lemmatize:
                to_add = token.lemma_

                if to_add == '-PRON-': 
                    to_add = token.text

            if parts_of_speech_to_consider:
                if token.pos_ in parts_of_speech_to_consider:
                    input_to_vader.append(to_add) 
            else:
                input_to_vader.append(to_add)

    scores = vader_model.polarity_scores(' '.join(input_to_vader))
    
    if verbose >= 1:
        print()
        print('INPUT SENTENCE', sent)
        print('INPUT TO VADER', input_to_vader)
        print('VADER OUTPUT', scores)

    return scores
    
run_vader(text, lemmatize=True)
    
    
# Only parent tweets for now - replies works, I'm just worried abt duplicates
print(analyze_topic('"Mac Studio"', bearer_token, num_replies=100, num_parents=100))

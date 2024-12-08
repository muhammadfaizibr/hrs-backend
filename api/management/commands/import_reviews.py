import pandas as pd
from api.models import User, Place, Review
from django.conf import settings
from pathlib import Path
from django.core.management.base import BaseCommand
import random
import joblib
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize



model_path = (settings.BASE_DIR) / 'models' / 'sentiment' / 'sentiment-trained-model.sav'
vectorizer_path = (settings.BASE_DIR) / 'models' / 'sentiment' / 'tfidf-vectorizer.sav'

stemmer = PorterStemmer()


def preprocess_text(text):

    tokens = word_tokenize(text)
    stemmed = [stemmer.stem(token) for token in tokens]
    return ' '.join(stemmed)

def sentiment_to_rating(encoded_sentiment):
    if encoded_sentiment == 2:  
        return random.randint(3, 5)  
    elif encoded_sentiment == 1:  
        return 2  
    else:  
        return random.randint(1, 2)

def calculate_rating_and_analyze_sentiment(review_text):
    reviews = []
    reviews.append(review_text)
    loaded_model = joblib.load(model_path)
    loaded_vectorizer = joblib.load(vectorizer_path)
    preprocessed_reviews = [preprocess_text(comment) for comment in reviews]
    transformed_reviews = loaded_vectorizer.transform(preprocessed_reviews)
    predictions = loaded_model.predict(transformed_reviews)
    
    return sentiment_to_rating(predictions[0]), "positive" if predictions[0] == 2 else "negative" if predictions[0] == 0 else "neutral"


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        file_names = ['attractions_with_reviews.csv', 'hotels_with_reviews.csv']
        
        for file_name in file_names:
            file_path = Path(settings.BASE_DIR) / 'static/datasets' / file_name
            df = pd.read_csv(file_path, encoding = "ISO-8859-1")
            df = df.drop_duplicates(subset=['author'])
            df["predicted_rating"] = df['sentiment'].apply(lambda x: random.randint(4, 6) if x == "Positive" else (3 if x == "Neutral" else random.randint(1, 3)))

            print(df.shape)

            i = 0
            for _, row in df.iterrows():
                try:
                    place = Place.objects.get(name=row['Hotel_Name'] if file_name == 'hotels_with_reviews.csv' else row['Attraction_Name'])

                    # place.rating = (place.rating * place.number_of_reviews + row['predicted_rating']) / (place.number_of_reviews + 1)

                    place.number_of_reviews = place.number_of_reviews + 1

                    place.save()


                    rating, sentiment = calculate_rating_and_analyze_sentiment(row['Reviews'])
                    Review.objects.create(
                        user=User.objects.get(email=f"{row['author'][1:]}@gmail.com"),   
                        place=place,     
                        rating=rating,
                        review_text=row['Reviews'],
                        sentiment=sentiment,
                    )

                except Exception as e:
                    i = i + 1
                    
                
                    
            print("failed: ", i)
            print(f"Review Imported of {file_name}!")

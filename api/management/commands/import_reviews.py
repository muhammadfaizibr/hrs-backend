import pandas as pd
from api.models import User, Place, Review
from django.conf import settings
from pathlib import Path
from django.core.management.base import BaseCommand
import random

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # file_names = ['attractions_with_reviews.csv']
        file_names = ['hotels_with_reviews.csv']
        # file_names = ['hotels_data.csv', 'attractions_data.csv']
        
        for file_name in file_names:
            file_path = Path(settings.BASE_DIR) / 'static/datasets' / file_name
            df = pd.read_csv(file_path, encoding = "ISO-8859-1")
            df = df.drop_duplicates(subset=['author'])
            df["predicted_rating"] = df['sentiment'].apply(lambda x: random.randint(4, 6) if x == "Positive" else (3 if x == "Neutral" else random.randint(1, 3)))

            print(df.shape)

            i = 1
            for _, row in df.iterrows():
                # if not Review.objects.filter(user=User.objects.get(email=f"{row['author'][1:]}@gmail.com"), place=Place.objects.get(name=row['Hotel_Name'] if file_name == 'hotels_with_reviews.csv' else row['Attraction_Name']),    ).exists():
                try:
                    place = Place.objects.get(name=row['Hotel_Name']) if file_name == 'hotels_with_reviews.csv' else row['Attraction_Name']

                    Review.objects.create(
                        user=User.objects.get(email=f"{row['author'][1:]}@gmail.com"),   
                        place=Place.objects.get(name=row['Hotel_Name'] if file_name == 'hotels_with_reviews.csv' else row['Attraction_Name']),     
                        rating=row['predicted_rating'],
                        review_text=row['Reviews'],
                        sentiment=row['sentiment'].lower(),
                    )
                except Exception as e:
                    i + 1
            print("failed: ", i)
            print(f"Review Imported of {file_name}!")

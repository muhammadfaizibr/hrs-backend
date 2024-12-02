import pandas as pd
from api.models import User, Place
from django.conf import settings
from pathlib import Path
from django.core.management.base import BaseCommand

def rename_columns(file_name):
    attractions_columns = {
        'Attraction_Name': 'name',
        'publishedAt': 'published_date',
        'preprocessed_title': 'title',
        'city': 'city',
        'id': 'id',
        'email': 'contact_email',
        'phone': 'contact_phone',
        'location': 'location',
        'address': 'address',
        'image': 'image_url',
        'description_att': 'description',
        'rating': 'rating',
        'no_of_reviews': 'review_count',
        'Category': 'category',
        'ranking': 'ranking',
        'subcategories': 'subcategories',
    }
    
    hotels_columns = {
        'Hotel_Name': 'name',
        'publishedAt': 'published_date',
        'preprocessed_title': 'title',
        'City': 'city',
        'subcategories': 'subcategories',
        'Description': 'description',
        'Category': 'category',
        'email': 'contact_email',
        'phone': 'contact_phone',
        'rating': 'rating',
        'Hotel_Address': 'address',
        'ID': 'id',
        'Image_URL': 'image_url',
        'numberOfReviews': 'review_count',
        'ranking': 'ranking',
        'combined_amenities': 'amenities',
    }

    file_path = Path(settings.BASE_DIR) / 'static/datasets' / file_name
    df = pd.read_csv(file_path, encoding="ISO-8859-1")
    
    if file_name == "hotels_data.csv":
        df = df.rename(columns=hotels_columns)
    elif file_name == "attractions_data.csv":
        df = df.rename(columns=attractions_columns)
    else:
        raise ValueError("Unsupported file type. Please provide a valid file.")
    
    df.columns = df.columns.str.lower()  
    df.reset_index(drop=True, inplace=True)
    df['contact_phone'] = df['contact_phone'].replace('phone unknown', '')
    df['contact_email'] = df['contact_email'].replace('phone unknown', '')

    return df

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        file_names = ['hotels_data.csv', 'attractions_data.csv']
        
        for file_name in file_names:
            df = rename_columns(file_name)
            df = df.drop_duplicates(subset=['id'])

            for _, row in df.iterrows():
                if not Place.objects.filter(name=row['name']).exists():
                    if file_name == "attractions_data.csv":
                        Place.objects.create(
                            user=User.objects.get(id=1),
                            name=row['name'],
                            location=row['location'],
                            place_type="hotel" if file_name == "hotels_data.csv" else "attraction",
                            is_image_file=False,
                            image_url=row['image_url'],
                            email=row['contact_email'],
                            phone=row['contact_phone'],
                            address=row['address'],
                            description=row['description'],
                            rating=row['rating'],
                            number_of_reviews=row['review_count'],
                            category=row['category'],
                            ranking=row['ranking'],
                            subcategories=row['subcategories'],
                            published_at=row['published_date'],
                        )
                    else:
                        Place.objects.create(
                            user=User.objects.get(id=1),
                            name=row['name'],
                            place_type="hotel" if file_name == "hotels_data.csv" else "attraction",
                            is_image_file=False,
                            image_url=row['image_url'],
                            email=row['contact_email'],
                            phone=row['contact_phone'],
                            address=row['address'],
                            description=row['description'],
                            rating=row['rating'],
                            number_of_reviews=row['review_count'],
                            category=row['category'],
                            ranking=row['ranking'],
                            subcategories=row['subcategories'],
                            published_at=row['published_date'],
                            combined_amenities=row['amenities'] if file_name == "hotels_data.csv" else None,
                        )


            print(f"Data Imported from {file_name}!")

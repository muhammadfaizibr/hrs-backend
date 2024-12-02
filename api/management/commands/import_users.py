import pandas as pd
from api.models import User
from django.conf import settings
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        file_names = ['hotels_data.csv', 'attractions_data.csv']
        
        for file_name in file_names:
            file_path = Path(settings.BASE_DIR) / 'static/datasets' / file_name
            df = pd.read_csv(file_path, encoding = "ISO-8859-1")
            df = df.drop_duplicates(subset=['author'])
            print(df.shape)
            i = 1

            for _, row in df.iterrows():
                author = row['author'][1:]

                if not User.objects.filter(email=f"{author}@gmail.com").exists():

                    print(f"{author}@gmail.com")

                    
                    User.objects.create(
                        username=author,   
                        email=f"{author}@gmail.com",     
                        password=f"defaultuser{author}"  
                    )
                i = i + 1

            print(f"Users Imported of {file_name}!")

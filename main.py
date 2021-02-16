from os import replace
import folium
import time
import pandas as pd
from haversine import haversine as get_distance
import re
import folium.plugins as plg
import random


def get_closest_locations(location: tuple,  dataset_path='worldcities.csv'):
    '''
    Gets distance for all cities in dataset and them sorted by it
    '''
    df = pd.read_csv(dataset_path)
    df['distance'] = df.apply(lambda row: get_distance(location, (row['lat'], row['lng'])), axis=1)
    sorted_df = df.sort_values(['distance'], ascending=True)
    sorted_df.reset_index(drop=True, inplace=True)
    return sorted_df


def parse_line(line):
    '''
    '''
    try:
        address = re.search(r'\t(.*)', line).group()
        title = re.search(r'"(.*)"', line).group()
        year = re.search(r'(\d{4})', line).group()
    except AttributeError:
        return None

    # Getting city out of address line
    regions = address.split(',')
    for i in range(-3, 0):
        try:
            city = regions[i].strip()
            break
        except IndexError:
            continue

    return title, year, city


def get_movies_dict(year: str, locations_list_path='locations.list') -> dict:
    '''
    Parses locations.list and creates dict in next format:
    city: {films}
    '''
    movies = dict()
    with open(locations_list_path, 'r') as file:
        for _, line in enumerate(file):
            movie_data = parse_line(line)
            if not movie_data:
                continue
            title, filmed_year, city = movie_data
            if filmed_year == year:
                movies.setdefault(city, set()).add(title)
    return movies


def get_closest_movies(locations_df, movies):
    matches = []
    for _, row in locations_df.iterrows():
        if len(matches) >= 40:
            return matches
        city = row['city']
        filtered_films = list(movies.get(city, []))
        if len(filtered_films) > 0:
            for film in filtered_films:
                matches.append((city, film))
    return matches


def random_deviation():
    return random.randint(0, 1000) / 100000


def create_map(location, closest_movies):
    map = folium.Map(location=list(location), zoom_start=10)

    folium.Marker(location=list(location), icon=folium.Icon(color="orange", icon="home")).add_to(map)

    clusters = dict()
    for movie in closest_movies:
        city_row = locations_df[locations_df['city'] == movie[0]][['lat', 'lng']]
        lat, lng = city_row.iloc[0]

        lat += random_deviation()
        lng += random_deviation()

        clusters[movie[0]] = city_cluster = clusters.get(movie[0], plg.MarkerCluster())

        folium.Marker(
            location=[lat, lng],
            radius=10, popup=movie[1],
        ).add_to(city_cluster)

    for cluster in clusters.values():
        cluster.add_to(map)

    map.save('Result.html')


if __name__ == '__main__':
    # year = '2003'
    # location = (42.3584300, -71.0597700)

    year = input('Enter creation year: ')

    location = input('Enter location (example: 42.3584300, -71.0597700): ')
    location = tuple(map(float, location.split(',')))

    print('Generating map...')

    start_time = time.time()
    locations_df = get_closest_locations(location)
    movies = get_movies_dict(year)
    closest_movies = get_closest_movies(locations_df, movies)

    create_map(location, closest_movies)

    print(f'--- {time.time() - start_time} seconds ---')

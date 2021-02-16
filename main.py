import folium
import time
import pandas as pd
from haversine import haversine
import re
import folium.plugins as plg
import random


def get_closest_locations(location: tuple,  dataset_path='worldcities.csv'):
    '''
    Returns cities sorted by distance between them and the location
    '''
    df = pd.read_csv(dataset_path)
    df['distance'] = df.apply(lambda row: haversine(location, (row['lat'], row['lng'])), axis=1)
    sorted_df = df.sort_values(['distance'], ascending=True)
    sorted_df.reset_index(drop=True, inplace=True)
    return sorted_df


def parse_line(line: str) -> tuple:
    '''
    Returns parsed line in
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
    Parses locations.list and creates dict in following format:
    {city: {films}}
    '''
    movies = dict()
    with open(locations_list_path, 'r') as file:
        for line in file:
            movie_data = parse_line(line)
            if not movie_data:
                continue
            title, filmed_year, city = movie_data
            if filmed_year == year:
                movies.setdefault(city, set()).add(title)
    return movies


def get_closest_movies(locations_df, movies) -> list:
    '''
    Returns movies that are filmed in nearest locations
    '''
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


def random_deviation() -> float:
    return random.randint(0, 1000) / 100000


def create_map(location, closest_movies):
    '''
    Creates and saves map
    '''
    map = folium.Map(location=list(location), zoom_start=10)

    folium.Marker(location=list(location), icon=folium.Icon(color="orange", icon="home")).add_to(map)

    clusters = dict()
    for movie in closest_movies:
        city_row = locations_df[locations_df['city'] == movie[0]][['lat', 'lng']]
        lat, lng = city_row.iloc[0]

        lat += random_deviation()
        lng += random_deviation()

        clusters[movie[0]] = city_cluster = clusters.get(
            movie[0], ((lat, lng), plg.MarkerCluster()))

        folium.Marker(
            location=[lat, lng],
            radius=10, popup=movie[1],
        ).add_to(city_cluster[1])

    points = folium.FeatureGroup(name='points')
    polylines = folium.FeatureGroup(name='polylines')
    for point_location, cluster in clusters.values():
        folium.PolyLine([location, point_location], color="red", weight=1.5, opacity=1).add_to(polylines)
        cluster.add_to(points)

    points.add_to(map)
    polylines.add_to(map)
    map.add_child(folium.LayerControl())
    map.save('Result.html')


if __name__ == '__main__':

    year = input('Please enter a year you would like to have a map for: ')

    location = input('Please enter your location (format: lat, long): ')
    location = tuple(map(float, location.split(',')))

    print('Generating map...')

    start_time = time.time()
    locations_df = get_closest_locations(location)
    movies = get_movies_dict(year)
    closest_movies = get_closest_movies(locations_df, movies)

    create_map(location, closest_movies)
    print('Finished!')
    print(f'--- {time.time() - start_time} seconds ---')

from flask import Flask, render_template
import folium
from folium import IFrame
import pandas as pd
import psycopg
import pandas as pd
from folium.map import CustomPane
import json
import os
import requests

conn = psycopg.connect(
    host="localhost",
    port='5432',
    dbname="5400",
    user="postgres",
    password="123")

app = Flask(__name__)

@app.route('/')
def about():
    return render_template('about.html')

@app.route('/youcompare_rent')
def youcompare_rent():
    # ... (code for fetching data, creating map, and saving map)
    cur = conn.cursor()

    # Retrieve data from PostgreSQL table
    cur.execute("""SELECT * FROM zillow""")
    rows = cur.fetchall()
    merged_df = pd.DataFrame(rows, columns=['id','city','region_name','borough','neighborhood','avg_rentalprice_2022','recent_rental_price','normalized','latitude','longitude','area_rating'])
    # Create map
    nyc_coordinates = [40.7128, -74.0060]
    nyc_map = folium.Map(location=nyc_coordinates, zoom_start=11)

    boroughs = merged_df['borough'].unique().tolist()

    # Define leveling through different colors
    def get_color(area_rating):
        if area_rating == 'A':
            return "lightblue"  # Pastel blue
        elif area_rating == 'B':
            return "lightgreen"  # Pastel green
        elif area_rating == 'C':
            return "pink"  # Pastel pink
        else:
            return "gray"  # Light gray (default color for other ratings)

        # Markers creation and add to map
    for borough in boroughs:
        borough_df = merged_df[merged_df['borough'] == borough]

        for index, row in borough_df.iterrows():

            info = f"""
            <style>
                @import url(static/fonts/font-awesome-4.7.0/css/font-awesome.min.css);
            p {{
                font-size: 16px;
                font-family: Arial;
            }}
            .info_label {{
                color: black;
                font-weight: bold;
            }}
            .info_value {{
                color: blue;
            }}
        </style>
        <p><span class="info_label">Borough:</span> <span class="info_value">{row['borough']}</span></p>
        <p><span class="info_label">Neighborhood:</span> <span class="info_value">{row['neighborhood']}</span></p>
        <p><span class="info_label">Zipcode:</span> <span class="info_value">{row['region_name']}</span></p>
        <p><span class="info_label">Average Rental Price 2022:</span> <span class="info_value">${row['avg_rentalprice_2022']:.2f}</span></p>
        <p><span class="info_label">Recent Rental Price:</span> <span class="info_value">${row['recent_rental_price']:.2f}</span></p>
        <p><span class="info_label">Affordability Rating:</span> <span class="info_value">{row['area_rating']}</span></p>
        """

            iframe = IFrame(html=info, width=300, height=200)
            popup = folium.Popup(iframe, max_width=300)

            marker = folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=popup,
                icon=folium.Icon(color=get_color(row['area_rating']), icon="home", prefix="fa")
            )
            marker.add_to(nyc_map)

    # Get the map HTML string
    map_html = nyc_map._repr_html_()
    
    return render_template('youcompare_rent.html', map_html=map_html)


@app.route('/youcompare_convenience')
def youcompare_convenience():
    # Retrieve data from PostgreSQL table
    cur2 = conn.cursor()
    cur2.execute("""SELECT * FROM borough_311""")
    rows2 = cur2.fetchall()
    df = pd.DataFrame(rows2, columns=['borough', 'num_complaints', 'top3_complaints', 'grading'])
    print(df.info())

    # Load the GeoJSON file
    with open('nyc_boroughs.geojson', 'r') as file:
        nyc_boroughs_geojson = json.load(file)
    
    # Create a Folium map
    nyc_map2 = folium.Map(location=[40.7128, -74.0060], zoom_start=10)

    # Create a pandas DataFrame with the boroughs and their values
    borough_data = pd.DataFrame([
        {'name': 'Manhattan', 'value': 1},
        {'name': 'Brooklyn', 'value': 2},
        {'name': 'Queens', 'value': 3},
        {'name': 'The Bronx', 'value': 4},
        {'name': 'Staten Island', 'value': 5}
    ])

    # Add choropleth layer
    choropleth = folium.Choropleth(
        geo_data=nyc_boroughs_geojson,
        data=borough_data,
        columns=['name', 'value'],
        key_on='feature.properties.boro_name',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Choropleth Map of NYC Boroughs'
    ).add_to(nyc_map2)

    tooltip_data = df.set_index('borough').to_dict(orient='index')

    for feature in nyc_boroughs_geojson['features']:
        boro_name = feature['properties']['boro_name']
        if boro_name in tooltip_data:
            feature['properties'].update(tooltip_data[boro_name])

    folium.features.GeoJsonTooltip(
        fields=['boro_name', 'num_complaints', 'top3_complaints', 'grading'],
        aliases=['Borough:', 'Total Complaints:', 'Top Three Complaints:', 'Grading:'],
        localize=True
    ).add_to(choropleth.geojson)

    # Get the map HTML string
    map_html2 = nyc_map2._repr_html_()

    # Render the template with the map HTML string
    return render_template('youcompare_convenience.html', map_html2=map_html2)


if __name__ == '__main__':
    app.run(debug=True)


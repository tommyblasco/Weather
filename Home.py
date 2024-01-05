import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from meteostat import Point, Daily
from geopy.geocoders import Nominatim
from country_list import countries_for_language
import requests

st.header("The climate change")
st.subheader("Historical weather data from all over the world")

oggi = datetime.now()
countr = [x[1] for x in countries_for_language('en')]
paese = st.selectbox('Choose a country',countr)
citta = st.text_input('Write a city',placeholder='Here, in english')
span = st.radio('Temporal Range',['1W','1M','6M','1Y','5Y','10Y','Max','Custom'],horizontal=True)
if span=='Custom':
    ran_date=st.date_input("Select an interval",(datetime(oggi.year,1,1),oggi),datetime(1900,1,1),oggi,format="YYYY-MM-DD")

geolocator = Nominatim(user_agent="abcd")

city = f'{citta}, {paese}'
try:
    if len(citta)>0:
        address=geolocator.geocode(city)
        lat=address.latitude
        lon=address.longitude
        url = f"https://api.opentopodata.org/v1/aster30m?locations={lat},{lon}"
        r = requests.get(url)

        data = r.json()
        elev=data['results'][0]['elevation']

        # Set time period
        end = oggi
        if span=='1W':
            start = oggi-relativedelta(weeks=1)
        elif span=='1M':
            start = oggi-relativedelta(months=1)
        elif span=='6M':
            start = oggi-relativedelta(months=6)
        elif span=='1Y':
            start = datetime(oggi.year-1,oggi.month,oggi.day)
        elif span=='5Y':
            start = datetime(oggi.year-5,oggi.month,oggi.day)
        elif span=='10Y':
            start = datetime(oggi.year-10,oggi.month,oggi.day)
        elif span=='Max':
            start = datetime(1900,1,1)
        else:
            start = ran_date[0]
            end = ran_date[1]

        # Create Point
        citta = Point(lat, lon,elev)

        # Get daily data
        data = Daily(citta, start, end)
        df_temp = data.fetch()
        df_temp = df_temp.rename(columns={'tavg':'Average','tmax':'Temp Max','tmin':'Temp Min'})

        st.text('Temperatures over the selected period:')
        col1, col2=st.columns([0.15,0.85])
        with col1:
            tmp_type=st.multiselect('Choose what you wanna see',['Average','Temp Max','Temp Min'],['Average'])
            agg_type=st.radio('Type of aggregation:',['By Day','By Month','By Year'])
        with col2:
            df_temp['Day']=df_temp.index
            if agg_type=='By Month':
                df_temp['ym']=[str(x.year)+'{:02d}'.format(x.month) for x in df_temp['Day']]
                df_to_plot = df_temp.groupby('ym',as_index=False).agg({'Average':'mean','Temp Max':'mean','Temp Min':'mean'})
                df_to_plot = df_to_plot[tmp_type]
                st.line_chart(df_to_plot,x='ym',y=tmp_type)
            elif agg_type=='By Year':
                df_temp['year']=[x.year for x in df_temp['Day']]
                df_to_plot = df_temp.groupby('year',as_index=False).agg({'Average':'mean','Temp Max':'mean','Temp Min':'mean'})
                df_to_plot = df_to_plot[tmp_type]
                st.line_chart(df_to_plot,x='year',y=tmp_type)
            else:
                df_to_plot = df_temp[tmp_type]
                st.line_chart(df_to_plot)

        st.text('Where we are:')
        st.map(pd.DataFrame({'Lat':[lat],'Lon':[lon]}),latitude='Lat',longitude='Lon',zoom=6,color='#FF0000')
except:
    st.error("Error: city not found!")
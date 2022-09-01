import streamlit as st 
import pandas as pd 
import datetime, duckdb
import plotly.graph_objs as go
import numpy as np



@st.experimental_memo(ttl=12*3600)
def load_data():
    
    data_2021 = pd.read_csv('2021.csv')
    data_2020 = pd.read_csv('2020.csv')
    data_2019 = pd.read_csv('2019.csv')
    
    #for d in [data_2019, data_2020, data_2021]: d['DayOfYear']=d['DayOfYear'].astype('str')
    
    #df = pd.read_excel('https://www.swissgrid.ch/dam/dataimport/energy-statistic/EnergieUebersichtCH-2022.xlsx', sheet_name='Zeitreihen0h15') # or Zeitreihen1h00
    #data_2022 = process_data(df, date_is_str=True)
    
    data_2022 = pd.read_csv('2022.csv')

    return data_2022, data_2021, data_2020, data_2019


st.set_page_config(page_title="Swiss Energy Prices", layout="centered")

with st.sidebar:
    st.markdown(f'### Swiss Energy Usage and Prices Information')

data_2022, data_2021, data_2020, data_2019 = load_data()


last_day = list(data_2022['Date'].tail(1))[0]
last_day = datetime.datetime.strptime(last_day, r'%Y-%m-%d %H:%M:%S')
first_day = datetime.datetime(year=2022, month=1, day=1)

max_days = (last_day - first_day).days

date_range = st.slider("Please choose a date range", 0, max_days, value=(0, max_days), format="")

range_start = datetime.datetime.strftime(first_day + datetime.timedelta(days=date_range[0]), '%B %d')
range_end = datetime.datetime.strftime(first_day + datetime.timedelta(days=date_range[1]), '%B %d')

st.markdown(f"{range_start} to {range_end}")

from_day = datetime.datetime.strftime(first_day + datetime.timedelta(days=date_range[0]), '%m/%d')
to_day = datetime.datetime.strftime(first_day + datetime.timedelta(days=date_range[1]), '%m/%d')

fig = go.Figure()




agg_field= 'DayOfYear'

agg_target = st.selectbox(label='Price type', options=['APSCEP', 'ANSCEP', 'APTCEP', 'ANTCEP'], \
    format_func=lambda _:{'APSCEP': 'Positive Secondary', 'ANSCEP': 'Negative Seconday', 'APTCEP': 'Positive Tertiary', 'ANTCEP': 'Negative Tertiary'}[_])

interpolate = st.checkbox(label='Interpolate zero and missing values', value=True)

for year,data in {'2019':data_2019, '2020':data_2020, '2021':data_2021, '2022':data_2022}.items():
    
    result = duckdb.query(f'select {agg_field}, Median({agg_target}) as Price, Min({agg_target}) as "Min Price", Max({agg_target}) as "Max Price" \
         from data where {agg_field}<=\'{to_day}\' and {agg_field}>=\'{from_day}\'  group by {agg_field} order by {agg_field} asc').to_df()
    if interpolate: result['Price'] = result['Price'].apply(lambda n: np.nan if n==0 else n).interpolate(method='linear')
    #fig.add_trace(go.Scatter(x=result[agg_field],  y=result['Min Price'] , name=f"{year}", mode='lines', fill=None , showlegend=False))
    #fig.add_trace(go.Scatter(x=result[agg_field],  y=result['Max Price'] , name=f"{year}", mode='lines', fillcolor='rgba(68, 68, 68, 0.3)',fill='tonexty',showlegend=False ))
    fig.add_trace(go.Scatter(x=result[agg_field],  y=result['Price'] , name=f"{year}", mode='lines'))


st.plotly_chart(fig, use_container_width=True)
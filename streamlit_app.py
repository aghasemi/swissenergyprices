import streamlit as st 
import pandas as pd 
import datetime, duckdb
import plotly.graph_objs as go
import numpy as np



@st.cache
def load_data():
    
    data_2021 = pd.read_csv('2021.csv')
    data_2020 = pd.read_csv('2020.csv')
    data_2019 = pd.read_csv('2019.csv')
    
    #for d in [data_2019, data_2020, data_2021]: d['DayOfYear']=d['DayOfYear'].astype('str')
    
    #df = pd.read_excel('https://www.swissgrid.ch/dam/dataimport/energy-statistic/EnergieUebersichtCH-2022.xlsx', sheet_name='Zeitreihen0h15') # or Zeitreihen1h00
    #data_2022 = process_data(df, date_is_str=True)
    
    data_2022 = pd.read_csv('2022.csv')

    return data_2022, data_2021, data_2020, data_2019


st.set_page_config(page_title="Swiss Energy Prices", layout="wide")

with st.sidebar:
    st.markdown('##### About')
    st.markdown(f'This dashboard visualises energy prices in Switzerland using [SwissGrid Energy Statistics](https://www.swissgrid.ch/en/home/customers/topics/energy-data-ch.html) published publicly. '+
      "\n\nData are available in granularity of 15 minutes, which we then aggregate per day. "
    + "\n\nThe prices we visualise are those of the [control power markets](https://www.swissgrid.ch/en/home/operation/market/control-energy.html) namely secondary and tertiary control energy prices. "
    + "Hopefully, these measures can act as proxy to the actual consumer price that is not published by SwissGrid. "
    + "\n\nFeel free to [contact me](https://twitter.com/a_ghasemi) if you have ideas to improve this.")

data_2022, data_2021, data_2020, data_2019 = load_data()


st.title(f'Swiss Energy Usage and Prices Information')


st.markdown(f'##### Dates')

last_day = list(data_2022['Date'].tail(1))[0]
last_day = datetime.datetime.strptime(last_day, r'%Y-%m-%d %H:%M:%S')
first_day = datetime.datetime(year=2022, month=1, day=1)

max_days = (last_day - first_day).days

date_range = st.slider("Date range", 0, max_days, value=(0, max_days), format="")

range_start = datetime.datetime.strftime(first_day + datetime.timedelta(days=date_range[0]), '%B %d')
range_end = datetime.datetime.strftime(first_day + datetime.timedelta(days=date_range[1]), '%B %d')

st.markdown(f"Showing _{range_start}_ to _{range_end}_")

from_day = datetime.datetime.strftime(first_day + datetime.timedelta(days=date_range[0]), '%m/%d')
to_day = datetime.datetime.strftime(first_day + datetime.timedelta(days=date_range[1]), '%m/%d')




st.markdown('##### Target')

agg_field= 'DayOfYear'

price_types = {'APSCEP': 'Positive Secondary', 'ANSCEP': 'Negative Seconday', 'APTCEP': 'Positive Tertiary', 'ANTCEP': 'Negative Tertiary'}
price_types = {k:v+' Control Energy Price' for k,v in price_types.items()}
agg_target = st.selectbox(label='Price type', options=['APSCEP', 'ANSCEP', 'APTCEP', 'ANTCEP'], \
    format_func=lambda _:price_types[_])


agg_fn = st.selectbox(label='Aggregate to daily', options=['Median', 'AVG', 'Min', 'Max'])

interpolate = st.checkbox(label='Interpolate zero and missing values', value=True)
smooth = st.checkbox(label='7-day moving average', value=False)


st.markdown('##### Years')
cols =  st.columns((1,1,1,1))

show_2019 = cols[0].checkbox(label='Show 2019 data', value=True)
show_2020 = cols[1].checkbox(label='Show 2020 data', value=True)
show_2021 = cols[2].checkbox(label='Show 2021 data', value=True)
show_2022 = cols[3].checkbox(label='Show 2022 data', value=True)

years = {} #{'2019':data_2019, '2020':data_2020, '2021':data_2021, }

if show_2019: years['2019'] = data_2019
if show_2020: years['2020'] = data_2020
if show_2021: years['2021'] = data_2021
if show_2022: years['2022'] = data_2022

fig = go.Figure()
for year,data in years.items():
    
    result = duckdb.query(f'select {agg_field}, {agg_fn}({agg_target}) as Price, Min({agg_target}) as "Min Price", Max({agg_target}) as "Max Price" \
         from data where {agg_field}<=\'{to_day}\' and {agg_field}>=\'{from_day}\'  group by {agg_field} order by {agg_field} asc').to_df()
    if interpolate: result['Price'] = result['Price'].apply(lambda n: np.nan if n==0 else n).interpolate(method='linear')
    if smooth: 
        result['Smooth Price'] = result['Price'].rolling(7).mean()
        fig.add_trace(go.Scatter(x=result[agg_field],  y=result['Smooth Price'] , name=f"{year}", mode='lines', opacity=1.0))

    #fig.add_trace(go.Scatter(x=result[agg_field],  y=result['Min Price'] , name=f"{year}", mode='lines', fill=None , showlegend=False))
    #fig.add_trace(go.Scatter(x=result[agg_field],  y=result['Max Price'] , name=f"{year}", mode='lines', fillcolor='rgba(68, 68, 68, 0.3)',fill='tonexty',showlegend=False ))
    fig.add_trace(go.Scatter(x=result[agg_field],  y=result['Price'] , name=f"{year}", mode='lines', opacity=0.1 if smooth else 1.0, showlegend= not smooth))

fig.update_layout(
    title=f"Price of the SwissGrid {price_types[agg_target]} between {range_start} and {range_end} ",
    xaxis_title="Day of Year",
    yaxis_title="Price",
    legend_title="Year",
    font=dict(
        family="Helvetica, monospace",
        #size=16,
        #color="RebeccaPurple"
    )
)
st.plotly_chart(fig, use_container_width=True)

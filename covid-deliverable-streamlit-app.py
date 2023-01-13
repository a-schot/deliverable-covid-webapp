import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine

POSTGRES_CONNECTION_STRING = st.secrets["POSTGRES_CONNECTION_STRING"]

@st.cache()
def load_covid_data(connection):
    """Loading COVID-19 data..."""
    engine = create_engine(connection)
    return pd.read_sql_query(
        """
        select municipality_name, date(date_of_publication), total_reported, deceased from covid.municipality_totals_daily mtd
        where municipality_name in ('Amsterdam', 'Rotterdam', 'Groningen')
        and extract(year from mtd.date_of_publication) = 2022
        order by municipality_name, date(date_of_publication);
        """,
        con=engine,
    )


@st.cache()
def load_review_data(connection):
    """Loading Deliverable review data..."""
    engine = create_engine(connection)
    return pd.read_sql_query(
        """
        select rest.location_city, date(r.datetime), count(*),
        AVG(r.rating_delivery) as rating_delivery,
        AVG(r.rating_food) as rating_food
        from reviews r
        join restaurants rest using(restaurant_id)
        where rest.location_city in ('Amsterdam', 'Rotterdam', 'Groningen')
        and extract(year from r.datetime) = 2022
        group by rest.location_city, date(r.datetime)
        order by rest.location_city, date(r.datetime);
        """,
        con=engine,
    )


df_case = load_covid_data(connection=POSTGRES_CONNECTION_STRING)
df_rev = load_review_data(connection=POSTGRES_CONNECTION_STRING)

st.title("COVID-19 cases and number of orders per day")

covid_check = st.checkbox("Show raw COVID-19 data")
if covid_check:
    st.dataframe(df_case)

order_check = st.checkbox("Show raw Deliverable review data")
if order_check:
    st.dataframe(df_rev)

start_date, end_date = st.slider("Select timeframe", value=(min(df_case.date), max(df_case.date)))
df_case_filtered = df_case.loc[(df_case.date >= start_date) & (df_case.date <= end_date)]
df_rev_filtered = df_rev.loc[(df_rev.date >= start_date) & (df_rev.date <= end_date)]

fig2 = px.line(
    df_case_filtered,
    x="date",
    y="total_reported",
    color="municipality_name",
    title="COVID-19 cases per day (2022)",
    labels={"date": "2022", "total_reported": "Cases", "municipality_name": "City"},
)

fig2.update_xaxes(dtick="M1", tickformat="%b", ticklabelmode="period")

st.plotly_chart(fig2)

fig1 = px.line(
    df_rev_filtered,
    x="date",
    y="count",
    color="location_city",
    title="Number of orders per day (2022)",
    labels={"date": "2022", "count": "Orders", "location_city": "City"},
)

fig1.update_xaxes(dtick="M1", tickformat="%b", ticklabelmode="period")

st.plotly_chart(fig1)

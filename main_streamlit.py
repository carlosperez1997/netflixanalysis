import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
import seaborn as sns

from datetime import date
from datetime import datetime

import streamlit as st
import os
import io
from io import BytesIO, StringIO
from typing import Union

#global year_chosen


def clean_and_prepare_data (netflix_vh):
    netflix_vh = netflix_vh.dropna()
    netflix_hist = netflix_vh.copy()

    netflix_hist.loc[:,'Date'] = pd.to_datetime( netflix_vh.loc[:,'Date'] )
    first_day = min(netflix_hist['Date'])
    last_day = max(netflix_hist['Date'])

    netflix_hist.set_index('Title', inplace=True)
    netflix_hist.loc[:,"is_TV_show"] = False
    
    for lab, row  in netflix_hist.iterrows():
        title = str(lab)
        is_TVshow = ['Temporada' in title, 'Season' in title, 'Serie' in title, 'Miniserie' in title, 'Capítulo' in title, 'Episode' in title, 'Parte' in title, 'Spartacus: Sangre y Arena​:' in title]    
        netflix_hist.loc[lab, "is_TV_show"] = max(is_TVshow)
 
    return netflix_hist, first_day, last_day


def TV_shows_ranking_plot(netflix_hist):
    TV_shows = netflix_hist[ netflix_hist["is_TV_show"] == True ]
    TV_shows = TV_shows.reset_index()
    TV_shows["TV_show"] = TV_shows["Title"].str.split(':',expand=True)[0]

    TV_show_unique = TV_shows["TV_show"].unique()

    TVshow_groupby = TV_shows.groupby(by='TV_show').agg(['sum','count'])

    TVshow_groupby = TVshow_groupby["duration"]

    TVshow_groupby = TVshow_groupby.sort_values('sum', ascending=False) 
    TVshow_groupby['duration_hours'] = TVshow_groupby['sum']/60

    most_watched = TVshow_groupby.head(10)

    return most_watched


def plot_most_watched (most_watched):

    st.write("""
    ## Top 10 TV shows most watched

    These are the TOP 10 TV shows you have most watched. 
    """)
    
    st.dataframe(most_watched[['count','duration_hours']].rename(columns={'count': 'Number of episodes', 'duration_hours' : 'Duration in hours' }))

    fig, ax = plt.subplots(1,1, figsize=(12,4))
    plt.barh(most_watched.index, most_watched['duration_hours'])
    plt.xlabel('Watched hours')

    return fig


def add_duration(netflix_hist, TV_show_duration, film_duration):
    netflix_hist.loc[ netflix_hist['is_TV_show'] == True, "duration"] = TV_show_duration
    netflix_hist.loc[ netflix_hist['is_TV_show'] == False, "duration"] = film_duration

    return netflix_hist


def summary (netflix_hist, first_day, last_day):
    st.write("## Overall Analysis")
    st.write(" Since the first day with a log in " + str(first_day.day) + '/' + str(first_day.month) + '/' + str(first_day.year) + ' until the last day with a log in ' + str(last_day.day) + '/' + str(last_day.month) + '/' + str(last_day.year) + '...' )
    st.write("  *  You have watched {:.0f} hours ".format(netflix_hist["duration"].sum()/60))
    st.write("  *  {:.0f} hours correspond to {:.0f} of days ".format(netflix_hist["duration"].sum()/60, netflix_hist["duration"].sum()/60/24))
    st.write("  *  And {:.0f} days to {:.2f} months".format(netflix_hist["duration"].sum()/60/24, netflix_hist["duration"].sum()/60/24/30))


def plot_year_month(netflix_hist, first_day, last_day):
    netflix_hist["month"] = netflix_hist["Date"].dt.month
    netflix_hist["year"] = netflix_hist["Date"].dt.year
    netflix_hist["weekday"] = netflix_hist["Date"].dt.weekday
    month_year_groupby = netflix_hist.groupby(by=['month','year']).sum()

    month_year_groupby['duration_hours'] = month_year_groupby['duration'] / 60

    month_year_groupby = month_year_groupby.reset_index(level=['month','year'])

    first_year = first_day.year
    last_year = last_day.year
    years = np.arange(first_year, last_day.year + 1)

    for year in years:
        for month in np.arange(1,13):
            months_list = list(month_year_groupby.loc[month_year_groupby["year"]==year]["month"])
            bool_m = month in months_list
            if bool_m == False:
                month_year_groupby = month_year_groupby.append( {"month":int(month), "year":int(year), "is_TV_show":0, "duration":0, "duration_hours":0}, ignore_index = True)

    month_year_groupby["year"] = month_year_groupby["year"].astype("int")

    month_names = pd.DataFrame([[1,"Jan"],[2,"Feb"],[3,"Mar"],[4,"Apr"],[5,"May"],[6,"Jun"],[7,"Jul"],[8,"Aug"],[9,"Sep"],[10,"Oct"],[11,"Nov"],[12,"Dec"]], columns=['month','month_name'])

    month_year_groupby = pd.merge(month_year_groupby, month_names, on='month')
    month_year_groupby['month-year'] = ["{}-{}".format(m, y) for m, y in zip(month_year_groupby['month_name'], month_year_groupby['year'])]

    month_year_groupby = month_year_groupby.sort_values(['year','month'])

    fig, ax = plt.subplots(figsize=(18,6))
    _ = sns.barplot(x='month-year', y='duration_hours', ax = ax, hue='year', data=month_year_groupby, dodge=False)

    change_width(_, .87)

    plt.xticks(rotation='vertical')
    plt.ylabel('Watched hours')
    plt.title('Distribution of watched hours across months')
    plt.xlabel('')
    
    return fig, month_year_groupby


def fill_quarter_info (quarter_year_info, first_day, last_day):

    quarter_names = {1:"Q1", 2:"Q2", 3:"Q3", 4:"Q4"}

    first_year = first_day.year
    last_year = last_day.year
    years = np.arange(first_year, last_day.year + 1)

    for year in years:
        for quarter in np.arange(1,5):
            quarters_list = list(quarter_year_info.loc[quarter_year_info["year"]==year]["quarter_id"])
            bool_m = quarter in quarters_list
            if bool_m == False:
                quarter_year_info = quarter_year_info.append( {"quarter_id":int(quarter), "year":int(year), "duration":0, "duration_hours":0}, ignore_index = True)

    quarter_year_info["quarter"] = quarter_year_info["quarter_id"].replace(quarter_names)
    quarter_year_info = quarter_year_info.reset_index()
    quarter_year_info['quarter-year'] = ["{}-{}".format(m, y) for m, y in zip(quarter_year_info['quarter'], quarter_year_info['year'])]
    quarter_year_info = quarter_year_info.set_index('quarter-year')

    quarter_year_info = quarter_year_info.sort_values(['year','quarter_id'])

    return quarter_year_info


def plot_year_quarter(netflix_hist, first_day, last_day):
    netflix_hist["month"] = netflix_hist["Date"].dt.month
    netflix_hist["year"] = netflix_hist["Date"].dt.year
    month_year_groupby = netflix_hist.groupby(by=['month','year']).sum()

    month_year_groupby['duration_hours'] = month_year_groupby['duration'] / 60

    month_year_groupby = month_year_groupby.reset_index(level=['month','year'])

    for year in month_year_groupby["year"].unique():
        for month in np.arange(1,13):
            months_list = list(month_year_groupby.loc[month_year_groupby["year"]==year]["month"])
            bool_m = month in months_list
            if bool_m == False:
                month_year_groupby = month_year_groupby.append( {"month":int(month), "year":int(year), "is_TV_show":0, "duration":0, "duration_hours":0}, ignore_index = True)

    month_year_groupby["year"] = month_year_groupby["year"].astype("int")

    quarter_names = pd.DataFrame([[1,"Q1"],[2,"Q1"],[3,"Q1"],[4,"Q2"],[5,"Q2"],[6,"Q2"],[7,"Q3"],[8,"Q3"],[9,"Q3"],[10,"Q4"],[11,"Q4"],[12,"Q4"]], columns=['month','quarter'])

    quarter_year_groupby = pd.merge(month_year_groupby, quarter_names, on='month')

    quarter_year_groupby = quarter_year_groupby.groupby(by = ['year','quarter']).sum()

    quarter_year_groupby = quarter_year_groupby.reset_index()

    quarter_year_groupby['quarter-year'] = ["{}-{}".format(m, y) for m, y in zip(quarter_year_groupby['quarter'], quarter_year_groupby['year'])]

    quarter_year_groupby = quarter_year_groupby.sort_values(['year','quarter'])

    fig, ax = plt.subplots(figsize=(18,6))
    _ = sns.barplot(x='quarter-year', y='duration_hours', ax = ax, hue='year', data=quarter_year_groupby, dodge=False)

    change_width(_, .87)

    plt.xticks(rotation='vertical')
    plt.ylabel('Watched hours')
    plt.title('Distribution of watched hours across quarters of the year')
    plt.xlabel('')
    
    return fig, quarter_year_groupby


def distribution_quarter_year(netflix_hist, quarter_year_groupby):
    quarter_code = pd.DataFrame([[1,1],[2,1],[3,1],[4,2],[5,2],[6,2],[7,3],[8,3],[9,3],[10,4],[11,4],[12,4]], columns=['month','quarter_id'])
    netflix_hist_ = netflix_hist.reset_index()
    netflix_hist_ = pd.merge(netflix_hist_, quarter_code, on='month')
    netflix_hist_ = netflix_hist_.set_index('Title')

    quarter_year_type_groupby = netflix_hist_.groupby(by=['year','quarter_id','is_TV_show']).sum()
    quarter_year_type_groupby['duration_hours'] = quarter_year_type_groupby['duration'] / 60
    quarter_year_type_groupby = quarter_year_type_groupby.reset_index()


    quarter_year_TV_show = quarter_year_type_groupby[ quarter_year_type_groupby["is_TV_show"] == True]
    quarter_year_film = quarter_year_type_groupby[ quarter_year_type_groupby["is_TV_show"] == False]

    quarter_year_TV_show = fill_quarter_info (quarter_year_TV_show[['year','quarter_id','duration','duration_hours']], first_day, last_day)
    quarter_year_film  = fill_quarter_info (quarter_year_film[['year','quarter_id','duration','duration_hours']], first_day, last_day)

    quarter_year_groupby = quarter_year_groupby.set_index('quarter-year')

    fig, ax = plt.subplots(figsize=(6,4))
    ax.plot(quarter_year_groupby.index, quarter_year_groupby["duration_hours"], label='Total')
    ax.plot(quarter_year_groupby.index, quarter_year_TV_show["duration_hours"], label='TV shows')
    ax.plot(quarter_year_groupby.index, quarter_year_film["duration_hours"], label='Films')

    plt.legend()
    plt.xticks(quarter_year_groupby.index, rotation='vertical')
    plt.ylabel('Watched hours')
    #plt.xlabel('Year')
    plt.title('Distribution between TV shows and films during the years')

    return fig


def year_evolution (netflix_hist):
    st.write('This has been the evolution of your consumption over the years:')

    netflix_hist["year"] = netflix_hist["Date"].dt.year
    year_groupby = netflix_hist.groupby(by=['year']).sum()

    year_groupby_ = pd.DataFrame(year_groupby[['duration']], columns = ['duration'], index = year_groupby.index )
    year_groupby_['duration [hours]'] = year_groupby['duration']/60
    year_groupby_["prev_duration"] = year_groupby_['duration [hours]'].shift(1)
    year_groupby_ = year_groupby_.replace(np.nan, 0)

    year_groupby_['growth [%]'] = (year_groupby_['duration [hours]'] - year_groupby_['prev_duration']) / year_groupby_['prev_duration'] * 100 
    year_groupby_ = year_groupby_.replace(np.inf, 0)

    st.dataframe(year_groupby_[['duration [hours]','growth [%]']])


def plot_overall_distribution(netflix_hist):
    TV_show_vs_films = netflix_hist.groupby("is_TV_show").sum()
    TV_show_vs_films = TV_show_vs_films["duration"]
    TV_show_vs_films = TV_show_vs_films.sort_values(ascending=False)
    size_TV_show_vs_films = TV_show_vs_films / TV_show_vs_films.sum()

    count_TV_show_vs_films = netflix_hist["is_TV_show"].value_counts()

    labels = ["TV shows", "Films & Documentaries"]

    fig, ax = plt.subplots(1,1, figsize=(8,4))

    # Pie
    ax.pie(size_TV_show_vs_films, labels=labels, autopct='%1.1f%%',
            shadow=False, startangle=180)
    ax.axis('equal')
   
    ax.set_title('Overall distribution')

    return fig


def plot_monthly_distribution (netflix_hist, first_day, last_day):
    month_years_pt = month_year_groupby.pivot_table( values="duration_hours", index = "month_name",                                                                                     columns = "year", aggfunc = sum, fill_value = 0)
    month_years_pt['acumulated'] = 0

    month_years_pt = month_years_pt.loc[["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]]

    first_year, last_year = first_day.year, last_day.year
    years = np.arange(first_year, last_day.year + 1)

    fig, ax = plt.subplots(figsize=(12,8))
    
    for year in years:
        ax.plot( month_years_pt.index, month_years_pt[year], label= str(year), linewidth = 3)
    
    # Stacked
    #for year in years:
    #    ax.bar( month_years_pt.index, month_years_pt[year], label= str(year), bottom = month_years_pt['acumulated'])
    #    month_years_pt['acumulated'] = month_years_pt['acumulated'] + month_years_pt[year]

    ax.set_xticklabels( month_years_pt.index) 
    ax.set_ylabel("Watched hours")
    plt.title('Distribution of monthly watched hours during the years')
    ax.legend()
    
    return fig


def fill_weekdays(weekday_df):
    for i in range(0,7):
        bool_w = i in list(weekday_df['weekday'])
        if bool_w == False:
            weekday_df = weekday_df.append({'weekday': i,'duration':0}, ignore_index = True)
    return weekday_df


def plot_weekday_distribution (netflix_hist):

    netflix_hist["weekday"] = netflix_hist["Date"].dt.weekday
    weekday_value_counts = netflix_hist["weekday"].value_counts()
    weekday_groupby = netflix_hist.groupby(by=['weekday','is_TV_show']).sum()

    weekday_groupby = weekday_groupby.reset_index()

    weekday_TV_shows = weekday_groupby[weekday_groupby["is_TV_show"] == True]
    weekday_films = weekday_groupby[weekday_groupby["is_TV_show"] == False]
    weekday_TV_shows = fill_weekdays(weekday_TV_shows[['weekday','duration']])
    weekday_films = fill_weekdays(weekday_films[['weekday','duration']])

    weekday_names =["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    fig, ax = plt.subplots(figsize=(8,4))

    ax.bar( weekday_names, weekday_TV_shows["duration"], label="TV shows" )
    ax.bar( weekday_names, weekday_films["duration"], bottom = weekday_TV_shows["duration"], label = "Films" )
    ax.set_ylabel("Watched hours")
    plt.title('Distribution of watched hours during the each day of the week')
    ax.legend()

    return fig


st.write("""
    # Netflix Viewing History Analysis

    Developed by: Carlos Pérez Ricardo

    Have you ever wondered how many hours, days or even months you have spent watching Netlflix? Which TV show have you watched most episodes of? How does your Viewing Activity changed over the month and years?  
    This website will answer these questions for you. In this project you can enter a csv file with your viewing activity from Netflix and obtain an analysis of your viewing activity. 

    Follow the following steps to **download the viewing activity** (https://help.netflix.com/es-es/node/101917):
    * You can check which series and movies have been viewed in the different profiles of your account.

    * In a web browser, go to the Account (Cuenta) page.

    * Open the Profile and parental controls settings for the profile you want to view.

    * Open Viewing Activity (Actividad de visionado).

    * If you see a limited list, use the Show more (Mostrar más) button.

    To download a list to a spreadsheet, select Download all at the bottom of the page. You will be able to open the downloaded file with any spreadsheet software that supports the CSV file format.

    **After downloading**

    Once you have downloaded the file from Netflix, enter the csv file in section "Drag and drop file here". The csv file is just a simple file with two columns named "Title" and "Date". And wait for the program to load all the information.

    Enjoy it! 

    """)

 
STYLE = """
<style>
img {
    max-width: 100%;
}
</style>
"""


class FileUpload(object):
 
    def __init__(self):
        self.fileTypes = ["csv"]
 
    def run(self):
        """
        Upload File on Streamlit Code
        :return:
        """
        #st.info(__doc__)
        found = False
        st.markdown(STYLE, unsafe_allow_html=True)
        file = st.file_uploader("Upload file", type=self.fileTypes)
        show_file = st.empty()
        if not file:
            show_file.info("Please upload a file of type: " + ", ".join(["csv"]))
            return 0, found

        content = file.getvalue()
        data = pd.read_csv(file)
        found = True
        #st.dataframe(data.head(10))
        file.close()
        return data, found


def change_width(ax, new_value) :
    for patch in ax.patches :
        current_width = patch.get_width()
        diff = current_width - new_value
        # we change the bar width
        patch.set_width(new_value)
        # we recenter the bar
        patch.set_x(patch.get_x() + diff * .5)


def plot_day (netflix_hist, month_chosen, year_chosen):
    netflix_hist['day'] = netflix_hist['Date'].dt.day
    netflix_hist['month'] = netflix_hist['Date'].dt.month
    netflix_hist['year'] = netflix_hist['Date'].dt.year

    months_duration = {1:31, 2:29, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    st.write('### Daily Viewing Activity in the most watched month: ' + month_names[month_chosen] + ' ,' + str(year_chosen) )

    month_dt = netflix_hist[ (netflix_hist['year'] == year_chosen) & (netflix_hist['month'] == month_chosen) ]
    day_groupby = month_dt.groupby('day').sum()
    day_groupby = day_groupby['duration']/60

    months_duration = months_duration[2]
    day_groupby = day_groupby.reset_index()

    for day in np.arange(1,months_duration+1):
            day_list = list(day_groupby["day"])
            bool_d = day in day_list
            if bool_d == False:
                day_groupby = day_groupby.append( {"day":int(day), "duration":0}, ignore_index = True)

    day_groupby = day_groupby.sort_values(by='day')

    fig, ax = plt.subplots(figsize=(12,4))
    _ = sns.barplot(x='day', y='duration', ax = ax, data=day_groupby, dodge=False)
    change_width(_, .87)

    plt.xticks(rotation='vertical')
    plt.ylabel('Watched hours')
    #plt.title('Distribution of watched hours each day in '+ month_names[month_chosen] + ', ' + str(year_chosen))
    plt.xlabel('')

    st.pyplot(fig)

    st.write(""" It is important to mention that as in the csv file only appears the Title and Date. Moreover, it is considered that every film or episode has been watched completely during that day.     
    And one last point to be considered is that you can watch Netflix on several plarforms so you could be watching a film and simultaneouly a relative could be watching another film. 
    These two assumptions can lead to days on unreasonable number of hours watched during that day (more than 24 hours registered in a day).  """)


def year_buttons(first_day, last_day):
    first_year = first_day.year
    last_year = last_day.year
    delta = last_year - first_year + 1
    years = np.arange(first_year, last_year+1)

    year_chosen = first_year 

    st.write('Select a year from the list:')

    years_buttons = []
    if delta == 1:
        year1 = st.beta_columns([0.1])
        years_buttons.append(year1)
    if delta == 2:
        year1, year2 = st.beta_columns([0.1, 0.1])
        years_buttons.append(year1); years_buttons.append(year2)
    if delta == 3:
        year1, year2, year3 = st.beta_columns([0.1, 0.1, 0.1])
        years_buttons.append(year1); years_buttons.append(year2); years_buttons.append(year3)
    if delta == 4:
        year1, year2, year3, year4 = st.beta_columns([0.1, 0.1, 0.1, 0.1])
        years_buttons.append(year1); years_buttons.append(year2); years_buttons.append(year3); years_buttons.append(year4)
    if delta == 5:
        year1, year2, year3, year4, year5 = st.beta_columns([0.1, 0.1, 0.1, 0.1, 0.1])
        years_buttons.append(year1); years_buttons.append(year2); years_buttons.append(year3); years_buttons.append(year4); years_buttons.append(year5)
    if delta == 6:
        year1, year2, year3, year4, year5, year6 = st.beta_columns([0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
        years_buttons.append(year1); years_buttons.append(year2); years_buttons.append(year3); years_buttons.append(year4); years_buttons.append(year5); years_buttons.append(year6)
    
    i = 0
    for x in years_buttons:
        if x.button(str(years[i])):
            #st.write('You selected ' + str(years[i]))
            year_chosen = years[i]
        i += 1


def month_buttons(netflix_hist):
    st.write('Select a month from the list:')

    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    month_buttons = []

    month1, month2, month3, month4, month5, month6, month7, month8, month9, month10, month11, month12 = st.beta_columns([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
    month_buttons.append(month1); month_buttons.append(month2); month_buttons.append(month3); month_buttons.append(month4); month_buttons.append(month5); month_buttons.append(month6)
    month_buttons.append(month7); month_buttons.append(month8); month_buttons.append(month9); month_buttons.append(month10); month_buttons.append(month11); month_buttons.append(month12)

    i = 0
    for x in month_buttons:
        if x.button(month_names[i]):
            st.write('Displaying ' + month_names[i] + ', ' + str(year_chosen))
            month_chosen = i
            plot_day (netflix_hist, month_chosen, year_chosen)
            #Action
        i += 1


if __name__ ==  "__main__":
    file_upload = FileUpload()
    netflix_data, found  = file_upload.run() 

    if found == True:
        netflix_hist, first_day, last_day = clean_and_prepare_data (netflix_data)    
        netflix_hist = add_duration(netflix_hist, 40, 100)

        # Summary
        summary (netflix_hist, first_day, last_day)

        year_evolution (netflix_hist)
        
        st.write(" The **duration of TV shows episodes** is considered to be **40 min**, whereas for the **films' duration** is **100 min**.")
        st.write("The following graph shows the number of watched hours across every month since the first log:")

        fig, month_year_groupby = plot_year_month(netflix_hist, first_day, last_day)
        st.pyplot(fig)

        st.write(" The following graph shows the number of watched hours across every trimester or quarter: ")
        fig, quarter_year_groupby = plot_year_quarter(netflix_hist, first_day, last_day)
        st.pyplot(fig)

        max_duration = month_year_groupby.max()['duration']

        plot_day (netflix_hist, int(month_year_groupby[ month_year_groupby['duration'] == max_duration ]['month']), int(month_year_groupby[ month_year_groupby['duration'] == max_duration ]['year']))

        #year_chosen = first_day.year
        #year_buttons(first_day, last_day)
        #month_buttons(netflix_hist)

        # Most watched TV shows
        most_watched_TV_shows = TV_shows_ranking_plot(netflix_hist)
        fig = plot_most_watched (most_watched_TV_shows)
        st.pyplot(fig)

        st.write('### Distribution of TV shows and films ')
        st.write('The following graphs describe how has been the distribution of watched hours. The first one describes the overall distribution and the second one describes this distribution across every trimester or quarter dintinguishing between TV shows and Films. ')

        fig = plot_overall_distribution(netflix_hist)
        st.pyplot(fig)

        fig = distribution_quarter_year(netflix_hist, quarter_year_groupby)
        st.pyplot(fig)

        # Weekly and monthly analysis
        st.write('## Monthly and weekday distribution')

        st.write('The following graph describes the sum number of watched hours for each month during all the years.')
        fig = plot_monthly_distribution (month_year_groupby, first_day, last_day)
        st.pyplot(fig)
        
        st.write('The following graph describes the sum number of watched hours for day of the week.')
        fig = plot_weekday_distribution (netflix_hist)
        st.pyplot(fig)


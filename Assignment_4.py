
# coding: utf-8

# ---
# 
# _You are currently looking at **version 1.1** of this notebook. To download notebooks and datafiles, as well as get help on Jupyter notebooks in the Coursera platform, visit the [Jupyter Notebook FAQ](https://www.coursera.org/learn/python-data-analysis/resources/0dhYG) course resource._
# 
# ---

# In[1]:

import pandas as pd
import numpy as np
from scipy.stats import ttest_ind


# # Assignment 4 - Hypothesis Testing
# This assignment requires more individual learning than previous assignments - you are encouraged to check out the [pandas documentation](http://pandas.pydata.org/pandas-docs/stable/) to find functions or methods you might not have used yet, or ask questions on [Stack Overflow](http://stackoverflow.com/) and tag them as pandas and python related. And of course, the discussion forums are open for interaction with your peers and the course staff.
# 
# Definitions:
# * A _quarter_ is a specific three month period, Q1 is January through March, Q2 is April through June, Q3 is July through September, Q4 is October through December.
# * A _recession_ is defined as starting with two consecutive quarters of GDP decline, and ending with two consecutive quarters of GDP growth.
# * A _recession bottom_ is the quarter within a recession which had the lowest GDP.
# * A _university town_ is a city which has a high percentage of university students compared to the total population of the city.
# 
# **Hypothesis**: University towns have their mean housing prices less effected by recessions. Run a t-test to compare the ratio of the mean price of houses in university towns the quarter before the recession starts compared to the recession bottom. (`price_ratio=quarter_before_recession/recession_bottom`)
# 
# The following data files are available for this assignment:
# * From the [Zillow research data site](http://www.zillow.com/research/data/) there is housing data for the United States. In particular the datafile for [all homes at a city level](http://files.zillowstatic.com/research/public/City/City_Zhvi_AllHomes.csv), ```City_Zhvi_AllHomes.csv```, has median home sale prices at a fine grained level.
# * From the Wikipedia page on college towns is a list of [university towns in the United States](https://en.wikipedia.org/wiki/List_of_college_towns#College_towns_in_the_United_States) which has been copy and pasted into the file ```university_towns.txt```.
# * From Bureau of Economic Analysis, US Department of Commerce, the [GDP over time](http://www.bea.gov/national/index.htm#gdp) of the United States in current dollars (use the chained value in 2009 dollars), in quarterly intervals, in the file ```gdplev.xls```. For this assignment, only look at GDP data from the first quarter of 2000 onward.
# 
# Each function in this assignment below is worth 10%, with the exception of ```run_ttest()```, which is worth 50%.

# In[2]:

# Use this dictionary to map state names to two letter acronyms
states = {'OH': 'Ohio', 'KY': 'Kentucky', 'AS': 'American Samoa', 'NV': 'Nevada', 'WY': 'Wyoming', 'NA': 'National', 'AL': 'Alabama', 'MD': 'Maryland', 'AK': 'Alaska', 'UT': 'Utah', 'OR': 'Oregon', 'MT': 'Montana', 'IL': 'Illinois', 'TN': 'Tennessee', 'DC': 'District of Columbia', 'VT': 'Vermont', 'ID': 'Idaho', 'AR': 'Arkansas', 'ME': 'Maine', 'WA': 'Washington', 'HI': 'Hawaii', 'WI': 'Wisconsin', 'MI': 'Michigan', 'IN': 'Indiana', 'NJ': 'New Jersey', 'AZ': 'Arizona', 'GU': 'Guam', 'MS': 'Mississippi', 'PR': 'Puerto Rico', 'NC': 'North Carolina', 'TX': 'Texas', 'SD': 'South Dakota', 'MP': 'Northern Mariana Islands', 'IA': 'Iowa', 'MO': 'Missouri', 'CT': 'Connecticut', 'WV': 'West Virginia', 'SC': 'South Carolina', 'LA': 'Louisiana', 'KS': 'Kansas', 'NY': 'New York', 'NE': 'Nebraska', 'OK': 'Oklahoma', 'FL': 'Florida', 'CA': 'California', 'CO': 'Colorado', 'PA': 'Pennsylvania', 'DE': 'Delaware', 'NM': 'New Mexico', 'RI': 'Rhode Island', 'MN': 'Minnesota', 'VI': 'Virgin Islands', 'NH': 'New Hampshire', 'MA': 'Massachusetts', 'GA': 'Georgia', 'ND': 'North Dakota', 'VA': 'Virginia'}


# In[3]:

f = open('university_towns.txt')
data = []
line = f.readline().rstrip()
while(line):
    if 'edit' in line:
        line = line.split('[')
        state = line[0]
    elif '(' in line:
        line = line.split(' (')
        town = line[0]
        data.append([state, town])
    else:
        town = line
        data.append([state, town])
    line = f.readline().rstrip()    
f.close()
university_df = pd.DataFrame(columns=['State', 'RegionName'])
for i in data:
    university_df = university_df.append({'State': i[0], 'RegionName': i[1]}, ignore_index=True)


# In[15]:

def get_list_of_university_towns():
    '''Returns a DataFrame of towns and the states they are in from the 
    university_towns.txt list. The format of the DataFrame should be:
    DataFrame( [ ["Michigan", "Ann Arbor"], ["Michigan", "Yipsilanti"] ], 
    columns=["State", "RegionName"]  )
    
    The following cleaning needs to be done:

    1. For "State", removing characters from "[" to the end.
    2. For "RegionName", when applicable, removing every character from " (" to the end.
    3. Depending on how you read the data, you may need to remove newline character '\n'. '''
    return(university_df)

get_list_of_university_towns()


# In[4]:

gdp_df = pd.read_excel('gdplev.xls', skiprows=7)

# Drop unnecessary columns
gdp_df.drop(gdp_df.columns[[0,1,2,3,7]], axis=1, inplace=True)
gdp_df.columns = ['Quarterly', 'GDP in billions of current dollars', 'GDP in billions of chained 2009 dollars']

# Only look at GDP data from the first quarter of 2000 onward.
i_2000q1 = gdp_df.loc[gdp_df['Quarterly'] == '2000q1'].index.values.item()
gdp_df = gdp_df.ix[i_2000q1:]
gdp_df.reset_index(drop=True, inplace=True)

# Add a new column for quarter over quarter difference. If the value < 0, it marks the beginning of a decline. 
gdp_df['Diff GDP in billions of current dollars'] = gdp_df['GDP in billions of current dollars'].diff()
# gdp_df[gdp_df['Diff GDP in billions of current dollars'] < 0]
# gdp_df[30:50]


# In[5]:

def get_recession_start():
    '''Returns the year and quarter of the recession start time as a 
    string value in a format such as 2005q3'''
    # A recession is defined as starting with two consecutive quarters of GDP decline, 
    # and ending with two consecutive quarters of GDP growth.
    # 2008q4 - 2009q2 : consecutive declines
    # 2009q3 : consecutive growth
    for i in range(2, len(gdp_df)):
        if (gdp_df.iloc[i-2][1] > gdp_df.iloc[i-1][1]) and (gdp_df.iloc[i-1][1] > gdp_df.iloc[i][1]):
            return(gdp_df.iloc[i-2][0])

get_recession_start()


# In[6]:

def get_recession_end():
    '''Returns the year and quarter of the recession end time as a 
    string value in a format such as 2005q3'''
    
    recession_start = get_recession_start()
    start_index = gdp_df[gdp_df['Quarterly'] == recession_start].index.tolist()[0]
    new_gdp_df = gdp_df.iloc[start_index:]
    
    for i in range(2, len(new_gdp_df)):
        if (new_gdp_df.iloc[i-2][1] < new_gdp_df.iloc[i-1][1]) and (new_gdp_df.iloc[i-1][1] < new_gdp_df.iloc[i][1]):
            return(new_gdp_df.iloc[i][0])
get_recession_end()        


# In[7]:

def get_recession_bottom():
    '''Returns the year and quarter of the recession bottom time as a 
    string value in a format such as 2005q3'''
    # A recession bottom is the quarter within a recession which had the lowest GDP.
    recession_start = get_recession_start()
    recession_end = get_recession_end()
    
    recession_period = gdp_df.loc[(gdp_df['Quarterly'] >= recession_start) & (gdp_df['Quarterly'] <= recession_end)]
    recession_bottom = gdp_df.loc[gdp_df['GDP in billions of current dollars'] == recession_period['GDP in billions of current dollars'].min()]
    
    return(recession_bottom['Quarterly'].item())

get_recession_bottom()


# In[8]:

zillow_df = pd.read_csv('City_Zhvi_AllHomes.csv')

# Drop unnecessary columns
zillow_df.drop(['RegionID', 'Metro', 'CountyName', 'SizeRank'], axis=1, inplace=True)
# 2000q1 through 2016q3
zillow_df.drop(zillow_df.columns[2:47], axis=1, inplace=True)
zillow_df['State'] = zillow_df['State'].map(states)
zillow_df.set_index(['State','RegionName'], inplace=True)


# In[16]:

def convert_housing_data_to_quarters():
    '''Converts the housing data to quarters and returns it as mean 
    values in a dataframe. This dataframe should be a dataframe with
    columns for 2000q1 through 2016q3, and should have a multi-index
    in the shape of ["State","RegionName"].
    
    Note: Quarters are defined in the assignment description, they are
    not arbitrary three month periods.
    
    The resulting dataframe should have 67 columns, and 10,730 rows.
    '''
    # Quarters of the year
    quater = [list(zillow_df.columns)[x:x+3] for x in range(0, len(list(zillow_df.columns)), 3)]
    
    # Generating the new coloumns names 
    years = list(range(2000,2017))
    quarters = ['q1','q2','q3','q4']
    quarter_years = []
    for i in years:
        for x in quarters:
            quarter_years.append((str(i)+x))
    quarter_years = quarter_years[:-1]
    
    for col,q in zip(quarter_years,quater):
        zillow_df[col] = zillow_df[q].mean(axis=1)
        
    zillow_df_new = zillow_df[quarter_years]
    
    return(zillow_df_new)
convert_housing_data_to_quarters()


# In[27]:

def run_ttest():
    '''First creates new data showing the decline or growth of housing prices
    between the recession start and the recession bottom. Then runs a ttest
    comparing the university town
    values to the non-university towns values, 
    return whether the alternative hypothesis (that the two groups are the same)
    is true or not as well as the p-value of the confidence. 
    
    Return the tuple (different, p, better) where different=True if the t-test is
    True at a p<0.01 (we reject the null hypothesis), or different=False if 
    otherwise (we cannot reject the null hypothesis). The variable p should
    be equal to the exact p value returned from scipy.stats.ttest_ind(). The
    value for better should be either "university town" or "non-university town"
    depending on which has a lower mean price ratio (which is equivilent to a
    reduced market loss).'''

    data_df = convert_housing_data_to_quarters().copy()
    recession_start = get_recession_start()
    recession_bottom = get_recession_bottom()
    
    data_df = data_df.loc[:, recession_start:recession_bottom]
    data_df = data_df.reset_index()
    
    def price_ratio(df):
        return (df[recession_start] - df[recession_bottom]) / df[recession_start]
    
    data_df['Price Ratio'] = data_df.apply(price_ratio, axis=1)
    uni_town = set(get_list_of_university_towns()['RegionName'])

    def is_uni_town(df):
        # Check if the town is a university towns or not
        if (df['RegionName'] in uni_town):
            return 1
        else:
            return 0
        
    data_df['is_uni'] = data_df.apply(is_uni_town, axis=1)
    not_uni = data_df[data_df['is_uni'] == 0].loc[:, 'Price Ratio'].dropna()
    is_uni  = data_df[data_df['is_uni'] == 1].loc[:, 'Price Ratio'].dropna()
    p_value = list(ttest_ind(not_uni, is_uni))[1]
    
    if p_value < 0.01:
        result = True
    else:
        result = False
        
    def better():
        if not_uni.mean() < is_uni.mean():
            return 'non-university town'
        else:
            return 'university town'
        
    return(result, p_value, better())

run_ttest()


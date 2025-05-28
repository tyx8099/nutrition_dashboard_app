import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pytz

# Set page configuration
st.set_page_config(
    page_title="Nutrition Dashboard",
    page_icon="🥗",
    layout="wide"
)

# Title
st.title("🥗 Nutrition Dashboard")

# Load and preprocess data
@st.cache_data
def load_data():
    df = pd.read_csv("Table 1-Grid view.csv")
    
    # Drop photo columns
    photo_columns = [col for col in df.columns if 'Photo' in col]
    df = df.drop(columns=photo_columns)
    
    # Convert date column
    df['Input Date'] = pd.to_datetime(df['Input Date'], format='%d/%m/%Y %I:%M%p')
    df['Date'] = df['Input Date'].dt.date
    
    return df

# Load data
df = load_data()

# Sidebar filters
st.sidebar.header("Filters")
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(df['Date'].min(), df['Date'].max()),
    min_value=df['Date'].min(),
    max_value=df['Date'].max()
)

# Filter data based on date range
mask = (df['Date'] >= date_range[0]) & (df['Date'] <= date_range[1])
filtered_df = df[mask]

# Daily Summary Metrics
st.header("Daily Nutritional Summary")

# Get current date in Singapore timezone
sg_tz = pytz.timezone('Asia/Singapore')
sg_now = datetime.now(sg_tz)
today_date = sg_now.date()

# Calculate today's metrics
today_metrics = filtered_df[filtered_df['Date'] == today_date].agg({
    'Calories (kcal)': 'sum',
    'Protein (g)': 'sum',
    'Carbohydrates (g)': 'sum',
    'Fat (g)': 'sum'
})

# Calculate average daily metrics
daily_metrics = filtered_df.groupby('Date').agg({
    'Calories (kcal)': 'sum',
    'Protein (g)': 'sum',
    'Carbohydrates (g)': 'sum',
    'Fat (g)': 'sum'
}).mean()

# Display metrics in two rows
st.subheader(f"Today's Intake ({sg_now.strftime('%Y-%m-%d')})")
col1, col2, col3, col4 = st.columns(4)
with col1:
    calories_value = float(today_metrics['Calories (kcal)']) if not pd.isna(today_metrics['Calories (kcal)']) else 0
    calories_delta = float(today_metrics['Calories (kcal)'] - daily_metrics['Calories (kcal)']) if not pd.isna(today_metrics['Calories (kcal)']) else None
    st.metric("Calories", 
              f"{calories_value:.0f} kcal",
              delta=f"{calories_delta:.0f}" if calories_delta is not None else None)
with col2:
    protein_value = float(today_metrics['Protein (g)']) if not pd.isna(today_metrics['Protein (g)']) else 0
    protein_delta = float(today_metrics['Protein (g)'] - daily_metrics['Protein (g)']) if not pd.isna(today_metrics['Protein (g)']) else None
    st.metric("Protein", 
              f"{protein_value:.1f}g",
              delta=f"{protein_delta:.1f}" if protein_delta is not None else None)
with col3:
    carbs_value = float(today_metrics['Carbohydrates (g)']) if not pd.isna(today_metrics['Carbohydrates (g)']) else 0
    carbs_delta = float(today_metrics['Carbohydrates (g)'] - daily_metrics['Carbohydrates (g)']) if not pd.isna(today_metrics['Carbohydrates (g)']) else None
    st.metric("Carbs", 
              f"{carbs_value:.1f}g",
              delta=f"{carbs_delta:.1f}" if carbs_delta is not None else None)
with col4:
    fat_value = float(today_metrics['Fat (g)']) if not pd.isna(today_metrics['Fat (g)']) else 0
    fat_delta = float(today_metrics['Fat (g)'] - daily_metrics['Fat (g)']) if not pd.isna(today_metrics['Fat (g)']) else None
    st.metric("Fat", 
              f"{fat_value:.1f}g",
              delta=f"{fat_delta:.1f}" if fat_delta is not None else None)

st.subheader("Average Daily Intake")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Avg. Daily Calories", f"{daily_metrics['Calories (kcal)']:.0f} kcal")
with col2:
    st.metric("Avg. Daily Protein", f"{daily_metrics['Protein (g)']:.1f}g")
with col3:
    st.metric("Avg. Daily Carbs", f"{daily_metrics['Carbohydrates (g)']:.1f}g")
with col4:
    st.metric("Avg. Daily Fat", f"{daily_metrics['Fat (g)']:.1f}g")

# Trends over time
st.header("Nutritional Trends")
tab1, tab2, tab3, tab4 = st.tabs(["Calories", "Protein", "Carbohydrates", "Fat"])

# Process the daily totals for all nutrients
daily_totals = filtered_df.groupby('Date').agg({
    'Calories (kcal)': 'sum',
    'Protein (g)': 'sum',
    'Carbohydrates (g)': 'sum',
    'Fat (g)': 'sum'
}).reset_index()

with tab1:
    fig_calories = px.bar(
        daily_totals, 
        x='Date', 
        y='Calories (kcal)',
        title='Daily Caloric Intake'
    )
    fig_calories.update_traces(marker_color='#FF9B9B')
    # Add average line
    avg_calories = daily_totals['Calories (kcal)'].mean()
    fig_calories.add_hline(y=avg_calories, line_dash="dash", line_color="red",
                          annotation_text=f"Average: {avg_calories:.0f} kcal", 
                          annotation_position="right")
    st.plotly_chart(fig_calories, use_container_width=True)

with tab2:
    fig_protein = px.bar(
        daily_totals, 
        x='Date', 
        y='Protein (g)',
        title='Daily Protein Intake'
    )
    fig_protein.update_traces(marker_color='#A0C4FF')
    # Add average line
    avg_protein = daily_totals['Protein (g)'].mean()
    fig_protein.add_hline(y=avg_protein, line_dash="dash", line_color="blue",
                         annotation_text=f"Average: {avg_protein:.1f}g", 
                         annotation_position="right")
    st.plotly_chart(fig_protein, use_container_width=True)

with tab3:
    fig_carbs = px.bar(
        daily_totals, 
        x='Date', 
        y='Carbohydrates (g)',
        title='Daily Carbohydrate Intake'
    )
    fig_carbs.update_traces(marker_color='#9BF6FF')
    # Add average line
    avg_carbs = daily_totals['Carbohydrates (g)'].mean()
    fig_carbs.add_hline(y=avg_carbs, line_dash="dash", line_color="cyan",
                       annotation_text=f"Average: {avg_carbs:.1f}g", 
                       annotation_position="right")
    st.plotly_chart(fig_carbs, use_container_width=True)

with tab4:
    fig_fat = px.bar(
        daily_totals, 
        x='Date', 
        y='Fat (g)',
        title='Daily Fat Intake'
    )
    fig_fat.update_traces(marker_color='#FFB347')
    # Add average line
    avg_fat = daily_totals['Fat (g)'].mean()
    fig_fat.add_hline(y=avg_fat, line_dash="dash", line_color="orange",
                     annotation_text=f"Average: {avg_fat:.1f}g", 
                     annotation_position="right")
    st.plotly_chart(fig_fat, use_container_width=True)

# Detailed nutrient analysis
st.header("Detailed Nutrient Analysis")
nutrients = ['Calories (kcal)', 'Protein (g)', 'Carbohydrates (g)', 'Sugar (g)',
            'Fat (g)', 'Saturated Fat (g)', 'Cholesterol (mg)', 'Fiber (g)', 'Omega-3 (mg)']

selected_nutrient = st.selectbox("Select Nutrient", nutrients)
nutrient_by_food = filtered_df.groupby('Item Name')[selected_nutrient].sum().sort_values(ascending=False).head(10)

fig_nutrients = px.bar(
    nutrient_by_food,
    orientation='h',
    title=f'Top 10 Food Items by {selected_nutrient}',
    height=400
)
# Reverse the y-axis to show highest values at the top
fig_nutrients.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig_nutrients, use_container_width=True)

# Display raw data
st.header("Raw Data")
if st.checkbox("Show raw data"):
    st.dataframe(filtered_df)
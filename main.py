import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pytz
from pyairtable import Api

# Airtable Configuration
AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
TABLE_ID = st.secrets["AIRTABLE_TABLE_ID"]

# Set page configuration
st.set_page_config(
    page_title="Nutrition Dashboard",
    page_icon="🥗",
    layout="wide"
)

# Load and preprocess data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_airtable_data():
    """Read nutrition data from Airtable and return as DataFrame"""
    try:
        # Initialize Airtable client
        api = Api(AIRTABLE_TOKEN)
        table = api.table(BASE_ID, TABLE_ID)
        
        # Fetch all records
        records = table.all()
        if not records:
            print("No records found in Airtable")
            return pd.DataFrame()
            
        # Convert to DataFrame
        df = pd.DataFrame([record['fields'] for record in records])
        
        # Add record IDs
        df['ID'] = [record['id'] for record in records]
        df = df.set_index('ID')
        
        # Drop any photo/attachment columns
        photo_cols = [col for col in df.columns if any(x in col.lower() for x in ['photo', 'attachment', 'image'])]
        df = df.drop(columns=photo_cols, errors='ignore')
        
        # Convert dates from ISO format
        df['Input Date'] = pd.to_datetime(df['Input Date'], format='ISO8601')
        # Convert to dd/mm/yyyy format for display
        df['Input Date String'] = df['Input Date'].dt.strftime('%d/%m/%Y %I:%M%p')
        df['Date'] = df['Input Date'].dt.date
        
        return df
        
    except Exception as e:
        print(f"Error accessing Airtable: {str(e)}")
        return None

def calculate_caloric_proportions(metrics_df):
    # Calculate calories from each macronutrient
    protein_cals = metrics_df['Protein (g)'] * 4  # 4 calories per gram of protein
    carbs_cals = metrics_df['Carbohydrates (g)'] * 4  # 4 calories per gram of carbs
    fat_cals = metrics_df['Fat (g)'] * 9  # 9 calories per gram of fat
    
    total_cals = metrics_df['Calories (kcal)']
    
    # Calculate percentages
    return {
        'Protein': protein_cals / total_cals * 100,
        'Carbohydrates': carbs_cals / total_cals * 100,
        'Fat': fat_cals / total_cals * 100
    }

# Define pastel color palette
PASTEL_COLORS = {
    'blue': '#B4D6FA',      # Protein
    'green': '#C1F0C1',     # Carbs
    'peach': '#FFE5B4',     # Fat
    'pink': '#FFD1DC',      # Calories
    'magenta': '#FFB5E8',   # Sugar
    'orange': '#FFDAB9',    # Saturated Fat
    'purple': '#E6E6FA',    # Cholesterol
    'yellow_green': '#E2F0CB', # Fiber
    'mint': '#B5EAD7'       # Omega-3
}

def create_macro_donut(proportions, title):
    fig = go.Figure(data=[go.Pie(
        labels=['Protein', 'Carbohydrates', 'Fat'],
        values=[proportions['Protein'], proportions['Carbohydrates'], proportions['Fat']],
        hole=.4,
        marker_colors=[PASTEL_COLORS['blue'], PASTEL_COLORS['green'], PASTEL_COLORS['peach']]
    )])
    
    fig.update_layout(
        title=title,
        showlegend=True,
        height=300,
        margin=dict(t=40, b=0, l=0, r=0)
    )
    
    return fig

# Add refresh button in sidebar
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Load data
df = get_airtable_data()

if df is None:
    st.error("Could not load data. Please check your Airtable configuration.")
    st.stop()

# Ensure we have data before proceeding
if len(df) == 0:
    st.warning("No data available in the selected source.")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")

# Get current date in Singapore timezone (used throughout the app)
sg_tz = pytz.timezone('Asia/Singapore')
sg_now = datetime.now(sg_tz)
today_date = sg_now.date()

# Get the actual start date from the data (first date with actual entries)
actual_start_date = df['Date'].min()
actual_end_date = min(df['Date'].max(), today_date)  # Use the earlier of today or last recorded date

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(actual_start_date, actual_end_date),
    min_value=actual_start_date,
    max_value=actual_end_date
)

# Show the date range info
st.sidebar.info(f"Data available from {actual_start_date.strftime('%Y-%m-%d')} to {actual_end_date.strftime('%Y-%m-%d')}")

# Filter data based on date range
mask = (df['Date'] >= date_range[0]) & (df['Date'] <= date_range[1])
filtered_df = df[mask]

# Daily Summary Metrics
st.header("📊 Daily Nutritional Summary")

# Calculate today's metrics
today_metrics = filtered_df[filtered_df['Date'] == today_date].agg({
    'Calories (kcal)': 'sum',
    'Protein (g)': 'sum',
    'Carbohydrates (g)': 'sum',
    'Fat (g)': 'sum',
    'Saturated Fat (g)': 'sum',
    'Cholesterol (mg)': 'sum'
})

# Calculate average daily metrics
daily_metrics = filtered_df.groupby('Date').agg({
    'Calories (kcal)': 'sum',
    'Protein (g)': 'sum',
    'Carbohydrates (g)': 'sum',
    'Fat (g)': 'sum',
    'Saturated Fat (g)': 'sum',
    'Cholesterol (mg)': 'sum'
}).mean()

# Display metrics in two rows
st.subheader(f"Today's Intake ({sg_now.strftime('%Y-%m-%d')})")

# Display today's metrics in 6 columns
col1, col2, col3, col4, col5, col6 = st.columns(6)
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
with col5:
    sat_fat_value = float(today_metrics['Saturated Fat (g)']) if not pd.isna(today_metrics['Saturated Fat (g)']) else 0
    sat_fat_delta = float(today_metrics['Saturated Fat (g)'] - daily_metrics['Saturated Fat (g)']) if not pd.isna(today_metrics['Saturated Fat (g)']) else None
    st.metric("Sat. Fat", 
              f"{sat_fat_value:.1f}g",
              delta=f"{sat_fat_delta:.1f}" if sat_fat_delta is not None else None)
with col6:
    chol_value = float(today_metrics['Cholesterol (mg)']) if not pd.isna(today_metrics['Cholesterol (mg)']) else 0
    chol_delta = float(today_metrics['Cholesterol (mg)'] - daily_metrics['Cholesterol (mg)']) if not pd.isna(today_metrics['Cholesterol (mg)']) else None
    st.metric("Cholesterol", 
              f"{chol_value:.0f}mg",
              delta=f"{chol_delta:.0f}" if chol_delta is not None else None)

st.subheader("Average Daily Intake")
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.metric("Avg. Daily Calories", f"{daily_metrics['Calories (kcal)']:.0f} kcal")
with col2:
    st.metric("Avg. Daily Protein", f"{daily_metrics['Protein (g)']:.1f}g")
with col3:
    st.metric("Avg. Daily Carbs", f"{daily_metrics['Carbohydrates (g)']:.1f}g")
with col4:
    st.metric("Avg. Daily Fat", f"{daily_metrics['Fat (g)']:.1f}g")
with col5:
    st.metric("Avg. Daily Sat. Fat", f"{daily_metrics['Saturated Fat (g)']:.1f}g")
with col6:
    st.metric("Avg. Daily Cholesterol", f"{daily_metrics['Cholesterol (mg)']:.0f}mg")

# Caloric Breakdown
st.subheader("Caloric Breakdown")
col1, col2 = st.columns(2)

with col1:
    # Today's caloric breakdown
    if not today_metrics.isna().any():  # Only show if we have data for today
        today_proportions = calculate_caloric_proportions(today_metrics)
        fig_today_donut = create_macro_donut(today_proportions, "Today's Caloric Sources")
        st.plotly_chart(fig_today_donut, use_container_width=True)
    else:
        st.info("No data available for today")

with col2:
    # Average daily caloric breakdown
    avg_proportions = calculate_caloric_proportions(daily_metrics)
    fig_avg_donut = create_macro_donut(avg_proportions, "Average Daily Caloric Sources")
    st.plotly_chart(fig_avg_donut, use_container_width=True)

# Trends over time
st.header("📊 Nutritional Trends")
tabs = st.tabs(["🔥 Calories", "🥩 Protein", "🍚 Carbohydrates", "🍯 Sugar", "🥑 Fat", "🧈 Saturated Fat", 
                "🥚 Cholesterol", "🥬 Fiber", "🐟 Omega-3"])

# Process the daily totals for all nutrients
daily_totals = filtered_df.groupby('Date').agg({
    'Calories (kcal)': 'sum',
    'Protein (g)': 'sum',
    'Carbohydrates (g)': 'sum',
    'Sugar (g)': 'sum',
    'Fat (g)': 'sum',
    'Saturated Fat (g)': 'sum',
    'Cholesterol (mg)': 'sum',
    'Fiber (g)': 'sum',
    'Omega-3 (mg)': 'sum'
}).reset_index()

# Calories tab
with tabs[0]:
    fig_calories = px.bar(
        daily_totals, 
        x='Date', 
        y='Calories (kcal)',        title='🔥 Daily Caloric Intake'
    )
    fig_calories.update_traces(marker_color=PASTEL_COLORS['pink'])
    avg_calories = daily_totals['Calories (kcal)'].mean()
    fig_calories.add_hline(y=avg_calories, line_dash="dash", line_color="#FF97A9",
                          annotation_text=f"Average: {avg_calories:.0f} kcal", 
                          annotation_position="right")
    st.plotly_chart(fig_calories, use_container_width=True)

# Protein tab
with tabs[1]:
    fig_protein = px.bar(
        daily_totals, 
        x='Date', 
        y='Protein (g)',        title='🥩 Daily Protein Intake'
    )
    fig_protein.update_traces(marker_color=PASTEL_COLORS['blue'])
    avg_protein = daily_totals['Protein (g)'].mean()
    fig_protein.add_hline(y=avg_protein, line_dash="dash", line_color="#7EB1E8",
                         annotation_text=f"Average: {avg_protein:.1f}g", 
                         annotation_position="right")
    st.plotly_chart(fig_protein, use_container_width=True)

# Carbohydrates tab
with tabs[2]:
    fig_carbs = px.bar(
        daily_totals, 
        x='Date', 
        y='Carbohydrates (g)',        title='🍚 Daily Carbohydrate Intake'
    )
    fig_carbs.update_traces(marker_color=PASTEL_COLORS['green'])
    avg_carbs = daily_totals['Carbohydrates (g)'].mean()
    fig_carbs.add_hline(y=avg_carbs, line_dash="dash", line_color="#98D698",
                       annotation_text=f"Average: {avg_carbs:.1f}g", 
                       annotation_position="right")
    st.plotly_chart(fig_carbs, use_container_width=True)

# Sugar tab
with tabs[3]:
    fig_sugar = px.bar(
        daily_totals, 
        x='Date', 
        y='Sugar (g)',        title='🍯 Daily Sugar Intake'
    )
    fig_sugar.update_traces(marker_color=PASTEL_COLORS['magenta'])
    avg_sugar = daily_totals['Sugar (g)'].mean()
    fig_sugar.add_hline(y=avg_sugar, line_dash="dash", line_color="#FF8DC7",
                       annotation_text=f"Average: {avg_sugar:.1f}g", 
                       annotation_position="right")
    st.plotly_chart(fig_sugar, use_container_width=True)

# Fat tab
with tabs[4]:
    fig_fat = px.bar(
        daily_totals, 
        x='Date', 
        y='Fat (g)',        title='🥑 Daily Fat Intake'
    )
    fig_fat.update_traces(marker_color=PASTEL_COLORS['peach'])
    avg_fat = daily_totals['Fat (g)'].mean()
    fig_fat.add_hline(y=avg_fat, line_dash="dash", line_color="#FFB366",
                     annotation_text=f"Average: {avg_fat:.1f}g", 
                     annotation_position="right")
    st.plotly_chart(fig_fat, use_container_width=True)

# Saturated Fat tab
with tabs[5]:
    fig_sat_fat = px.bar(
        daily_totals, 
        x='Date', 
        y='Saturated Fat (g)',        title='🧈 Daily Saturated Fat Intake'
    )
    fig_sat_fat.update_traces(marker_color=PASTEL_COLORS['orange'])
    avg_sat_fat = daily_totals['Saturated Fat (g)'].mean()
    fig_sat_fat.add_hline(y=avg_sat_fat, line_dash="dash", line_color="#FFC087",
                         annotation_text=f"Average: {avg_sat_fat:.1f}g", 
                         annotation_position="right")
    st.plotly_chart(fig_sat_fat, use_container_width=True)

# Cholesterol tab
with tabs[6]:
    fig_chol = px.bar(
        daily_totals, 
        x='Date', 
        y='Cholesterol (mg)',        title='🥚 Daily Cholesterol Intake'
    )
    fig_chol.update_traces(marker_color=PASTEL_COLORS['purple'])
    avg_chol = daily_totals['Cholesterol (mg)'].mean()
    fig_chol.add_hline(y=avg_chol, line_dash="dash", line_color="#BBA0FF",
                       annotation_text=f"Average: {avg_chol:.0f}mg", 
                       annotation_position="right")
    st.plotly_chart(fig_chol, use_container_width=True)

# Fiber tab
with tabs[7]:
    fig_fiber = px.bar(
        daily_totals, 
        x='Date', 
        y='Fiber (g)',        title='🥬 Daily Fiber Intake'
    )
    fig_fiber.update_traces(marker_color=PASTEL_COLORS['yellow_green'])
    avg_fiber = daily_totals['Fiber (g)'].mean()
    fig_fiber.add_hline(y=avg_fiber, line_dash="dash", line_color="#C5D86D",
                       annotation_text=f"Average: {avg_fiber:.1f}g", 
                       annotation_position="right")
    st.plotly_chart(fig_fiber, use_container_width=True)

# Omega-3 tab
with tabs[8]:
    fig_omega = px.bar(
        daily_totals, 
        x='Date', 
        y='Omega-3 (mg)',        title='🐟 Daily Omega-3 Intake'
    )
    fig_omega.update_traces(marker_color=PASTEL_COLORS['mint'])
    avg_omega = daily_totals['Omega-3 (mg)'].mean()
    fig_omega.add_hline(y=avg_omega, line_dash="dash", line_color="#95D5B2",
                       annotation_text=f"Average: {avg_omega:.0f}mg", 
                       annotation_position="right")
    st.plotly_chart(fig_omega, use_container_width=True)

# Detailed nutrient analysis
st.header("🔍 Detailed Nutrient Analysis")
nutrients = ['Calories (kcal)', 'Protein (g)', 'Carbohydrates (g)', 'Sugar (g)',
            'Fat (g)', 'Saturated Fat (g)', 'Cholesterol (mg)', 'Fiber (g)', 'Omega-3 (mg)']

# Map nutrients to their corresponding soft pastel colors
nutrient_colors = {
    'Calories (kcal)': '#FFC3C3',      # Soft coral pink
    'Protein (g)': '#C3E6FF',          # Baby blue
    'Carbohydrates (g)': '#D4F0C6',    # Soft mint green
    'Sugar (g)': '#FFD7E9',            # Light rose
    'Fat (g)': '#FFE4CC',              # Soft peach
    'Saturated Fat (g)': '#FFD4B8',    # Light apricot
    'Cholesterol (mg)': '#E0D7FF',     # Soft lavender
    'Fiber (g)': '#D8EDB8',            # Soft lime
    'Omega-3 (mg)': '#B8E6D9'          # Soft aqua
}

selected_nutrient = st.selectbox("Select Nutrient", nutrients)
nutrient_by_food = filtered_df.groupby('Item Name')[selected_nutrient].sum().sort_values(ascending=False).head(10)

fig_nutrients = px.bar(
    nutrient_by_food,
    orientation='h',
    title=f'Top 10 Food Items by {selected_nutrient}',
    height=400
)
# Set the color based on the selected nutrient
fig_nutrients.update_traces(marker_color=nutrient_colors[selected_nutrient])
# Reverse the y-axis to show highest values at the top
fig_nutrients.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig_nutrients, use_container_width=True)

# Display raw data
st.header("📋 Raw Data")
if st.checkbox("Show raw data"):
    st.dataframe(filtered_df)

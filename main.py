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
    page_icon="static/images/salad.png",
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
        df = df.drop(columns=photo_cols, errors='ignore')          # Convert dates from ISO format and handle timezone
        df['Input Date'] = pd.to_datetime(df['Input Date'], format='ISO8601')
        # Convert to Singapore timezone, handling both tz-naive and tz-aware times
        if df['Input Date'].dt.tz is None:
            df['Input Date'] = df['Input Date'].dt.tz_localize('UTC').dt.tz_convert('Asia/Singapore')
        else:
            df['Input Date'] = df['Input Date'].dt.tz_convert('Asia/Singapore')
        # Convert to dd/mm/yyyy format for display
        df['Input Date String'] = df['Input Date'].dt.strftime('%d/%m/%Y %I:%M%p')
        df['Date'] = df['Input Date'].dt.date
        
        return df
        
    except Exception as e:
        print(f"Error accessing Airtable: {str(e)}")
        return None

# Define color palette using earthy tones

# Define color palette using earthy tones
PASTEL_COLORS = {
    'blue': '#2A9D8F',      # Protein - Teal
    'green': '#8AB17D',     # Carbs - Sage Green (added to complement theme)
    'peach': '#F4A261',     # Fat - Peach
    'pink': '#E76F51',      # Calories - Coral
    'magenta': '#E29578',   # Sugar - Light Coral (added to complement theme)
    'orange': '#EFBC9B',    # Saturated Fat - Light Peach (added to complement theme)
    'purple': '#264653',    # Cholesterol - Dark Teal
    'yellow_green': '#E9C46A', # Fiber - Yellow/Gold
    'mint': '#7EBDC3'       # Omega-3 - Light Teal (added to complement theme)
}

# Add refresh button in sidebar
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.markdown("""
        <script>
            window.parent.location.reload();
        </script>
    """, unsafe_allow_html=True)

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

# No need to convert timezone again since it's already done during data loading

# Get the actual start date from the data (first date with actual entries)
actual_start_date = df['Date'].min()
actual_end_date = today_date  # Use today's date as the end date

# Update the date range input
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
import base64
from pathlib import Path

def img_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')
        
# Create header with icon
icon_base64 = img_to_base64("static/images/growth.png")
st.markdown(f"<h1><img src='data:image/png;base64,{icon_base64}' width='30' style='margin-right: 10px; vertical-align: middle;'>Daily Nutritional Summary</h1>", unsafe_allow_html=True)

# Calculate today's metrics
today_metrics = filtered_df[filtered_df['Date'] == today_date].agg({
    'Calories (kcal)': 'sum',
    'Protein (g)': 'sum',
    'Carbohydrates (g)': 'sum',
    'Fat (g)': 'sum',
    'Saturated Fat (g)': 'sum',
    'Cholesterol (mg)': 'sum',
    'Fiber (g)': 'sum'
})

# Calculate average daily metrics
daily_metrics = filtered_df.groupby('Date').agg({
    'Calories (kcal)': 'sum',
    'Protein (g)': 'sum',
    'Carbohydrates (g)': 'sum',
    'Fat (g)': 'sum',
    'Saturated Fat (g)': 'sum',
    'Cholesterol (mg)': 'sum',
    'Fiber (g)': 'sum'
}).mean()

# Display metrics in two rows
st.subheader(f"Today's Intake ({sg_now.strftime('%Y-%m-%d')})")

# Display today's metrics in 6 columns
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
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
with col7:
    fiber_value = float(today_metrics['Fiber (g)']) if not pd.isna(today_metrics['Fiber (g)']) else 0
    fiber_delta = float(today_metrics['Fiber (g)'] - daily_metrics['Fiber (g)']) if not pd.isna(today_metrics['Fiber (g)']) else None
    st.metric("Fiber", 
              f"{fiber_value:.1f}g",
              delta=f"{fiber_delta:.1f}" if fiber_delta is not None else None)

st.subheader("Average Daily Intake")
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
with col1:
    st.metric("Calories", f"{daily_metrics['Calories (kcal)']:.0f} kcal")
with col2:
    st.metric("Protein", f"{daily_metrics['Protein (g)']:.1f}g")
with col3:
    st.metric("Carbs", f"{daily_metrics['Carbohydrates (g)']:.1f}g")
with col4:
    st.metric("Fat", f"{daily_metrics['Fat (g)']:.1f}g")
with col5:
    st.metric("Sat. Fat", f"{daily_metrics['Saturated Fat (g)']:.1f}g")
with col6:
    st.metric("Cholesterol", f"{daily_metrics['Cholesterol (mg)']:.0f}mg")
with col7:
    st.metric("Fiber", f"{daily_metrics['Fiber (g)']:.1f}g")



# Trends over time
st.markdown(f"<h1><img src='data:image/png;base64,{icon_base64}' width='30' style='margin-right: 10px; vertical-align: middle;'>Nutritional Trends</h1>", unsafe_allow_html=True)

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
        y='Calories (kcal)',
        title='🔥 Daily Caloric Intake'
    )
    fig_calories.update_traces(marker_color=PASTEL_COLORS['pink'])
    avg_calories = daily_totals['Calories (kcal)'].mean()
    fig_calories.add_hline(y=avg_calories, line_dash="dash", line_color="#BA4F3C",
                          annotation_text=f"Average: {avg_calories:.0f} kcal", 
                          annotation_position="right")
    st.plotly_chart(fig_calories, use_container_width=True)

# Protein tab
with tabs[1]:
    fig_protein = px.bar(
        daily_totals, 
        x='Date', 
        y='Protein (g)',
        title='🥩 Daily Protein Intake'
    )
    fig_protein.update_traces(marker_color=PASTEL_COLORS['blue'])
    avg_protein = daily_totals['Protein (g)'].mean()
    fig_protein.add_hline(y=avg_protein, line_dash="dash", line_color="#1D7268",
                         annotation_text=f"Average: {avg_protein:.1f}g", 
                         annotation_position="right")
    st.plotly_chart(fig_protein, use_container_width=True)

# Carbohydrates tab
with tabs[2]:
    fig_carbs = px.bar(
        daily_totals, 
        x='Date', 
        y='Carbohydrates (g)',
        title='🍚 Daily Carbohydrate Intake'
    )
    fig_carbs.update_traces(marker_color=PASTEL_COLORS['green'])
    avg_carbs = daily_totals['Carbohydrates (g)'].mean()
    fig_carbs.add_hline(y=avg_carbs, line_dash="dash", line_color="#68935F",
                       annotation_text=f"Average: {avg_carbs:.1f}g", 
                       annotation_position="right")
    st.plotly_chart(fig_carbs, use_container_width=True)

# Sugar tab
with tabs[3]:
    fig_sugar = px.bar(
        daily_totals, 
        x='Date', 
        y='Sugar (g)',
        title='🍯 Daily Sugar Intake'
    )
    fig_sugar.update_traces(marker_color=PASTEL_COLORS['magenta'])
    avg_sugar = daily_totals['Sugar (g)'].mean()
    fig_sugar.add_hline(y=avg_sugar, line_dash="dash", line_color="#C17A60",
                       annotation_text=f"Average: {avg_sugar:.1f}g", 
                       annotation_position="right")
    st.plotly_chart(fig_sugar, use_container_width=True)

# Fat tab
with tabs[4]:
    fig_fat = px.bar(
        daily_totals, 
        x='Date', 
        y='Fat (g)',
        title='🥑 Daily Fat Intake'
    )
    fig_fat.update_traces(marker_color=PASTEL_COLORS['peach'])
    avg_fat = daily_totals['Fat (g)'].mean()
    fig_fat.add_hline(y=avg_fat, line_dash="dash", line_color="#D28745",
                     annotation_text=f"Average: {avg_fat:.1f}g", 
                     annotation_position="right")
    st.plotly_chart(fig_fat, use_container_width=True)

# Saturated Fat tab
with tabs[5]:
    fig_sat_fat = px.bar(
        daily_totals, 
        x='Date', 
        y='Saturated Fat (g)',
        title='🧈 Daily Saturated Fat Intake'
    )
    fig_sat_fat.update_traces(marker_color=PASTEL_COLORS['orange'])
    avg_sat_fat = daily_totals['Saturated Fat (g)'].mean()
    fig_sat_fat.add_hline(y=avg_sat_fat, line_dash="dash", line_color="#C9966E",
                         annotation_text=f"Average: {avg_sat_fat:.1f}g", 
                         annotation_position="right")
    st.plotly_chart(fig_sat_fat, use_container_width=True)

# Cholesterol tab
with tabs[6]:
    fig_chol = px.bar(
        daily_totals, 
        x='Date', 
        y='Cholesterol (mg)',
        title='🥚 Daily Cholesterol Intake'
    )
    fig_chol.update_traces(marker_color=PASTEL_COLORS['purple'])
    avg_chol = daily_totals['Cholesterol (mg)'].mean()
    fig_chol.add_hline(y=avg_chol, line_dash="dash", line_color="#1A2F37",
                       annotation_text=f"Average: {avg_chol:.0f}mg", 
                       annotation_position="right")
    st.plotly_chart(fig_chol, use_container_width=True)

# Fiber tab
with tabs[7]:
    fig_fiber = px.bar(
        daily_totals, 
        x='Date', 
        y='Fiber (g)',
        title='🥬 Daily Fiber Intake'
    )
    fig_fiber.update_traces(marker_color=PASTEL_COLORS['yellow_green'])
    avg_fiber = daily_totals['Fiber (g)'].mean()
    fig_fiber.add_hline(y=avg_fiber, line_dash="dash", line_color="#C9A94B",
                       annotation_text=f"Average: {avg_fiber:.1f}g", 
                       annotation_position="right")
    st.plotly_chart(fig_fiber, use_container_width=True)

# Omega-3 tab
with tabs[8]:
    fig_omega = px.bar(
        daily_totals, 
        x='Date', 
        y='Omega-3 (mg)',
        title='🐟 Daily Omega-3 Intake'
    )
    fig_omega.update_traces(marker_color=PASTEL_COLORS['mint'])
    avg_omega = daily_totals['Omega-3 (mg)'].mean()
    fig_omega.add_hline(y=avg_omega, line_dash="dash", line_color="#4F8C92",
                       annotation_text=f"Average: {avg_omega:.0f}mg", 
                       annotation_position="right")
    st.plotly_chart(fig_omega, use_container_width=True)

# Detailed nutrient analysis
st.markdown("<h1>🔍 Detailed Nutrient Analysis</h1>", unsafe_allow_html=True)
nutrients = ['Calories (kcal)', 'Protein (g)', 'Carbohydrates (g)', 'Sugar (g)',
            'Fat (g)', 'Saturated Fat (g)', 'Cholesterol (mg)', 'Fiber (g)', 'Omega-3 (mg)']

# Map nutrients to their corresponding colors from the new theme
nutrient_colors = {
    'Calories (kcal)': '#E76F51',      # Coral
    'Protein (g)': '#2A9D8F',          # Teal
    'Carbohydrates (g)': '#8AB17D',    # Sage Green
    'Sugar (g)': '#E29578',            # Light Coral
    'Fat (g)': '#F4A261',              # Peach
    'Saturated Fat (g)': '#EFBC9B',    # Light Peach
    'Cholesterol (mg)': '#264653',     # Dark Teal
    'Fiber (g)': '#E9C46A',            # Yellow/Gold
    'Omega-3 (mg)': '#7EBDC3'          # Light Teal
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
st.markdown("<h1>📋 Raw Data</h1>", unsafe_allow_html=True)
if st.checkbox("Show raw data"):
    st.dataframe(filtered_df)

# Nutrition Dashboard

A Streamlit-based dashboard for tracking and visualizing daily nutritional intake. The dashboard provides insights into caloric intake, macronutrients, and detailed nutrient analysis.

## Features

- Daily nutritional summary with current day's metrics (Singapore timezone)
- Comparison with average daily intake
- Nutritional trends visualization for:
  - Calories
  - Protein
  - Carbohydrates
  - Sugar
  - Fat
  - Saturated Fat
  - Cholesterol
  - Fiber
  - Omega-3
- Detailed nutrient analysis with top contributing foods
- Date range filtering
- Raw data view

## Data Format

Place your nutrition data in `Table 1-Grid view.csv` with the following columns:
- Input Date: Date of food intake (YYYY-MM-DD)
- Item Name: Name of the food item
- Calories (kcal): Caloric content
- Protein (g): Protein content in grams
- Carbohydrates (g): Carbohydrate content in grams
- Fat (g): Fat content in grams
- Sugar (g): Sugar content in grams
- Saturated Fat (g): Saturated fat content in grams
- Cholesterol (mg): Cholesterol content in milligrams
- Fiber (g): Fiber content in grams
- Omega-3 (mg): Omega-3 content in milligrams

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The dashboard uses Airtable as its data source. You'll need to set up the following:

1. Create a `.streamlit/secrets.toml` file with your Airtable credentials:
   ```toml
   AIRTABLE_TOKEN = "your_airtable_api_key"
   AIRTABLE_BASE_ID = "your_base_id"
   AIRTABLE_TABLE_ID = "your_table_id"
   ```

2. Make sure your Airtable table has the following required columns:
   - Input Date (Date)
   - Food Name (Text)
   - Calories (Number)
   - Protein (Number)
   - Carbohydrates (Number)
   - Fat (Number)
   - Other nutrient columns as needed

## Deployment

### Local Development

Run the app locally with:
```bash
streamlit run main.py
```

### Streamlit Cloud Deployment

1. Push your code to GitHub
2. Create a new app on [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Add your Airtable credentials in the Streamlit Cloud secrets management
5. Deploy!

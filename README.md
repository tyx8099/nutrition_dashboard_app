# Nutrition Dashboard

A Streamlit-based dashboard for tracking and visualizing daily nutritional intake. The dashboard provides insights into caloric intake, macronutrients, and detailed nutrient analysis.

## Features

- Daily nutritional summary with current day's metrics (Singapore timezone)
- Comparison with average daily intake
- Nutritional trends visualization for:
  - Calories
  - Protein
  - Carbohydrates
  - Fat
- Detailed nutrient analysis with top contributing foods
- Date range filtering
- Raw data view

## Installation

1. Clone this repository:
```bash
git clone [repository-url]
cd nutrition-dashboard-app
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:
```bash
streamlit run main.py
```

## Data Format

The dashboard expects a CSV file named "Table 1-Grid view.csv" with the following columns:
- Input Date
- Item Name
- Calories (kcal)
- Protein (g)
- Carbohydrates (g)
- Sugar (g)
- Fat (g)
- Saturated Fat (g)
- Cholesterol (mg)
- Fiber (g)
- Omega-3 (mg)

## Technologies Used

- Python
- Streamlit
- Pandas
- Plotly
- PyTZ

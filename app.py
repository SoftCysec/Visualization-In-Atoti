import atoti as tt
import pandas as pd
import sys

# read the CSV file name from the command line arguments
if len(sys.argv) < 2:
    print("Usage: python app.py <csv_file>")
    sys.exit(1)

csv_file = sys.argv[1]

# create a session
session = tt.create_session()

# load the data into atoti
store = pd.read_csv(csv_file)
data = session.read_pandas(store, "sales")

# create a cube
cube = session.create_cube(data)

# define dimensions and hierarchies
date = cube.dimension("Date", hierarchy=True)
date_level_year = date.level("Year", "Year")
date_level_month = date.level("Month", "Month", level_type="Time")
product = cube.dimension("Product", hierarchy=True)
product_level_category = product.level("Category", "Category")
product_level_subcategory = product.level("Subcategory", "Subcategory")
measures = cube.measures

# define some calculated measures
measures["SalesAmount"] = tt.agg.sum(data["Sales"])
measures["SalesQuantity"] = tt.agg.sum(data["Quantity"])
measures["AveragePrice"] = measures["SalesAmount"] / measures["SalesQuantity"]

# create the dashboard
dashboard = session.create_dashboard("Sales Dashboard")

# add the charts to the dashboard
chart1 = dashboard.create_chart(
    "Sales by Category",
    tt.plot.bar(
        product_level_category,
        measures["SalesAmount"],
        stack=date_level_year,
        colors=product_level_subcategory,
    ),
)
chart2 = dashboard.create_chart(
    "Sales by Month",
    tt.plot.line(date_level_month,
                 measures["SalesAmount"], relative_date=date_level_month[-1, 0]),
)
chart3 = dashboard.create_chart(
    "Sales by Subcategory",
    tt.plot.bar(
        product_level_subcategory,
        measures["SalesAmount"],
        stack=product_level_category,
        colors=date_level_year,
    ),
)

# display the dashboard
dashboard.preview()

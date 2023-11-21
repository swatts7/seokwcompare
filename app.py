import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

# Function to create and save chart as an image
def create_chart(data, chart_type):
    plt.figure(figsize=(10, 15))

    # Extracting relevant columns based on their positions
    keywords = data.iloc[:, 0]
    clicks_date1 = data.iloc[:, 1]
    clicks_date2 = data.iloc[:, 2]

    if chart_type == "chart1":
        # Calculate clicks lost and gained
        clicks_change = clicks_date2 - clicks_date1
        top_50_gained = data.iloc[clicks_change.nlargest(50).index]
        top_50_lost = data.iloc[clicks_change.nsmallest(50).index]

        combined_data = pd.concat([top_50_gained, top_50_lost])
        combined_data['click_change'] = combined_data.iloc[:, 2] - combined_data.iloc[:, 1]

        # Sort data for better visualization
        combined_data_sorted = combined_data.sort_values(by='click_change')

        plt.barh(combined_data_sorted.iloc[:, 0], combined_data_sorted['click_change'], 
                 color=combined_data_sorted['click_change'].apply(lambda x: 'blue' if x > 0 else 'red'))

        # Set title and labels
        plt.title('Top 50 Keywords by Click Gain/Loss', fontsize=14)
        plt.xlabel('Click Change Date1 vs Date2', fontsize=12)

        # Adjust y-axis label size for readability
        plt.yticks(fontsize=10)  # Adjust font size as needed

        # Ensure layout fits well
        plt.tight_layout()

    elif chart_type == "chart2":
        # Example logic for Chart 2 - Adjust according to your data
        # Assuming 'additional_data' should be the core_keywords DataFrame
        core_keywords_df = st.session_state['core_keywords_df']
        data['click_change'] = data.iloc[:, 2] - data.iloc[:, 1]
        core_data = data[data.iloc[:, 0].isin(core_keywords_df['Keyword'])]
        missing_keywords = len(core_keywords_df) - len(core_data)

        core_data_sorted = core_data.sort_values(by='click_change', ascending=False)
        plt.barh(core_data_sorted.iloc[:, 0], core_data_sorted['click_change'], 
                 color=core_data_sorted['click_change'].apply(lambda x: 'blue' if x > 0 else 'red'))
        plt.title('Core Keyword Click Gain/Loss', fontsize=14)
        plt.xlabel('Click Change Date1 vs Date2', fontsize=12)
        plt.yticks(fontsize=10)
        plt.tight_layout()

        # Annotation for missing keywords
        plt.figtext(0.01, 0.01, f"{missing_keywords} core keywords not found", ha="left", fontsize=10, bbox={"facecolor":"orange", "alpha":0.5, "pad":5})

    elif chart_type == "chart3":
        # Assuming the first column after 'Top queries' is 'Clicks Date1' and the next is 'Clicks Date2'
        # The columns for clicks are in positions 1 and 2 respectively
        clicks_date1_col_position = 1
        clicks_date2_col_position = 2

        # Use iloc to reference the columns by position for both obtaining the top 25 and calculating change
        top_25 = data.nlargest(25, data.columns[clicks_date1_col_position])
        top_25['click_change'] = top_25.iloc[:, clicks_date2_col_position] - top_25.iloc[:, clicks_date1_col_position]
        top_25_sorted = top_25.sort_values(by='click_change', ascending=False)

        # Create the barh plot using positions
        bars = plt.barh(top_25_sorted.iloc[:, 0], top_25_sorted['click_change'], 
                        color=top_25_sorted['click_change'].apply(lambda x: 'blue' if x > 0 else 'red'))
        plt.title('Top 25 Volume Keywords Click Gain/Loss', fontsize=14)
        plt.xlabel('Click Change Date1 vs Date2', fontsize=12)
        plt.yticks(fontsize=10)
        plt.tight_layout()

        # Annotate each bar with the respective click values
        for bar, (index, row) in zip(bars, top_25_sorted.iterrows()):
            label = f"({int(row.iloc[clicks_date1_col_position])} vs {int(row.iloc[clicks_date2_col_position])})"
            x_position = bar.get_width()
            y_position = bar.get_y() + bar.get_height() / 2
            
            # Flip the alignment based on the bar's width
            ha = 'left' if x_position < 0 else 'right'
            
            # Adjust the x_position so that the label is set away from the end of the bar
            if x_position < 0:
                x_position = -5  # Padding for left side
            else:
                x_position = 5  # Padding for right side
            
            plt.text(x_position, y_position, label, ha=ha, va='center', fontsize=8)
        
    elif chart_type == "cluster_analysis":
        # Filter out keywords with less than 20 clicks on Date 1
        filtered_data = data[data.iloc[:, 1] >= 20]

        # Calculate the percentage change in clicks
        filtered_data['percent_change_clicks'] = ((filtered_data.iloc[:, 2] - filtered_data.iloc[:, 1]) / filtered_data.iloc[:, 1]) * 100

        # Define thresholds for little change and significant change
        significant_change_threshold = 20  # Change beyond +/-20% is considered significant

        # Cluster data into categories
        bins = [-float('inf'), -significant_change_threshold, significant_change_threshold, float('inf')]
        labels = ['Negative Change', 'Little Change', 'Positive Change']
        filtered_data['change_category'] = pd.cut(filtered_data['percent_change_clicks'], bins=bins, labels=labels)

        # Standard point size and alpha for all points
        point_size = 50
        alpha = 0.6

        # Plotting the clusters with fixed point size and alpha values
        colors = {'Negative Change': 'red', 'Little Change': 'grey', 'Positive Change': 'green'}
        
        # Adding vertical grid lines for x-axis values
        plt.grid(axis='x', color='lightgrey')

        for category, color in colors.items():
            subset = filtered_data[filtered_data['change_category'] == category]
            plt.scatter(subset.iloc[:, 1], subset['percent_change_clicks'], s=point_size, c=color, alpha=alpha, label=category)

            # Annotate count of keywords in each category
            count = len(subset)
            plt.text(subset.iloc[:, 1].max(), filtered_data['percent_change_clicks'].max() * 0.9, 
                    f'{category}: {count}', fontsize=10, color=color, horizontalalignment='right')

        # Set the title and labels
        plt.title('Cluster Analysis of Clicks', fontsize=14)
        plt.xlabel('Total Clicks from Date 1', fontsize=12)
        plt.ylabel('Percentage Change in Clicks', fontsize=12)

        # Adding a legend
        plt.legend(title="Change Category")

        # Ensure the layout fits well
        plt.tight_layout()

    chart_path = f"{chart_type}.png"
    plt.savefig(chart_path)
    plt.close()
    return chart_path

# Function to generate PDF from chart images
def generate_pdf(chart_paths):
    pdf = FPDF()
    # Set PDF margins if needed
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.set_top_margin(10)
    
    for chart_path in chart_paths:
        pdf.add_page()
        # Assuming the images are saved at a resolution that fits an A4 page.
        # Adjust x, y, w, and h as needed, based on the image size.
        pdf.image(chart_path, x=10, y=8, w=180)
        # Remove the image file after adding to PDF if you don't need the image files afterwards
        os.remove(chart_path)
    
    # Return the PDF object for further actions like saving or downloading
    return pdf

# Streamlit UI
def main():
    st.title("Keyword Analysis Tool")
    st.text('Upload core keywords file and GSC queries file covering two time periods')
    st.text('Data visualizations will be generate to help you better understand changes',)

    queries_file = st.file_uploader("Upload Queries.csv", type="csv")
    core_keywords_file = st.file_uploader("Upload Core_Keywords.csv", type="csv")

    if queries_file and core_keywords_file:
        queries_df = pd.read_csv(queries_file)
        core_keywords_df = pd.read_csv(core_keywords_file)
        # Save core_keywords_df in the session state for later use
        st.session_state['core_keywords_df'] = core_keywords_df

    if st.button("Generate Charts"):
        if queries_file and core_keywords_file:
            # Create charts
            cluster_chart_path = create_chart(queries_df, "cluster_analysis")
            chart1_path = create_chart(queries_df, "chart1")
            chart2_path = create_chart(queries_df, "chart2")
            chart3_path = create_chart(queries_df, "chart3")
              # Generate the cluster chart

            # Generate PDF
            pdf = generate_pdf([cluster_chart_path, chart1_path, chart2_path, chart3_path])  # Include the cluster chart
            st.download_button("Download PDF", pdf.output(dest="S").encode("latin1"), "report.pdf", "application/pdf")
        else:
            st.error("Please upload both files.")

if __name__ == "__main__":
    main()
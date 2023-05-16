import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from io import StringIO, BytesIO
import numpy as np
import plotly.subplots as sp
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import snowflake.connector

# Set page configuration with background image
st.set_page_config(
    page_title="Snowflake Plotter 📈",
    layout="centered",
    initial_sidebar_state="expanded"
)


st.title("Snowflake Plotter 📈 ")
st.subheader('Feed me with your Snowflake Data')

def generate_excel_download_link(df):
    # Credit Excel: https://discuss.streamlit.io/t/how-to-add-a-download-excel-csv-function-to-a-button/4474/5
    towrite = BytesIO()
    df.to_excel(towrite, encoding="utf-8", index=False, header=True)  # write to BytesIO buffer
    towrite.seek(0)  # reset pointer
    b64 = base64.b64encode(towrite.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="Data.xlsx">Download Excel File</a>'
    return st.markdown(href, unsafe_allow_html=True)

#

def generate_html_download_link(fig):
    # Credit Plotly: https://discuss.streamlit.io/t/download-plotly-plot-as-html/4426/2
    towrite = StringIO()
    fig.write_html(towrite, include_plotlyjs="cdn")
    towrite = BytesIO(towrite.getvalue().encode())
    b64 = base64.b64encode(towrite.read()).decode()
    href = f'<a href="data:text/html;charset=utf-8;base64, {b64}" download="plot.html">Download Plot</a>'
    return st.markdown(href, unsafe_allow_html=True)

st.sidebar.header("Snowflake Credentials")
snowflake_user = st.sidebar.text_input("User")
snowflake_password = st.sidebar.text_input("Password", type="password")
snowflake_account = st.sidebar.text_input("Account")
snowflake_database = st.sidebar.text_input("Database")
snowflake_schema = st.sidebar.text_input("Schema")
snowflake_warehouse = st.sidebar.text_input("Warehouse")
snowflake_table = st.sidebar.text_input("Table")

submit_button = st.sidebar.button("Connect to Snowflake")

try:
    conn = snowflake.connector.connect(
        user=snowflake_user,
        password=snowflake_password,
        account=snowflake_account,
        warehouse=snowflake_warehouse,
        database=snowflake_database,
        schema=snowflake_schema
    )
    st.sidebar.success("Connected to Snowflake")
    
    query = f"SELECT * FROM \"{snowflake_database}\".\"{snowflake_schema}\".\"{snowflake_table}\""
    df = pd.read_sql(query, conn)
    st.dataframe(df)
        
    groupby_column = st.selectbox(
        'What would you like to Analyse?',
        df.columns.tolist(),
    )
    
    filtered_df = df[df[groupby_column].notnull()]
    
    metric_columns = []
    for column in filtered_df.columns:
        if np.issubdtype(filtered_df[column].dtype, np.number):
            metric_columns.append(column)
   
    output_columns = st.multiselect(
        'Select metric columns for analysis',
        metric_columns,
        default=[]
    )
   
    df_grouped = filtered_df.groupby(by=groupby_column, as_index=False)[output_columns].sum()
    st.dataframe(df_grouped)
    
    st.title("Snowflake KPI - Key Metric Dashboard")
    
    kpi_metric_column = st.selectbox("Select a metric column fro KPI Chart's:", metric_columns, key='metric_select')

    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        avg_value1 = np.mean(df_grouped[kpi_metric_column])
        avg_value_rounded1 = round(avg_value1, 2)
        kpi1.metric(label=f"Average {kpi_metric_column}", value=avg_value_rounded1)
    
    with kpi2:
        avg_value2 = np.max(df_grouped[kpi_metric_column])
        avg_value_rounded2 = round(avg_value2, 2)
        kpi2.metric(label=f"Maximum {kpi_metric_column}", value=avg_value_rounded2)
    
    with kpi3:
        avg_value3 = np.min(df_grouped[kpi_metric_column])
        avg_value_rounded3 = round(avg_value3, 2)
        kpi3.metric(label=f"Minimum {kpi_metric_column}", value=avg_value_rounded3)
        
    st.markdown("----")
 
    fig = sp.make_subplots(rows=len(output_columns), cols=2, subplot_titles=["Bar Chart", "Line Chart"])

    for i, col in enumerate(output_columns, 1):
        fig.add_trace(
            go.Bar(x=df_grouped[groupby_column], y=df_grouped[col], name=col),
            row=i,
            col=1
        )
        
        fig.add_trace(
            go.Line(x=df_grouped[groupby_column], y=df_grouped[col], name=col),
            row=i,
            col=2
        )
    
    fig.update_layout(
        height=500 * len(output_columns),
        showlegend=True,
        template='plotly_white',
        title=f'<b>Sales & Profit by {groupby_column}</b>'
    )
    
    st.plotly_chart(fig)
    

    
    st.subheader('Downloads:')
    generate_excel_download_link(df_grouped)
    generate_html_download_link(fig)
    
except Exception as e:
    st.sidebar.error(f"Error connecting to Snowflake: {e}")
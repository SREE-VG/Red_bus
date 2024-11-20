import streamlit as st
import pymysql
from pymysql import Error
import pandas as pd
import numpy as np
import time
import qrcode
from PIL import Image
import io

# Function to handle timedelta to HH:MM format conversion
def timedelta_to_hhmm(value):
    t_seconds = value.seconds
    hours = t_seconds // 3600  # 1 hour = 3600 seconds
    minutes = (t_seconds % 3600) // 60  # 1 hour = 60 minutes
    return f"{hours:02}:{minutes:02}"  # Formatting to 00:00

# Function to configure database connection
def configuration():
    try:
        connection = pymysql.connect(
            host='localhost', user='root', password='09876', database='red_bus')
        print("Connection successful")
        return connection
    except Error as e:
        print("Error occurred during configuration:", e)

# Function to connect to the MySQL database
def connect():
    try:
        conn = configuration()
        if conn is None:
            return None
        if conn.open:
            print("Connection completed")
        return conn
    except Error as e:
        print("Error occurred when opening connection:", e)

# Function to use the selected database
def use_database(conn, query_database):
    with conn.cursor() as c:
        try:
            c.execute(query_database)
            print("Using the selected database")
        except Error as e:
            print("Error occurred when selecting database:", e)

# Function to fetch distinct values (like state names)
def fetch_distinct_value(conn, query_distinct):
    with conn.cursor() as c:
        try:
            c.execute(query_distinct)
            result = [row[0] for row in c.fetchall()]
            print("Fetched distinct values")
            return result
        except Error as e:
            print("Error occurred when fetching distinct values:", e)

# Function to fetch route names based on the state
def fetch_route_names(conn, query_routes_names):
    with conn.cursor() as c:
        try:
            c.execute(query_routes_names)
            result = [row[0] for row in c.fetchall()]
            print("Fetched route names")
            return result
        except Error as e:
            print("Error occurred when fetching route names:", e)

# Function to fetch filtered data based on user input
def fetch_filtered_value(conn, query_filtered_value):
    with conn.cursor() as c:
        try:
            c.execute(query_filtered_value)
            columns = [desc[0] for desc in c.description]
            data = c.fetchall()
            df = pd.DataFrame(data, columns=columns, index=[index + 1 for index in range(len(data))])

            # Apply formatting if columns exist
            if "departing_time" in df.columns:
                df["departing_time"] = df["departing_time"].apply(timedelta_to_hhmm)
            if "reaching_time" in df.columns:
                df["reaching_time"] = df["reaching_time"].apply(timedelta_to_hhmm)
            if "star_rating" in df.columns:
                df['star_rating'] = df['star_rating'].replace(0.0, np.nan)
            return df
        except Error as e:
            print("Error occurred when fetching filtered data:", e)
            return pd.DataFrame()

# Close the database connection
def close_connection(conn):
    try:
        conn.close()
        print("Connection closed successfully")
    except Error as e:
        print("Error occurred when closing the connection:", e)

# Function to generate and display QR code for Play Store
def generate_qr_code(play_store_url):
    # Generate QR code with smaller size
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,  # Smaller box size for a smaller QR code
        border=4,
    )
    qr.add_data(play_store_url)
    qr.make(fit=True)

    # Create a PIL image from the QR code
    img = qr.make_image(fill='black', back_color='white')

    # Convert PIL Image to BytesIO (bytes-like object)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # Display the image in Streamlit
    col1, col2, col3 = st.columns([1, 1, 1])  # Adjust the width ratio as per your needs

    with col1:
        st.image(img_byte_arr, caption="Scan to Download Redbus App", width=150)

    # RED BUS ICON
    with col2:
        red_bus_icon = "http://st.redbus.in/Images/carousel/homepage_general.png"
        st.image(red_bus_icon, caption="Travel Everywhere", width=150)  

    with col3:
        play_store_icon = "https://vectorified.com/images/google-play-store-icon-size-3.png"
        st.image(play_store_icon, caption="Download the App on", width=200)  # Fixed width for Play Store icon


# Connect to the database
conn = connect()

# Use the database
use_database(conn, "USE red_bus;")

# Setting page configuration for Streamlit
st.set_page_config(
    page_title="Redbus - Search and Book Your Bus 🚌",
    page_icon=":oncoming_bus:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar Navigation
with st.sidebar:
    st.title("Redbus")
    st.markdown("Book Your Ride 🚌")
    selected = st.radio("Select Option", ["Home", "Search Bus"])

# If "Home" is selected
if selected == "Home":
    st.title(":red[REDBUS] - Your ticket to less stress 🚌")
    st.markdown(""" 
    Redbus is an online bus ticketing platform founded in 2006 in India. 
    It allows users to book bus tickets through its website and mobile app, 
    providing access to a wide network of bus operators across various routes. 
    """)
    st.image("https://akm-img-a-in.tosshub.com/indiatoday/images/story/202204/redbus_1200x768.png?VersionId=JXyxPyUZzox7t3MdV6IBbiu1NbhivRvE&size=690:388", caption="Redbus Booking", use_container_width=True)

    # Generate and display the QR code for the Play Store URL
    play_store_url = "https://play.google.com/store/apps/details?id=com.redbus.android"
    generate_qr_code(play_store_url)

# If "Search Bus" is selected
if selected == "Search Bus":
    st.title(":red[REDBUS] - 🔍 Search Bus")

    col1, col2 = st.columns([4, 1])

    with col1:
        state_query = "SELECT DISTINCT state_name FROM route_data;"
        state_names = fetch_distinct_value(conn, state_query)
        state_name = st.selectbox("State", ['--- Select State ---'] + state_names)
        
        if state_name != '--- Select State ---':
            route_query = f"SELECT route_name FROM route_data WHERE state_name = '{state_name}';"
            route_names = fetch_route_names(conn, route_query)
            route_name = st.selectbox("Route", ['--- Select Route ---'] + route_names)

    with col2:
        bus_types_query = "SELECT DISTINCT bus_type FROM bus_data;"
        bus_types = fetch_distinct_value(conn, bus_types_query)
        bus_type = st.selectbox("Bus Type", ['--- Select Bus Type ---'] + bus_types)
        
        price_range = st.slider("Price Range", min_value=0, max_value=3000, value=(0, 3000), step=100)
        min_price, max_price = price_range
        
        rating = st.slider("Star Rating", min_value=0, max_value=5, value=(0, 5), step=1)
        min_rating, max_rating = rating

    if st.button("Search"):
        query = f"""
        SELECT r.route_name, r.route_link, b.bus_name, b.bus_type, b.departing_time, 
               b.duration, b.reaching_time, b.star_rating, b.price, b.seat_available
        FROM route_data r
        JOIN bus_data b ON r.route_no = b.bus_no
        WHERE r.state_name = '{state_name}' 
        AND r.route_name = '{route_name}' 
        AND (b.bus_type = '{bus_type}' OR '{bus_type}' = 'All') 
        AND b.star_rating BETWEEN {min_rating} AND {max_rating}
        AND b.price BETWEEN {min_price} AND {max_price};
        """
        
        with st.spinner('Searching...'):
            time.sleep(2)
            filtered_data = fetch_filtered_value(conn, query)
        
        if not filtered_data.empty:
            st.dataframe(filtered_data)
        else:
            st.markdown("<h4>Sorry, no buses found for the selected filters</h4>", unsafe_allow_html=True)

# Close the database connection at the end
close_connection(conn)



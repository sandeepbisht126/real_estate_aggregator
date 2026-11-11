import streamlit as st
import pandas as pd
import asyncio
import sys
import os
from sqlalchemy import create_engine, text

# Add parent directory to path to import main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import run

# -------------------------
# DATABASE
# -------------------------

engine = create_engine(
    "postgresql://postgres:postgres@localhost/properties"
)

# -------------------------
# PAGE CONFIG
# -------------------------

st.set_page_config(
    page_title="Property Aggregator",
    layout="wide"
)

# -------------------------
# CUSTOM CSS
# -------------------------

st.markdown("""
<style>

/* Main container */
.block-container {
    padding-top: 0.7rem;
    padding-bottom: 1rem;
}

/* Sidebar width */
section[data-testid="stSidebar"] {
    width: 300px !important;
    min-width: 300px !important;
    max-width: 300px !important;
}

/* Compact sidebar spacing */
section[data-testid="stSidebar"] .stTextInput,
section[data-testid="stSidebar"] .stNumberInput,
section[data-testid="stSidebar"] .stSelectbox,
section[data-testid="stSidebar"] .stCheckbox {

    margin-bottom: -0.3rem !important;
}

/* Compact labels */
section[data-testid="stSidebar"] label {

    font-size: 12px !important;

    font-weight: 600 !important;

    margin-bottom: 0px !important;
}

/* Reduce widget padding */
section[data-testid="stSidebar"] div[data-baseweb="input"] {
    min-height: 34px !important;
}

/* Sidebar title */
.sidebar-title {

    font-size: 18px;

    font-weight: 700;

    margin-bottom: 0.5rem;

    color: #1f2937;
}

/* Apply button */
div.stButton > button {

    background: linear-gradient(
        90deg,
        #2563eb,
        #1d4ed8
    ) !important;

    color: white !important;

    border: none !important;

    border-radius: 10px !important;

    font-size: 15px !important;

    font-weight: 700 !important;

    height: 42px !important;

    width: 100% !important;

    margin-top: 0.7rem !important;

    transition: all 0.25s ease;
}

/* Apply button hover */
div.stButton > button:hover {

    background: linear-gradient(
        90deg,
        #1d4ed8,
        #1e40af
    ) !important;

    transform: scale(1.01);

    color: white !important;
}

/* TABLE */
table {

    width: 100%;

    border-collapse: collapse;

    font-size: 14px;

    border: 1px solid #d9d9d9;
}

/* TABLE HEADER */
thead tr th {

    background-color: #1f2937 !important;

    color: white !important;

    padding: 12px !important;

    text-align: center !important;

    vertical-align: middle !important;

    font-size: 13px !important;

    font-weight: 700 !important;

    border: 1px solid #4b5563 !important;
}

/* Zebra rows */
tbody tr:nth-child(even) {
    background-color: #f8fafc;
}

tbody tr:nth-child(odd) {
    background-color: white;
}

/* Row hover */
tbody tr:hover {
    background-color: #dbeafe !important;
}

/* Table cells */
tbody td {

    padding: 10px !important;

    border: 1px solid #e5e7eb !important;

    text-align: center !important;

    vertical-align: middle !important;

    font-size: 13px;
}

/* Links */
a {

    text-decoration: none;

    color: #2563eb !important;

    font-weight: 600;
}

a:hover {
    text-decoration: underline;
}

/* Summary text */
h3 {
    margin-top: 0.2rem !important;
}

</style>
""", unsafe_allow_html=True)

# -------------------------
# TITLE
# -------------------------

st.title("🏠 Property Aggregator")

# -------------------------
# SIDEBAR FILTERS
# -------------------------

with st.sidebar.form("filters_form"):

    st.markdown(
        '<div class="sidebar-title">🔍 Filters</div>',
        unsafe_allow_html=True
    )

    # Berlin areas for multiselect
    berlin_areas = [
        "ALL",
        "Berlin",
        "Mitte",
        "Prenzlauer Berg",
        "Charlottenburg",
        "Kreuzberg",
        "Neukölln",
        "Adlershof",
        "Pankow",
        "Steglitz",
        "Tempelhof",
        "Köpenick",
        "Lichtenberg",
        "Reinickendorf",
        "Neu-Hohenschönhausen",
        "Alt-Hohenschönhausen",
        "Hohenschönhausen"
    ]
    
    selected_areas = st.multiselect(
        "Area",
        options=berlin_areas,
        default=["ALL"]
    )
    
    # Convert to single area string for filtering
    if "ALL" in selected_areas or not selected_areas:
        area = ""
    else:
        area = selected_areas[0] if len(selected_areas) == 1 else ",".join(selected_areas)

    min_price = st.number_input(
        "Min Price (€)",
        min_value=0,
        max_value=5000000,
        value=200000,
        step=10000
    )

    max_price = st.number_input(
        "Max Price (€)",
        min_value=0,
        max_value=5000000,
        value=350000,
        step=10000
    )

    min_rooms = st.number_input(
        "Min Rooms",
        min_value=0.0,
        max_value=10.0,
        value=2.5,
        step=0.5
    )

    max_rooms = st.number_input(
        "Max Rooms",
        min_value=0.0,
        max_value=10.0,
        value=4.0,
        step=0.5
    )

    min_space = st.number_input(
        "Min Living Space (sqm)",
        min_value=0,
        max_value=1000,
        value=70
    )

    max_space = st.number_input(
        "Max Living Space (sqm)",
        min_value=0,
        max_value=1000,
        value=120
    )

    property_type = st.multiselect(
        "Property Type",
        ["Apartment", "House"],
        default=["Apartment", "House"]
    )

    max_hausgeld = st.number_input(
        "Max Hausgeld",
        value=400
    )

    balcony_only = st.checkbox(
        "Balcony Only"
    )

    posted_filter = st.selectbox(
        "Posted In",
        options=[
            "All",
            "Last 24 Hours",
            "Last 48 Hours",
            "Last 72 Hours",
            "Last 7 Days",
            "Last 14 Days",
            "Last 30 Days"
        ]
    )

    use_fast_scrape = st.checkbox(
        "🔄 Fast Scrape (Latest 10 Properties)",
        value=False,
        help="Scrape latest 10 properties directly without database"
    )
    
    force_refresh = st.checkbox(
        "🔄 Force Refresh (Ignore Cache)",
        value=False,
        help="Re-scrape even if cache is available"
    )

    apply_filters = st.form_submit_button(
        "🚀 Apply Filters",
        use_container_width=True
    )

# -------------------------
# LOAD DATA
# -------------------------

if apply_filters:
    
    # Fast scrape mode
    if use_fast_scrape:
        # Create progress bar and status placeholder
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(progress, message):
            """Callback to update Streamlit progress"""
            progress_bar.progress(progress)
            status_text.text(message)
        
        try:
            # Run fast scrape with progress callback and filters
            properties = asyncio.run(
                run(
                    max_scan_pages=2,
                    use_database=False,
                    max_results=10,
                    fast_mode=True,
                    progress_callback=progress_callback,
                    filters={
                        'min_price': min_price,
                        'max_price': max_price,
                        'min_rooms': min_rooms,
                        'max_rooms': max_rooms,
                        'min_space': min_space,
                        'max_space': max_space,
                        'area': area
                    },
                    use_cache=not force_refresh
                )
            )
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            if properties:
                df = pd.DataFrame(properties)
                if force_refresh:
                    st.success(f"✅ Scraped {len(df)} latest properties (force refresh)!")
                else:
                    st.success(f"✅ Loaded {len(df)} latest properties!")
            else:
                st.warning("No properties found.")
                df = pd.DataFrame()
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Error during fast scrape: {e}")
            df = pd.DataFrame()
    else:
        # Database mode
        query = """
        SELECT *
        FROM properties
        WHERE
            price BETWEEN :min_price AND :max_price

            AND rooms BETWEEN :min_rooms AND :max_rooms

            AND living_space BETWEEN :min_space AND :max_space

            AND area ILIKE :area
            
            AND hausgeld <= :max_hausgeld
        """

        # Balcony filter

        if balcony_only:

            query += """
            AND balcony = TRUE
            """

        # Posted date filter

        if posted_filter == "Last 24 Hours":

            query += """
            AND posted_date >= NOW() - INTERVAL '24 HOURS'
            """

        elif posted_filter == "Last 48 Hours":

            query += """
            AND posted_date >= NOW() - INTERVAL '48 HOURS'
            """

        elif posted_filter == "Last 72 Hours":

            query += """
            AND posted_date >= NOW() - INTERVAL '72 HOURS'
            """

        elif posted_filter == "Last 7 Days":

            query += """
            AND posted_date >= NOW() - INTERVAL '7 DAYS'
            """

        elif posted_filter == "Last 14 Days":

            query += """
            AND posted_date >= NOW() - INTERVAL '14 DAYS'
            """

        elif posted_filter == "Last 30 Days":

            query += """
            AND posted_date >= NOW() - INTERVAL '30 DAYS'
            """

        # Sorting
        query += """
        ORDER BY posted_date DESC NULLS LAST
        """

        params = {
            "min_price": min_price,
            "max_price": max_price,
            "min_rooms": min_rooms,
            "max_rooms": max_rooms,
            "min_space": min_space,
            "max_space": max_space,
            "area": f"%{area}%",
            "max_hausgeld": max_hausgeld
        }

        df = pd.read_sql(
            text(query),
            engine,
            params=params
        )

    # -------------------------
    # CLEAN DATA
    # -------------------------

    if not df.empty:
        df = df.fillna("")
        
        # Apply additional filters for fast scrape mode
        # (scraper already uses price/rooms/space filters, but we still filter by hausgeld, balcony, area)
        if use_fast_scrape:
            # Filter by hausgeld (handle empty strings safely)
            df["hausgeld_numeric"] = pd.to_numeric(df["hausgeld"], errors="coerce").fillna(0)
            df = df[df["hausgeld_numeric"] <= max_hausgeld]
            df = df.drop(columns=["hausgeld_numeric"])
            
            # Filter by area (handle multiple areas)
            if area and area != "":
                if "," in area:
                    # Multiple areas selected
                    area_list = [a.strip().lower() for a in area.split(",")]
                    df = df[df["area"].astype(str).str.lower().apply(lambda x: any(a in x for a in area_list))]
                else:
                    # Single area
                    df = df[df["area"].astype(str).str.lower().str.contains(area.lower(), na=False)]
            
            # Filter by balcony
            if balcony_only:
                df = df[df["balcony"] == True]
            
            # Sort by posted date
            df = df.sort_values(by="posted_date", ascending=False)
    else:
        df = pd.DataFrame()

    # Year formatting

    if "year_built" in df.columns:

        df["year_built"] = df["year_built"].apply(
            lambda x:
            str(int(float(x)))
            if x != ""
            else ""
        )

    # Posted date formatting

    if "posted_date" in df.columns:

        df["posted_date"] = pd.to_datetime(
            df["posted_date"],
            errors="coerce"
        ).dt.strftime("%d-%m-%Y %H:%M")

        df["posted_date"] = df[
            "posted_date"
        ].fillna("")

    # -------------------------
    # SUMMARY
    # -------------------------

    st.subheader(
        f"Found {len(df)} Properties"
    )

    # -------------------------
    # TABLE VIEW
    # -------------------------

    if not df.empty:

        display_df = df.copy()

        display_df["Price"] = display_df["price"].apply(
            lambda x:
            f"€{float(x):,.0f}"
            if x != ""
            else ""
        )

        display_df["Hausgeld"] = display_df["hausgeld"].apply(
            lambda x:
            f"€{float(x):,.0f}"
            if x != ""
            else ""
        )

        display_df["Living Space"] = display_df[
            "living_space"
        ].apply(
            lambda x:
            f"{x}"
            if x != ""
            else ""
        )

        display_df["Property Link"] = display_df["url"].apply(
            lambda x:
            f'<a href="{x}" target="_blank">Open Listing</a>'
            if x != ""
            else ""
        )

        display_df = display_df[
            [
                "title",
                "Price",
                "rooms",
                "Living Space",
                "floor",
                "Hausgeld",
                "property_type",
                "year_built",
                "energy_class",
                "posted_date",
                "Property Link"
            ]
        ]

        display_df.columns = [
            "Title",
            "Price",
            "Rooms",
            "Living Space",
            "Floor",
            "Hausgeld",
            "Property Type",
            "Year Built",
            "Energy Class",
            "Posted Date",
            "Property Link"
        ]

        st.markdown(
            display_df.to_html(
                escape=False,
                index=False
            ),
            unsafe_allow_html=True
        )

    else:

        st.warning(
            "No properties found."
        )

else:

    st.info(
        "Select filters and click 'Apply Filters'."
    )
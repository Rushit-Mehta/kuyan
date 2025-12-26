"""
KUYAN - Monthly Net Worth Tracker
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from database import Database
from currency import CurrencyConverter
from version import __version__
import json
import os


# Detect sandbox mode from query parameters
query_params = st.query_params
is_sandbox = query_params.get("mode") == "sandbox"

# Page config
st.set_page_config(
    page_title="KUYAN - Net Worth Tracker" + (" [SANDBOX]" if is_sandbox else ""),
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize database (sandbox or production)
@st.cache_resource
def init_db(sandbox_mode=False):
    db_path = "kuyan-sandbox.db" if sandbox_mode else "kuyan.db"

    db = Database(db_path=db_path)

    # Create sandbox database with sample data if it doesn't exist
    if sandbox_mode:
        # Check if database is empty (no accounts)
        accounts = db.get_accounts()
        if len(accounts) == 0:
            db.seed_sample_data()

    return db


db = init_db(sandbox_mode=is_sandbox)


# ===== CONSTANTS =====
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


# ===== HELPER FUNCTIONS =====

def get_default_currency():
    """Get the default base currency (first enabled currency)"""
    codes = db.get_currency_codes()
    return codes[0] if codes else "CAD"


def get_rates_from_snapshot(snapshot):
    """Extract exchange rates from a snapshot, returning empty dict if not present"""
    return json.loads(snapshot["exchange_rates"]) if snapshot.get("exchange_rates") else {}


def show_success_toast(item_type):
    """
    Display success toast if an item was just added

    Args:
        item_type: Type of item (e.g., 'account', 'currency', 'owner')
    """
    state_key = f'{item_type}_added'
    name_key = f'added_{item_type}_name'
    code_key = f'added_{item_type}_code'

    if st.session_state.get(state_key, False):
        # Try to get name first, fall back to code
        item_name = st.session_state.get(name_key, st.session_state.get(code_key, ''))
        icons = {'account': '🏦', 'currency': '💱', 'owner': '👥'}
        icon = icons.get(item_type, '✅')
        st.toast(f"{item_type.capitalize()} '{item_name}' added successfully!", icon=icon)
        st.session_state[state_key] = False


def render_snapshot_log(snapshots, base_currency, rates):
    """
    Render a formatted log of snapshots grouped by owner

    Args:
        snapshots: List of snapshot dictionaries
        base_currency: Currency code for conversion
        rates: Exchange rate dictionary
    """
    owners = db.get_owners()
    owner_names = [owner['name'] for owner in owners]
    currency_symbol = get_currency_symbol(base_currency)

    log_entries = []
    for owner_name in owner_names:
        owner_snapshots = [s for s in snapshots if s['owner'] == owner_name]

        if owner_snapshots:
            log_entries.append(f"  **{owner_name}:**")

            for snapshot in owner_snapshots:
                converted_value = get_converted_value(
                    snapshot["balance"],
                    snapshot["currency"],
                    base_currency,
                    rates
                )

                acc_symbol = get_currency_symbol(snapshot['currency'])
                entry = (
                    f"    • {snapshot['name']} ({snapshot['account_type']}): "
                    f"`{acc_symbol}{snapshot['balance']:,.2f}` {snapshot['currency']}"
                )
                if snapshot['currency'] != base_currency:
                    entry += f" = `{currency_symbol}{converted_value:,.2f}` {base_currency}"

                log_entries.append(entry)

    st.markdown("\n".join(log_entries))


def apply_chart_theme(fig, colors, xaxis_title=None, yaxis_title=None, show_legend=False, legend_title=""):
    """
    Apply consistent KUYAN theme styling to a Plotly chart

    Args:
        fig: Plotly figure object
        colors: Theme colors dictionary from get_theme_colors()
        xaxis_title: Optional x-axis title
        yaxis_title: Optional y-axis title
        show_legend: Whether to show legend
        legend_title: Title for legend (if show_legend=True)
    """
    layout_config = {
        'xaxis': dict(
            showline=True,
            linewidth=2,
            linecolor=colors['plot_axis'],
            mirror=False,
            showgrid=True,
            gridwidth=1,
            gridcolor=colors['plot_grid'],
            title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
            showspikes=True,
            spikecolor=colors['plot_axis'],
            spikethickness=1
        ),
        'yaxis': dict(
            showline=True,
            linewidth=2,
            linecolor=colors['plot_axis'],
            mirror=False,
            showgrid=True,
            gridwidth=1,
            gridcolor=colors['plot_grid'],
            title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
            showspikes=True,
            spikecolor=colors['plot_axis'],
            spikethickness=1
        ),
        'plot_bgcolor': colors['plot_bg'],
        'paper_bgcolor': colors['plot_bg'],
        'font': dict(color=colors['plot_text']),
        'title_font': dict(color=colors['text_primary']),
        'hoverlabel': dict(
            bgcolor=colors['surface'],
            font_size=13,
            font_family="Arial, sans-serif",
            font_color=colors['text_primary']
        ),
        'hovermode': 'x unified'
    }

    if xaxis_title:
        layout_config['xaxis']['title'] = xaxis_title
    if yaxis_title:
        layout_config['yaxis']['title'] = yaxis_title

    if show_legend:
        layout_config['legend'] = dict(
            title=dict(text=legend_title, font=dict(weight='bold', color=colors['text_primary'])),
            bgcolor=colors['surface'],
            bordercolor=colors['border'],
            borderwidth=1,
            font=dict(color=colors['text_primary'])
        )

    fig.update_layout(**layout_config)
    return fig


# Custom CSS for button styling
def inject_custom_css():
    """Inject custom CSS to override default Streamlit button colors"""
    st.markdown("""
        <style>
        /* Primary button styling - Blue-Gray color */
        button[kind="primary"] {
            background-color: #6B7C93 !important;
            border-color: #6B7C93 !important;
        }
        button[kind="primary"]:hover {
            background-color: #5B6D82 !important;
            border-color: #5B6D82 !important;
        }
        button[kind="primary"]:active {
            background-color: #4B5D72 !important;
            border-color: #4B5D72 !important;
        }

        /* Reduce divider padding in sidebar */
        section[data-testid="stSidebar"] hr {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }

        /* Ensure sidebar overlays on top of sandbox banner */
        section[data-testid="stSidebar"] {
            z-index: 1000001 !important;
        }

        /* Hide all image hover elements in sidebar */
        section[data-testid="stSidebar"] button[data-testid="stBaseButton-elementToolbar"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stElementToolbar"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] .st-emotion-cache-1v0mbdj {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)


# Sandbox mode floating banner
def render_sandbox_banner():
    """Render a floating top banner for sandbox mode"""
    if is_sandbox:
        st.markdown("""
        <div style="
            position: fixed;
            top: 0;
            left: 50px;
            right: 0;
            background: #fef9f3;
            color: #7a6f5d;
            padding: 10px 20px;
            text-align: center;
            font-size: 15px;
            z-index: 1000000;
            border-bottom: 1px solid #e8dcc8;
        ">
            Sandbox Mode
        </div>
        <div style="height: 40px;"></div>
        """, unsafe_allow_html=True)


# ===== THEME COLOR SYSTEM =====
# Comprehensive color palette that works elegantly with Streamlit's native theme detection

def is_dark_theme():
    """Detect if the active theme is dark using Streamlit's native theme detection"""
    try:
        return st.context.theme.type == "dark"
    except:
        # Fallback if st.context.theme is not available
        return False

def get_theme_colors():
    """
    Returns a comprehensive color palette based on the active Streamlit theme.
    Uses native st.context.theme for elegant theme detection.
    """
    is_dark = is_dark_theme()

    if is_dark:
        return {
            # Backgrounds
            'bg_primary': '#0E1117',      # Main background
            'bg_secondary': '#262730',    # Cards, containers
            'bg_tertiary': '#1E1E1E',     # Tables, alternating rows

            # Text colors
            'text_primary': '#FAFAFA',    # Main text
            'text_secondary': '#A3A8B8',  # Secondary text
            'text_muted': '#6C7A89',      # Muted/disabled text

            # Accent colors
            'accent_primary': '#6B7C93',  # Primary accent (Blue-Gray)
            'accent_secondary': '#0068C9', # Secondary accent (Streamlit blue)

            # UI Elements
            'border': '#3D3D3D',          # Borders, dividers
            'surface': '#262730',         # Elevated surfaces
            'surface_hover': '#31333C',   # Hover states

            # Chart colors
            'plot_bg': '#0E1117',         # Plot background
            'plot_grid': '#2D2D2D',       # Grid lines
            'plot_axis': '#6C7A89',       # Axis lines
            'plot_text': '#FAFAFA',       # Chart text

            # Table colors
            'table_row_even': '#262730',  # Even rows
            'table_row_odd': '#0E1117',   # Odd rows
            'table_header': '#31333C',    # Table headers
        }
    else:
        return {
            # Backgrounds
            'bg_primary': '#FFFFFF',      # Main background
            'bg_secondary': '#F0F2F6',    # Cards, containers
            'bg_tertiary': '#FAFAFA',     # Tables, alternating rows

            # Text colors
            'text_primary': '#262730',    # Main text
            'text_secondary': '#6C7A89',  # Secondary text
            'text_muted': '#A3A8B8',      # Muted/disabled text

            # Accent colors
            'accent_primary': '#6B7C93',  # Primary accent (Blue-Gray)
            'accent_secondary': '#0068C9', # Secondary accent (Streamlit blue)

            # UI Elements
            'border': '#E0E0E0',          # Borders, dividers
            'surface': '#FFFFFF',         # Elevated surfaces
            'surface_hover': '#F0F2F6',   # Hover states

            # Chart colors
            'plot_bg': '#FFFFFF',         # Plot background
            'plot_grid': '#E0E0E0',       # Grid lines
            'plot_axis': '#6C7A89',       # Axis lines
            'plot_text': '#262730',       # Chart text

            # Table colors
            'table_row_even': '#FFFFFF',  # Even rows
            'table_row_odd': '#F8F9FA',   # Odd rows
            'table_header': '#F0F2F6',    # Table headers
        }


# ===== REUSABLE TABLE COMPONENT =====
# Provides consistent table styling across the app

def render_data_table(data, columns=None, hide_index=True):
    """
    Render a styled dataframe with consistent theme-aware formatting.

    Args:
        data: List of dictionaries or pandas DataFrame
        columns: Optional list of column names to display (in order)
        hide_index: Whether to hide the index column (default: True)

    Returns:
        Displays the styled dataframe
    """
    import pandas as pd

    # Convert to DataFrame if needed
    if not isinstance(data, pd.DataFrame):
        df = pd.DataFrame(data)
    else:
        df = data

    # Select and order columns if specified
    if columns:
        df = df[columns]

    # Apply alternating row colors using theme palette
    colors = get_theme_colors()
    styled_df = df.style.apply(
        lambda x: [f'background-color: {colors["table_row_even"]}' if i % 2 == 0
                   else f'background-color: {colors["table_row_odd"]}' for i in range(len(x))],
        axis=0
    )

    st.dataframe(styled_df, width="stretch", hide_index=hide_index)


# ===== REUSABLE CURRENCY SELECTOR COMPONENT =====
# Provides consistent currency selection across the app

def render_currency_selector(label="Select Currency", default_index=0, key=None):
    """
    Render a currency selector dropdown with consistent formatting.

    Args:
        label: Label for the dropdown (default: "Select Currency")
        default_index: Index of default selection (defaults to first currency)
        key: Unique key for the selectbox (required if multiple selectors on same page)

    Returns:
        str: Selected currency code
    """
    # Get enabled currencies from database
    enabled_currencies = db.get_currency_codes()

    # Ensure default_index is valid
    if default_index >= len(enabled_currencies):
        default_index = 0

    selected = st.selectbox(
        label,
        options=enabled_currencies,
        index=default_index,
        key=key
    )
    return selected


# Sidebar
def render_sidebar():
    with st.sidebar:
        # Logo - centered, 55% of previous size (27.5% of sidebar width)
        col1, col2, col3 = st.columns([0.3625, 0.275, 0.3625])
        with col2:
            st.image("assets/logo.png", width="stretch")

        # Centered title and captions
        st.markdown("<h1 style='text-align: center;'>KUYAN</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 0.875rem; color: gray;'>Monthly Net Worth Tracker</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 0.875rem; color: gray;'>v{__version__}</p>", unsafe_allow_html=True)

        st.divider()

        # Initialize navigation in session state
        if "settings_nav" not in st.session_state:
            st.session_state.settings_nav = None

        # Navigation buttons
        if st.button("📊 Dashboard", width="stretch"):
            st.session_state.settings_nav = None
            st.rerun()

        st.divider()

        # Settings section (ascending order)
        if st.button("🏦 Accounts", width="stretch"):
            st.session_state.settings_nav = "Accounts"
            st.rerun()

        if st.button("💱 Currencies", width="stretch"):
            st.session_state.settings_nav = "Currencies"
            st.rerun()

        if st.button("👥 Owners", width="stretch"):
            st.session_state.settings_nav = "Owners"
            st.rerun()

        st.divider()

        # Tools section (ascending order)
        render_tool_button(
            icon="📅",
            label="Calendar Invite",
            state_key="calendar_panel_open",
            widget_renderer=render_calendar_widget
        )

        render_tool_button(
            icon="🧮",
            label="Calculator",
            state_key="calculator_panel_open",
            widget_renderer=render_calculator_widget
        )

        render_tool_button(
            icon="📥",
            label="Export Dashboard",
            state_key="export_panel_open",
            widget_renderer=render_export_widget
        )

        render_tool_button(
            icon="💹",
            label="Exchange Rate",
            state_key="exchange_rate_panel_open",
            widget_renderer=render_exchange_rate_widget_inline
        )

        page = st.session_state.settings_nav

        # Sandbox reset button
        if is_sandbox:
            st.divider()
            if st.button("🔄 Reset Sandbox", type="secondary", width="stretch"):
                show_reset_confirmation()

        return page


@st.dialog("Reset Sandbox Confirmation")
def show_reset_confirmation():
    """Show confirmation dialog for sandbox reset"""
    st.warning("⚠️ This will reset all sandbox data to the original sample data.")
    st.write("All current snapshots, owners, and accounts in the sandbox will be replaced.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, Reset", width="stretch", type="primary"):
            reset_sandbox()
            st.session_state.sandbox_reset = True
            st.rerun()
    with col2:
        if st.button("❌ Cancel", width="stretch"):
            st.rerun()


def reset_sandbox():
    """Reset the sandbox database to initial sample data"""
    if is_sandbox:
        # Clear cache to force database reload
        st.cache_resource.clear()

        # Recreate sandbox database with fresh sample data
        db_path = "kuyan-sandbox.db"
        if os.path.exists(db_path):
            os.remove(db_path)

        # Create new database and seed
        fresh_db = Database(db_path=db_path)
        fresh_db.seed_sample_data()


# Helper functions
def get_currency_symbol(currency):
    """Get currency symbol for display"""
    symbols = {
        "AUD": "A$",
        "BGN": "лв",
        "BRL": "R$",
        "CAD": "CA$",
        "CHF": "CHF",
        "CNY": "¥",
        "CZK": "Kč",
        "DKK": "kr",
        "EUR": "€",
        "GBP": "£",
        "HKD": "HK$",
        "HUF": "Ft",
        "IDR": "Rp",
        "ILS": "₪",
        "INR": "₹",
        "ISK": "kr",
        "JPY": "¥",
        "KRW": "₩",
        "MXN": "MX$",
        "MYR": "RM",
        "NOK": "kr",
        "NZD": "NZ$",
        "PHP": "₱",
        "PLN": "zł",
        "RON": "lei",
        "RUB": "₽",
        "SEK": "kr",
        "SGD": "S$",
        "THB": "฿",
        "TRY": "₺",
        "USD": "US$",
        "ZAR": "R"
    }
    return symbols.get(currency, currency)


def get_converted_value(amount, from_currency, to_currency, rates):
    """Convert amount using exchange rates"""
    if not rates:
        return amount
    return CurrencyConverter.convert(amount, from_currency, to_currency, rates)


def calculate_total_net_worth(snapshots, base_currency):
    """Calculate total net worth from snapshots in base currency"""
    if not snapshots:
        return 0.0

    total = 0.0
    rates = None

    for snapshot in snapshots:
        if snapshot.get("exchange_rates"):
            rates = json.loads(snapshot["exchange_rates"])

        if rates:
            converted = get_converted_value(
                snapshot["balance"],
                snapshot["currency"],
                base_currency,
                rates
            )
            total += converted
        else:
            total += snapshot["balance"]

    return total


# Page: Dashboard
def page_dashboard():
    # Get default base currency (first enabled currency)
    default_currency = get_default_currency()
    base_currency = st.session_state.get("base_currency", default_currency)

    # Get latest snapshots
    latest_snapshots = db.get_latest_snapshots()

    if not latest_snapshots:
        st.info("No data available. Add accounts and create your first monthly snapshot!")
        return

    # Get enabled currencies
    enabled_currencies = db.get_currencies()

    # Calculate current net worth in all enabled currencies
    net_worths = {}
    for currency in enabled_currencies:
        net_worths[currency['code']] = calculate_total_net_worth(latest_snapshots, currency['code'])

    # Display current net worth in all currencies with flags
    st.subheader("Current Net Worth")

    # Get theme colors for metric cards
    colors = get_theme_colors()

    # Smart row distribution to prevent wrapping
    # 1-4 currencies: 1 row (up to 4 columns)
    # 5-6 currencies: 2 rows (3 columns each)
    # 7-9 currencies: 3 rows (3 columns each)
    num_currencies = len(enabled_currencies)

    if num_currencies <= 4:
        rows = [enabled_currencies]  # All in one row
    elif num_currencies <= 6:
        # Split into 2 rows of 3 each
        mid = (num_currencies + 1) // 2
        rows = [enabled_currencies[:mid], enabled_currencies[mid:]]
    else:
        # Split into 3 rows of 3 each
        third = (num_currencies + 2) // 3
        rows = [
            enabled_currencies[:third],
            enabled_currencies[third:third*2],
            enabled_currencies[third*2:]
        ]

    # Render each row
    for row_currencies in rows:
        cols = st.columns(len(row_currencies))

        for idx, currency in enumerate(row_currencies):
            with cols[idx]:
                curr_symbol = get_currency_symbol(currency['code'])
                net_worth = net_worths[currency['code']]

                st.markdown(f"""
                <div style="background-color: {colors['bg_secondary']}; padding: 20px; border-radius: 10px; border-left: 5px solid {currency['color']};">
                    <p style="margin: 0; font-size: 14px; color: {colors['text_secondary']};">{currency['flag_emoji']} {currency['code']}</p>
                    <p style="margin: 0; font-size: 28px; font-weight: bold; color: {currency['color']};">{curr_symbol}{net_worth:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)

        # Add small spacing between rows
        if row_currencies != rows[-1]:
            st.write("")

    st.divider()

    # Account breakdown table
    col_header, col_currency = st.columns([3, 1])
    with col_header:
        st.subheader("Account Breakdown")
        st.caption("Currency conversions use exchange rates from the 1st of the snapshot month")
    with col_currency:
        base_currency = render_currency_selector(
            label="Select Currency",
            default_index=0,
            key="currency_selector"
        )
        # Update session state for other pages
        st.session_state.base_currency = base_currency

    if latest_snapshots:
        rates = json.loads(latest_snapshots[0]["exchange_rates"]) if latest_snapshots[0].get("exchange_rates") else {}

        breakdown_data = []
        total_converted = 0.0

        for snapshot in latest_snapshots:
            converted_value = get_converted_value(
                snapshot["balance"],
                snapshot["currency"],
                base_currency,
                rates
            )
            total_converted += converted_value

            breakdown_data.append({
                "Account": snapshot["name"],
                "Owner": snapshot["owner"],
                "Type": snapshot["account_type"],
                "Native Currency": snapshot["currency"],
                "Native Balance": f"{get_currency_symbol(snapshot['currency'])}{snapshot['balance']:,.2f}",
                f"{base_currency} Value": f"{get_currency_symbol(base_currency)}{converted_value:,.2f}"
            })

        # Display account breakdown table (without total)
        render_data_table(breakdown_data)

        # Display total row separately using theme colors
        colors = get_theme_colors()
        st.markdown(f"""
        <div style="margin-top: 10px; padding: 15px; background-color: {colors['bg_secondary']}; border-top: 2px solid {colors['border']}; border-radius: 5px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: bold; font-size: 16px; color: {colors['text_primary']};">TOTAL {base_currency}</span>
                <span style="font-weight: bold; font-size: 16px; color: {colors['text_primary']};">{get_currency_symbol(base_currency)}{total_converted:,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Net worth over time with currency selector
    st.subheader("Net Worth Over Time")

    snapshot_dates = db.get_all_snapshot_dates()

    if len(snapshot_dates) > 1:
        # Currency selector
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_currency = render_currency_selector(
                label="Select Currency",
                default_index=0,
                key="networth_currency_selector"
            )

        # Collect data for selected currency
        history_data = []

        for snapshot_date in reversed(snapshot_dates):
            snapshots = db.get_snapshots_by_date(date.fromisoformat(snapshot_date))
            net_worth = calculate_total_net_worth(snapshots, selected_currency)

            # Use month label instead of full date (uppercase month, year on next line)
            dt = datetime.fromisoformat(snapshot_date)
            month_label = f"{dt.strftime('%b').upper()}<br>{dt.year}"
            history_data.append({
                "Month": month_label,
                "Net Worth": net_worth
            })

        df_history = pd.DataFrame(history_data)

        # Build dynamic currency color map from database
        color_map = {}
        for curr in db.get_currencies():
            color_map[curr['code']] = curr['color']

        currency_symbol = get_currency_symbol(selected_currency)

        fig_line = px.line(
            df_history,
            x="Month",
            y="Net Worth",
            title=f"Total Net Worth in {selected_currency}",
            markers=True
        )

        # Apply color based on selected currency
        fig_line.update_traces(
            line_color=color_map[selected_currency],
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate=f'Net Worth: {currency_symbol}' + '%{y:,.2f}<br>' +
                         '<extra></extra>'
        )

        # Get theme colors
        colors = get_theme_colors()

        fig_line.update_layout(
            xaxis_title="Month",
            yaxis_title=f"Net Worth ({selected_currency})",
            hovermode="x unified",
            xaxis=dict(
                showline=True,
                linewidth=2,
                linecolor=colors['plot_axis'],
                mirror=False,
                showgrid=True,
                gridwidth=1,
                gridcolor=colors['plot_grid'],
                title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                showspikes=True,
                spikecolor=colors['plot_axis'],
                spikethickness=1
            ),
            yaxis=dict(
                showline=True,
                linewidth=2,
                linecolor=colors['plot_axis'],
                mirror=False,
                showgrid=True,
                gridwidth=1,
                gridcolor=colors['plot_grid'],
                title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                showspikes=True,
                spikecolor=colors['plot_axis'],
                spikethickness=1
            ),
            plot_bgcolor=colors['plot_bg'],
            paper_bgcolor=colors['plot_bg'],
            font=dict(color=colors['plot_text']),
            title_font=dict(color=colors['text_primary']),
            hoverlabel=dict(
                bgcolor=colors['surface'],
                font_size=13,
                font_family="Arial, sans-serif",
                font_color=colors['text_primary']
            )
        )
        st.plotly_chart(fig_line, width="stretch")
        st.markdown(
            '<p style="text-align: right; font-size: 0.6rem; margin-top: -10px;">* Monthly exchange rates are derived from rates effective on the 1st of each month</p>',
            unsafe_allow_html=True
        )
        st.divider()

        # Currency split - amounts held in each currency (normalized)
        st.subheader("Currency Holdings Growth (Normalized)")

        # Baseline month selector
        col_baseline, col_spacer = st.columns([2, 3])
        with col_baseline:
            # Convert dates to month labels for display (descending order - newest first)
            month_labels = [datetime.fromisoformat(d).strftime("%b %Y") for d in snapshot_dates]
            baseline_month_label = st.selectbox(
                "Baseline Month (100%)",
                options=month_labels,
                index=len(month_labels) - 1,  # Default to oldest month
                key="baseline_month_selector"
            )
            # Get the index of selected baseline (adjusted for reversed loop below)
            baseline_index = len(month_labels) - 1 - month_labels.index(baseline_month_label)

        # Collect data for amounts held in each currency
        currency_split_data = []
        baseline_holdings = {}

        # Get all enabled currencies dynamically
        enabled_currency_codes = db.get_currency_codes()

        for i, snapshot_date in enumerate(reversed(snapshot_dates)):
            snapshots = db.get_snapshots_by_date(date.fromisoformat(snapshot_date))

            # Calculate totals for each currency (not converted) - dynamically initialize
            currency_totals = {curr: 0.0 for curr in enabled_currency_codes}

            for snapshot in snapshots:
                curr = snapshot["currency"]
                balance = snapshot["balance"]
                if curr in currency_totals:
                    currency_totals[curr] += balance

            # Store baseline values from selected month
            if i == baseline_index:
                for curr in enabled_currency_codes:
                    baseline_holdings[curr] = currency_totals[curr] if currency_totals[curr] > 0 else 1

            # Calculate percentage relative to baseline for each currency
            if baseline_holdings:  # Only calculate if baseline is set
                for currency, total in currency_totals.items():
                    pct = (total / baseline_holdings[currency] * 100) if baseline_holdings[currency] > 0 else 100
                    # Use month label instead of full date (uppercase month, year on next line)
                    dt = datetime.fromisoformat(snapshot_date)
                    month_label = f"{dt.strftime('%b').upper()}<br>{dt.year}"
                    currency_split_data.append({
                        "Month": month_label,
                        "Currency": currency,
                        "Growth %": pct
                    })

        df_currency_split = pd.DataFrame(currency_split_data)

        fig_split = px.line(
            df_currency_split,
            x="Month",
            y="Growth %",
            color="Currency",
            color_discrete_map=color_map,
            title=f"Currency Holdings Growth (Baseline: {baseline_month_label} = 100%)",
            markers=True
        )

        fig_split.update_traces(
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate='Growth: %{y:.1f}%<br>' +
                         '<extra></extra>'
        )

        # Get theme colors
        colors = get_theme_colors()

        fig_split.update_layout(
            xaxis_title="Month",
            yaxis_title=f"Growth Index ({baseline_month_label} = 100%)",
            hovermode="x unified",
            xaxis=dict(
                showline=True,
                linewidth=2,
                linecolor=colors['plot_axis'],
                mirror=False,
                showgrid=True,
                gridwidth=1,
                gridcolor=colors['plot_grid'],
                title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                showspikes=True,
                spikecolor=colors['plot_axis'],
                spikethickness=1
            ),
            yaxis=dict(
                showline=True,
                linewidth=2,
                linecolor=colors['plot_axis'],
                mirror=False,
                showgrid=True,
                gridwidth=1,
                gridcolor=colors['plot_grid'],
                title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                showspikes=True,
                spikecolor=colors['plot_axis'],
                spikethickness=1
            ),
            plot_bgcolor=colors['plot_bg'],
            paper_bgcolor=colors['plot_bg'],
            font=dict(color=colors['plot_text']),
            title_font=dict(color=colors['text_primary']),
            hoverlabel=dict(
                bgcolor=colors['surface'],
                font_size=13,
                font_family="Arial, sans-serif",
                font_color=colors['text_primary']
            ),
            legend=dict(
                title=dict(text="Currency", font=dict(weight='bold', color=colors['text_primary'])),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor=colors['surface'],
                bordercolor=colors['border'],
                borderwidth=1,
                font=dict(color=colors['text_primary'])
            )
        )
        st.plotly_chart(fig_split, width="stretch")
        st.divider()

        # Year-over-year comparison if we have enough data
        if len(snapshot_dates) >= 12:
            st.subheader("Year-over-Year Comparison")

            # Currency selector for YoY graph
            col1, col2 = st.columns([1, 3])
            with col1:
                yoy_currency = render_currency_selector(
                    label="Select Currency",
                    default_index=0,
                    key="yoy_currency_selector"
                )

            # Get all unique years from snapshots
            years = sorted(list(set([datetime.fromisoformat(d).year for d in snapshot_dates])))

            # Month names in order (uppercase)
            month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

            # Create data structure with only months that have data
            yoy_data = []

            # Create a lookup dict for existing data
            data_lookup = {}
            for snapshot_date in snapshot_dates:
                dt = datetime.fromisoformat(snapshot_date)
                snapshots = db.get_snapshots_by_date(date.fromisoformat(snapshot_date))
                total = calculate_total_net_worth(snapshots, yoy_currency)
                key = (dt.year, dt.month)
                data_lookup[key] = total

            # Populate only months that have data (include year in x-axis label)
            for year in years:
                for month_num in range(1, 13):
                    key = (year, month_num)
                    if key in data_lookup:
                        yoy_data.append({
                            "Month": f"{month_names[month_num - 1]}<br>{year}",
                            "Year": str(year),
                            "Net Worth": data_lookup[key]
                        })

            df_yoy = pd.DataFrame(yoy_data)

            currency_symbol = get_currency_symbol(yoy_currency)
            fig_yoy = px.line(
                df_yoy,
                x="Month",
                y="Net Worth",
                color="Year",
                title=f"Year-over-Year Comparison ({yoy_currency})",
                markers=True
            )

            # Set month order
            fig_yoy.update_xaxes(categoryorder='array', categoryarray=month_names)

            fig_yoy.update_traces(
                line=dict(width=3),
                marker=dict(size=8),
                hovertemplate=f'Net Worth: {currency_symbol}' + '%{y:,.2f}<br>' +
                             '<extra></extra>'
            )

            # Get theme colors
            colors = get_theme_colors()

            fig_yoy.update_layout(
                hovermode="x unified",
                xaxis=dict(
                    showline=True,
                    linewidth=2,
                    linecolor=colors['plot_axis'],
                    mirror=False,
                    showgrid=True,
                    gridwidth=1,
                    gridcolor=colors['plot_grid'],
                    title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                    showspikes=True,
                    spikecolor=colors['plot_axis'],
                    spikethickness=1
                ),
                yaxis=dict(
                    showline=True,
                    linewidth=2,
                    linecolor=colors['plot_axis'],
                    mirror=False,
                    showgrid=True,
                    gridwidth=1,
                    gridcolor=colors['plot_grid'],
                    title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                    showspikes=True,
                    spikecolor=colors['plot_axis'],
                    spikethickness=1
                ),
                plot_bgcolor=colors['plot_bg'],
                paper_bgcolor=colors['plot_bg'],
                font=dict(color=colors['plot_text']),
                title_font=dict(color=colors['text_primary']),
                hoverlabel=dict(
                    bgcolor=colors['surface'],
                    font_size=13,
                    font_family="Arial, sans-serif",
                    font_color=colors['text_primary']
                ),
                legend=dict(
                    title=dict(text="Year", font=dict(weight='bold', color=colors['text_primary'])),
                    bgcolor=colors['surface'],
                    bordercolor=colors['border'],
                    borderwidth=1,
                    font=dict(color=colors['text_primary'])
                )
            )
            st.plotly_chart(fig_yoy, width="stretch")
            st.markdown(
                '<p style="text-align: right; font-size: 0.6rem; margin-top: -10px;">* Monthly exchange rates are derived from rates effective on the 1st of each month</p>',
                unsafe_allow_html=True
            )
            st.divider()
    else:
        st.info("Add more monthly snapshots to see trends over time")


# Page: Accounts
def page_accounts():
    st.title("Manage Accounts")

    # Show success message if account was just added
    show_success_toast('account')

    # List existing accounts
    st.subheader("Existing Accounts")

    accounts = db.get_accounts()
    owner_names = db.get_owner_names()
    currency_codes = db.get_currency_codes()

    if accounts:
        # Group accounts by owner for better organization
        accounts_by_owner = {}
        for acc in accounts:
            if acc['owner'] not in accounts_by_owner:
                accounts_by_owner[acc['owner']] = []
            accounts_by_owner[acc['owner']].append(acc)

        # Display accounts grouped by owner
        for owner_name in sorted(accounts_by_owner.keys()):
            st.write(f"**{owner_name}:**")

            for account in accounts_by_owner[owner_name]:
                # Create expandable section for each account
                account_icon = "🏦" if account['account_type'] == "Bank" else "📈" if account['account_type'] == "Investment" else "💼"
                with st.expander(f"{account_icon} {account['name']} - {account['currency']}", expanded=False):
                    st.write(f"**Type:** {account['account_type']}")
                    st.write(f"**Currency:** {account['currency']}")

                    st.write("**Edit Account:**")
                    col1, col2 = st.columns(2)

                    with col1:
                        new_name = st.text_input(
                            "Account Name",
                            value=account['name'],
                            key=f"name_{account['id']}"
                        )
                        owner_index = owner_names.index(account['owner']) if account['owner'] in owner_names else 0
                        new_owner = st.selectbox(
                            "Owner",
                            owner_names,
                            index=owner_index,
                            key=f"owner_{account['id']}"
                        )

                    with col2:
                        type_options = ["Bank", "Investment", "Other"]
                        type_index = type_options.index(account['account_type']) if account['account_type'] in type_options else 0
                        new_type = st.selectbox(
                            "Account Type",
                            type_options,
                            index=type_index,
                            key=f"type_{account['id']}"
                        )
                        curr_index = currency_codes.index(account['currency']) if account['currency'] in currency_codes else 0
                        new_currency = st.selectbox(
                            "Currency",
                            currency_codes,
                            index=curr_index,
                            key=f"currency_{account['id']}"
                        )

                    # Update button
                    if st.button(f"💾 Update Account", key=f"update_btn_{account['id']}", width="stretch"):
                        if new_name:
                            db.update_account(account['id'], new_name, new_owner, new_type, new_currency)
                            st.success(f"Account updated!")
                            st.rerun()
                        else:
                            st.error("Please enter an account name")

                    st.divider()

                    # Remove account button
                    if st.button(f"🗑️ Remove {account['name']}", key=f"remove_btn_{account['id']}", width="stretch", type="secondary"):
                        db.delete_account(account['id'])
                        st.success(f"Account '{account['name']}' removed!")
                        st.rerun()

            st.write("")  # Add spacing between owners
    else:
        st.warning("No accounts found!")

    st.divider()

    # Add new account section
    st.subheader("Add New Account")

    if not owner_names:
        st.warning("Please add at least one owner first in the Owners page!")
    else:
        col1, col2 = st.columns(2)

        with col1:
            account_name = st.text_input("Account Name", placeholder="e.g., TD Chequing", key="add_account_name")
            owner = st.selectbox("Owner", owner_names, key="add_account_owner")

        with col2:
            account_type = st.selectbox("Account Type", ["Bank", "Investment", "Other"], key="add_account_type")
            currency = st.selectbox("Currency", currency_codes, key="add_account_currency")

        # Add button
        if st.button("➕ Add Account", width="stretch", type="primary", key="add_account_btn"):
            if account_name:
                db.add_account(account_name, owner, account_type, currency)
                st.session_state.account_added = True
                st.session_state.added_account_name = account_name
                st.rerun()
            else:
                st.error("Please enter an account name")


# Page: Update Balances
def page_update_balances():
    accounts = db.get_accounts()

    if not accounts:
        st.warning("No accounts found. Please add accounts first!")
        return

    current_date = date.today()
    month_names = MONTH_NAMES

    # Initialize session state for dialog
    if 'show_save_dialog' not in st.session_state:
        st.session_state.show_save_dialog = False
    if 'save_snapshot_data' not in st.session_state:
        st.session_state.save_snapshot_data = None

    # Show success message if save was just completed
    if st.session_state.get('snapshot_saved', False):
        saved_month = st.session_state.get('saved_month_name', '')
        saved_year = st.session_state.get('saved_year', '')
        st.toast(f"Snapshot saved successfully for {saved_month} {saved_year}!", icon="💰")
        # Clear the flag
        st.session_state.snapshot_saved = False

    # Get most recent 3 months with actual snapshot data
    snapshot_dates = db.get_all_snapshot_dates()

    prev_months = []
    prev_month_data = {}

    if snapshot_dates:
        # Sort snapshot dates in descending order and take the most recent 3
        recent_dates = sorted(snapshot_dates, reverse=True)[:3]

        for snapshot_date_str in recent_dates:
            prev_date = date.fromisoformat(snapshot_date_str)
            prev_months.append(prev_date)

            # Get snapshots for this month
            prev_snapshots = db.get_snapshots_by_date(prev_date)
            for snap in prev_snapshots:
                if snap['account_id'] not in prev_month_data:
                    prev_month_data[snap['account_id']] = {}
                prev_month_data[snap['account_id']][prev_date] = snap['balance']

    # Top section: Historical balances table
    st.subheader("📊 Account Balance History (Most recent 3 months)")

    # Create table data grouped by owner
    owners = db.get_owners()
    owner_names = [owner['name'] for owner in owners]

    table_data = []
    for account in accounts:
        row = {
            'Owner': account['owner'],
            'Account': account['name'],
            'Currency': account['currency'],
        }

        # Add previous 3 months
        for prev_date in reversed(prev_months):  # Show oldest to newest
            month_label = prev_date.strftime("%b %Y")
            if account['id'] in prev_month_data and prev_date in prev_month_data[account['id']]:
                row[month_label] = f"{prev_month_data[account['id']][prev_date]:,.2f}"
            else:
                row[month_label] = "N/A"

        table_data.append(row)

    # Display table with previous months (read-only)
    if table_data:
        render_data_table(table_data)

    st.divider()

    # Month/Year selector section
    st.subheader("📅 Update Monthly Balances")

    col1, col2, col_warning = st.columns([2, 2, 4])

    with col1:
        selected_year = st.selectbox(
            "Year",
            options=list(range(current_date.year, current_date.year - 10, -1)),
            index=0
        )

    with col2:
        # Create months in descending order (Dec to Jan)
        months_desc = list(range(12, 0, -1))
        selected_month = st.selectbox(
            "Month",
            options=months_desc,
            format_func=lambda x: month_names[x - 1],
            index=months_desc.index(current_date.month)
        )

    # Create snapshot date as first day of selected month
    snapshot_date = date(selected_year, selected_month, 1)

    # Check if future date
    if snapshot_date > current_date:
        with col_warning:
            st.error("❌ Cannot create snapshots for future months!")
        return

    # Check if snapshot already exists and show alert
    snapshot_exists = db.snapshot_exists_for_date(snapshot_date)
    if snapshot_exists:
        with col_warning:
            st.warning(f"⚠️ Snapshot exists for {month_names[selected_month - 1]} {selected_year}. Saving will overwrite it.")

    st.divider()

    # Display existing snapshot if it exists
    if snapshot_exists:
        existing_snapshots = db.get_snapshots_by_date(snapshot_date)
        if existing_snapshots:
            st.subheader(f"📋 Existing Snapshot for {month_names[selected_month - 1]} {selected_year}")

            # Get base currency (default to first enabled currency)
            default_currency = get_default_currency()
            base_currency = st.session_state.get("base_currency", default_currency)
            currency_symbol = get_currency_symbol(base_currency)

            # Get exchange rates
            rates = json.loads(existing_snapshots[0]["exchange_rates"]) if existing_snapshots[0].get("exchange_rates") else {}

            # Calculate total net worth
            total = calculate_total_net_worth(existing_snapshots, base_currency)

            st.markdown(f"**Total Net Worth:** `{currency_symbol}{total:,.2f}` ({base_currency})")

            # Display snapshots grouped by owner
            log_entries = []
            for owner_name in owner_names:
                owner_snapshots = [s for s in existing_snapshots if s['owner'] == owner_name]

                if owner_snapshots:
                    log_entries.append(f"  **{owner_name}:**")

                    for snapshot in owner_snapshots:
                        converted_value = get_converted_value(
                            snapshot["balance"],
                            snapshot["currency"],
                            base_currency,
                            rates
                        )

                        acc_symbol = get_currency_symbol(snapshot['currency'])
                        entry = (
                            f"    • {snapshot['name']} ({snapshot['account_type']}): "
                            f"`{acc_symbol}{snapshot['balance']:,.2f}` {snapshot['currency']}"
                        )
                        if snapshot['currency'] != base_currency:
                            entry += f" = `{currency_symbol}{converted_value:,.2f}` {base_currency}"

                        log_entries.append(entry)

            # Display all log entries
            st.markdown("\n".join(log_entries))

            st.divider()

    # Fetch exchange rates for the selected date
    with st.spinner("Fetching exchange rates..."):
        enabled_currencies = db.get_currency_codes()
        exchange_rates = CurrencyConverter.get_all_cross_rates(enabled_currencies, snapshot_date.isoformat())

    if not exchange_rates:
        st.error("Unable to fetch exchange rates. Please check your internet connection.")
        return

    # Get existing snapshot data if it exists for pre-filling the form
    existing_snapshot_data = {}
    if snapshot_exists:
        existing_snapshots = db.get_snapshots_by_date(snapshot_date)
        for snap in existing_snapshots:
            existing_snapshot_data[snap['account_id']] = snap['balance']

    # Balance entry form - grouped by owner
    with st.form("balance_form"):
        st.write(f"**Enter Balances for {month_names[selected_month - 1]} {selected_year}**")

        balances = {}

        # Group accounts by owner
        for owner_name in owner_names:
            owner_accounts = [acc for acc in accounts if acc['owner'] == owner_name]

            if owner_accounts:
                st.markdown(f"### {owner_name}")

                # Create 2-column layout for accounts
                cols_per_row = 2
                for i in range(0, len(owner_accounts), cols_per_row):
                    cols = st.columns(cols_per_row)

                    for j, col in enumerate(cols):
                        idx = i + j
                        if idx < len(owner_accounts):
                            account = owner_accounts[idx]
                            with col:
                                # Priority: 1) Existing snapshot for this month, 2) Previous month's balance, 3) 0.0
                                default_val = 0.0

                                # Check if existing snapshot has this account
                                if account['id'] in existing_snapshot_data:
                                    default_val = float(existing_snapshot_data[account['id']])
                                # Otherwise, use previous month's balance
                                elif prev_months and account['id'] in prev_month_data:
                                    most_recent = prev_months[0]  # Most recent previous month
                                    if most_recent in prev_month_data[account['id']]:
                                        default_val = float(prev_month_data[account['id']][most_recent])

                                balance = st.number_input(
                                    f"{account['name']} ({account['currency']})",
                                    min_value=0.0,
                                    value=default_val,
                                    step=100.0,
                                    format="%.2f",
                                    key=f"balance_{account['id']}"
                                )
                                balances[account['id']] = balance

                st.write("")  # Spacing between owners

        st.divider()
        submit = st.form_submit_button("💾 Save Snapshot", width="stretch")

        if submit:
            # Validate that at least one balance is entered
            if all(balance == 0 for balance in balances.values()):
                st.error("Please enter at least one non-zero balance")
            else:
                # Store data in session state for confirmation dialog
                st.session_state.save_snapshot_data = {
                    'snapshot_date': snapshot_date,
                    'balances': balances,
                    'exchange_rates': exchange_rates,
                    'snapshot_exists': snapshot_exists,
                    'month_name': month_names[selected_month - 1],
                    'year': selected_year
                }
                st.session_state.show_save_dialog = True
                st.rerun()

    # Show confirmation dialog
    if st.session_state.show_save_dialog and st.session_state.save_snapshot_data:
        data = st.session_state.save_snapshot_data

        @st.dialog("Confirm Save")
        def confirm_save():
            st.write(f"**Save snapshot for {data['month_name']} {data['year']}?**")

            if data['snapshot_exists']:
                st.warning("⚠️ This will overwrite the existing snapshot.")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("💾 Save", type="primary", width="stretch"):
                    # If snapshot exists, delete it first (overwrite)
                    if data['snapshot_exists']:
                        existing_snapshots = db.get_snapshots_by_date(data['snapshot_date'])
                        for snapshot in existing_snapshots:
                            db.delete_snapshot(snapshot['id'])

                    # Save new snapshots
                    for account_id, balance in data['balances'].items():
                        db.add_snapshot(data['snapshot_date'], account_id, balance, data['exchange_rates'])

                    # Set success flag to show message after rerun
                    st.session_state.snapshot_saved = True
                    st.session_state.saved_month_name = data['month_name']
                    st.session_state.saved_year = data['year']

                    # Clear dialog state
                    st.session_state.show_save_dialog = False
                    st.session_state.save_snapshot_data = None

                    st.rerun()

            with col2:
                if st.button("❌ Cancel", width="stretch"):
                    st.session_state.show_save_dialog = False
                    st.session_state.save_snapshot_data = None
                    st.rerun()

        confirm_save()


# Page: History
def page_history():
    st.caption("View all snapshot entries by year")

    snapshot_dates = db.get_all_snapshot_dates()

    if not snapshot_dates:
        st.info("No snapshots yet. Create your first monthly snapshot!")
        return

    # Extract unique years from snapshot dates
    years = sorted(list(set([datetime.fromisoformat(d).year for d in snapshot_dates])), reverse=True)

    # Year selector
    col1, _ = st.columns([2, 6])
    with col1:
        selected_year = st.selectbox(
            "Select Year",
            options=years,
            index=0
        )

    st.divider()

    # Get base currency (default to first enabled currency)
    default_currency = get_default_currency()
    base_currency = st.session_state.get("base_currency", default_currency)
    currency_symbol = get_currency_symbol(base_currency)

    # Month names
    month_names = MONTH_NAMES

    # Filter snapshots for selected year and organize by month
    year_snapshots = {}
    for snapshot_date_str in snapshot_dates:
        snapshot_dt = datetime.fromisoformat(snapshot_date_str)
        if snapshot_dt.year == selected_year:
            month_num = snapshot_dt.month
            year_snapshots[month_num] = date.fromisoformat(snapshot_date_str)

    # Display log entries for each month in descending order (Current month → Jan)
    st.markdown(f"### 📅 {selected_year} Snapshot Log")
    st.markdown("---")

    # Determine starting month
    current_date = date.today()
    if selected_year == current_date.year:
        # For current year, start from current month
        start_month = current_date.month
    else:
        # For past years, start from December
        start_month = 12

    for month_num in range(start_month, 0, -1):
        if month_num in year_snapshots:
            snapshot_date = year_snapshots[month_num]
            snapshots = db.get_snapshots_by_date(snapshot_date)

            if snapshots:
                # Get exchange rates
                rates = json.loads(snapshots[0]["exchange_rates"]) if snapshots[0].get("exchange_rates") else {}

                # Calculate total net worth
                total = calculate_total_net_worth(snapshots, base_currency)

                # Display month header
                st.markdown(f"#### 📌 {month_names[month_num - 1]} {selected_year}")
                st.markdown(f"**Total Net Worth:** `{currency_symbol}{total:,.2f}` ({base_currency})")

                # Group snapshots by owner for better organization
                owners = db.get_owners()
                owner_names = [owner['name'] for owner in owners]

                # Display snapshots grouped by owner
                log_entries = []
                for owner_name in owner_names:
                    owner_snapshots = [s for s in snapshots if s['owner'] == owner_name]

                    if owner_snapshots:
                        log_entries.append(f"  **{owner_name}:**")

                        for snapshot in owner_snapshots:
                            converted_value = get_converted_value(
                                snapshot["balance"],
                                snapshot["currency"],
                                base_currency,
                                rates
                            )

                            acc_symbol = get_currency_symbol(snapshot['currency'])
                            entry = (
                                f"    • {snapshot['name']} ({snapshot['account_type']}): "
                                f"`{acc_symbol}{snapshot['balance']:,.2f}` {snapshot['currency']}"
                            )
                            if snapshot['currency'] != base_currency:
                                entry += f" = `{currency_symbol}{converted_value:,.2f}` {base_currency}"

                            log_entries.append(entry)

                # Display all log entries
                st.markdown("\n".join(log_entries))

                # Delete button for this month
                col_delete, _ = st.columns([2, 6])
                with col_delete:
                    if st.button(f"🗑️ Delete {month_names[month_num - 1]}", key=f"delete_{month_num}"):
                        if st.session_state.get(f"confirm_delete_{month_num}", False):
                            db.delete_snapshots_by_date(snapshot_date)
                            st.success(f"Deleted snapshot for {month_names[month_num - 1]} {selected_year}!")
                            st.session_state[f"confirm_delete_{month_num}"] = False
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_{month_num}"] = True
                            st.warning("⚠️ Click again to confirm deletion")

                st.markdown("---")
        else:
            # No snapshot for this month
            st.markdown(f"#### ⚪ {month_names[month_num - 1]} {selected_year}")
            st.markdown("  *No snapshot recorded*")
            st.markdown("---")


# Page: Exchange Rates
def page_exchange_rates():
    st.caption("View current and historical exchange rates for supported currencies")

    # Date selector
    current_date = date.today()
    selected_date = st.date_input(
        "Select Date",
        value=current_date,
        max_value=current_date,
        help="View exchange rates for a specific date"
    )

    st.divider()

    # Fetch exchange rates
    with st.spinner("Fetching exchange rates..."):
        enabled_currencies = db.get_currency_codes()
        exchange_rates = CurrencyConverter.get_all_cross_rates(enabled_currencies, selected_date.isoformat())

    if not exchange_rates:
        st.error("Unable to fetch exchange rates. Please check your internet connection.")
        return

    st.success(f"✅ Exchange rates for {selected_date.strftime('%B %d, %Y')}")

    st.divider()

    # Display exchange rates in a grid
    st.subheader("Currency Exchange Rates")

    rates_display = {
        "USD to CAD": exchange_rates.get("USD_CAD", "N/A"),
        "USD to INR": exchange_rates.get("USD_INR", "N/A"),
        "CAD to USD": exchange_rates.get("CAD_USD", "N/A"),
        "CAD to INR": exchange_rates.get("CAD_INR", "N/A"),
        "INR to USD": exchange_rates.get("INR_USD", "N/A"),
        "INR to CAD": exchange_rates.get("INR_CAD", "N/A"),
    }

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("USD → CAD", f"{rates_display['USD to CAD']:.4f}")
        st.metric("CAD → USD", f"{rates_display['CAD to USD']:.4f}")

    with col2:
        st.metric("USD → INR", f"{rates_display['USD to INR']:.4f}")
        st.metric("INR → USD", f"{rates_display['INR to USD']:.4f}")

    with col3:
        st.metric("CAD → INR", f"{rates_display['CAD to INR']:.4f}")
        st.metric("INR → CAD", f"{rates_display['INR to CAD']:.4f}")

    st.divider()

    # Exchange rate information
    with st.expander("ℹ️ About Exchange Rates"):
        st.write("""
        **Source:** Exchange rates are fetched from the frankfurter.app API

        **Update Frequency:** Rates are updated daily

        **Usage:** These rates are automatically used when calculating net worth across different currencies

        **Historical Rates:** You can view historical rates by selecting past dates. The same rates
        are stored with each snapshot to ensure accurate historical calculations.
        """)


# Page: Currencies
def page_currencies():
    st.title("Manage Currencies")

    # Currency metadata (Frankfurter API supported currencies with flags)
    AVAILABLE_CURRENCIES = {
        "AUD": {"name": "Australian Dollar", "flag": "🇦🇺"},
        "BGN": {"name": "Bulgarian Lev", "flag": "🇧🇬"},
        "BRL": {"name": "Brazilian Real", "flag": "🇧🇷"},
        "CAD": {"name": "Canadian Dollar", "flag": "🇨🇦"},
        "CHF": {"name": "Swiss Franc", "flag": "🇨🇭"},
        "CNY": {"name": "Chinese Yuan", "flag": "🇨🇳"},
        "CZK": {"name": "Czech Koruna", "flag": "🇨🇿"},
        "DKK": {"name": "Danish Krone", "flag": "🇩🇰"},
        "EUR": {"name": "Euro", "flag": "🇪🇺"},
        "GBP": {"name": "British Pound", "flag": "🇬🇧"},
        "HKD": {"name": "Hong Kong Dollar", "flag": "🇭🇰"},
        "HUF": {"name": "Hungarian Forint", "flag": "🇭🇺"},
        "IDR": {"name": "Indonesian Rupiah", "flag": "🇮🇩"},
        "ILS": {"name": "Israeli Shekel", "flag": "🇮🇱"},
        "INR": {"name": "Indian Rupee", "flag": "🇮🇳"},
        "ISK": {"name": "Icelandic Króna", "flag": "🇮🇸"},
        "JPY": {"name": "Japanese Yen", "flag": "🇯🇵"},
        "KRW": {"name": "South Korean Won", "flag": "🇰🇷"},
        "MXN": {"name": "Mexican Peso", "flag": "🇲🇽"},
        "MYR": {"name": "Malaysian Ringgit", "flag": "🇲🇾"},
        "NOK": {"name": "Norwegian Krone", "flag": "🇳🇴"},
        "NZD": {"name": "New Zealand Dollar", "flag": "🇳🇿"},
        "PHP": {"name": "Philippine Peso", "flag": "🇵🇭"},
        "PLN": {"name": "Polish Złoty", "flag": "🇵🇱"},
        "RON": {"name": "Romanian Leu", "flag": "🇷🇴"},
        "RUB": {"name": "Russian Ruble", "flag": "🇷🇺"},
        "SEK": {"name": "Swedish Krona", "flag": "🇸🇪"},
        "SGD": {"name": "Singapore Dollar", "flag": "🇸🇬"},
        "THB": {"name": "Thai Baht", "flag": "🇹🇭"},
        "TRY": {"name": "Turkish Lira", "flag": "🇹🇷"},
        "USD": {"name": "US Dollar", "flag": "🇺🇸"},
        "ZAR": {"name": "South African Rand", "flag": "🇿🇦"},
    }

    # Theme-friendly colors (work well in both light and dark mode)
    COLOR_OPTIONS = {
        "Crimson Red": "#DC143C",
        "Navy Blue": "#003366",
        "Dark Orange": "#FF8C00",
        "Forest Green": "#228B22",
        "Purple": "#8B008B",
        "Teal": "#008080",
        "Maroon": "#800000",
        "Olive": "#808000",
        "Steel Blue": "#4682B4",
    }

    # Show success message if currency was just added
    if st.session_state.get('currency_added', False):
        currency_code = st.session_state.get('added_currency_code', '')
        st.toast(f"Currency '{currency_code}' added successfully!", icon="💱")
        st.session_state.currency_added = False

    # Get enabled currencies
    enabled_currencies = db.get_currencies()
    enabled_codes = [c['code'] for c in enabled_currencies]
    currency_count = len(enabled_currencies)

    st.info(f"**{currency_count}/9 currencies enabled** (Minimum: 1, Maximum: 9)")

    st.divider()

    # Show enabled currencies with inline editing and removal
    st.subheader("Enabled Currencies")

    if enabled_currencies:
        for curr in enabled_currencies:
            currency_name = AVAILABLE_CURRENCIES.get(curr['code'], {}).get('name', curr['code'])
            is_in_use = db.currency_in_use(curr['code'])
            in_use_text = "Yes" if is_in_use else "No"

            # Create expandable section for each currency
            with st.expander(f"{curr['flag_emoji']} {curr['code']} - {currency_name}", expanded=False):
                st.write(f"**In Use:** {in_use_text}")

                st.write("**Change Color:**")
                col1, col2, col3 = st.columns([2, 3, 2])

                with col1:
                    # Current color preview - aligned with dropdown center
                    st.markdown("<div style='text-align: center;'>Current</div>", unsafe_allow_html=True)
                    st.markdown(f"""
                        <div style="
                            width: 40px;
                            height: 40px;
                            background-color: {curr['color']};
                            border-radius: 50%;
                            border: 2px solid #666;
                            margin-left: auto;
                            margin-right: auto;
                        "></div>
                    """, unsafe_allow_html=True)

                with col2:
                    # Color selector
                    new_color = st.selectbox(
                        "Select Color",
                        list(COLOR_OPTIONS.keys()),
                        key=f"color_select_{curr['id']}"
                    )

                with col3:
                    # New color preview - aligned with dropdown center
                    st.markdown("<div style='text-align: center;'>New</div>", unsafe_allow_html=True)
                    new_color_value = COLOR_OPTIONS[new_color]
                    st.markdown(f"""
                        <div style="
                            width: 40px;
                            height: 40px;
                            background-color: {new_color_value};
                            border-radius: 50%;
                            border: 2px solid #666;
                            margin-left: auto;
                            margin-right: auto;
                        "></div>
                    """, unsafe_allow_html=True)

                # Update button
                if st.button(f"🎨 Update Color", key=f"update_btn_{curr['id']}", width="stretch"):
                    success = db.update_currency_color(curr['id'], new_color_value)
                    if success:
                        st.success(f"Color updated!")
                        st.rerun()
                    else:
                        st.error("Failed to update color")

                st.divider()

                # Remove currency button
                if currency_count <= 1:
                    st.info("Cannot remove the last currency. At least one currency is required.")
                elif is_in_use:
                    st.warning(f"Cannot remove {curr['code']} - it's currently used by existing accounts.")
                else:
                    if st.button(f"🗑️ Remove {curr['code']}", key=f"remove_btn_{curr['id']}", width="stretch", type="secondary"):
                        success = db.delete_currency(curr['id'])
                        if success:
                            st.success(f"Currency {curr['code']} removed!")
                            st.rerun()
                        else:
                            st.error("Failed to remove currency")
    else:
        st.warning("No currencies enabled!")

    # Add new currency section
    if currency_count < 9:  # Only allow adding if less than 9 currencies
        st.subheader("Add New Currency")

        # Filter out already enabled currencies
        available_to_add = {k: v for k, v in AVAILABLE_CURRENCIES.items() if k not in enabled_codes}

        if available_to_add:
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                # Currency selector
                currency_options = [f"{v['flag']} {k} - {v['name']}" for k, v in sorted(available_to_add.items())]
                selected = st.selectbox("Select Currency", currency_options, key="add_currency_selector")

                # Extract currency code from selection
                selected_code = selected.split()[1] if selected else None

            with col2:
                # Color selector
                color_name = st.selectbox("Select Color", list(COLOR_OPTIONS.keys()), key="add_color_selector")
                color_value = COLOR_OPTIONS[color_name]

            with col3:
                # Color preview - aligned with dropdown center
                st.markdown("<div style='text-align: center;'>Preview</div>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="
                        width: 40px;
                        height: 40px;
                        background-color: {color_value};
                        border-radius: 50%;
                        border: 2px solid #666;
                        margin-left: auto;
                        margin-right: auto;
                    "></div>
                """, unsafe_allow_html=True)

            # Add button with proper spacing
            if st.button("➕ Add Currency", width="stretch", type="primary", key="add_currency_btn"):
                if selected_code:
                    flag_emoji = AVAILABLE_CURRENCIES[selected_code]['flag']
                    db.add_currency(selected_code, flag_emoji, color_value)
                    st.session_state.currency_added = True
                    st.session_state.added_currency_code = selected_code
                    st.rerun()
        else:
            st.info("All available currencies have been added!")
    else:
        st.warning("Maximum of 9 currencies reached. Remove a currency to add a new one.")

    st.divider()

    st.info("""
**About Currencies**

- Exchange rates are fetched from the [Frankfurter API](https://frankfurter.dev/)
- Rates are effective as of the 1st of each month
- View current rates using the **Exchange Rate** tool in the sidebar
- Currencies cannot be removed if they're used by accounts
    """)


# Page: Owners
def page_owners():
    st.title("Manage Owners")

    # Show success message if owner was just added
    show_success_toast('owner')

    # List existing owners
    st.subheader("Existing Owners")

    owners = db.get_owners()
    owner_count = len(owners)

    if owners:
        for owner in owners:
            has_accounts = db.owner_has_accounts(owner['name'])
            has_accounts_text = "Yes" if has_accounts else "No"

            # Create expandable section for each owner
            with st.expander(f"👤 {owner['name']} - {owner['owner_type']}", expanded=False):
                st.write(f"**Has Accounts:** {has_accounts_text}")

                st.write("**Edit Owner:**")
                col1, col2 = st.columns(2)

                with col1:
                    new_name = st.text_input(
                        "Owner Name",
                        value=owner['name'],
                        key=f"name_{owner['id']}"
                    )

                with col2:
                    type_options = ["Individual", "Company", "Joint/Shared", "Trust", "Other"]
                    current_index = type_options.index(owner['owner_type']) if owner['owner_type'] in type_options else 0
                    new_type = st.selectbox(
                        "Owner Type",
                        type_options,
                        index=current_index,
                        key=f"type_{owner['id']}"
                    )

                # Update button
                if st.button(f"💾 Update Owner", key=f"update_btn_{owner['id']}", width="stretch"):
                    if new_name:
                        try:
                            db.update_owner(owner['id'], new_name, new_type)
                            st.success(f"Owner updated!")
                            st.rerun()
                        except Exception as e:
                            if "UNIQUE constraint failed" in str(e):
                                st.error(f"Owner '{new_name}' already exists!")
                            else:
                                st.error(f"Error updating owner: {str(e)}")
                    else:
                        st.error("Please enter an owner name")

                st.divider()

                # Remove owner button
                if owner_count <= 1:
                    st.info("Cannot remove the last owner. At least one owner is required.")
                elif has_accounts:
                    st.warning(f"Cannot remove {owner['name']} - this owner has existing accounts.")
                else:
                    if st.button(f"🗑️ Remove {owner['name']}", key=f"remove_btn_{owner['id']}", width="stretch", type="secondary"):
                        success = db.delete_owner(owner['id'])
                        if success:
                            st.success(f"Owner '{owner['name']}' removed!")
                            st.rerun()
                        else:
                            st.error("Failed to remove owner")
    else:
        st.warning("No owners found!")

    st.divider()

    # Add new owner section
    st.subheader("Add New Owner")

    col1, col2 = st.columns(2)

    with col1:
        owner_name = st.text_input("Owner Name", placeholder="e.g., John, Acme Corp", key="add_owner_name")

    with col2:
        owner_type = st.selectbox("Owner Type", ["Individual", "Company", "Joint/Shared", "Trust", "Other"], key="add_owner_type")

    # Add button
    if st.button("➕ Add Owner", width="stretch", type="primary", key="add_owner_btn"):
        if owner_name:
            try:
                db.add_owner(owner_name, owner_type)
                st.session_state.owner_added = True
                st.session_state.added_owner_name = owner_name
                st.rerun()
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    st.error(f"Owner '{owner_name}' already exists!")
                else:
                    st.error(f"Error adding owner: {str(e)}")
        else:
            st.error("Please enter an owner name")


# ===== TOOL BUTTON TEMPLATE =====
# Reusable template for expandable tool buttons with visual connection

def render_tool_button(icon, label, state_key, widget_renderer):
    """
    Render a tool button with arrow that expands to show a widget

    Args:
        icon: Emoji icon for the button
        label: Button label text
        state_key: Session state key for tracking open/closed state
        widget_renderer: Function to render the widget content
    """
    colors = get_theme_colors()

    # Check if widget is open
    is_open = st.session_state.get(state_key, False)
    arrow = "▼" if is_open else "▲"

    # Render button
    if st.button(f"{icon} {label} {arrow}", width="stretch", key=f"{state_key}_btn"):
        # Toggle state
        st.session_state[state_key] = not is_open
        st.rerun()

    # Render widget if open
    if is_open:
        # Visual connection using columns for indentation
        col_spacer, col_content = st.columns([0.08, 0.92])

        with col_spacer:
            # Subtle vertical line indicator
            st.markdown(f"""
                <div style="
                    width: 2px;
                    background-color: {colors['border']};
                    height: 100%;
                    min-height: 500px;
                    border-radius: 1px;
                    opacity: 0.6;
                "></div>
            """, unsafe_allow_html=True)

        with col_content:
            # Render the actual widget content
            widget_renderer()


# ===== EXCHANGE RATE WIDGET =====

def render_exchange_rate_widget_inline():
    """Exchange Rate widget content"""

    # Date selector
    current_date = date.today()
    selected_date = st.date_input(
        "Select Date",
        value=current_date,
        max_value=current_date,
        key="exchange_rate_date"
    )

    st.write("")  # Add spacing

    # Fetch exchange rates
    with st.spinner("Fetching rates..."):
        enabled_currencies = db.get_currency_codes()
        exchange_rates = CurrencyConverter.get_all_cross_rates(enabled_currencies, selected_date.isoformat())

    if not exchange_rates:
        st.error("Unable to fetch rates.")
        return

    # Display date caption
    st.caption(f"📅 {selected_date.strftime('%B %d, %Y')}")

    st.divider()

    # Get enabled currencies
    enabled_currencies = db.get_currency_codes()

    # Generate all currency pairs (sorted alphabetically)
    rates_display = []
    for from_curr in enabled_currencies:
        for to_curr in enabled_currencies:
            if from_curr != to_curr:
                pair_key = f"{from_curr}_{to_curr}"
                rate_value = exchange_rates.get(pair_key, "N/A")
                rates_display.append((f"{from_curr} → {to_curr}", rate_value))

    # Sort alphabetically
    rates_display.sort(key=lambda x: x[0])

    # Display rates with better formatting
    for label, rate in rates_display:
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.markdown(f"**{label}**")
        with col2:
            if rate != "N/A":
                st.text(f"{rate:.4f}")
            else:
                st.text("N/A")


# ===== CALENDAR INVITE WIDGET =====

def render_calendar_widget():
    """Calendar Invite widget for monthly balance update reminders"""
    from datetime import datetime, timedelta

    st.write("**Create Monthly Reminder**")
    st.caption("Set up a calendar invite to remind you to update monthly balances")

    # Date selector for first reminder
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "First Reminder Date",
            value=datetime.now().date() + timedelta(days=30),
            key="calendar_start_date"
        )

    with col2:
        reminder_time = st.time_input(
            "Reminder Time",
            value=datetime.strptime("09:00", "%H:%M").time(),
            key="calendar_time"
        )

    # Email input
    emails = st.text_input(
        "Invite additional attendees",
        placeholder="email1@example.com, email2@example.com",
        help="Add comma-separated email addresses",
        key="calendar_emails"
    )

    # Generate invite button
    if st.button("Generate Calendar Invite", width="stretch", type="primary", key="gen_calendar"):
        if emails:
            # Create .ics file content
            event_datetime = datetime.combine(start_date, reminder_time)

            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//KUYAN//Monthly Balance Reminder//EN
BEGIN:VEVENT
UID:{event_datetime.strftime('%Y%m%d%H%M%S')}@kuyan
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{event_datetime.strftime('%Y%m%dT%H%M%S')}
DTEND:{(event_datetime + timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')}
RRULE:FREQ=MONTHLY;COUNT=12
SUMMARY:Update Monthly Balances in KUYAN
DESCRIPTION:Monthly reminder to update account balances in KUYAN
LOCATION:KUYAN App
ATTENDEE:MAILTO:{emails.split(',')[0].strip()}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""

            # Offer download
            st.download_button(
                label="📅 Download .ics File",
                data=ics_content,
                file_name=f"kuyan_reminder_{start_date.strftime('%Y%m%d')}.ics",
                mime="text/calendar",
                width="stretch"
            )
            st.success("Calendar invite generated! Click above to download.")
        else:
            st.error("Please enter at least one email address")


# ===== EXPORT DASHBOARD WIDGET =====

def render_export_widget():
    """Export Dashboard widget for exporting as PDF/PNG"""

    st.write("**Export Dashboard**")
    st.caption("Export the dashboard view in various formats")

    # Format selector
    export_format = st.selectbox(
        "Select Format",
        options=["PNG (Image)", "PDF (Document)", "HTML (Interactive)"],
        key="export_format"
    )

    st.write("")

    # Export instructions
    if export_format == "PNG (Image)":
        st.info("""
**PNG Export Instructions:**
1. Navigate to the Dashboard tab
2. Use your browser's screenshot tool or:
   - **Windows**: Win + Shift + S
   - **Mac**: Cmd + Shift + 4
   - **Linux**: Use Screenshot tool
3. Select the dashboard area to capture
        """)

    elif export_format == "PDF (Document)":
        st.info("""
**PDF Export Instructions:**
1. Navigate to the Dashboard tab
2. Use browser's Print function:
   - **Chrome/Edge**: Ctrl/Cmd + P
   - Select "Save as PDF" as destination
   - Choose "Save"
        """)

    elif export_format == "HTML (Interactive)":
        st.info("""
**HTML Export Instructions:**
1. Navigate to the Dashboard tab
2. Use browser's Save Page function:
   - **Chrome/Edge**: Ctrl/Cmd + S
   - Select "Webpage, Complete"
   - Choose save location
        """)

    st.divider()
    st.caption("Tip: retract the side bar using the top arrow before exporting")


# ===== CALCULATOR WIDGET =====

def render_calculator_widget():
    """Calculator widget content"""

    # Initialize calculator history in session state
    if "calc_history" not in st.session_state:
        st.session_state.calc_history = []
    if "calc_trigger" not in st.session_state:
        st.session_state.calc_trigger = False

    # Callback to trigger calculation on Enter
    def on_enter():
        st.session_state.calc_trigger = True

    # Calculator input
    expression = st.text_input(
        "Enter calculation",
        placeholder="e.g., 1500 * 1.35 + 200",
        key="calc_input",
        help="Use +, -, *, /, (), and numbers. Press Enter to calculate.",
        on_change=on_enter
    )

    # Calculate and Clear buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        calculate = st.button("Calculate", width="stretch", type="primary", key="calc_button")
    with col2:
        clear_history = st.button("Clear History", width="stretch", key="clear_calc_history")

    # Check if calculation should be triggered (by Enter or button click)
    should_calculate = calculate or st.session_state.calc_trigger
    if st.session_state.calc_trigger:
        st.session_state.calc_trigger = False  # Reset trigger

    # Clear history
    if clear_history:
        st.session_state.calc_history = []
        st.rerun()

    # Perform calculation
    if should_calculate and expression:
        try:
            # Safe evaluation of mathematical expressions
            result = eval(expression, {"__builtins__": {}}, {})

            # Add to history
            st.session_state.calc_history.insert(0, {
                "expression": expression,
                "result": result
            })

            # Keep only last 5 calculations
            st.session_state.calc_history = st.session_state.calc_history[:5]

            # Display result
            st.success(f"**Result:** {result:,.2f}")

        except Exception as e:
            st.error(f"Invalid expression: {str(e)}")

    # Display calculation history
    if st.session_state.calc_history:
        st.divider()
        st.caption("Recent Calculations")

        for calc in st.session_state.calc_history:
            with st.container():
                col1, col2 = st.columns([1.5, 1])
                with col1:
                    st.text(calc["expression"])
                with col2:
                    st.text(f"= {calc['result']:,.2f}")


# Main app
def main():
    # Inject custom CSS for button styling
    inject_custom_css()

    # Render sandbox banner if in sandbox mode
    render_sandbox_banner()

    # Show toast if sandbox was just reset
    if st.session_state.get('sandbox_reset', False):
        st.toast("Sandbox reset successfully!", icon="🔄")
        st.session_state.sandbox_reset = False

    # Initialize session state
    if "base_currency" not in st.session_state:
        # Set default to first enabled currency
        default_currency = get_default_currency()
        st.session_state.base_currency = default_currency

    # Render sidebar and get selected settings page
    settings_page = render_sidebar()

    # Check if a settings page is selected
    if settings_page in ["Owners", "Accounts", "Currencies"]:
        # Show settings page
        if settings_page == "Owners":
            page_owners()
        elif settings_page == "Accounts":
            page_accounts()
        elif settings_page == "Currencies":
            page_currencies()
    else:
        # Custom CSS to make tabs larger
        st.markdown("""
            <style>
            div[data-baseweb="tab-list"] {
                gap: 8px !important;
            }
            div[data-baseweb="tab-list"] button {
                height: 50px !important;
                padding: 12px 20px !important;
            }
            div[data-baseweb="tab-list"] button[role="tab"] * {
                font-size: 24px !important;
                font-weight: 600 !important;
            }
            </style>
        """, unsafe_allow_html=True)


        # Main navigation tabs at the top for primary pages
        tab1, tab2, tab3 = st.tabs(
            ["📊 Overview", "💰 Update Balances", "📜 History"]
        )

        with tab1:
            page_dashboard()

        with tab2:
            page_update_balances()

        with tab3:
            page_history()


if __name__ == "__main__":
    main()

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Agentic Grocery OS",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme with navbar-style tabs
st.markdown("""
    <style>
    /* Main background */
    .main {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        color: #ffffff !important;
    }

    /* Ensure all text is visible */
    .main * {
        color: #ffffff !important;
    }

    /* Override Streamlit defaults */
    .stMarkdown, .stText {
        color: #ffffff !important;
    }

    div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }

    div[data-testid="stMarkdownContainer"] {
        color: #ffffff !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a2a4e 0%, #0f1b3a 100%);
    }

    [data-testid="stSidebar"] * {
        color: #e0e6ed !important;
    }

    /* Hide default tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background-color: rgba(15, 27, 58, 0.8);
        padding: 0;
        border-radius: 10px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }

    .stTabs [data-baseweb="tab"] {
        height: 60px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 0;
        color: #a8b8d8;
        font-size: 16px;
        font-weight: 600;
        padding: 0 2rem;
        border: none;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }

    .stTabs [data-baseweb="tab"]:last-child {
        border-right: none;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(66, 135, 245, 0.2);
        color: #ffffff;
        transform: translateY(-2px);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4287f5 0%, #3b5998 100%);
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(66, 135, 245, 0.4);
    }

    /* Button styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
        background: linear-gradient(135deg, #4287f5 0%, #3b5998 100%);
        color: white;
        border: none;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(66, 135, 245, 0.5);
        background: linear-gradient(135deg, #5a9aff 0%, #4a6ab5 100%);
    }

    /* Text colors - Force white for all text */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700;
    }

    p, label, .stMarkdown, span, div {
        color: #ffffff !important;
    }

    /* Specific fixes for title and descriptions */
    [data-testid="stHeader"] {
        color: #ffffff !important;
    }

    .element-container {
        color: #ffffff !important;
    }

    /* Input fields */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.1);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
    }

    .stTextInput>div>div>input::placeholder {
        color: #a8b8d8;
    }

    /* Slider */
    .stSlider {
        color: #ffffff;
    }

    /* Dataframe */
    .stDataFrame {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 8px;
        overflow: hidden;
    }

    /* Success/Info/Error boxes */
    .stSuccess, .stInfo, .stWarning, .stError {
        background-color: rgba(255, 255, 255, 0.1);
        color: #ffffff;
        border-radius: 8px;
        backdrop-filter: blur(10px);
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        color: #ffffff;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.1);
        color: #ffffff !important;
        border-radius: 8px;
    }

    .streamlit-expanderContent {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 0 0 8px 8px;
    }

    /* Cards */
    .info-card {
        background: linear-gradient(135deg, rgba(66, 135, 245, 0.2) 0%, rgba(59, 89, 152, 0.2) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        margin: 1rem 0;
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #4287f5 !important;
    }

    /* JSON viewer */
    .stJson {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
    }

    /* Warning box for confirmation */
    .confirmation-box {
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.2) 0%, rgba(255, 152, 0, 0.2) 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'order_preview' not in st.session_state:
    st.session_state.order_preview = None
if 'show_confirmation' not in st.session_state:
    st.session_state.show_confirmation = False

# Sidebar
with st.sidebar:
    st.markdown("<div style='text-align: center; padding: 1rem 0;'>", unsafe_allow_html=True)
    st.markdown("# 🛒")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Configuration")
    API = st.text_input('🌐 API Base URL', 'http://localhost:8000', help="Enter your API endpoint")

    st.markdown("---")
    st.markdown("### 📊 System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Status", "🟢 Online")
    with col2:
        st.metric("API", "✓ Ready")

    st.markdown("---")
    st.markdown("### 📖 Quick Guide")
    st.markdown("""
    - **Auto Order**: Predict inventory needs
    - **Pricing Rules**: Optimize product prices
    - **Supplier Hub**: Query purchase history
    """)

# Main header
st.markdown("<h1 style='text-align: center; font-size: 3rem; margin-bottom: 0.5rem;'>🛒 Agentic Grocery OS</h1>",
            unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; color: #ffffff; font-size: 1.2rem; margin-bottom: 2rem;'>Intelligent Inventory & Pricing Management System</p>",
    unsafe_allow_html=True)

# Navbar-style tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["📦 Inventory Management", "💰 Pricing Optimization", "🤝 Supplier Intelligence", "📜 Order History"])

# Tab 1: Auto Order with Confirmation
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    st.markdown("### 📦 Automated Inventory Ordering")
    st.markdown("Predict and generate orders based on historical consumption patterns.")
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        days_ahead = st.slider("📅 Forecast Period (days)", 1, 14, 3, help="Select how many days ahead to forecast")

        # Preview Order Button
        if st.button('🔍 Preview Order', use_container_width=True):
            with st.spinner('Analyzing inventory patterns...'):
                try:
                    r = requests.post(f'{API}/order/preview', json={'days_ahead': days_ahead})
                    data = r.json()
                    st.session_state.order_preview = data
                    st.session_state.show_confirmation = True
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Show order preview and confirmation
    if st.session_state.show_confirmation and st.session_state.order_preview:
        data = st.session_state.order_preview

        if data.get('status') == 'preview':
            st.markdown("<br>", unsafe_allow_html=True)

            # Warning box
            st.markdown("""
            <div class='confirmation-box'>
                <strong>⚠️ Confirmation Required</strong><br>
                Review the order details below before sending to supplier via WhatsApp.
            </div>
            """, unsafe_allow_html=True)

            # Display the WhatsApp message preview
            st.markdown("### 📱 WhatsApp Message Preview")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(66, 135, 245, 0.2) 0%, rgba(59, 89, 152, 0.2) 100%); 
                        padding: 1.5rem; 
                        border-radius: 8px; 
                        border-left: 4px solid #4287f5;
                        color: #ffffff;
                        backdrop-filter: blur(10px);
                        margin: 1rem 0;
                        white-space: pre-line;
                        font-family: monospace;">
{data['message']}
            </div>
            """, unsafe_allow_html=True)

            # Display order table
            if 'orders' in data and data['orders']:
                st.markdown("### 📋 Order Details")
                df = pd.DataFrame(data['orders'])
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "item": st.column_config.TextColumn("🏷️ Item", width="medium"),
                        "qty": st.column_config.NumberColumn("📊 Quantity", width="small", format="%d"),
                        "unit": st.column_config.TextColumn("📦 Unit", width="small")
                    }
                )

                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Items", len(df))
                with col2:
                    st.metric("Total Quantity", df['qty'].sum() if 'qty' in df else 0)
                with col3:
                    st.metric("Unique Products", df['item'].nunique() if 'item' in df else 0)

                # Confirmation buttons
                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2, col3, col4, col5 = st.columns([1, 1.5, 0.5, 1.5, 1])

                with col2:
                    if st.button('✅ Confirm & Send to Supplier', use_container_width=True, type="primary"):
                        with st.spinner('Sending order via WhatsApp...'):
                            try:
                                confirm_payload = {
                                    'orders': data['orders'],
                                    'store_name': 'My Store'
                                }
                                r = requests.post(f'{API}/order/confirm', json=confirm_payload)
                                result = r.json()

                                if result.get('status') == 'sent':
                                    st.success('✅ Order sent successfully via WhatsApp!')
                                    st.session_state.show_confirmation = False
                                    st.session_state.order_preview = None
                                else:
                                    st.error(f"❌ Failed to send: {result.get('message')}")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")

                with col4:
                    if st.button('❌ Cancel Order', use_container_width=True):
                        st.session_state.show_confirmation = False
                        st.session_state.order_preview = None
                        st.info("Order cancelled. No message sent.")
                        st.rerun()

        elif data.get('status') == 'no_items':
            st.info("ℹ️ No items are currently low on stock.")
            st.session_state.show_confirmation = False

        elif data.get('status') == 'no_order':
            st.info("ℹ️ No order required after forecasting.")
            st.session_state.show_confirmation = False

# Tab 2: Pricing Rules
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    st.markdown("### 💰 Dynamic Pricing Optimization")
    st.markdown("Apply intelligent pricing rules based on market conditions and inventory levels.")
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button('⚡ Run Pricing Rules', use_container_width=True):
            with st.spinner('Optimizing prices...'):
                try:
                    r = requests.post(f'{API}/pricing/adjust')
                    data = r.json()

                    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                        st.markdown("### 📊 Pricing Adjustments")
                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        st.success(f"✅ Successfully adjusted pricing for {len(df)} items")

                    elif isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                                st.markdown(f"### 📈 {key.replace('_', ' ').title()}")
                                df = pd.DataFrame(value)
                                st.dataframe(df, use_container_width=True, hide_index=True)
                            else:
                                st.info(f"**{key.replace('_', ' ').title()}:** {value}")
                    else:
                        st.json(data)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Tab 3: Supplier Hub
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    st.markdown("### 🤝 Supplier Intelligence Hub")
    st.markdown("Ask questions about your purchase history and supplier relationships.")
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("💡 Example Questions"):
        st.markdown("""
        - What items did we purchase from Baron Suppliers last month?
        - What was the average price for tomatoes in October?
        - Which supplier offers the best prices for onions?
        - Show me all purchases above $100
        """)

    q = st.text_input('🔍 Ask a question about suppliers or purchases',
                      placeholder="e.g., What items did we buy from XYZ Suppliers?")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button('🔎 Search', use_container_width=True) and q:
            with st.spinner('Analyzing purchase data...'):
                try:
                    r = requests.post(f'{API}/supplier/query', json={'query': q})
                    data = r.json()

                    st.markdown("### 📝 Answer")
                    if isinstance(data, dict):
                        if 'answer' in data or 'response' in data:
                            answer = data.get('answer') or data.get('response')
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, rgba(66, 135, 245, 0.2) 0%, rgba(59, 89, 152, 0.2) 100%); 
                                        padding: 1.5rem; 
                                        border-radius: 8px; 
                                        border-left: 4px solid #4287f5;
                                        color: #ffffff;
                                        backdrop-filter: blur(10px);">
                                {answer}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.json(data)
                    else:
                        st.write(data)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #ffffff; padding: 1rem;'>
    <small>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Powered by AI & Analytics</small>
</div>
""", unsafe_allow_html=True)

# Tab 4: Order History
with tab4:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    st.markdown("### 📜 Order History")
    st.markdown("View all past orders sent to suppliers.")
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Limit selector
        limit = st.selectbox("📊 Number of orders to display", [10, 25, 50, 100], index=2)

        if st.button('🔄 Refresh History', use_container_width=True):
            st.rerun()

    # Fetch order history
    try:
        with st.spinner('Loading order history...'):
            r = requests.get(f'{API}/order/history', params={'limit': limit})
            data = r.json()

            if 'orders' in data and len(data['orders']) > 0:
                orders = data['orders']
                df = pd.DataFrame(orders)

                # Display summary metrics
                st.markdown("### 📊 Summary")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Orders", df['order_id'].nunique() if 'order_id' in df else 0)
                with col2:
                    st.metric("Total Items", len(df))
                with col3:
                    st.metric("Unique Products", df['item'].nunique() if 'item' in df else 0)
                with col4:
                    total_qty = df['qty'].sum() if 'qty' in df else 0
                    st.metric("Total Quantity", f"{total_qty:,.0f}")

                # Display order history table
                st.markdown("### 📋 Detailed Order History")

                # Reorder columns for better display
                display_columns = ['order_id', 'timestamp', 'item', 'qty', 'unit', 'status']
                df_display = df[display_columns] if all(col in df.columns for col in display_columns) else df

                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "order_id": st.column_config.TextColumn("📋 Order ID", width="medium"),
                        "timestamp": st.column_config.TextColumn("🕒 Date & Time", width="medium"),
                        "item": st.column_config.TextColumn("🏷️ Item", width="medium"),
                        "qty": st.column_config.NumberColumn("📊 Quantity", width="small", format="%d"),
                        "unit": st.column_config.TextColumn("📦 Unit", width="small"),
                        "status": st.column_config.TextColumn("✅ Status", width="small")
                    }
                )

                # Group by order_id to show individual orders
                if 'order_id' in df.columns:
                    st.markdown("### 📦 Orders Grouped by Order ID")

                    # Get unique order IDs (most recent first)
                    unique_orders = df['order_id'].unique()[:10]  # Show last 10 orders

                    for order_id in unique_orders:
                        order_items = df[df['order_id'] == order_id]
                        timestamp = order_items.iloc[0]['timestamp'] if 'timestamp' in order_items else 'N/A'
                        status = order_items.iloc[0]['status'] if 'status' in order_items else 'N/A'

                        with st.expander(f"🔖 Order #{order_id} - {timestamp} ({len(order_items)} items)"):
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.write(f"**Status:** {status}")
                                st.write(f"**Total Items:** {len(order_items)}")
                            with col2:
                                total = order_items['qty'].sum() if 'qty' in order_items else 0
                                st.write(f"**Total Qty:** {total}")

                            # Show items in this order
                            order_display = order_items[['item', 'qty', 'unit']]
                            st.dataframe(
                                order_display,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "item": "Item",
                                    "qty": "Quantity",
                                    "unit": "Unit"
                                }
                            )

                # Download button
                st.markdown("### 💾 Export Data")
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Order History as CSV",
                    data=csv,
                    file_name=f"order_history_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            else:
                st.info("📭 No order history found. Place your first order to see it here!")

    except Exception as e:
        st.error(f"❌ Error loading order history: {str(e)}")
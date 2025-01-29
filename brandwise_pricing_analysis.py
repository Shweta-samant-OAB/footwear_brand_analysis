import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Home", page_icon="👋", layout="wide")

st.title("Product Type Comparison Across Brands")

PRICE_RANGES = [
    "0-100",
    "100-200",
    "200-300",
    "300-400",
    "400-500",
    "500+"
]

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Data Cleaning
    df['Product type'] = df['Product type'].str.replace('Lace Up', 'Lace Up Trainers', regex=False) 
    df['Product type'] = df['Product type'].str.replace('Lace Up Trainers', 'Lace Up', regex=False) 

    selected_range = st.selectbox("Select Price Range", PRICE_RANGES)
    
    if selected_range != "500+":
        min_price = float(selected_range.split("-")[0])
        max_price = float(selected_range.split("-")[1])
    else:
        min_price = 500
        max_price = float(df['Price'].max())
    
    # First, combine "Lace up" and "Lace up trainers" into one category
    df['Product type'] = df['Product type'].replace({"Lace up trainers": "Lace up"})

    # Now filter the DataFrame based on price range
    df_filtered = df[(df['Price'] >= min_price) & (df['Price'] <= max_price)]

    # Get top 10 product types
    top_10_products = df_filtered['Product type'].value_counts().head(10).index.tolist()
    
    # Create a copy of the DataFrame for modification
    df_filtered_with_others = df_filtered.copy()
    
    # Replace all non-top-10 product types with "Others"
    df_filtered_with_others.loc[~df_filtered_with_others['Product type'].isin(top_10_products), 'Product type'] = 'Others'
    
    # Calculate frequencies including "Others"
    overall_freq = df['Product type'].value_counts()
    overall_others = pd.Series({'Others': overall_freq[~overall_freq.index.isin(top_10_products)].sum()})
    overall_freq = pd.concat([overall_freq[overall_freq.index.isin(top_10_products)], overall_others])
    
    range_freq = df_filtered_with_others['Product type'].value_counts()
    
    fig_freq = make_subplots(rows=1, cols=2, 
                            subplot_titles=('Overall Product Type Distribution',
                                          f'Distribution in Price Range ${min_price}-${max_price}')) 
    
    fig_freq.add_trace(
        go.Bar(x=overall_freq.index, y=overall_freq.values, name='Overall'),
        row=1, col=1
    )
    
    fig_freq.add_trace(
        go.Bar(x=range_freq.index, y=range_freq.values, 
               name=f'Range ${min_price}-${max_price}'),
        row=1, col=2
    )
    
    fig_freq.update_layout(
        height=400,
        showlegend=True,
        title_text="Product Type Frequency Comparison"
    )
    
    fig_freq.update_xaxes(tickangle=45)
    
    st.plotly_chart(fig_freq, use_container_width=True)
    
    # Include "Others" in top products list
    top_products = list(range_freq.index)
    top_products = [p for p in range_freq.index if p != "Others"] + (["Others"] if "Others" in range_freq.index else [])
    
    fig = go.Figure()
    
    brands = df_filtered_with_others['Brand'].unique().tolist()
    brand_spacing = 75

    # Calculate brand minimum prices
    brand_min_prices = {brand: min(df_filtered_with_others[df_filtered_with_others['Brand'] == brand]['Price']) 
                       for brand in brands}
    
    # Sort brands based on minimum prices in ascending order
    sorted_brands = sorted(brands, key=lambda brand: brand_min_prices[brand])

    # Consistent red color for all brands
    brand_colors = ['red'] * len(sorted_brands)

    for idx, brand in enumerate(sorted_brands):
        brand_data = df_filtered_with_others[df_filtered_with_others['Brand'] == brand]
        
        product_info = []
        
        for prod_type in top_products:
            prod_data = brand_data[brand_data['Product type'] == prod_type]
            if not prod_data.empty:
                max_price = prod_data['Price'].max()
                freq = len(prod_data)
                product_info.append({
                    'product_type': prod_type,
                    'price': max_price,
                    'frequency': freq,
                    'x_coord': top_products.index(prod_type)
                })
        
        product_info.sort(key=lambda x: x['x_coord'])
        
        if product_info:
            brand_min_price = brand_min_prices[brand]
            brand_max_price = max(p['price'] for p in product_info)
            price_range = brand_max_price - brand_min_price
            
            y_coords = []
            for p in product_info:
                if price_range != 0:
                    variation = ((p['price'] - brand_min_price) / price_range) * (brand_spacing * 0.8)
                    y_coords.append(idx * brand_spacing + variation)
                else:
                    y_coords.append(idx * brand_spacing)

            fig.add_trace(go.Scatter(
                x=[p['x_coord'] for p in product_info],
                y=y_coords,
                mode='lines+markers',
                name=brand,
                marker=dict(
                    size=[max(10, min(20, p['frequency']*2)) for p in product_info],
                    color='red',
                    showscale=False
                ),
                line=dict(color="blue", width=2),
                text=[f"{p['product_type']}<br>Price: ${p['price']:.2f}<br>Frequency: {p['frequency']}" 
                      for p in product_info],
                hovertemplate="<b>%{text}</b><br>" + "Brand: " + brand + "<br>" + "<extra></extra>"
            ))
            
            price_display = f"${brand_min_price}" if brand_min_price == brand_max_price else f"${brand_min_price} - ${brand_max_price}"
            fig.add_annotation(
                x=len(top_products),
                y=idx * brand_spacing,
                text=price_display,
                showarrow=False,
                font=dict(size=12, color="black"),
                xanchor='left'
            )
    
    fig.update_layout(
        title=f'Product Type Comparison (Price Range: ${min_price}-${max_price})',
        xaxis=dict(
            title='Product Types',
            ticktext=top_products,
            tickvals=list(range(len(top_products))),
            tickangle=0
        ),
        yaxis=dict(
            title='Brands',
            ticktext=sorted_brands,
            tickvals=[i * brand_spacing for i in range(len(sorted_brands))]  # Adjusted brand spacing
        ),
        height=max(700, 200 + (len(brands) * brand_spacing)),  # Increase height dynamically
        showlegend=False,
        margin=dict(l=150, r=50, b=100, t=50),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show detailed frequency analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Overall Product Type Frequencies")
        overall_df = pd.DataFrame({
            'Product Type': overall_freq.index,
            'Count': overall_freq.values,
            'Percentage': (overall_freq.values / len(df) * 100).round(2)
        })
        st.dataframe(overall_df)
    
    with col2:
        st.subheader(f"Frequencies in Range ${min_price}-${max_price}")
        range_df = pd.DataFrame({
            'Product Type': range_freq.index,
            'Count': range_freq.values,
            'Percentage': (range_freq.values / len(df_filtered_with_others) * 100).round(2)
        })
        st.dataframe(range_df)

else:
    st.write("Please upload a CSV file with columns: 'Brand', 'Price', and 'Product type'")

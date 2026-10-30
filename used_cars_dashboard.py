"""
Indonesia Used Car Market Dashboard
Run:  streamlit run used_cars_dashboard.py

Default data is SIMULATED (not real market data).
To use real data, upload a CSV in the sidebar with columns:
brand, model, year, price, mileage, transmission, fuel, city
(price in IDR, mileage in km)
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Indonesia Used Car Dashboard", page_icon="🚗", layout="wide")

CURRENT_YEAR = 2026

# ---------------------------------------------------------------- SIMULATED DATA
CATALOG = {
    "Toyota": {"Avanza": 240e6, "Innova": 380e6, "Rush": 280e6, "Agya": 160e6, "Fortuner": 520e6},
    "Honda": {"Brio": 175e6, "Jazz": 290e6, "HR-V": 380e6, "CR-V": 570e6, "Mobilio": 220e6},
    "Daihatsu": {"Xenia": 230e6, "Terios": 270e6, "Ayla": 145e6, "Sigra": 150e6},
    "Suzuki": {"Ertiga": 245e6, "Ignis": 170e6, "Baleno": 230e6, "Carry": 175e6},
    "Mitsubishi": {"Xpander": 280e6, "Pajero Sport": 540e6, "L300": 260e6},
    "Nissan": {"Grand Livina": 220e6, "Juke": 250e6, "March": 160e6},
    "Mazda": {"Mazda 2": 300e6, "CX-5": 480e6},
    "Hyundai": {"Creta": 330e6, "Stargazer": 270e6},
    "Wuling": {"Confero": 170e6, "Almaz": 330e6},
    "BMW": {"320i": 780e6, "X1": 900e6},
    "Mercedes-Benz": {"C200": 950e6, "E250": 1200e6},
}
BRAND_WEIGHTS = {"Toyota": 28, "Honda": 18, "Daihatsu": 14, "Suzuki": 10, "Mitsubishi": 9,
                 "Nissan": 4, "Mazda": 3, "Hyundai": 3, "Wuling": 3, "BMW": 4, "Mercedes-Benz": 4}
CITIES = {"Jakarta": 25, "Surabaya": 12, "Bandung": 10, "Medan": 8, "Semarang": 7,
          "Makassar": 6, "Denpasar": 5, "Palembang": 5, "Yogyakarta": 5, "Balikpapan": 4}


@st.cache_data
def generate_data(n: int = 4000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    brands = rng.choice(list(BRAND_WEIGHTS), n,
                        p=np.array(list(BRAND_WEIGHTS.values())) / sum(BRAND_WEIGHTS.values()))
    cities = rng.choice(list(CITIES), n,
                        p=np.array(list(CITIES.values())) / sum(CITIES.values()))
    rows = []
    for brand, city in zip(brands, cities):
        model = rng.choice(list(CATALOG[brand]))
        age = int(np.clip(rng.gamma(2.2, 2.6), 1, 18))
        year = CURRENT_YEAR - age
        km = int(np.clip(rng.normal(age * 14000, 6000), 3000, 300000))
        new_price = CATALOG[brand][model]
        price = new_price * (0.87 ** age) * (1 - km / 1_500_000) * rng.normal(1, 0.07)
        price = max(round(price / 1e6) * 1e6, 25e6)
        trans = rng.choice(["Manual", "Automatic"], p=[0.45, 0.55] if age > 6 else [0.30, 0.70])
        diesel_models = ("Fortuner", "Pajero Sport", "L300", "Innova")
        fuel = "Diesel" if model in diesel_models and rng.random() < 0.6 else "Petrol"
        rows.append((brand, model, year, price, km, trans, fuel, city))
    return pd.DataFrame(rows, columns=["brand", "model", "year", "price", "mileage",
                                       "transmission", "fuel", "city"])


def idr(x: float) -> str:
    """Format a rupiah amount in millions, e.g. 'Rp 240 mn'."""
    return f"Rp {x / 1e6:,.0f} mn"


# ---------------------------------------------------------------- SIDEBAR
st.sidebar.header("⚙️ Filters")
upload = st.sidebar.file_uploader("Upload your own CSV (optional)", type="csv")
if upload:
    df = pd.read_csv(upload)
    st.sidebar.success("Using uploaded data")
else:
    df = generate_data()
    st.sidebar.info("Using simulated data")

brand_sel = st.sidebar.multiselect("Brand", sorted(df.brand.unique()), default=sorted(df.brand.unique()))
city_sel = st.sidebar.multiselect("City", sorted(df.city.unique()), default=sorted(df.city.unique()))
year_sel = st.sidebar.slider("Model year", int(df.year.min()), int(df.year.max()),
                             (int(df.year.min()), int(df.year.max())))
pmin, pmax = int(df.price.min() / 1e6), int(df.price.max() / 1e6)
price_sel = st.sidebar.slider("Price (IDR million)", pmin, pmax, (pmin, pmax))
trans_sel = st.sidebar.multiselect("Transmission", df.transmission.unique(),
                                   default=list(df.transmission.unique()))
fuel_sel = st.sidebar.multiselect("Fuel", df.fuel.unique(), default=list(df.fuel.unique()))

f = df[
    df.brand.isin(brand_sel) & df.city.isin(city_sel)
    & df.year.between(*year_sel) & df.price.between(price_sel[0] * 1e6, price_sel[1] * 1e6)
    & df.transmission.isin(trans_sel) & df.fuel.isin(fuel_sel)
]

# ---------------------------------------------------------------- HEADER + KPIs
st.title("🚗 Indonesia Used Car Market Dashboard")
if f.empty:
    st.warning("No data matches the current filters.")
    st.stop()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Listings", f"{len(f):,}")
k2.metric("Average price", idr(f.price.mean()))
k3.metric("Median price", idr(f.price.median()))
k4.metric("Average mileage (km)", f"{f.mileage.mean():,.0f}")
k5.metric("% Automatic", f"{(f.transmission == 'Automatic').mean() * 100:.0f}%")

tab1, tab2, tab3 = st.tabs(["📊 Overview", "📉 Price & Depreciation", "📋 Data"])

# ---------------------------------------------------------------- TAB 1
with tab1:
    c1, c2 = st.columns(2)
    top_brands = f.brand.value_counts().reset_index()
    top_brands.columns = ["brand", "listings"]
    c1.plotly_chart(px.bar(top_brands, x="listings", y="brand", orientation="h",
                           title="Listings by brand").update_yaxes(autorange="reversed"),
                    use_container_width=True)

    avg_brand = f.groupby("brand", as_index=False).price.mean().sort_values("price")
    c2.plotly_chart(px.bar(avg_brand, x="price", y="brand", orientation="h",
                           title="Average price by brand (IDR)"),
                    use_container_width=True)

    c3, c4, c5 = st.columns(3)
    city_df = f.city.value_counts().reset_index()
    city_df.columns = ["city", "listings"]
    c3.plotly_chart(px.bar(city_df, x="city", y="listings", title="Listings by city"),
                    use_container_width=True)
    c4.plotly_chart(px.pie(f, names="transmission", title="Transmission", hole=0.45),
                    use_container_width=True)
    c5.plotly_chart(px.pie(f, names="fuel", title="Fuel type", hole=0.45),
                    use_container_width=True)

# ---------------------------------------------------------------- TAB 2
with tab2:
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.histogram(f, x="price", nbins=40, title="Price distribution (IDR)"),
                    use_container_width=True)
    c2.plotly_chart(px.box(f, x="brand", y="price", title="Price spread by brand"),
                    use_container_width=True)

    c3, c4 = st.columns(2)
    dep = f.groupby("year", as_index=False).price.mean()
    c3.plotly_chart(px.line(dep, x="year", y="price", markers=True,
                            title="Average price by model year"),
                    use_container_width=True)
    sample = f.sample(min(len(f), 1500), random_state=1)
    c4.plotly_chart(px.scatter(sample, x="mileage", y="price", color="brand", opacity=0.6,
                               hover_data=["model", "year", "city"],
                               title="Price vs mileage (sample of 1,500 listings)"),
                    use_container_width=True)

    st.subheader("Most listed models")
    top_models = (f.groupby(["brand", "model"])
                  .agg(listings=("price", "size"), avg_price=("price", "mean"),
                       avg_mileage=("mileage", "mean"))
                  .reset_index().sort_values("listings", ascending=False).head(15))
    top_models["avg_price"] = top_models.avg_price.map(idr)
    top_models["avg_mileage"] = top_models.avg_mileage.round(0).astype(int)
    st.dataframe(top_models, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------- TAB 3
with tab3:
    st.dataframe(f.sort_values("price"), use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download CSV (filtered)", f.to_csv(index=False).encode("utf-8"),
                       "used_cars_filtered.csv", "text/csv")

st.caption("⚠️ Default data is simulated for demo purposes, not real market prices.")


import importlib.util, sys
packages = ["streamlit", "pandas", "streamlit_folium", "folium"]
missing = [p for p in packages if importlib.util.find_spec(p) is None]
if missing:
    print("Missing packages:", ", ".join(missing))
    print("Run: pip install -r requirements.txt")
    sys.exit(1)
print("All required packages appear installed.")

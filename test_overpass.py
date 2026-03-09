import requests
import json
radius = 5000
lat = 45.78249557343524
lon = 4.866350445270991
overpass_url = 'http://overpass-api.de/api/interpreter'
overpass_query = f"""
[out:json];
(
  node["shop"="supermarket"](around:{radius},{lat},{lon});
  way["shop"="supermarket"](around:{radius},{lat},{lon});
  relation["shop"="supermarket"](around:{radius},{lat},{lon});
);
out center;
"""
print("Querying overpass...")
response = requests.post(overpass_url, data={'data': overpass_query})
data = response.json()
print('Number of elements:', len(data.get('elements', [])))
for element in data.get('elements', [])[:10]:
    name = element.get('tags', {}).get('name', '')
    print(name)

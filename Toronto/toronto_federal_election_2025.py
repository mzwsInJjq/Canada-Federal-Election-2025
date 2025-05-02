"""df: https://enr.elections.ca/DownloadResults.aspx"""

"""gdf: https://open.canada.ca/data/en/dataset/18bf3ea7-1940-46ec-af52-9ba3f77ed708/resource/1f4b018b-a303-48bb-8ea0-10746e7cf435"""

"""boundries: https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/index2021-eng.cfm?year=21"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

path = r"D:\EventResults.txt"
columns = [
    "Electoral district number - Numéro de la circonscription",
    "Electoral district name",
    "Nom de la circonscription",
    "Type of results",
    "Type de résultats",
    "Surname - Nom de famille",
    "Middle name(s) - Autre(s) prénom(s)",
    "Given name - Prénom",
    "Political affiliation",
    "Appartenance politique",
    "Votes obtained - Votes obtenus",
    "% Votes obtained - Votes obtenus %",
    "Rejected ballots - Bulletins rejetés",
    "Total number of ballots cast - Nombre total de votes déposés"]
df = pd.DataFrame(columns=columns)

with open(path, "r", encoding="utf-8") as file:
    for line in file:
        if not line[0].isnumeric():
            continue
        columns = line.strip().split("\t")
        df = pd.concat([df, pd.DataFrame([columns], columns=df.columns)], ignore_index=True)

toronto_ed_nums = [
    "35007", "35022", "35023", "35024",
    "35026", "35029", "35030", "35031",
    "35041", "35092", "35093", "35094",
    "35095", "35096", "35097", "35100",
    "35105", "35109", "35110", "35111",
    "35112", "35117", "35120", "35122"]

toronto_df = df[df["Electoral district number - Numéro de la circonscription"].isin(toronto_ed_nums) & df["Type of results"].str.startswith("preliminary")]
print(toronto_df.head(10))

# Sum all the liberal votes
lib = toronto_df[toronto_df["Political affiliation"] == "Liberal"]["Votes obtained - Votes obtenus"].astype(int).sum()
# Sum all the conservative votes
con = toronto_df[toronto_df["Political affiliation"] == "Conservative"]["Votes obtained - Votes obtenus"].astype(int).sum()
# Sum all the NDP votes
ndp = toronto_df[toronto_df["Political affiliation"] == "NDP-New Democratic Party"]["Votes obtained - Votes obtenus"].astype(int).sum()
# Sum all the other votes
other = toronto_df[~toronto_df["Political affiliation"].isin(["Liberal", "Conservative", "NDP-New Democratic Party"])]["Votes obtained - Votes obtenus"].astype(int).sum()
# Sum all the votes
total = lib + con + ndp + other

# Calculate the percentage of votes for each party
lib_perc = lib / total * 100
con_perc = con / total * 100
ndp_perc = ndp / total * 100
other_perc = other / total * 100

# Calculate the MOV (Margin of Victory) for each electoral district
mov = pd.DataFrame(columns=["Electoral district number - Numéro de la circonscription", "Electoral district name", "MOV"])
for ed in toronto_ed_nums:
    ed_df = toronto_df[toronto_df["Electoral district number - Numéro de la circonscription"] == ed]
    ed_name = ed_df["Electoral district name"].values[0]
    ed_mov = ed_df[ed_df["Political affiliation"] == 'Liberal']["% Votes obtained - Votes obtenus %"].astype(float).sum() - ed_df[ed_df["Political affiliation"] == 'Conservative']["% Votes obtained - Votes obtenus %"].astype(float).sum()
    mov = pd.concat([mov, pd.DataFrame([[ed, ed_name, ed_mov]], columns=mov.columns)], ignore_index=True)

# Print the MOV for each electoral district
print("MOV for each Toronto ED:")
for index, row in mov.iterrows():
    print(f"{row['Electoral district number - Numéro de la circonscription']} {row["Electoral district name"]}: {row['MOV']:.2f}%")

# Create a color map
norm = TwoSlopeNorm(vmin=-100, vcenter=0, vmax=100)
cmap = plt.get_cmap('bwr')

# Print the overall results
print("\nToronto 2025 Federal Election Results:")
print(f"Liberal: {lib} ({lib_perc:.2f}%)")
print(f"Conservative: {con} ({con_perc:.2f}%)")
print(f"NDP: {ndp} ({ndp_perc:.2f}%)")
print(f"Other: {other} ({other_perc:.2f}%)")

# Plotting the results
gdf = gpd.read_file(r"D:\FED_CA_2023_EN-SHP\FED_CA_2023_EN.shp")
gdf = gdf.to_crs("epsg:4326")
toronto_ed_nums = list(map(int, toronto_ed_nums))
gdf = gdf[gdf["FED_NUM"].isin(toronto_ed_nums)]

# Ensure both columns are of the same type before merging
gdf["FED_NUM"] = gdf["FED_NUM"].astype(str)
mov["Electoral district number - Numéro de la circonscription"] = mov["Electoral district number - Numéro de la circonscription"].astype(str)

# Add the MOV to the GeoDataFrame from mov
gdf = gdf.merge(mov, left_on="FED_NUM", right_on="Electoral district number - Numéro de la circonscription", how="left")

# Clip to the Toronto boundaries
boundries = gpd.read_file(r"D:\lpr_000b21a_e\lpr_000b21a_e.shp")
boundries = boundries[boundries['PRUID'] == '35']
boundries = boundries.to_crs("epsg:4326")
gdf = gpd.overlay(gdf, boundries, how='intersection', keep_geom_type=False)

# Plotting the map
fig, ax = plt.subplots(figsize=(5, 10))
gdf.plot(column='MOV', cmap=cmap, linewidth=0, ax=ax, norm=norm)
ax.axis('off')

# Set the bbox for Toronto
bbox = (-79.6392832, 43.5796082, -79.1132193, 43.8554425)
ax.set_xlim(bbox[0], bbox[2])
ax.set_ylim(bbox[1], bbox[3])

plt.savefig('toronto_federal_election_2025.pdf', format='pdf', bbox_inches='tight')
import sys
import spotipy
import spotipy.util as util
import json
import sqlite3
import matplotlib.pyplot as plt
import numpy as np

scope = 'user-library-read'
client_id = '72990b4d624944d6a669b2b7dcda750a'
client_secret = '23417561d668444b97c33560801fb204'
redirect_uri = 'http://google.com/'

if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    print("Usage: %s username" % (sys.argv[0],))
    sys.exit()

token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)

# Create Spotify object
sp = spotipy.Spotify(auth=token)

# Print list of genres
genres = sp.recommendation_genre_seeds()['genres']
genre_list = []
for genre in genres:
	print(genre)

# Ask for user input to generate a list of genres (must be between 1-5 different genres)
print()
print("Choose up to 5 genres to create your playlist")
print()
while len(genre_list) < 5:
	action = input("Type 1 genre name or 'stop' to cancel: ")
	if action.lower() in genres:
		if action in genre_list:
			print("Genre already listed, please try again")
			continue
		else:
			genre_list.append(action.lower())
		continue
	elif action.lower() == 'stop':
		if len(genre_list) == 0:
			print("At least 1 genre must be entered, please try again")
			continue
		else:
			break
	else:
		print("Invalid input, please try again")
		continue

# Print genre_list input
print()
print(genre_list)
print()
	
# Create 100 track recommendations based on genre_list input
recs = sp.recommendations(seed_genres=genre_list, limit=100)
tracks = recs['tracks']
sort_popularity = sorted(tracks, key=lambda x: x['popularity'], reverse=True)

# Create Tracks database
conn = sqlite3.connect('tracks.sqlite')
cur = conn.cursor()
cur.execute('''DROP TABLE IF EXISTS Tracks''')
cur.execute('''
			CREATE TABLE IF NOT EXISTS Tracks
			(title TEXT, artist TEXT, duration INTEGER, popularity INTEGER)''')

# Output playlist and save track data to database
print("PLAYLIST:")
print("--------------------------------------------------")
for track in sort_popularity:
	title = track['name']
	duration = track['duration_ms']
	artist = track['artists'][0]['name']
	popularity = track['popularity']

	# print(json.dumps(track, sort_keys=True, indent=3))

	print("{}; {}; {}ms; {}".format(title, artist, duration, popularity))

	cur.execute('INSERT INTO Tracks (title, artist, duration, popularity) VALUES (?,?,?,?)',
		(title, artist, duration, popularity))

conn.commit()

# Calculate total playlist time, average song time, average popularity score
# Convert milliseconds to seconds, minutes, and hours
total_duration = 0
total_popularity = 0
cur.execute('SELECT * FROM Tracks')
for row in cur:
	d = row[2]
	p = row[3]
	total_duration += d
	total_popularity += p

h = total_duration / 3600000
hours = int(h)

m = (total_duration % 3600000) / 60000
minutes = int(m)

s = ((total_duration % 3600000) % 60000) / 1000
seconds = round(s)

hrs_min_sec = str(hours) + " h, " + str(minutes) + " m, " + str(seconds) + " s"

avg_duration_ms = total_duration / 100
avg_popularity = total_popularity / 100

avg_total_seconds = avg_duration_ms / 1000
avg_min = int(avg_total_seconds // 60)
avg_sec = round((avg_total_seconds % 60), 3)
avg_min_sec = str(avg_min) + " min, " + str(avg_sec) + " sec"

# Terminal output
print()
print("=============================================================")
print("Total time of playlist: " + str(total_duration) + " ms (" + hrs_min_sec + ")")
print("Average song duration: " + str(avg_duration_ms) + " ms (" + avg_min_sec + ")")
print("Average song popularity score: " + str(avg_popularity))
print("=============================================================")
print()

# Visualization - scatter plot and trend line of duration and popularity score
cur.execute('SELECT * FROM Tracks')
duration_list = []
popularity_list = []
for row in cur:
	duration_list.append(row[2] / 60000)
	popularity_list.append(row[3])

plt.plot(duration_list, popularity_list, 'm.')
plt.xlabel("Duration (min)")
plt.ylabel("Popularity Score")
plt.title("Correlation between duration and popularity of songs in playlist")

z = np.polyfit(duration_list, popularity_list, 1)
p = np.poly1d(z)
plt.plot(duration_list,p(duration_list),"k-")

plt.show()

# Visualization - bar graph of the duration of the top 5 most popular songs
top5_songs_popularity = []
top5_songs_duration = []
count = 1
for song in sort_popularity[:5]:
	popularity = song['popularity']
	duration = song['duration_ms'] / 60000

	top5_songs_popularity.append(str(popularity) + " (song " + str(count) + ")")
	top5_songs_duration.append(duration)
	count+=1

plt.figure(1, figsize=(10, 5))
plt.bar(top5_songs_popularity, top5_songs_duration, color='green')
plt.title('Duration of top 5 most popular songs in playlist')
plt.xlabel('Popularity score')
plt.ylabel('Duration (min)')

plt.show()



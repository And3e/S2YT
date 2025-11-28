from time import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
import inquirer

class MusicMigrator:
    def __init__(self, spotify_client_id, spotify_client_secret):
        print("\n" + "="*50)
        print("⏳  Initiating Spotify Authentication...")
        print("👀  Watch your browser! A window will open shortly.")
        print("⚠️   IMPORTANT WARNING:")
        print("    -> Ensure you log in with the CORRECT Spotify account.")
        print("    -> It must be the account registered in your Developer Dashboard.")
        print("="*50 + "\n")
        
        # Add a small delay so the user has time to read the warning
        time.sleep(2)

        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret,
            redirect_uri="http://127.0.0.1:8888/callback",
            scope="playlist-read-private playlist-read-collaborative",
            show_dialog=True
        ))
        
        try:
            print("... Waiting for user login ...")
            user = self.sp.me()
            print(f"✅  Logged in as: {user['display_name']} ({user['id']})")
        except Exception as e:
            print("❌  Authentication failed or cancelled.")
            raise e
        
        self.yt = None

    def login_to_youtube(self, headers_file='ytmusic_headers.json'):
        """
        Authenticates with YouTube Music.
        """
        try:
            self.yt = YTMusic(headers_file)
            print("✅ Successfully connected to YouTube Music.")
        except Exception as e:
            print(f"❌ YouTube Login Failed: {e}")
            print("Please ensure your headers.json is valid.")

    def select_spotify_playlists(self):
        """
        Fetches user's Spotify playlists and asks them to select which ones to move.
        """
        print("\nfetching your Spotify playlists...")
        results = self.sp.current_user_playlists(limit=50)
        playlists = results['items']
        
        choices = []
        playlist_map = {}
        
        for p in playlists:
            name = p['name']
            pid = p['id']
            display_name = f"{name} ({p['tracks']['total']} tracks)"
            choices.append(display_name)
            playlist_map[display_name] = {'id': pid, 'name': name}

        if not choices:
            print("No playlists found!")
            return []

        questions = [
            inquirer.Checkbox('selected_playlists',
                              message="Select playlists to migrate (Space to select, Enter to confirm)",
                              choices=choices,
                              ),
        ]
        answers = inquirer.prompt(questions)
        
        return [playlist_map[choice] for choice in answers['selected_playlists']]

    def migrate_playlists(self, selected_playlists):
        """
        The main logic to move songs.
        """
        if not self.yt:
            print("❌ You must login to YouTube first.")
            return

        for playlist in selected_playlists:
            print(f"\n🚀 Starting migration for: {playlist['name']}")
            
            try:
                yt_playlist_id = self.yt.create_playlist(
                    title=playlist['name'],
                    description="Migrated from Spotify"
                )
                print(f"   Created YouTube Playlist: {playlist['name']}")
            except Exception as e:
                print(f"   Error creating playlist: {e}")
                continue

            results = self.sp.playlist_items(playlist['id'])
            tracks = results['items']
            while results['next']:
                results = self.sp.next(results)
                tracks.extend(results['items'])

            video_ids = []
            for item in tracks:
                track = item['track']
                if not track: continue
                
                artist_name = track['artists'][0]['name']
                song_name = track['name']
                query = f"{artist_name} {song_name}"
                
                try:
                    search_results = self.yt.search(query, filter="songs")
                    if not search_results:
                        search_results = self.yt.search(query, filter="videos")
                    
                    if search_results:
                        # Grab the first result's ID
                        video_ids.append(search_results[0]['videoId'])
                        print(f"   Found: {query}")
                    else:
                        print(f"   ⚠️ Could not find: {query}")
                except Exception as e:
                    print(f"   Error searching {query}: {e}")

            if video_ids:
                try:
                    self.yt.add_playlist_items(yt_playlist_id, video_ids)
                    print(f"✅ added {len(video_ids)} tracks to {playlist['name']}")
                except Exception as e:
                    print(f"   Error adding tracks: {e}")
            
            print("------------------------------------------------")
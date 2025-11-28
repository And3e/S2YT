import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
import inquirer
from tqdm import tqdm
import random

class MusicMigrator:
    def __init__(self, spotify_client_id, spotify_client_secret):
        print("\n" + "="*50)
        print("⏳  Initiating Spotify Authentication...")
        print("="*50 + "\n")
        
        questions = [
            inquirer.List('auth_mode',
                message="How do you want to authenticate with Spotify?",
                choices=[
                    'Automatic (Open System Default Browser)',
                    'Manual (I will copy-paste the link myself)',
                ],
            ),
        ]
        answers = inquirer.prompt(questions)
        
        use_browser = True
        if answers['auth_mode'].startswith('Manual'):
            use_browser = False
            print("\n" + "-"*50)
            print("📋  MANUAL MODE SELECTED")
            print("1. Copy the URL that will appear below.")
            print("2. Paste it into the specific Browser/Tab you want to use.")
            print("-"*50 + "\n")

        auth_manager = SpotifyOAuth(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret,
            redirect_uri="http://127.0.0.1:8888/callback",
            scope="playlist-read-private playlist-read-collaborative",
            show_dialog=True,
            open_browser=use_browser
        )

        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        
        try:
            print("... Waiting for user login ...")
            # If Manual Mode: The URL prints here automatically by Spotipy.
            # You copy it -> Paste in Browser -> Agree -> Copy Redirect URL -> Paste in Terminal
            user = self.sp.me()
            print(f"✅ Logged in as: {user['display_name']} ({user['id']})")
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
                              message="Select playlists to migrate (Space to select, CTRL-D to confirm)",
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
            
            yt_playlist_id = None
            create_attempts = 0
            max_create_attempts = 3
            
            while create_attempts < max_create_attempts and yt_playlist_id is None:
                try:
                    yt_playlist_id = self.yt.create_playlist(
                        title=playlist['name'],
                        description="Migrated from Spotify"
                    )
                    print(f"   Created YouTube Playlist: {playlist['name']}")
                    
                except Exception as e:
                    error_msg = str(e)
                    if "Expecting value" in error_msg or "429" in error_msg:
                        wait_time = [10, 20, 60][create_attempts]
                        print(f"   ⏳ Error creating playlist (Rate Limit). Cooling down {wait_time}s...")
                        time.sleep(wait_time)
                        create_attempts += 1
                    else:
                        print(f"   ❌ Fatal Error creating playlist: {e}")
                        break

            if yt_playlist_id is None:
                print(f"   ⏭️ Skipping '{playlist['name']}' due to creation failure. (Try to re-generate YouTube Music headers)")
                continue

            # 2. Get Spotify Tracks
            results = self.sp.playlist_items(playlist['id'])
            tracks = results['items']
            while results['next']:
                results = self.sp.next(results)
                tracks.extend(results['items'])

            # 3. Find Video IDs
            video_ids = []
            print(f"   🔍 Searching for {len(tracks)} tracks...")
            
            for item in tqdm(tracks, desc="   Processing", unit="song"):
                if item is None or item.get('track') is None: continue
                track = item['track']
                if not track.get('artists'): continue

                query = f"{track['artists'][0]['name']} {track['name']}"
                
                # Wait between 0.5 and 2 seconds per song
                time.sleep(random.uniform(0.5, 2.0)) 

                found = False
                attempts = 0
                max_attempts = 3
                backoff_times = [10, 20, 60]
                
                while attempts < max_attempts and not found:
                    try:
                        search_results = self.yt.search(query, filter="songs")
                        
                        if not search_results:
                            search_results = self.yt.search(query, filter="videos")
                        
                        if search_results:
                            video_ids.append(search_results[0]['videoId'])
                            found = True
                        else:
                            # --- FALLBACK: Try searching the raw Spotify Track Name ---
                            fallback_query = track['name']
                            tqdm.write(f"      ⚠️ Standard search failed. Trying fallback: '{fallback_query}'...")
                            
                            time.sleep(1) 
                            
                            fallback_results = self.yt.search(fallback_query, filter="songs")
                            if not fallback_results:
                                fallback_results = self.yt.search(fallback_query, filter="videos")
                                
                            if fallback_results:
                                video_ids.append(fallback_results[0]['videoId'])
                                found = True
                                tqdm.write(f"      ✅ Found via fallback!")
                            else:
                                tqdm.write(f"      ❌ Strictly not found: {query}")
                                found = True
                            
                    except Exception as e:
                        error_msg = str(e)
                        
                        if "Expecting value" in error_msg or "429" in error_msg:
                            wait_time = backoff_times[attempts] if attempts < len(backoff_times) else 60
                            
                            tqdm.write(f"      ⏳ Rate limited. Cooling down {wait_time}s (Attempt {attempts+1}/{max_attempts})...")
                            
                            time.sleep(wait_time)
                            attempts += 1
                        else:
                            tqdm.write(f"      ❌ Error searching '{query}': {e}")
                            break

            # 4. Remove internal duplicates
            video_ids = list(dict.fromkeys(video_ids))

            # 5. Add to YouTube
            if video_ids:
                try:
                    print(f"   📤 Sending {len(video_ids)} tracks to YouTube...")
                    
                    response = self.yt.add_playlist_items(yt_playlist_id, video_ids, duplicates=True)
                    
                    if response.get('status') == 'STATUS_SUCCEEDED':
                        print(f"   ✅ SUCCESS! Added {len(video_ids)} tracks.")
                    else:
                        if 'actions' in response:
                            print(f"   ✅ SUCCESS! Added {len(video_ids)} tracks (forced).")
                        else:
                            print(f"   ⚠️ WARNING: API returned: {response}")
                        
                except Exception as e:
                    print(f"   ❌ Error adding tracks: {e}")
            
            print("------------------------------------------------")
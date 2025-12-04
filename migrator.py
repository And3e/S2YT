import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
import inquirer
from tqdm import tqdm
import random
from simple_term_menu import TerminalMenu

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
        Fetches user's Spotify playlists.
        Asks to Migrate All or Select Manually.
        """
        print("\nFetching your Spotify playlists...")
        
        results = self.sp.current_user_playlists(limit=50)
        playlists = results['items']
        
        while results['next']:
            results = self.sp.next(results)
            playlists.extend(results['items'])
            
        if not playlists:
            print("❌ No playlists found!")
            return []

        all_real_playlists = []
        menu_items = []

        for p in playlists:
            name = p['name']
            pid = p['id']
            total = p['tracks']['total'] if 'tracks' in p and p['tracks'] else 0
            
            display_str = f"{name} ({total} tracks)"
            
            menu_items.append(display_str)
            all_real_playlists.append({'id': pid, 'name': name})

        print(f"\n✅ Found {len(all_real_playlists)} playlists.")
        
        mode_questions = [
            inquirer.List('mode',
                message="How would you like to proceed?",
                choices=[
                    f'Select specific playlists manually',
                    f'Migrate ALL `{len(all_real_playlists)}` playlists immediately',
                ],
            ),
        ]
        mode_answer = inquirer.prompt(mode_questions)
        
        if mode_answer['mode'].startswith('Migrate ALL'):
            print(f"✅ 'Migrate All' chosen. Queueing {len(all_real_playlists)} playlists...")
            return all_real_playlists

        terminal_menu = TerminalMenu(
            menu_items,
            title="Select playlists (Space to select, Enter to confirm)",
            multi_select=True,
            show_multi_select_hint=False,
            multi_select_cursor="[X] ",
            multi_select_cursor_style=("fg_green", "bold"),
        )
        
        selected_indices = terminal_menu.show()
        
        if not selected_indices:
            return []

        selected_playlists = []
        for index in selected_indices:
            selected_playlists.append(all_real_playlists[index])

        return selected_playlists
    
    def migrate_playlists(self, selected_playlists):
        """
        The main logic to move songs.
        Includes Normalized Matching and a GLOBAL collision strategy.
        """
        if not self.yt:
            print("❌ You must login to YouTube first.")
            return

        # --- PRE-FETCH: Get existing YT playlists ---
        print("\n⏳ Fetching your existing YouTube Music playlists to check for duplicates...")
        try:
            my_yt_playlists = self.yt.get_library_playlists(limit=5000)
            
            yt_playlist_map_normalized = {}
            
            for p in my_yt_playlists:
                p_title = p['title']
                p_id = p['playlistId']
                # Normalize: Lowercase and strip whitespace
                norm_title = p_title.lower().strip()
                yt_playlist_map_normalized[norm_title] = {'original_title': p_title, 'id': p_id}
                
            print(f"✅ Indexed {len(yt_playlist_map_normalized)} existing YouTube playlists.")
            
        except Exception as e:
            print(f"⚠️ Could not fetch existing playlists (Collision check disabled): {e}")
            yt_playlist_map_normalized = {}

        # --- NEW: ASK FOR GLOBAL COLLISION STRATEGY ---
        if yt_playlist_map_normalized:
            print("\n" + "-"*50)
            strategy_questions = [
                inquirer.List('strategy',
                    message="How should we handle playlists that already exist on YouTube Music?",
                    choices=[
                        'Ask for each playlist individually (Default)',
                        'Always UPDATE existing playlists (Sync/Add missing songs)',
                        'Always CREATE new playlists (Duplicate)',
                    ],
                ),
            ]
            strategy_answer = inquirer.prompt(strategy_questions)
            global_strategy = strategy_answer['strategy']
        else:
            global_strategy = 'Ask for each playlist individually'

        total_playlists = len(selected_playlists)

        for index, playlist in enumerate(selected_playlists, start=1):
            print(f"\n🚀 Processing: {playlist['name']} ({index}/{total_playlists})")
            
            yt_playlist_id = None
            existing_video_ids = set()
            
            spotify_name_norm = playlist['name'].lower().strip()
            
            # 1. CHECK FOR COLLISION
            if spotify_name_norm in yt_playlist_map_normalized:
                
                match_data = yt_playlist_map_normalized[spotify_name_norm]
                found_title = match_data['original_title']
                found_id = match_data['id']
                
                action_to_take = None
                
                if global_strategy.startswith('Always UPDATE'):
                    print(f"      Match found ('{found_title}'). Auto-selecting: UPDATE.\n")
                    action_to_take = 'Update'
                elif global_strategy.startswith('Always CREATE'):
                    print(f"   ✨ Match found ('{found_title}'). Auto-selecting: CREATE NEW.")
                    action_to_take = 'Create'
                else:
                    # 'Ask for each' mode
                    print(f"   ⚠️  Found existing match: '{found_title}'")
                    q = [inquirer.List('action',
                            message=f"What do you want to do?",
                            choices=['Update existing', 'Create a new duplicate'],
                        )]
                    action_to_take = inquirer.prompt(q)['action']

                if action_to_take.startswith('Update'):
                    yt_playlist_id = found_id
                    print(f" 🔄 Syncing '{playlist['name']}' with existing playlist ID: {yt_playlist_id}")
                    
                    try:
                        print("   📥 Downloading current playlist tracks for deduplication...")
                        current_yt_data = self.yt.get_playlist(yt_playlist_id, limit=None)
                        if 'tracks' in current_yt_data:
                            for t in current_yt_data['tracks']:
                                if t.get('videoId'):
                                    existing_video_ids.add(t['videoId'])
                        print(f"   ℹ️  Existing playlist has {len(existing_video_ids)} tracks. They will be skipped.")
                    except Exception as e:
                        print(f"   ⚠️ Error fetching existing tracks: {e}. Duplicates might occur.")

            # 2. CREATE PLAYLIST (If we aren't updating an existing one)
            if yt_playlist_id is None:
                create_attempts = 0
                max_create_attempts = 3
                
                while create_attempts < max_create_attempts and yt_playlist_id is None:
                    try:
                        yt_playlist_id = self.yt.create_playlist(
                            title=playlist['name'],
                            description="Migrated from Spotify"
                        )
                        print(f"   ✨ Created New YouTube Playlist: {playlist['name']}")
                        
                        new_norm = playlist['name'].lower().strip()
                        yt_playlist_map_normalized[new_norm] = {'original_title': playlist['name'], 'id': yt_playlist_id}
                        
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
                print(f"   ⏭️ Skipping '{playlist['name']}' due to creation failure.")
                continue

            # 3. GET SPOTIFY TRACKS
            results = self.sp.playlist_items(playlist['id'])
            tracks = results['items']
            while results['next']:
                results = self.sp.next(results)
                tracks.extend(results['items'])

            # 4. SEARCH AND MATCH
            video_ids_to_add = []
            missing_songs = []

            print(f"   🔍 Searching for {len(tracks)} tracks...")
            
            for item in tqdm(tracks, desc="   Processing", unit="song"):
                if item is None or item.get('track') is None: continue
                track = item['track']
                if not track.get('artists'): continue

                query = f"{track['artists'][0]['name']} {track['name']}"
                
                time.sleep(random.uniform(0.5, 2.0)) 

                found_id = None
                
                attempts = 0
                max_attempts = 3
                backoff_times = [10, 20, 60]
                
                while attempts < max_attempts and found_id is None:
                    try:
                        search_results = self.yt.search(query, filter="songs")
                        if not search_results:
                            search_results = self.yt.search(query, filter="videos")
                        
                        if search_results:
                            found_id = search_results[0]['videoId']
                        else:
                            fallback_query = track['name']
                            time.sleep(1) 
                            
                            fallback_results = self.yt.search(fallback_query, filter="songs")
                            if not fallback_results:
                                fallback_results = self.yt.search(fallback_query, filter="videos")
                                
                            if fallback_results:
                                found_id = fallback_results[0]['videoId']
                            else:
                                missing_songs.append(f"{track['artists'][0]['name']} - {track['name']}")
                                break 
                            
                    except Exception as e:
                        error_msg = str(e)
                        if "Expecting value" in error_msg or "429" in error_msg:
                            wait_time = backoff_times[attempts] if attempts < len(backoff_times) else 60
                            tqdm.write(f"      ⏳ Rate limited. Cooling down {wait_time}s...")
                            time.sleep(wait_time)
                            attempts += 1
                        else:
                            tqdm.write(f"      ❌ Error searching '{query}': {e}")
                            missing_songs.append(f"{track['artists'][0]['name']} - {track['name']}")
                            break

                if found_id:
                    if found_id in existing_video_ids:
                        pass
                    else:
                        video_ids_to_add.append(found_id)

            # 5. REMOVE INTERNAL DUPLICATES
            video_ids_to_add = list(dict.fromkeys(video_ids_to_add))

            # 6. PUSH TO YOUTUBE
            if video_ids_to_add:
                try:
                    print(f"   📤 Adding {len(video_ids_to_add)} new tracks to YouTube...")
                    
                    response = self.yt.add_playlist_items(yt_playlist_id, video_ids_to_add, duplicates=True)
                    
                    if response.get('status') == 'STATUS_SUCCEEDED' or 'actions' in response:
                        print(f"   ✅ SUCCESS! Added {len(video_ids_to_add)} tracks.")
                    else:
                        print(f"   ⚠️ WARNING: API returned: {response}")
                        
                except Exception as e:
                    print(f"   ❌ Error adding tracks: {e}")
            else:
                print("   ℹ️  No new tracks to add (all found tracks were already in the playlist).")
            
            print("-" * 50)

            # 7. REPORT
            if missing_songs:
                print("\n" + "!"*50)
                print(f"⚠️  MISSING SONGS REPORT for '{playlist['name']}':")
                for song in missing_songs:
                    print(f"   • {song}")
                print("!"*50 + "\n")
            else:
                print(f"\nAll searched tracks were found (or already existed).\n")

            print("-" * 50)
            
        print("\n✨ All playlist migrations completed! ✨\n")
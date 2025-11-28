import shutil
from migrator import MusicMigrator
from dotenv import load_dotenv
import os
import ytmusicapi

load_dotenv(override=True)

def main():
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

    if os.path.exists(".cache"):
        os.remove(".cache")
    
    if os.path.exists("__pycache__"):
        try:
            shutil.rmtree("__pycache__")
            print(f"Deleted {"__pycache__"} and all its contents.")
        except Exception as e:
            print(f"Error deleting folder: {e}")

    app = MusicMigrator(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    
    if not os.path.exists("ytmusic_headers.json"):
        print("\n" + "="*60)
        print("🛑  'ytmusic_headers.json' was not found.")
        print("⚙️   Starting interactive setup...")
        print("-" * 60)
        print("📋  INSTRUCTIONS:")
        print("    1. Open Firefox -> music.youtube.com (Ensure you are logged in)")
        print("    2. Press F12 -> Go to 'Network' tab")
        print("    3. Click 'Create Playlist' in YouTube Music (enter any name)")
        print("    4. In Dev Tools, right-click the request named 'create' (POST)")
        print("    5. Select: Copy -> Copy Request Headers")
        print("-" * 60)
        print("👇  PASTE THE HEADERS BELOW AND PRESS ENTER:")
        print("="*60 + "\n")

        try:
            ytmusicapi.setup("ytmusic_headers.json")
            print("\n✅  'ytmusic_headers.json' created successfully!")
        except Exception as e:
            print(f"\n❌  Error creating headers: {e}")
            print("Please try running the script again.")
            return
        
    app.login_to_youtube()

    to_migrate = app.select_spotify_playlists()
    
    if not to_migrate:
        print("No playlists selected. Exiting.")
        return

    app.migrate_playlists(to_migrate)

if __name__ == "__main__":
    main()
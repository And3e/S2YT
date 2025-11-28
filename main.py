import shutil
from migrator import MusicMigrator
from dotenv import load_dotenv
import os
import ytmusicapi
import inquirer

load_dotenv(override=True)

def main():
    print("\n" + "-"*50)
    
    questions = [
        inquirer.List('clear_cache',
                      message="Startup: Do you want to clear old cache/login files?",
                      choices=['No (Keep my current login)', 'Yes (Clear cache - fixes 403 errors)'],
                      default='No (Keep my current login)'
                      ),
    ]
    answer = inquirer.prompt(questions)

    if answer and answer['clear_cache'].startswith('Yes'):
        print("🧹 Cleaning up files...")
        
        if os.path.exists(".cache"):
            try:
                os.remove(".cache")
                print("   -> Deleted .cache file")
            except Exception as e:
                print(f"   -> Error deleting .cache: {e}")
        
        if os.path.exists("__pycache__"):
            try:
                shutil.rmtree("__pycache__")
                print("   -> Deleted __pycache__ folder")
            except Exception as e:
                print(f"   -> Error deleting folder: {e}")
        
        print("✅ Cache cleared.\n")
    else:
        print("⏩ Skipping cache clear.\n")

    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

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
        print("👇  PASTE THE HEADERS BELOW AND PRESS ENTER, THEN `CTRL+D`:")
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
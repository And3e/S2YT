from migrator import MusicMigrator
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

    app = MusicMigrator(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    
    if not os.path.exists("ytmusic_headers.json"):
        print("Please run `python -c \"import ytmusicapi; ytmusicapi.setup('ytmusic_headers.json')\"` in terminal first to generate headers!")
        return
        
    app.login_to_youtube()

    to_migrate = app.select_spotify_playlists()
    
    if not to_migrate:
        print("No playlists selected. Exiting.")
        return

    app.migrate_playlists(to_migrate)

if __name__ == "__main__":
    main()
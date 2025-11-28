# S2YT - Spotify to YouTube Playlist Switcher

A Python tool to interactively migrate your playlists from Spotify to YouTube Music.

## Prerequisites

  * Python 3.x installed
  * Firefox Web Browser (for capturing headers)
  * A Spotify Account
  * A YouTube Music Account

## Installation

1.  Clone or download this repository.
2.  Install the required dependencies using the requirements file:

```bash
pip install -r requirements.txt
```

-----

## Configuration

### Part 1: Youtube configuration [only if needed (e.g. first time running)]

Follow the instruction in order to generate `ytmusic_headers.json`.

### Part 2: Spotify App Setup

You need a Client ID and Secret to access your Spotify Library.

1.  Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and log in.
2.  Click **Create App**.
3.  Fill in the details:
      * **App Name:** `S2YT`
      * **App Description:** `Spotify to YouTube Playlist switcher`
      * **Redirect URIs:**
        ```text
        http://127.0.0.1:8888/callback
        ```
        *(Note: Do not use localhost, use the IP 127.0.0.1)*
      * **Which API/SDKs are you planning to use?** Check **Web API**.
4.  Click **Save**.
5.  Click on **Settings** in your new app.
6.  Keep this tab open, you will need the **Client ID** and **Client Secret** for the next step.

### Part 3: Environment Variables

Instead of hardcoding your passwords, we will use a `.env` file.

1.  Create a new file in the project folder named `.env` (just `.env`, no name before the dot).
2.  Open it with a text editor and paste the following, replacing the values with your actual Spotify credentials:

```env
SPOTIFY_CLIENT_ID=<your_pasted_client_id_here>
SPOTIFY_CLIENT_SECRET=<your_pasted_client_secret_here>
```

-----

## Usage

1.  Run the main script:

```bash
python main.py
```

1.  **Spotify Login:** A browser window will open asking you to authorize the app. Click **Agree**.
      * *Note: If the page fails to load after agreeing, check the URL bar. If it contains `?code=...`, copy the entire URL and paste it back into the terminal.*
      * *Note*: Check if the page is opened on the correct browser (FIREFOX), if not copy the `URL` of the opened page and paste it on the right browser (account should correspond)
2.  **Select Playlists:** Use the **Arrow Keys** to navigate and **Spacebar** to select the playlists you want to migrate. Press **Enter** to confirm.
3.  The script will now search for songs on YouTube Music and create the playlists automatically.
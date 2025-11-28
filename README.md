# S2YT - Spotify to YouTube Playlist Switcher

A Python tool to interactively migrate your playlists from Spotify to YouTube Music.

## Prerequisites

- Python 3.x installed
- Firefox Web Browser (for capturing headers)
- A Spotify Account
- A YouTube Music Account

## Installation

1.  Clone or download this repository.
2.  Install the required dependencies using the requirements file:

```bash
pip install -r requirements.txt
```

---

## Configuration

### Part 1: Youtube configuration

Follow the on-screen instructions when running the script to generate `ytmusic_headers.json`.

### Part 2: Spotify App Setup

You need a Client ID and Secret to access your Spotify Library.

1.  Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and log in.
2.  Click **Create App**.
3.  Fill in the details:
    - **App Name:** `S2YT`
    - **App Description:** `Spotify to YouTube Playlist switcher`
    - **Redirect URIs:**
      ```text
      [http://127.0.0.1:8888/callback](http://127.0.0.1:8888/callback)
      ```
      _(Note: Do not use localhost, use the IP 127.0.0.1)_
    - **Which API/SDKs are you planning to use?** Check **Web API**.
4.  Click **Save**.
5.  Click on **Settings** in your new app.
6.  Keep this tab open, you will need the **Client ID** and **Client Secret** for the next step.
7.  **IMPORTANT:** Go to **User Management** in the dashboard settings and add your name/email to the list of allowed users, otherwise you will get a 403 error.

### Part 3: Environment Variables

1.  Create a new file in the project folder named `.env` (just `.env`, no name before the dot).
2.  Open it with a text editor and paste the following, replacing the values with your actual Spotify credentials:

<!-- end list -->

```env
SPOTIFY_CLIENT_ID=<your_pasted_client_id_here>
SPOTIFY_CLIENT_SECRET=<your_pasted_client_secret_here>
```

---

## Usage

1.  Run the main script:

<!-- end list -->

```bash
python main.py
```

2.  **Spotify Login:**

    - A browser window will open asking you to authorize the app. Click **Agree**.
    - _Note:_ If the page fails to load after agreeing, check the URL bar. If it contains `?code=...`, copy the entire URL and paste it back into the terminal.
    - _Note:_ Ensure the page is opened in the correct browser (e.g., Firefox) where you are logged into the correct account. If not, copy the URL and paste it manually into the correct browser.

3.  **Select Playlists:** Use the **Arrow Keys** to navigate and **Spacebar** to select the playlists you want to migrate. Press **Enter** to confirm.

4.  The script will now search for songs on YouTube Music and create the playlists automatically.

---

## Troubleshooting & Common Errors

### Spotify: "403 Forbidden" or "User not registered"

If you have added your email to the dashboard but still receive persistent `403` errors:

> **The Fix:** The quickest solution is to **create a brand new App** on the Spotify Developer Dashboard.
>
> 1.  Delete or ignore the old app.
> 2.  Create a new App with a new Client ID and Secret.
> 3.  **Immediately** add your email to "User Management" in the new app.
> 4.  Update your `.env` file with the new credentials.

### YouTube: "Expecting value: line 1 column 1" or "403 Forbidden"

If the script crashes while searching or creating playlists with this error, it means your YouTube session cookies have expired or been blocked by Google.

> **The Fix:**
>
> 1.  **Delete** the `ytmusic_headers.json` file in your project folder.
> 2.  Run the script again.
> 3.  When asked for headers, log in to YouTube Music and copy the fresh request headers. (use a **New Private/Incognito Window** in Firefox if needed)

# GitHub Pages - OAuth Redirect

This directory contains the GitHub Pages site for pyWeastCoastBot, primarily used for OAuth redirect callbacks.

## Files

- `index.html` - Main landing page for the GitHub Pages site
- `oauth-callback.html` - OAuth redirect callback page that displays the authorization code

## OAuth Callback Page

The `oauth-callback.html` page is designed to:
1. Extract the OAuth authorization code from the URL query parameter (`?code=...`)
2. Display the code in a user-friendly format
3. Provide a "Copy to Clipboard" button for easy copying
4. Show clear instructions for completing the OAuth flow in Discord

### Usage

When setting up the Google Health OAuth integration:
1. Enable the Google Health API in Google Cloud and create an OAuth client.
2. Add `https://ejnarvala.github.io/pyWeastCoastBot/oauth-callback.html` as an authorized redirect URI.
3. Configure the OAuth consent screen to allow `https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly`. While the app is in Testing, add each test account to the Test users list.
4. Users must link or migrate their Fitbit account in the Google Health app before authorizing.
5. Fitbot requests read-only activity and fitness access to show steps and active minutes in the server's Fitbot leaderboard.
6. Users can copy the authorization code from this page and paste it into Discord to complete registration.

## GitHub Pages Configuration

To enable GitHub Pages for this repository:
1. Go to repository Settings → Pages
2. Set Source to "Deploy from a branch"
3. Select the branch (e.g., `main`) and `/docs` folder
4. Save the configuration

The site will be available at: `https://ejnarvala.github.io/pyWeastCoastBot/`

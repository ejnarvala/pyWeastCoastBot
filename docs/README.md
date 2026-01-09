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

When setting up the Fitbit OAuth integration:
1. Configure the OAuth redirect URI to point to: `https://ejnarvala.github.io/pyWeastCoastBot/oauth-callback.html`
2. Users will be redirected here after authorizing the app
3. They can then copy the code and paste it into Discord to complete registration

## GitHub Pages Configuration

To enable GitHub Pages for this repository:
1. Go to repository Settings → Pages
2. Set Source to "Deploy from a branch"
3. Select the branch (e.g., `main`) and `/docs` folder
4. Save the configuration

The site will be available at: `https://ejnarvala.github.io/pyWeastCoastBot/`

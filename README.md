# EMEA Market Pulse
Standalone SOLMAX market-intelligence site for GitHub Pages.

## Upload
1. Create an empty GitHub repository with `main` as the default branch.
2. Upload every file and folder from this package to the repository root.
3. In **Settings > Pages**, choose **GitHub Actions** as the source.
4. Open **Actions > Weekly market data refresh > Run workflow** once to test collection.

## Automation
The refresh workflow is scheduled twice in UTC and contains a `Europe/Madrid` guard, so only the run corresponding to Monday 07:30 local time proceeds across CET/CEST changes. GitHub schedules can start later than the nominal minute.

## Data scope
The packaged collector refreshes the Harmonised Europe overall construction indicator from Eurostat. The seven verticals and Broader EMEA stay on the last validated dataset until their source-specific adapters are added. The UI identifies the refresh timestamp and source audit.

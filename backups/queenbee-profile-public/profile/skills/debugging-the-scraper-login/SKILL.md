---
name: debugging-the-scraper-login
summary: Steps to troubleshoot and debug scraper login issues with Okta MFA.
description: A skill for handling login issues related to the HiveMind scraper process, especially when MFA is involved.

---
# Skill: Debugging the Scraper Login

## Overview
This skill outlines the steps taken to debug the scraper when it fails to log into Okta, especially useful when dealing with MFA requirements.

## Steps
1. **Identify the Issue:** Check if the scraper is successfully connecting to the HiveMind server and verifies Okta login.
2. **Manual Intervention:** If automated login fails, manually log into Safari.
3. **Use MFA:** Complete any required multi-factor authentication (MFA) manually to establish a session.
4. **Reattempt Scraping:** Once logged in, rerun the scraping command to ensure it captures data correctly.

## Troubleshooting Tips
- Ensure Safari is open and functioning properly before rerunning the scraper.
- If timeouts occur, check for any issues with loading the Okta login page.
- Verify that the Okta login settings are correctly configured in the scraping script.

## Important Commands
- Open Safari: `open -a Safari`
- Run Scraper: `python3 tools/scrape-all.py`

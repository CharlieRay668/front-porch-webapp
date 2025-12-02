# Database Restoration Instructions

## Quick Start (Inside Docker Container)

1. Copy the HTML snapshot file into your container:
   ```bash
   # From your local machine, copy the HTML file to the running container:
   docker cp "Volunteer Signup-snapshot.html" frontporch:/app/
   
   # Copy the restoration script to the container:
   docker cp restore_database.py frontporch:/app/
   ```

2. Execute the restoration inside the container:
   ```bash
   # Enter the running container:
   docker exec -it frontporch bash
   
   # Run the restoration script:
   python restore_database.py
   ```

3. Restart your application to pick up the new database:
   ```bash
   # Exit the container and restart:
   exit
   docker restart frontporch
   ```

## Alternative: One-Command Restoration

If you prefer to do it all in one go:

```bash
# Copy files and run restoration in one command:
docker cp "Volunteer Signup-snapshot.html" frontporch:/app/ && \
docker cp restore_database.py frontporch:/app/ && \
docker exec frontporch python restore_database.py && \
docker restart frontporch
```

## What the Script Does

- ✅ **Parses** the HTML snapshot to extract all volunteer names and time slots
- ✅ **Clears** existing database data (if any)
- ✅ **Restores** all 234 volunteer signups found in the snapshot
- ✅ **Creates** the admin user (frontporchadmin/toomanymugs) if needed
- ✅ **Validates** the restoration with detailed statistics

## Verification

After restoration, you should see:
- **234 total signups** restored
- Signups distributed across Monday-Sunday (Saturday unavailable by design)
- Time slots from 7 AM to 10 PM populated
- Your volunteer signup app should show all the original data

## Troubleshooting

- **File not found**: Make sure the HTML snapshot file is copied to `/app/` in the container
- **Permission errors**: Run `chmod +x restore_database.py` if needed
- **Database locked**: Stop the FastAPI app before running restoration

## Files Created

- `volunteers.db` - Your restored SQLite database
- `restore_database.py` - The restoration script (can be deleted after use)
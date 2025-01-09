import os
import random
from atproto import Client
from dotenv import load_dotenv
import dropbox
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz

load_dotenv()

BLUESKY_USERNAME = os.getenv("BLUESKY_USERNAME")
BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

timezone = pytz.timezone('US/Central')
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)


client = Client("https://bsky.social")


def get_random_photo():
    """Fetch a random photo from Dropbox."""
    try:
       
        folder_path = "/Chicago Photos"  
        result = dbx.files_list_folder(folder_path)

  
        images = [
            entry.name for entry in result.entries
            if isinstance(entry, dropbox.files.FileMetadata) and entry.name.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

        if not images:
            raise Exception("No images found in the Dropbox folder!")

        # Pick a random image
        random_image = random.choice(images)
        file_path = f"{folder_path}/{random_image}"

        # Download the image to a local temp file
        _, res = dbx.files_download(file_path)
        local_path = f"./{random_image}"  # Save locally
        with open(local_path, "wb") as f:
            f.write(res.content)

        print(f"Fetched image: {random_image}")
        return local_path

    except dropbox.exceptions.ApiError as e:
        raise Exception(f"Dropbox API error: {e}")


def send_post():
    """Log in to Bluesky and post a random photo."""
    try:
        client.login(BLUESKY_USERNAME, BLUESKY_PASSWORD)

      
        photo_path = get_random_photo()

       
        with open(photo_path, "rb") as image_file:
            response = client.upload_blob(image_file)

      
        blob_ref = response.blob

    
        embed = {
            "$type": "app.bsky.embed.images",
            "images": [
                {
                    "image": blob_ref,  # Ensure this is the BlobRef object
                    "alt": "A scenic photo of Chicago."  # Provide a meaningful alt text
                }
            ]
        }

        # Post the photo
        client.post(text="", embed=embed)
        print(f"Posted successfully: {photo_path}")

        # Delete the local temp file
        os.remove(photo_path)

    except Exception as e:
        print(f"Error during posting: {e}")


if __name__ == "__main__":
  # Initialize scheduler
  scheduler = BlockingScheduler()

  # Schedule the send_post function to run at 8 PM daily
  scheduler.add_job(send_post, 'cron', hour=20, minute=12, timezone=timezone)

  print("Scheduled daily posts at 8:12 PM. Waiting for the next run...")
  try:
     
      scheduler.start()
  except (KeyboardInterrupt, SystemExit):
      print("Scheduler stopped.")
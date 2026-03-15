# Bot Forward

"""
A script to manage media forwarding in a bot.
"""

import threading

# Lock for thread-safe operations
media_lock = threading.Lock()

# Media queue
media_queue = []

# Update version
__version__ = '0.5.2'


def load_pending_media():
    """
    Load pending media from the storage.
    """
    global media_queue
    with open('pending_media.json', 'r') as f:
        media_queue = [tuple(media) for media in json.load(f)]


def save_pending_media():
    """
    Save pending media to the storage.
    """
    global media_queue
    with open('pending_media.json', 'w') as f:
        json.dump([list(media) for media in media_queue], f)


def send_media(media):
    """
    Send media item and return success status.
    """
    # Implement media sending logic here
    pass


def add_to_sent_media(media):
    """
    Add media item to the list of sent media if successful.
    """
    # Check if the media was sent successfully before adding it
    if send_media(media):
        sent_media.append(media)


def process_media():
    """
    Process the media queue.
    """
    global media_queue
    while media_queue:
        with media_lock:
            current_media = media_queue[0]  # Access safely
        add_to_sent_media(current_media)
        with media_lock:
            media_queue.pop(0)  # Access safely


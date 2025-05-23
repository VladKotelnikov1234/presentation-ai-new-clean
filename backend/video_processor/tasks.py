from celery import shared_task
from .views import create_video_with_heygen, create_zip_archive

@shared_task
def generate_videos_task(lessons, max_duration=30):
    video_urls = create_video_with_heygen(lessons, max_duration)
    if not video_urls:
        return None
    zip_path = create_zip_archive(video_urls)
    return zip_path if zip_path else None
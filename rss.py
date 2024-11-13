from datetime import datetime
from typing import Dict, List

import feedgenerator


def convert_to_rss(jobs: List[Dict]) -> str:
    """
    Converts job listings to RSS feed format
    """
    feed = feedgenerator.Rss201rev2Feed(
        title="Job Listings",
        link="http://example.com",
        description="Job listings from multiple sources",
        language="en"
    )
    
    for job in jobs:
        feed.add_item(
            title=job.get('title', 'No Title') + " - " + job.get('created_at', '') + " - " + job.get('updated_at', ''),
            link=job.get('url', ''),
            description=job.get('description', 'No Description'),
            author_name=job.get('company', 'Unknown Company'),
            pubdate=datetime.fromisoformat(job.get('created_at'))
        )
    
    return feed.writeString('utf-8')

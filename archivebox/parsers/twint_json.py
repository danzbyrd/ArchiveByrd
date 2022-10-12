__package__ = 'archivebox.parsers'

import json
import jsonlines

from typing import IO, Iterable
from datetime import datetime, timezone

from ..index.schema import Link
from ..util import (
    htmldecode,
    enforce_types,
)

@enforce_types
def parse_twint_json_export(json_file: IO[str], **_kwargs) -> Iterable[Link]:
    """Parse Twint export using JSON  output"""

    json_file.seek(0)
    json_date = lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M:%S %Z')
    reader = jsonlines.Reader(json_file)

    for data in reader.iter(type=dict, skip_invalid=True):
        # example line
        # {"href":"http:\/\/www.reddit.com\/r\/example","description":"title here","extended":"","meta":"18a973f09c9cc0608c116967b64e0419","hash":"910293f019c2f4bb1a749fb937ba58e3","time":"2014-06-14T15:51:42Z","shared":"no","toread":"no","tags":"reddit android"}]
        if data:
            url = data.get('href') or data.get('url') or data.get('URL') or data.get('link')
            if not url:
                raise Exception('Twint JSON must contain a URL in each entry [{"link": "http://....",.....},...]')

            # Parse the timestamp
            ts_str = str(datetime.now(timezone.utc).timestamp())
            if data.get('timestamp'):
                # chrome/ff histories use a very precise timestamp
                ts_str = str(data['timestamp'])  
            elif data.get('time'):
                ts_str = str(json_date(data['time'].split(',', 1)[0]).timestamp())
            elif data.get('created_at'):
                ts_str = str(json_date(data['created_at']).timestamp())
            elif data.get('created'):
                ts_str = str(json_date(data['created']).timestamp())
            elif data.get('date'):
                ts_str = str(json_date(data['date']).timestamp())
            elif data.get('bookmarked'):
                ts_str = str(json_date(data['bookmarked']).timestamp())
            elif data.get('saved'):
                ts_str = str(json_date(data['saved']).timestamp())
            
            # Parse the title
            title = None
            if data.get('title'):
                title = data['title'].strip()
            elif data.get('description'):
                title = data['description'].replace(' — Readability', '').strip()
            elif data.get('name'):
                title = data['name'].strip()

            yield Link(
                url=htmldecode(url),
                timestamp=ts_str,
                title=htmldecode(title) or None,
                tags=htmldecode(data.get('tags')) or '',
                sources=[json_file.name],
            )

KEY = 'twint_json'
NAME = 'Twint JSON'
PARSER = parse_twint_json_export

import feedparser, datetime, time, hashlib
from articles.models import Article, FeedPosition
from feeds.models import Feed, Publisher, NEWS_GENRES
import urllib, requests
from urllib.parse import urlparse
from django.core.cache import cache
from django.db import connection
from django.conf import settings

import requests, threading, html
from bs4 import BeautifulSoup


def article_get_full_text(**kwargs):
    request_url = f'{settings.FULL_TEXT_URL}extract.php?url={urllib.parse.quote(kwargs["link"], safe="")}'
    response = requests.get(request_url)
    if response.status_code == 200:
        data = response.json()
        if 'summary' not in kwargs or len(kwargs['summary']) < 20:
            kwargs['summary'] = data['excerpt']
        if 'author' not in kwargs or len(kwargs['author']) < 4:
            kwargs['author'] = data['author']
        if 'image_url' not in kwargs or len(kwargs['image_url']) < 4:
            kwargs['image_url'] = data['og_image']
        if 'full_text' not in kwargs or len(kwargs['full_text']) < 20:
            full_text = data['content']
            soup = BeautifulSoup(full_text, "html.parser")
            for img in soup.find_all('img'):
                img['style'] = 'max-width: 100%; max-height: 80vh;'
            for a in soup.find_all('a'):
                a['target'] = '_blank'
            kwargs['full_text'] = soup.prettify()
        if 'language' not in kwargs or len(kwargs['language']) < 20:
            kwargs['language'] = data['language']
    else:
        print(f'Full Text Fetch Error response {response.status_code}')
    return kwargs


def postpone(function):
    def decorator(*args, **kwargs):
        t = threading.Thread(target = function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator

@postpone
def update_feeds():

    cache.set('currentlyRefresing', True, 60*60)

    feeds = Feed.objects.filter(active=True)
    added_articles = 0
    for feed in feeds:
        added_articles += fetch_feed(feed)
    print(f'Added {added_articles} articles')

    if added_articles > 10:
        fetched_pictures = 0
        publishers = Publisher.objects.all()
        for publisher in publishers:
            fetched_pictures += fetch_pictures(publisher)
        print(f'Scraped websites for {fetched_pictures} additional images')

    cache.set('currentlyRefresing', False, 60 * 60)

    articles = Article.objects.all().exclude(main_genre='sport').exclude(min_article_relevance__isnull=True).order_by('min_article_relevance')[:64]
    cache.set('homepage', articles, 60 * 60 * 48)
    lastRefreshed = datetime.datetime.now()
    cache.set('lastRefreshed', lastRefreshed, 60 * 60 * 48)
    now = datetime.datetime.now()
    now_h = now.hour
    if now_h >= 6 and now_h < 19:
        refresh_time = 60 * 15
    else:
        refresh_time = 60 * 30
    cache.set('upToDate', True, refresh_time)

    connection.close()




def delete_feed_positions(feed):
    all_articles = Article.objects.filter(feed_position__feed=feed)
    all_articles.update(min_feed_position=None)
    all_articles.update(max_importance=None)
    all_articles.update(min_article_relevance=None)
    all_feedpositions = feed.feedposition_set.all()
    all_feedpositions.delete()
    print(f'Updating current artcile sorting for feed {feed.name}')


def fetch_feed(feed):
    hash_obj = hashlib.new('sha256')
    fetched_feed = feedparser.parse(feed.url)
    added_articles = 0

    news_categories = {
        i: j.upper().split(' / ') for i, j in NEWS_GENRES
    }

    if len(fetched_feed) > 0:
        delete_feed_positions(feed)

    for i, article in enumerate(fetched_feed.entries):
        article_kwargs = {}

        feed_position = i + 1
        article_kwargs['min_feed_position'] = feed_position
        importance = feed.importance
        if feed.feed_ordering == 'r':
            if feed_position <= 3:
                importance += 2
            elif feed_position <= 7:
                importance += 1
            importance = min(4, importance)
        article_kwargs['max_importance'] = importance
        article_kwargs['publisher'] = feed.publisher

        if hasattr(article, 'title'):
            article_kwargs['title'] = article.title
            if 'live news' in str(article_kwargs['title']).lower() or 'breaking' in str(article_kwargs['title']).lower():
                article_kwargs['max_importance'] = importance = 4
        if hasattr(article, 'summary'):
            article_kwargs['summary'] = html.unescape(article.summary)
        if hasattr(article, 'link'):
            article_kwargs['link'] = article.link
        if hasattr(article, 'id') and 'http' not in article.id and 'www' not in article.id:
            article_kwargs['guid'] = article.id
        else:
            hash_obj.update(str(article.link).encode())
            hash_str = hash_obj.hexdigest()
            article_kwargs['guid'] = f'{hash_str}'
        article_kwargs['hash'] = f'{feed.publisher.id}_' + article_kwargs['guid']
        if hasattr(article, 'published_parsed'):
            article_kwargs['pub_date'] = datetime.datetime.fromtimestamp(time.mktime(article.published_parsed))
        elif hasattr(fetched_feed, 'feed') and hasattr(fetched_feed.feed, 'updated_parsed'):
            article_kwargs['pub_date'] = datetime.datetime.fromtimestamp(time.mktime(fetched_feed.feed.updated_parsed))
        if hasattr(article, 'tags'):
            article_kwargs['categories'] = ', '.join([i['term'] for i in article.tags])
        if hasattr(article, 'author'):
            article_kwargs['author'] = article.author
        if feed.genre is None and 'categories' in article_kwargs:
            matching_tags = [k for k, v in news_categories.items() for i in article_kwargs['categories'].upper().split(', ') if any([z in i for z in v])]
            if len(matching_tags) > 0:
                article_kwargs['main_genre'] = matching_tags[0]
        elif feed.genre is not None:
            article_kwargs['main_genre'] = feed.genre

        if hasattr(article, 'image'):
            article_kwargs['image_url'] = 'included'
        else:
            if feed.full_text_fetch == 'Y':
                resp = requests.get(article.link)
                soup = BeautifulSoup(resp.content, 'html5lib')
                body = soup.find('body')
                images = body.find_all('img')
                new_images = []
                for i in images:
                    i_alt = ''
                    i_class = ''
                    i_src = ''
                    try:
                        i_src = str(i['src']).lower()
                        i_alt = str(i['alt']).lower()
                        i_class = str(i['class']).lower()
                    except:
                        pass
                    if len(i_src) > 3 and any([j in i_src for j in ['.avif', '.gif', '.jpg', '.jpeg', '.jfif', '.pjpeg', '.pjp', '.png', '.svg', '.webp']]) and 'logo' not in i_class  and 'logo' not in i_alt and 'author' not in i_class  and 'author' not in i_alt:
                        new_images.append(i)
                if len(new_images) > 0:
                    images = new_images
                    image = images[0]['src']
                    if 'www.' not in image and 'http' not in image:
                        url_parts = urlparse(article.link)
                        image = url_parts.scheme + '://' + url_parts.hostname + image
                    article_kwargs['image_url'] = image

        article_relevance = round(feed_position *
                             {3: 3 / 6, 2: 5 / 6, 1: 1, 0: 1, -1: 8 / 6, -2: 10 / 6, -3: 12 / 6}[article_kwargs['publisher'].renowned] *
                             {4: 1 / 6, 3: 2 / 6, 2: 4 / 6, 1: 1, 0: 8 / 6}[importance],
                             6)

        article_kwargs['min_article_relevance'] = article_relevance

        check_articles = Article.objects.filter(hash=article_kwargs['hash'])

        if len(check_articles) == 0:

            if settings.FULL_TEXT_URL is not None:
                article_kwargs = article_get_full_text(**article_kwargs)


            added_article = Article(**article_kwargs)
            added_article.save()
            added_articles += 1

        else:
            added_article = check_articles[0]

            for k, v in article_kwargs.items():
                value = getattr(added_article, k)
                if value is None and v is not None:
                    check_articles.update(**{f'{k}': v})
                elif 'min' in k and v < value:
                    check_articles.update(**{f'{k}': v})
                elif 'max' in k and v > value:
                    check_articles.update(**{f'{k}': v})



        added_feed_position = FeedPosition(
            feed = feed,
            position = feed_position,
            importance = importance,
            relevance = article_relevance,
            genre = added_article.main_genre if feed.genre is None else feed.genre
        )
        added_feed_position.save()

        added_article.feed_position.add(added_feed_position)
    return added_articles


def fetch_pictures(publisher):
    fetched_pictures = 0
    for link in publisher.img_scrape_urls.split('\n'):
        resp = requests.get(link)
        soup = BeautifulSoup(resp.content, 'html5lib')
        body = soup.find('body')
        images = body.find_all('img')
        for image in images:
            article_found = False
            item = image
            i = 0
            while article_found is False and i < 5 and item is not None:
                item = item.parent
                i += 1
                matched_article = None
                try:
                    href_value = item['href']
                    article_found = True
                    matched_article = publisher.article_set.filter(link__contains=href_value)
                except:
                    pass
                if matched_article is not None:
                    for article in matched_article:
                        if article.image_url is None:
                            url_img = None
                            try:
                                url_img = image['src']
                            except:
                                pass
                            if url_img is None:
                                try:
                                    url_img = image['data-src']
                                except:
                                    pass
                            try:
                                if 'logo' in str(image['alt']).lower() or 'author' in str(image['alt']).lower() or 'logo' in str(image['class']).lower() or 'author' in str(image['class']).lower():
                                    url_img = None
                            except:
                                pass
                            if url_img is not None and any([i in str(url_img).lower() for i in ['.avif', '.gif', '.jpg', '.jpeg', '.jfif', '.pjpeg', '.pjp', '.png', '.svg', '.webp']]):
                                url_parts = urlparse(link)
                                if 'www.' not in url_img and 'http' not in url_img:
                                    url_img = url_parts.scheme + '://' + url_parts.hostname + url_img
                                article.image_url = url_img
                                article.save()
                                fetched_pictures += 1
    return fetched_pictures



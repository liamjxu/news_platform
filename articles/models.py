from django.db import models
from feeds.models import Feed, Publisher

from feeds.models import NEWS_IMPORTANCE, NEWS_GENRES

# Create your models here.
class FeedPosition(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    position = models.SmallIntegerField()
    importance = models.SmallIntegerField(choices=NEWS_IMPORTANCE)
    relevance = models.SmallIntegerField(null=True)
    genre = models.CharField(choices=NEWS_GENRES, max_length=15, null=True)

    def __str__(self):
        return f'{self.feed} - {self.position}'


class Article(models.Model):
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    feed_position = models.ManyToManyField(FeedPosition)
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=500, null=True)
    full_text = models.TextField(null=True)
    author = models.CharField(max_length=50, null=True)
    link = models.URLField(null=True)
    pub_date = models.DateTimeField(null=True)
    guid = models.CharField(max_length=75, null=True)
    image_url = models.URLField(null=True)
    min_feed_position = models.SmallIntegerField(null=True)
    min_article_relevance = models.DecimalField(null=True, decimal_places=6, max_digits=12)
    max_importance = models.SmallIntegerField(choices=NEWS_IMPORTANCE, null=True)
    main_genre = models.CharField(choices=NEWS_GENRES, max_length=15, null=True)
    categories = models.CharField(max_length=250, null=True, blank=True)
    language = models.CharField(max_length=6, null=True, blank=True)
    hash = models.CharField(max_length=80)

    def __str__(self):
        return f'{self.title}'


class ArticleGroup(models.Model):
    feeds = models.ManyToManyField(Feed)
    articles = models.ManyToManyField(Article)
    title = models.CharField(max_length=30)
    summary = models.CharField(max_length=250, null=True)
    full_text = models.TextField(null=True)
    author = models.CharField(max_length=50, null=True)
    link = models.URLField(null=True)
    pub_date = models.DateTimeField(null=True)
    guid = models.CharField(max_length=75, null=True)
    image_url = models.TextField(null=True)
    min_feed_position = models.SmallIntegerField()
    min_article_relevance = models.DecimalField(null=True, decimal_places=6, max_digits=12)
    max_importance = models.SmallIntegerField(choices=NEWS_IMPORTANCE)
    main_genre = models.CharField(choices=NEWS_GENRES, max_length=15, null=True)
    categories = models.CharField(max_length=250, null=True)
    language = models.CharField(max_length=6, null=True)
    hash = models.CharField(max_length=80)

    def __str__(self):
        return f'{self.title}'

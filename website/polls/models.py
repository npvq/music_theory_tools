from django.db import models
from django.contrib import admin

import datetime
from django.utils import timezone

# Create your models here, nimda.

class Question(models.Model):

	question_text = models.CharField(max_length=200)
	pub_date = models.DateTimeField('date published')

	def __str__(self):
		return (lambda x : x[:25].strip()+"..." if len(x)>25 else x)(self.question_text)+" ["+(str(self.id) if self.id else "Null")+"]"

	@admin.display(
			boolean = True,
			ordering = pub_date,
			description = 'Published recently?',
		)
	def was_published_recently(self):
		now = timezone.now()
		return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Choice(models.Model):

	question = models.ForeignKey(Question, on_delete=models.CASCADE)
	choice_text = models.CharField(max_length=200)
	votes = models.IntegerField(default=0)

	def __str__(self):
		return (lambda x : x[:25].strip()+"..." if len(x)>25 else x)(self.choice_text)+" ["+(str(self.id) if self.id else "Null")+"]"
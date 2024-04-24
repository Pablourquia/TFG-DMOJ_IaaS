from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = ['Questionnaire', 'Question']

class Questionnaire(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, verbose_name=_('name'))

    def __str__(self):
        return self.name


class Question(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, verbose_name=_('name'))
    file = models.FileField(upload_to='question_files/', verbose_name=_('file'))
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questions', verbose_name=_('questionnaire'))
    type_question = models.CharField(max_length=100, verbose_name=_('type'))
    options = models.JSONField(verbose_name=_('options'))
    entries_quantity = models.IntegerField(verbose_name=_('entries quantity'))

    def __str__(self):
        return self.name

class CorrectAnswers(models.Model):
    id = models.AutoField(primary_key=True)
    question_id = models.IntegerField(verbose_name=_('question id'))
    answer = models.JSONField(verbose_name=_('answer'))

    def __str__(self):
        return self.answer

class SubmissionAnswers(models.Model):
    id = models.AutoField(primary_key=True)
    name_user = models.CharField(max_length=100, verbose_name=_('name user'))
    name_question = models.CharField(max_length=100, verbose_name=_('name question'))
    question_id = models.IntegerField(verbose_name=_('question id'))
    user_id = models.IntegerField(verbose_name=_('user id'))
    answer = models.JSONField(verbose_name=_('answer'))
    correct = models.BooleanField(verbose_name=_('correct'))
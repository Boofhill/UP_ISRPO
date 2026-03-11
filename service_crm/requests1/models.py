from django.db import models
from accounts.models import Client, Master


class Request(models.Model):
    request_id = models.AutoField(primary_key=True)
    start_date = models.DateTimeField(verbose_name="Дата начала")
    home_tech_type = models.CharField(max_length=100, verbose_name="Тип техники")
    home_tech_model = models.CharField(max_length=100, verbose_name="Модель техники")
    problem_description = models.TextField(verbose_name="Описание проблемы")
    request_status = models.BooleanField(default=False, verbose_name="Статус (выполнено/нет)")
    completion_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")
    repair_parts = models.TextField(blank=True, verbose_name="Запчасти")
    master = models.ForeignKey(Master, on_delete=models.SET_NULL, null=True, db_column='masterID',
                               verbose_name="Мастер")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, db_column='clientID', verbose_name="Клиент")

    def __str__(self):
        return f"Заявка #{self.request_id} - {self.home_tech_type} {self.home_tech_model}"

    class Meta:
        db_table = 'requests'
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'


class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    message = models.TextField(verbose_name="Сообщение")
    request = models.ForeignKey(Request, on_delete=models.CASCADE, db_column='requestID', verbose_name="Заявка")
    master = models.ForeignKey(Master, on_delete=models.CASCADE, db_column='masterID', verbose_name="Мастер")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Комментарий #{self.comment_id} к заявке #{self.request_id}"

    class Meta:
        db_table = 'comments'
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
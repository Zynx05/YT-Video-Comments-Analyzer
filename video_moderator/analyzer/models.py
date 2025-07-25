from django.db import models

class AnalysisResult(models.Model):
    comment = models.TextField()
    sentiment = models.CharField(max_length=10)
    explanation = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sentiment} - {self.comment[:50]}"

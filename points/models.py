# points/models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Team(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)

    def __str__(self):
        return self.name

class MatchResult(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    wins = models.PositiveIntegerField(default=0)
    matches = models.PositiveIntegerField(default=0)
    fp = models.PositiveIntegerField(default=0)
    pp = models.PositiveIntegerField(default=0)

    def tp(self):
        return self.fp + self.pp

    def __str__(self):
        return f"Match Result for {self.team.name}"

class Points(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    wins = models.PositiveIntegerField(default=0)
    matches = models.PositiveIntegerField(default=0)
    fp = models.PositiveIntegerField(default=0)
    pp = models.PositiveIntegerField(default=0)
    tp = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Points for {self.team.name}"

@receiver(post_save, sender=MatchResult)
def update_points(sender, instance, **kwargs):
    # Update Points model whenever a MatchResult is added or updated
    points, created = Points.objects.get_or_create(team=instance.team)
    match_results = MatchResult.objects.filter(team=instance.team)
    wins = match_results.filter(wins=True).count()
    points.wins = wins
    points.matches = match_results.count()
    points.fp = match_results.aggregate(fp_sum=models.Sum('fp'))['fp_sum'] or 0
    points.pp = match_results.aggregate(pp_sum=models.Sum('pp'))['pp_sum'] or 0
    points.tp = points.fp + points.pp
    points.save()

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Training

@receiver(pre_save, sender=Training)
def check_training_time_change(sender, instance, **kwargs):
    try:
        if instance.pk:
            old_instance = Training.objects.get(pk=instance.pk)
            
            date_changed = old_instance.date != instance.date
            time_changed = old_instance.time != instance.time
            duration_changed = old_instance.duration_hours != instance.duration_hours
            
            if date_changed or time_changed or duration_changed:
                instance._old_date = old_instance.date
                instance._old_time = old_instance.time
                instance._old_duration = old_instance.duration_hours
    
    except Training.DoesNotExist:
        pass

@receiver(post_save, sender=Training)
def handle_training_time_change(sender, instance, created, **kwargs):
    if created:
        return
    
    if hasattr(instance, '_old_date') and hasattr(instance, '_old_time'):
        old_date = getattr(instance, '_old_date', None)
        old_time = getattr(instance, '_old_time', None)
        old_duration = getattr(instance, '_old_duration', None)
        
        current_time = timezone.now()
        new_end_time = datetime.combine(
            instance.date, 
            instance.time
        ).replace(tzinfo=current_time.tzinfo) + timedelta(hours=instance.duration_hours)
        
        if current_time > new_end_time:
            print(f"Training {instance.id} time changed to past, checking attendance...")
            
            marked_count, message = instance.mark_absent_for_unchecked_users()
            
            print(f"Marked {marked_count} users as absent for training {instance.title}")
            
            if hasattr(instance, '_old_date'):
                del instance._old_date
            if hasattr(instance, '_old_time'):
                del instance._old_time
            if hasattr(instance, '_old_duration'):
                del instance._old_duration
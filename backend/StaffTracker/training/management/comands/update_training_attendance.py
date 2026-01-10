from django.core.management.base import BaseCommand
from django.utils import timezone
from training.models import Training
from datetime import datetime, timedelta
import sys

class Command(BaseCommand):
    help = 'Update attendance records for trainings with changed times'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--training-id',
            type=int,
            help='Specific training ID to process'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force processing even if training is not in the past'
        )
    
    def handle(self, *args, **options):
        training_id = options.get('training_id')
        force = options.get('force', False)
        
        if training_id:
            trainings = Training.objects.filter(id=training_id)
        else:
            trainings = Training.objects.all()
        
        current_time = timezone.now()
        processed_count = 0
        total_marked = 0
        
        self.stdout.write("Checking trainings for attendance updates...")
        
        for training in trainings:
            training_end_time = datetime.combine(
                training.date, 
                training.time
            ).replace(tzinfo=current_time.tzinfo) + timedelta(hours=training.duration_hours)
            
            if current_time > training_end_time or force:
                self.stdout.write(f"\nProcessing training: {training.title} (ID: {training.id})")
                self.stdout.write(f"  Date: {training.date}, Time: {training.time}")
                self.stdout.write(f"  Duration: {training.duration_hours}h")
                self.stdout.write(f"  End time: {training_end_time}")
                
                missing_attendance = training.get_registered_users_without_attendance()
                
                if missing_attendance:
                    self.stdout.write(f"  Found {len(missing_attendance)} users without attendance records")
                    
                    marked_count, message = training.mark_absent_for_unchecked_users()
                    
                    if marked_count > 0:
                        processed_count += 1
                        total_marked += marked_count
                        self.stdout.write(f"  ✓ Marked {marked_count} users as absent")
                        self.stdout.write(f"  Message: {message}")
                    else:
                        self.stdout.write(f"  {message}")
                else:
                    self.stdout.write("  ✓ All registered users have attendance records")
        
        self.stdout.write("\n" + "="*50)
        
        if total_marked > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Successfully marked {total_marked} users as absent from {processed_count} training(s)"
                )
            )
        else:
            self.stdout.write("ℹ️ No users needed to be marked as absent")
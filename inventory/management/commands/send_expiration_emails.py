"""
Management command to send expiration email alerts.
Sends emails starting 2 days before expiration date.
Run this command daily via cron or scheduled task.
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from inventory.models import InventoryItem, ExpirationEmailNotification
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Send email alerts for items expiring within 2 days and for expired items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=2,
            help='Number of days before expiration to send alerts (default: 2)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )

    def handle(self, *args, **options):
        days_before = options['days']
        dry_run = options['dry_run']
        
        today = timezone.now().date()
        target_date = today + timedelta(days=days_before)
        
        # Get items expiring on target_date (2 days from now)
        expiring_items = InventoryItem.objects.filter(
            expiration_date=target_date,
            status__in=['fresh', 'expiring_soon'],  # Only active items
        ).exclude(
            status='consumed'
        ).select_related('user', 'user__profile')
        
        if not expiring_items.exists():
            self.stdout.write(
                self.style.SUCCESS(f'No items expiring in {days_before} days.')
            )
            return
        
        # Group items by user
        items_by_user = {}
        for item in expiring_items:
            user = item.user
            if user not in items_by_user:
                items_by_user[user] = []
            
            # Check if we've already sent an email for this item at this days_before
            notification_exists = ExpirationEmailNotification.objects.filter(
                inventory_item=item,
                days_before_expiry=days_before
            ).exists()
            
            if not notification_exists:
                items_by_user[user].append(item)
        
        if not items_by_user:
            self.stdout.write(
                self.style.WARNING('All expiration emails have already been sent.')
            )
            return
        
        # Send emails
        emails_sent = 0
        emails_failed = 0
        
        for user, items in items_by_user.items():
            if not items:
                continue
            
            # Calculate days until expiry for each item
            items_with_days = []
            for item in items:
                days_until = (item.expiration_date - today).days
                items_with_days.append({
                    'item': item,
                    'days_until_expiry': days_until,
                })
            
            # Sort by urgency (expiring soonest first)
            items_with_days.sort(key=lambda x: x['days_until_expiry'])
            
            # Prepare email context
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            if not site_url.startswith('http'):
                site_url = f'http://{site_url}'
            
            # Prepare items with days_until_expiry for template
            items_for_template = []
            for item_data in items_with_days:
                item = item_data['item']
                item.days_until_expiry = item_data['days_until_expiry']
                items_for_template.append(item)
            
            context = {
                'user': user,
                'items': items_for_template,
                'site_url': site_url,
            }
            
            # Render email templates
            subject = f'⚠️ Food Expiration Alert: {len(items)} Item{"s" if len(items) > 1 else ""} Expiring Soon'
            
            html_message = render_to_string('emails/expiration_alert.html', context)
            plain_message = render_to_string('emails/expiration_alert.txt', context)
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'\n[DRY RUN] Would send email to {user.email}')
                )
                self.stdout.write(f'  Subject: {subject}')
                self.stdout.write(f'  Items: {len(items)}')
                for item_data in items_with_days:
                    item = item_data['item']
                    days = item_data['days_until_expiry']
                    self.stdout.write(
                        f'    - {item.item_name} (expires in {days} day{"s" if days != 1 else ""})'
                    )
                continue
            
            try:
                # Send email
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodmanagement.com'),
                    to=[user.email],
                )
                email.attach_alternative(html_message, "text/html")
                email.send()
                
                # Record notification
                for item_data in items_with_days:
                    item = item_data['item']
                    ExpirationEmailNotification.objects.create(
                        inventory_item=item,
                        user=user,
                        days_before_expiry=days_before,
                        email_sent=True
                    )
                
                emails_sent += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Email sent to {user.email} ({len(items)} items)')
                )
                
            except Exception as e:
                emails_failed += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send email to {user.email}: {str(e)}')
                )
        
        # Summary
        if not dry_run:
            self.stdout.write('\n' + '='*50)
            self.stdout.write(
                self.style.SUCCESS(f'Summary: {emails_sent} email(s) sent, {emails_failed} failed')
            )
            
            # Also check for items expiring today or tomorrow (send reminder)
            self.stdout.write('\nChecking for items expiring today or tomorrow...')
            self._send_urgent_reminders(today, dry_run)
            
            # Check for expired items and send notifications
            self.stdout.write('\nChecking for expired items...')
            self._send_expired_notifications(today, dry_run)
    
    def _send_urgent_reminders(self, today, dry_run):
        """Send urgent reminders for items expiring today or tomorrow."""
        tomorrow = today + timedelta(days=1)
        
        urgent_items = InventoryItem.objects.filter(
            expiration_date__in=[today, tomorrow],
            status__in=['fresh', 'expiring_soon'],
        ).exclude(
            status='consumed'
        ).select_related('user', 'user__profile')
        
        if not urgent_items.exists():
            return
        
        # Group by user
        items_by_user = {}
        for item in urgent_items:
            user = item.user
            if user not in items_by_user:
                items_by_user[user] = []
            
            # Check if we've sent a reminder today
            days_until = (item.expiration_date - today).days
            notification_exists = ExpirationEmailNotification.objects.filter(
                inventory_item=item,
                days_before_expiry=days_until,
                sent_date=today
            ).exists()
            
            if not notification_exists:
                items_by_user[user].append(item)
        
        for user, items in items_by_user.items():
            if not items:
                continue
            
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            if not site_url.startswith('http'):
                site_url = f'http://{site_url}'
            
            # Add days_until_expiry to items
            items_for_template = []
            for item in items:
                days_until = (item.expiration_date - today).days
                item.days_until_expiry = days_until
                items_for_template.append(item)
            
            context = {
                'user': user,
                'items': items_for_template,
                'site_url': site_url,
            }
            
            # Determine urgency
            today_count = sum(1 for item in items_for_template if item.expiration_date == today)
            if today_count > 0:
                subject = f'🚨 URGENT: {today_count} Item{"s" if today_count > 1 else ""} Expiring TODAY!'
            else:
                subject = f'⚠️ Reminder: {len(items)} Item{"s" if len(items) > 1 else ""} Expiring Tomorrow'
            
            html_message = render_to_string('emails/expiration_alert.html', context)
            plain_message = render_to_string('emails/expiration_alert.txt', context)
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'\n[DRY RUN] Would send urgent reminder to {user.email}')
                )
                self.stdout.write(f'  Subject: {subject}')
                continue
            
            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodmanagement.com'),
                    to=[user.email],
                )
                email.attach_alternative(html_message, "text/html")
                email.send()
                
                # Record notifications
                for item in items:
                    days_until = (item.expiration_date - today).days
                    ExpirationEmailNotification.objects.create(
                        inventory_item=item,
                        user=user,
                        days_before_expiry=days_until,
                        email_sent=True
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Urgent reminder sent to {user.email}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send urgent reminder to {user.email}: {str(e)}')
                )
    
    def _send_expired_notifications(self, today, dry_run):
        """Send notifications for items that have expired."""
        # Get items that have expired (expiration_date < today)
        # Include both items that haven't been updated yet AND items already marked as expired
        expired_items = InventoryItem.objects.filter(
            expiration_date__lt=today,
        ).exclude(
            status='consumed'
        ).select_related('user', 'user__profile')
        
        if not expired_items.exists():
            self.stdout.write(
                self.style.SUCCESS('No expired items found.')
            )
            return
        
        # Update status to expired for items that haven't been updated yet
        for item in expired_items:
            if item.status != 'expired':
                item.update_status()  # This will set status to 'expired'
        
        # Group by user
        items_by_user = {}
        for item in expired_items:
            user = item.user
            if user not in items_by_user:
                items_by_user[user] = []
            
            # Check if we've already sent an email for this expired item
            # Use days_before_expiry = -1 to indicate expired items
            # Check if we've sent an email in the last 7 days to avoid spam
            seven_days_ago = today - timedelta(days=7)
            notification_exists = ExpirationEmailNotification.objects.filter(
                inventory_item=item,
                days_before_expiry=-1,  # -1 indicates expired
                sent_date__gte=seven_days_ago  # Sent in last 7 days
            ).exists()
            
            if not notification_exists:
                items_by_user[user].append(item)
        
        if not items_by_user:
            self.stdout.write(
                self.style.WARNING('All expired item emails have already been sent today.')
            )
            return
        
        emails_sent = 0
        emails_failed = 0
        
        for user, items in items_by_user.items():
            if not items:
                continue
            
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            if not site_url.startswith('http'):
                site_url = f'http://{site_url}'
            
            # Calculate days expired for each item
            items_for_template = []
            for item in items:
                days_expired = (today - item.expiration_date).days
                item.days_until_expiry = -days_expired  # Negative indicates expired
                item.days_expired = days_expired
                items_for_template.append(item)
            
            context = {
                'user': user,
                'items': items_for_template,
                'site_url': site_url,
                'is_expired': True,  # Flag to indicate these are expired items
            }
            
            # Determine subject based on urgency
            if len(items) == 1:
                subject = f'🚨 URGENT: {items[0].item_name} Has Expired!'
            else:
                subject = f'🚨 URGENT: {len(items)} Items Have Expired!'
            
            html_message = render_to_string('emails/expiration_alert.html', context)
            plain_message = render_to_string('emails/expiration_alert.txt', context)
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'\n[DRY RUN] Would send expired item notification to {user.email}')
                )
                self.stdout.write(f'  Subject: {subject}')
                self.stdout.write(f'  Items: {len(items)}')
                for item in items_for_template:
                    self.stdout.write(
                        f'    - {item.item_name} (expired {item.days_expired} day{"s" if item.days_expired != 1 else ""} ago)'
                    )
                continue
            
            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodmanagement.com'),
                    to=[user.email],
                )
                email.attach_alternative(html_message, "text/html")
                email.send()
                
                # Record notifications (use -1 to indicate expired items)
                for item in items:
                    ExpirationEmailNotification.objects.create(
                        inventory_item=item,
                        user=user,
                        days_before_expiry=-1,  # -1 indicates expired
                        email_sent=True
                    )
                
                emails_sent += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Expired item notification sent to {user.email} ({len(items)} items)')
                )
            except Exception as e:
                emails_failed += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send expired notification to {user.email}: {str(e)}')
                )
        
        if not dry_run and (emails_sent > 0 or emails_failed > 0):
            self.stdout.write(
                self.style.SUCCESS(f'Expired items: {emails_sent} email(s) sent, {emails_failed} failed')
            )


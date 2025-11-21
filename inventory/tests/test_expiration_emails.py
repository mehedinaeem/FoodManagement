"""
Tests for expiration email notifications.
"""

from django.test import TestCase
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from inventory.models import InventoryItem, ExpirationEmailNotification
from accounts.models import UserProfile


class ExpirationEmailTests(TestCase):
    """Test expiration email functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            household_size=2
        )
        
        # Create expired item
        self.expired_item = InventoryItem.objects.create(
            user=self.user,
            item_name='Expired Milk',
            quantity=1.0,
            unit='l',
            category='dairy',
            purchase_date=timezone.now().date() - timedelta(days=10),
            expiration_date=timezone.now().date() - timedelta(days=2),  # Expired 2 days ago
            status='expiring_soon'
        )
        
        # Create item expiring in 2 days
        self.expiring_item = InventoryItem.objects.create(
            user=self.user,
            item_name='Expiring Bread',
            quantity=1.0,
            unit='piece',
            category='grain',
            purchase_date=timezone.now().date() - timedelta(days=5),
            expiration_date=timezone.now().date() + timedelta(days=2),
            status='fresh'
        )
    
    def test_expired_item_email_sent(self):
        """Test that emails are sent for expired items."""
        from django.core.management import call_command
        from io import StringIO
        
        # Clear mail outbox
        mail.outbox.clear()
        
        # Run command
        out = StringIO()
        call_command('send_expiration_emails', stdout=out)
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('expired', mail.outbox[0].subject.lower())
        
        # Check notification was recorded
        notification = ExpirationEmailNotification.objects.filter(
            inventory_item=self.expired_item,
            days_before_expiry=-1
        ).first()
        self.assertIsNotNone(notification)
        self.assertTrue(notification.email_sent)
    
    def test_expired_item_status_updated(self):
        """Test that expired item status is updated."""
        from django.core.management import call_command
        
        # Item should be expiring_soon initially
        self.assertEqual(self.expired_item.status, 'expiring_soon')
        
        # Run command
        call_command('send_expiration_emails')
        
        # Refresh from database
        self.expired_item.refresh_from_db()
        
        # Status should be updated to expired
        self.assertEqual(self.expired_item.status, 'expired')
    
    def test_no_duplicate_emails(self):
        """Test that duplicate emails are not sent."""
        from django.core.management import call_command
        
        # Create notification record
        ExpirationEmailNotification.objects.create(
            inventory_item=self.expired_item,
            user=self.user,
            days_before_expiry=-1,
            email_sent=True
        )
        
        # Clear mail outbox
        mail.outbox.clear()
        
        # Run command again
        call_command('send_expiration_emails')
        
        # No new email should be sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_expiring_item_email_sent(self):
        """Test that emails are sent for items expiring in 2 days."""
        from django.core.management import call_command
        
        # Clear mail outbox
        mail.outbox.clear()
        
        # Run command
        call_command('send_expiration_emails')
        
        # Should send email for expiring item
        self.assertGreater(len(mail.outbox), 0)
        
        # Check notification was recorded
        notification = ExpirationEmailNotification.objects.filter(
            inventory_item=self.expiring_item,
            days_before_expiry=2
        ).first()
        self.assertIsNotNone(notification)


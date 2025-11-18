"""
Signals for automatic loyalty rewards management
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import (
    Order, GiftBoxOrder, Customer, LoyaltyCard, LoyaltyReward,
    CustomerAchievement, Achievement
)


@receiver(post_save, sender=Customer)
def create_loyalty_card(sender, instance, created, **kwargs):
    """Automatically create a loyalty card when a new customer is created"""
    if created:
        LoyaltyCard.objects.get_or_create(customer=instance)


@receiver(post_save, sender=Order)
def process_order_loyalty(sender, instance, created, **kwargs):
    """Process loyalty rewards when an order is completed"""
    if instance.status == 'completed':
        # Get or create loyalty card
        loyalty_card, _ = LoyaltyCard.objects.get_or_create(customer=instance.customer)
        
        # Update statistics
        loyalty_card.total_orders += 1
        loyalty_card.total_spent += instance.total_price
        
        # Add stamp
        reward_earned = loyalty_card.add_stamp()
        
        # Add points (5 points per ₹100 spent)
        points_to_add = int(instance.total_price / 100) * 5
        loyalty_card.add_points(points_to_add, f'Order #{instance.order_number}')
        
        loyalty_card.save()
        
        # If reward earned, create the reward voucher
        if reward_earned:
            discount_percentage = loyalty_card.tier_benefits['discount']
            expiry_date = timezone.now().date() + timedelta(days=60)
            
            LoyaltyReward.objects.create(
                loyalty_card=loyalty_card,
                reward_type='stamp_card',
                discount_percentage=discount_percentage,
                expiry_date=expiry_date,
                description=f'{discount_percentage}% discount for completing {loyalty_card.stamps_to_reward} orders!'
            )
        
        # Check for achievements
        check_achievements(loyalty_card)


@receiver(post_save, sender=GiftBoxOrder)
def process_gift_box_order_loyalty(sender, instance, created, **kwargs):
    """Process loyalty rewards for gift box orders"""
    if instance.status == 'completed':
        # Get or create loyalty card
        loyalty_card, _ = LoyaltyCard.objects.get_or_create(customer=instance.customer)
        
        # Update statistics
        loyalty_card.total_orders += 1
        loyalty_card.total_spent += instance.total_price
        
        # Add stamp
        reward_earned = loyalty_card.add_stamp()
        
        # Add points (5 points per ₹100 spent)
        points_to_add = int(instance.total_price / 100) * 5
        loyalty_card.add_points(points_to_add, f'Gift Box Order #{instance.order_number}')
        
        loyalty_card.save()
        
        # If reward earned, create the reward voucher
        if reward_earned:
            discount_percentage = loyalty_card.tier_benefits['discount']
            expiry_date = timezone.now().date() + timedelta(days=60)
            
            LoyaltyReward.objects.create(
                loyalty_card=loyalty_card,
                reward_type='stamp_card',
                discount_percentage=discount_percentage,
                expiry_date=expiry_date,
                description=f'{discount_percentage}% discount for completing {loyalty_card.stamps_to_reward} orders!'
            )
        
        # Check for achievements
        check_achievements(loyalty_card)


def check_achievements(loyalty_card):
    """Check and unlock achievements for the customer"""
    achievements = Achievement.objects.filter(is_active=True)
    
    for achievement in achievements:
        # Check if already unlocked
        if CustomerAchievement.objects.filter(
            loyalty_card=loyalty_card, 
            achievement=achievement
        ).exists():
            continue
        
        # Check criteria
        unlocked = False
        if achievement.criteria_type == 'orders':
            if loyalty_card.total_orders >= achievement.criteria_value:
                unlocked = True
        elif achievement.criteria_type == 'spent':
            if loyalty_card.total_spent >= Decimal(achievement.criteria_value):
                unlocked = True
        elif achievement.criteria_type == 'referrals':
            if loyalty_card.referrals_made >= achievement.criteria_value:
                unlocked = True
        elif achievement.criteria_type == 'stamps':
            if loyalty_card.total_stamps >= achievement.criteria_value:
                unlocked = True
        
        # Unlock achievement
        if unlocked:
            CustomerAchievement.objects.create(
                loyalty_card=loyalty_card,
                achievement=achievement
            )
            # Award points
            if achievement.points_reward > 0:
                loyalty_card.add_points(
                    achievement.points_reward,
                    f'Achievement unlocked: {achievement.name}'
                )


def check_birthday_rewards():
    """
    Check for customer birthdays and issue birthday rewards
    This should be run as a daily cron job or scheduled task
    """
    from django.utils import timezone
    today = timezone.now().date()
    
    # Find customers with birthdays today
    customers = Customer.objects.filter(
        date_of_birth__month=today.month,
        date_of_birth__day=today.day
    )
    
    for customer in customers:
        if hasattr(customer, 'loyalty_card'):
            loyalty_card = customer.loyalty_card
            
            # Check if birthday reward already issued this year
            existing_reward = LoyaltyReward.objects.filter(
                loyalty_card=loyalty_card,
                reward_type='birthday',
                issued_date__year=today.year
            ).exists()
            
            if not existing_reward:
                # Create birthday reward
                birthday_bonus = loyalty_card.tier_benefits['birthday_bonus']
                expiry_date = today + timedelta(days=30)
                
                LoyaltyReward.objects.create(
                    loyalty_card=loyalty_card,
                    reward_type='birthday',
                    discount_percentage=5,
                    discount_amount=0,
                    expiry_date=expiry_date,
                    description=f'🎂 Happy Birthday! Special {birthday_bonus} points bonus'
                )
                
                # Add birthday bonus points
                loyalty_card.add_points(birthday_bonus, '🎂 Birthday bonus!')


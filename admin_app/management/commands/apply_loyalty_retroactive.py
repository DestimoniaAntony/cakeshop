"""
Management command to retroactively apply loyalty rewards to existing completed orders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from admin_app.models import (
    Order, GiftBoxOrder, Customer, LoyaltyCard, LoyaltyReward,
    CustomerAchievement, Achievement
)


class Command(BaseCommand):
    help = 'Retroactively apply loyalty rewards to existing completed orders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customer-id',
            type=int,
            help='Process only specific customer by ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        customer_id = options.get('customer_id')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get customers with completed orders
        if customer_id:
            customers = Customer.objects.filter(id=customer_id)
        else:
            customers = Customer.objects.all()
        
        total_customers = 0
        total_orders = 0
        total_points = 0
        total_stamps = 0
        total_rewards = 0
        
        for customer in customers:
            # Get or create loyalty card
            loyalty_card, created = LoyaltyCard.objects.get_or_create(customer=customer)
            
            if created and not dry_run:
                self.stdout.write(f'  Created loyalty card for {customer.name}')
            
            # Get all completed orders for this customer
            regular_orders = Order.objects.filter(
                customer=customer,
                status='completed'
            ).order_by('created_at')
            
            gift_box_orders = GiftBoxOrder.objects.filter(
                customer=customer,
                status='completed'
            ).order_by('created_at')
            
            # Combine and sort by created_at
            all_orders = list(regular_orders) + list(gift_box_orders)
            all_orders.sort(key=lambda x: x.created_at)
            
            if not all_orders:
                continue
            
            self.stdout.write(self.style.SUCCESS(f'\nProcessing {customer.name} ({len(all_orders)} orders)'))
            total_customers += 1
            
            # Reset loyalty card stats to recalculate
            if not dry_run:
                loyalty_card.current_stamps = 0
                loyalty_card.total_stamps = 0
                loyalty_card.total_orders = 0
                loyalty_card.total_spent = Decimal('0.00')
                loyalty_card.points_balance = 0
                loyalty_card.lifetime_points = 0
                loyalty_card.rewards_claimed = 0
            
            customer_points = 0
            customer_stamps = 0
            customer_spent = Decimal('0.00')
            
            for order in all_orders:
                total_orders += 1
                
                # Calculate points (10 points per ₹100)
                order_points = int(order.total_price / 100) * 10
                
                # Apply tier multiplier (recalculated based on current order count)
                if loyalty_card.total_orders >= 50:
                    multiplier = 2.5
                elif loyalty_card.total_orders >= 25:
                    multiplier = 2.0
                elif loyalty_card.total_orders >= 10:
                    multiplier = 1.5
                else:
                    multiplier = 1.0
                
                bonus_points = int(order_points * multiplier)
                
                self.stdout.write(f'  Order #{order.order_number}: ₹{order.total_price} → +{bonus_points} pts, +1 stamp')
                
                if not dry_run:
                    # Update card
                    loyalty_card.total_orders += 1
                    loyalty_card.total_spent += order.total_price
                    loyalty_card.current_stamps += 1
                    loyalty_card.total_stamps += 1
                    
                    # Add points
                    loyalty_card.points_balance += bonus_points
                    loyalty_card.lifetime_points += bonus_points
                    
                    # Log transaction
                    from admin_app.models import PointsTransaction
                    PointsTransaction.objects.create(
                        loyalty_card=loyalty_card,
                        points=bonus_points,
                        transaction_type='earned',
                        reason=f'Retroactive: Order #{order.order_number}',
                        order=order if isinstance(order, Order) else None
                    )
                    
                    # Check for reward (every 5 stamps)
                    if loyalty_card.current_stamps >= loyalty_card.stamps_to_reward:
                        loyalty_card.current_stamps = 0
                        loyalty_card.rewards_claimed += 1
                        
                        # Create reward voucher
                        discount_percentage = loyalty_card.tier_benefits['discount']
                        expiry_date = timezone.now().date() + timedelta(days=60)
                        
                        LoyaltyReward.objects.create(
                            loyalty_card=loyalty_card,
                            reward_type='stamp_card',
                            discount_percentage=discount_percentage,
                            expiry_date=expiry_date,
                            description=f'{discount_percentage}% discount for completing {loyalty_card.stamps_to_reward} orders!'
                        )
                        
                        total_rewards += 1
                        self.stdout.write(self.style.SUCCESS(f'    ** REWARD EARNED! {discount_percentage}% discount voucher'))
                
                customer_points += bonus_points
                customer_stamps += 1
                customer_spent += order.total_price
                total_points += bonus_points
                total_stamps += 1
            
            if not dry_run:
                loyalty_card.save()
                
                # Check achievements
                self._check_achievements(loyalty_card)
            
            self.stdout.write(
                f'  ** Total: {customer_stamps} stamps, {customer_points} points, Rs.{customer_spent} spent'
            )
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'\nSUMMARY:'))
        self.stdout.write(f'  Customers Processed: {total_customers}')
        self.stdout.write(f'  Orders Processed: {total_orders}')
        self.stdout.write(f'  Total Stamps Added: {total_stamps}')
        self.stdout.write(f'  Total Points Awarded: {total_points}')
        self.stdout.write(f'  Total Rewards Created: {total_rewards}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n** DRY RUN - No changes were made. Run without --dry-run to apply.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n** All loyalty rewards applied successfully!'))
    
    def _check_achievements(self, loyalty_card):
        """Check and unlock achievements"""
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
                    loyalty_card.points_balance += achievement.points_reward
                    loyalty_card.lifetime_points += achievement.points_reward
                    loyalty_card.save()
                    
                    from admin_app.models import PointsTransaction
                    PointsTransaction.objects.create(
                        loyalty_card=loyalty_card,
                        points=achievement.points_reward,
                        transaction_type='earned',
                        reason=f'Achievement: {achievement.name}'
                    )
                
                self.stdout.write(self.style.SUCCESS(f'    ** Achievement Unlocked: {achievement.name}'))


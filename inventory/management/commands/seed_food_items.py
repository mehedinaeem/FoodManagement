from django.core.management.base import BaseCommand
from inventory.models import FoodItem


class Command(BaseCommand):
    help = 'Seed the food items database with common household foods'

    def handle(self, *args, **options):
        food_items = [
            # Fruits
            {
                'name': 'Apple',
                'category': 'fruit',
                'typical_expiration_days': 30,
                'sample_cost_per_unit': 0.50,
                'unit': 'piece',
                'description': 'Fresh, crisp apples perfect for snacking or cooking.',
                'storage_tips': 'Store in refrigerator crisper drawer. Keep away from bananas.'
            },
            {
                'name': 'Banana',
                'category': 'fruit',
                'typical_expiration_days': 7,
                'sample_cost_per_unit': 0.30,
                'unit': 'piece',
                'description': 'Sweet, potassium-rich bananas.',
                'storage_tips': 'Store at room temperature. Refrigerate when ripe to slow ripening.'
            },
            {
                'name': 'Orange',
                'category': 'fruit',
                'typical_expiration_days': 14,
                'sample_cost_per_unit': 0.40,
                'unit': 'piece',
                'description': 'Vitamin C rich citrus fruit.',
                'storage_tips': 'Store at room temperature or in refrigerator.'
            },
            {
                'name': 'Strawberries',
                'category': 'fruit',
                'typical_expiration_days': 5,
                'sample_cost_per_unit': 3.50,
                'unit': 'pack',
                'description': 'Sweet, juicy strawberries.',
                'storage_tips': 'Refrigerate immediately. Do not wash until ready to eat.'
            },
            
            # Vegetables
            {
                'name': 'Carrot',
                'category': 'vegetable',
                'typical_expiration_days': 21,
                'sample_cost_per_unit': 1.20,
                'unit': 'bunch',
                'description': 'Crunchy, vitamin A rich root vegetable.',
                'storage_tips': 'Store in refrigerator. Remove green tops before storing.'
            },
            {
                'name': 'Broccoli',
                'category': 'vegetable',
                'typical_expiration_days': 7,
                'sample_cost_per_unit': 2.50,
                'unit': 'bunch',
                'description': 'Nutritious green vegetable high in vitamins.',
                'storage_tips': 'Store in refrigerator crisper. Keep dry.'
            },
            {
                'name': 'Tomato',
                'category': 'vegetable',
                'typical_expiration_days': 7,
                'sample_cost_per_unit': 2.00,
                'unit': 'kg',
                'description': 'Versatile red fruit used as a vegetable.',
                'storage_tips': 'Store at room temperature until ripe, then refrigerate.'
            },
            {
                'name': 'Lettuce',
                'category': 'vegetable',
                'typical_expiration_days': 7,
                'sample_cost_per_unit': 1.80,
                'unit': 'bunch',
                'description': 'Crisp leafy green for salads.',
                'storage_tips': 'Store in refrigerator. Keep dry and wrapped in paper towel.'
            },
            {
                'name': 'Potato',
                'category': 'vegetable',
                'typical_expiration_days': 60,
                'sample_cost_per_unit': 1.50,
                'unit': 'kg',
                'description': 'Starchy tuber, versatile for cooking.',
                'storage_tips': 'Store in cool, dark, dry place. Do not refrigerate.'
            },
            
            # Dairy
            {
                'name': 'Milk',
                'category': 'dairy',
                'typical_expiration_days': 7,
                'sample_cost_per_unit': 3.50,
                'unit': 'l',
                'description': 'Fresh whole milk.',
                'storage_tips': 'Always refrigerate. Use within expiration date.'
            },
            {
                'name': 'Eggs',
                'category': 'dairy',
                'typical_expiration_days': 30,
                'sample_cost_per_unit': 4.00,
                'unit': 'pack',
                'description': 'Fresh chicken eggs.',
                'storage_tips': 'Store in refrigerator. Keep in original carton.'
            },
            {
                'name': 'Cheese',
                'category': 'dairy',
                'typical_expiration_days': 14,
                'sample_cost_per_unit': 5.00,
                'unit': 'pack',
                'description': 'Aged cheddar cheese.',
                'storage_tips': 'Wrap tightly and refrigerate. Keep away from strong odors.'
            },
            {
                'name': 'Yogurt',
                'category': 'dairy',
                'typical_expiration_days': 14,
                'sample_cost_per_unit': 2.50,
                'unit': 'pack',
                'description': 'Creamy plain yogurt.',
                'storage_tips': 'Always refrigerate. Check expiration date regularly.'
            },
            
            # Grains
            {
                'name': 'Bread',
                'category': 'grain',
                'typical_expiration_days': 7,
                'sample_cost_per_unit': 2.50,
                'unit': 'piece',
                'description': 'Fresh white bread loaf.',
                'storage_tips': 'Store in cool, dry place. Can be frozen to extend shelf life.'
            },
            {
                'name': 'Rice',
                'category': 'grain',
                'typical_expiration_days': 365,
                'sample_cost_per_unit': 4.00,
                'unit': 'kg',
                'description': 'Long grain white rice.',
                'storage_tips': 'Store in airtight container in cool, dry place.'
            },
            {
                'name': 'Pasta',
                'category': 'grain',
                'typical_expiration_days': 730,
                'sample_cost_per_unit': 2.00,
                'unit': 'pack',
                'description': 'Dried spaghetti pasta.',
                'storage_tips': 'Store in cool, dry place. Keep in original packaging or airtight container.'
            },
            
            # Meat
            {
                'name': 'Chicken Breast',
                'category': 'meat',
                'typical_expiration_days': 3,
                'sample_cost_per_unit': 8.00,
                'unit': 'kg',
                'description': 'Fresh boneless chicken breast.',
                'storage_tips': 'Refrigerate immediately. Use or freeze within 2 days.'
            },
            {
                'name': 'Ground Beef',
                'category': 'meat',
                'typical_expiration_days': 2,
                'sample_cost_per_unit': 7.50,
                'unit': 'kg',
                'description': 'Fresh ground beef.',
                'storage_tips': 'Refrigerate immediately. Use within 1-2 days or freeze.'
            },
            
            # Beverages
            {
                'name': 'Orange Juice',
                'category': 'beverage',
                'typical_expiration_days': 7,
                'sample_cost_per_unit': 3.00,
                'unit': 'l',
                'description': 'Fresh squeezed orange juice.',
                'storage_tips': 'Refrigerate after opening. Consume within 3-5 days.'
            },
            {
                'name': 'Coffee',
                'category': 'beverage',
                'typical_expiration_days': 180,
                'sample_cost_per_unit': 12.00,
                'unit': 'pack',
                'description': 'Ground coffee beans.',
                'storage_tips': 'Store in airtight container in cool, dark place.'
            },
        ]

        created_count = 0
        updated_count = 0

        for item_data in food_items:
            food_item, created = FoodItem.objects.update_or_create(
                name=item_data['name'],
                defaults={
                    'category': item_data['category'],
                    'typical_expiration_days': item_data['typical_expiration_days'],
                    'sample_cost_per_unit': item_data['sample_cost_per_unit'],
                    'unit': item_data['unit'],
                    'description': item_data.get('description', ''),
                    'storage_tips': item_data.get('storage_tips', ''),
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {food_item.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated: {food_item.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully seeded food items database!\n'
                f'Created: {created_count}\n'
                f'Updated: {updated_count}\n'
                f'Total items: {FoodItem.objects.count()}'
            )
        )


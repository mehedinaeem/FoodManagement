from django.core.management.base import BaseCommand
from resources.models import Resource


class Command(BaseCommand):
    help = 'Seed the resources database with sustainable food practice tips and guides'

    def handle(self, *args, **options):
        resources = [
            # Waste Reduction
            {
                'title': '10 Ways to Reduce Food Waste at Home',
                'description': 'Practical tips for reducing food waste in your household, including meal planning, proper storage, and creative ways to use leftovers.',
                'url': 'https://www.epa.gov/recycle/reducing-wasted-food-home',
                'category': 'waste_reduction',
                'resource_type': 'article',
                'featured': True,
            },
            {
                'title': 'Understanding Food Expiration Dates',
                'description': 'Learn the difference between "sell by", "use by", and "best by" dates to reduce unnecessary food waste.',
                'url': 'https://www.fda.gov/consumers/consumer-updates/confused-date-labels-packaged-foods',
                'category': 'waste_reduction',
                'resource_type': 'guide',
                'featured': False,
            },
            {
                'title': 'Composting Basics for Food Scraps',
                'description': 'A beginner-friendly guide to composting food scraps and reducing organic waste in landfills.',
                'url': 'https://www.epa.gov/recycle/composting-home',
                'category': 'waste_reduction',
                'resource_type': 'guide',
                'featured': False,
            },
            
            # Storage Tips
            {
                'title': 'How to Store Fruits and Vegetables Properly',
                'description': 'Comprehensive guide on storing different types of produce to maximize freshness and shelf life.',
                'url': 'https://www.fda.gov/food/buy-store-serve-safe-food/refrigerator-thermometers-cold-facts-about-food-safety',
                'category': 'storage_tips',
                'resource_type': 'article',
                'featured': True,
            },
            {
                'title': 'Freezer Storage Tips and Best Practices',
                'description': 'Learn how to properly freeze foods to maintain quality and prevent freezer burn.',
                'url': 'https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts',
                'category': 'storage_tips',
                'resource_type': 'tip',
                'featured': False,
            },
            {
                'title': 'Pantry Organization for Food Safety',
                'description': 'Tips for organizing your pantry to prevent food spoilage and make inventory management easier.',
                'category': 'storage_tips',
                'resource_type': 'tip',
                'featured': False,
            },
            
            # Meal Planning
            {
                'title': 'Meal Planning 101: Save Time and Money',
                'description': 'Step-by-step guide to effective meal planning that reduces waste and saves money on groceries.',
                'category': 'meal_planning',
                'resource_type': 'guide',
                'featured': True,
            },
            {
                'title': 'Batch Cooking for Busy Families',
                'description': 'Learn how to prepare meals in advance to save time, reduce waste, and eat healthier throughout the week.',
                'category': 'meal_planning',
                'resource_type': 'article',
                'featured': False,
            },
            {
                'title': 'Using Leftovers Creatively',
                'description': 'Creative recipes and ideas for transforming leftovers into delicious new meals.',
                'category': 'meal_planning',
                'resource_type': 'recipe',
                'featured': False,
            },
            
            # Budget Tips
            {
                'title': 'Smart Grocery Shopping on a Budget',
                'description': 'Strategies for buying nutritious food while staying within your budget, including seasonal shopping and bulk buying tips.',
                'category': 'budget_tips',
                'resource_type': 'article',
                'featured': True,
            },
            {
                'title': 'Buying in Bulk: When It Makes Sense',
                'description': 'Learn when buying in bulk saves money and when it leads to waste, with practical guidelines.',
                'category': 'budget_tips',
                'resource_type': 'tip',
                'featured': False,
            },
            {
                'title': 'Seasonal Produce Shopping Guide',
                'description': 'Guide to buying fruits and vegetables when they are in season for better prices and quality.',
                'category': 'budget_tips',
                'resource_type': 'guide',
                'featured': False,
            },
            
            # Nutrition
            {
                'title': 'Balanced Nutrition on a Budget',
                'description': 'How to maintain a nutritious diet without breaking the bank, focusing on affordable superfoods.',
                'url': 'https://www.myplate.gov/eat-healthy/healthy-eating-budget',
                'category': 'nutrition',
                'resource_type': 'article',
                'featured': True,
            },
            {
                'title': 'Understanding Food Labels',
                'description': 'Learn to read and understand nutrition labels to make healthier food choices.',
                'url': 'https://www.fda.gov/food/new-nutrition-facts-label/how-understand-and-use-nutrition-facts-label',
                'category': 'nutrition',
                'resource_type': 'guide',
                'featured': False,
            },
            
            # Sustainability
            {
                'title': 'Sustainable Food Choices for the Environment',
                'description': 'Learn how your food choices impact the environment and discover sustainable alternatives.',
                'category': 'sustainability',
                'resource_type': 'article',
                'featured': True,
            },
            {
                'title': 'Reducing Your Food Carbon Footprint',
                'description': 'Practical ways to reduce the environmental impact of your food consumption.',
                'category': 'sustainability',
                'resource_type': 'guide',
                'featured': False,
            },
            
            # Cooking Tips
            {
                'title': 'Cooking with Food Scraps',
                'description': 'Creative recipes using parts of food that are often thrown away, like vegetable peels and stems.',
                'category': 'cooking_tips',
                'resource_type': 'recipe',
                'featured': False,
            },
            {
                'title': 'Preserving Fresh Herbs',
                'description': 'Methods for preserving fresh herbs to extend their shelf life and reduce waste.',
                'category': 'preservation',
                'resource_type': 'tip',
                'featured': False,
            },
            
            # Preservation
            {
                'title': 'Home Canning Safety Guide',
                'description': 'Safe methods for canning and preserving foods at home to extend shelf life.',
                'url': 'https://www.fda.gov/food/buy-store-serve-safe-food/selecting-and-serving-produce-safely',
                'category': 'preservation',
                'resource_type': 'guide',
                'featured': False,
            },
            {
                'title': 'Dehydrating Foods at Home',
                'description': 'Learn how to dehydrate fruits, vegetables, and herbs for long-term storage.',
                'category': 'preservation',
                'resource_type': 'guide',
                'featured': False,
            },
            
            # Shopping
            {
                'title': 'Reading Unit Prices at the Grocery Store',
                'description': 'How to compare prices effectively and get the best value when shopping for groceries.',
                'category': 'shopping',
                'resource_type': 'tip',
                'featured': False,
            },
        ]

        created_count = 0
        updated_count = 0

        for resource_data in resources:
            resource, created = Resource.objects.update_or_create(
                title=resource_data['title'],
                defaults={
                    'description': resource_data['description'],
                    'url': resource_data.get('url', ''),
                    'category': resource_data['category'],
                    'resource_type': resource_data['resource_type'],
                    'featured': resource_data.get('featured', False),
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {resource.title}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated: {resource.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully seeded resources database!\n'
                f'Created: {created_count}\n'
                f'Updated: {updated_count}\n'
                f'Total resources: {Resource.objects.count()}'
            )
        )


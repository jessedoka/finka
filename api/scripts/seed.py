import asyncio
import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import settings
from models import Base
from models.user import User
from models.account import Account
from models.category import Category
from models.transaction import Transaction

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)

CATEGORIES = [
    {"name": "Salary", "colour": "#22C55E", "icon": "briefcase", "is_income": True},
    {"name": "Freelance", "colour": "#10B981", "icon": "laptop", "is_income": True},
    {"name": "Groceries", "colour": "#F59E0B", "icon": "shopping-cart", "is_income": False},
    {"name": "Rent", "colour": "#EF4444", "icon": "home", "is_income": False},
    {"name": "Eating Out", "colour": "#F97316", "icon": "utensils", "is_income": False},
    {"name": "Transport", "colour": "#3B82F6", "icon": "car", "is_income": False},
    {"name": "Subscriptions", "colour": "#8B5CF6", "icon": "repeat", "is_income": False},
    {"name": "Gym", "colour": "#06B6D4", "icon": "dumbbell", "is_income": False},
    {"name": "Shopping", "colour": "#EC4899", "icon": "shopping-bag", "is_income": False},
    {"name": "Bills", "colour": "#6366F1", "icon": "file-text", "is_income": False},
]

# Realistic transaction templates: (description, merchant, category_name, amount_range)
EXPENSE_TEMPLATES = [
    ("Tesco Weekly Shop", "Tesco", "Groceries", (35, 85)),
    ("Aldi", "Aldi", "Groceries", (20, 55)),
    ("Co-op", "Co-op", "Groceries", (8, 25)),
    ("Monthly Rent", None, "Rent", (750, 750)),
    ("Council Tax", "Tewkesbury Borough Council", "Bills", (145, 145)),
    ("Electric & Gas", "Octopus Energy", "Bills", (80, 140)),
    ("Water Bill", "Severn Trent", "Bills", (35, 35)),
    ("Spotify Premium", "Spotify", "Subscriptions", (11, 11)),
    ("Netflix", "Netflix", "Subscriptions", (11, 11)),
    ("Claude Pro", "Anthropic", "Subscriptions", (18, 18)),
    ("GitHub Copilot", "GitHub", "Subscriptions", (8, 8)),
    ("PureGym", "PureGym", "Gym", (25, 25)),
    ("Costa Coffee", "Costa", "Eating Out", (3, 6)),
    ("Nando's", "Nando's", "Eating Out", (12, 22)),
    ("Greggs", "Greggs", "Eating Out", (3, 7)),
    ("The Meadow", "The Meadow Tewkesbury", "Eating Out", (15, 35)),
    ("Train to Cheltenham", "GWR", "Transport", (5, 9)),
    ("Petrol", "Shell", "Transport", (40, 65)),
    ("Amazon", "Amazon", "Shopping", (10, 80)),
    ("Currys", "Currys", "Shopping", (15, 200)),
]

INCOME_TEMPLATES = [
    ("Corp Salary", "Corp Systems", "Salary", (2800, 2800)),
]


async def seed():
    async with async_session() as session:
        # 1. Create user
        user = User(
            cognito_sub="dev-user-001",
            email="jd@finka.dev",
            display_name="JD",
        )
        session.add(user)
        await session.flush()  # get user.id

        # 2. Create accounts
        current_account = Account(
            user_id=user.id,
            name="Monzo Current Account",
            account_type="current",
            currency="GBP",
            institution="Monzo",
            balance=Decimal("1842.50"),
        )
        savings_account = Account(
            user_id=user.id,
            name="Marcus Savings",
            account_type="savings",
            currency="GBP",
            institution="Goldman Sachs",
            balance=Decimal("5200.00"),
        )
        session.add_all([current_account, savings_account])
        await session.flush()

        # 3. Create categories
        category_map = {}
        for cat_data in CATEGORIES:
            cat = Category(user_id=user.id, **cat_data)
            session.add(cat)
            await session.flush()
            category_map[cat.name] = cat

        # 4. Generate 6 months of transactions
        today = date.today()
        start_date = today.replace(day=1) - timedelta(days=180)
        current_date = start_date

        while current_date <= today:
            # Monthly salary on the 28th
            if current_date.day == 28:
                for tmpl in INCOME_TEMPLATES:
                    desc, merchant, cat_name, (lo, hi) = tmpl
                    session.add(Transaction(
                        user_id=user.id,
                        account_id=current_account.id,
                        category_id=category_map[cat_name].id,
                        amount=Decimal(str(random.randint(lo, hi))),
                        description=desc,
                        merchant_name=merchant,
                        transaction_date=current_date,
                    ))

            # Monthly bills on the 1st
            if current_date.day == 1:
                for tmpl in EXPENSE_TEMPLATES:
                    desc, merchant, cat_name, (lo, hi) = tmpl
                    if cat_name in ("Rent", "Bills", "Subscriptions", "Gym"):
                        session.add(Transaction(
                            user_id=user.id,
                            account_id=current_account.id,
                            category_id=category_map[cat_name].id,
                            amount=-Decimal(str(random.randint(lo, hi))),
                            description=desc,
                            merchant_name=merchant,
                            transaction_date=current_date,
                        ))

            # Random daily expenses (2-4 per day on weekdays, 1-2 on weekends)
            is_weekend = current_date.weekday() >= 5
            num_daily = random.randint(1, 2) if is_weekend else random.randint(0, 3)

            daily_candidates = [
                t for t in EXPENSE_TEMPLATES
                if t[2] not in ("Rent", "Bills", "Subscriptions", "Gym")
            ]

            for _ in range(num_daily):
                tmpl = random.choice(daily_candidates)
                desc, merchant, cat_name, (lo, hi) = tmpl
                session.add(Transaction(
                    user_id=user.id,
                    account_id=current_account.id,
                    category_id=category_map[cat_name].id,
                    amount=-Decimal(str(round(random.uniform(lo, hi), 2))),
                    description=desc,
                    merchant_name=merchant,
                    transaction_date=current_date,
                ))

            current_date += timedelta(days=1)

        await session.commit()

        # Count what we created
        from sqlalchemy import func, select
        count = await session.scalar(
            select(func.count()).select_from(Transaction)
        )
        print(f"Seeded: 1 user, 2 accounts, {len(CATEGORIES)} categories, {count} transactions")


if __name__ == "__main__":
    asyncio.run(seed())
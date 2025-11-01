import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
from pathlib import Path


class DataGenerator:
    
    def __init__(self, seed: int = 42):
        self.fake = Faker()
        Faker.seed(seed)
        np.random.seed(seed)
        random.seed(seed)
    
    def generate_structured_data(self, rows: int = 1000, columns: int = 10) -> pd.DataFrame:
        
        data = {
            'id': range(1, rows + 1),
            'name': [self.fake.name() for _ in range(rows)],
            'email': [self.fake.email() for _ in range(rows)],
            'age': np.random.randint(18, 80, rows),
            'salary': np.random.randint(30000, 200000, rows),
            'department': np.random.choice(['Sales', 'Engineering', 'HR', 'Marketing', 'Finance'], rows),
            'join_date': [self.fake.date_between(start_date='-10y', end_date='today') for _ in range(rows)],
            'performance_score': np.random.uniform(1.0, 5.0, rows).round(2),
            'projects_completed': np.random.randint(0, 50, rows),
            'city': [self.fake.city() for _ in range(rows)]
        }
        
        df = pd.DataFrame(data)
        df['join_date'] = pd.to_datetime(df['join_date'])
        
        return df
    
    def generate_unstructured_data(self, rows: int = 1000, columns: int = 5) -> pd.DataFrame:
        
        data = {
            'id': range(1, rows + 1),
            'customer_feedback': [self._generate_feedback() for _ in range(rows)],
            'product_review': [self._generate_review() for _ in range(rows)],
            'support_ticket': [self._generate_ticket() for _ in range(rows)],
            'notes': [self.fake.paragraph(nb_sentences=3) for _ in range(rows)]
        }
        
        return pd.DataFrame(data)
    
    def _generate_feedback(self) -> str:
        sentiments = [
            "Great service! Very satisfied with the product quality.",
            "Poor experience. The delivery was delayed by 2 weeks.",
            "Average product. Nothing special but gets the job done.",
            "Excellent customer support. They resolved my issue quickly.",
            "Disappointed with the quality. Expected much better.",
            "Good value for money. Would recommend to others.",
            "The product broke after just one week of use.",
            "Outstanding! Exceeded all my expectations.",
            "Needs improvement in packaging. Product arrived damaged.",
            "Satisfied overall. Minor issues but nothing major."
        ]
        return random.choice(sentiments)
    
    def _generate_review(self) -> str:
        reviews = [
            f"Bought this product last {random.choice(['week', 'month'])}. {self.fake.sentence()}",
            f"Quality is {random.choice(['excellent', 'good', 'average', 'poor'])}. {self.fake.sentence()}",
            f"Price is {random.choice(['reasonable', 'high', 'low'])} for what you get. {self.fake.sentence()}",
        ]
        return " ".join(random.sample(reviews, 2))
    
    def _generate_ticket(self) -> str:
        issues = [
            "Unable to login to account. Getting error message.",
            "Payment failed but amount was deducted from account.",
            "Product not working as described in the manual.",
            "Need help with installation and setup process.",
            "Billing discrepancy in last month's invoice.",
            "Feature request: Add dark mode to the application.",
            "Bug report: Application crashes on startup.",
            "Account access issue. Password reset not working."
        ]
        return random.choice(issues)
    
    def save_to_excel(
        self, 
        structured_df: pd.DataFrame, 
        unstructured_df: pd.DataFrame = None,
        filepath: str = "data/output/sample_data.xlsx"
    ):
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            structured_df.to_excel(writer, sheet_name='Structured_Data', index=False)
            
            if unstructured_df is not None:
                unstructured_df.to_excel(writer, sheet_name='Unstructured_Data', index=False)
        
        print(f"Data saved to {filepath}")
        return filepath


def main():
    generator = DataGenerator()
    
    structured_df = generator.generate_structured_data(rows=1000, columns=10)
    print(f"Generated structured data: {structured_df.shape}")
    print(structured_df.head())
    
    unstructured_df = generator.generate_unstructured_data(rows=1000, columns=5)
    print(f"\nGenerated unstructured data: {unstructured_df.shape}")
    print(unstructured_df.head())
    
    filepath = generator.save_to_excel(structured_df, unstructured_df)
    print(f"\nSample data ready at: {filepath}")


if __name__ == "__main__":
    main()
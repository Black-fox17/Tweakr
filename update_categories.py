import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datapipeline.core.constants import SQLALCHEMY_DATABASE_URL

# Load environment variables
load_dotenv()

# Database connection

engine = create_engine(SQLALCHEMY_DATABASE_URL)
Session = sessionmaker(bind=engine)

def standardize_category(category):
    """Standardize category format"""
    if not category:
        return "uncategorized"
    
    # Convert to lowercase and strip whitespace
    category = category.lower().strip()
    
    # Replace spaces with underscores
    category = category.replace(" ", "_")
    
    # Remove any special characters
    category = ''.join(c for c in category if c.isalnum() or c == '_')
    
    return category

def update_categories():
    """Update categories in the database to standardized format"""
    session = Session()
    
    try:
        # Get all unique categories
        result = session.execute(text("SELECT DISTINCT category FROM papers"))
        categories = [row[0] for row in result]
        
        print(f"Found {len(categories)} unique categories before standardization")
        
        # Create a mapping of old categories to standardized ones
        category_mapping = {}
        for category in categories:
            if category:
                standardized = standardize_category(category)
                if standardized != category:
                    category_mapping[category] = standardized
        
        # Update categories in the database
        for old_category, new_category in category_mapping.items():
            print(f"Updating '{old_category}' to '{new_category}'")
            session.execute(
                text("UPDATE papers SET category = :new_category WHERE category = :old_category"),
                {"new_category": new_category, "old_category": old_category}
            )
        
        session.commit()
        
        # Verify the changes
        result = session.execute(text("SELECT DISTINCT category FROM papers ORDER BY category"))
        cleaned_categories = [row[0] for row in result]
        
        print(f"\nStandardized categories ({len(cleaned_categories)}):")
        for category in cleaned_categories:
            print(f"  - {category}")
            
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    update_categories() 
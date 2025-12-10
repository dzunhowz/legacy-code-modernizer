# Example: Using Refactoring Crew for Code Modernization

from src.agents.refactoring_crew import RefactoringCrew
import json

# Example legacy code to refactor
LEGACY_CODE = """
def process_user_data(data):
    # Process user data
    results = []
    for d in data:
        if d['age'] > 18:
            if d['active'] == True:
                user = {}
                user['name'] = d['name']
                user['email'] = d['email']
                user['age'] = d['age']
                results.append(user)
    return results

def calculate_discount(price, customer_type):
    # Calculate discount
    if customer_type == 'gold':
        discount = 0.2
    elif customer_type == 'silver':
        discount = 0.1
    else:
        discount = 0
    final_price = price - (price * discount)
    return final_price
"""

def main():
    """Example usage of Refactoring Crew agent."""
    
    # Initialize Refactoring Crew with AWS Bedrock
    print("Initializing Refactoring Crew with AWS Bedrock...")
    crew = RefactoringCrew(
        bedrock_model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        aws_region="ap-southeast-2"
    )
    
    # Example 1: Full refactoring workflow
    print("\n" + "="*70)
    print("EXAMPLE 1: Full Refactoring Workflow")
    print("="*70)
    
    result = crew.full_refactoring_workflow(
        code=LEGACY_CODE,
        context="""
        This code is part of a user management service that processes
        user registrations. It's called frequently (100+ times/second)
        and needs to be more maintainable and performant.
        """
    )
    
    print("\n--- REFACTORING PLAN ---")
    print(result['refactoring_plan'])
    
    print("\n--- REFACTORED CODE ---")
    print(result['refactored_code'])
    
    # Example 2: Generate tests for refactored code
    print("\n" + "="*70)
    print("EXAMPLE 2: Generate Tests")
    print("="*70)
    
    tests = crew.generate_tests(
        code=LEGACY_CODE,
        refactored_code=result['refactored_code']
    )
    
    print("\n--- GENERATED TESTS ---")
    print(tests)
    
    # Example 3: Architectural review
    print("\n" + "="*70)
    print("EXAMPLE 3: Architectural Review")
    print("="*70)
    
    codebase_description = """
    Legacy E-commerce Platform
    - Monolithic architecture
    - 50k+ lines of Python code
    - Django 2.2 (EOL)
    - MySQL database
    - No test coverage
    - Manual deployment process
    - Core modules:
        * User management (authentication, profiles)
        * Product catalog (inventory, search)
        * Order processing (cart, checkout, payment)
        * Admin dashboard
    - Pain points:
        * Slow response times (2-5 seconds)
        * Frequent bugs in production
        * Difficult to add new features
        * No API for mobile apps
    """
    
    review = crew.architectural_review(codebase_description)
    
    print("\n--- ARCHITECTURAL REVIEW ---")
    print(review)
    
    # Example 4: Step-by-step refactoring
    print("\n" + "="*70)
    print("EXAMPLE 4: Step-by-Step Refactoring")
    print("="*70)
    
    # Step 1: Analyze and create plan
    print("\nStep 1: Creating refactoring plan...")
    plan = crew.analyze_and_plan(
        code=LEGACY_CODE,
        context="High-priority function used in API endpoints"
    )
    print("Plan created!")
    
    # Step 2: Implement refactoring
    print("\nStep 2: Implementing refactoring...")
    refactored = crew.refactor_code(
        code=LEGACY_CODE,
        plan=plan
    )
    print("Refactoring complete!")
    
    print("\n--- REFACTORED CODE (Step-by-Step) ---")
    print(refactored)


if __name__ == "__main__":
    main()

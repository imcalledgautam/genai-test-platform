# Bank Transaction Analyzer Dashboard

## Project Vision
The Bank Transaction Analyzer Dashboard is designed to help users gain insights into their spending patterns, categorize expenses effortlessly, manage budgets, and identify overspending. It serves as a practical demonstration of requirements analysis, database interaction, data analytics, and visualization skills.

## Functional Requirements

### Transaction Categorization
- Automatically categorize transactions into predefined categories:
  - Groceries
  - Rent
  - Dining
  - Entertainment
  - Utilities
  - Transport
  - Health
  - Others

### Budget Management
- Enable users to set monthly budget limits per category.
- Provide clear visual indicators or alerts for overspending.

### Trend Analysis
- Display monthly spending trends per category.
- Show year-to-date summaries and visual analytics.

### Visualization Dashboard
- Interactive visualizations, including:
  - Pie charts (expenses by category).
  - Line graphs (monthly and yearly spending trends).
- Provide filtering options by:
  - Month
  - Year
  - Expense category

## Non-Functional Requirements

### Usability
- User-friendly interface with intuitive navigation and clear visuals.

### Performance
- Responsive interface with quick data retrieval and visualization (loading within seconds).

### Maintainability
- Clean, organized, and commented code.
- Comprehensive documentation, including setup instructions and code explanations.

### Technology Constraints
- Python (using pandas and matplotlib/seaborn)
- SQLite or PostgreSQL for database management
- Streamlit or Jupyter Notebook for interactive visualization

## Data Requirements

### Transactions Dataset
- Transaction ID (unique identifier)
- Date of transaction
- Transaction amount
- Transaction category (automatic categorization, user-editable)
- Transaction description (free text)

### Budget Dataset
- Expense category
- Monthly budget limit

## Project Deliverables
- Structured Requirements Document (this document)
- Entity-Relationship Diagram (ERD) for the database
- Script for generating mock transaction data
- Python analysis scripts
- Interactive Visualization Dashboard
- GitHub repository with README (setup instructions, screenshots, and explanations)


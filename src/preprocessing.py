import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set style for better visualizations
plt.style.use('default')
sns.set_palette("husl")

class HospitalDataProcessor:
    def __init__(self, data_path=None):
        """Initialize the data processor"""
        self.data_path = data_path
        self.df = None
        self.processed_df = None
    
    def generate_sample_data(self, n_rows=41544):
        """Generate sample data matching the dataset description"""
        np.random.seed(42)
        
        # Date range for 3 years
        start_date = pd.Timestamp('2021-01-01')
        end_date = pd.Timestamp('2024-01-01')
        
        # Hospital names in Riyadh
        hospitals = [
            'King Fahad Medical City', 'Riyadh Care Hospital', 
            'King Khalid University Hospital', 'Prince Sultan Military Medical City',
            'National Guard Hospital', 'Security Forces Hospital', 
            'King Abdulaziz Medical City', 'Al-Faisal Hospital',
            'Dallah Hospital', 'Sulaiman Al Habib Hospital'
        ]
        
        # Condition types
        conditions = [
            'Cardiovascular', 'Respiratory', 'Neurological', 'Orthopedic',
            'Gastrointestinal', 'Endocrine', 'Infectious Disease', 'Oncology',
            'Psychiatric', 'Emergency Medicine'
        ]
        
        # Patient demographics
        age_groups = ['0-18', '19-35', '36-50', '51-65', '66+']
        genders = ['Male', 'Female']
        severity_levels = ['Low', 'Medium', 'High', 'Critical']
        seasons = ['Winter', 'Spring', 'Summer', 'Fall']
        
        # Primary diagnosis codes (ICD-10 style)
        diagnosis_codes = [f"{chr(65+i//100)}{i%100:02d}.{j}" 
                          for i in range(26) for j in range(10)][:500]
        
        # Generate data
        data = []
        for _ in range(n_rows):
            # Random date with seasonal bias
            date = start_date + timedelta(days=np.random.randint(0, (end_date - start_date).days))
            
            # Seasonal indicator based on date
            month = date.month
            if month in [12, 1, 2]:
                season = 'Winter'
                seasonal_multiplier = 1.3  # Higher admissions in winter
            elif month in [3, 4, 5]:
                season = 'Spring'
                seasonal_multiplier = 1.0
            elif month in [6, 7, 8]:
                season = 'Summer'
                seasonal_multiplier = 0.8
            else:
                season = 'Fall'
                seasonal_multiplier = 1.1
            
            # Hospital and condition
            hospital = np.random.choice(hospitals)
            condition = np.random.choice(conditions)
            
            # Admission count with seasonal bias
            base_admissions = np.random.poisson(15)
            admission_count = max(1, int(base_admissions * seasonal_multiplier))
            
            # Patient demographics
            age_group = np.random.choice(age_groups, p=[0.15, 0.25, 0.25, 0.20, 0.15])
            gender = np.random.choice(genders)
            
            # Severity and related metrics
            severity = np.random.choice(severity_levels, p=[0.4, 0.3, 0.2, 0.1])
            
            # Length of stay based on severity
            if severity == 'Low':
                los_avg = np.random.normal(2, 0.5)
            elif severity == 'Medium':
                los_avg = np.random.normal(5, 1.5)
            elif severity == 'High':
                los_avg = np.random.normal(8, 2)
            else:  # Critical
                los_avg = np.random.normal(12, 3)
            
            los_avg = max(0.5, los_avg)
            
            # Readmissions and emergency visits correlated with severity
            severity_factor = {'Low': 0.1, 'Medium': 0.3, 'High': 0.6, 'Critical': 0.8}[severity]
            readmission_count = np.random.poisson(severity_factor * 2)
            emergency_visit_count = np.random.poisson(severity_factor * 3)
            
            # Comorbid conditions
            comorbid_count = np.random.poisson(1.5) if age_group in ['51-65', '66+'] else np.random.poisson(0.8)
            
            # Medication dosage
            medication_dosage = np.random.lognormal(2, 0.5)
            
            data.append({
                'admission_date': date,
                'hospital_name': hospital,
                'admission_count': admission_count,
                'condition_type': condition,
                'patient_age_group': age_group,
                'patient_gender': gender,
                'readmission_count': readmission_count,
                'severity_level': severity,
                'length_of_stay_avg': round(los_avg, 1),
                'seasonal_indicator': season,
                'comorbid_conditions_count': comorbid_count,
                'primary_diagnosis_code': np.random.choice(diagnosis_codes),
                'daily_medication_dosage': round(medication_dosage, 2),
                'emergency_visit_count': emergency_visit_count
            })
        
        self.df = pd.DataFrame(data)
        print(f"Generated sample dataset with {len(self.df)} rows")
        return self.df
    
    def load_data(self, file_path):
        """Load data from CSV file"""
        try:
            self.df = pd.read_csv(file_path)
            print(f"Loaded dataset with {len(self.df)} rows and {len(self.df.columns)} columns")
            return self.df
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def preprocess_data(self):
        """Comprehensive data preprocessing"""
        if self.df is None:
            print("No data loaded. Please load data first.")
            return None
        
        print("Starting data preprocessing...")
        

        # Create a copy for processing
        df = self.df.copy()
        print(f"Initial columns: {df.columns}")
        # 1. Convert admission_date to datetime
        if df['admission_date'].dtype == 'object':
            df['admission_date'] = pd.to_datetime(df['admission_date'])
        
        # 2. Handle missing values
        print("Checking for missing values:")
        missing_values = df.isnull().sum()
        print(missing_values[missing_values > 0])
        
        # Fill missing values if any
        for col in df.columns:
            if df[col].isnull().any():
                if df[col].dtype in ['float64', 'int64']:
                    df[col].fillna(df[col].median(), inplace=True)
                else:
                    df[col].fillna(df[col].mode()[0], inplace=True)
        
        # 3. Create additional time-based features
        df['year'] = df['admission_date'].dt.year
        df['month'] = df['admission_date'].dt.month
        df['day_of_week'] = df['admission_date'].dt.day_name()
        df['day_of_year'] = df['admission_date'].dt.dayofyear
        df['week_of_year'] = df['admission_date'].dt.isocalendar().week
        df['is_weekend'] = df['admission_date'].dt.weekday >= 5
        
        # 4. Create seasonal grouping (if not already present)
        def get_season(month):
            if month in [12, 1, 2]:
                return 'Winter'
            elif month in [3, 4, 5]:
                return 'Spring'
            elif month in [6, 7, 8]:
                return 'Summer'
            else:
                return 'Fall'
        
        if 'seasonal_indicator' not in df.columns:
            df['seasonal_indicator'] = df['month'].apply(get_season)
        
        # 5. Create derived features
        df['readmission_rate'] = df['readmission_count'] / df['admission_count']
        df['emergency_rate'] = df['emergency_visit_count'] / df['admission_count']
        df['severity_score'] = df['severity_level'].map({
            'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4
        })
        
        # 6. Age group encoding
        df['age_group_numeric'] = df['patient_age_group'].map({
            '0-18': 1, '19-35': 2, '36-50': 3, '51-65': 4, '66+': 5
        })
        
        self.processed_df = df
        print(f"Data preprocessing completed. Final columns: {df.columns}")
        print(f"Data preprocessing completed. Final dataset shape: {df.shape}")
        return df
     
    def perform_eda(self):
        """Comprehensive Exploratory Data Analysis"""
        if self.processed_df is None:
            print("Please preprocess data first.")
            return
        
        df = self.processed_df
        
        # Set up the plotting style
        plt.rcParams['figure.figsize'] = (15, 10)
        
        print("=== EXPLORATORY DATA ANALYSIS ===\n")
        
        # Basic statistics
        print("1. BASIC DATASET INFORMATION:")
        print(f"Dataset shape: {df.shape}")
        print(f"Date range: {df['admission_date'].min()} to {df['admission_date'].max()}")
        print(f"Total admissions: {df['admission_count'].sum():,}")
        print(f"Average length of stay: {df['length_of_stay_avg'].mean():.2f} days")
        print(f"Total emergency visits: {df['emergency_visit_count'].sum():,}\n")
        
        # Create subplots for comprehensive EDA
        fig, axes = plt.subplots(3, 3, figsize=(20, 18))
        fig.suptitle('Hospital Admissions - Comprehensive EDA', fontsize=16, fontweight='bold')
        
        # 1. Admission trends over time
        daily_admissions = df.groupby('admission_date')['admission_count'].sum().reset_index()
        axes[0, 0].plot(daily_admissions['admission_date'], daily_admissions['admission_count'], alpha=0.7)
        axes[0, 0].set_title('Daily Admission Trends')
        axes[0, 0].set_xlabel('Date')
        axes[0, 0].set_ylabel('Total Admissions')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. Admissions by hospital
        hospital_admissions = df.groupby('hospital_name')['admission_count'].sum().sort_values(ascending=False)
        axes[0, 1].bar(range(len(hospital_admissions)), hospital_admissions.values, color='skyblue')
        axes[0, 1].set_title('Total Admissions by Hospital')
        axes[0, 1].set_xlabel('Hospital')
        axes[0, 1].set_ylabel('Total Admissions')
        axes[0, 1].set_xticks(range(len(hospital_admissions)))
        axes[0, 1].set_xticklabels(hospital_admissions.index, rotation=45, ha='right')
        
        # 3. Admissions by condition type
        condition_admissions = df.groupby('condition_type')['admission_count'].sum().sort_values(ascending=False)
        axes[0, 2].barh(range(len(condition_admissions)), condition_admissions.values, color='lightcoral')
        axes[0, 2].set_title('Admissions by Condition Type')
        axes[0, 2].set_xlabel('Total Admissions')
        axes[0, 2].set_yticks(range(len(condition_admissions)))
        axes[0, 2].set_yticklabels(condition_admissions.index)
        
        # 4. Seasonal distribution
        seasonal_admissions = df.groupby('seasonal_indicator')['admission_count'].sum()
        axes[1, 0].pie(seasonal_admissions.values, labels=seasonal_admissions.index, autopct='%1.1f%%', startangle=90)
        axes[1, 0].set_title('Seasonal Distribution of Admissions')
        
        # 5. Age group distribution
        age_admissions = df.groupby('patient_age_group')['admission_count'].sum()
        axes[1, 1].bar(age_admissions.index, age_admissions.values, color='lightgreen')
        axes[1, 1].set_title('Admissions by Age Group')
        axes[1, 1].set_xlabel('Age Group')
        axes[1, 1].set_ylabel('Total Admissions')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        # 6. Severity level distribution
        severity_admissions = df.groupby('severity_level')['admission_count'].sum()
        axes[1, 2].bar(severity_admissions.index, severity_admissions.values, color='orange')
        axes[1, 2].set_title('Admissions by Severity Level')
        axes[1, 2].set_xlabel('Severity Level')
        axes[1, 2].set_ylabel('Total Admissions')
        
        # 7. Length of stay vs readmissions
        axes[2, 0].scatter(df['length_of_stay_avg'], df['readmission_count'], alpha=0.6, color='purple')
        axes[2, 0].set_title('Length of Stay vs Readmissions')
        axes[2, 0].set_xlabel('Average Length of Stay (days)')
        axes[2, 0].set_ylabel('Readmission Count')
        
        # 8. Emergency visits vs admissions
        axes[2, 1].scatter(df['admission_count'], df['emergency_visit_count'], alpha=0.6, color='red')
        axes[2, 1].set_title('Admissions vs Emergency Visits')
        axes[2, 1].set_xlabel('Admission Count')
        axes[2, 1].set_ylabel('Emergency Visit Count')
        
        # 9. Monthly admission heatmap
        monthly_data = df.groupby(['month', 'severity_level'])['admission_count'].sum().unstack(fill_value=0)
        im = axes[2, 2].imshow(monthly_data.values, cmap='YlOrRd', aspect='auto')
        axes[2, 2].set_title('Monthly Admissions Heatmap by Severity')
        axes[2, 2].set_xlabel('Severity Level')
        axes[2, 2].set_ylabel('Month')
        axes[2, 2].set_xticks(range(len(monthly_data.columns)))
        axes[2, 2].set_xticklabels(monthly_data.columns, rotation=45)
        axes[2, 2].set_yticks(range(len(monthly_data.index)))
        axes[2, 2].set_yticklabels(monthly_data.index)
        
        plt.tight_layout()
        plt.show()
        
        # Additional correlation analysis
        print("\n2. CORRELATION ANALYSIS:")
        numeric_cols = ['admission_count', 'readmission_count', 'length_of_stay_avg', 
                       'emergency_visit_count', 'comorbid_conditions_count', 'severity_score']
        correlation_matrix = df[numeric_cols].corr()
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
                    square=True, linewidths=0.5, cbar_kws={"shrink": .8})
        plt.title('Correlation Matrix of Key Metrics')
        plt.tight_layout()
        plt.show()
        
        # Statistical summaries
        print("\n3. STATISTICAL SUMMARIES:")
        print(df[numeric_cols].describe())
        
        print("\n4. KEY INSIGHTS:")
        print("- Peak admission months:", df.groupby('month')['admission_count'].sum().nlargest(3).index.tolist())
        print("- Most common condition:", df.groupby('condition_type')['admission_count'].sum().idxmax())
        print("- Hospital with highest admissions:", df.groupby('hospital_name')['admission_count'].sum().idxmax())
        print("- Average readmission rate:", f"{df['readmission_rate'].mean():.3f}")
        print("- Weekend vs weekday admission ratio:", 
              f"{df[df['is_weekend']]['admission_count'].sum() / df[~df['is_weekend']]['admission_count'].sum():.3f}")
    
    def save_processed_data(self, filename='processed_hospital_data.csv'):
        """Save processed data to CSV"""
        if self.processed_df is not None:
            self.processed_df.to_csv(filename, index=False)
            print(f"Processed data saved to {filename}")
        else:
            print("No processed data to save.")

# Example usage
if __name__ == "__main__":
    processor = HospitalDataProcessor()
    df = processor.load_data("Hospital_Dataset_2020_2024.csv")  # Use your CSV file path here
    processed_df = processor.preprocess_data()
    # processor.perform_eda()
    processor.save_processed_data()
    
    print("\nData preprocessing and EDA completed successfully!")
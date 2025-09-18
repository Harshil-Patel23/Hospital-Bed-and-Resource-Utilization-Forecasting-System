from setuptools import setup, find_packages

setup(
    name="hospital-forecasting-system",
    version="1.0.0",
    description="Hospital Bed & Resource Utilization Forecasting System",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.1",
        "pandas>=2.0.3",
        "numpy>=1.24.3",
        "plotly>=5.15.0",
        "seaborn>=0.12.2",
        "matplotlib>=3.7.2",
        "scikit-learn>=1.3.0",
        "xgboost>=1.7.6",
        "statsmodels>=0.14.0",
        "openpyxl>=3.1.2"
    ],
    python_requires=">=3.8",
)
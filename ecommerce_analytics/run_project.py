# run_project.py
import os
import sys
import subprocess

# Change to the project directory
project_dir = r"C:\Users\pnkot\OneDrive\Desktop\Clean Code\E-Commerce-Sales-Analytics-\ecommerce_analytics\ecommerce_sales_analytics"
os.chdir(project_dir)
print(f"Changed to: {os.getcwd()} - run_project.py:9")

def run_script(script_name):
    """Run a Python script"""
    print(f"\n{'='*60} - run_project.py:13")
    print(f"Running: {script_name} - run_project.py:14")
    print('= - run_project.py:15'*60)
    result = subprocess.run([sys.executable, script_name], cwd=project_dir)
    return result.returncode

def run_dashboard():
    """Run Streamlit dashboard"""
    print(f"\n{'='*60} - run_project.py:21")
    print("Starting Streamlit Dashboard - run_project.py:22")
    print('= - run_project.py:23'*60)
    subprocess.run(["streamlit", "run", "dashboard/app.py"], cwd=project_dir)

def main():
    print("\n - run_project.py:27" + "="*60)
    print("ECOMMERCE SALES ANALYTICS - run_project.py:28")
    print("= - run_project.py:29"*60)
    print("\nOptions: - run_project.py:30")
    print("1. Run Data Cleaning - run_project.py:31")
    print("2. Run Data Analysis - run_project.py:32")
    print("3. Run Visualizations - run_project.py:33")
    print("4. Run Dashboard - run_project.py:34")
    print("5. Run All - run_project.py:35")
    print("6. Exit - run_project.py:36")
    
    choice = input("\nEnter choice (1-6): ")
    
    if choice == '1':
        run_script("scripts/data_cleaning.py")
    elif choice == '2':
        run_script("scripts/data_analysis.py")
    elif choice == '3':
        run_script("scripts/visualization.py")
    elif choice == '4':
        run_dashboard()
    elif choice == '5':
        run_script("scripts/data_cleaning.py")
        run_script("scripts/data_analysis.py")
        run_script("scripts/visualization.py")
        run_dashboard()
    else:
        print("Exiting... - run_project.py:54")

if __name__ == "__main__":
    main()
# Car Scraper Project

## Overview
The Car Scraper project is a web scraping application that extracts information about used cars from a popular automotive website (auto.ria.com). The scraped data includes details such as car title, price, odometer reading, seller information, and more. The project uses Python, Selenium, Beautiful Soup, and PostgreSQL to automate data extraction and storage.

## Features
- **Web Scraping:** Extracts car information from the specified website using web scraping techniques.
- **Database Storage:** Stores the scraped data in a PostgreSQL database for later analysis and retrieval.
- **Scheduled Execution:** Automates the scraping and database dumping tasks using scheduled jobs.

## Prerequisites
Before running the project, ensure you have the following installed:
- Python (3.x)
- PostgreSQL
- Chrome WebDriver (for Selenium)

## Setup
1. Install project dependencies: `pip install -r requirements.txt`
2. Set up the PostgreSQL database and configure the connection parameters in the script.
3. Ensure Chrome WebDriver is available in the system's PATH or provide the path in the script.

## Usage
1. Run the script `main_script.py` to initiate the scraping and data insertion process.
2. The script will create dumps folder and perform a database dump daily at midnight.
3. Scraped data is inserted into the PostgreSQL database.

## Configuration
- Configure database connection parameters in the script (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, etc.).
- Adjust scheduling settings in the script for daily execution.

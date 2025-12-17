# WhatsApp Chat Analyzer (Streamlit)

This project is a Streamlit-based web application that analyzes exported WhatsApp chat files.
It provides insights such as message statistics, user activity patterns, timelines, word usage,
emoji frequency, and engagement trends for both individual users and entire groups.

## Features
- Total messages, words, media, and links count
- Monthly and daily message timelines
- Weekly and monthly activity analysis
- Activity heatmap by day and time period
- Most active users in group chats
- Word cloud generation with Hinglish stopword filtering
- Most common words analysis
- Emoji usage analysis with tabular and pie chart views

## Tech Stack
- Python
- Streamlit
- Pandas
- Matplotlib
- Seaborn
- WordCloud
- urlextract
- emoji

## Project Structure
- app.py: Streamlit application and UI logic
- preprocessor.py: WhatsApp chat parsing and dataframe creation
- helper.py: Data cleaning, analysis, and visualization utilities
- requirements.txt: Project dependencies
- README.md: Project documentation

## Setup Instructions
1. Clone the repository:
   git clone https://github.com/your-username/whatsapp-chat-analyzer.git

2. Navigate to the project directory:
   cd whatsapp-chat-analyzer

3. Create and activate a virtual environment (optional but recommended).

4. Install dependencies:
   pip install -r requirements.txt

5. Run the application:
   streamlit run app.py

6. Upload an exported WhatsApp .txt chat file from the sidebar to begin analysis.

## Notes
- Group notifications (e.g., user joined/left, group created) are excluded from text analysis.
- Media messages such as images or videos are normalized and counted separately.
- The app supports both individual and group chat analysis.

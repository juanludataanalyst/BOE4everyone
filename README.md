# BOE4Everyone

A personal project to create an accessible, chat-based interface for querying the Spanish *Boletín Oficial del Estado* (BOE). BOE4Everyone extracts data from the official BOE API, stores it efficiently, and allows users to retrieve information using natural language through an Agentic Retrieval-Augmented Generation (RAG) system, all presented via a user-friendly Streamlit interface.

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Data Source](#data-source)
- [Technologies](#technologies)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Project Overview
BOE4Everyone aims to democratize access to the Spanish *Boletín Oficial del Estado* by providing a simple and intuitive way to query its data. The project extracts structured data from the BOE API, stores it locally, and leverages an Agentic RAG system to process natural language queries. The Streamlit interface ensures an accessible and engaging user experience. This is a collaborative personal project developed by two contributors passionate about open data and user-friendly technology.

## Features
- **Data Extraction**: Automatically pulls data from the BOE API.
- **Natural Language Queries**: Search BOE content using conversational language.
- **Agentic RAG**: Enhances query accuracy with retrieval-augmented generation.
- **Streamlit Interface**: Clean, interactive web-based UI for querying and viewing results.
- **Efficient Storage**: Optimized data storage for fast retrieval (database TBD).

## Data Source
The project uses the official BOE Open Data API provided by the Spanish government:
- **API Endpoint**: [https://www.boe.es/datosabiertos/api/api.php](https://www.boe.es/datosabiertos/api/api.php)
- The API provides access to structured BOE data, including legislation, announcements, and other official publications.

## Technologies
- **Python**: Core programming language.
- **BOE API**: Official source for BOE data.
- **Agentic RAG**: For intelligent natural language processing and query handling.
- **Streamlit**: Web framework for the interactive user interface.
- **Database**: (TBD, e.g., SQLite, PostgreSQL, or similar for data storage).
- **Additional Libraries**: (e.g., `requests`, `pandas`, `langchain`, to be finalized).

## Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/boe4everyone.git
   cd boe4everyone
   ```

2. **Set up a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   - Create a `.env` file in the root directory.
   - Add any required API keys or configuration details (e.g., for BOE API access, if needed).

5. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## Usage
1. Start the Streamlit app with the command above.
2. Open your browser and navigate to `http://localhost:8501` (or the provided URL).
3. Enter natural language queries (e.g., "Show me BOE laws from 2023 about education").
4. View and interact with the results displayed in the Streamlit interface.

More detailed usage instructions will be provided as the project evolves.

## Contributing
BOE4Everyone is a personal project maintained by two collaborators. We welcome feedback and ideas! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request for review.

Please ensure your contributions align with the project's goals and follow the code style.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For questions, suggestions, or feedback, please create a GitHub Issue or reach out via the repository.
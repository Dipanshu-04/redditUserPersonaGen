# Reddit User Persona Generator
###  scrapes comments and posts from user's reddit profile and generates a persona using LLM.
## Installation

**1. Clone the repo**

```bash
  git clone https://github.com/Dipanshu-04/redditUserPersonaGen.git
  ```
```bash
    cd redditUserPersonaGen
```
**2. Install the new dependency:**

```bash
      pip install requirements.txt
```

**3. Get a Gemini API key:**

* Go to Google AI Studio

* Create a new API key

* Add it to your ```.env``` file:

```bash
GEMINI_API_KEY=<your_api_key_here>
```
## Run Locally

Run the script

```bash
  python3 main.py
```
### User Interface

**1. Enter the Username or URL of the User** 

```bash
Reddit User Persona Generator
==================================================
Enter Reddit user URL or username: <username/URL>

```

**Response**

```bash
Analyzing user: u/<username>
Scraping user data...
Found 'n' posts/comments
Analyzing user persona...
Generating report...
Report saved to: persona_<username>_yyyymmdd_hhmmss.txt

==================================================
PERSONA SUMMARY
==================================================
Username: u/<username>
lorem ipsum....
Full report saved to: persona_<username>_yyyymmdd_hhmmss.txt
```



## Features

- Flexible user input - supports multiple Reddits URL format and direct Username input.
- Robust Error Handling.
- Integration of Google Generative AI gives more insightful persona for users.
- Can work with or without Google genai API.
- Provides insightful user personas based on user activity on reddit.



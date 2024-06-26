# Web Action Agent

## Installation Instructions

To set up the environment for this AI application that uses Playwright to scrape web data and store it locally, please follow these steps:

1. **Install Homebrew**:
    Homebrew is a package manager for macOS that makes it easy to install and manage software packages. Run the following command to install Homebrew:
    ```shell
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```
   
2. **Install Required Libraries**: 
    ```shell
    brew install libjpeg libtiff webp little-cms2
    ```
   
3. **Install everything in requirements.txt**: 
    
    This project has been tested on Python 3.12
    ```shell
    pip install -r requirements.txt 
    ```

## Prepare the .env File
To configure the environment variables for your project, create a .env file in the root directory of your project and copy the following content into it:
```text
# LLM Configuration
LLM_MODEL_TYPE=ChatOpenAI
LLM_OPENAI_API_KEY=<your_openai_api_key>

# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=<your_langchain_api_key>
LANGCHAIN_PROJECT=<your_project_name>

# Amazon Credentials
AMAZON_EMAIL=<your_amazon_email>
AMAZON_PASSWORD=<your_amazon_password>
```
1. LLM_MODEL_TYPE: Specifies the type of Language Learning Model (LLM) to use. Currently supported values are ChatOpenAI and AzureChatOpenAI. For more information on how to initialize the LLM, refer to utils/chat_model_env_util.py.
2. LLM_OPENAI_API_KEY: Your OpenAI API key. This is required to authenticate and interact with OpenAI's API.
3. LANGCHAIN_API_KEY: Your LangSmith API key. This is required to authenticate and interact with LangSmith's services.
4. LANGCHAIN_PROJECT: The name of your LangSmith project. This helps in organizing and managing your projects within LangSmith.
5. AMAZON_EMAIL: The email address associated with your Amazon account. This is used for Amazon-related operations within the application.
6. AMAZON_PASSWORD: The password for your Amazon account. This is used for Amazon-related operations within the application.

## Start the application
```shell
streamlit run main.py
```

You can then send some inputs, for example: "Show me my shopping cart info on Amazon" 

Because I didn't have any orders on Amazon, so I tested shopping carts instead

## Evaluation
I use LangSmith for evaluation, check out the process by running **eval/eval_amazon_web_agent.py**

## Demo Video
Here is a demo video showcasing the features of the application， located at **assets/Demo-video.mp4**

## Project Structure
```text
.
├── README.md
├── app
│   └── amazon_web_agent
│       ├── amazon_web_agent.py
│       └── tools
│           ├── amazon_web_agent_toolkit.py
│           └── extract_content_tool.py
├── assets
│   ├── Demo-video.mp4
├── data
├── eval
│   └── eval_amazon_web_agent.py
├── main.py
├── requirements.txt
├── tests
│   ├── 0_test_amazon_web_page_login.py
│   ├── 1_test_amazon_web_page_login_async.py
│   ├── 2_test_amazon_web_page_extract_async.py
│   ├── 3_test_amazon_web_agent.py
└── utils
    ├── chat_model_env_util.py
    ├── env_util.py
    └── logger_util.py
```
1. app: Contains all agents. Currently, it includes only one agent, amazon_web_agent.
2. assets: Contains the demo video.
3. data: Stores the output of the extracted content.
4. eval: Contains the evaluation code.
5. main.py: The main entry point of the application.
6. tests: Contains all test code.
7. utils: Contains utility classes.